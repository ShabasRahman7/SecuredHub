"""
Bandit Security Rules Knowledge Base Ingestion
Extracts Bandit rule documentation and adds to ChromaDB
"""
import sys
sys.path.append('/app')

from app.knowledge.vector_store import VectorStore

# bandit rules with descriptions (from Bandit documentation)
BANDIT_RULES = {
    "B102": {
        "title": "exec used",
        "description": "Use of exec detected. This is dangerous as it allows execution of arbitrary code.",
        "severity": "medium",
        "cwe": "CWE-78"
    },
    "B103": {
        "title": "set_bad_file_permissions",
        "description": "Chmod setting a permissive mask on file or directory",
        "severity": "high",
        "cwe": "CWE-732"
    },
    "B105": {
        "title": "hardcoded_password_string",
        "description": "Possible hardcoded password detected",
        "severity": "low",
        "cwe": "CWE-259"
    },
    "B106": {
        "title": "hardcoded_password_funcarg",
        "description": "Possible hardcoded password in function argument",
        "severity": "low",
        "cwe": "CWE-259"
    },
    "B201": {
        "title": "flask_debug_true",
        "description": "A Flask app appears to be run with debug=True, which exposes debugging information",
        "severity": "high",
        "cwe": "CWE-489"
    },
    "B301": {
        "title": "pickle",
        "description": "Pickle library appears to be in use, possible security issue. Consider using safer serialization formats.",
        "severity": "medium",
        "cwe": "CWE-502"
    },
    "B324": {
        "title": "hashlib",
        "description": "Use of insecure MD2, MD4, MD5, or SHA1 hash function",
        "severity": "high",
        "cwe": "CWE-327"
    },
    "B403": {
        "title": "import_pickle",
        "description": "Consider possible security implications associated with pickle module",
        "severity": "low",
        "cwe": "CWE-502"
    },
    "B501": {
        "title": "request_with_no_cert_validation",
        "description": "Requests call with verify=False disabling SSL certificate checks",
        "severity": "high",
        "cwe": "CWE-295"
    },
    "B602": {
        "title": "subprocess_popen_with_shell_equals_true",
        "description": "subprocess call with shell=True identified, security issue. Consider using shell=False or pass arguments as list.",
        "severity": "high",
        "cwe": "CWE-78"
    },
    "B605": {
        "title": "start_process_with_a_shell",
        "description": "Starting a process with a shell: Seems safe, but may be changed in the future",
        "severity": "high",
        "cwe": "CWE-78"
    },
    "B608": {
        "title": "hardcoded_sql_expressions",
        "description": "Possible SQL injection vector through string-based query construction",
        "severity": "medium",
        "cwe": "CWE-89"
    },
}

def ingest_bandit_rules():
    """Ingest Bandit security rules into ChromaDB"""
    print("[STARTING] Bandit rules ingestion...")
    
    vector_store = VectorStore()
    
    texts = []
    metadatas = []
    ids = []
    
    for rule_id, data in BANDIT_RULES.items():
        # creating comprehensive text for embedding
        text = f"""Bandit Rule {rule_id}: {data['title']}

Description: {data['description']}

Severity: {data['severity']}
CWE: {data['cwe']}

This is a security check performed by the Bandit static analysis tool for Python code.
"""
        texts.append(text)
        metadatas.append({
            "source": "Bandit",
            "rule_id": rule_id,
            "severity": data['severity'],
            "cwe": data['cwe'],
            "category": "security_rule"
        })
        ids.append(f"bandit_{rule_id}")
    
    print(f"[STORING] Adding {len(texts)} Bandit rules to ChromaDB...")
    vector_store.add_documents(texts, metadatas, ids)
    print(f"[SUCCESS] Bandit ingestion complete! Total chunks in DB: {vector_store.count()}")

if __name__ == "__main__":
    ingest_bandit_rules()
