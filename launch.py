#!/usr/bin/env python3
"""Launch the macOS StarCraft II Editor on Apple Silicon.

The editor (x86_64, Rosetta) only has an OpenGL renderer. Blizzard's SysInfo
cannot match Apple Silicon GPUs by IOKit vendor, so it labels the GPU "Apple
Software Renderer" (0 MB VRAM), and the editor's GL init refuses that with
"Apple Software Renderer isn't supported", which surfaces as the "error while
initializing your videocard" dialog. The game avoids this because it uses
Metal, where the same mislabel is only a warning.

This script launches the editor under lldb (which also disables ASLR, keeping
the addresses below stable), clears the software-renderer flag just before
the check, and detaches. The addresses are specific to editor build 96592; the
script refuses to patch anything else.

Usage:  ./launch.sh [--app /path/to/StarCraft II Editor.app]
"""
import argparse
import plistlib
import sys

import lldb

EXPECTED_BUILD = "96592"
CHECK_PC = 0x103346882  # cmpl $0x0, -0x908(%rbp) just before the software-renderer check
CHECK_BYTES = bytes.fromhex("83bdf8f6ffff00")
SYSINFO = 0x103345D27 + 0x19780B9  # global SysInfo block (lea at 0x103345d20)
SOFTWARE_RENDERER_FLAG = SYSINFO + 0xFD8

parser = argparse.ArgumentParser()
parser.add_argument("--app", default="/Applications/StarCraft II/StarCraft II Editor.app")
args = parser.parse_args()

with open(f"{args.app}/Contents/Info.plist", "rb") as f:
    build = plistlib.load(f).get("CFBundleVersion")
if build != EXPECTED_BUILD:
    sys.exit(f"editor build {build} != {EXPECTED_BUILD}; addresses need re-deriving")

dbg = lldb.SBDebugger.Create()
dbg.SetAsync(False)
target = dbg.CreateTarget(f"{args.app}/Contents/MacOS/StarCraft II Editor")
# The code is unpacked at runtime, so wait until GL setup starts before
# planting the address breakpoint.
first = target.BreakpointCreateByName("CGLCreateContext")
process = target.LaunchSimple(None, None, "/tmp")
if not process or process.GetState() != lldb.eStateStopped:
    sys.exit("editor did not reach CGLCreateContext")
target.BreakpointDelete(first.GetID())

err = lldb.SBError()
code = process.ReadMemory(CHECK_PC, len(CHECK_BYTES), err)
if not err.Success() or code != CHECK_BYTES:
    process.Kill()
    sys.exit("unexpected code at check site; refusing to patch")

check = target.BreakpointCreateByAddress(CHECK_PC)
process.Continue()
if process.GetSelectedThread().GetFrameAtIndex(0).GetPC() != CHECK_PC:
    process.Kill()
    sys.exit("did not stop at check site")
target.BreakpointDelete(check.GetID())

process.WriteMemory(SOFTWARE_RENDERER_FLAG, b"\x00", err)
if not err.Success():
    process.Kill()
    sys.exit(f"patch failed: {err}")
print(f"patched; editor running as pid {process.GetProcessID()}")
process.Detach()
