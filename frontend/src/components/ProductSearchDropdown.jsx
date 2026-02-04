import { useState, useEffect, useRef } from 'react';
import { getAllProducts } from '../api/products';

/**
 * Searchable product dropdown for forms.
 * @param {Object} props
 * @param {number|string} props.value - Selected product_id
 * @param {Function} props.onChange - Called with product_id on select/clear
 */
export default function ProductSearchDropdown({ value, onChange }) {
  const [products, setProducts] = useState([]);
  const [search, setSearch] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const ref = useRef(null);
  const listboxId = 'product-search-listbox';

  useEffect(() => {
    getAllProducts().then((res) => setProducts(res.data)).catch(() => {});
  }, []);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (ref.current && !ref.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const filtered = products.filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase())
  );

  const handleSelect = (product) => {
    onChange(product.id);
    setSearch(product.name);
    setShowDropdown(false);
    setActiveIndex(-1);
  };

  const handleClear = () => {
    onChange('');
    setSearch('');
    setActiveIndex(-1);
  };

  const handleKeyDown = (e) => {
    if (!showDropdown || filtered.length === 0) {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        setShowDropdown(true);
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setActiveIndex((prev) => (prev < filtered.length - 1 ? prev + 1 : 0));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setActiveIndex((prev) => (prev > 0 ? prev - 1 : filtered.length - 1));
        break;
      case 'Enter':
        e.preventDefault();
        if (activeIndex >= 0 && activeIndex < filtered.length) {
          handleSelect(filtered[activeIndex]);
        }
        break;
      case 'Escape':
        setShowDropdown(false);
        setActiveIndex(-1);
        break;
    }
  };

  // Reset active index when filtered list changes
  useEffect(() => {
    setActiveIndex(-1);
  }, [search]);

  const activeDescendant = activeIndex >= 0 && filtered[activeIndex]
    ? `product-option-${filtered[activeIndex].id}`
    : undefined;

  return (
    <div className="form-group" ref={ref} style={{ position: 'relative' }}>
      <label htmlFor="product-search">Product</label>
      <div style={{ display: 'flex', gap: '0.25rem' }}>
        <input
          id="product-search"
          type="text"
          placeholder="Search product..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setShowDropdown(true);
            if (!e.target.value) handleClear();
          }}
          onFocus={() => setShowDropdown(true)}
          onKeyDown={handleKeyDown}
          role="combobox"
          aria-expanded={showDropdown}
          aria-controls={listboxId}
          aria-autocomplete="list"
          aria-activedescendant={activeDescendant}
          style={{ flex: 1 }}
        />
        {value && (
          <button type="button" className="btn btn-secondary" onClick={handleClear} aria-label="Clear product selection">
            ✕
          </button>
        )}
      </div>
      {showDropdown && (
        <div
          id={listboxId}
          role="listbox"
          aria-label="Product list"
          style={{
            position: 'absolute', top: '100%', left: 0, right: 0,
            background: 'var(--bg-secondary, #fff)', border: '1px solid var(--border-color, #ddd)',
            borderRadius: 4, maxHeight: 200, overflowY: 'auto', zIndex: 10,
          }}
        >
          {filtered.length === 0 ? (
            <div style={{ padding: '0.5rem', color: '#888' }}>No results</div>
          ) : (
            filtered.map((p, idx) => (
              <div
                key={p.id}
                id={`product-option-${p.id}`}
                role="option"
                aria-selected={value === p.id}
                onClick={() => handleSelect(p)}
                style={{
                  padding: '0.5rem', cursor: 'pointer',
                  background: idx === activeIndex
                    ? 'var(--hover-bg, #f5f5f5)'
                    : value === p.id
                      ? 'var(--accent-light, #e3f2fd)'
                      : 'transparent',
                }}
                onMouseEnter={() => setActiveIndex(idx)}
              >
                {p.name}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
