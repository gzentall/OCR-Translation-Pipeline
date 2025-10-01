import { z } from 'zod';

// Environment configuration schema
const ConfigSchema = z.object({
  API_BASE_URL: z.string().url().default('http://localhost:5001'),
  API_TOKEN: z.string().optional(),
  TIMEOUT_MS: z.coerce.number().min(1000).max(300000).default(120000),
  MODE: z.enum(['http', 'local']).default('http'),
  AUTH_HEADER: z.string().optional(),
});

// Load and validate configuration
function loadConfig() {
  const rawConfig = {
    API_BASE_URL: process.env.API_BASE_URL,
    API_TOKEN: process.env.API_TOKEN,
    TIMEOUT_MS: process.env.TIMEOUT_MS,
    MODE: process.env.MODE,
    AUTH_HEADER: process.env.AUTH_HEADER,
  };

  try {
    return ConfigSchema.parse(rawConfig);
  } catch (error) {
    if (error instanceof z.ZodError) {
      const errorMessages = error.errors.map(err => 
        `${err.path.join('.')}: ${err.message}`
      ).join(', ');
      throw new Error(`Configuration validation failed: ${errorMessages}`);
    }
    throw error;
  }
}

export const config = loadConfig();

// Helper function to get API headers
export function getApiHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (config.API_TOKEN) {
    headers['Authorization'] = `Bearer ${config.API_TOKEN}`;
  }

  if (config.AUTH_HEADER) {
    headers['Authorization'] = config.AUTH_HEADER;
  }

  return headers;
}

// Helper function to build API URL
export function buildApiUrl(endpoint: string): string {
  const baseUrl = config.API_BASE_URL.replace(/\/$/, '');
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${baseUrl}${cleanEndpoint}`;
}

// Logging helper
export function logCall(toolName: string, duration: number, result: 'success' | 'error') {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] MCP Call: ${toolName} - ${duration}ms - ${result}`);
}

export type Config = z.infer<typeof ConfigSchema>;
