#!/usr/bin/env python3

"""
Local storage system for OCR results.
Supports dual-mode: local file storage or Cloudflare R2 cloud storage.
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class LocalOCRStorage:
    """
    Storage system for OCR documents and people.
    Supports dual-mode operation:
    - Local file storage (default, for development)
    - Cloudflare R2 storage (for production, when USE_R2=true)
    """
    
    def __init__(self, storage_dir: str = "ocr_storage"):
        self.storage_dir = Path(storage_dir)
        self.documents_dir = self.storage_dir / "documents"
        self.people_dir = self.storage_dir / "people"
        self.metadata_file = self.storage_dir / "metadata.json"
        
        # Check if R2 mode is enabled
        self.use_r2 = os.getenv('USE_R2', 'false').lower() == 'true'
        self.r2 = None
        
        if self.use_r2:
            # Initialize R2 storage
            try:
                from scripts.r2_storage import R2Storage
                self.r2 = R2Storage()
                print("🌐 Using Cloudflare R2 for storage")
            except Exception as e:
                print(f"⚠️  Failed to initialize R2, falling back to local storage: {e}")
                self.use_r2 = False
        
        if not self.use_r2:
            # Create local directories for local mode
            self.documents_dir.mkdir(parents=True, exist_ok=True)
            self.people_dir.mkdir(parents=True, exist_ok=True)
            print("💾 Using local file storage")
        
        # Load existing metadata (from R2 or local)
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Load existing metadata from R2 or local file."""
        if self.use_r2 and self.r2:
            # Load from R2
            try:
                metadata = self.r2.get_metadata()
                if metadata:
                    return metadata
            except Exception as e:
                print(f"⚠️  Error loading metadata from R2: {e}")
        
        # Load from local file (fallback or default)
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "documents": {},
            "people": {},
            "context_notes": {},
            "references": {},
            "document_references": {},
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_metadata(self):
        """Save metadata to R2 or local file."""
        self.metadata["last_updated"] = datetime.now().isoformat()
        
        if self.use_r2 and self.r2:
            # Save to R2
            try:
                self.r2.save_metadata(self.metadata)
            except Exception as e:
                print(f"⚠️  Error saving metadata to R2: {e}")
                # Fall through to save locally as backup
        
        # Always save locally as well (backup in R2 mode, primary in local mode)
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            if not self.use_r2:
                # In local mode, this is critical
                raise
            print(f"⚠️  Error saving metadata locally (backup): {e}")
    
    def add_document(self, document_data: Dict, doc_id: str = None) -> str:
        """Add a processed document to local storage."""
        if doc_id is None:
            doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize new fields if not present
        if "reviews" not in document_data:
            document_data["reviews"] = []
        if "history" not in document_data:
            document_data["history"] = []
        if "sender" not in document_data:
            document_data["sender"] = None
        if "recipient" not in document_data:
            document_data["recipient"] = None
        if "sender_location" not in document_data:
            document_data["sender_location"] = None
        if "recipient_location" not in document_data:
            document_data["recipient_location"] = None
        
        # Save document content to R2 and/or local
        if self.use_r2 and self.r2:
            # Save to R2
            try:
                self.r2.save_document(doc_id, document_data)
            except Exception as e:
                print(f"⚠️  Error saving document {doc_id} to R2: {e}")
        
        # Always save locally as well (backup in R2 mode, primary in local mode)
        doc_file = self.documents_dir / f"{doc_id}.json"
        with open(doc_file, 'w') as f:
            json.dump(document_data, f, indent=2)
        
        # Count pages from image files if available
        page_count = self._count_document_pages(doc_id)
        
        # Update metadata
        self.metadata["documents"][doc_id] = {
            "title": document_data.get("title", "Untitled"),
            "date_processed": document_data.get("date_processed", datetime.now().isoformat()),
            "source_language": document_data.get("source_language", "unknown"),
            "target_language": document_data.get("target_language", "en"),
            "file_size": document_data.get("file_size", 0),
            "people_count": len(document_data.get("people", [])),
            "summary": document_data.get("summary", "")[:100] + "..." if len(document_data.get("summary", "")) > 100 else document_data.get("summary", ""),
            "page_count": page_count,
            "status": document_data.get("status", "New")
        }
        
        # Add people to metadata
        for person in document_data.get("people", []):
            # Handle both string and dict formats
            if isinstance(person, dict):
                person_name = person.get("normalized_name", "")
                original_name = person.get("original_name", "")
            else:
                person_name = str(person)
                original_name = person_name
            
            if person_name:
                if person_name not in self.metadata["people"]:
                    self.metadata["people"][person_name] = {
                        "aliases": [original_name],
                        "first_mentioned": document_data.get("date_processed", datetime.now().isoformat()),
                        "documents": [doc_id]
                    }
                else:
                    # Add alias if new
                    if original_name not in self.metadata["people"][person_name]["aliases"]:
                        self.metadata["people"][person_name]["aliases"].append(original_name)
                    # Add document if new
                    if doc_id not in self.metadata["people"][person_name]["documents"]:
                        self.metadata["people"][person_name]["documents"].append(doc_id)
        
        self._save_metadata()
        return doc_id
    
    def _count_document_pages(self, doc_id: str) -> int:
        """Count the number of pages for a document based on image files."""
        try:
            work_dir = Path("letters/work")
            page_count = 0
            
            # Look for image files with the document ID
            for i in range(1, 100):  # Check up to 100 pages
                image_patterns = [
                    f"{doc_id}_page_{i:03d}.png",
                    f"{doc_id}_page_{i}.png",
                    f"{doc_id}_{i}.png"
                ]
                
                found = False
                for pattern in image_patterns:
                    if (work_dir / pattern).exists():
                        page_count = i
                        found = True
                        break
                
                if not found:
                    break
            
            return page_count
        except Exception as e:
            print(f"Error counting pages for {doc_id}: {e}")
            return 0
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """Get a document by ID from R2 or local storage."""
        document = None
        
        # Try R2 first if enabled
        if self.use_r2 and self.r2:
            try:
                document = self.r2.get_document(doc_id)
            except Exception as e:
                print(f"⚠️  Error loading document {doc_id} from R2: {e}")
        
        # Fallback to local file if R2 failed or not enabled
        if not document:
            doc_file = self.documents_dir / f"{doc_id}.json"
            if doc_file.exists():
                with open(doc_file, 'r') as f:
                    document = json.load(f)
        
        if document:
            # Add the document ID to the document object
            document['id'] = doc_id
            
            # Add metadata fields if available (but don't override document values)
            if doc_id in self.metadata["documents"]:
                metadata = self.metadata["documents"][doc_id]
                # Only use metadata values if document doesn't have them
                if 'page_count' not in document or document['page_count'] is None:
                    document['page_count'] = metadata.get('page_count', 0)
                if 'people_count' not in document or document['people_count'] is None:
                    document['people_count'] = metadata.get('people_count', 0)
            
            # Ensure new fields exist for backwards compatibility
            if "reviews" not in document:
                document["reviews"] = []
            if "history" not in document:
                document["history"] = []
            if "sender" not in document:
                document["sender"] = None
            if "recipient" not in document:
                document["recipient"] = None
            if "sender_location" not in document:
                document["sender_location"] = None
            if "recipient_location" not in document:
                document["recipient_location"] = None
            if "status" not in document:
                document["status"] = "new"
            
            # Resolve all people names to their CURRENT canonical names
            # This ensures renamed references always display with updated names
            if "people" in document and isinstance(document["people"], list):
                resolved_people = []
                for person in document["people"]:
                    # Handle both string and dict format
                    person_name = person if isinstance(person, str) else person.get("original_name", person)
                    canonical_name = self._resolve_to_canonical_name(person_name)
                    resolved_people.append(canonical_name if canonical_name else person_name)
                document["people"] = resolved_people
            
            # Resolve sender and recipient to canonical names
            if document.get("sender"):
                canonical_sender = self._resolve_to_canonical_name(document["sender"])
                if canonical_sender:
                    document["sender"] = canonical_sender
            
            if document.get("recipient"):
                canonical_recipient = self._resolve_to_canonical_name(document["recipient"])
                if canonical_recipient:
                    document["recipient"] = canonical_recipient
            
            return document
        
        # Document not found in R2 or local storage
        # Clean up orphaned metadata
        if doc_id in self.metadata["documents"]:
            print(f"Warning: Document {doc_id} has metadata but no file. Cleaning up...")
            del self.metadata["documents"][doc_id]
            self._save_metadata()
        
        return None
    
    def update_document(self, doc_id: str, updates: Dict, regenerate_summary: bool = False) -> bool:
        """Update a document with new data in R2 or local storage."""
        try:
            # Get existing document (handles R2/local automatically)
            document = self.get_document(doc_id)
            if not document:
                return False
            
            # Update the document
            document.update(updates)
            
            # Regenerate summary if requested and translation text is available
            if regenerate_summary and "translated_text" in updates:
                try:
                    from .ai_processor import AIProcessor
                    from .fallback_ai_processor import FallbackAIProcessor
                    
                    # Try AI processor first, fallback to rule-based
                    try:
                        ai_processor = AIProcessor()
                        ai_result = ai_processor.process_document(
                            updates["translated_text"],
                            source_language=updates.get("source_language", "unknown"),
                            document_date=document.get("date_processed", datetime.now().isoformat())
                        )
                        document["summary"] = ai_result.get("summary", document.get("summary", ""))
                        document["people"] = ai_result.get("people", document.get("people", []))
                    except Exception as e:
                        print(f"AI processor failed, using fallback: {e}")
                        fallback_processor = FallbackAIProcessor()
                        fallback_result = fallback_processor.process_document(
                            updates["translated_text"],
                            source_language=updates.get("source_language", "unknown"),
                            document_date=document.get("date_processed", datetime.now().isoformat())
                        )
                        document["summary"] = fallback_result.get("summary", document.get("summary", ""))
                        document["people"] = fallback_result.get("people", document.get("people", []))
                    
                    # Update the updates dict to include the regenerated summary
                    updates["summary"] = document["summary"]
                    updates["people"] = document["people"]
                    
                except Exception as e:
                    print(f"Error regenerating summary: {e}")
                    # Continue with update even if summary regeneration fails
            
            # Save updated document to R2 and/or local
            if self.use_r2 and self.r2:
                try:
                    self.r2.save_document(doc_id, document)
                except Exception as e:
                    print(f"⚠️  Error saving document {doc_id} to R2: {e}")
            
            # Always save locally as well (backup in R2 mode, primary in local mode)
            doc_file = self.documents_dir / f"{doc_id}.json"
            with open(doc_file, 'w') as f:
                json.dump(document, f, indent=2)
            
            # Update metadata
            if doc_id in self.metadata["documents"]:
                metadata = self.metadata["documents"][doc_id]
                
                # Update metadata fields if they exist in updates
                if "title" in updates:
                    metadata["title"] = updates["title"]
                if "summary" in updates:
                    metadata["summary"] = updates["summary"][:100] + "..." if len(updates["summary"]) > 100 else updates["summary"]
                if "people" in updates:
                    metadata["people_count"] = len(updates["people"])
                if "source_language" in updates:
                    metadata["source_language"] = updates["source_language"]
                if "target_language" in updates:
                    metadata["target_language"] = updates["target_language"]
                if "status" in updates:
                    metadata["status"] = updates["status"]
                if "sender" in updates:
                    metadata["sender"] = updates["sender"]
                if "recipient" in updates:
                    metadata["recipient"] = updates["recipient"]
                
                self._save_metadata()
            
            return True
            
        except Exception as e:
            print(f"Error updating document {doc_id}: {e}")
            return False
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document and its metadata."""
        try:
            # Remove document file
            doc_file = self.documents_dir / f"{doc_id}.json"
            if doc_file.exists():
                doc_file.unlink()
            
            # Remove from metadata
            if doc_id in self.metadata["documents"]:
                del self.metadata["documents"][doc_id]
                
                # Remove from people's document lists
                people_to_remove = []
                for person_name, person_data in self.metadata["people"].items():
                    if doc_id in person_data.get("documents", []):
                        person_data["documents"].remove(doc_id)
                        
                        # Mark person for removal if no documents left
                        if not person_data["documents"]:
                            people_to_remove.append(person_name)
                
                # Remove people with no documents
                for person_name in people_to_remove:
                    del self.metadata["people"][person_name]
                
                self._save_metadata()
            
            return True
            
        except Exception as e:
            print(f"Error deleting document {doc_id}: {e}")
            return False
    
    def list_documents(self) -> List[Dict]:
        """List all documents with metadata."""
        return list(self.metadata["documents"].items())

    # -----------------------------
    # Reviews and History
    # -----------------------------
    def add_review(self, doc_id: str, user_id: str, username: str, notes: str = None) -> Optional[Dict]:
        """Add or toggle a review for a document. If user already reviewed, removes the review."""
        try:
            doc = self.get_document(doc_id)
            if doc is None:
                return None
            
            # Check if user already reviewed
            reviews = doc.get("reviews", [])
            user_review_index = -1
            for i, r in enumerate(reviews):
                if r.get("userId") == user_id:
                    user_review_index = i
                    break
            
            if user_review_index >= 0:
                # User already reviewed - remove the review (toggle off)
                removed_review = reviews.pop(user_review_index)
                doc["reviews"] = reviews
                
                # Save document
                doc_file = self.documents_dir / f"{doc_id}.json"
                with open(doc_file, 'w') as f:
                    json.dump(doc, f, indent=2)
                
                # Log history
                self.log_history(doc_id, username, "unreviewed", f"unmarked document as reviewed")
                
                # Return special indicator that review was removed
                return {"removed": True, "userId": user_id}
            else:
                # Add new review
                review = {
                    "userId": user_id,
                    "username": username,
                    "timestamp": datetime.now().isoformat(),
                    "notes": notes or ""
                }
                reviews.append(review)
                doc["reviews"] = reviews
                
                # Save document
                doc_file = self.documents_dir / f"{doc_id}.json"
                with open(doc_file, 'w') as f:
                    json.dump(doc, f, indent=2)
                
                # Log history
                self.log_history(doc_id, username, "reviewed", f"marked document as reviewed")
                
                return review
        except Exception as e:
            print(f"Error toggling review for {doc_id}: {e}")
            return None
    
    def get_reviews(self, doc_id: str) -> List[Dict]:
        """Get all reviews for a document."""
        try:
            doc = self.get_document(doc_id)
            if doc is None:
                return []
            return doc.get("reviews", [])
        except Exception as e:
            print(f"Error getting reviews for {doc_id}: {e}")
            return []
    
    def log_history(self, doc_id: str, username: str, action: str, details: str) -> bool:
        """Add a history entry to a document."""
        try:
            doc = self.get_document(doc_id)
            if doc is None:
                return False
            
            # Format timestamp for display
            now = datetime.now()
            timestamp_display = now.strftime("%b %d, %Y")
            
            # Get document title for display
            doc_title = doc.get("title", "").split(" - ")[0] if doc.get("title") else doc_id
            
            # Create formatted history entry
            history_entry = {
                "timestamp": now.isoformat(),
                "timestampDisplay": timestamp_display,
                "username": username,
                "action": action,
                "details": details,
                "formattedMessage": f"{timestamp_display} - {username} {details}"
            }
            
            history = doc.get("history", [])
            history.append(history_entry)
            doc["history"] = history
            
            # Save document
            doc_file = self.documents_dir / f"{doc_id}.json"
            with open(doc_file, 'w') as f:
                json.dump(doc, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error logging history for {doc_id}: {e}")
            return False
    
    def get_history(self, doc_id: str) -> List[Dict]:
        """Get history log for a document."""
        try:
            doc = self.get_document(doc_id)
            if doc is None:
                return []
            history = doc.get("history", [])
            # Return in reverse chronological order (newest first)
            return sorted(history, key=lambda x: x.get("timestamp", ""), reverse=True)
        except Exception as e:
            print(f"Error getting history for {doc_id}: {e}")
            return []

    # -----------------------------
    # Context Notes (Per-letter)
    # -----------------------------
    def add_context_note(self, letter_id: str, username: str, note: str) -> Optional[Dict]:
        """Add a context note to a letter and return created note."""
        try:
            # Ensure document exists
            if letter_id not in self.metadata["documents"]:
                return None

            # Initialize context list on document file if needed
            doc = self.get_document(letter_id)
            if doc is None:
                return None

            context_list = doc.get("context_notes", [])

            # Create note object
            context_id = f"ctx_{datetime.now().strftime('%Y%m%d_%H%M%S%f')}"
            created_at = datetime.now().isoformat()
            note_obj = {
                "id": context_id,
                "letterId": letter_id,
                "username": username,
                "note": note,
                "createdAt": created_at
            }

            context_list.append(note_obj)
            doc["context_notes"] = context_list

            # Save updated document to R2 and/or local
            if self.use_r2 and self.r2:
                try:
                    self.r2.save_document(letter_id, doc)
                except Exception as e:
                    print(f"⚠️  Error saving document {letter_id} to R2: {e}")
            
            # Always save locally as well (backup in R2 mode, primary in local mode)
            doc_file = self.documents_dir / f"{letter_id}.json"
            with open(doc_file, 'w') as f:
                json.dump(doc, f, indent=2)

            # Track in global index for quick lookup by id
            self.metadata.setdefault("context_notes", {})[context_id] = {
                "letterId": letter_id,
                "createdAt": created_at
            }
            self._save_metadata()
            return note_obj
        except Exception as e:
            print(f"Error adding context note to {letter_id}: {e}")
            return None

    def list_context_notes(self, letter_id: str) -> List[Dict]:
        """List all context notes for a letter."""
        try:
            doc = self.get_document(letter_id)
            if doc is None:
                return []
            return doc.get("context_notes", [])
        except Exception as e:
            print(f"Error listing context notes for {letter_id}: {e}")
            return []

    def update_context_note(self, context_id: str, note: str) -> Optional[Dict]:
        """Update a context note by ID and return the updated note."""
        try:
            # Find letter id from index
            ctx_meta = self.metadata.get("context_notes", {}).get(context_id)
            if not ctx_meta:
                return None
            letter_id = ctx_meta["letterId"]

            doc = self.get_document(letter_id)
            if doc is None:
                return None

            updated_at = datetime.now().isoformat()
            notes = doc.get("context_notes", [])
            updated_note = None
            for n in notes:
                if n.get("id") == context_id:
                    n["note"] = note
                    n["updatedAt"] = updated_at
                    updated_note = n
                    break

            if updated_note is None:
                return None

            # Save updated document to R2 and/or local
            if self.use_r2 and self.r2:
                try:
                    self.r2.save_document(letter_id, doc)
                except Exception as e:
                    print(f"⚠️  Error saving document {letter_id} to R2: {e}")
            
            # Always save locally as well (backup in R2 mode, primary in local mode)
            doc_file = self.documents_dir / f"{letter_id}.json"
            with open(doc_file, 'w') as f:
                json.dump(doc, f, indent=2)

            self._save_metadata()
            return updated_note
        except Exception as e:
            print(f"Error updating context note {context_id}: {e}")
            return None

    def delete_context_note(self, context_id: str) -> bool:
        """Delete a context note by ID."""
        try:
            ctx_meta = self.metadata.get("context_notes", {}).get(context_id)
            if not ctx_meta:
                return False
            letter_id = ctx_meta["letterId"]

            doc = self.get_document(letter_id)
            if doc is None:
                return False

            notes = doc.get("context_notes", [])
            filtered = [n for n in notes if n.get("id") != context_id]
            if len(filtered) == len(notes):
                return False

            doc["context_notes"] = filtered
            
            # Save updated document to R2 and/or local
            if self.use_r2 and self.r2:
                try:
                    self.r2.save_document(letter_id, doc)
                except Exception as e:
                    print(f"⚠️  Error saving document {letter_id} to R2: {e}")
            
            # Always save locally as well (backup in R2 mode, primary in local mode)
            doc_file = self.documents_dir / f"{letter_id}.json"
            with open(doc_file, 'w') as f:
                json.dump(doc, f, indent=2)

            # Remove from global index
            del self.metadata["context_notes"][context_id]
            self._save_metadata()
            return True
        except Exception as e:
            print(f"Error deleting context note {context_id}: {e}")
            return False
    
    def get_people(self) -> Dict:
        """Get all people with their metadata."""
        return self.metadata["people"]
    
    def get_people_with_documents(self) -> List[Dict]:
        """Get all people with their associated documents."""
        people_list = []
        for person_name, person_data in self.metadata["people"].items():
            # Get document details for each person
            document_details = []
            for doc_id in person_data.get("documents", []):
                if doc_id in self.metadata["documents"]:
                    doc_metadata = self.metadata["documents"][doc_id]
                    document_details.append({
                        "id": doc_id,
                        "title": doc_metadata.get("title", "Unknown"),
                        "date_processed": doc_metadata.get("date_processed", ""),
                        "source_language": doc_metadata.get("source_language", "unknown")
                    })
            
            # Get the properly-cased display name from aliases (first one that's not just lowercase)
            # or fall back to capitalizing the normalized name
            aliases = person_data.get("aliases", [])
            display_name = person_name  # Fallback to normalized name
            
            # Look for an alias with proper capitalization
            for alias in aliases:
                if alias != person_name and alias != alias.lower():
                    display_name = alias
                    break
            
            # If no properly-cased alias found, try title-casing the normalized name
            if display_name == person_name:
                display_name = person_name.title()
            
            people_list.append({
                "name": display_name,  # Use display name instead of normalized name
                "normalized_name": person_name,  # Keep normalized for lookups
                "aliases": person_data.get("aliases", []),
                "first_mentioned": person_data.get("first_mentioned", ""),
                "context": person_data.get("context", ""),
                "type": person_data.get("type", "person"),
                "secondary_references": person_data.get("secondary_references", []),
                "documents": document_details,
                "document_count": len(document_details)
            })
        
        # Sort by document count (most mentioned first)
        people_list.sort(key=lambda x: x["document_count"], reverse=True)
        return people_list
    
    def get_person_documents(self, person_name: str) -> List[Dict]:
        """Get all documents that mention a specific person."""
        normalized_name = self.normalize_name(person_name)
        
        if normalized_name not in self.metadata["people"]:
            return []
        
        person_data = self.metadata["people"][normalized_name]
        document_details = []
        
        for doc_id in person_data.get("documents", []):
            if doc_id in self.metadata["documents"]:
                doc_metadata = self.metadata["documents"][doc_id]
                # Get full document data
                full_doc = self.get_document(doc_id)
                if full_doc:
                    document_details.append({
                        "id": doc_id,
                        "title": doc_metadata.get("title", "Unknown"),
                        "date_processed": doc_metadata.get("date_processed", ""),
                        "source_language": doc_metadata.get("source_language", "unknown"),
                        "summary": doc_metadata.get("summary", ""),
                        "translated_text": full_doc.get("translated_text", ""),
                        "people_mentioned": full_doc.get("people", [])
                    })
        
        # Sort by date (most recent first)
        document_details.sort(key=lambda x: x["date_processed"], reverse=True)
        return document_details
    
    def _resolve_to_canonical_name(self, name: str) -> Optional[str]:
        """
        Resolve a person name (which might be old/outdated) to its current canonical name.
        Searches metadata['people'] to find the person by normalized name or alias,
        and returns the primary display name (first alias with proper casing).
        
        Args:
            name: The person name to resolve (could be old/outdated)
        
        Returns:
            The current canonical display name, or None if not found
        """
        if not name:
            return None
        
        normalized = self.normalize_name(name)
        
        # First, check if it's a direct key
        if normalized in self.metadata["people"]:
            person_data = self.metadata["people"][normalized]
            aliases = person_data.get("aliases", [])
            # Return the first alias with proper casing (primary canonical name)
            for alias in aliases:
                if alias != normalized and alias != alias.lower():
                    return alias
            # Fallback to title case
            return name.title()
        
        # Not a direct key - search aliases
        for key, person_data in self.metadata["people"].items():
            aliases = person_data.get("aliases", [])
            # Check if the name matches any alias (case-insensitive)
            if any(self.normalize_name(alias) == normalized for alias in aliases):
                # Found it! Return the primary canonical name (first properly-cased alias)
                for alias in aliases:
                    if alias != key and alias != alias.lower():
                        return alias
                # Fallback to title case of the key
                return key.title()
        
        # Not found anywhere - return None
        return None
    
    def normalize_name(self, name: str) -> str:
        """Normalize a name for consistent matching."""
        import re
        # Remove common titles and suffixes
        name = re.sub(r'\b(Mr|Mrs|Ms|Dr|Prof|Rev|Sir|Lady)\b\.?\s*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\b(Jr|Sr|III|IV|V)\b\.?$', '', name, flags=re.IGNORECASE)
        
        # Clean up whitespace and punctuation
        name = re.sub(r'[^\w\s]', '', name)
        name = ' '.join(name.split())
        
        return name.lower().strip()
    
    def add_person(self, name: str, aliases: List[str] = None, context: str = None) -> bool:
        """Add a new person to the database."""
        try:
            normalized_name = self.normalize_name(name)
            
            # Check if person already exists
            if normalized_name in self.metadata["people"]:
                return False
            
            # Prepare aliases list
            if aliases is None:
                aliases = []
            
            # Add the main name to aliases if not already present
            if name not in aliases:
                aliases.insert(0, name)
            
            # Create person data
            person_data = {
                "aliases": aliases,
                "first_mentioned": datetime.now().isoformat(),
                "documents": [],
                "context": context or ""
            }
            
            # Add to metadata
            self.metadata["people"][normalized_name] = person_data
            
            # Save metadata
            self._save_metadata()
            return True
            
        except Exception as e:
            print(f"Error adding person {name}: {e}")
            return False
    
    def merge_person(self, source_name: str, target_name: str) -> bool:
        """Merge a source person into a target person."""
        try:
            source_normalized = self.normalize_name(source_name)
            target_normalized = self.normalize_name(target_name)
            
            if source_normalized not in self.metadata["people"]:
                return False
            
            if target_normalized not in self.metadata["people"]:
                return False
            
            # Get both person data
            source_data = self.metadata["people"][source_normalized]
            target_data = self.metadata["people"][target_normalized]
            
            # Merge aliases
            source_aliases = source_data.get("aliases", [])
            target_aliases = target_data.get("aliases", [])
            
            # Combine aliases and remove duplicates
            combined_aliases = list(set(target_aliases + source_aliases))
            target_data["aliases"] = combined_aliases
            
            # Merge documents
            source_docs = source_data.get("documents", [])
            target_docs = target_data.get("documents", [])
            
            # Combine document lists and remove duplicates
            combined_docs = list(set(target_docs + source_docs))
            target_data["documents"] = combined_docs
            
            # Merge context if source has context and target doesn't
            if source_data.get("context") and not target_data.get("context"):
                target_data["context"] = source_data["context"]
            
            # Update all documents that reference the source person
            for doc_id in source_docs:
                if doc_id in self.metadata["documents"]:
                    doc_file = self.documents_dir / f"{doc_id}.json"
                    if doc_file.exists():
                        with open(doc_file, 'r') as f:
                            doc_data = json.load(f)
                        
                        # Update people in document
                        updated_people = []
                        for person in doc_data.get("people", []):
                            if isinstance(person, dict):
                                if person.get("normalized_name") == source_normalized:
                                    person["normalized_name"] = target_normalized
                                    person["original_name"] = target_name
                                updated_people.append(person)
                            else:
                                # Handle string format
                                if self.normalize_name(person) == source_normalized:
                                    updated_people.append(target_name)
                                else:
                                    updated_people.append(person)
                        
                        doc_data["people"] = updated_people
                        
                        # Save updated document
                        with open(doc_file, 'w') as f:
                            json.dump(doc_data, f, indent=2)
            
            # Remove the source person
            del self.metadata["people"][source_normalized]
            
            # Save metadata
            self._save_metadata()
            return True
            
        except Exception as e:
            print(f"Error merging person {source_name} into {target_name}: {e}")
            return False

    def add_person_to_document(self, doc_id: str, person_name: str) -> bool:
        """Add a person reference to a document."""
        try:
            doc_file = self.documents_dir / f"{doc_id}.json"
            if not doc_file.exists():
                return False
            
            with open(doc_file, 'r') as f:
                doc_data = json.load(f)
            
            # Check if person already exists in document
            existing_people = doc_data.get("people", [])
            for person in existing_people:
                if isinstance(person, dict):
                    if person.get("original_name", "").lower() == person_name.lower():
                        return False  # Person already exists
                else:
                    if person.lower() == person_name.lower():
                        return False  # Person already exists
            
            # Add person to document
            person_data = {
                "original_name": person_name,
                "normalized_name": self.normalize_name(person_name)
            }
            existing_people.append(person_data)
            doc_data["people"] = existing_people
            
            with open(doc_file, 'w') as f:
                json.dump(doc_data, f, indent=2)
            
            # Update person metadata
            normalized_name = self.normalize_name(person_name)
            if normalized_name not in self.metadata["people"]:
                # Create new person entry
                self.metadata["people"][normalized_name] = {
                    "aliases": [person_name],
                    "first_mentioned": datetime.now().isoformat(),
                    "documents": [doc_id],
                    "context": ""
                }
            else:
                # Add document to existing person
                person_data = self.metadata["people"][normalized_name]
                if doc_id not in person_data.get("documents", []):
                    person_data["documents"].append(doc_id)
            
            self._save_metadata()
            return True
            
        except Exception as e:
            print(f"Error adding person {person_name} to document {doc_id}: {e}")
            return False

    def remove_person_from_document(self, doc_id: str, person_name: str) -> bool:
        """Remove a person reference from a document."""
        try:
            doc_file = self.documents_dir / f"{doc_id}.json"
            if not doc_file.exists():
                return False
            
            with open(doc_file, 'r') as f:
                doc_data = json.load(f)
            
            # Remove person from document
            existing_people = doc_data.get("people", [])
            updated_people = []
            person_removed = False
            
            for person in existing_people:
                if isinstance(person, dict):
                    if person.get("original_name", "").lower() != person_name.lower():
                        updated_people.append(person)
                    else:
                        person_removed = True
                else:
                    if person.lower() != person_name.lower():
                        updated_people.append(person)
                    else:
                        person_removed = True
            
            if not person_removed:
                return False  # Person not found in document
            
            doc_data["people"] = updated_people
            
            with open(doc_file, 'w') as f:
                json.dump(doc_data, f, indent=2)
            
            # Update person metadata
            normalized_name = self.normalize_name(person_name)
            if normalized_name in self.metadata["people"]:
                person_data = self.metadata["people"][normalized_name]
                if doc_id in person_data.get("documents", []):
                    person_data["documents"].remove(doc_id)
                    
                    # If no documents left, remove person entirely
                    if not person_data.get("documents", []):
                        del self.metadata["people"][normalized_name]
            
            self._save_metadata()
            return True
            
        except Exception as e:
            print(f"Error removing person {person_name} from document {doc_id}: {e}")
            return False
    
    def update_person(self, old_name: str, new_name: str, new_context: str = None, 
                     new_type: str = None, new_aliases: List[str] = None, 
                     new_secondary_refs: List[str] = None) -> bool:
        """Update a person's name, context, type, aliases, and secondary references."""
        try:
            old_normalized = self.normalize_name(old_name)
            new_normalized = self.normalize_name(new_name)
            
            # First, check if old_normalized is directly in people
            if old_normalized not in self.metadata["people"]:
                # It might be an alias - search for it
                canonical_key = None
                for key, person_data in self.metadata["people"].items():
                    aliases = person_data.get("aliases", [])
                    # Check if old_name matches any alias (case-insensitive)
                    if any(self.normalize_name(alias) == old_normalized for alias in aliases):
                        canonical_key = key
                        break
                
                if canonical_key:
                    # Found it as an alias, use the canonical key
                    old_normalized = canonical_key
                    print(f"Resolved alias '{old_name}' to canonical '{canonical_key}'")
                else:
                    # Not found anywhere
                    return False
            
            # Get the person data
            person_data = self.metadata["people"][old_normalized]
            
            # Update the name if it changed
            if old_normalized != new_normalized:
                # Remove from old location
                del self.metadata["people"][old_normalized]
                
                # Add to new location
                self.metadata["people"][new_normalized] = person_data
                
                # Update aliases to make new_name the primary canonical name
                current_aliases = person_data.get("aliases", [])
                
                # KEEP all existing aliases (for backward compatibility with old document references)
                # But ensure new name is FIRST (primary display name)
                new_aliases = []
                
                # Add new canonical name as FIRST alias (primary)
                if new_name not in current_aliases:
                    new_aliases.append(new_name)
                
                # Keep all existing aliases that aren't the new name
                for alias in current_aliases:
                    if alias != new_name:
                        new_aliases.append(alias)
                
                # Also add normalized version if not already present
                if new_normalized not in new_aliases and new_normalized != new_name:
                    new_aliases.append(new_normalized)
                
                person_data["aliases"] = new_aliases
                
                # Update all documents that reference this person
                for doc_id in person_data.get("documents", []):
                    if doc_id in self.metadata["documents"]:
                        # Update the document's people list
                        doc_file = self.documents_dir / f"{doc_id}.json"
                        if doc_file.exists():
                            with open(doc_file, 'r') as f:
                                doc_data = json.load(f)
                            
                            # Update people in document
                            updated_people = []
                            for person in doc_data.get("people", []):
                                if isinstance(person, dict):
                                    if person.get("normalized_name") == old_normalized:
                                        person["normalized_name"] = new_normalized
                                        person["original_name"] = new_name
                                    updated_people.append(person)
                                else:
                                    # Handle string format
                                    if self.normalize_name(person) == old_normalized:
                                        updated_people.append(new_name)
                                    else:
                                        updated_people.append(person)
                            
                            doc_data["people"] = updated_people
                            
                            # Save updated document
                            with open(doc_file, 'w') as f:
                                json.dump(doc_data, f, indent=2)
            else:
                # Name normalized to same key, but display name might have changed
                # Update the primary display name in aliases
                if new_name != old_name:
                    current_aliases = person_data.get("aliases", [])
                    
                    # Remove old display name if present
                    new_aliases = [a for a in current_aliases if a != old_name]
                    
                    # Add new display name as first alias (primary)
                    if new_name not in new_aliases:
                        new_aliases.insert(0, new_name)
                    
                    person_data["aliases"] = new_aliases
                    
                    # Update all documents with the new display name
                    for doc_id in person_data.get("documents", []):
                        if doc_id in self.metadata["documents"]:
                            doc_file = self.documents_dir / f"{doc_id}.json"
                            if doc_file.exists():
                                with open(doc_file, 'r') as f:
                                    doc_data = json.load(f)
                                
                                # Update people in document
                                updated_people = []
                                for person in doc_data.get("people", []):
                                    if isinstance(person, str):
                                        # String format - update if it matches old_name
                                        if person == old_name or self.normalize_name(person) == old_normalized:
                                            updated_people.append(new_name)
                                        else:
                                            updated_people.append(person)
                                    else:
                                        updated_people.append(person)
                                
                                doc_data["people"] = updated_people
                                
                                with open(doc_file, 'w') as f:
                                    json.dump(doc_data, f, indent=2)
            
            # Update context if provided
            if new_context is not None:
                person_data["context"] = new_context
            
            # Update type if provided
            if new_type is not None:
                person_data["type"] = new_type
            
            # Update aliases if provided
            if new_aliases is not None:
                person_data["aliases"] = new_aliases
                # Ensure new_normalized is in the aliases
                if new_normalized not in person_data["aliases"]:
                    person_data["aliases"].append(new_normalized)
            else:
                # Update aliases to include the new name
                if new_normalized not in person_data.get("aliases", []):
                    person_data.setdefault("aliases", []).append(new_normalized)
            
            # Update secondary references if provided
            if new_secondary_refs is not None:
                person_data["secondary_references"] = new_secondary_refs
            
            self._save_metadata()
            return True
            
        except Exception as e:
            print(f"Error updating person {old_name}: {e}")
            return False
    
    def remove_person(self, person_name: str) -> bool:
        """Remove a person from the database and all documents."""
        try:
            normalized_name = self.normalize_name(person_name)
            
            if normalized_name not in self.metadata["people"]:
                return False
            
            person_data = self.metadata["people"][normalized_name]
            
            # Remove person from all documents
            for doc_id in person_data.get("documents", []):
                if doc_id in self.metadata["documents"]:
                    # Update the document's people list
                    doc_file = self.documents_dir / f"{doc_id}.json"
                    if doc_file.exists():
                        with open(doc_file, 'r') as f:
                            doc_data = json.load(f)
                        
                        # Remove person from document
                        updated_people = []
                        for person in doc_data.get("people", []):
                            if isinstance(person, dict):
                                if person.get("normalized_name") != normalized_name:
                                    updated_people.append(person)
                            else:
                                # Handle string format
                                if self.normalize_name(person) != normalized_name:
                                    updated_people.append(person)
                        
                        doc_data["people"] = updated_people
                        
                        # Update metadata people count
                        if doc_id in self.metadata["documents"]:
                            self.metadata["documents"][doc_id]["people_count"] = len(updated_people)
                        
                        # Save updated document
                        with open(doc_file, 'w') as f:
                            json.dump(doc_data, f, indent=2)
            
            # Remove person from metadata
            del self.metadata["people"][normalized_name]
            
            self._save_metadata()
            return True
            
        except Exception as e:
            print(f"Error removing person {person_name}: {e}")
            return False
    
    def search_documents(self, query: str) -> List[Dict]:
        """Search documents by title or content."""
        results = []
        query_lower = query.lower()
        
        for doc_id, metadata in self.metadata["documents"].items():
            if (query_lower in metadata["title"].lower() or 
                query_lower in metadata["summary"].lower()):
                results.append((doc_id, metadata))
        
        return results
    
    def export_to_notion_format(self) -> Dict:
        """Export data in format ready for Notion import."""
        return {
            "documents": self.metadata["documents"],
            "people": self.metadata["people"],
            "export_date": datetime.now().isoformat(),
            "total_documents": len(self.metadata["documents"]),
            "total_people": len(self.metadata["people"])
        }
    
    def generate_report(self) -> str:
        """Generate a text report of all stored data."""
        report = []
        report.append("OCR Translation Pipeline - Local Storage Report")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Documents: {len(self.metadata['documents'])}")
        report.append(f"Total People: {len(self.metadata['people'])}")
        report.append("")
        
        # Documents section
        report.append("DOCUMENTS:")
        report.append("-" * 20)
        for doc_id, metadata in self.metadata["documents"].items():
            report.append(f"• {metadata['title']}")
            report.append(f"  Date: {metadata['date_processed']}")
            report.append(f"  Language: {metadata['source_language']} → {metadata['target_language']}")
            report.append(f"  People: {metadata['people_count']}")
            report.append(f"  Summary: {metadata['summary']}")
            report.append("")
        
        # People section
        report.append("PEOPLE:")
        report.append("-" * 20)
        for person_name, person_data in self.metadata["people"].items():
            report.append(f"• {person_name}")
            report.append(f"  Aliases: {', '.join(person_data['aliases'])}")
            report.append(f"  First mentioned: {person_data['first_mentioned']}")
            report.append(f"  Documents: {len(person_data['documents'])}")
            report.append("")
        
        return "\n".join(report)

    # -----------------------------
    # References (with stable IDs)
    # -----------------------------
    def add_reference(self, ref_type: str, name: str, aliases: List[str] = None, notes: str = None) -> Optional[Dict]:
        """Add a new reference with stable ID."""
        try:
            ref_id = str(uuid.uuid4())
            created_at = datetime.now().isoformat()
            
            if aliases is None:
                aliases = []
            if name not in aliases:
                aliases.insert(0, name)
            
            ref_data = {
                "id": ref_id,
                "type": ref_type,
                "name": name,
                "aliases": aliases,
                "notes": notes or "",
                "mergedIntoId": None,
                "createdAt": created_at,
                "updatedAt": created_at
            }
            
            self.metadata.setdefault("references", {})[ref_id] = ref_data
            self._save_metadata()
            return ref_data
        except Exception as e:
            print(f"Error adding reference {name}: {e}")
            return None

    def get_reference(self, ref_id: str) -> Optional[Dict]:
        """Get a reference by ID."""
        return self.metadata.get("references", {}).get(ref_id)

    def list_references(self, ref_type: str = None, query: str = None) -> List[Dict]:
        """List references with optional filtering."""
        refs = list(self.metadata.get("references", {}).values())
        
        if ref_type:
            refs = [r for r in refs if r.get("type") == ref_type]
        
        if query:
            query_lower = query.lower()
            filtered = []
            for ref in refs:
                if (query_lower in ref.get("name", "").lower() or
                    any(query_lower in alias.lower() for alias in ref.get("aliases", []))):
                    filtered.append(ref)
            refs = filtered
        
        return refs

    def update_reference(self, ref_id: str, name: str = None, aliases: List[str] = None, notes: str = None) -> Optional[Dict]:
        """Update a reference."""
        try:
            if ref_id not in self.metadata.get("references", {}):
                return None
            
            ref_data = self.metadata["references"][ref_id]
            updated_at = datetime.now().isoformat()
            
            if name is not None:
                ref_data["name"] = name
            if aliases is not None:
                ref_data["aliases"] = aliases
            if notes is not None:
                ref_data["notes"] = notes
            
            ref_data["updatedAt"] = updated_at
            self._save_metadata()
            return ref_data
        except Exception as e:
            print(f"Error updating reference {ref_id}: {e}")
            return None

    def delete_reference(self, ref_id: str) -> bool:
        """Delete a reference (soft delete by setting mergedIntoId)."""
        try:
            if ref_id not in self.metadata.get("references", {}):
                return False
            
            # Soft delete: mark as merged into a special "deleted" reference
            deleted_ref_id = "deleted"
            if deleted_ref_id not in self.metadata.get("references", {}):
                self.metadata.setdefault("references", {})[deleted_ref_id] = {
                    "id": deleted_ref_id,
                    "type": "other",
                    "name": "Deleted Reference",
                    "aliases": [],
                    "notes": "Placeholder for deleted references",
                    "mergedIntoId": None,
                    "createdAt": datetime.now().isoformat(),
                    "updatedAt": datetime.now().isoformat()
                }
            
            ref_data = self.metadata["references"][ref_id]
            ref_data["mergedIntoId"] = deleted_ref_id
            ref_data["updatedAt"] = datetime.now().isoformat()
            
            self._save_metadata()
            return True
        except Exception as e:
            print(f"Error deleting reference {ref_id}: {e}")
            return False

    def merge_references(self, source_id: str, target_id: str) -> bool:
        """Soft merge: move source into target, keep source as redirect."""
        try:
            if source_id not in self.metadata.get("references", {}) or target_id not in self.metadata.get("references", {}):
                return False
            
            source_ref = self.metadata["references"][source_id]
            target_ref = self.metadata["references"][target_id]
            
            # Merge aliases
            combined_aliases = list(set(target_ref.get("aliases", []) + source_ref.get("aliases", [])))
            target_ref["aliases"] = combined_aliases
            
            # Merge notes
            if source_ref.get("notes") and not target_ref.get("notes"):
                target_ref["notes"] = source_ref["notes"]
            
            # Mark source as merged into target
            source_ref["mergedIntoId"] = target_id
            source_ref["updatedAt"] = datetime.now().isoformat()
            target_ref["updatedAt"] = datetime.now().isoformat()
            
            # Move all document relations from source to target
            doc_refs = self.metadata.get("document_references", {})
            for rel_id, rel_data in list(doc_refs.items()):
                if rel_data.get("referenceId") == source_id:
                    rel_data["referenceId"] = target_id
                    rel_data["updatedAt"] = datetime.now().isoformat()
            
            self._save_metadata()
            return True
        except Exception as e:
            print(f"Error merging references {source_id} -> {target_id}: {e}")
            return False
    
    def get_reference_with_parent(self, ref_id: str) -> Optional[Dict]:
        """Get a reference and resolve to its canonical parent if it's been merged."""
        try:
            ref = self.get_reference(ref_id)
            if not ref:
                return None
            
            # Follow merge chain to find canonical parent
            visited = set()
            current_ref = ref
            while current_ref.get("mergedIntoId"):
                merged_into_id = current_ref["mergedIntoId"]
                
                # Prevent infinite loops
                if merged_into_id in visited:
                    break
                visited.add(merged_into_id)
                
                # Get parent reference
                parent_ref = self.get_reference(merged_into_id)
                if not parent_ref:
                    break
                
                current_ref = parent_ref
            
            # Return the canonical parent
            return current_ref
        except Exception as e:
            print(f"Error resolving reference {ref_id} to parent: {e}")
            return None
    
    def search_references_with_hierarchy(self, query: str, ref_type: str = None) -> List[Dict]:
        """Search references including both parents and children, showing hierarchy."""
        try:
            query_lower = query.lower()
            results = []
            
            # Always search in people for person references
            people = self.metadata.get("people", {})
            
            # Convert people format to references format for searching
            for person_name in people:
                person_data = people[person_name]
                aliases = person_data.get("aliases", [])
                
                # Check if query matches the canonical name
                name_match = query_lower in person_name.lower()
                
                # Add parent entry if name matches
                if name_match:
                    results.append({
                        'name': person_name,
                        'is_parent': len(aliases) > 0,
                        'parent_name': None,
                        'children_count': len(aliases),
                        'canonical_name': person_name
                    })
                
                # Check if query matches any alias (child)
                for alias in aliases:
                    if query_lower in alias.lower():
                        # Add child entry showing it maps to parent
                        results.append({
                            'name': alias,
                            'is_parent': False,
                            'parent_name': person_name,  # Points to canonical name
                            'children_count': 0,
                            'canonical_name': person_name
                        })
            
            return results
        except Exception as e:
            print(f"Error searching references with hierarchy: {e}")
            return []

    def add_reference_to_document(self, doc_id: str, ref_id: str, role: str = None) -> bool:
        """Add a reference to a document with optional role."""
        try:
            if doc_id not in self.metadata.get("documents", {}) or ref_id not in self.metadata.get("references", {}):
                return False
            
            rel_id = str(uuid.uuid4())
            created_at = datetime.now().isoformat()
            
            rel_data = {
                "id": rel_id,
                "documentId": doc_id,
                "referenceId": ref_id,
                "role": role,
                "createdAt": created_at
            }
            
            self.metadata.setdefault("document_references", {})[rel_id] = rel_data
            self._save_metadata()
            return True
        except Exception as e:
            print(f"Error adding reference {ref_id} to document {doc_id}: {e}")
            return False

    def remove_reference_from_document(self, doc_id: str, ref_id: str) -> bool:
        """Remove a reference from a document."""
        try:
            doc_refs = self.metadata.get("document_references", {})
            to_remove = []
            
            for rel_id, rel_data in doc_refs.items():
                if rel_data.get("documentId") == doc_id and rel_data.get("referenceId") == ref_id:
                    to_remove.append(rel_id)
            
            for rel_id in to_remove:
                del doc_refs[rel_id]
            
            self._save_metadata()
            return len(to_remove) > 0
        except Exception as e:
            print(f"Error removing reference {ref_id} from document {doc_id}: {e}")
            return False

    def list_document_references(self, doc_id: str) -> List[Dict]:
        """List all references for a document."""
        try:
            doc_refs = self.metadata.get("document_references", {})
            ref_ids = [rel_data.get("referenceId") for rel_data in doc_refs.values() 
                      if rel_data.get("documentId") == doc_id]
            
            references = []
            for ref_id in ref_ids:
                ref = self.get_reference(ref_id)
                if ref:
                    # Find the relation to get the role
                    rel_data = next((rel for rel in doc_refs.values() 
                                   if rel.get("documentId") == doc_id and rel.get("referenceId") == ref_id), None)
                    if rel_data:
                        ref_copy = ref.copy()
                        ref_copy["role"] = rel_data.get("role")
                        references.append(ref_copy)
            
            return references
        except Exception as e:
            print(f"Error listing references for document {doc_id}: {e}")
            return []


