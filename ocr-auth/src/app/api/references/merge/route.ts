import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '../../auth/[...nextauth]/auth'
import ReferencesService from '@/lib/references-service'

const referencesService = new ReferencesService()

export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions)
    
    if (!session?.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    
    // Only admins can merge references
    if ((session.user as any).role !== 'SUPER_ADMIN' && (session.user as any).role !== 'ADMIN') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
    }
    
    const body = await request.json()
    const { sourceId, targetId } = body
    
    if (!sourceId || !targetId) {
      return NextResponse.json(
        { error: 'sourceId and targetId are required' },
        { status: 400 }
      )
    }
    
    if (sourceId === targetId) {
      return NextResponse.json(
        { error: 'Cannot merge reference with itself' },
        { status: 400 }
      )
    }
    
    const success = await referencesService.mergeParents(sourceId, targetId)
    
    if (!success) {
      return NextResponse.json(
        { error: 'Failed to merge references' },
        { status: 400 }
      )
    }
    
    return NextResponse.json({
      success: true,
      message: 'References merged successfully'
    })
  } catch (error) {
    console.error('Error merging references:', error)
    return NextResponse.json(
      { error: 'Failed to merge references' },
      { status: 500 }
    )
  }
}

