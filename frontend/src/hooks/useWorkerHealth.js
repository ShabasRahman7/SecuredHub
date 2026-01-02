import { useState, useCallback, useEffect, useRef } from 'react';
import api from '../api/axios';
import { API_ENDPOINTS } from '../constants/api';

// in-memory cache shared across hook instances
let cachedHealth = null;
let cachedAt = 0;
const CACHE_TTL_MS = 60000; // 60 seconds

const useWorkerHealth = ({ auto = false } = {}) => {
  const [data, setData] = useState(() => cachedHealth);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const fetchedRef = useRef(false);

  const fetchHealth = useCallback(async ({ force = false } = {}) => {
    const now = Date.now();

    // use cache when recent and not forced
    if (!force && cachedHealth && now - cachedAt < CACHE_TTL_MS) {
      setData(cachedHealth);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await api.get(API_ENDPOINTS.WORKER_HEALTH);
      cachedHealth = res.data;
      cachedAt = Date.now();
      setData(res.data);
    } catch (err) {
      console.error('Failed to fetch worker health', err);
      setError(err.response?.data || { message: 'Failed to load worker health' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (auto && !cachedHealth && !fetchedRef.current) {
      fetchedRef.current = true;
      fetchHealth();
    }
  }, [auto, fetchHealth]);

  return {
    data,
    loading,
    error,
    refetch: () => fetchHealth({ force: true }),
  };
};

export default useWorkerHealth;
