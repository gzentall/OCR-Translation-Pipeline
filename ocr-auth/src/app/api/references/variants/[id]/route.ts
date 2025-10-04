import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '../../../auth/[...nextauth]/auth'
import ReferencesService from '@/lib/references-service'

const referencesService = new ReferencesService()

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const session = await getServerSession(authOptions)
    
    if (!session?.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    
    // Only admins can remove variants
    if ((session.user as any).role !== 'SUPER_ADMIN' && (session.user as any).role !== 'ADMIN') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
    }
    
    const success = await referencesService.removeChild(params.id)
    
    if (!success) {
      return NextResponse.json(
        { error: 'Failed to remove variant' },
        { status: 400 }
      )
    }
    
    return NextResponse.json({
      success: true,
      message: 'Variant removed successfully'
    })
  } catch (error) {
    console.error('Error removing variant:', error)
    return NextResponse.json(
      { error: 'Failed to remove variant' },
      { status: 500 }
    )
  }
}

