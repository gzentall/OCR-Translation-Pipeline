import { describe, it, expect, vi, beforeEach } from 'vitest';
import { letterAttachReference, letterDetachReference, letterListReferences } from '../tools/relations.js';
import { apiClient } from '../client.js';

// Mock the API client
vi.mock('../client.js', () => ({
  apiClient: {
    attachReferenceToLetter: vi.fn(),
    detachReferenceFromLetter: vi.fn(),
    listLetterReferences: vi.fn(),
  },
}));

const mockApiClient = vi.mocked(apiClient);

describe('Relations Tools', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('letterAttachReference', () => {
    it('should attach reference successfully', async () => {
      const mockResponse = {
        success: true,
        message: 'Reference ref_123 added to document doc_123',
      };

      mockApiClient.attachReferenceToLetter.mockResolvedValue(mockResponse);

      const result = await letterAttachReference({
        letterId: 'doc_123',
        referenceId: 'ref_123',
        role: 'sender',
      });

      expect(result.status).toBe('ok');
      expect(result.message).toBe('Reference ref_123 attached to letter doc_123');
      expect(result.relation).toEqual({
        letterId: 'doc_123',
        referenceId: 'ref_123',
        role: 'sender',
      });
    });

    it('should handle attach errors', async () => {
      mockApiClient.attachReferenceToLetter.mockResolvedValue({
        success: false,
        error: 'Attach failed',
      });

      const result = await letterAttachReference({
        letterId: 'doc_123',
        referenceId: 'ref_123',
      });

      expect(result.status).toBe('error');
      expect(result.message).toBe('Attach failed');
    });
  });

  describe('letterDetachReference', () => {
    it('should detach reference successfully', async () => {
      const mockResponse = {
        success: true,
        message: 'Reference ref_123 removed from document doc_123',
      };

      mockApiClient.detachReferenceFromLetter.mockResolvedValue(mockResponse);

      const result = await letterDetachReference({
        letterId: 'doc_123',
        referenceId: 'ref_123',
      });

      expect(result.status).toBe('ok');
      expect(result.message).toBe('Reference ref_123 detached from letter doc_123');
    });

    it('should handle detach errors', async () => {
      mockApiClient.detachReferenceFromLetter.mockResolvedValue({
        success: false,
        error: 'Detach failed',
      });

      const result = await letterDetachReference({
        letterId: 'doc_123',
        referenceId: 'ref_123',
      });

      expect(result.status).toBe('error');
      expect(result.message).toBe('Detach failed');
    });
  });

  describe('letterListReferences', () => {
    it('should list references successfully', async () => {
      const mockResponse = {
        success: true,
        references: [
          {
            id: 'ref_123',
            type: 'person',
            name: 'John Doe',
            aliases: ['John', 'Johnny'],
            notes: 'Test person',
            createdAt: '2025-01-01T00:00:00Z',
            updatedAt: '2025-01-01T00:00:00Z',
            role: 'sender',
          },
          {
            id: 'ref_456',
            type: 'person',
            name: 'Jane Smith',
            aliases: ['Jane'],
            notes: 'Another person',
            createdAt: '2025-01-01T00:00:00Z',
            updatedAt: '2025-01-01T00:00:00Z',
            role: 'recipient',
          },
        ],
        total: 2,
      };

      mockApiClient.listLetterReferences.mockResolvedValue(mockResponse);

      const result = await letterListReferences({
        letterId: 'doc_123',
      });

      expect(result.status).toBe('ok');
      expect(result.message).toBe('Found 2 references for letter doc_123');
      expect(result.items).toHaveLength(2);
      expect(result.items?.[0].name).toBe('John Doe');
      expect(result.items?.[1].name).toBe('Jane Smith');
    });

    it('should handle list errors', async () => {
      mockApiClient.listLetterReferences.mockResolvedValue({
        success: false,
        error: 'List failed',
      });

      const result = await letterListReferences({
        letterId: 'doc_123',
      });

      expect(result.status).toBe('error');
      expect(result.message).toBe('List failed');
    });

    it('should handle empty references list', async () => {
      const mockResponse = {
        success: true,
        references: [],
        total: 0,
      };

      mockApiClient.listLetterReferences.mockResolvedValue(mockResponse);

      const result = await letterListReferences({
        letterId: 'doc_123',
      });

      expect(result.status).toBe('ok');
      expect(result.message).toBe('Found 0 references for letter doc_123');
      expect(result.items).toHaveLength(0);
    });
  });
});