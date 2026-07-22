class GoldProvenanceError(Exception):
    """Raised when something attempts to write a non-human-verified row to
    the gold table through the repository API."""
