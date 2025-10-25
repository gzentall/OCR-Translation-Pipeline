import { NextRequest, NextResponse } from 'next/server'

const FLASK_URL = 'http://localhost:5001'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const resolvedParams = await params
  const path = resolvedParams.path.join('/')
  const url = new URL(`${FLASK_URL}/api/${path}`)
  
  // Forward query parameters
  request.nextUrl.searchParams.forEach((value, key) => {
    url.searchParams.set(key, value)
  })

  console.log('🔄 Proxying request to Flask:', url.toString())

  try {
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        // Forward relevant headers but don't modify content-type
        'User-Agent': request.headers.get('user-agent') || 'Next.js Proxy',
        'Accept': request.headers.get('accept') || '*/*',
      },
    })

    console.log('📡 Flask response status:', response.status)
    console.log('📡 Flask response content-type:', response.headers.get('content-type'))
    console.log('📡 Flask response content-length:', response.headers.get('content-length'))

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Flask request failed' },
        { status: response.status }
      )
    }

    // CRITICAL: Return raw response without parsing for binary data
    return new NextResponse(response.body, {
      status: response.status,
      headers: {
        'Content-Type': response.headers.get('content-type') || 'application/octet-stream',
        'Content-Length': response.headers.get('content-length') || '',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      },
    })
  } catch (error) {
    console.error('❌ Flask proxy error:', error)
    return NextResponse.json(
      { error: 'Failed to connect to Flask backend' },
      { status: 500 }
    )
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const resolvedParams = await params
  const path = resolvedParams.path.join('/')
  const url = new URL(`${FLASK_URL}/api/${path}`)
  
  // Forward query parameters
  request.nextUrl.searchParams.forEach((value, key) => {
    url.searchParams.set(key, value)
  })

  const body = await request.text()

  try {
    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        'Content-Type': request.headers.get('content-type') || 'application/json',
        'User-Agent': request.headers.get('user-agent') || 'Next.js Proxy',
      },
      body,
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Flask request failed' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('❌ Flask proxy error:', error)
    return NextResponse.json(
      { error: 'Failed to connect to Flask backend' },
      { status: 500 }
    )
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const resolvedParams = await params
  const path = resolvedParams.path.join('/')
  const url = new URL(`${FLASK_URL}/api/${path}`)
  
  // Forward query parameters
  request.nextUrl.searchParams.forEach((value, key) => {
    url.searchParams.set(key, value)
  })

  const body = await request.text()

  try {
    const response = await fetch(url.toString(), {
      method: 'PUT',
      headers: {
        'Content-Type': request.headers.get('content-type') || 'application/json',
        'User-Agent': request.headers.get('user-agent') || 'Next.js Proxy',
      },
      body,
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Flask request failed' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('❌ Flask proxy error:', error)
    return NextResponse.json(
      { error: 'Failed to connect to Flask backend' },
      { status: 500 }
    )
  }
}

// Handle OPTIONS for CORS
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  })
}
