"""
CSO Knowledge — Olya methodology storage.

SPRINT: S27.0
STATUS: SCAFFOLD

This module manages:
- Knowledge files from intake/olya/
- Transformed methodology specs
- ICT concept mappings
"""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib


@dataclass
class KnowledgeEntry:
    """Single knowledge entry."""
    entry_id: str
    source_file: str
    content_hash: str
    loaded_at: datetime
    category: str  # e.g., 'htf_context', 'entry_triggers', 'position_sizing'


class KnowledgeStore:
    """
    Store for loaded knowledge.
    
    READ-ONLY in S27 — loads and indexes, does not modify.
    """
    
    def __init__(self, intake_path: Optional[Path] = None):
        self.intake_path = intake_path or Path(__file__).parent.parent.parent / 'intake' / 'olya'
        self._entries: Dict[str, KnowledgeEntry] = {}
    
    def scan_intake(self) -> List[str]:
        """
        Scan intake directory for new files.
        
        Returns:
            List of new file paths found
        """
        if not self.intake_path.exists():
            return []
        
        new_files = []
        for file in self.intake_path.glob('*.md'):
            if file.name != 'README.md':
                file_hash = hashlib.sha256(file.read_bytes()).hexdigest()[:16]
                if file_hash not in [e.content_hash for e in self._entries.values()]:
                    new_files.append(str(file))
        
        for file in self.intake_path.glob('*.yaml'):
            file_hash = hashlib.sha256(file.read_bytes()).hexdigest()[:16]
            if file_hash not in [e.content_hash for e in self._entries.values()]:
                new_files.append(str(file))
        
        return new_files
    
    def load_file(self, file_path: str) -> Optional[KnowledgeEntry]:
        """
        Load a knowledge file.
        
        Args:
            file_path: Path to knowledge file
        
        Returns:
            KnowledgeEntry if loaded, None on error
        """
        path = Path(file_path)
        if not path.exists():
            return None
        
        content = path.read_bytes()
        content_hash = hashlib.sha256(content).hexdigest()[:16]
        
        # Infer category from filename
        name = path.stem
        parts = name.split('_')
        category = parts[1] if len(parts) > 1 else 'general'
        
        entry = KnowledgeEntry(
            entry_id=f"KNO-{content_hash}",
            source_file=str(path),
            content_hash=content_hash,
            loaded_at=datetime.now(timezone.utc),
            category=category,
        )
        
        self._entries[entry.entry_id] = entry
        return entry
    
    def get_by_category(self, category: str) -> List[KnowledgeEntry]:
        """Get all entries in a category."""
        return [e for e in self._entries.values() if e.category == category]
    
    def get_all(self) -> List[KnowledgeEntry]:
        """Get all loaded entries."""
        return list(self._entries.values())


__all__ = ['KnowledgeEntry', 'KnowledgeStore']
