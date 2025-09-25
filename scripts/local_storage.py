#!/usr/bin/env python3

"""
Local storage system for OCR results.
Stores documents locally with metadata, can export to Notion later when upgraded.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class LocalOCRStorage:
    """Local storage system for OCR documents and people."""
    
    def __init__(self, storage_dir: str = "ocr_storage"):
        self.storage_dir = Path(storage_dir)
        self.documents_dir = self.storage_dir / "documents"
        self.people_dir = self.storage_dir / "people"
        self.metadata_file = self.storage_dir / "metadata.json"
        
        # Create directories
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self.people_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing metadata
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Load existing metadata."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            "documents": {},
            "people": {},
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_metadata(self):
        """Save metadata to file."""
        self.metadata["last_updated"] = datetime.now().isoformat()
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def add_document(self, document_data: Dict, doc_id: str = None) -> str:
        """Add a processed document to local storage."""
        if doc_id is None:
            doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Save document content
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
            "page_count": page_count
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
        """Get a document by ID."""
        doc_file = self.documents_dir / f"{doc_id}.json"
        if doc_file.exists():
            with open(doc_file, 'r') as f:
                document = json.load(f)
                # Add the document ID to the document object
                document['id'] = doc_id
                
                # Add metadata fields if available
                if doc_id in self.metadata["documents"]:
                    metadata = self.metadata["documents"][doc_id]
                    document['page_count'] = metadata.get('page_count', 0)
                    document['people_count'] = metadata.get('people_count', 0)
                
                return document
        else:
            # Document file doesn't exist, clean up orphaned metadata
            if doc_id in self.metadata["documents"]:
                print(f"Warning: Document {doc_id} has metadata but no file. Cleaning up...")
                del self.metadata["documents"][doc_id]
                self._save_metadata()
        return None
    
    def update_document(self, doc_id: str, updates: Dict, regenerate_summary: bool = False) -> bool:
        """Update a document with new data."""
        try:
            # Get existing document
            doc_file = self.documents_dir / f"{doc_id}.json"
            if not doc_file.exists():
                return False
            
            with open(doc_file, 'r') as f:
                document = json.load(f)
            
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
            
            # Save updated document
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
            
            people_list.append({
                "name": person_name,
                "aliases": person_data.get("aliases", []),
                "first_mentioned": person_data.get("first_mentioned", ""),
                "context": person_data.get("context", ""),
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
    
    def update_person(self, old_name: str, new_name: str, new_context: str = None) -> bool:
        """Update a person's name and context."""
        try:
            old_normalized = self.normalize_name(old_name)
            new_normalized = self.normalize_name(new_name)
            
            if old_normalized not in self.metadata["people"]:
                return False
            
            # Get the person data
            person_data = self.metadata["people"][old_normalized]
            
            # Update the name if it changed
            if old_normalized != new_normalized:
                # Remove from old location
                del self.metadata["people"][old_normalized]
                
                # Add to new location
                self.metadata["people"][new_normalized] = person_data
                
                # Update aliases
                if new_normalized not in person_data.get("aliases", []):
                    person_data.setdefault("aliases", []).append(new_normalized)
                
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
            
            # Update context if provided
            if new_context is not None:
                person_data["context"] = new_context
            
            # Update aliases to include the new name
            if new_normalized not in person_data.get("aliases", []):
                person_data.setdefault("aliases", []).append(new_normalized)
            
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
