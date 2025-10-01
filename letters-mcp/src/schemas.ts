import { z } from 'zod';

// Base response schema
export const BaseResponseSchema = z.object({
  status: z.enum(['ok', 'error']),
  message: z.string(),
});

// Letter/Document schemas
export const LetterSummarySchema = z.object({
  id: z.string(),
  title: z.string(),
  date: z.string().optional(),
  language: z.string().optional(),
  summary: z.string().optional(),
  pageCount: z.number().optional(),
  peopleCount: z.number().optional(),
  status: z.string().optional(),
});

export const LetterSchema = z.object({
  id: z.string(),
  title: z.string(),
  date: z.string().optional(),
  language: z.string().optional(),
  summary: z.string().optional(),
  originalText: z.string().optional(),
  translatedText: z.string().optional(),
  fileSize: z.number().optional(),
  pageCount: z.number().optional(),
  people: z.array(z.string()).optional(),
  status: z.string().optional(),
  createdAt: z.string().optional(),
  updatedAt: z.string().optional(),
});

// Reference/Person schemas
export const ReferenceSchema = z.object({
  id: z.string(),
  type: z.enum(['person', 'place', 'event', 'other']),
  name: z.string(),
  aliases: z.array(z.string()).optional(),
  notes: z.string().optional(),
  context: z.string().optional(),
  firstMentioned: z.string().optional(),
  documentCount: z.number().optional(),
  createdAt: z.string().optional(),
  updatedAt: z.string().optional(),
});

// Context note schemas
export const ContextNoteSchema = z.object({
  id: z.string(),
  letterId: z.string(),
  note: z.string(),
  createdAt: z.string(),
  updatedAt: z.string().optional(),
});

// Input schemas for MCP tools
export const LettersSearchInputSchema = z.object({
  query: z.string().optional(),
  dateFrom: z.string().optional(),
  dateTo: z.string().optional(),
  language: z.string().optional(),
  page: z.number().min(1).default(1),
  pageSize: z.number().min(1).max(100).default(10),
});

export const LetterGetInputSchema = z.object({
  id: z.string().min(1),
});

export const LetterCreateInputSchema = z.object({
  title: z.string().min(1),
  date: z.string().optional(),
  language: z.string().optional(),
  summary: z.string().optional(),
  originalText: z.string().optional(),
  translatedText: z.string().optional(),
  fileSize: z.number().optional(),
  pageCount: z.number().optional(),
});

export const LetterUpdateInputSchema = z.object({
  id: z.string().min(1),
  title: z.string().optional(),
  date: z.string().optional(),
  language: z.string().optional(),
  summary: z.string().optional(),
  originalText: z.string().optional(),
  translatedText: z.string().optional(),
  fileSize: z.number().optional(),
  pageCount: z.number().optional(),
  regenerateSummary: z.boolean().optional(),
});

export const LetterDeleteInputSchema = z.object({
  id: z.string().min(1),
});

export const ReferencesSearchInputSchema = z.object({
  query: z.string().optional(),
  type: z.enum(['person', 'place', 'event', 'other']).optional(),
  page: z.number().min(1).default(1),
  pageSize: z.number().min(1).max(100).default(10),
});

export const ReferenceGetInputSchema = z.object({
  id: z.string().min(1),
});

export const ReferenceCreateInputSchema = z.object({
  type: z.enum(['person', 'place', 'event', 'other']),
  name: z.string().min(1),
  aliases: z.array(z.string()).optional(),
  notes: z.string().optional(),
  context: z.string().optional(),
});

export const ReferenceUpdateInputSchema = z.object({
  id: z.string().min(1),
  name: z.string().optional(),
  aliases: z.array(z.string()).optional(),
  notes: z.string().optional(),
  context: z.string().optional(),
});

export const ReferenceDeleteInputSchema = z.object({
  id: z.string().min(1),
});

export const LetterAttachReferenceInputSchema = z.object({
  letterId: z.string().min(1),
  referenceId: z.string().min(1),
  role: z.string().optional(),
});

export const LetterDetachReferenceInputSchema = z.object({
  letterId: z.string().min(1),
  referenceId: z.string().min(1),
});

export const LetterListReferencesInputSchema = z.object({
  letterId: z.string().min(1),
});

export const LetterAddContextInputSchema = z.object({
  letterId: z.string().min(1),
  note: z.string().min(1),
});

export const LetterUpdateContextInputSchema = z.object({
  contextId: z.string().min(1),
  note: z.string().min(1),
});

export const LetterDeleteContextInputSchema = z.object({
  contextId: z.string().min(1),
});

export const LetterListContextInputSchema = z.object({
  letterId: z.string().min(1),
});

export const HealthCheckInputSchema = z.object({});

// Output schemas for MCP tools
export const LettersSearchOutputSchema = BaseResponseSchema.extend({
  items: z.array(LetterSummarySchema).optional(),
  total: z.number().optional(),
  page: z.number().optional(),
  pageSize: z.number().optional(),
});

export const LetterGetOutputSchema = BaseResponseSchema.extend({
  item: LetterSchema.nullable().optional(),
});

export const LetterCreateOutputSchema = BaseResponseSchema.extend({
  item: LetterSchema.optional(),
});

export const LetterUpdateOutputSchema = BaseResponseSchema.extend({
  item: LetterSchema.optional(),
  regeneratedSummary: z.string().optional(),
  regeneratedPeople: z.array(z.string()).optional(),
});

