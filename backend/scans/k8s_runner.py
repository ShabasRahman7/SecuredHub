import os
import yaml
from datetime import datetime
from kubernetes import client, config

K3S_CONFIG_PATH = os.environ.get('K3S_CONFIG_PATH', '/opt/securedhub/k3s-config.yaml')
ECR_IMAGE = os.environ.get('SCANNER_IMAGE', '180667017068.dkr.ecr.ap-south-1.amazonaws.com/securedhub-scanner:latest')
NAMESPACE = 'securedhub-scanners'

def get_k8s_client():
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    config.load_kube_config(config_file=K3S_CONFIG_PATH)
    
    # Skip TLS verification for external IP access
    configuration = client.Configuration.get_default_copy()
    configuration.verify_ssl = False
    client.Configuration.set_default(configuration)
    
    return client.BatchV1Api()

def create_scan_job(scan_id, repo_url, commit_sha='HEAD'):
    job_name = f"scan-{scan_id}"
    
    job = client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(
            name=job_name,
            namespace=NAMESPACE,
            labels={"app": "scanner", "scan-id": str(scan_id)}
        ),
        spec=client.V1JobSpec(
            ttl_seconds_after_finished=3600,
            backoff_limit=1,
            template=client.V1PodTemplateSpec(
                spec=client.V1PodSpec(
                    containers=[
                        client.V1Container(
                            name="scanner",
                            image=ECR_IMAGE,
                            env=[
                                client.V1EnvVar(name="SCAN_ID", value=str(scan_id)),
                                client.V1EnvVar(name="REPO_URL", value=repo_url),
                                client.V1EnvVar(name="COMMIT_SHA", value=commit_sha),
                            ],
                            env_from=[
                                client.V1EnvFromSource(
                                    secret_ref=client.V1SecretEnvSource(name="scanner-secrets")
                                )
                            ],
                            resources=client.V1ResourceRequirements(
                                requests={"memory": "512Mi", "cpu": "500m"},
                                limits={"memory": "1Gi", "cpu": "1000m"}
                            )
                        )
                    ],
                    image_pull_secrets=[client.V1LocalObjectReference(name="ecr-secret")],
                    restart_policy="Never"
                )
            )
        )
    )
    
    return job

def submit_scan_job(scan_id, repo_url, commit_sha='HEAD'):
    try:
        batch_v1 = get_k8s_client()
        job = create_scan_job(scan_id, repo_url, commit_sha)
        
        result = batch_v1.create_namespaced_job(namespace=NAMESPACE, body=job)
        return {
            "success": True,
            "job_name": result.metadata.name,
            "namespace": NAMESPACE,
            "created_at": datetime.utcnow().isoformat()
        }
    except client.exceptions.ApiException as e:
        if e.status == 409:
            return {"success": False, "error": f"Job scan-{scan_id} already exists"}
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_job_status(scan_id):
    try:
        batch_v1 = get_k8s_client()
        job_name = f"scan-{scan_id}"
        
        job = batch_v1.read_namespaced_job(name=job_name, namespace=NAMESPACE)
        
        if job.status.succeeded:
            return {"status": "completed", "succeeded": job.status.succeeded}
        elif job.status.failed:
            return {"status": "failed", "failed": job.status.failed}
        elif job.status.active:
            return {"status": "running", "active": job.status.active}
        else:
            return {"status": "pending"}
    except client.exceptions.ApiException as e:
        if e.status == 404:
            return {"status": "not_found"}
        return {"status": "error", "error": str(e)}

def delete_scan_job(scan_id):
    try:
        batch_v1 = get_k8s_client()
        job_name = f"scan-{scan_id}"
        
        batch_v1.delete_namespaced_job(
            name=job_name,
            namespace=NAMESPACE,
            body=client.V1DeleteOptions(propagation_policy="Foreground")
        )
        return {"success": True, "job_name": job_name}
    except client.exceptions.ApiException as e:
        return {"success": False, "error": str(e)}
