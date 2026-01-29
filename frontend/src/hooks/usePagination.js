import { useState, useCallback } from 'react';

/**
 * Pagination state management hook.
 * @param {number} initialPage - Initial page number (default: 1)
 * @returns {Object} Pagination state and handlers
 */
export default function usePagination(initialPage = 1) {
  const [page, setPage] = useState(initialPage);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  const resetPage = useCallback(() => {
    setPage(1);
  }, []);

  const updateFromResponse = useCallback((response) => {
    if (response.total_pages !== undefined) {
      setTotalPages(response.total_pages);
    }
    if (response.total !== undefined) {
      setTotal(response.total);
    }
  }, []);

  const goToPage = useCallback((newPage) => {
    setPage(Math.max(1, Math.min(newPage, totalPages)));
  }, [totalPages]);

  const nextPage = useCallback(() => {
    if (page < totalPages) setPage((p) => p + 1);
  }, [page, totalPages]);

  const prevPage = useCallback(() => {
    if (page > 1) setPage((p) => p - 1);
  }, [page]);

  return {
    page,
    totalPages,
    total,
    setPage,
    setTotalPages,
    setTotal,
    resetPage,
    updateFromResponse,
    goToPage,
    nextPage,
    prevPage,
    hasNextPage: page < totalPages,
    hasPrevPage: page > 1,
  };
}
