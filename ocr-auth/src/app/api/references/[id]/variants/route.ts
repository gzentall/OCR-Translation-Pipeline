import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '../../../auth/[...nextauth]/auth'
import ReferencesService from '@/lib/references-service'

const referencesService = new ReferencesService()

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const session = await getServerSession(authOptions)
    
    if (!session?.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    
    // Only admins can add variants
    if ((session.user as any).role !== 'SUPER_ADMIN' && (session.user as any).role !== 'ADMIN') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
    }
    
    const body = await request.json()
    const { label } = body
    
    if (!label) {
      return NextResponse.json(
        { error: 'label is required' },
        { status: 400 }
      )
    }
    
    const success = await referencesService.addChild(params.id, label)
    
    if (!success) {
      return NextResponse.json(
        { error: 'Failed to add variant' },
        { status: 400 }
      )
    }
    
    return NextResponse.json({
      success: true,
      message: 'Variant added successfully'
    })
  } catch (error) {
    console.error('Error adding variant:', error)
    return NextResponse.json(
      { error: 'Failed to add variant' },
      { status: 500 }
    )
  }
}

