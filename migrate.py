#!/usr/bin/env python3
"""
Memory Migration Tool
Migrate from file-based memory to ChromaDB
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path

class MemoryMigrator:
    """Migrate old memory files to ChromaDB"""
    
    def __init__(self, source_dir: str, target_manager):
        self.source_dir = Path(source_dir)
        self.memory = target_manager
        self.stats = {
            'files_processed': 0,
            'memories_created': 0,
            'errors': []
        }
    
    def migrate_all(self):
        """Migrate all memory files"""
        print("=" * 50)
        print("  Memory Migration Tool")
        print("=" * 50)
        print(f"\nSource: {self.source_dir}")
        print(f"Target: ChromaDB")
        print()
        
        # Find all memory files
        memory_files = list(self.source_dir.glob('**/*.md'))
        print(f"Found {len(memory_files)} files to migrate\n")
        
        for filepath in memory_files:
            self._migrate_file(filepath)
        
        # Print summary
        print("\n" + "=" * 50)
        print("  Migration Complete")
        print("=" * 50)
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Memories created: {self.stats['memories_created']}")
        
        if self.stats['errors']:
            print(f"\nErrors ({len(self.stats['errors'])}):")
            for error in self.stats['errors']:
                print(f"  - {error}")
        
        return self.stats
    
    def _migrate_file(self, filepath: Path):
        """Migrate a single memory file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse filename for date
            date_match = re.match(r'(\d{4}-\d{2}-\d{2})', filepath.name)
            date = date_match.group(1) if date_match else datetime.now().strftime('%Y-%m-%d')
            
            # Parse content sections
            sections = self._parse_sections(content)
            
            # Create memories for each section
            for section in sections:
                self.memory.remember(
                    content=section['content'],
                    source='migrated',
                    metadata={
                        'original_file': str(filepath.name),
                        'section_title': section.get('title', ''),
                        'date': date,
                        'migrated_at': datetime.now().isoformat()
                    }
                )
                self.stats['memories_created'] += 1
            
            self.stats['files_processed'] += 1
            print(f"✓ {filepath.name} ({len(sections)} sections)")
            
        except Exception as e:
            self.stats['errors'].append(f"{filepath.name}: {e}")
            print(f"✗ {filepath.name} (ERROR: {e})")
    
    def _parse_sections(self, content: str) -> list:
        """Parse markdown content into sections"""
        sections = []
        
        # Split by headers
        parts = re.split(r'\n(#{1,3}\s+.+?)\n', content)
        
        if len(parts) == 1:
            # No headers, treat as single section
            sections.append({
                'title': 'General',
                'content': content.strip()
            })
        else:
            # Parse sections
            current_title = 'Introduction'
            current_content = parts[0].strip() if parts[0] else ''
            
            for i in range(1, len(parts), 2):
                if i + 1 < len(parts):
                    # Save previous section
                    if current_content:
                        sections.append({
                            'title': current_title,
                            'content': current_content
                        })
                    
                    # Start new section
                    current_title = parts[i].strip('# ')
                    current_content = parts[i + 1].strip()
            
            # Don't forget last section
            if current_content:
                sections.append({
                    'title': current_title,
                    'content': current_content
                })
        
        return sections
    
    def verify_migration(self):
        """Verify migrated data"""
        print("\n" + "=" * 50)
        print("  Verification")
        print("=" * 50)
        
        stats = self.memory.stats()
        print(f"\nTotal memories in ChromaDB: {stats.get('total_documents', 0)}")
        
        # Sample search
        results = self.memory.recall("OpenClaw", n_results=3)
        print(f"\nSample search 'OpenClaw': {len(results)} results")
        for r in results:
            print(f"  - {r['content'][:60]}...")
        
        return stats


# =================================================================
# CLI
# =================================================================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, '/root/.openclaw/extensions/memory-manager')
    
    from memory_manager import get_memory
    
    # Source directory
    source = os.path.expanduser('~/.openclaw/workspace/memory')
    
    # Target
    memory = get_memory()
    
    # Create migrator
    migrator = MemoryMigrator(source, memory)
    
    # Run migration
    stats = migrator.migrate_all()
    
    # Verify
    migrator.verify_migration()
    
    print("\n✅ Migration complete!")
