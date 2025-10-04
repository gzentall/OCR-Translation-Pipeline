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
    
    // Only admins can convert references
    if ((session.user as any).role !== 'SUPER_ADMIN' && (session.user as any).role !== 'ADMIN') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
    }
    
    const body = await request.json()
    const { sourceParentId, targetParentId, childLabel } = body
    
    if (!sourceParentId || !targetParentId) {
      return NextResponse.json(
        { error: 'sourceParentId and targetParentId are required' },
        { status: 400 }
      )
    }
    
    if (sourceParentId === targetParentId) {
      return NextResponse.json(
        { error: 'Cannot convert reference to itself' },
        { status: 400 }
      )
    }
    
    const success = await referencesService.convertParentToChild(
      sourceParentId,
      targetParentId,
      childLabel
    )
    
    if (!success) {
      return NextResponse.json(
        { error: 'Failed to convert reference' },
        { status: 400 }
      )
    }
    
    return NextResponse.json({
      success: true,
      message: 'Reference converted successfully'
    })
  } catch (error) {
    console.error('Error converting reference:', error)
    return NextResponse.json(
      { error: 'Failed to convert reference' },
      { status: 500 }
    )
  }
}

