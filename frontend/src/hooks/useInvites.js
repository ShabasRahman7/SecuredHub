import { useState, useEffect } from 'react';
import { inviteService } from '../api/services/inviteService';
import { toast } from 'react-toastify';
import { showConfirmDialog, showSuccessToast, showErrorToast } from '../utils/sweetAlert';

export const useInvites = (currentTenant, activeTab) => {
  const [invites, setInvites] = useState([]);
  const [loading, setLoading] = useState(false);
  const [resendingInvite, setResendingInvite] = useState(null);

  // Fetch invites only when on developers tab
  useEffect(() => {
    if (currentTenant && activeTab === 'developers') {
      fetchInvites();
    }
  }, [currentTenant, activeTab]);

  const fetchInvites = async () => {
    if (!currentTenant) return;
    setLoading(true);
    try {
      const data = await inviteService.getInvites(currentTenant.id);
      setInvites(data.invites || []);
    } catch (error) {
      console.error('Failed to fetch invites', error);
    } finally {
      setLoading(false);
    }
  };

  const sendInvite = async (email) => {
    if (!currentTenant) return false;

    try {
      const data = await inviteService.inviteDeveloper(currentTenant.id, email);
      if (data.success) {
        toast.success(`Invitation sent to ${email}`);
        fetchInvites();
        return true;
      }
    } catch (error) {
      toast.error(error.response?.data?.error?.message || 'Failed to send invite');
      return false;
    }
  };

  const resendInvite = async (token) => {
    setResendingInvite(token);
    try {
      const data = await inviteService.resendInvite(currentTenant.id, token);
      if (data.success) {
        toast.success(data.message);
        fetchInvites();
      }
    } catch (error) {
      toast.error(error.response?.data?.error?.message || 'Failed to resend invite');
    } finally {
      setResendingInvite(null);
    }
  };

  const cancelInvite = async (token) => {
    const isConfirmed = await showConfirmDialog({
      title: 'Cancel Invite?',
      text: 'This invitation will be cancelled.',
      icon: 'warning',
    });

    if (!isConfirmed) return;

    try {
      const data = await inviteService.cancelInvite(currentTenant.id, token);
      if (data.success) {
        showSuccessToast('Invitation cancelled');
        fetchInvites();
      }
    } catch (error) {
      showErrorToast('Failed to cancel invite');
    }
  };

  return {
    invites,
    loading,
    resendingInvite,
    fetchInvites,
    sendInvite,
    resendInvite,
    cancelInvite,
  };
};
