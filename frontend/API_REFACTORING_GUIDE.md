# API Constants Refactoring Guide

This document provides a quick reference for refactoring hardcoded API paths to use the centralized `API_ENDPOINTS` constants.

## Import Statement

Add this to all files making API calls:
```javascript
import { API_ENDPOINTS } from '../../constants/api';  // Adjust path as needed
```

## Replacement Map

Use find/replace in your IDE with these mappings:

### Auth Endpoints
| Before | After |
|--------|-------|
| `'/auth/login/'` | `API_ENDPOINTS.LOGIN` |
| `'/auth/register/'` | `API_ENDPOINTS.REGISTER` |
| `'/auth/send-otp/'` | `API_ENDPOINTS.SEND_OTP` |
| `'/auth/verify-otp/'` | `API_ENDPOINTS.VERIFY_OTP` |
| `'/auth/request-access/'` | `API_ENDPOINTS.REQUEST_ACCESS` |
| ```'/auth/verify-invite/?token=${token}'``` | ```API_ENDPOINTS.VERIFY_INVITE + `?token=${token}` ``` |

### Admin Endpoints
| Before | After |
|--------|-------|
| `'/auth/admin/tenants/'` | `API_ENDPOINTS.ADMIN_TENANTS` |
| `'/auth/admin/tenants/?include_deleted=true'` | `API_ENDPOINTS.ADMIN_TENANTS_WITH_DELETED` |
| `'/auth/admin/tenant-invites/'` | `API_ENDPOINTS.ADMIN_TENANT_INVITES` |
| `'/auth/admin/invite-tenant/'` | `API_ENDPOINTS.ADMIN_INVITE_TENANT` |
| `'/auth/admin/access-requests/'` | `API_ENDPOINTS.ADMIN_ACCESS_REQUESTS` |
| ``` `/auth/admin/access-requests/${id}/approve/` ``` | `API_ENDPOINTS.ADMIN_APPROVE_ACCESS_REQUEST(id)` |
| ``` `/auth/admin/access-requests/${id}/reject/` ``` | `API_ENDPOINTS.ADMIN_REJECT_ACCESS_REQUEST(id)` |
| ``` `/auth/admin/tenant-invites/${id}/resend/` ``` | `API_ENDPOINTS.ADMIN_RESEND_TENANT_INVITE(id)` |
| ``` `/auth/admin/tenant-invites/${id}/delete/` ``` | `API_ENDPOINTS.ADMIN_DELETE_TENANT_INVITE(id)` |
| ``` `/auth/admin/tenants/${id}/delete/` ``` | `API_ENDPOINTS.ADMIN_DELETE_TENANT(id, false)` |
| ``` `/auth/admin/tenants/${id}/delete/?hard_delete=true` ``` | `API_ENDPOINTS.ADMIN_DELETE_TENANT(id, true)` |
| ``` `/auth/admin/tenants/${id}/restore/` ``` | `API_ENDPOINTS.ADMIN_RESTORE_TENANT(id)` |
| ``` `/auth/admin/tenants/${id}/block/` ``` | `API_ENDPOINTS.ADMIN_BLOCK_TENANT(id)` |

### Tenant Endpoints
| Before | After |
|--------|-------|
| ``` `/tenants/${id}/` ``` | `API_ENDPOINTS.TENANT_DETAIL(id)` |
| ``` `/tenants/${id}/update/` ``` | `API_ENDPOINTS.TENANT_UPDATE(id)` |
| ``` `/tenants/${id}/members/` ``` | `API_ENDPOINTS.TENANT_MEMBERS(id)` |
| ``` `/tenants/${id}/members/?include_deleted=true` ``` | `API_ENDPOINTS.TENANT_MEMBERS_WITH_DELETED(id)` |
| ``` `/tenants/${id}/invites/` ``` | `API_ENDPOINTS.TENANT_INVITES(id)` |
| ``` `/tenants/${id}/invite/` ``` | `API_ENDPOINTS.TENANT_INVITE_DEVELOPER(id)` |
| ``` `/tenants/${tId}/invites/${iId}/resend/` ``` | `API_ENDPOINTS.TENANT_RESEND_INVITE(tId, iId)` |
| ``` `/tenants/${tId}/invites/${iId}/cancel/` ``` | `API_ENDPOINTS.TENANT_CANCEL_INVITE(tId, iId)` |
| ``` `/tenants/${tId}/members/${mId}/block/` ``` | `API_ENDPOINTS.TENANT_BLOCK_MEMBER(tId, mId)` |
| ``` `/tenants/${tId}/members/${mId}/remove/` ``` | `API_ENDPOINTS.TENANT_REMOVE_MEMBER(tId, mId, false)` |
| ``` `/tenants/${tId}/members/${mId}/remove/?hard_delete=true` ``` | `API_ENDPOINTS.TENANT_REMOVE_MEMBER(tId, mId, true)` |
| ``` `/tenants/${tId}/members/${mId}/restore/` ``` | `API_ENDPOINTS.TENANT_RESTORE_MEMBER(tId, mId)` |