export const LetterDeleteOutputSchema = BaseResponseSchema;

export const ReferencesSearchOutputSchema = BaseResponseSchema.extend({
  items: z.array(ReferenceSchema).optional(),
  total: z.number().optional(),
  page: z.number().optional(),
  pageSize: z.number().optional(),
});

export const ReferenceGetOutputSchema = BaseResponseSchema.extend({
  item: ReferenceSchema.nullable().optional(),
});

export const ReferenceCreateOutputSchema = BaseResponseSchema.extend({
  item: ReferenceSchema.optional(),
});

export const ReferenceUpdateOutputSchema = BaseResponseSchema.extend({
  item: ReferenceSchema.optional(),
});

export const ReferenceDeleteOutputSchema = BaseResponseSchema;

export const LetterAttachReferenceOutputSchema = BaseResponseSchema.extend({
  relation: z.object({
    letterId: z.string(),
    referenceId: z.string(),
    role: z.string().optional(),
  }).optional(),
});

export const LetterDetachReferenceOutputSchema = BaseResponseSchema;

export const LetterListReferencesOutputSchema = BaseResponseSchema.extend({
  items: z.array(ReferenceSchema).optional(),
});

export const LetterAddContextOutputSchema = BaseResponseSchema.extend({
  item: ContextNoteSchema.optional(),
});

export const LetterUpdateContextOutputSchema = BaseResponseSchema.extend({
  item: ContextNoteSchema.optional(),
});

export const LetterDeleteContextOutputSchema = BaseResponseSchema;

export const LetterListContextOutputSchema = BaseResponseSchema.extend({
  items: z.array(ContextNoteSchema).optional(),
});

export const HealthCheckOutputSchema = BaseResponseSchema.extend({
  appVersion: z.string().optional(),
  timestamp: z.string().optional(),
});

// Type exports
export type LetterSummary = z.infer<typeof LetterSummarySchema>;
export type Letter = z.infer<typeof LetterSchema>;
export type Reference = z.infer<typeof ReferenceSchema>;
export type ContextNote = z.infer<typeof ContextNoteSchema>;

export type LettersSearchInput = z.infer<typeof LettersSearchInputSchema>;
export type LetterGetInput = z.infer<typeof LetterGetInputSchema>;
export type LetterCreateInput = z.infer<typeof LetterCreateInputSchema>;
export type LetterUpdateInput = z.infer<typeof LetterUpdateInputSchema>;
export type LetterDeleteInput = z.infer<typeof LetterDeleteInputSchema>;

export type ReferencesSearchInput = z.infer<typeof ReferencesSearchInputSchema>;
export type ReferenceGetInput = z.infer<typeof ReferenceGetInputSchema>;
export type ReferenceCreateInput = z.infer<typeof ReferenceCreateInputSchema>;
export type ReferenceUpdateInput = z.infer<typeof ReferenceUpdateInputSchema>;
export type ReferenceDeleteInput = z.infer<typeof ReferenceDeleteInputSchema>;

export type LetterAttachReferenceInput = z.infer<typeof LetterAttachReferenceInputSchema>;
export type LetterDetachReferenceInput = z.infer<typeof LetterDetachReferenceInputSchema>;
export type LetterListReferencesInput = z.infer<typeof LetterListReferencesInputSchema>;

export type LetterAddContextInput = z.infer<typeof LetterAddContextInputSchema>;
export type LetterUpdateContextInput = z.infer<typeof LetterUpdateContextInputSchema>;
export type LetterDeleteContextInput = z.infer<typeof LetterDeleteContextInputSchema>;
export type LetterListContextInput = z.infer<typeof LetterListContextInputSchema>;

export type HealthCheckInput = z.infer<typeof HealthCheckInputSchema>;

export type LettersSearchOutput = z.infer<typeof LettersSearchOutputSchema>;
export type LetterGetOutput = z.infer<typeof LetterGetOutputSchema>;
export type LetterCreateOutput = z.infer<typeof LetterCreateOutputSchema>;
export type LetterUpdateOutput = z.infer<typeof LetterUpdateOutputSchema>;
export type LetterDeleteOutput = z.infer<typeof LetterDeleteOutputSchema>;

export type ReferencesSearchOutput = z.infer<typeof ReferencesSearchOutputSchema>;
export type ReferenceGetOutput = z.infer<typeof ReferenceGetOutputSchema>;
export type ReferenceCreateOutput = z.infer<typeof ReferenceCreateOutputSchema>;
export type ReferenceUpdateOutput = z.infer<typeof ReferenceUpdateOutputSchema>;
export type ReferenceDeleteOutput = z.infer<typeof ReferenceDeleteOutputSchema>;

export type LetterAttachReferenceOutput = z.infer<typeof LetterAttachReferenceOutputSchema>;
export type LetterDetachReferenceOutput = z.infer<typeof LetterDetachReferenceOutputSchema>;
export type LetterListReferencesOutput = z.infer<typeof LetterListReferencesOutputSchema>;

export type LetterAddContextOutput = z.infer<typeof LetterAddContextOutputSchema>;
export type LetterUpdateContextOutput = z.infer<typeof LetterUpdateContextOutputSchema>;
export type LetterDeleteContextOutput = z.infer<typeof LetterDeleteContextOutputSchema>;
export type LetterListContextOutput = z.infer<typeof LetterListContextOutputSchema>;

export type HealthCheckOutput = z.infer<typeof HealthCheckOutputSchema>;
