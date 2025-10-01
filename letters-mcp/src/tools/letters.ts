import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { apiClient } from '../client.js';
import {
  LettersSearchInputSchema,
  LetterGetInputSchema,
  LetterCreateInputSchema,
  LetterUpdateInputSchema,
  LetterDeleteInputSchema,
  LettersSearchOutputSchema,
  LetterGetOutputSchema,
  LetterCreateOutputSchema,
  LetterUpdateOutputSchema,
  LetterDeleteOutputSchema,
  type LettersSearchInput,
  type LetterGetInput,
  type LetterCreateInput,
  type LetterUpdateInput,
  type LetterDeleteInput,
  type LettersSearchOutput,
  type LetterGetOutput,
  type LetterCreateOutput,
  type LetterUpdateOutput,
  type LetterDeleteOutput,
} from '../schemas.js';

// Helper function to transform API response to MCP format
function transformLetter(apiDoc: any) {
  return {
    id: apiDoc.id,
    title: apiDoc.title,
    date: apiDoc.date_processed,
    language: apiDoc.source_language,
    summary: apiDoc.summary,
    originalText: apiDoc.original_text,
    translatedText: apiDoc.translated_text,
    fileSize: apiDoc.file_size,
    pageCount: apiDoc.page_count,
    people: apiDoc.people || [],
    status: apiDoc.status,
    createdAt: apiDoc.date_processed,
    updatedAt: apiDoc.date_processed,
  };
}

function transformLetterSummary(apiDoc: any) {
  return {
    id: apiDoc.id,
    title: apiDoc.title,
    date: apiDoc.date_processed,
    language: apiDoc.source_language,
    summary: apiDoc.summary,
    pageCount: apiDoc.page_count,
    peopleCount: apiDoc.people_count,
    status: apiDoc.status,
  };
}

// Letters search tool
export const lettersSearchTool: Tool = {
  name: 'letters_search',
  description: 'Search for letters/documents with optional filters',
  inputSchema: {
    type: 'object',
    properties: {
      query: { type: 'string', description: 'Search query text' },
      dateFrom: { type: 'string', description: 'Start date filter (ISO format)' },
      dateTo: { type: 'string', description: 'End date filter (ISO format)' },
      language: { type: 'string', description: 'Language filter' },
      page: { type: 'number', minimum: 1, default: 1, description: 'Page number' },
      pageSize: { type: 'number', minimum: 1, maximum: 100, default: 10, description: 'Items per page' },
    },
  },
};

