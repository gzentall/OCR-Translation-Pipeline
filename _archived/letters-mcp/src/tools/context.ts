import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { apiClient } from '../client.js';
import {
  LetterAddContextInputSchema,
  LetterUpdateContextInputSchema,
  LetterDeleteContextInputSchema,
  LetterListContextInputSchema,
  LetterAddContextOutputSchema,
  LetterUpdateContextOutputSchema,
  LetterDeleteContextOutputSchema,
  LetterListContextOutputSchema,
  type LetterAddContextInput,
  type LetterUpdateContextInput,
  type LetterDeleteContextInput,
  type LetterListContextInput,
  type LetterAddContextOutput,
  type LetterUpdateContextOutput,
  type LetterDeleteContextOutput,
  type LetterListContextOutput,
} from '../schemas.js';

// Context notes are not yet implemented in the Letters API
// These are placeholder implementations that return appropriate error messages

// Letter add context tool
export const letterAddContextTool: Tool = {
  name: 'letter_add_context',
  description: 'Add a context note to a letter',
  inputSchema: {
    type: 'object',
    properties: {
      letterId: { type: 'string', description: 'Letter ID' },
      note: { type: 'string', description: 'Context note text' },
    },
    required: ['letterId', 'note'],
  },
};

export async function letterAddContext(input: unknown): Promise<LetterAddContextOutput> {
  try {
    const validatedInput = LetterAddContextInputSchema.parse(input);
    const response = await apiClient.addContextToLetter(validatedInput.letterId, validatedInput.note);
    if (!response.success) {
      return { status: 'error', message: response.error || 'Failed to add context note' };
    }
    return { status: 'ok', message: 'Context note added', item: (response as any).item };
  } catch (error) {
    return {
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

// Letter update context tool
export const letterUpdateContextTool: Tool = {
  name: 'letter_update_context',
  description: 'Update a context note',
  inputSchema: {
    type: 'object',
    properties: {
      contextId: { type: 'string', description: 'Context note ID' },
      note: { type: 'string', description: 'Updated context note text' },
    },
    required: ['contextId', 'note'],
  },
};

export async function letterUpdateContext(input: unknown): Promise<LetterUpdateContextOutput> {
  try {
    const validatedInput = LetterUpdateContextInputSchema.parse(input);
    const response = await apiClient.updateContextNote(validatedInput.contextId, validatedInput.note);
    if (!response.success) {
      return { status: 'error', message: response.error || 'Failed to update context note' };
    }
    return { status: 'ok', message: 'Context note updated', item: (response as any).item };
  } catch (error) {
    return {
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

// Letter delete context tool
export const letterDeleteContextTool: Tool = {
  name: 'letter_delete_context',
  description: 'Delete a context note',
  inputSchema: {
    type: 'object',
    properties: {
      contextId: { type: 'string', description: 'Context note ID' },
    },
    required: ['contextId'],
  },
};

export async function letterDeleteContext(input: unknown): Promise<LetterDeleteContextOutput> {
  try {
    const validatedInput = LetterDeleteContextInputSchema.parse(input);
    const response = await apiClient.deleteContextNote(validatedInput.contextId);
    if (!response.success) {
      return { status: 'error', message: response.error || 'Failed to delete context note' };
    }
    return { status: 'ok', message: 'Context note deleted' };
  } catch (error) {
    return {
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

// Letter list context tool
export const letterListContextTool: Tool = {
  name: 'letter_list_context',
  description: 'List all context notes for a letter',
  inputSchema: {
    type: 'object',
    properties: {
      letterId: { type: 'string', description: 'Letter ID' },
    },
    required: ['letterId'],
  },
};

export async function letterListContext(input: unknown): Promise<LetterListContextOutput> {
  try {
    const validatedInput = LetterListContextInputSchema.parse(input);
    const response = await apiClient.listLetterContext(validatedInput.letterId);
    if (!response.success) {
      return { status: 'error', message: response.error || 'Failed to list context notes', items: [] };
    }
    return { status: 'ok', message: 'Context notes listed', items: (response as any).items || [] };
  } catch (error) {
    return {
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error occurred',
      items: [],
    };
  }
}
