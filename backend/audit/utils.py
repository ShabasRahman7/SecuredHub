from django.utils import timezone


def log_audit_event(
    event_type: str,
    actor=None,
    target_type: str = '',
    target_id: int = None,
    target_name: str = '',
    tenant=None,
    request=None,
    metadata: dict = None
):
    from audit.models import AuditLog
    
    ip_address = None
    user_agent = ''
    
    if request:
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        ip_address = x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
    
    AuditLog.objects.create(
        event_type=event_type,
        actor_id=actor.id if actor else None,
        actor_email=actor.email if actor else '',
        target_type=target_type,
        target_id=target_id,
        target_name=target_name,
        tenant_id=tenant.id if tenant else None,
        tenant_name=tenant.name if tenant else '',
        ip_address=ip_address,
        user_agent=user_agent,
        metadata=metadata or {}
    )
