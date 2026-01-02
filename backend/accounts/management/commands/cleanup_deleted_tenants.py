from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction, connection
from datetime import timedelta

from accounts.models import Tenant, TenantMember, TenantInvite, AccessRequest, MemberInvite
from accounts.utils.redis_tokens import InviteTokenManager

class Command(BaseCommand):
    help = "Permanently delete tenants that were soft-deleted more than 30 days ago"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without modifying data",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Number of days after soft delete to permanently delete (default: 30)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        days = options["days"]

        self.stdout.write(
            self.style.SUCCESS(
                f"Starting tenant cleanup for tenants soft-deleted more than {days} days ago {'(DRY RUN)' if dry_run else ''}"
            )
        )

        now = timezone.now()
        cutoff_date = now - timedelta(days=days)

        # finding tenants that were soft-deleted and scheduled for deletion
        tenants_to_delete = Tenant.objects.filter(
            deleted_at__isnull=False,
            deletion_scheduled_at__lte=now
        )

        count = tenants_to_delete.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No tenants scheduled for permanent deletion"))
            return

        self.stdout.write(f"Found {count} tenant(s) scheduled for permanent deletion")

        if dry_run:
            for tenant in tenants_to_delete:
                days_since_deletion = (now - tenant.deleted_at).days
                self.stdout.write(
                    f"  - {tenant.name} (ID: {tenant.id}) - Deleted {days_since_deletion} days ago"
                )
            return

        deleted_count = 0
        errors = []

        for tenant in tenants_to_delete:
            try:
                with transaction.atomic():
                    self.stdout.write(f"Permanently deleting tenant: {tenant.name} (ID: {tenant.id})")
                    
                    # storing owner email before deletion
                    owner_email = tenant.created_by.email if tenant.created_by else None
                    
                    # checking if users table has a tenant_id column and set it to NULL
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                SELECT column_name 
                                FROM information_schema.columns 
                                WHERE table_name='users' AND column_name='tenant_id'
                            """)
                            if cursor.fetchone():
                                cursor.execute("""
                                    UPDATE users 
                                    SET tenant_id = NULL 
                                    WHERE tenant_id = %s
                                """, [tenant.id])
                    except Exception:
                        pass
                    
                    # deleting all TenantMember records first
                    tenant_members = TenantMember.objects.filter(tenant=tenant)
                    member_count = tenant_members.count()
                    tenant_members.delete()
                    self.stdout.write(f"  - Deleted {member_count} tenant member(s)")
                    
                    # deleting member invites for this tenant
                    member_invites = MemberInvite.objects.filter(tenant=tenant)
                    invite_count = member_invites.count()
                    member_invites.delete()
                    self.stdout.write(f"  - Deleted {invite_count} member invite(s)")
                    
                    # deleting related tenant invites and access requests
                    if owner_email:
                        tenant_invites = TenantInvite.objects.filter(email=owner_email)
                        for invite in tenant_invites:
                            try:
                                if invite.token:
                                    InviteTokenManager.delete_token(str(invite.token))
                            except Exception:
                                pass
                        invite_count = tenant_invites.count()
                        tenant_invites.delete()
                        self.stdout.write(f"  - Deleted {invite_count} tenant invite(s)")
                        
                        access_requests = AccessRequest.objects.filter(email=owner_email)
                        request_count = access_requests.count()
                        access_requests.delete()
                        self.stdout.write(f"  - Deleted {request_count} access request(s)")
                    
                    # permanently delete the tenant
                    tenant_name = tenant.name
                    tenant.delete()
                    deleted_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ Permanently deleted tenant: {tenant_name}")
                    )
            except Exception as e:
                error_msg = f"Failed to delete tenant {tenant.name} (ID: {tenant.id}): {str(e)}"
                errors.append(error_msg)
                self.stdout.write(self.style.ERROR(f"  ✗ {error_msg}"))

        # summary
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Tenant cleanup completed"))
        self.stdout.write(f"  - Successfully deleted: {deleted_count} tenant(s)")
        if errors:
            self.stdout.write(self.style.WARNING(f"  - Errors: {len(errors)}"))
            for error in errors:
                self.stdout.write(self.style.ERROR(f"    {error}"))

