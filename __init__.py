"""Directory-plugin entry point for Hermes discovery.

Hermes loads user plugins from the directory containing ``plugin.yaml``.  The
implementation lives in ``ai_super_learning_companion`` so it is also usable as
a normal Python package; this thin entry point keeps both installation paths
identical.
"""
from ai_super_learning_companion import register

__all__ = ["register"]
