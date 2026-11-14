"""PyInstaller entry point for the standalone metascrub GUI binary."""
import sys

from metascrub.gui.app import main

if __name__ == "__main__":
    sys.exit(main())
