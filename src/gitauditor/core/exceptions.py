"""
Custom exception hierarchy for GitAuditor.
"""

class GitAuditorError(Exception):
    """Base exception for all GitAuditor errors."""
    pass

class CatalogError(GitAuditorError):
    """Raised when there is an issue with the repository catalog or database operations."""
    pass

class AIProviderError(GitAuditorError):
    """Raised when there is an issue communicating with or parsing responses from the AI provider."""
    pass

class PolicyError(GitAuditorError):
    """Raised when there is an issue loading or enforcing repository policies."""
    pass

class ScanError(GitAuditorError):
    """Raised when there is an issue scanning or parsing local git repositories."""
    pass
