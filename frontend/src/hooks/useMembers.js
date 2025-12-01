import { useState, useEffect } from 'react';
import { tenantService } from '../api/services/tenantService';
import { showConfirmDialog, showSuccessToast, showErrorToast } from '../utils/sweetAlert';
import api from '../api/axios';

export const useMembers = (currentTenant) => {
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (currentTenant) {
      fetchMembers();
    }
  }, [currentTenant]);

  const fetchMembers = async () => {
    if (!currentTenant) return;
    setLoading(true);
    try {
      const data = await tenantService.getMembers(currentTenant.id);
      setMembers(data.members || []);
    } catch (error) {
      console.error('Failed to fetch members', error);
    } finally {
      setLoading(false);
    }
  };

  const removeMember = async (memberId) => {
    if (!currentTenant) return;
    
    const isConfirmed = await showConfirmDialog({
      title: 'Remove Member?',
      text: 'They will lose access.',
      icon: 'warning',
    });

    if (!isConfirmed) return;

    try {
      const response = await api.delete(`/tenants/${currentTenant.id}/members/${memberId}/remove/`);
      if (response.data.success) {
        showSuccessToast('Member removed');
        setMembers(members.filter(m => m.id !== memberId));
      }
    } catch (error) {
      showErrorToast('Failed to remove member');
    }
  };

  return {
    members,
    loading,
    fetchMembers,
    removeMember,
  };
};
