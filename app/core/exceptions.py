class DocumentError(Exception):
    """Base class for expected document workflow errors."""


class DocumentValidationError(DocumentError):
    """Raised when an uploaded file is unsafe or unsupported."""


class DuplicateDocumentError(DocumentError):
    def __init__(self, document_id: str) -> None:
        super().__init__("This PDF has already been uploaded.")
        self.document_id = document_id


class DocumentNotFoundError(DocumentError):
    """Raised when a requested document does not exist."""


class ProviderError(Exception):
    """Raised when an LLM provider is unavailable or returns unusable output."""


class ProviderConfigurationError(ProviderError):
    """Raised when a selected provider has incomplete configuration."""


class ConversationNotFoundError(Exception):
    """Raised when a conversation ID does not exist."""
