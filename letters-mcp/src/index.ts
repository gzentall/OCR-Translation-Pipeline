#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

// Import all tools
import {
  lettersSearchTool,
  letterGetTool,
  letterCreateTool,
  letterUpdateTool,
  letterDeleteTool,
  lettersSearch,
  letterGet,
  letterCreate,
  letterUpdate,
  letterDelete,
} from './tools/letters.js';

import {
  referencesSearchTool,
  referenceGetTool,
  referenceCreateTool,
  referenceUpdateTool,
  referenceDeleteTool,
  referenceMergeTool,
  referencesSearch,
  referenceGet,
  referenceCreate,
  referenceUpdate,
  referenceDelete,
  referenceMerge,
} from './tools/references.js';

import {
  letterAttachReferenceTool,
  letterDetachReferenceTool,
  letterListReferencesTool,
  letterAttachReference,
  letterDetachReference,
  letterListReferences,
} from './tools/relations.js';

import {
  letterAddContextTool,
  letterUpdateContextTool,
  letterDeleteContextTool,
  letterListContextTool,
  letterAddContext,
  letterUpdateContext,
  letterDeleteContext,
  letterListContext,
} from './tools/context.js';

import {
  healthCheckTool,
  healthCheck,
} from './tools/health.js';

// Tool registry
const tools = [
  // Letters tools
  lettersSearchTool,
  letterGetTool,
  letterCreateTool,
  letterUpdateTool,
  letterDeleteTool,
  
  // References tools
  referencesSearchTool,
  referenceGetTool,
  referenceCreateTool,
  referenceUpdateTool,
  referenceDeleteTool,
  referenceMergeTool,
  
  // Relations tools
  letterAttachReferenceTool,
  letterDetachReferenceTool,
  letterListReferencesTool,
  
  // Context tools
  letterAddContextTool,
  letterUpdateContextTool,
  letterDeleteContextTool,
  letterListContextTool,
  
  // Health tool
  healthCheckTool,
];

// Tool handler mapping
const toolHandlers: Record<string, (input: unknown) => Promise<any>> = {
  // Letters
  letters_search: lettersSearch,
  letter_get: letterGet,
  letter_create: letterCreate,
  letter_update: letterUpdate,
  letter_delete: letterDelete,
  
  // References
  references_search: referencesSearch,
  reference_get: referenceGet,
  reference_create: referenceCreate,
  reference_update: referenceUpdate,
  reference_delete: referenceDelete,
  reference_merge: referenceMerge,
  
  // Relations
  letter_attach_reference: letterAttachReference,
  letter_detach_reference: letterDetachReference,
  letter_list_references: letterListReferences,
  
  // Context
  letter_add_context: letterAddContext,
  letter_update_context: letterUpdateContext,
  letter_delete_context: letterDeleteContext,
  letter_list_context: letterListContext,
  
  // Health
  health_check: healthCheck,
};

// Create MCP server
const server = new Server(
  {
    name: 'letters-mcp',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Handle list tools request
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: tools.map(tool => ({
      name: tool.name,
      description: tool.description,
      inputSchema: tool.inputSchema,
    })),
  };
});

// Handle call tool request
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  const handler = toolHandlers[name];
  if (!handler) {
    throw new Error(`Unknown tool: ${name}`);
  }

  try {
    const result = await handler(args);
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            status: 'error',
            message: errorMessage,
          }, null, 2),
        },
      ],
      isError: true,
    };
  }
});

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  
  console.error('Letters MCP Server started successfully');
  console.error('Available tools:', tools.map(t => t.name).join(', '));
}

// Handle uncaught errors
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
  process.exit(1);
});

// Start the server
main().catch((error) => {
  console.error('Failed to start server:', error);
  process.exit(1);
});
