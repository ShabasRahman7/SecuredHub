import api from '../axios';
import { API_ENDPOINTS } from '../../constants/api';

export const inviteService = {
  // getting pending invites
  getInvites: async (tenantId) => {
    const response = await api.get(API_ENDPOINTS.TENANT_INVITES(tenantId));
    return response.data;
  },

  // invite developer
  inviteDeveloper: async (tenantId, email) => {
    const response = await api.post(API_ENDPOINTS.INVITE_DEVELOPER(tenantId), { email });
    return response.data;
  },

  // resend invite
  resendInvite: async (tenantId, token) => {
    const response = await api.post(API_ENDPOINTS.RESEND_INVITE(tenantId), { token });
    return response.data;
  },

  // canceling invite
  cancelInvite: async (tenantId, token) => {
    const response = await api.post(API_ENDPOINTS.CANCEL_INVITE(tenantId), { token });
    return response.data;
  },

  // verifying invite token
  verifyInvite: async (token) => {
    const response = await api.post(API_ENDPOINTS.VERIFY_INVITE, { token });
    return response.data;
  },

  // accepting invite
  acceptInvite: async (token) => {
    const response = await api.post(API_ENDPOINTS.ACCEPT_INVITE, { token });
    return response.data;
  },
};
