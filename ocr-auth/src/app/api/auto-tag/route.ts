import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '../auth/[...nextauth]/auth'
import ContextAutoTagger from '@/lib/context-auto-tagger'

const autoTagger = new ContextAutoTagger()

export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions)
    
    if (!session?.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    
    // Only admins can run auto-tagging
    if ((session.user as any).role !== 'SUPER_ADMIN' && (session.user as any).role !== 'ADMIN') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
    }
    
    const body = await request.json()
    const { documentId, rebuild } = body
    
    if (documentId) {
      // Run auto-tagging for a specific document
      const result = await autoTagger.runForDocument(documentId)
      
      return NextResponse.json({
        success: true,
        result,
        message: `Auto-tagging completed for document ${documentId}`
      })
    } else {
      // Run batch auto-tagging
      const result = await autoTagger.runBatch({ rebuild: rebuild || false })
      
      return NextResponse.json({
        success: true,
        result,
        message: `Batch auto-tagging completed. Processed ${result.linked} references.`
      })
    }
  } catch (error) {
    console.error('Error running auto-tagging:', error)
    return NextResponse.json(
      { error: 'Failed to run auto-tagging' },
      { status: 500 }
    )
  }
}

