"""Make ``python -m tools.testiny`` run the pull CLI."""

import sys

from tools.testiny.cli import main

if __name__ == "__main__":
    sys.exit(main())
