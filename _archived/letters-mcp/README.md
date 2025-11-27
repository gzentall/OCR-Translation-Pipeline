# Letters MCP Server

A Model Context Protocol (MCP) server for the Letters app that provides CRUD operations for documents, references, and context management. This server acts as a thin adapter layer between MCP clients (like Cursor) and your existing Letters Flask API.

## Features

- **Letters/Documents**: Create, read, update, delete, and search letters
- **References/People**: Manage people, places, events, and other entities
- **Relations**: Attach and detach references to letters
- **Context Notes**: Add contextual information to letters with full CRUD support
- **Health Check**: Monitor the health of the Letters app and MCP server

## Prerequisites

- Node.js 18+ 
- Your Letters Flask app running (default: http://localhost:5001)
- Valid API token for authentication (if required)

## Installation

1. **Clone or copy the MCP server files**:
   ```bash
   cd /path/to/your/letters-mcp
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

4. **Build the project**:
   ```bash
   npm run build
   ```

## Configuration

Create a `.env` file with the following variables:

```env
# API Configuration
API_BASE_URL=http://localhost:5001
API_TOKEN_READONLY=your-readonly-token-here
API_TOKEN_ADMIN=your-admin-token-here
TIMEOUT_MS=120000

# Mode: 'http' for REST API calls, 'local' for direct module imports
MODE=http

# Optional: Custom headers for authentication
# AUTH_HEADER=Bearer your-jwt-token-here
```

### Server Modes

The MCP server supports two access levels:

- **Readonly Mode**: Can only read and search data (letters, references, context)
- **Admin Mode**: Full CRUD access to all data including creating, updating, and deleting

The mode is determined by the `MODE` environment variable and the corresponding API token permissions.

### Configuration Options

- `API_BASE_URL`: Base URL of your Letters Flask app (default: http://localhost:5001)
- `API_TOKEN_READONLY`: Readonly API token for read-only access
- `API_TOKEN_ADMIN`: Admin API token for full CRUD access
- `TIMEOUT_MS`: Request timeout in milliseconds (default: 120000)
- `MODE`: Operation mode - 'http' for REST API calls, 'local' for direct module imports
- `AUTH_HEADER`: Custom authorization header (overrides API_TOKEN if set)

## Usage

### Development Mode

Run the server in development mode with hot reload:

```bash
npm run dev
```

### Production Mode

Build and run the server:

```bash
npm run build
npm start
```

### Testing

Run the test suite:

```bash
npm test
```

Run tests in watch mode:

```bash
npm run test:watch
```

## MCP Tools

### Letters/Documents

#### `letters_search`
Search for letters with optional filters.

**Input:**
```json
{
  "query": "Berlin 1940",
  "dateFrom": "1940-01-01",
  "dateTo": "1940-12-31",
  "language": "de",
  "page": 1,
  "pageSize": 10
}
```

**Output:**
```json
{
  "status": "ok",
  "message": "Found 5 letters matching \"Berlin 1940\"",
  "items": [
    {
      "id": "doc_123",
      "title": "Letter from Berlin",
      "date": "1940-05-15T00:00:00Z",
      "language": "de",
      "summary": "Letter discussing...",
      "pageCount": 2,
      "peopleCount": 3,
      "status": "New"
    }
  ],
  "total": 5,
  "page": 1,
  "pageSize": 10
}
```

#### `letter_get`
Get a specific letter by ID.

**Input:**
```json
{
  "id": "doc_123"
}
```

#### `letter_create`
Create a new letter (requires backend implementation).

**Input:**
```json
{
  "title": "New Letter",
  "date": "1940-05-15",
  "language": "de",
  "summary": "Letter summary",
  "originalText": "Original German text",
  "translatedText": "Translated English text",
  "fileSize": 1024,
  "pageCount": 2
}
```

#### `letter_update`
Update an existing letter.

**Input:**
```json
{
  "id": "doc_123",
  "title": "Updated Title",
  "summary": "Updated summary",
  "regenerateSummary": true
}
```

#### `letter_delete`
Delete a letter.

**Input:**
```json
{
  "id": "doc_123"
}
```

### References/People

#### `references_search`
Search for references (people, places, events).

**Input:**
```json
{
  "query": "Robert",
  "type": "person",
  "page": 1,
  "pageSize": 10
}
```

#### `reference_create`
Create a new reference.

**Input:**
```json
{
  "type": "person",
  "name": "Robert (Bobby) Smith",
  "aliases": ["Bobby", "Rob"],
  "notes": "Family member mentioned in letters"
}
```

#### `reference_update`
Update an existing reference.

**Input:**
```json
{
  "id": "ref_123",
  "name": "Robert Smith",
  "aliases": ["Bobby", "Rob", "Bob"],
  "notes": "Updated context information"
}
```

#### `reference_delete`
Delete a reference.

**Input:**
```json
{
  "id": "ref_123"
}
```

#### `reference_merge`
Merge a source reference into a target reference (soft merge).

**Input:**
```json
{
  "sourceId": "ref_123",
  "targetId": "ref_456"
}
```

### Relations

#### `letter_attach_reference`
Attach a reference to a letter.

**Input:**
```json
{
  "letterId": "doc_123",
  "referenceId": "ref_123",
  "role": "sender"
}
```

#### `letter_detach_reference`
Detach a reference from a letter.

**Input:**
```json
{
  "letterId": "doc_123",
  "referenceId": "ref_123"
}
```

#### `letter_list_references`
List all references attached to a letter.

**Input:**
```json
{
  "letterId": "doc_123"
}
```

### Context Notes

#### `letter_add_context`
Add a context note to a letter.

**Input:**
```json
{
  "letterId": "doc_123",
  "note": "This letter was written during the Berlin air raids"
}
```

#### `letter_update_context`
Update a context note.

**Input:**
```json
{
  "contextId": "ctx_456",
  "note": "Updated context information"
}
```

#### `letter_delete_context`
Delete a context note.

**Input:**
```json
{
  "contextId": "ctx_456"
}
```

#### `letter_list_context`
List all context notes for a letter.

**Input:**
```json
{
  "letterId": "doc_123"
}
```

### Health Check

#### `health_check`
Check the health status of the Letters app and MCP server.

**Input:**
```json
{}
```

**Output:**
```json
{
  "status": "ok",
  "message": "Letters app and MCP server are healthy",
  "appVersion": "flask-ocr-api",
  "timestamp": "2025-01-01T00:00:00Z"
}
```

## Cursor Integration

To use this MCP server with Cursor, add the following to your `mcp/servers.json`:

```json
{
  "servers": {
    "letters_mcp_readonly": {
      "command": "node",
      "args": ["/path/to/letters-mcp/dist/index.js"],
      "env": {
        "API_BASE_URL": "http://localhost:5001",
        "API_TOKEN": "${API_TOKEN_READONLY}",
        "TIMEOUT_MS": "120000",
        "MODE": "readonly"
      }
    },
    "letters_mcp_admin": {
      "command": "node",
      "args": ["/path/to/letters-mcp/dist/index.js"],
      "env": {
        "API_BASE_URL": "http://localhost:5001",
        "API_TOKEN": "${API_TOKEN_ADMIN}",
        "TIMEOUT_MS": "120000",
        "MODE": "admin"
      }
    }
  }
}
```

This configuration provides two MCP server instances:
- `letters_mcp_readonly`: For read-only access to search and view data
- `letters_mcp_admin`: For full CRUD access to manage all data

## Error Handling

All tools return responses with a `status` field that is either `"ok"` or `"error"`. Error responses include a descriptive `message` field explaining what went wrong.

Common error scenarios:
- Invalid input parameters
- Network timeouts
- API authentication failures
- Resource not found
- Server errors

## Safety Rules

- All inputs are validated using Zod schemas
- API calls have configurable timeouts
- Sensitive information is never logged
- All operations are logged for audit purposes
- The server gracefully handles errors without crashing

## Development

### Project Structure

```
letters-mcp/
├── src/
│   ├── index.ts              # MCP server bootstrap
│   ├── config.ts             # Configuration management
│   ├── client.ts             # API client wrapper
│   ├── schemas.ts            # Zod schemas
│   ├── tools/
│   │   ├── letters.ts        # Letter/document tools
│   │   ├── references.ts     # Reference/people tools
│   │   ├── relations.ts      # Letter-reference relations
│   │   ├── context.ts        # Context notes (placeholder)
│   │   └── health.ts         # Health check
│   └── tests/                # Test files
├── package.json
├── tsconfig.json
├── vitest.config.ts
└── README.md
```

### Adding New Tools

1. Create a new tool file in `src/tools/`
2. Define the tool schema and handler function
3. Add the tool to the registry in `src/index.ts`
4. Add tests in `src/tests/`
5. Update this README

### API Compatibility

This MCP server is designed to work with your existing Flask API structure. If you modify your API endpoints or data formats, you may need to update the corresponding client methods in `src/client.ts`.

## Troubleshooting

### Common Issues

1. **Connection refused**: Ensure your Letters Flask app is running on the configured port
2. **Authentication errors**: Check your API token configuration
3. **Timeout errors**: Increase the `TIMEOUT_MS` value for slow operations
4. **Build errors**: Ensure you're using Node.js 18+ and all dependencies are installed

### Debug Mode

Set `NODE_ENV=development` to enable additional logging:

```bash
NODE_ENV=development npm run dev
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the error messages in the MCP client
3. Check the Letters app logs
4. Create an issue with detailed error information
