import { describe, it, expect, vi, beforeEach } from 'vitest';
import { lettersSearch, letterGet, letterCreate, letterUpdate, letterDelete } from '../tools/letters.js';
import { apiClient } from '../client.js';

// Mock the API client
vi.mock('../client.js', () => ({
  apiClient: {
    searchLetters: vi.fn(),
    getLetter: vi.fn(),
    createLetter: vi.fn(),
    updateLetter: vi.fn(),
    deleteLetter: vi.fn(),
    listLetters: vi.fn(),
  },
}));

const mockApiClient = vi.mocked(apiClient);

describe('Letters Tools', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('lettersSearch', () => {
    it('should search letters successfully', async () => {
      const mockResponse = {
        success: true,
        results: [
          {
            id: 'doc_123',
            title: 'Test Letter',
            date_processed: '2025-01-01T00:00:00Z',
            source_language: 'en',
            summary: 'Test summary',
            page_count: 2,
            people_count: 1,
            status: 'New',
          },
        ],
      };

      mockApiClient.searchLetters.mockResolvedValue(mockResponse);

      const result = await lettersSearch({
        query: 'test',
        page: 1,
        pageSize: 10,
      });

      expect(result.status).toBe('ok');
      expect(result.items).toHaveLength(1);
      expect(result.items?.[0].id).toBe('doc_123');
      expect(result.items?.[0].title).toBe('Test Letter');
    });

    it('should handle search errors', async () => {
      mockApiClient.searchLetters.mockResolvedValue({
        success: false,
        error: 'Search failed',
      });

      const result = await lettersSearch({
        query: 'test',
      });

      expect(result.status).toBe('error');
      expect(result.message).toBe('Search failed');
    });

    it('should list all letters when no query provided', async () => {
      const mockResponse = {
        success: true,
        documents: [
          {
            id: 'doc_123',
            title: 'Test Letter',
            date_processed: '2025-01-01T00:00:00Z',
            source_language: 'en',
            summary: 'Test summary',
            page_count: 2,
            people_count: 1,
            status: 'New',
          },
        ],
      };

      mockApiClient.listLetters.mockResolvedValue(mockResponse);

      const result = await lettersSearch({
        page: 1,
        pageSize: 10,
      });

      expect(result.status).toBe('ok');
      expect(result.items).toHaveLength(1);
      expect(mockApiClient.listLetters).toHaveBeenCalled();
    });
  });

  describe('letterGet', () => {
    it('should get letter successfully', async () => {
      const mockResponse = {
        success: true,
        document: {
          id: 'doc_123',
          title: 'Test Letter',
          date_processed: '2025-01-01T00:00:00Z',
          source_language: 'en',
          summary: 'Test summary',
          original_text: 'Original text',
          translated_text: 'Translated text',
          file_size: 1024,
          page_count: 2,
          people: ['John Doe'],
          status: 'New',
        },
      };

      mockApiClient.getLetter.mockResolvedValue(mockResponse);

      const result = await letterGet({ id: 'doc_123' });

      expect(result.status).toBe('ok');
      expect(result.item).toBeDefined();
      expect(result.item?.id).toBe('doc_123');
      expect(result.item?.title).toBe('Test Letter');
    });

    it('should handle letter not found', async () => {
      mockApiClient.getLetter.mockResolvedValue({
        success: false,
        error: 'Document not found',
      });

      const result = await letterGet({ id: 'nonexistent' });

      expect(result.status).toBe('error');
      expect(result.message).toBe('Document not found');
      expect(result.item).toBeNull();
    });
  });

  describe('letterCreate', () => {
    it('should create letter successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          id: 'doc_123',
          title: 'New Letter',
          date_processed: '2025-01-01T00:00:00Z',
          source_language: 'en',
          summary: 'New summary',
          original_text: 'Original text',
          translated_text: 'Translated text',
          file_size: 1024,
          page_count: 2,
          people: [],
          status: 'New',
        },
      };

      mockApiClient.createLetter.mockResolvedValue(mockResponse);

      const result = await letterCreate({
        title: 'New Letter',
        summary: 'New summary',
      });

      expect(result.status).toBe('ok');
      expect(result.item).toBeDefined();
      expect(result.item?.title).toBe('New Letter');
    });

    it('should handle create errors', async () => {
      mockApiClient.createLetter.mockRejectedValue(new Error('Create failed'));

      const result = await letterCreate({
        title: 'New Letter',
      });

      expect(result.status).toBe('error');
      expect(result.message).toBe('Create failed');
    });
  });

  describe('letterUpdate', () => {
    it('should update letter successfully', async () => {
      const mockResponse = {
        success: true,
        document: {
          id: 'doc_123',
          title: 'Updated Letter',
          date_processed: '2025-01-01T00:00:00Z',
          source_language: 'en',
          summary: 'Updated summary',
          original_text: 'Original text',
          translated_text: 'Translated text',
          file_size: 1024,
          page_count: 2,
          people: ['John Doe'],
          status: 'Updated',
        },
      };

      mockApiClient.updateLetter.mockResolvedValue(mockResponse);

      const result = await letterUpdate({
        id: 'doc_123',
        title: 'Updated Letter',
        summary: 'Updated summary',
      });

      expect(result.status).toBe('ok');
      expect(result.item).toBeDefined();
      expect(result.item?.title).toBe('Updated Letter');
    });

    it('should handle update errors', async () => {
      mockApiClient.updateLetter.mockResolvedValue({
        success: false,
        error: 'Update failed',
      });

      const result = await letterUpdate({
        id: 'doc_123',
        title: 'Updated Letter',
      });

      expect(result.status).toBe('error');
      expect(result.message).toBe('Update failed');
    });
  });

  describe('letterDelete', () => {
    it('should delete letter successfully', async () => {
      const mockResponse = {
        success: true,
        message: 'Document deleted successfully',
      };

      mockApiClient.deleteLetter.mockResolvedValue(mockResponse);

      const result = await letterDelete({ id: 'doc_123' });

      expect(result.status).toBe('ok');
      expect(result.message).toBe('Letter deleted successfully');
    });

    it('should handle delete errors', async () => {
      mockApiClient.deleteLetter.mockResolvedValue({
        success: false,
        error: 'Delete failed',
      });

      const result = await letterDelete({ id: 'doc_123' });

      expect(result.status).toBe('error');
      expect(result.message).toBe('Delete failed');
    });
  });
});
