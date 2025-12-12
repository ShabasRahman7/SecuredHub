import { useState, useEffect } from 'react';
import { tenantService } from '../api/services/tenantService';
import { toast } from 'react-toastify';

export const useTenantData = (tenant) => {
  const [currentTenant, setCurrentTenant] = useState(null);
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [tenantName, setTenantName] = useState('');
  const [tenantDescription, setTenantDescription] = useState('');

  useEffect(() => {
    if (tenant) {
      setCurrentTenant(tenant);
      setTenantName(tenant?.name || '');
      setTenantDescription(tenant?.description || '');
    }
  }, [tenant]);

  const updateProfile = async (e) => {
    e.preventDefault();
    if (!currentTenant) return;

    try {
      const data = await tenantService.updateTenant(currentTenant.id, {
        name: tenantName,
        description: tenantDescription,
      });

      if (data.success) {
        toast.success('Tenant profile updated');
        setIsEditingProfile(false);
        setCurrentTenant({ ...currentTenant, name: tenantName, description: tenantDescription });
      }
    } catch (error) {
      toast.error('Failed to update profile');
    }
  };

  return {
    currentTenant,
    setCurrentTenant,
    isEditingProfile,
    setIsEditingProfile,
    tenantName,
    setTenantName,
    tenantDescription,
    setTenantDescription,
    updateProfile,
  };
};
