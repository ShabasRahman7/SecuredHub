import { useState, useEffect } from 'react';
import { tenantService } from '../api/services/tenantService';
import { toast } from 'react-toastify';

export const useTenantData = (tenants) => {
  const [currentTenant, setCurrentTenant] = useState(null);
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [tenantName, setTenantName] = useState('');
  const [tenantDescription, setTenantDescription] = useState('');

  useEffect(() => {
    if (tenants.length > 0) {
      const tenant = tenants.find(t => t.role === 'owner') || tenants[0];
      setCurrentTenant(tenant);
      setTenantName(tenant?.name || '');
      setTenantDescription(tenant?.description || '');
    }
  }, [tenants]);

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
