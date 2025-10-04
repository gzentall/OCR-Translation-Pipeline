// import { NextAuthOptions } from "next-auth"

type NextAuthOptions = {
  providers: any[]
  session: any
  callbacks: any
  pages?: any
}
import CredentialsProvider from "next-auth/providers/credentials"
import { PrismaClient } from "@prisma/client"
import bcrypt from "bcryptjs"
import { logAuditEvent, AUDIT_ACTIONS } from "@/lib/audit"

const prisma = new PrismaClient()

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "credentials",
      credentials: {
        username: { label: "Username", type: "text" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        console.log("🔐 Auth attempt:", { username: credentials?.username })
        
        if (!credentials?.username || !credentials?.password) {
          console.log("❌ Missing credentials")
          return null
        }

        const user = await prisma.user.findFirst({
          where: {
            OR: [
              { username: credentials.username },
              { email: credentials.username }
            ],
            isActive: true
          }
        })

        console.log("👤 User found:", user ? { id: user.id, username: user.username, role: user.role } : "No user found")

        if (!user || !user.passwordHash) {
          console.log("❌ No user or password hash")
          return null
        }

        console.log("🔑 Comparing passwords...")
        console.log("🔑 Input password length:", credentials.password.length)
        console.log("🔑 Stored hash length:", user.passwordHash.length)
        console.log("🔑 Stored hash preview:", user.passwordHash.substring(0, 20) + "...")
        
        let isValidPassword = false
        try {
          isValidPassword = await bcrypt.compare(credentials.password, user.passwordHash)
          console.log("🔑 Password valid:", isValidPassword)
        } catch (error) {
          console.log("❌ Password comparison error:", error)
          return null
        }
        
        if (!isValidPassword) {
          console.log("❌ Invalid password")
          return null
        }

        console.log("✅ Authentication successful")
        
        // Log successful login
        await logAuditEvent({
          actorUserId: user.id,
          action: AUDIT_ACTIONS.USER_LOGIN,
          targetType: "USER",
          targetId: user.id,
          metadata: {
            loginMethod: "credentials",
            timestamp: new Date().toISOString()
          }
        })
        
        return {
          id: user.id,
          email: user.email,
          username: user.username,
          role: user.role,
          name: user.username
        }
      }
    })
  ],
  session: {
    strategy: "jwt"
  },
  callbacks: {
    async jwt({ token, user }: any) {
      if (user) {
        token.role = user.role
        token.username = user.username
      }
      return token
    },
    async session({ session, token }: any) {
      if (token) {
        session.user.id = token.sub!
        session.user.role = token.role as string
        session.user.username = token.username as string
      }
      return session
    }
  },
  events: {
    async signOut({ token }: any) {
      // Log logout event
      if (token?.sub) {
        await logAuditEvent({
          actorUserId: token.sub,
          action: AUDIT_ACTIONS.USER_LOGOUT,
          targetType: "USER",
          targetId: token.sub,
          metadata: {
            timestamp: new Date().toISOString()
          }
        })
      }
    }
  },
  pages: {
    signIn: "/login"
  }
}
