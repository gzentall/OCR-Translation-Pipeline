import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { apiClient } from '../client.js';
import {
  LetterAttachReferenceInputSchema,
  LetterDetachReferenceInputSchema,
  LetterListReferencesInputSchema,
  LetterAttachReferenceOutputSchema,
  LetterDetachReferenceOutputSchema,
  LetterListReferencesOutputSchema,
  type LetterAttachReferenceInput,
  type LetterDetachReferenceInput,
  type LetterListReferencesInput,
  type LetterAttachReferenceOutput,
  type LetterDetachReferenceOutput,
  type LetterListReferencesOutput,
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
    role: apiRef.role, // Include role from relations
  };
}

// Letter attach reference tool
export const letterAttachReferenceTool: Tool = {
  name: 'letter_attach_reference',
  description: 'Attach a reference (person, place, event) to a letter',
  inputSchema: {
    type: 'object',
    properties: {
      letterId: { type: 'string', description: 'Letter ID' },
      referenceId: { type: 'string', description: 'Reference ID (name)' },
      role: { type: 'string', description: 'Role of the reference in the letter (e.g., sender, recipient)' },
    },
    required: ['letterId', 'referenceId'],
  },
};

export async function letterAttachReference(input: unknown): Promise<LetterAttachReferenceOutput> {
  try {
    const validatedInput = LetterAttachReferenceInputSchema.parse(input);
    
    const response = await apiClient.attachReferenceToLetter(
      validatedInput.letterId,
      validatedInput.referenceId,
      validatedInput.role
    );
    
    if (!response.success) {
      return {
        status: 'error',
        message: response.error || 'Failed to attach reference to letter',
      };
    }

    return {
      status: 'ok',
      message: `Reference ${validatedInput.referenceId} attached to letter ${validatedInput.letterId}`,
      relation: {
        letterId: validatedInput.letterId,
        referenceId: validatedInput.referenceId,
        role: validatedInput.role,
      },
    };
  } catch (error) {
    return {
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

// Letter detach reference tool
export const letterDetachReferenceTool: Tool = {
  name: 'letter_detach_reference',
  description: 'Detach a reference from a letter',
  inputSchema: {
    type: 'object',
    properties: {
      letterId: { type: 'string', description: 'Letter ID' },
      referenceId: { type: 'string', description: 'Reference ID (name)' },
    },
    required: ['letterId', 'referenceId'],
  },
};

export async function letterDetachReference(input: unknown): Promise<LetterDetachReferenceOutput> {
  try {
    const validatedInput = LetterDetachReferenceInputSchema.parse(input);
    
    const response = await apiClient.detachReferenceFromLetter(
      validatedInput.letterId,
      validatedInput.referenceId
    );
    
    if (!response.success) {
      return {
        status: 'error',
        message: response.error || 'Failed to detach reference from letter',
      };
    }

    return {
      status: 'ok',
      message: `Reference ${validatedInput.referenceId} detached from letter ${validatedInput.letterId}`,
    };
  } catch (error) {
    return {
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

// Letter list references tool
export const letterListReferencesTool: Tool = {
  name: 'letter_list_references',
  description: 'List all references attached to a letter',
  inputSchema: {
    type: 'object',
    properties: {
      letterId: { type: 'string', description: 'Letter ID' },
    },
    required: ['letterId'],
  },
};

export async function letterListReferences(input: unknown): Promise<LetterListReferencesOutput> {
  try {
    const validatedInput = LetterListReferencesInputSchema.parse(input);
    
    const response = await apiClient.listLetterReferences(validatedInput.letterId);
    
    if (!response.success) {
      return {
        status: 'error',
        message: response.error || 'Failed to list letter references',
      };
    }

    return {
      status: 'ok',
      message: `Found ${response.references?.length || 0} references for letter ${validatedInput.letterId}`,
      items: (response.references || []).map(transformReference),
    };
  } catch (error) {
    return {
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}
