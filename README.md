# StarCraft II Editor on Apple Silicon

A launcher that gets the macOS StarCraft II Editor past the "error while
initializing your videocard" dialog on M-series Macs.

## Why the editor fails

- The editor is x86_64-only, so it runs under Rosetta. Unlike the game, it
  only has an OpenGL renderer and ignores `GraphicsApi=Metal`.
- Blizzard's hardware detection looks the GPU up through IOKit by vendor. That
  lookup fails on Apple Silicon (`no GPU matched in SysInfo with vendorName:
  apple`), so it records the GPU as "Apple Software Renderer" with 0 MB of
  video memory.
- The editor's OpenGL setup then hits a hard check, "Apple Software Renderer
  isn't supported", which shows up as the videocard error dialog.
- The game has the same misdetection, but it renders with Metal, where it's
  only a warning.

## What the launcher does

It starts the editor under lldb, waits for OpenGL setup to begin, sets the
"software renderer" flag to 0 just before the check, then detaches. It doesn't
modify the app bundle.

The memory addresses are specific to editor build **96592** (5.0.15). lldb
turns off ASLR, which keeps them stable. The launcher refuses to patch if the
build number or the code at the check site doesn't match.

## Requirements

- An Apple Silicon Mac with Rosetta 2
- Xcode, or the Command Line Tools, for `lldb` and its Python module
- StarCraft II installed at `/Applications/StarCraft II`, or pass `--app`

## Usage

```sh
./launch.sh
./launch.sh --app "/path/to/StarCraft II Editor.app"
```

Quit any running editor first. When the launcher prints `patched; editor
running as pid N`, the editor is running on its own.

## Known caveats

- The editor then reports `Initialized OpenGL3 GraphicsDevice: Apple Software
  Renderer` and `Hardware Depth Sampling: Unavailable`. Rendering is real
  GPU-backed OpenGL (Apple's GL-on-Metal under Rosetta), but expect rough
  edges.
- After a Blizzard patch, the addresses have to be worked out again.

## Testing notes

When you report results, include:

- Your Mac model and macOS version
- Whether the editor opened, and what you tried (terrain, triggers, test map, etc.)
- The latest `~/Library/Application Support/Blizzard/StarCraft II/EditorLogs/*Graphics.txt`
- Any crash folders in that same `EditorLogs` directory
