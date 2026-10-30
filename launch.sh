#!/bin/sh
# Wrapper: run the launcher with Xcode's python, which can import lldb.
# Runs from /tmp so nothing in the caller's cwd shadows Python modules.
HERE="$(cd "$(dirname "$0")" && pwd)" || exit 1
cd /tmp || exit 1
PYTHONPATH="$(lldb -P)" exec xcrun python3 "$HERE/launch.py" "$@"
