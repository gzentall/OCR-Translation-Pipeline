import { NextRequest, NextResponse } from "next/server"
import { PrismaClient } from "@prisma/client"
import { hash } from "@node-rs/argon2"
import { Resend } from "resend"

const prisma = new PrismaClient()
const resend = new Resend(process.env.RESEND_API_KEY)

export async function POST(request: NextRequest) {
  try {
    const { username, email, password } = await request.json()

    // Validate input
    if (!username || !email || !password) {
      return NextResponse.json(
        { error: "Username, email, and password are required" },
        { status: 400 }
      )
    }

    // Check if user already exists
    const existingUser = await prisma.user.findFirst({
      where: {
        OR: [
          { username },
          { email }
        ]
      }
    })

    if (existingUser) {
      return NextResponse.json(
        { error: "Username or email already exists" },
        { status: 400 }
      )
    }

    // Hash password
    const passwordHash = await hash(password)

    // Create user
    await prisma.user.create({
      data: {
        username,
        email,
        passwordHash,
        role: "USER", // Default role
        isActive: false, // Will be activated after email verification
      }
    })

    // Generate verification token
    const verificationToken = crypto.randomUUID()
    const expiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000) // 24 hours

    await prisma.verificationToken.create({
      data: {
        identifier: email,
        token: verificationToken,
        expires: expiresAt
      }
    })

    // Send verification email
    try {
      await resend.emails.send({
        from: "noreply@yourdomain.com", // Replace with your domain
        to: email,
        subject: "Verify your account",
        html: `
          <h1>Welcome to OCR Auth!</h1>
          <p>Please click the link below to verify your account:</p>
          <a href="${process.env.APP_URL}/verify?token=${verificationToken}">
            Verify Account
          </a>
          <p>This link will expire in 24 hours.</p>
        `
      })
    } catch (emailError) {
      console.error("Failed to send verification email:", emailError)
      // Don't fail registration if email fails
    }

    return NextResponse.json(
      { message: "Registration successful. Please check your email to verify your account." },
      { status: 201 }
    )

  } catch (error) {
    console.error("Registration error:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}

