import { useState, useEffect } from 'react';
import { tenantService } from '../api/services/tenantService';
import { toast } from 'react-toastify';

export const useRepositories = (currentTenant) => {
  const [repositories, setRepositories] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (currentTenant) {
      fetchRepositories();
    }
  }, [currentTenant]);

  const fetchRepositories = async () => {
    if (!currentTenant) return;
    setLoading(true);
    try {
      const data = await tenantService.getRepositories(currentTenant.id);
      setRepositories(data.repositories || []);
    } catch (error) {
      console.error('Failed to fetch repositories', error);
    } finally {
      setLoading(false);
    }
  };

  const addRepository = async (repoData) => {
    if (!currentTenant) return;

    try {
      await tenantService.addRepository(currentTenant.id, repoData);
      toast.success('Repository added successfully');
      fetchRepositories();
      return true;
    } catch (error) {
      toast.error('Failed to add repository');
      return false;
    }
  };

  const deleteRepository = async (repoId) => {
    if (!currentTenant) return;

    try {
      await tenantService.deleteRepository(currentTenant.id, repoId);
      toast.success('Repository deleted');
      setRepositories(repositories.filter(r => r.id !== repoId));
      return true;
    } catch (error) {
      toast.error('Failed to delete repository');
      return false;
    }
  };

  const assignDevelopers = async (repoId, developerIds) => {
    if (!currentTenant) return;

    try {
      await tenantService.assignDevelopers(currentTenant.id, repoId, developerIds);
      toast.success('Developers assigned successfully');
      fetchRepositories();
      return true;
    } catch (error) {
      toast.error('Failed to assign developers');
      return false;
    }
  };

  return {
    repositories,
    loading,
    fetchRepositories,
    addRepository,
    deleteRepository,
    assignDevelopers,
  };
};
