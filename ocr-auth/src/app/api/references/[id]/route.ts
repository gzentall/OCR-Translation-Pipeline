import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '../../auth/[...nextauth]/auth'
import ReferencesService from '@/lib/references-service'

const referencesService = new ReferencesService()

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const session = await getServerSession(authOptions)
    
    if (!session?.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    
    const reference = await referencesService.getById(params.id)
    
    if (!reference) {
      return NextResponse.json(
        { error: 'Reference not found' },
        { status: 404 }
      )
    }
    
    return NextResponse.json({
      success: true,
      reference
    })
  } catch (error) {
    console.error('Error fetching reference:', error)
    return NextResponse.json(
      { error: 'Failed to fetch reference' },
      { status: 500 }
    )
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const session = await getServerSession(authOptions)
    
    if (!session?.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    
    // Only admins can update references
    if ((session.user as any).role !== 'SUPER_ADMIN' && (session.user as any).role !== 'ADMIN') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
    }
    
    const body = await request.json()
    const { canonicalName, type, notes } = body
    
    const reference = await referencesService.update(params.id, {
      canonicalName,
      type,
      notes
    })
    
    if (!reference) {
      return NextResponse.json(
        { error: 'Reference not found' },
        { status: 404 }
      )
    }
    
    return NextResponse.json({
      success: true,
      reference
    })
  } catch (error) {
    console.error('Error updating reference:', error)
    return NextResponse.json(
      { error: 'Failed to update reference' },
      { status: 500 }
    )
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const session = await getServerSession(authOptions)
    
    if (!session?.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    
    // Only super admins can delete references
    if ((session.user as any).role !== 'SUPER_ADMIN') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
    }
    
    const success = await referencesService.delete(params.id)
    
    if (!success) {
      return NextResponse.json(
        { error: 'Failed to delete reference or reference has linked documents' },
        { status: 400 }
      )
    }
    
    return NextResponse.json({
      success: true,
      message: 'Reference deleted successfully'
    })
  } catch (error) {
    console.error('Error deleting reference:', error)
    return NextResponse.json(
      { error: 'Failed to delete reference' },
      { status: 500 }
    )
  }
}

