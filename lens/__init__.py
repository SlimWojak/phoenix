"""
Phoenix Lens Module — Response Injection
========================================

File-based response injection mechanism for Claude.
Enables Claude to see CSO briefings, Shadow positions, etc.

Components:
- ResponseWriter: Write responses to file
- MCP tool: read_phoenix_response()

PATTERN:
1. Phoenix writes to responses/{type}.md
2. Claude reads via MCP tool
3. File has TTL, auto-expires

No daemon required. Simple file I/O.
"""

from .response_writer import Response, ResponseType, ResponseWriter

__all__ = ["ResponseWriter", "Response", "ResponseType"]