def main():
    """Test the local storage system."""
    print("🧪 Testing Local OCR Storage System")
    print("=" * 40)
    
    # Initialize storage
    storage = LocalOCRStorage()
    
    # Test data
    test_document = {
        "title": "Test Letter - 1938",
        "date_processed": datetime.now().isoformat(),
        "source_language": "de",
        "target_language": "en",
        "original_text": "Lieber John, ich hoffe es geht dir gut...",
        "translated_text": "Dear John, I hope you are well...",
        "file_size": 1024,
        "summary": "A personal letter from 1938 discussing family matters",
        "people": [
            {
                "original_name": "John Smith",
                "normalized_name": "john smith",
                "context": "Recipient of the letter"
            },
            {
                "original_name": "Maria Schmidt",
                "normalized_name": "maria schmidt", 
                "context": "Mentioned in the letter"
            }
        ]
    }
    
    # Add document
    doc_id = storage.add_document(test_document)
    print(f"✅ Added document: {doc_id}")
    
    # List documents
    documents = storage.list_documents()
    print(f"✅ Total documents: {len(documents)}")
    
    # Get people
    people = storage.get_people()
    print(f"✅ Total people: {len(people)}")
    
    # Generate report
    report = storage.generate_report()
    print("\n📊 Report:")
    print(report)
    
    print(f"\n💾 Data stored in: {storage.storage_dir}")


if __name__ == "__main__":
    main()
