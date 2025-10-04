-- Fix the updatedAt field to have a default value
ALTER TABLE "Reference" ALTER COLUMN "updatedAt" SET DEFAULT CURRENT_TIMESTAMP;