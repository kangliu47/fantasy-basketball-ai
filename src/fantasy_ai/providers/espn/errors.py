"""Provider errors with messages safe to display to a user."""


class ESPNError(Exception):
    """Base error for the ESPN provider."""


class ESPNAuthenticationError(ESPNError):
    """Authentication or league membership was rejected."""


class ESPNHTTPError(ESPNError):
    """An unexpected HTTP status or redirect was returned."""


class ESPNRateLimitError(ESPNHTTPError):
    """ESPN asked the caller to reduce request frequency."""


class ESPNUnavailableError(ESPNError):
    """A timeout or transport failure prevented the request."""


class ESPNResponseError(ESPNError):
    """The response could not be decoded as JSON."""


class ESPNSchemaError(ESPNResponseError):
    """The response does not match the minimal requested view envelope."""
