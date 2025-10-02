# Nina Admin Console

Internal operations dashboard for platform administrators.

## Features

- **Analytics Dashboard**: Real-time platform metrics and business intelligence
- **Team Management**: Monitor and manage all teams
- **User Management**: View and manage user accounts
- **Admin Authentication**: Secure admin-only access

## Tech Stack

- React 18 + TypeScript
- Vite (build tool)
- TailwindCSS (styling)
- React Router (routing)
- Recharts (data visualization)

## Development

```bash
# Install dependencies
npm install

# Start dev server (port 8102)
npm run dev

# Type check
npm run type-check

# Lint
npm run lint

# Build for production
npm run build
```

## Port

- Dev server: `http://localhost:8102`
- Distinct from customer app (8101)

## Integration

- Connects to `/admin-analytics` API endpoints
- Requires admin authentication
- SPEC-030: Admin-Level Analytics Console
- SPEC-068: Team Billing Portal (admin view)
