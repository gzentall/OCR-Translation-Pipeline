# Archived Applications

This directory contains alternative implementations and experimental versions that are not actively used.

## 📁 Contents

### Node.js Applications

#### `ocr-auth/` - Next.js Authentication Frontend
- **Purpose**: Modern authentication system with Next.js, Prisma, and NextAuth
- **Features**: User management, role-based access, email verification
- **Status**: Functional but not needed for the main Flask app
- **Tech Stack**: Next.js 15, Tailwind CSS, PostgreSQL (Neon)

#### `letters-mcp/` - MCP Server
- **Purpose**: Model Context Protocol server for document management
- **Features**: CRUD operations for documents and references
- **Status**: Optional integration tool
- **Tech Stack**: TypeScript, MCP SDK

### Flask Applications

#### `app_with_auth.py`
- Flask app with JWT authentication
- Includes CORS support
- Designed to work with Next.js frontend

#### `app_simple_auth.py`
- Flask app with simple session-based authentication
- Includes email verification via Resend API
- Self-contained user management

#### `flask_api.py`
- Flask API that integrates with Next.js auth system
- JWT token verification
- Designed as backend-only API

### Documentation

#### `HYBRID_SETUP.md`
- Setup guide for the hybrid Next.js + Flask architecture
- Deployment instructions
- API endpoint documentation

---

## 🎯 Why These Were Archived

The main Flask app (`app.py` in the project root) provides a simpler, self-contained solution that:
- ✅ Works without authentication complexity
- ✅ Uses Material Design 3 UI directly
- ✅ No Node.js dependencies
- ✅ Easier to maintain and deploy

These archived versions were experimental approaches to add:
- Multi-user authentication
- Modern frontend framework
- Role-based access control
- Microservices architecture

---

## 🔄 To Use These Again

If you want to use any of these archived applications:

### For Next.js Auth Frontend:
```bash
cd _archived/ocr-auth
npm install
npm run dev
```

### For MCP Server:
```bash
cd _archived/letters-mcp
npm install
npm run dev
```

### For Alternative Flask Apps:
```bash
# Copy back to root
cp _archived/app_with_auth.py .
# Then run
python3 app_with_auth.py
```

---

## 📝 Notes

- All these apps were functional at the time of archiving
- Dependencies may need updating if restored
- See individual app directories for specific setup instructions
- The main `app.py` in the project root is the recommended version

---

**Archived on:** November 11, 2025  
**Reason:** Simplifying project structure to focus on the working Flask app






