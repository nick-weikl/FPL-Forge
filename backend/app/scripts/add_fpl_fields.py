"""Compatibility entry point. Schema changes are versioned centrally."""
from app.scripts.migrate import migrate


def add_fpl_fields():
    return migrate()


if __name__ == '__main__':
    print(add_fpl_fields())
