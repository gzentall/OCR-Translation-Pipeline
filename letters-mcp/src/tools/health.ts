import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { apiClient } from '../client.js';
import {
  HealthCheckInputSchema,
  HealthCheckOutputSchema,
  type HealthCheckInput,
  type HealthCheckOutput,
} from '../schemas.js';

// Health check tool
export const healthCheckTool: Tool = {
  name: 'health_check',
  description: 'Check the health status of the Letters app and MCP server',
  inputSchema: {
    type: 'object',
    properties: {},
  },
};

export async function healthCheck(input: unknown): Promise<HealthCheckOutput> {
  try {
    const validatedInput = HealthCheckInputSchema.parse(input);
    
    // Check the Letters app health
    const response = await apiClient.healthCheck();
    
    if (!response.success) {
      return {
        status: 'error',
        message: `Letters app is not healthy: ${response.error || 'Unknown error'}`,
        appVersion: 'unknown',
        timestamp: new Date().toISOString(),
      };
    }

    return {
      status: 'ok',
      message: 'Letters app and MCP server are healthy',
      appVersion: response.data?.service || 'unknown',
      timestamp: response.data?.timestamp || new Date().toISOString(),
    };
  } catch (error) {
    return {
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error occurred',
      appVersion: 'unknown',
      timestamp: new Date().toISOString(),
    };
  }
}
