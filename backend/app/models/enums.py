from __future__ import annotations

import enum


class OrgRole(str, enum.Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    SECURITY_ANALYST = "SECURITY_ANALYST"
    DEVELOPER = "DEVELOPER"
    VIEWER = "VIEWER"


class Environment(str, enum.Enum):
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"


class VerificationStatus(str, enum.Enum):
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    PRIVATE_ENVIRONMENT = "PRIVATE_ENVIRONMENT"


class VerificationMethod(str, enum.Enum):
    WELL_KNOWN_FILE = "WELL_KNOWN_FILE"
    DNS_TXT = "DNS_TXT"


class ScanType(str, enum.Enum):
    QUICK_SCAN = "QUICK_SCAN"
    FULL_SCAN = "FULL_SCAN"
    API_SCAN = "API_SCAN"
    INFRA_SCAN = "INFRA_SCAN"
    CHECKOUT_SCAN = "CHECKOUT_SCAN"
    PENTEST_SCAN = "PENTEST_SCAN"
    CODE_SCAN = "CODE_SCAN"
    SUPABASE_SCAN = "SUPABASE_SCAN"


class ScanStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Severity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Confidence(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FindingStatus(str, enum.Enum):
    OPEN = "open"
    CONFIRMED = "confirmed"
    POSSIBLE = "possible"
    FALSE_POSITIVE = "false_positive"
    FIXED = "fixed"
    ACCEPTED_RISK = "accepted_risk"
    IGNORED = "ignored"
