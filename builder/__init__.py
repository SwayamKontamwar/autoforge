"""The autoforge self-building engine.

``run.py`` is the entry point invoked by the scheduled workflow. It selects the
next backlog item, asks a language model to implement it, and commits the change
only if lint and tests pass.
"""
