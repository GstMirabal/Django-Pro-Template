#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main() -> None:
    """Run administrative tasks."""
    # .env is loaded by config/settings.py, not here. It used to be loaded in
    # this function with plain assignment, which overwrote variables already
    # present in the real environment — so `DEBUG=false manage.py check
    # --deploy` silently read DEBUG back from the file. settings.py uses
    # setdefault, giving the environment precedence, and covers every entrypoint
    # rather than this one.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
