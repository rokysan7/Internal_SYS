# CS Dashboard Frontend

Internal CS (Customer Support) Case Management System - Frontend

## Tech Stack

- React 19 + Vite
- React Router DOM
- Axios

## Getting Started

```bash
npm install
npm run dev      # Development server
npm run build    # Production build
```

## Project Structure

```
src/
├── api/              # API modules (cases, products, licenses, memos)
├── components/       # Reusable UI components
│   ├── CaseDetail/   # Case detail sub-components
│   └── index.js      # Barrel exports
├── hooks/            # Custom React hooks
│   └── index.js      # Barrel exports
├── pages/            # Page components
│   ├── shared.css    # Shared styles
│   └── [Page].css    # Page-specific styles
├── App.jsx
└── main.jsx
```

## Changelog

### v1.0.2 (2026-01-29)

**Frontend Refactoring** - Improved modularity and reusability

- **CaseDetail**: Split into 5 sub-components (DescriptionCard, CommentsCard, InfoCard, ChecklistCard)
- **ProductPage**: Extracted ProductCreateForm, BulkUploadForm components
- **CSS**: Split pages.css into shared.css + page-specific CSS files
- **Hooks**: Added custom hooks (useDebounce, usePagination, useFetch)
- **Barrel Exports**: Added index.js for components and hooks

### v1.0.1

- Initial release with core features
