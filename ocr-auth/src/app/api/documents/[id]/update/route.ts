import { NextRequest, NextResponse } from "next/server"
import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth"
import { PrismaClient } from "@prisma/client"
import { logAuditEvent, AUDIT_ACTIONS } from "@/lib/audit"

const prisma = new PrismaClient()

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const session = await getServerSession(authOptions)
    if (!session?.user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    }

    const documentId = params.id
    const data = await request.json()

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

    // Update the document
    const updatedDocument = await prisma.document.update({
      where: { id: documentId },
      data: {
        title: data.title,
        summary: data.summary,
        translatedText: data.translatedText,
        updatedAt: new Date()
      }
    })

    // Log the update event
    await logAuditEvent({
      actorUserId: (session.user as any).id,
      action: AUDIT_ACTIONS.DOCUMENT_UPDATE,
      targetType: "DOCUMENT",
      targetId: documentId,
      metadata: {
        changes: Object.keys(data),
        previousTitle: document.title,
        newTitle: data.title,
        timestamp: new Date().toISOString()
      }
    })

    return NextResponse.json({
      success: true,
      document: updatedDocument
    })

  } catch (error) {
    console.error("Error updating document:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}

