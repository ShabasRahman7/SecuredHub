import os
import json
import boto3
from botocore.exceptions import ClientError


class SNSPublisher:
    def __init__(self):
        self.topic_arn = os.getenv('SNS_SCAN_COMPLETED_TOPIC')
        self.region = os.getenv('AWS_REGION', 'ap-south-1')
        
        if not self.topic_arn:
            self.client = None
            return
            
        self.client = boto3.client(
            'sns',
            region_name=self.region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
    
    def publish_scan_completed(self, scan_data: dict) -> bool:
        if not self.client:
            print("[SNS] Skipping - not configured")
            return False
        
        message = {
            'event_type': 'scan.completed',
            'scan_id': scan_data.get('scan_id'),
            'repo_id': scan_data.get('repo_id'),
            'repo_name': scan_data.get('repo_name'),
            'tenant_id': scan_data.get('tenant_id'),
            'tenant_name': scan_data.get('tenant_name'),
            'triggered_by': scan_data.get('triggered_by', 'manual'),
            'findings_count': scan_data.get('findings_count', 0),
            'severity_breakdown': scan_data.get('severity_breakdown', {}),
            'commit_hash': scan_data.get('commit_hash'),
            'scan_url': scan_data.get('scan_url'),
            'notification_targets': scan_data.get('notification_targets', [])
        }
        
        high_count = scan_data.get('severity_breakdown', {}).get('high', 0)
        critical_count = scan_data.get('severity_breakdown', {}).get('critical', 0)
        
        if critical_count > 0 or high_count >= 3:
            subject = f"[CRITICAL] Scan completed with {critical_count + high_count} high/critical findings"
        elif high_count > 0:
            subject = f"[WARNING] Scan completed with {high_count} high severity findings"
        else:
            subject = f"Scan completed - {scan_data.get('findings_count', 0)} findings"
        
        try:
            response = self.client.publish(
                TopicArn=self.topic_arn,
                Message=json.dumps(message),
                Subject=subject[:100],  # SNS limit
                MessageAttributes={
                    'event_type': {
                        'DataType': 'String',
                        'StringValue': 'scan.completed'
                    },
                    'has_high_severity': {
                        'DataType': 'String',
                        'StringValue': 'true' if high_count > 0 else 'false'
                    }
                }
            )
            print(f"[SNS] Published: {response['MessageId']}")
            return True
        except ClientError as e:
            print(f"[SNS] Failed: {e}")
            return False
    
    def publish_scan_failed(self, scan_data: dict) -> bool:
        if not self.client:
            return False
        
        message = {
            'event_type': 'scan.failed',
            'scan_id': scan_data.get('scan_id'),
            'repo_id': scan_data.get('repo_id'),
            'repo_name': scan_data.get('repo_name'),
            'tenant_id': scan_data.get('tenant_id'),
            'error_message': scan_data.get('error_message'),
            'notification_targets': scan_data.get('notification_targets', [])
        }
        
        try:
            self.client.publish(
                TopicArn=self.topic_arn,
                Message=json.dumps(message),
                Subject=f"[FAILED] Scan failed for {scan_data.get('repo_name', 'repository')}"
            )
            return True
        except ClientError as e:
            print(f"[SNS] Failed: {e}")
            return False
