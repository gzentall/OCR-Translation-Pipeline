import { describe, it, expect, vi, beforeEach } from 'vitest';
import { healthCheck } from '../tools/health.js';
import { apiClient } from '../client.js';

// Mock the API client
vi.mock('../client.js', () => ({
  apiClient: {
    healthCheck: vi.fn(),
  },
}));

const mockApiClient = vi.mocked(apiClient);

describe('Health Tool', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('healthCheck', () => {
    it('should return healthy status when app is healthy', async () => {
      const mockResponse = {
        success: true,
        data: {
          status: 'healthy',
          timestamp: '2025-01-01T00:00:00Z',
          service: 'flask-ocr-api',
        },
      };

      mockApiClient.healthCheck.mockResolvedValue(mockResponse);

      const result = await healthCheck({});

      expect(result.status).toBe('ok');
      expect(result.message).toBe('Letters app and MCP server are healthy');
      expect(result.appVersion).toBe('flask-ocr-api');
      expect(result.timestamp).toBe('2025-01-01T00:00:00Z');
    });

    it('should return error status when app is unhealthy', async () => {
      const mockResponse = {
        success: false,
        error: 'Service unavailable',
      };

      mockApiClient.healthCheck.mockResolvedValue(mockResponse);

      const result = await healthCheck({});

      expect(result.status).toBe('error');
      expect(result.message).toBe('Letters app is not healthy: Service unavailable');
      expect(result.appVersion).toBe('unknown');
      expect(result.timestamp).toBeDefined();
    });

    it('should handle API errors', async () => {
      mockApiClient.healthCheck.mockRejectedValue(new Error('Network error'));

      const result = await healthCheck({});

      expect(result.status).toBe('error');
      expect(result.message).toBe('Network error');
      expect(result.appVersion).toBe('unknown');
      expect(result.timestamp).toBeDefined();
    });

    it('should handle missing timestamp in response', async () => {
      const mockResponse = {
        success: true,
        data: {
          status: 'healthy',
          service: 'flask-ocr-api',
        },
      };

      mockApiClient.healthCheck.mockResolvedValue(mockResponse);

      const result = await healthCheck({});

      expect(result.status).toBe('ok');
      expect(result.message).toBe('Letters app and MCP server are healthy');
      expect(result.appVersion).toBe('flask-ocr-api');
      expect(result.timestamp).toBeDefined(); // Should fallback to current timestamp
    });
  });
});
