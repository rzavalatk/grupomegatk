"""Server-side provenance. RPC context values cannot set or disable these flags."""
from contextlib import contextmanager
from contextvars import ContextVar
from uuid import uuid4

INTERNAL_APPEND = ContextVar('sentinel_internal_append', default=False)
ORIGIN = ContextVar('sentinel_origin', default=None)
TRANSACTION = ContextVar('sentinel_operation', default=None)


@contextmanager
def origin(kind, initiating_uid, evidence):
    token = ORIGIN.set({'kind': kind, 'initiating_uid': initiating_uid, 'evidence': evidence})
    try:
        yield
    finally:
        ORIGIN.reset(token)


@contextmanager
def operation():
    token = None
    if TRANSACTION.get() is None:
        token = TRANSACTION.set(str(uuid4()))
    try:
        yield TRANSACTION.get()
    finally:
        if token is not None:
            TRANSACTION.reset(token)


@contextmanager
def internal_append():
    token = INTERNAL_APPEND.set(True)
    try:
        yield
    finally:
        INTERNAL_APPEND.reset(token)
