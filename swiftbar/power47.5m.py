#!/usr/bin/env python3
# <swiftbar.title>Світло, група 47.1</swiftbar.title>
# <swiftbar.hideRunInTerminal>true</swiftbar.hideRunInTerminal>
# <swiftbar.hideLastUpdated>false</swiftbar.hideLastUpdated>
"""SwiftBar plugin (refresh every 5 min). Symlink this file into the SwiftBar plugin folder."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from power.menubar import main  # noqa: E402

main()
