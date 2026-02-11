import client from './client';

/** Tag prefix search (auto-complete) */
export const searchTags = (query) =>
  client.get('/tags/search', { params: { q: query } });

/** Tag suggestion based on case title + content */
export const suggestTags = (title, content = '') =>
  client.get('/tags/suggest', { params: { title, content } });
