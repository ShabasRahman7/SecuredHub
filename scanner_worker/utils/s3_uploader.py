import os
import json
import boto3
from datetime import datetime, timezone
from botocore.exceptions import ClientError


class S3Uploader:
    def __init__(self):
        self.bucket = os.getenv('S3_SCAN_BUCKET')
        self.region = os.getenv('AWS_REGION', 'ap-south-1')
        
        if not self.bucket:
            self.client = None
            return
            
        self.client = boto3.client(
            's3',
            region_name=self.region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
    
    def upload_scan_results(self, scan_id: int, repo_id: int, findings: list, metadata: dict) -> str:
        if not self.client:
            print("[S3] Skipping - not configured")
            return None
            
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        s3_key = f"scans/{repo_id}/{scan_id}/{timestamp}_results.json"
        
        payload = {
            'scan_id': scan_id,
            'repo_id': repo_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'findings_count': len(findings),
            'findings': findings,
            'metadata': metadata
        }
        
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=json.dumps(payload, indent=2),
                ContentType='application/json'
            )
            print(f"[S3] Uploaded: s3://{self.bucket}/{s3_key}")
            return s3_key
        except ClientError as e:
            print(f"[S3] Failed: {e}")
            return None
    
    def upload_status(self, scan_id: int, repo_id: int, status: str, message: str = '') -> str:
        if not self.client:
            return None
            
        s3_key = f"scans/{repo_id}/{scan_id}/status.json"
        
        payload = {
            'scan_id': scan_id,
            'repo_id': repo_id,
            'status': status,
            'message': message,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=json.dumps(payload),
                ContentType='application/json'
            )
            print(f"[S3] Status: {status}")
            return s3_key
        except ClientError as e:
            print(f"[S3] Failed: {e}")
            return None
