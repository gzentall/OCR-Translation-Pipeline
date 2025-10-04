import { NextRequest, NextResponse } from "next/server"
import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth"
import { PrismaClient } from "@prisma/client"

const prisma = new PrismaClient()

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const session = await getServerSession(authOptions)
    if (!session?.user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    }

    const userId = params.id
    const { searchParams } = new URL(request.url)
    const page = parseInt(searchParams.get("page") || "1")
    const limit = parseInt(searchParams.get("limit") || "100")
    const startDate = searchParams.get("startDate")
    const endDate = searchParams.get("endDate")
    const eventType = searchParams.get("eventType")

    // Verify user has access to this user's history (either own history or admin)
    const isOwnHistory = (session.user as any).id === userId
    const isAdmin = (session.user as any).role === "SUPER_ADMIN" || (session.user as any).role === "ADMIN"
    
    if (!isOwnHistory && !isAdmin) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 })
    }

    // Build where clause for filtering
    const whereClause: any = {
      actorUserId: userId
    }

    if (startDate || endDate) {
      whereClause.createdAt = {}
      if (startDate) {
        whereClause.createdAt.gte = new Date(startDate)
      }
      if (endDate) {
        whereClause.createdAt.lte = new Date(endDate)
      }
    }

    if (eventType && eventType !== "all") {
      whereClause.action = eventType
    }

    // Get total count for pagination
    const totalCount = await prisma.auditLog.count({ where: whereClause })

    // Get paginated results
    const auditLogs = await prisma.auditLog.findMany({
      where: whereClause,
      include: {
        document: {
          select: {
            id: true,
            title: true
          }
        },
        person: {
          select: {
            id: true,
            name: true
          }
        }
      },
      orderBy: {
        createdAt: "desc"
      },
      skip: (page - 1) * limit,
      take: limit
    })

    // Format the results for the frontend
    const formattedLogs = auditLogs.map(log => {
      const action = formatAction(log.action)
      let object = ""
      
      if (log.targetType === "DOCUMENT" && log.document) {
        object = `"${log.document.title}"`
      } else if (log.targetType === "PERSON" && log.person) {
        object = `"${log.person.name}"`
      } else if (log.targetType === "USER") {
        object = "profile"
      }
      
      return {
        id: log.id,
        timestamp: log.createdAt,
        description: `${action}${object}`,
        action: log.action,
        targetType: log.targetType,
        targetId: log.targetId,
        metadata: log.metadata
      }
    })

    return NextResponse.json({
      success: true,
      data: formattedLogs,
      pagination: {
        page,
        limit,
        total: totalCount,
        totalPages: Math.ceil(totalCount / limit)
      }
    })

  } catch (error) {
    console.error("Error fetching user history:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}

function formatAction(action: string): string {
  const actionMap: { [key: string]: string } = {
    "DOCUMENT_CREATE": "created document",
    "DOCUMENT_UPDATE": "modified document",
    "DOCUMENT_DELETE": "deleted document",
    "DOCUMENT_VIEW": "viewed document",
    "DOCUMENT_TRANSLATE": "translated document",
    "DOCUMENT_PROCESS": "processed document",
    "DOCUMENT_SUMMARY_UPDATE": "updated document summary",
    "DOCUMENT_PEOPLE_UPDATE": "updated document people",
    "USER_LOGIN": "logged in",
    "USER_LOGOUT": "logged out",
    "USER_UPDATE": "updated",
    "PERSON_CREATE": "created person",
    "PERSON_UPDATE": "updated person",
    "PERSON_DELETE": "deleted person"
  }
  
  return actionMap[action] || action.toLowerCase().replace(/_/g, " ")
}

