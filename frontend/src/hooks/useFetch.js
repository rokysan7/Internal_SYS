import { useState, useEffect, useCallback } from 'react';

/**
 * Generic API fetch hook with loading and error state management.
 * @param {Function} fetchFn - Async function that returns data
 * @param {Array} deps - Dependency array to trigger refetch
 * @param {Object} options - Options { immediate: boolean, onSuccess: fn, onError: fn }
 * @returns {Object} { data, loading, error, refetch }
 */
export default function useFetch(fetchFn, deps = [], options = {}) {
  const { immediate = true, onSuccess, onError } = options;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState(null);

  const execute = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchFn();
      setData(result);
      onSuccess?.(result);
      return result;
    } catch (err) {
      setError(err);
      onError?.(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchFn, onSuccess, onError]);

  useEffect(() => {
    if (immediate) {
      execute().catch(() => {});
    }
  }, [...deps, immediate]);

  const refetch = useCallback(() => {
    return execute();
  }, [execute]);

  return { data, loading, error, refetch, setData };
}
