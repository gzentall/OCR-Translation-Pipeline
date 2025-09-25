#!/usr/bin/env python3

"""
Interactive query tool for local OCR storage.
Allows you to search, browse, and analyze your OCR data.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent / 'scripts'))

from local_storage import LocalOCRStorage


class OCRQueryTool:
    """Interactive tool for querying OCR data."""
    
    def __init__(self):
        self.storage = LocalOCRStorage()
    
    def show_menu(self):
        """Display the main menu."""
        print("\n🔍 OCR Data Query Tool")
        print("=" * 30)
        print("1. List all documents")
        print("2. Search documents")
        print("3. Browse people")
        print("4. Find documents by person")
        print("5. Generate full report")
        print("6. Export data")
        print("7. View document details")
        print("8. Statistics")
        print("0. Exit")
        print("-" * 30)
    
    def list_documents(self):
        """List all documents with basic info."""
        documents = self.storage.list_documents()
        if not documents:
            print("No documents found.")
            return
        
        print(f"\n📄 Found {len(documents)} documents:")
        print("-" * 50)
        for i, (doc_id, metadata) in enumerate(documents, 1):
            print(f"{i}. {metadata['title']}")
            print(f"   Date: {metadata['date_processed'][:10]}")
            print(f"   Language: {metadata['source_language']} → {metadata['target_language']}")
            print(f"   People: {metadata['people_count']}")
            print(f"   Summary: {metadata['summary']}")
            print()
    
    def search_documents(self):
        """Search documents by query."""
        query = input("Enter search query: ").strip()
        if not query:
            return
        
        results = self.storage.search_documents(query)
        if not results:
            print("No documents found matching your query.")
            return
        
        print(f"\n🔍 Found {len(results)} documents matching '{query}':")
        print("-" * 50)
        for doc_id, metadata in results:
            print(f"• {metadata['title']}")
            print(f"  Date: {metadata['date_processed'][:10]}")
            print(f"  Summary: {metadata['summary']}")
            print()
    
    def browse_people(self):
        """Browse all people mentioned in documents."""
        people = self.storage.get_people()
        if not people:
            print("No people found.")
            return
        
        print(f"\n👥 Found {len(people)} people:")
        print("-" * 50)
        for person_name, person_data in people.items():
            print(f"• {person_name}")
            print(f"  Aliases: {', '.join(person_data['aliases'])}")
            print(f"  First mentioned: {person_data['first_mentioned'][:10]}")
            print(f"  Documents: {len(person_data['documents'])}")
            print()
    
    def find_documents_by_person(self):
        """Find documents mentioning a specific person."""
        person_name = input("Enter person name: ").strip()
        if not person_name:
            return
        
        people = self.storage.get_people()
        person_name_lower = person_name.lower()
        
        # Find matching people
        matches = []
        for pname, pdata in people.items():
            if (person_name_lower in pname.lower() or 
                any(person_name_lower in alias.lower() for alias in pdata['aliases'])):
                matches.append((pname, pdata))
        
        if not matches:
            print(f"No people found matching '{person_name}'.")
            return
        
        print(f"\n👤 Found {len(matches)} people matching '{person_name}':")
        print("-" * 50)
        
        for person_name, person_data in matches:
            print(f"• {person_name}")
            print(f"  Aliases: {', '.join(person_data['aliases'])}")
            print(f"  Documents mentioning this person:")
            
            for doc_id in person_data['documents']:
                doc_metadata = self.storage.metadata['documents'].get(doc_id, {})
                print(f"    - {doc_metadata.get('title', 'Unknown')} ({doc_metadata.get('date_processed', '')[:10]})")
            print()
    
    def view_document_details(self):
        """View full details of a specific document."""
        documents = self.storage.list_documents()
        if not documents:
            print("No documents found.")
            return
        
        print("\nSelect a document to view:")
        for i, (doc_id, metadata) in enumerate(documents, 1):
            print(f"{i}. {metadata['title']}")
        
        try:
            choice = int(input("\nEnter document number: ")) - 1
            if 0 <= choice < len(documents):
                doc_id, _ = documents[choice]
                doc_data = self.storage.get_document(doc_id)
                
                if doc_data:
                    print(f"\n📄 {doc_data['title']}")
                    print("=" * 50)
                    print(f"Date Processed: {doc_data['date_processed']}")
                    print(f"Source Language: {doc_data['source_language']}")
                    print(f"Target Language: {doc_data['target_language']}")
                    print(f"File Size: {doc_data['file_size']} bytes")
                    print(f"\nSummary:")
                    print(doc_data['summary'])
                    print(f"\nOriginal Text:")
                    print(doc_data['original_text'][:500] + "..." if len(doc_data['original_text']) > 500 else doc_data['original_text'])
                    print(f"\nTranslated Text:")
                    print(doc_data['translated_text'][:500] + "..." if len(doc_data['translated_text']) > 500 else doc_data['translated_text'])
                    print(f"\nPeople Mentioned:")
                    for person in doc_data['people']:
                        print(f"  • {person['original_name']} - {person['context']}")
                else:
                    print("Document not found.")
            else:
                print("Invalid selection.")
        except ValueError:
            print("Invalid input.")
    
    def show_statistics(self):
        """Show statistics about the stored data."""
        documents = self.storage.list_documents()
        people = self.storage.get_people()
        
        print("\n📊 Statistics:")
        print("-" * 30)
        print(f"Total Documents: {len(documents)}")
        print(f"Total People: {len(people)}")
        
        if documents:
            # Language statistics
            languages = {}
            for _, metadata in documents:
                lang = metadata['source_language']
                languages[lang] = languages.get(lang, 0) + 1
            
            print(f"\nDocuments by Language:")
            for lang, count in sorted(languages.items()):
                print(f"  {lang}: {count}")
            
            # Date range
            dates = [metadata['date_processed'][:10] for _, metadata in documents]
            if dates:
                print(f"\nDate Range: {min(dates)} to {max(dates)}")
        
        if people:
            # Most mentioned people
            people_by_docs = [(name, len(data['documents'])) for name, data in people.items()]
            people_by_docs.sort(key=lambda x: x[1], reverse=True)
            
            print(f"\nMost Mentioned People:")
            for name, count in people_by_docs[:5]:
                print(f"  {name}: {count} documents")
    
    def export_data(self):
        """Export data to various formats."""
        print("\n📤 Export Options:")
        print("1. JSON format (for Notion import later)")
        print("2. Text report")
        print("3. CSV format")
        
        choice = input("Select export format (1-3): ").strip()
        
        if choice == "1":
            data = self.storage.export_to_notion_format()
            filename = f"ocr_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✅ Data exported to: {filename}")
            
        elif choice == "2":
            report = self.storage.generate_report()
            filename = f"ocr_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w') as f:
                f.write(report)
            print(f"✅ Report exported to: {filename}")
            
        elif choice == "3":
            # Simple CSV export
            import csv
            filename = f"ocr_documents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Title', 'Date', 'Source Language', 'Target Language', 'People Count', 'Summary'])
                for _, metadata in self.storage.list_documents():
                    writer.writerow([
                        metadata['title'],
                        metadata['date_processed'][:10],
                        metadata['source_language'],
                        metadata['target_language'],
                        metadata['people_count'],
                        metadata['summary']
                    ])
            print(f"✅ CSV exported to: {filename}")
        
        else:
            print("Invalid choice.")
    
    def run(self):
        """Run the interactive query tool."""
        while True:
            self.show_menu()
            choice = input("Enter your choice: ").strip()
            
            if choice == "0":
                print("Goodbye!")
                break
            elif choice == "1":
                self.list_documents()
            elif choice == "2":
                self.search_documents()
            elif choice == "3":
                self.browse_people()
            elif choice == "4":
                self.find_documents_by_person()
            elif choice == "5":
                report = self.storage.generate_report()
                print("\n" + report)
            elif choice == "6":
                self.export_data()
            elif choice == "7":
                self.view_document_details()
            elif choice == "8":
                self.show_statistics()
            else:
                print("Invalid choice. Please try again.")
            
            input("\nPress Enter to continue...")


def main():
    """Run the query tool."""
    tool = OCRQueryTool()
    tool.run()


if __name__ == "__main__":
    main()
