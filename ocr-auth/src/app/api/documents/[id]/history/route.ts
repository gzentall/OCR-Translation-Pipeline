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

    const documentId = params.id
    const { searchParams } = new URL(request.url)
    const page = parseInt(searchParams.get("page") || "1")
    const limit = parseInt(searchParams.get("limit") || "100")
    const startDate = searchParams.get("startDate")
    const endDate = searchParams.get("endDate")
    const eventType = searchParams.get("eventType")

    // Verify user has access to this document
    const document = await prisma.document.findFirst({
      where: {
        id: documentId,
        userId: (session.user as any).id
      }
    })

    if (!document) {
      return NextResponse.json({ error: "Document not found" }, { status: 404 })
    }

    // Build where clause for filtering
    const whereClause: any = {
      OR: [
        { targetType: "DOCUMENT", targetId: documentId },
        { actorUserId: (session.user as any).id }
      ]
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
        actor: {
          select: {
            id: true,
            username: true,
            email: true
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
      const actor = log.actor ? `${log.actor.username}` : "System"
      const action = formatAction(log.action)
      const object = log.targetType === "DOCUMENT" ? `"${document.title}"` : ""
      
      return {
        id: log.id,
        timestamp: log.createdAt,
        description: `${actor} ${action}${object}`,
        action: log.action,
        actor: log.actor,
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
    console.error("Error fetching document history:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}

function formatAction(action: string): string {
  const actionMap: { [key: string]: string } = {
    "DOCUMENT_CREATE": "created",
    "DOCUMENT_UPDATE": "modified",
    "DOCUMENT_DELETE": "deleted",
    "DOCUMENT_VIEW": "viewed",
    "DOCUMENT_TRANSLATE": "translated",
    "DOCUMENT_PROCESS": "processed",
    "DOCUMENT_SUMMARY_UPDATE": "updated summary for",
    "DOCUMENT_PEOPLE_UPDATE": "updated people for",
    "USER_LOGIN": "logged in",
    "USER_LOGOUT": "logged out",
    "USER_UPDATE": "updated profile",
    "PERSON_CREATE": "created person",
    "PERSON_UPDATE": "updated person",
    "PERSON_DELETE": "deleted person"
  }
  
  return actionMap[action] || action.toLowerCase().replace(/_/g, " ")
}

