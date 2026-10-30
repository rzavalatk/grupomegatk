"""URL policy for the public MEGATK domain; no database or header access."""

from urllib.parse import urlsplit, urlunsplit


def https_target(url):
    """Return a fixed-host HTTPS URL, or None when no redirect is needed.

    Odoo's trusted proxy handling determines the request scheme. Never read
    X-Forwarded-Proto directly here. Keep ACME HTTP validation available.
    """
    parsed = urlsplit(url)
    if parsed.scheme != 'http' or parsed.hostname not in (
        'www.megatk.net', 'megatk.net',
    ):
        return None
    if parsed.path.startswith('/.well-known/acme-challenge/'):
        return None
    return urlunsplit((
        'https', 'www.megatk.net', parsed.path or '/', parsed.query, '',
    ))
