-- CreateEnum
CREATE TYPE "public"."ReferenceType" AS ENUM ('PERSON', 'PLACE', 'EVENT', 'OTHER');

-- CreateEnum
CREATE TYPE "public"."CreatedBy" AS ENUM ('AUTO', 'HUMAN');

-- CreateTable
CREATE TABLE "public"."Reference" (
    "id" TEXT NOT NULL,
    "type" "public"."ReferenceType" NOT NULL,
    "canonicalName" TEXT NOT NULL,
    "notes" TEXT,
    "createdBy" "public"."CreatedBy" NOT NULL DEFAULT 'AUTO',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Reference_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."ReferenceVariant" (
    "id" TEXT NOT NULL,
    "parentId" TEXT NOT NULL,
    "label" TEXT NOT NULL,
    "createdBy" "public"."CreatedBy" NOT NULL DEFAULT 'AUTO',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ReferenceVariant_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."DocumentReference" (
    "id" TEXT NOT NULL,
    "documentId" TEXT NOT NULL,
    "referenceId" TEXT NOT NULL,
    "matchText" TEXT NOT NULL,
    "confidence" INTEGER NOT NULL,
    "role" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "DocumentReference_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "ReferenceVariant_parentId_label_key" ON "public"."ReferenceVariant"("parentId", "label");

-- CreateIndex
CREATE UNIQUE INDEX "DocumentReference_documentId_referenceId_matchText_key" ON "public"."DocumentReference"("documentId", "referenceId", "matchText");

-- AddForeignKey
ALTER TABLE "public"."ReferenceVariant" ADD CONSTRAINT "ReferenceVariant_parentId_fkey" FOREIGN KEY ("parentId") REFERENCES "public"."Reference"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."DocumentReference" ADD CONSTRAINT "DocumentReference_documentId_fkey" FOREIGN KEY ("documentId") REFERENCES "public"."Document"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."DocumentReference" ADD CONSTRAINT "DocumentReference_referenceId_fkey" FOREIGN KEY ("referenceId") REFERENCES "public"."Reference"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."AuditLog" ADD CONSTRAINT "AuditLog_reference_fkey" FOREIGN KEY ("targetId") REFERENCES "public"."Reference"("id") ON DELETE SET NULL ON UPDATE CASCADE;
