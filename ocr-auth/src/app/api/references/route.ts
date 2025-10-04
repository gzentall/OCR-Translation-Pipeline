import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '../auth/[...nextauth]/auth'
import ReferencesService from '@/lib/references-service'

const referencesService = new ReferencesService()

export async function GET(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions)
    
    if (!session?.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    
    const { searchParams } = new URL(request.url)
    const query = searchParams.get('q') || undefined
    const type = searchParams.get('type') as any || undefined
    
    const references = await referencesService.search(query, type)
    
    return NextResponse.json({
      success: true,
      references,
      total: references.length
    })
  } catch (error) {
    console.error('Error fetching references:', error)
    return NextResponse.json(
      { error: 'Failed to fetch references' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions)
    
    if (!session?.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    
    // Only admins can create references
    if ((session.user as any).role !== 'SUPER_ADMIN' && (session.user as any).role !== 'ADMIN') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
    }
    
    const body = await request.json()
    const { canonicalName, type, notes, initialVariants } = body
    
    if (!canonicalName || !type) {
      return NextResponse.json(
        { error: 'canonicalName and type are required' },
        { status: 400 }
      )
    }
    
    const reference = await referencesService.create(
      canonicalName,
      type,
      notes,
      initialVariants || []
    )
    
    return NextResponse.json({
      success: true,
      reference
    })
  } catch (error) {
    console.error('Error creating reference:', error)
    return NextResponse.json(
      { error: 'Failed to create reference' },
      { status: 500 }
    )
  }
}

