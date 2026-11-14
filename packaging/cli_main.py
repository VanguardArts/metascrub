"""PyInstaller entry point for the standalone metascrub CLI binary."""
import sys

from metascrub.cli import main

if __name__ == "__main__":
    sys.exit(main())
