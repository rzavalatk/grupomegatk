"""Expose the regression suite to Odoo's test loader."""

if __package__:
    from . import test_redirect
    from . import test_routing
