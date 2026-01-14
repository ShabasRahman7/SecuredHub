import json
import boto3
from datetime import datetime

s3 = boto3.client('s3')
BUCKET = 'securedhub-scan-artifacts-prod'

def lambda_handler(event, context):
    for record in event.get('Records', []):
        sns_message = record.get('Sns', {})
        message = json.loads(sns_message.get('Message', '{}'))
        
        scan_id = message.get('scan_id')
        repo_name = message.get('repo_name', 'unknown')
        tenant_name = message.get('tenant_name', 'unknown')
        
        now = datetime.utcnow()
        s3_key = f"audit/{now.year}/{now.month:02d}/{now.day:02d}/scan_{scan_id}.json"
        
        audit_record = {
            'event_type': message.get('event_type'),
            'timestamp': now.isoformat() + 'Z',
            'scan_id': scan_id,
            'repo_id': message.get('repo_id'),
            'repo_name': repo_name,
            'tenant_id': message.get('tenant_id'),
            'tenant_name': tenant_name,
            'findings_count': message.get('findings_count', 0),
            'severity_breakdown': message.get('severity_breakdown', {}),
            'commit_hash': message.get('commit_hash'),
            'notification_targets': message.get('notification_targets', [])
        }
        
        s3.put_object(
            Bucket=BUCKET,
            Key=s3_key,
            Body=json.dumps(audit_record, indent=2),
            ContentType='application/json'
        )
        
        print(f"[AUDIT] Logged: s3://{BUCKET}/{s3_key}")
    
    return {'statusCode': 200}
