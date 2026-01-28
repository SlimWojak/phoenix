"""
Phoenix Daemons — Background Services
======================================

S34: OPERATIONAL_FINISHING

Watcher: Detects new intents, routes to workers
Lens: Injects responses into Claude's view
"""

from .lens import ResponseLens
from .routing import IntentRouter, IntentType
from .watcher import IntentWatcher

__all__ = [
    "IntentWatcher",
    "ResponseLens",
    "IntentRouter",
    "IntentType",
]