export async function lettersSearch(input: unknown): Promise<LettersSearchOutput> {
  try {
    const validatedInput = LettersSearchInputSchema.parse(input);
    
    // If no query provided, list all documents
    if (!validatedInput.query) {
      const response = await apiClient.listLetters();
      
      if (!response.success) {
        return {
          status: 'error',
          message: response.error || 'Failed to list letters',
        };
      }

      const documents = response.documents || [];
      const startIndex = (validatedInput.page - 1) * validatedInput.pageSize;
      const endIndex = startIndex + validatedInput.pageSize;
      const paginatedDocs = documents.slice(startIndex, endIndex);

      return {
        status: 'ok',
        message: `Found ${documents.length} letters`,
        items: paginatedDocs.map(transformLetterSummary),
        total: documents.length,
        page: validatedInput.page,
        pageSize: validatedInput.pageSize,
      };
    }

    // Use search endpoint
    const response = await apiClient.searchLetters(validatedInput);
    
    if (!response.success) {
      return {
        status: 'error',
        message: response.error || 'Search failed',
      };
    }

    const results = response.results || [];
    const startIndex = (validatedInput.page - 1) * validatedInput.pageSize;
    const endIndex = startIndex + validatedInput.pageSize;
    const paginatedResults = results.slice(startIndex, endIndex);

    return {
      status: 'ok',
      message: `Found ${results.length} letters matching "${validatedInput.query}"`,
      items: paginatedResults.map(transformLetterSummary),
      total: results.length,
      page: validatedInput.page,
      pageSize: validatedInput.pageSize,
    };
  } catch (error) {
    return {
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

// Letter get tool
export const letterGetTool: Tool = {
  name: 'letter_get',
  description: 'Get a specific letter/document by ID',
  inputSchema: {
    type: 'object',
    properties: {
      id: { type: 'string', description: 'Letter ID' },
    },
    required: ['id'],
  },
};

export async function letterGet(input: unknown): Promise<LetterGetOutput> {
  try {
    const validatedInput = LetterGetInputSchema.parse(input);
    
    const response = await apiClient.getLetter(validatedInput.id);
    
    if (!response.success) {
      return {
        status: 'error',
        message: response.error || 'Letter not found',
        item: null,
      };
    }

    return {
      status: 'ok',
      message: 'Letter retrieved successfully',
      item: transformLetter(response.document!),
    };
  } catch (error) {
    return {
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error occurred',
      item: null,
    };
  }
}

// Letter create tool
export const letterCreateTool: Tool = {
  name: 'letter_create',
  description: 'Create a new letter/document',
  inputSchema: {
    type: 'object',
    properties: {
      title: { type: 'string', description: 'Letter title' },
      date: { type: 'string', description: 'Letter date (ISO format)' },
      language: { type: 'string', description: 'Source language' },
      summary: { type: 'string', description: 'Letter summary' },
      originalText: { type: 'string', description: 'Original text content' },
      translatedText: { type: 'string', description: 'Translated text content' },
      fileSize: { type: 'number', description: 'File size in bytes' },
      pageCount: { type: 'number', description: 'Number of pages' },
    },
    required: ['title'],
  },
};

export async function letterCreate(input: unknown): Promise<LetterCreateOutput> {
  try {
    const validatedInput = LetterCreateInputSchema.parse(input);
    
    const response = await apiClient.createLetter(validatedInput);
    
    if (!response.success) {
      return {
        status: 'error',
        message: response.error || 'Failed to create letter',
      };
    }

    return {
      status: 'ok',
      message: 'Letter created successfully',
      item: transformLetter(response.data!),
    };
  } catch (error) {
    return {
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

// Letter update tool
export const letterUpdateTool: Tool = {
  name: 'letter_update',
  description: 'Update an existing letter/document',
  inputSchema: {
    type: 'object',
    properties: {
      id: { type: 'string', description: 'Letter ID' },
      title: { type: 'string', description: 'Letter title' },
      date: { type: 'string', description: 'Letter date (ISO format)' },
      language: { type: 'string', description: 'Source language' },
      summary: { type: 'string', description: 'Letter summary' },
      originalText: { type: 'string', description: 'Original text content' },
      translatedText: { type: 'string', description: 'Translated text content' },
      fileSize: { type: 'number', description: 'File size in bytes' },
      pageCount: { type: 'number', description: 'Number of pages' },
      regenerateSummary: { type: 'boolean', description: 'Regenerate AI summary' },
    },
    required: ['id'],
  },
};

export async function letterUpdate(input: unknown): Promise<LetterUpdateOutput> {
  try {
    const validatedInput = LetterUpdateInputSchema.parse(input);
    const { id, ...updateData } = validatedInput;
    
    const response = await apiClient.updateLetter(id, updateData);
    
    if (!response.success) {
      return {
        status: 'error',
        message: response.error || 'Failed to update letter',
      };
    }

    const result: LetterUpdateOutput = {
      status: 'ok',
      message: 'Letter updated successfully',
      item: transformLetter(response.document!),
    };

    // Add regenerated data if available
    if (response.regenerated_summary) {
      result.regeneratedSummary = response.regenerated_summary;
    }
    if (response.regenerated_people) {
      result.regeneratedPeople = response.regenerated_people;
    }

    return result;
  } catch (error) {
    return {
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

// Letter delete tool
export const letterDeleteTool: Tool = {
  name: 'letter_delete',
  description: 'Delete a letter/document',
  inputSchema: {
    type: 'object',
    properties: {
      id: { type: 'string', description: 'Letter ID' },
    },
    required: ['id'],
  },
};

export async function letterDelete(input: unknown): Promise<LetterDeleteOutput> {
  try {
    const validatedInput = LetterDeleteInputSchema.parse(input);
    
    const response = await apiClient.deleteLetter(validatedInput.id);
    
    if (!response.success) {
      return {
        status: 'error',
        message: response.error || 'Failed to delete letter',
      };
    }

    return {
      status: 'ok',
      message: 'Letter deleted successfully',
    };
  } catch (error) {
    return {
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}
