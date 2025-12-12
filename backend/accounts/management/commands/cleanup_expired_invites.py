from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import logging

from accounts.models import MemberInvite, TenantInvite

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clean up expired and old invitations"

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete-old",
            action="store_true",
            help="Delete invitations older than 30 days (default: only mark expired)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be cleaned without modifying data",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        delete_old = options["delete_old"]

        self.stdout.write(
            self.style.SUCCESS(f"Starting invitation cleanup {'(DRY RUN)' if dry_run else ''}")
        )

        now = timezone.now()

        # -------------------------
        # EXPIRE INVITES (COMMON LOGIC)
        # -------------------------
        def expire_invites(model, pending_status, expired_status, label):
            qs = model.objects.filter(
                expires_at__lt=now,
                status=pending_status,
            )
            count = qs.count()

            if count == 0:
                return 0

            self.stdout.write(f"Found {count} expired {label} invitations")

            if dry_run:
                return count

            updated = qs.update(status=expired_status)
            self.stdout.write(self.style.SUCCESS(f"Marked {updated} {label} invitations as expired"))
            logger.info(f"Marked {updated} {label} invitations as expired")
            return updated

        expired_members = expire_invites(
            MemberInvite,
            MemberInvite.STATUS_PENDING,
            MemberInvite.STATUS_EXPIRED,
            "member",
        )

        expired_tenants = expire_invites(
            TenantInvite,
            TenantInvite.STATUS_PENDING,
            TenantInvite.STATUS_EXPIRED,
            "tenant",
        )

        # -------------------------
        # DELETE OLD INVITES (OPTIONAL)
        # -------------------------
        if delete_old:
            thirty_days_ago = now - timedelta(days=30)

            # --- MemberInvites: delete expired + cancelled ---
            old_member_qs = MemberInvite.objects.filter(
                created_at__lt=thirty_days_ago,
                status__in=[MemberInvite.STATUS_EXPIRED, MemberInvite.STATUS_CANCELLED],
            )
            old_member_count = old_member_qs.count()

            if old_member_count > 0:
                self.stdout.write(f"Found {old_member_count} old member invitations to delete")
                if not dry_run:
                    deleted_count, _ = old_member_qs.delete()
                    self.stdout.write(
                        self.style.WARNING(f"Deleted {deleted_count} old member invitations")
                    )
                    logger.info(f"Deleted {deleted_count} old member invitations")

            # --- TenantInvites: delete expired only (NOT registered) ---
            old_tenant_qs = TenantInvite.objects.filter(
                invited_at__lt=thirty_days_ago,
                status=TenantInvite.STATUS_EXPIRED,
            )
            old_tenant_count = old_tenant_qs.count()

            if old_tenant_count > 0:
                self.stdout.write(f"Found {old_tenant_count} old tenant invitations to delete")
                if not dry_run:
                    deleted_count, _ = old_tenant_qs.delete()
                    self.stdout.write(
                        self.style.WARNING(f"Deleted {deleted_count} old tenant invitations")
                    )
                    logger.info(f"Deleted {deleted_count} old tenant invitations")

        # -------------------------
        # SUMMARY
        # -------------------------
        if expired_members == 0 and expired_tenants == 0 and not delete_old:
            self.stdout.write(self.style.SUCCESS("No expired invitations found"))

        self.stdout.write(self.style.SUCCESS("Invitation cleanup completed"))
