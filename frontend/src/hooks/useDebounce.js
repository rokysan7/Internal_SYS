import { useState, useEffect } from 'react';

/**
 * Debounce a value by specified delay.
 * @param {any} value - The value to debounce
 * @param {number} delay - Debounce delay in milliseconds (default: 500)
 * @returns {any} The debounced value
 */
export default function useDebounce(value, delay = 500) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}
