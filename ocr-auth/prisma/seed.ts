import { PrismaClient } from "@prisma/client"
import bcrypt from "bcryptjs"

const prisma = new PrismaClient()

async function main() {
  const email = process.env.SEED_SUPERADMIN_EMAIL
  const username = process.env.SEED_SUPERADMIN_USERNAME
  const password = process.env.SEED_SUPERADMIN_PASSWORD

  if (!email || !username || !password) {
    console.error("Missing required environment variables for seeding")
    console.error("Please set: SEED_SUPERADMIN_EMAIL, SEED_SUPERADMIN_USERNAME, SEED_SUPERADMIN_PASSWORD")
    process.exit(1)
  }

  // Check if super admin already exists
  const existingAdmin = await prisma.user.findFirst({
    where: {
      OR: [
        { email },
        { username },
        { role: "SUPER_ADMIN" }
      ]
    }
  })

  if (existingAdmin) {
    console.log("Super admin user already exists")
    return
  }

  // Hash password
  const passwordHash = await bcrypt.hash(password, 12)

  // Create super admin user
  const superAdmin = await prisma.user.create({
    data: {
      email,
      username,
      passwordHash,
      role: "SUPER_ADMIN",
      isActive: true,
      emailVerifiedAt: new Date(),
    }
  })

  console.log("Super admin user created:", {
    id: superAdmin.id,
    email: superAdmin.email,
    username: superAdmin.username,
    role: superAdmin.role
  })
}

main()
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
