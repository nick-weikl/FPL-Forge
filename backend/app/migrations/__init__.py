"""Ordered migration registry shared by the operator runner and readiness checks."""

from app.migrations import v001

MIGRATIONS = [("001_fpl_history", v001)]
