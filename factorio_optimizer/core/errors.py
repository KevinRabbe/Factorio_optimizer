from __future__ import annotations


class DomainError(ValueError):
    """Base error for invalid optimizer domain inputs or impossible plans."""


class InputError(DomainError):
    """Raised when user/API input cannot be compiled into a valid request."""
