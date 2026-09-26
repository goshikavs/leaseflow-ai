from enum import StrEnum


class ProcessingStatus(StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    FAILED = "failed"


class LeaseStatus(StrEnum):
    DRAFT = "draft"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"


class ExtractionStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REJECTED = "rejected"


class ConfidenceStatus(StrEnum):
    EVIDENCE_FOUND = "evidence_found"
    MISSING = "missing"
    UNSUPPORTED_EVIDENCE = "unsupported_evidence"


class IssueSeverity(StrEnum):
    BLOCKING = "blocking"
    WARNING = "warning"
    INFORMATION = "information"


class AuditEventType(StrEnum):
    DOCUMENT_UPLOADED = "document_uploaded"
    PROCESSING_STARTED = "processing_started"
    PROCESSING_COMPLETED = "processing_completed"
    PROCESSING_FAILED = "processing_failed"
    LEASE_CORRECTED = "lease_corrected"
    LEASE_APPROVED = "lease_approved"
    LEASE_EXPORTED = "lease_exported"
