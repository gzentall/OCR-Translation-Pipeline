# Hybrid OCR System Setup Guide

This guide will help you set up the hybrid Next.js + Flask architecture for your OCR document processing system.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Next.js Frontend (Vercel)                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Auth UI   │  │ Document UI │  │   User Management   │  │
│  │ - Login     │  │ - Browse    │  │ - Invite Users      │  │
│  │ - Passkeys  │  │ - Upload    │  │ - Role Management   │  │
│  │ - Register  │  │ - Edit      │  │ - Audit Logs        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Flask API (Railway/Render)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Auth Proxy  │  │ OCR Pipeline│  │   Document API      │  │
│  │ - Validate  │  │ - Vision API│  │ - CRUD Operations   │  │
│  │ - Sessions  │  │ - Translate │  │ - People Management │  │
│  │ - Roles     │  │ - AI Process│  │ - Search/Export     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL Database (Neon)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Auth Tables │  │ Document    │  │   People Tables     │  │
│  │ - Users     │  │ Tables      │  │ - People            │  │
│  │ - Sessions  │  │ - Documents │  │ - Relationships     │  │
│  │ - Passkeys  │  │ - Metadata  │  │ - Document Links    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Setup Steps

### 1. Database Setup (Neon PostgreSQL)

1. **Create Neon Account**: Go to [neon.tech](https://neon.tech) and create an account
2. **Create Database**: Create a new PostgreSQL database
3. **Get Connection String**: Copy the connection string (it looks like `postgresql://username:password@host/database`)

### 2. Next.js Auth System Setup

1. **Navigate to auth directory**:
   ```bash
   cd ocr-auth
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Set up environment variables**:
   ```bash
   cp env.example .env.local
   ```
   
   Edit `.env.local` with your values:
   ```env
   DATABASE_URL="your-neon-connection-string"
   NEXTAUTH_SECRET="your-random-secret-key"
   NEXTAUTH_URL="http://localhost:3000"
   RESEND_API_KEY="your-resend-api-key"
   APP_URL="http://localhost:3000"
   FLASK_API_URL="http://localhost:5001"
   SEED_SUPERADMIN_EMAIL="admin@yourdomain.com"
   SEED_SUPERADMIN_USERNAME="admin"
   SEED_SUPERADMIN_PASSWORD="your-secure-password"
   ```

4. **Set up database**:
   ```bash
   npx prisma generate
   npx prisma migrate dev
   npm run db:seed
   ```

5. **Start development server**:
   ```bash
   npm run dev
   ```

### 3. Flask API Setup

1. **Install Python dependencies**:
   ```bash
   pip3 install flask-cors pyjwt
   ```

2. **Set environment variables**:
   ```bash
   export NEXTAUTH_SECRET="same-secret-as-nextjs"
   export NEXTAUTH_URL="http://localhost:3000"
   ```

3. **Start Flask API**:
   ```bash
   python3 flask_api.py
   ```

### 4. Email Service Setup (Resend)

1. **Create Resend Account**: Go to [resend.com](https://resend.com)
2. **Get API Key**: Create an API key in your dashboard
3. **Add to environment**: Add the API key to your `.env.local` file

## Testing the System

### 1. Test Authentication

1. **Start both services**:
   ```bash
   # Terminal 1: Next.js
   cd ocr-auth && npm run dev
   
   # Terminal 2: Flask API
   python3 flask_api.py
   ```

2. **Access the application**:
   - Go to `http://localhost:3000`
   - You should be redirected to login
   - Use your super admin credentials to log in

### 2. Test Document Upload

1. **Login as admin**
2. **Upload a PDF document**
3. **Verify OCR processing works**
4. **Check document appears in the list**

### 3. Test User Management

1. **Login as super admin**
2. **Go to Admin Panel** (`/admin`)
3. **Verify you can see user list**
4. **Test role-based access**

## Deployment

### 1. Deploy Next.js to Vercel

1. **Connect GitHub repository to Vercel**
2. **Set environment variables in Vercel dashboard**
3. **Deploy automatically on push**

### 2. Deploy Flask API to Railway

1. **Create Railway account**
2. **Connect GitHub repository**
3. **Set environment variables**
4. **Deploy automatically**

### 3. Configure Production URLs

Update environment variables with production URLs:
- `NEXTAUTH_URL`: Your Vercel app URL
- `FLASK_API_URL`: Your Railway app URL
- `APP_URL`: Your Vercel app URL

## Security Features

- ✅ **JWT Authentication**: Secure token-based auth
- ✅ **Role-Based Access Control**: SUPER_ADMIN, ADMIN, USER roles
- ✅ **CORS Protection**: Configured for frontend-backend communication
- ✅ **Password Hashing**: Argon2id for secure password storage
- ✅ **Email Verification**: Required for account activation
- ✅ **Session Management**: Secure JWT sessions

## API Endpoints

### Authentication Required
All endpoints require a valid JWT token in the Authorization header:
```
Authorization: Bearer <jwt-token>
```

### Document Endpoints
- `GET /api/documents` - List all documents
- `GET /api/documents/<id>` - Get specific document
- `POST /api/documents` - Upload and process document
- `PUT /api/documents/<id>` - Update document (Admin only)
- `DELETE /api/documents/<id>` - Delete document (Admin only)

### People Endpoints
- `GET /api/people` - List all people
- `POST /api/people` - Add person (Admin only)

### Utility Endpoints
- `GET /api/health` - Health check
- `GET /api/download/<filename>` - Download processed files

## Troubleshooting

### Common Issues

1. **Database Connection Failed**:
   - Check `DATABASE_URL` format
   - Ensure database is accessible from your IP

2. **Authentication Errors**:
   - Verify `NEXTAUTH_SECRET` matches between services
   - Check JWT token format

3. **CORS Errors**:
   - Ensure Flask API allows your Next.js origin
   - Check `FLASK_API_URL` is correct

4. **Email Not Sending**:
   - Verify `RESEND_API_KEY` is valid
   - Check domain configuration in Resend

### Development Tips

1. **Use different ports**: Next.js (3000), Flask API (5001)
2. **Check logs**: Both services provide detailed error logs
3. **Test incrementally**: Start with auth, then add document features
4. **Use browser dev tools**: Check network requests and responses

## Next Steps

1. **Add WebAuthn/Passkeys**: Implement biometric authentication
2. **Real-time Updates**: Add WebSocket support for live updates
3. **Advanced Search**: Implement full-text search across documents
4. **Export Features**: Add PDF export and data export capabilities
5. **Audit Logging**: Implement comprehensive audit trails

## Support

If you encounter issues:
1. Check the logs in both services
2. Verify environment variables are set correctly
3. Test each component individually
4. Check network connectivity between services

