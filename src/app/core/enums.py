from enum import StrEnum


class UserRole(StrEnum):
    EMPLOYEE = "employee"
    APPROVER = "approver"


class ExpenseCategory(StrEnum):
    OFFICE = "OFFICE"
    TRAVEL = "TRAVEL"
    CLIENT_ENTERTAINMENT = "CLIENT_ENTERTAINMENT"
    SOFTWARE_SUBSCRIPTIONS = "SOFTWARE_SUBSCRIPTIONS"
    OTHER = "OTHER"


class ExpenseStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class ApprovalAction(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    WITHDRAW = "withdraw"


class AIAnalysisStatus(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
