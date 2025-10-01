import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { apiClient } from '../client.js';
import {
  ReferencesSearchInputSchema,
  ReferenceGetInputSchema,
  ReferenceCreateInputSchema,
  ReferenceUpdateInputSchema,
  ReferenceDeleteInputSchema,
  ReferencesSearchOutputSchema,
  ReferenceGetOutputSchema,
  ReferenceCreateOutputSchema,
  ReferenceUpdateOutputSchema,
  ReferenceDeleteOutputSchema,
  type ReferencesSearchInput,
  type ReferenceGetInput,
  type ReferenceCreateInput,
  type ReferenceUpdateInput,
  type ReferenceDeleteInput,
  type ReferencesSearchOutput,
  type ReferenceGetOutput,
  type ReferenceCreateOutput,
  type ReferenceUpdateOutput,
  type ReferenceDeleteOutput,
} from '../schemas.js';

// Helper function to transform API response to MCP format
function transformReference(apiRef: any): any {
  return {
    id: apiRef.id,
    type: apiRef.type,
    name: apiRef.name,
    aliases: apiRef.aliases || [],
    notes: apiRef.notes || '',
    context: apiRef.notes || '', // For backward compatibility
    firstMentioned: apiRef.createdAt,
    documentCount: 0, // Will be populated by relations
    createdAt: apiRef.createdAt,
    updatedAt: apiRef.updatedAt,
    mergedIntoId: apiRef.mergedIntoId,
  };
}

// References search tool
export const referencesSearchTool: Tool = {
  name: 'references_search',
  description: 'Search for references (people, places, events) with optional filters',
  inputSchema: {
    type: 'object',
    properties: {
      query: { type: 'string', description: 'Search query text' },
      type: { type: 'string', enum: ['person', 'place', 'event', 'other'], description: 'Reference type filter' },
      page: { type: 'number', minimum: 1, default: 1, description: 'Page number' },
      pageSize: { type: 'number', minimum: 1, maximum: 100, default: 10, description: 'Items per page' },
    },
  },
};

export async function referencesSearch(input: unknown): Promise<ReferencesSearchOutput> {
  try {
    const validatedInput = ReferencesSearchInputSchema.parse(input);
    
    const response = await apiClient.searchReferences(validatedInput);
    
    if (!response.success) {
      return {
        status: 'error',
        message: response.error || 'Search failed',
      };
    }

    const references = response.references || [];
    const startIndex = (validatedInput.page - 1) * validatedInput.pageSize;
    const endIndex = startIndex + validatedInput.pageSize;
    const paginatedReferences = references.slice(startIndex, endIndex);

    return {
      status: 'ok',
      message: `Found ${references.length} references`,
      items: paginatedReferences.map(transformReference),
      total: references.length,
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

// Reference get tool
export const referenceGetTool: Tool = {
  name: 'reference_get',
  description: 'Get a specific reference by ID (name)',
  inputSchema: {
    type: 'object',
    properties: {
      id: { type: 'string', description: 'Reference ID (name)' },
    },
    required: ['id'],
  },
};

export async function referenceGet(input: unknown): Promise<ReferenceGetOutput> {
  try {
    const validatedInput = ReferenceGetInputSchema.parse(input);
    
    const response = await apiClient.getReference(validatedInput.id);
    
    if (!response.success) {
      return {
        status: 'error',
        message: response.error || 'Reference not found',
        item: null,
      };
    }

    return {
      status: 'ok',
      message: 'Reference retrieved successfully',
      item: transformReference(response.reference!),
    };
  } catch (error) {
    return {
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error occurred',
      item: null,
    };
  }
}

// Reference create tool
export const referenceCreateTool: Tool = {
  name: 'reference_create',
  description: 'Create a new reference (person, place, event)',
  inputSchema: {
    type: 'object',
    properties: {
      type: { type: 'string', enum: ['person', 'place', 'event', 'other'], description: 'Reference type' },
      name: { type: 'string', description: 'Reference name' },
      aliases: { type: 'array', items: { type: 'string' }, description: 'Alternative names' },
      notes: { type: 'string', description: 'Reference notes' },
      context: { type: 'string', description: 'Reference context' },
    },
    required: ['type', 'name'],
  },
};

export async function referenceCreate(input: unknown): Promise<ReferenceCreateOutput> {
  try {
    const validatedInput = ReferenceCreateInputSchema.parse(input);
    
    const response = await apiClient.createReference(validatedInput);
    
    if (!response.success) {
      return {
        status: 'error',
        message: response.error || 'Failed to create reference',
      };
    }

    return {
      status: 'ok',
      message: 'Reference created successfully',
      item: transformReference(response.reference!),
    };
  } catch (error) {
    return {
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

// Reference update tool
export const referenceUpdateTool: Tool = {
  name: 'reference_update',
  description: 'Update an existing reference',
  inputSchema: {
    type: 'object',
    properties: {
      id: { type: 'string', description: 'Reference ID (name)' },
      name: { type: 'string', description: 'New reference name' },
      aliases: { type: 'array', items: { type: 'string' }, description: 'Alternative names' },
      notes: { type: 'string', description: 'Reference notes' },
      context: { type: 'string', description: 'Reference context' },
    },
    required: ['id'],
  },
};

export async function referenceUpdate(input: unknown): Promise<ReferenceUpdateOutput> {
  try {
    const validatedInput = ReferenceUpdateInputSchema.parse(input);
    const { id, ...updateData } = validatedInput;
    
    const response = await apiClient.updateReference(id, updateData);
    
    if (!response.success) {
      return {
        status: 'error',
        message: response.error || 'Failed to update reference',
      };
    }

    return {
      status: 'ok',
      message: 'Reference updated successfully',
      item: transformReference(response.reference!),
    };
  } catch (error) {
    return {
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

// Reference delete tool
export const referenceDeleteTool: Tool = {
  name: 'reference_delete',
  description: 'Delete a reference',
  inputSchema: {
    type: 'object',
    properties: {
      id: { type: 'string', description: 'Reference ID (name)' },
    },
    required: ['id'],
  },
};

export async function referenceDelete(input: unknown): Promise<ReferenceDeleteOutput> {
  try {
    const validatedInput = ReferenceDeleteInputSchema.parse(input);
    
    const response = await apiClient.deleteReference(validatedInput.id);
    
    if (!response.success) {
      return {
        status: 'error',
        message: response.error || 'Failed to delete reference',
      };
    }

    return {
      status: 'ok',
      message: 'Reference deleted successfully',
    };
  } catch (error) {
    return {
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

// Reference merge tool
export const referenceMergeTool: Tool = {
  name: 'reference_merge',
  description: 'Merge a source reference into a target reference (soft merge)',
  inputSchema: {
    type: 'object',
    properties: {
      sourceId: { type: 'string', description: 'Source reference ID to merge' },
      targetId: { type: 'string', description: 'Target reference ID to merge into' },
    },
    required: ['sourceId', 'targetId'],
  },
};

export async function referenceMerge(input: unknown): Promise<{ status: 'ok' | 'error'; message: string }> {
  try {
    const { sourceId, targetId } = input as { sourceId: string; targetId: string };
    
    const response = await apiClient.mergeReferences(sourceId, targetId);
    
    if (!response.success) {
      return {
        status: 'error',
        message: response.error || 'Failed to merge references',
      };
    }

    return {
      status: 'ok',
      message: `Reference ${sourceId} merged into ${targetId}`,
    };
  } catch (error) {
    return {
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}
