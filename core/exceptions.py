# -*- coding: utf-8 -*-


class GeoQAException(Exception):
    """Base exception class for all GeoQA operations."""

    pass


class RuleException(GeoQAException):
    """Raised when a validation rule fails to compile, evaluate, or execute."""

    pass


class ReportException(GeoQAException):
    """Raised when generating or exporting HTML/CSV reports fails."""

    pass


class ConfigurationException(GeoQAException):
    """Raised when reading or saving configuration settings fails."""

    pass


class ValidationException(GeoQAException):
    """Raised when the core validation engine encounters internal issues."""

    pass
