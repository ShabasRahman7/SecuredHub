#!/bin/bash

# Script to add API_ENDPOINTS import and refactor API calls
# This script updates all frontend pages to use centralized API constants

echo "Starting API constants refactoring..."

# Find all JS/JSX files that make API calls
FILES=$(grep -rl "api\.\(get\|post\|put\|delete\|patch\)(['\"]/" --include="*.js" --include="*.jsx" frontend/src/pages/)

# Add API_ENDPOINTS import if not present
for FILE in $FILES; do
    if ! grep -q "API_ENDPOINTS" "$FILE"; then
        # Check if there are other imports from constants
        if grep -q "from.*constants" "$FILE"; then
            # Add to existing constants import
            sed -i "s|from '\(.*\)constants/\(.*\)';|from '\1constants/\2';\nimport { API_ENDPOINTS } from '\1constants/api';|" "$FILE"
        else
            # Add new import after other imports
            sed -i "/^import.*from/a import { API_ENDPOINTS } from '../../constants/api';" "$FILE"
        fi
        echo "Added API_ENDPOINTS import to: $FILE"
    fi
done

echo "✅ API_ENDPOINTS imports added"
echo ""
echo "Now manually replace API calls with constants using find/replace in your IDE:"
echo "  /auth/admin/tenants/ → API_ENDPOINTS.ADMIN_TENANTS"
echo "  /auth/admin/access-requests/ → API_ENDPOINTS.ADMIN_ACCESS_REQUESTS"
echo "  /tenants/\${id}/repositories/ → API_ENDPOINTS.TENANT_REPOSITORIES(id)"
echo "  etc..."
