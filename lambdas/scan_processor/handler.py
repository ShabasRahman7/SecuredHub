import json
import boto3
import urllib.parse


def lambda_handler(event, context):
    s3 = boto3.client('s3')
    
    for record in event.get('Records', []):
        bucket = record['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        
        print(f"Processing: s3://{bucket}/{key}")
        
        if not key.endswith('status.json'):
            print(f"Skipping: {key}")
            continue
        
        try:
            response = s3.get_object(Bucket=bucket, Key=key)
            status_data = json.loads(response['Body'].read().decode('utf-8'))
            
            scan_id = status_data.get('scan_id')
            repo_id = status_data.get('repo_id')
            status = status_data.get('status')
            message = status_data.get('message', '')
            
            print(f"Scan {scan_id} for repo {repo_id}: {status} - {message}")
            
            if status == 'completed':
                print(f"Scan {scan_id} completed")
            
        except Exception as e:
            print(f"Error: {e}")
            raise
    
    return {'statusCode': 200, 'body': json.dumps('OK')}
