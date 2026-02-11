import { memo, useCallback, useEffect, useRef, useState } from 'react';
import { searchTags, suggestTags } from '../api/tags';
import useDebounce from '../hooks/useDebounce';

/**
 * Hashtag chip input with auto-complete and AI-powered suggestions.
 * @param {Object} props
 * @param {string[]} props.value - Currently selected tags
 * @param {(tags: string[]) => void} props.onChange - Tag change callback
 * @param {string} props.title - Case title for suggestions
 * @param {string} props.content - Case content for suggestions
 */
function TagInput({ value = [], onChange, title = '', content = '' }) {
  const [inputValue, setInputValue] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const inputRef = useRef(null);
  const wrapperRef = useRef(null);

  const debouncedInput = useDebounce(inputValue, 300);
  const debouncedTitle = useDebounce(title, 500);
  const debouncedContent = useDebounce(content, 500);

  // Auto-complete search
  useEffect(() => {
    if (debouncedInput.trim().length < 1) {
      setSearchResults([]);
      setShowDropdown(false);
      return;
    }
    searchTags(debouncedInput.trim())
      .then((res) => {
        const filtered = res.data.filter((t) => !value.includes(t.name));
        setSearchResults(filtered);
        setShowDropdown(filtered.length > 0);
      })
      .catch(() => setSearchResults([]));
  }, [debouncedInput, value]);

  // Tag suggestions based on title + content
  useEffect(() => {
    if (debouncedTitle.trim().length < 2) {
      setSuggestions([]);
      return;
    }
    suggestTags(debouncedTitle.trim(), debouncedContent.trim())
      .then((res) => {
        const filtered = res.data.filter((t) => !value.includes(t.name));
        setSuggestions(filtered);
      })
      .catch(() => setSuggestions([]));
  }, [debouncedTitle, debouncedContent, value]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const addTag = useCallback((tagName) => {
    const normalized = tagName.trim();
    if (!normalized || value.includes(normalized)) return;
    onChange([...value, normalized]);
    setInputValue('');
    setShowDropdown(false);
    setActiveIndex(-1);
    inputRef.current?.focus();
  }, [value, onChange]);

  const removeTag = useCallback((tagName) => {
    onChange(value.filter((t) => t !== tagName));
  }, [value, onChange]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      if (activeIndex >= 0 && activeIndex < searchResults.length) {
        addTag(searchResults[activeIndex].name);
      } else if (inputValue.trim()) {
        addTag(inputValue);
      }
    } else if (e.key === 'Backspace' && !inputValue && value.length > 0) {
      removeTag(value[value.length - 1]);
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex((prev) => Math.min(prev + 1, searchResults.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex((prev) => Math.max(prev - 1, -1));
    } else if (e.key === 'Escape') {
      setShowDropdown(false);
      setActiveIndex(-1);
    }
  };

  return (
    <div className="tag-input-wrapper" ref={wrapperRef}>
      <div className="tag-input-chips">
        {value.map((tag) => (
          <span key={tag} className="tag-chip">
            #{tag}
            <button
              type="button"
              onClick={() => removeTag(tag)}
              aria-label={`Remove tag ${tag}`}
            >
              &times;
            </button>
          </span>
        ))}
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => { if (searchResults.length > 0) setShowDropdown(true); }}
          placeholder={value.length === 0 ? 'Type tag name...' : ''}
          className="tag-input-field"
          aria-label="Tag input"
          aria-expanded={showDropdown}
          role="combobox"
          aria-autocomplete="list"
        />
      </div>

      {showDropdown && searchResults.length > 0 && (
        <ul className="tag-dropdown" role="listbox">
          {searchResults.map((item, idx) => (
            <li
              key={item.name}
              className={`tag-dropdown-item${idx === activeIndex ? ' active' : ''}`}
              onClick={() => addTag(item.name)}
              role="option"
              aria-selected={idx === activeIndex}
            >
              <span className="tag-dropdown-name">#{item.name}</span>
              <span className="tag-dropdown-count">{item.usage_count} cases</span>
            </li>
          ))}
        </ul>
      )}

      {suggestions.length > 0 && (
        <div className="tag-suggestions">
          <span className="tag-suggestions-label">Suggested:</span>
          {suggestions.map((s) => (
            <button
              key={s.name}
              type="button"
              className="tag-suggestion-badge"
              onClick={() => addTag(s.name)}
              title={`Score: ${s.score}, Used in ${s.usage_count} cases`}
            >
              #{s.name}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default memo(TagInput);
