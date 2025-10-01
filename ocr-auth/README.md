# OCR Auth System

A Next.js authentication system for the OCR Document Processing application. This provides user management, role-based access control, and secure authentication for the hybrid Flask + Next.js architecture.

## Features

- **User Authentication**: Username/password login with NextAuth.js
- **Role-Based Access Control**: SUPER_ADMIN, ADMIN, USER roles
- **Email Verification**: Account activation via email links
- **User Management**: Admin panel for user management (SuperAdmin only)
- **Secure Sessions**: JWT-based sessions with proper security
- **Database Integration**: PostgreSQL with Prisma ORM

## Architecture

This is the frontend authentication layer that works with your existing Flask OCR backend:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Next.js       │    │   Flask API      │    │   Database      │
│   (Auth + UI)   │◄──►│   (OCR Pipeline) │◄──►│   (PostgreSQL)  │
│   - Login/Reg   │    │   - Vision API   │    │   - Auth Data   │
│   - User Mgmt   │    │   - Translation  │    │   - Documents   │
│   - Admin Panel │    │   - AI Process   │    │   - People      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Setup

### 1. Environment Variables

Copy `env.example` to `.env.local` and configure:

```bash
cp env.example .env.local
```

Required variables:
- `DATABASE_URL`: PostgreSQL connection string
- `NEXTAUTH_SECRET`: Random secret for JWT signing
- `NEXTAUTH_URL`: Your app URL (http://localhost:3000 for dev)
- `RESEND_API_KEY`: For sending verification emails
- `SEED_SUPERADMIN_*`: Initial admin user credentials

### 2. Database Setup

```bash
# Generate Prisma client
npx prisma generate

# Run database migrations
npx prisma migrate dev

# Seed the database with super admin user
npm run db:seed
```

### 3. Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

## User Roles

- **SUPER_ADMIN**: Full system access, user management, cannot be deleted
- **ADMIN**: Can edit documents and people, no user management access
- **USER**: Read-only access to documents and people

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/verify` - Email verification
- `GET/POST /api/auth/[...nextauth]` - NextAuth.js endpoints

### Admin (SuperAdmin only)
- `GET /api/admin/users` - List all users

## Pages

- `/` - Dashboard (authenticated users)
- `/login` - Login page
- `/register` - Registration page
- `/verify` - Email verification
- `/admin` - Admin panel (SuperAdmin only)

## Integration with Flask Backend

The Next.js frontend will communicate with your Flask backend via API calls. The Flask backend should:

1. **Validate JWT tokens** from Next.js sessions
2. **Check user roles** for authorization
3. **Handle OCR processing** as it currently does
4. **Store document data** in the shared PostgreSQL database

## Deployment

### Vercel (Frontend)
1. Connect your GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push

### Database (Neon)
1. Create a Neon PostgreSQL database
2. Update `DATABASE_URL` in environment variables
3. Run migrations: `npx prisma migrate deploy`

### Flask Backend
Deploy your Flask app to Railway, Render, or similar service with:
- Access to the same PostgreSQL database
- Environment variables for database connection
- CORS configuration for Next.js frontend

## Security Features

- **Password Hashing**: Argon2id for secure password storage
- **JWT Sessions**: Secure, stateless session management
- **Email Verification**: Required for account activation
- **Role-Based Access**: Granular permissions system
- **CSRF Protection**: Built-in with NextAuth.js
- **Rate Limiting**: Can be added via middleware

## Next Steps

1. **Set up database** and run migrations
2. **Configure email service** (Resend)
3. **Create super admin user** via seed script
4. **Test authentication flow**
5. **Integrate with Flask backend**
6. **Deploy to production**

## Troubleshooting

- **Database connection issues**: Check `DATABASE_URL` format
- **Email not sending**: Verify `RESEND_API_KEY` and domain setup
- **Authentication errors**: Check `NEXTAUTH_SECRET` is set
- **Role access denied**: Ensure user has correct role in database