### Repository Endpoints
| Before | After |
|--------|-------|
| ``` `/tenants/${tId}/repositories/` ``` | `API_ENDPOINTS.TENANT_REPOSITORIES(tId)` |
| ``` `/tenants/${tId}/repositories/create/` ``` | `API_ENDPOINTS.ADD_REPOSITORY(tId)` |
| ``` `/tenants/${tId}/repositories/${rId}/delete/` ``` | `API_ENDPOINTS.DELETE_REPOSITORY(tId, rId)` |
| ``` `/tenants/${tId}/repositories/${rId}/assignments/` ``` | `API_ENDPOINTS.REPOSITORY_ASSIGNMENTS(tId, rId)` |
| ``` `/tenants/${tId}/repositories/${rId}/assign/` ``` | `API_ENDPOINTS.ASSIGN_DEVELOPERS(tId, rId)`  |
| ``` `/tenants/${tId}/repositories/${rId}/assignments/${aId}/unassign/` ``` | `API_ENDPOINTS.UNASSIGN_DEVELOPER(tId, rId, aId)` |

### Scan Endpoints
| Before | After |
|--------|-------|
| ``` `/scans/${id}/` ``` | `API_ENDPOINTS.SCAN_DETAIL(id)` |
| ``` `/scans/${id}/findings/` ``` | `API_ENDPOINTS.SCAN_FINDINGS(id)` |
| ``` `/scans/repository/${repoId}/` ``` | `API_ENDPOINTS.REPOSITORY_SCANS(repoId)` |
| ``` `/scans/trigger/${repoId}/` ``` | `API_ENDPOINTS.TRIGGER_SCAN(repoId)` |
| ``` `/scans/${id}/delete/` ``` | `API_ENDPOINTS.DELETE_SCAN(id)` |

### Chat/AI Endpoints
| Before | After |
|--------|-------|
| `'/chat/conversations'` | `API_ENDPOINTS.CHAT_CONVERSATIONS` |
| ``` `/chat/findings/${id}/chat/init` ``` | `API_ENDPOINTS.CHAT_INIT_FINDING(id)` |
| ``` `/chat/findings/${id}/chat` ``` | `API_ENDPOINTS.CHAT_SEND_MESSAGE(id)` |
| ``` `/chat/conversations/${id}` ``` | `API_ENDPOINTS.CHAT_DELETE_CONVERSATION(id)` |

### Notifications Endpoints
| Before | After |
|--------|-------|
| `'/notifications/'` | `API_ENDPOINTS.NOTIFICATIONS` |
| ``` `/notifications/${id}/` ``` | `API_ENDPOINTS.NOTIFICATION_DETAIL(id)` |
| `'/notifications/mark-read/'` | `API_ENDPOINTS.MARK_NOTIFICATIONS_READ` |
| `'/notifications/mark-all-read/'` | `API_ENDPOINTS.MARK_ALL_NOTIFICATIONS_READ` |
| `'/notifications/clear-all/'` | `API_ENDPOINTS.CLEAR_ALL_NOTIFICATIONS` |
| `'/notifications/unread-count/'` | `API_ENDPOINTS.UNREAD_NOTIFICATION_COUNT` |

## Tips

1. **Use IDE Find/Replace** with regex for bulk replacements
2. **Test after each section** to ensure no breaking changes  
3. **Already refactored**: `Tenant Repositories.jsx` is done as an example
4. **Variable names**: Replace `${id}`, `${tenantId}`, etc. with actual variable names from code

## Benefits

- ✅ Single source of truth for API URLs
- ✅ Easy to update all endpoints from one place
- ✅ Better type safety and autocomplete
- ✅ Self-documenting code
- ✅ Easier to maintain and debug
