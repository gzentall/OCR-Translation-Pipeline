import { describe, it, expect, vi, beforeEach } from 'vitest';
import { referencesSearch, referenceGet, referenceCreate, referenceUpdate, referenceDelete } from '../tools/references.js';
import { apiClient } from '../client.js';

// Mock the API client
vi.mock('../client.js', () => ({
  apiClient: {
    searchReferences: vi.fn(),
    getReference: vi.fn(),
    createReference: vi.fn(),
    updateReference: vi.fn(),
    deleteReference: vi.fn(),
    listReferences: vi.fn(),
  },
}));

const mockApiClient = vi.mocked(apiClient);

describe('References Tools', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('referencesSearch', () => {
    it('should search references successfully', async () => {
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
          },
        ],
      };

      mockApiClient.searchReferences.mockResolvedValue(mockResponse);

      const result = await referencesSearch({
        query: 'john',
        page: 1,
        pageSize: 10,
      });

      expect(result.status).toBe('ok');
      expect(result.items).toHaveLength(1);
      expect(result.items?.[0].name).toBe('John Doe');
      expect(result.items?.[0].type).toBe('person');
    });

    it('should list all references when no query provided', async () => {
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
          },
        ],
      };

      mockApiClient.searchReferences.mockResolvedValue(mockResponse);

      const result = await referencesSearch({
        page: 1,
        pageSize: 10,
      });

      expect(result.status).toBe('ok');
      expect(result.items).toHaveLength(1);
      expect(mockApiClient.searchReferences).toHaveBeenCalled();
    });

    it('should handle search errors', async () => {
      mockApiClient.searchReferences.mockResolvedValue({
        success: false,
        error: 'Search failed',
      });

      const result = await referencesSearch({
        query: 'test',
      });

      expect(result.status).toBe('error');
      expect(result.message).toBe('Search failed');
    });
  });

  describe('referenceGet', () => {
    it('should get reference successfully', async () => {
      const mockResponse = {
        success: true,
        reference: {
          id: 'ref_123',
          type: 'person',
          name: 'John Doe',
          aliases: ['John', 'Johnny'],
          notes: 'Test person',
          createdAt: '2025-01-01T00:00:00Z',
          updatedAt: '2025-01-01T00:00:00Z',
        },
      };

      mockApiClient.getReference.mockResolvedValue(mockResponse);

      const result = await referenceGet({ id: 'ref_123' });

      expect(result.status).toBe('ok');
      expect(result.item).toBeDefined();
      expect(result.item?.name).toBe('John Doe');
      expect(result.item?.type).toBe('person');
    });

    it('should handle reference not found', async () => {
      mockApiClient.getReference.mockResolvedValue({
        success: false,
        error: 'Reference not found',
      });

      const result = await referenceGet({ id: 'nonexistent' });

      expect(result.status).toBe('error');
      expect(result.message).toBe('Reference not found');
      expect(result.item).toBeNull();
    });
  });

  describe('referenceCreate', () => {
    it('should create reference successfully', async () => {
      const mockResponse = {
        success: true,
        reference: {
          id: 'ref_456',
          type: 'person',
          name: 'Jane Doe',
          aliases: ['Jane'],
          notes: 'New person',
          createdAt: '2025-01-01T00:00:00Z',
          updatedAt: '2025-01-01T00:00:00Z',
        },
      };

      mockApiClient.createReference.mockResolvedValue(mockResponse);

      const result = await referenceCreate({
        type: 'person',
        name: 'Jane Doe',
        aliases: ['Jane'],
        notes: 'New person',
      });

      expect(result.status).toBe('ok');
      expect(result.item).toBeDefined();
      expect(result.item?.name).toBe('Jane Doe');
    });

    it('should handle create errors', async () => {
      mockApiClient.createReference.mockResolvedValue({
        success: false,
        error: 'Create failed',
      });

      const result = await referenceCreate({
        type: 'person',
        name: 'Jane Doe',
      });

      expect(result.status).toBe('error');
      expect(result.message).toBe('Create failed');
    });
  });

  describe('referenceUpdate', () => {
    it('should update reference successfully', async () => {
      const mockResponse = {
        success: true,
        reference: {
          id: 'ref_123',
          type: 'person',
          name: 'John Updated',
          aliases: ['John', 'Johnny', 'J'],
          notes: 'Updated person',
          createdAt: '2025-01-01T00:00:00Z',
          updatedAt: '2025-01-01T00:00:00Z',
        },
      };

      mockApiClient.updateReference.mockResolvedValue(mockResponse);

      const result = await referenceUpdate({
        id: 'ref_123',
        name: 'John Updated',
        aliases: ['John', 'Johnny', 'J'],
        notes: 'Updated person',
      });

      expect(result.status).toBe('ok');
      expect(result.item).toBeDefined();
      expect(result.item?.name).toBe('John Updated');
    });

    it('should handle update errors', async () => {
      mockApiClient.updateReference.mockResolvedValue({
        success: false,
        error: 'Update failed',
      });

      const result = await referenceUpdate({
        id: 'ref_123',
        name: 'John Updated',
      });

      expect(result.status).toBe('error');
      expect(result.message).toBe('Update failed');
    });
  });

  describe('referenceDelete', () => {
    it('should delete reference successfully', async () => {
      const mockResponse = {
        success: true,
        message: 'Reference deleted successfully',
      };

      mockApiClient.deleteReference.mockResolvedValue(mockResponse);

      const result = await referenceDelete({ id: 'ref_123' });

      expect(result.status).toBe('ok');
      expect(result.message).toBe('Reference deleted successfully');
    });

    it('should handle delete errors', async () => {
      mockApiClient.deleteReference.mockResolvedValue({
        success: false,
        error: 'Delete failed',
      });

      const result = await referenceDelete({ id: 'ref_123' });

      expect(result.status).toBe('error');
      expect(result.message).toBe('Delete failed');
    });
  });
});