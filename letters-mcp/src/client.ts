import fetch from 'node-fetch';
import { config, getApiHeaders, buildApiUrl, logCall } from './config.js';
import type { 
  Letter, 
  Reference, 
  ContextNote,
  LettersSearchInput,
  ReferencesSearchInput,
  LetterCreateInput,
  LetterUpdateInput,
  ReferenceCreateInput,
  ReferenceUpdateInput,
  LetterAttachReferenceInput,
  LetterAddContextInput,
  LetterUpdateContextInput
} from './schemas.js';

// API Response types
interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  documents?: T[];
  people?: T[];
  references?: T[];
  document?: T;
  person?: T;
  reference?: T;
  error?: string;
  message?: string;
  total?: number;
  results?: T[];
  query?: string;
  person_name?: string;
  regenerated_summary?: string;
  regenerated_people?: string[];
}

// HTTP Client class
export class LettersApiClient {
  private baseUrl: string;
  private headers: Record<string, string>;
  private timeout: number;

  constructor() {
    this.baseUrl = config.API_BASE_URL;
    this.headers = getApiHeaders();
    this.timeout = config.TIMEOUT_MS;
  }

  private async makeRequest<T>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE',
    endpoint: string,
    body?: any
  ): Promise<T> {
    const url = buildApiUrl(endpoint);
    const startTime = Date.now();
    
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(url, {
        method,
        headers: this.headers,
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      const duration = Date.now() - startTime;
      logCall(`${method} ${endpoint}`, duration, response.ok ? 'success' : 'error');

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const data = await response.json() as ApiResponse<T>;
      
      if (!data.success && data.error) {
        throw new Error(data.error);
      }

      return data as T;
    } catch (error) {
      const duration = Date.now() - startTime;
      logCall(`${method} ${endpoint}`, duration, 'error');
      
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new Error(`Request timeout after ${this.timeout}ms`);
        }
        throw error;
      }
      throw new Error(`Unknown error: ${error}`);
    }
  }

  // Letters/Documents API
  async searchLetters(params: LettersSearchInput): Promise<ApiResponse<Letter[]>> {
    const queryParams = new URLSearchParams();
    
    if (params.query) queryParams.append('q', params.query);
    if (params.language) queryParams.append('language', params.language);
    if (params.dateFrom) queryParams.append('dateFrom', params.dateFrom);
    if (params.dateTo) queryParams.append('dateTo', params.dateTo);
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.pageSize) queryParams.append('pageSize', params.pageSize.toString());

    const endpoint = `/search?${queryParams.toString()}`;
    return this.makeRequest<ApiResponse<Letter[]>>('GET', endpoint);
  }

  async getLetter(id: string): Promise<ApiResponse<Letter>> {
    return this.makeRequest<ApiResponse<Letter>>('GET', `/documents/${id}`);
  }

  async createLetter(data: LetterCreateInput): Promise<ApiResponse<Letter>> {
    // Note: Your current API doesn't have a direct create endpoint
    // This would need to be implemented in your Flask app
    throw new Error('Letter creation not yet implemented in the API');
  }

  async updateLetter(id: string, data: Partial<LetterUpdateInput>): Promise<ApiResponse<Letter>> {
    return this.makeRequest<ApiResponse<Letter>>('PUT', `/documents/${id}`, data);
  }

  async deleteLetter(id: string): Promise<ApiResponse<void>> {
    return this.makeRequest<ApiResponse<void>>('DELETE', `/documents/${id}`);
  }

  async listLetters(): Promise<ApiResponse<Letter[]>> {
    return this.makeRequest<ApiResponse<Letter[]>>('GET', '/documents');
  }

  // References API (new with stable IDs)
  async searchReferences(params: ReferencesSearchInput): Promise<ApiResponse<Reference[]>> {
    const queryParams = new URLSearchParams();
    
    if (params.query) queryParams.append('query', params.query);
    if (params.type) queryParams.append('type', params.type);
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.pageSize) queryParams.append('pageSize', params.pageSize.toString());

    const endpoint = `/api/references?${queryParams.toString()}`;
    return this.makeRequest<ApiResponse<Reference[]>>('GET', endpoint);
  }

  async getReference(id: string): Promise<ApiResponse<Reference>> {
    return this.makeRequest<ApiResponse<Reference>>('GET', `/api/references/${id}`);
  }

  async createReference(data: ReferenceCreateInput): Promise<ApiResponse<Reference>> {
    return this.makeRequest<ApiResponse<Reference>>('POST', '/api/references', {
      type: data.type,
      name: data.name,
      aliases: data.aliases || [],
      notes: data.notes || data.context || '',
    });
  }

  async updateReference(id: string, data: Partial<ReferenceUpdateInput>): Promise<ApiResponse<Reference>> {
    return this.makeRequest<ApiResponse<Reference>>('PUT', `/api/references/${id}`, {
      name: data.name,
      aliases: data.aliases,
      notes: data.notes || data.context,
    });
  }

  async deleteReference(id: string): Promise<ApiResponse<void>> {
    return this.makeRequest<ApiResponse<void>>('DELETE', `/api/references/${id}`);
  }

  async listReferences(): Promise<ApiResponse<Reference[]>> {
    return this.makeRequest<ApiResponse<Reference[]>>('GET', '/api/references');
  }

  async mergeReferences(sourceId: string, targetId: string): Promise<ApiResponse<void>> {
    return this.makeRequest<ApiResponse<void>>('POST', `/api/references/${sourceId}/merge`, {
      targetId: targetId,
    });
  }

  // Relations API (updated for new reference system)
  async attachReferenceToLetter(letterId: string, referenceId: string, role?: string): Promise<ApiResponse<void>> {
    return this.makeRequest<ApiResponse<void>>('POST', `/api/documents/${letterId}/references`, {
      referenceId: referenceId,
      role: role,
    });
  }

  async detachReferenceFromLetter(letterId: string, referenceId: string): Promise<ApiResponse<void>> {
    return this.makeRequest<ApiResponse<void>>('DELETE', `/api/documents/${letterId}/references`, {
      referenceId: referenceId,
    });
  }

  async listLetterReferences(letterId: string): Promise<ApiResponse<Reference[]>> {
    return this.makeRequest<ApiResponse<Reference[]>>('GET', `/api/documents/${letterId}/references`);
  }

  // Context Notes API
  async addContextToLetter(letterId: string, note: string): Promise<ApiResponse<ContextNote>> {
    return this.makeRequest<ApiResponse<ContextNote>>('POST', `/documents/${letterId}/context`, { note });
  }

  async updateContextNote(contextId: string, note: string): Promise<ApiResponse<ContextNote>> {
    return this.makeRequest<ApiResponse<ContextNote>>('PUT', `/context/${contextId}`, { note });
  }

  async deleteContextNote(contextId: string): Promise<ApiResponse<void>> {
    return this.makeRequest<ApiResponse<void>>('DELETE', `/context/${contextId}`);
  }

  async listLetterContext(letterId: string): Promise<ApiResponse<ContextNote[]>> {
    return this.makeRequest<ApiResponse<ContextNote[]>>('GET', `/documents/${letterId}/context`);
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<{ status: string; timestamp: string; service: string }>> {
    return this.makeRequest<ApiResponse<{ status: string; timestamp: string; service: string }>>('GET', '/status');
  }
}

// Export singleton instance
export const apiClient = new LettersApiClient();
