import api from '../axios';
import { API_ENDPOINTS } from '../../constants/api';

export const inviteService = {
  // Get pending invites
  getInvites: async (tenantId) => {
    const response = await api.get(API_ENDPOINTS.TENANT_INVITES(tenantId));
    return response.data;
  },

  // Invite developer
  inviteDeveloper: async (tenantId, email) => {
    const response = await api.post(API_ENDPOINTS.INVITE_DEVELOPER(tenantId), { email });
    return response.data;
  },

  // Resend invite
  resendInvite: async (tenantId, token) => {
    const response = await api.post(API_ENDPOINTS.RESEND_INVITE(tenantId), { token });
    return response.data;
  },

  // Cancel invite
  cancelInvite: async (tenantId, token) => {
    const response = await api.post(API_ENDPOINTS.CANCEL_INVITE(tenantId), { token });
    return response.data;
  },

  // Verify invite token
  verifyInvite: async (token) => {
    const response = await api.post(API_ENDPOINTS.VERIFY_INVITE, { token });
    return response.data;
  },

  // Accept invite
  acceptInvite: async (token) => {
    const response = await api.post(API_ENDPOINTS.ACCEPT_INVITE, { token });
    return response.data;
  },
};
