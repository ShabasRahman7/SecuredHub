"""Seed script to populate vector store with OWASP/CWE security knowledge."""
import sys
sys.path.append('/app')

from app.knowledge.vector_store import VectorStore

# comprehensive security knowledge for common vulnerabilities
SECURITY_KNOWLEDGE = [
    # sQL Injection
    {
        "title": "SQL Injection Prevention",
        "content": """SQL Injection is a code injection technique that exploits security vulnerabilities in database layer of applications.

**How it works:**
Attackers insert malicious SQL code into application queries, potentially gaining unauthorized access to sensitive data or manipulating database contents.

**Prevention in Python/Django:**
1. Use parameterized queries (ORM): User.objects.filter(username=user_input)
2. Never concatenate strings: UNSAFE: f'SELECT * FROM users WHERE name = {user_input}'
3. Use Django ORM which automatically escapes inputs
4. Validate and sanitize all user inputs

**Example Safe Code (Django):**
```python
# safe - uses ORM
users = User.objects.filter(email=request.POST['email'])

# safe - parameterized query
cursor.execute('SELECT * FROM users WHERE id = %s', [user_id])
```

**CWE-89, OWASP A03:2025 Injection**
""",
        "metadata": {"source": "Manual", "cwe": "CWE-89", "category": "injection", "language": "python"}
    },
    
    # hardcoded Secrets
    {
        "title": "Hardcoded Secrets and Passwords",
        "content": """Hardcoded credentials in source code pose serious security risks.

**Why it's dangerous:**
- Secrets visible in version control
- Easy to discover by attackers
- Difficult to rotate/update
- Violates principle of least privilege

**Best Practices:**
1. Use environment variables: os.getenv('API_KEY')
2. Use secret management tools (AWS Secrets Manager, HashiCorp Vault)
3. Never commit .env files containing secrets
4. Use configuration files excluded from Git (.gitignore)

**Example Secure Pattern:**
```python
# BAD
API_KEY = "sk_live_51H7cXXXXXXXXX"
DATABASE_PASSWORD = "admin123"

# GOOD
import os
API_KEY = os.environ.get('API_KEY')
DB_PASSWORD = os.getenv('DATABASE_PASSWORD')

# even better - use python-decouple
from decouple import config
API_KEY = config('API_KEY')
```

**Related:** Bandit B105, B106, CWE-259, OWASP A07:2025 Authentication Failures
""",
        "metadata": {"source": "Manual", "cwe": "CWE-259", "category": "secrets", "language": "python"}
    },
    
    # command Injection
    {
        "title": "Command Injection and Shell=True",
        "content": """Using shell=True in subprocess calls creates command injection vulnerabilities.

**The Problem:**
When shell=True is used, the command is passed through the shell, allowing attackers to inject additional commands using shell metacharacters like ; | & $ ( ) ` etc.

**Vulnerable Code:**
```python
import subprocess
user_input = request.GET['filename']
subprocess.call(f'cat {user_input}', shell=True)  # VULNERABLE!
# attacker input: "file.txt; rm -rf /"
```

**Secure Alternatives:**
```python
# option 1: Use shell=False with list arguments
subprocess.run(['cat', user_input], shell=False)

# option 2: Use shlex.quote() if shell is necessary
import shlex
safe_input = shlex.quote(user_input)
subprocess.run(f'cat {safe_input}', shell=True)

# option 3: Avoid subprocess entirely
with open(user_input, 'r') as f:
    content = f.read()
```

**Bandit Rules:** B602, B605, B607
**CWE-78 OS Command Injection, OWASP A03:2025 Injection**
""",
        "metadata": {"source": "Manual", "cwe": "CWE-78", "category": "command_injection", "language": "python", "rule_id": "B602"}
    },
    
    # insecure Deserialization
    {
        "title": "Pickle Deserialization Vulnerabilities",
        "content": """Python's pickle module can execute arbitrary code during deserialization.

**Why Pickle is Dangerous:**
Pickle can serialize and deserialize Python objects, including code. Malicious pickle data can execute arbitrary commands when unpickled.

**Attack Scenario:**
Attacker sends crafted pickle data that executes os.system('malicious command') during unpickling.

**Secure Alternatives:**
```python
# INSECURE
import pickle
data = pickle.loads(untrusted_data)  # Can execute code!

# sECURE Options:
# 1. Use JSON (only supports basic data types)
import json
data = json.loads(untrusted_data)

# 2. Use safer serialization
import msgpack
data = msgpack.unpackb(untrusted_data)

# 3. If pickle is absolutely necessary, sign the data
import hmac, hashlib
signature = hmac.new(secret_key, pickled_data, hashlib.sha256).digest()
# verifying signature before unpickling
```

**Bandit:** B301, B403
**CWE-502 Deserialization of Untrusted Data**
**OWASP A08:2025 Software and Data Integrity Failures**
""",
        "metadata": {"source": "Manual", "cwe": "CWE-502", "category": "deserialization", "language": "python", "rule_id": "B301"}
    },
    
    # weak Cryptography
    {
        "title": "Weak Hash Functions MD5 and SHA1",
        "content": """MD5 and SHA1 are cryptographically broken and should not be used for security purposes.

**Why They're Weak:**
- MD5: Collision attacks are trivial (2^24 operations)
- SHA1: Collision attacks demonstrated in 2017
- Both vulnerable to rainbow table attacks

**When It's Dangerous:**
- Password hashing
- Digital signatures  
- Certificate validation
- Integrity verification of sensitive data

**Secure Alternatives:**
```python
# INSECURE
import hashlib
password_hash = hashlib.md5(password.encode()).hexdigest()  # BAD!
sha1_hash = hashlib.sha1(data).hexdigest()  # BAD!

# sECURE for passwords - use bcrypt/argon2
import bcrypt
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# sECURE for general hashing - use SHA256/SHA512
secure_hash = hashlib.sha256(data.encode()).hexdigest()

# sECURE for passwords - use Django's built-in
from django.contrib.auth.hashers import make_password
hashed = make_password(password)
```

**Acceptable MD5/SHA1 Use:**
- Non-security checksums (file integrity checks)
- ETags in HTTP
- Git commit hashes

**Bandit:** B324
**CWE-327 Use of Broken Cryptography**
**OWASP A02:2025 Cryptographic Failures**
""",
        "metadata": {"source": "Manual", "cwe": "CWE-327", "category": "cryptography", "language": "python", "rule_id": "B324"}
    },
    
    # sSL Verification
    {
        "title": "SSL Certificate Verification",
        "content": """Disabling SSL certificate verification exposes applications to man-in-the-middle attacks.

**The Vulnerability:**
When verify=False is used in requests, the application doesn't verify the server's SSL certificate, allowing attackers to intercept and modify traffic.

**Insecure Code:**
```python
import requests
# INSECURE - vulnerable to MITM
response = requests.get('https://api.example.com', verify=False)
```

**Secure Practices:**
```python
# sECURE - verify certificates (default behavior)
response = requests.get('https://api.example.com')  # verify=True is default

# if you need custom CA certificate
response = requests.get('https://api.example.com', verify='/path/to/certfile')

# for development/testing with self-signed certs
# use environment-specific config, never hardcode verify=False
import os
VERIFY_SSL = os.getenv('VERIFY_SSL', 'true').lower() == 'true'
response = requests.get(url, verify=VERIFY_SSL)
```

**Bandit:** B501
**CWE-295 Improper Certificate Validation**
**OWASP A02:2025 Cryptographic Failures**
""",
        "metadata": {"source": "Manual", "cwe": "CWE-295", "category": "ssl", "language": "python", "rule_id": "B501"}
    },
]

def ingest_security_knowledge():
    print("[STARTING] Comprehensive security knowledge ingestion...")
    
    vector_store = VectorStore()
    
    texts = []
    metadatas = []
    ids = []
    
    for idx, item in enumerate(SECURITY_KNOWLEDGE):
        full_text = f"{item['title']}\n\n{item['content']}"
        texts.append(full_text)
        metadatas.append(item['metadata'])
        ids.append(f"security_knowledge_{idx}")
    
    print(f"[STORING] Adding {len(texts)} comprehensive security knowledge chunks...")
    vector_store.add_documents(texts, metadatas, ids)
    print(f"[SUCCESS] Knowledge ingestion complete! Total chunks in DB: {vector_store.count()}")

if __name__ == "__main__":
    ingest_security_knowledge()
