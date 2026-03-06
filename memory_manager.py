#!/usr/bin/env python3
"""
OpenClaw Memory Manager
Unified interface for ChromaDB (default) with fallback options
"""

import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Optional, Any

# Add extension paths
sys.path.insert(0, '/root/.openclaw/extensions/chroma-memory')
sys.path.insert(0, '/root/.openclaw/extensions/hybrid-memory')

from chroma_memory import ChromaMemory, OpenClawMemoryTool

class OpenClawMemoryManager:
    """
    Unified memory manager for OpenClaw
    
    Default: ChromaDB (local, no API keys)
    Optional: Hybrid (ChromaDB + Memgraph) for advanced features
    Legacy: Supabase (if configured)
    """
    
    def __init__(self):
        self.backend = None
        self.backend_type = None
        self._init_backend()
    
    def _init_backend(self):
        """Initialize the best available backend"""
        
        # Priority 1: ChromaDB (always works)
        try:
            self.backend = ChromaMemory(
                persist_dir=os.path.expanduser('~/.openclaw/memory/chromadb'),
                collection_name='openclaw_memory'
            )
            self.backend_type = 'chromadb'
            print(f"[Memory] Using ChromaDB backend")
            return
        except Exception as e:
            print(f"[Memory] ChromaDB failed: {e}")
        
        # Priority 2: Hybrid (if Memgraph available)
        try:
            from hybrid_memory import HybridMemory
            self.backend = HybridMemory(
                chroma_dir='~/.openclaw/memory/chromadb',
                memgraph_host='localhost'
            )
            self.backend_type = 'hybrid'
            print(f"[Memory] Using Hybrid backend (ChromaDB + Memgraph)")
            return
        except Exception as e:
            print(f"[Memory] Hybrid failed: {e}")
        
        # Fallback: No memory
        self.backend_type = 'none'
        print("[Memory] No backend available")
    
    # =================================================================
    # CORE API
    # =================================================================
    
    def remember(self, content: str, source: str = "session", 
                 metadata: Dict = None, **kwargs) -> str:
        """
        Store a memory
        
        Args:
            content: What to remember
            source: Where it came from (session, file, web, user)
            metadata: Additional data
            **kwargs: Backend-specific options
        
        Returns:
            memory_id: Unique identifier
        """
        if not self.backend:
            raise RuntimeError("No memory backend available")
        
        # Add timestamp to metadata
        meta = {
            'stored_at': datetime.now().isoformat(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            **(metadata or {})
        }
        
        memory_id = self.backend.add(
            content=content,
            source=source,
            metadata=meta,
            **kwargs
        )
        
        return memory_id
    
    def recall(self, query: str, n_results: int = 5, 
               filter_dict: Dict = None, **kwargs) -> List[Dict]:
        """
        Search memories
        
        Args:
            query: What to search for
            n_results: Number of results
            filter_dict: Filters (e.g., {'source': 'session'})
            **kwargs: Backend-specific options
        
        Returns:
            List of memory entries
        """
        if not self.backend:
            return []
        
        if self.backend_type == 'chromadb':
            entries = self.backend.search(query, n_results, filter_dict)
            return [
                {
                    'id': e.id,
                    'content': e.content,
                    'source': e.source,
                    'timestamp': e.timestamp,
                    'metadata': e.metadata
                }
                for e in entries
            ]
        
        elif self.backend_type == 'hybrid':
            return self.backend.search(query, n_results, **kwargs)
        
        return []
    
    def recall_by_date(self, date: str) -> List[Dict]:
        """Get all memories from a specific date (YYYY-MM-DD)"""
        if not self.backend:
            return []
        
        if self.backend_type == 'chromadb':
            entries = self.backend.get_by_date(date)
            return [
                {
                    'id': e.id,
                    'content': e.content,
                    'source': e.source,
                    'timestamp': e.timestamp
                }
                for e in entries
            ]
        
        return []
    
    def recall_by_source(self, source: str) -> List[Dict]:
        """Get all memories from a specific source"""
        if not self.backend:
            return []
        
        if self.backend_type == 'chromadb':
            entries = self.backend.get_by_source(source)
            return [
                {
                    'id': e.id,
                    'content': e.content,
                    'source': e.source,
                    'timestamp': e.timestamp
                }
                for e in entries
            ]
        
        return []
    
    def forget(self, memory_id: str) -> bool:
        """Delete a memory by ID"""
        if not self.backend:
            return False
        
        return self.backend.delete(memory_id)
    
    def get(self, memory_id: str) -> Optional[Dict]:
        """Get a specific memory by ID"""
        if not self.backend:
            return None
        
        entry = self.backend.get(memory_id)
        if entry:
            return {
                'id': entry.id,
                'content': entry.content,
                'source': entry.source,
                'timestamp': entry.timestamp,
                'metadata': entry.metadata
            }
        return None
    
    def stats(self) -> Dict:
        """Get memory statistics"""
        if not self.backend:
            return {'backend': 'none', 'status': 'unavailable'}
        
        backend_stats = self.backend.stats()
        
        return {
            'backend': self.backend_type,
            'status': 'active',
            **backend_stats
        }
    
    # =================================================================
    # TELEGRAM BOT INTEGRATION
    # =================================================================
    
    def remember_telegram_message(self, message: dict, context: str = None):
        """
        Store a Telegram message
        
        Args:
            message: Telegram message object
            context: Additional context
        """
        # Extract relevant info
        chat_id = message.get('chat', {}).get('id')
        user = message.get('from', {}).get('username') or message.get('from', {}).get('first_name')
        text = message.get('text', '')
        message_id = message.get('message_id')
        
        if not text:
            return None
        
        # Format content
        content = f"[{user}]: {text}"
        if context:
            content = f"{context}\n{content}"
        
        # Store with Telegram metadata
        return self.remember(
            content=content,
            source='telegram',
            metadata={
                'chat_id': chat_id,
                'message_id': message_id,
                'user': user,
                'platform': 'telegram'
            }
        )
    
    def recall_for_telegram_user(self, user: str, query: str = None, n: int = 5):
        """Recall memories related to a Telegram user"""
        if query:
            # Search with user filter
            return self.recall(
                query=f"{user} {query}",
                n_results=n,
                filter_dict={'source': 'telegram'}
            )
        else:
            # Get all from user
            all_memories = self.recall_by_source('telegram')
            return [m for m in all_memories if user in m.get('content', '')][:n]
    
    # =================================================================
    # MIGRATION
    # =================================================================
    
    def migrate_from_files(self, memory_dir: str = None):
        """
        Migrate from old file-based memory to ChromaDB
        
        Args:
            memory_dir: Directory containing memory files
        """
        if memory_dir is None:
            memory_dir = os.path.expanduser('~/.openclaw/workspace/memory')
        
        if not os.path.exists(memory_dir):
            print(f"[Memory] Directory not found: {memory_dir}")
            return 0
        
        migrated = 0
        
        # Migrate markdown files
        for filename in os.listdir(memory_dir):
            if filename.endswith('.md'):
                filepath = os.path.join(memory_dir, filename)
                
                with open(filepath, 'r') as f:
                    content = f.read()
                
                # Extract date from filename (YYYY-MM-DD.md)
                date = filename.replace('.md', '')
                
                # Store in ChromaDB
                self.remember(
                    content=content,
                    source='migrated_file',
                    metadata={
                        'original_file': filename,
                        'date': date,
                        'migrated_at': datetime.now().isoformat()
                    }
                )
                
                migrated += 1
                print(f"[Memory] Migrated: {filename}")
        
        print(f"[Memory] Migration complete: {migrated} files")
        return migrated


# =================================================================
# GLOBAL INSTANCE
# =================================================================

# Singleton instance
_memory_manager = None

def get_memory() -> OpenClawMemoryManager:
    """Get or create global memory manager"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = OpenClawMemoryManager()
    return _memory_manager


# =================================================================
# CLI
# =================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='OpenClaw Memory Manager')
    parser.add_argument('command', choices=['remember', 'recall', 'stats', 'migrate'])
    parser.add_argument('--content', '-c', help='Content to remember')
    parser.add_argument('--query', '-q', help='Query to recall')
    parser.add_argument('--source', '-s', default='cli', help='Memory source')
    parser.add_argument('--n', type=int, default=5, help='Number of results')
    
    args = parser.parse_args()
    
    memory = get_memory()
    
    if args.command == 'remember':
        if not args.content:
            print("Error: --content required")
            sys.exit(1)
        mid = memory.remember(args.content, args.source)
        print(f"Remembered: {mid}")
    
    elif args.command == 'recall':
        query = args.query or input("Query: ")
        results = memory.recall(query, args.n)
        for i, r in enumerate(results, 1):
            print(f"\n{i}. [{r['source']}] {r['content'][:100]}...")
    
    elif args.command == 'stats':
        print(json.dumps(memory.stats(), indent=2))
    
    elif args.command == 'migrate':
        count = memory.migrate_from_files()
        print(f"Migrated {count} files")
