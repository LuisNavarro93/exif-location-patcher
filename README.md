# EXIF Location Patcher

A small local Django tool to see where your pictures and videos were taken
and fix or add their GPS location.

1. **Pick a folder** on the landing page.
2. The **workspace** shows the folder's thumbnails on the left and a map on
   the right. Click a thumbnail and the pin jumps to where it was taken.
3. Drag the pin (or click the map) to choose a new spot, then press
   **Set new location** to write it into the file. When the pin hasn't been
   moved, the button reads **Refresh location** and re-reads it from the file.

Ctrl/Shift-click thumbnails to set one location on several files at once.

Press **📍 Show all** in the map's corner (or click the "N with location"
count) to see a pin for every located file; close pins group into numbered
clusters. Click a pin to see the picture, then **Edit location** to change it.

> **Files are modified in place.** The write is atomic and keeps the file's
> modification time, but make a backup of anything irreplaceable first.

## Quick start

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
   and ffmpeg:

   | System  | uv                                                              | ffmpeg                    |
   |---------|-----------------------------------------------------------------|---------------------------|
   | Linux   | `curl -LsSf https://astral.sh/uv/install.sh \| sh`              | `sudo apt install ffmpeg` |
   | macOS   | `curl -LsSf https://astral.sh/uv/install.sh \| sh`              | `brew install ffmpeg`     |
   | Windows | `powershell -c "irm https://astral.sh/uv/install.ps1 \| iex"`   | `winget install ffmpeg`   |

2. Clone and run:

   ```bash
   git clone https://github.com/LuisNavarro93/exif-location-patcher.git
   cd exif-location-patcher
   uv run launcher.py          # or: uv run launcher.py 8080
   ```

   The first run downloads Python 3.12 (if needed) and the exact package
   versions in `uv.lock`. The app then opens at <http://127.0.0.1:8000/>.
   Press Ctrl+C to stop it.

**Without cloning**, run it straight from GitHub:

```bash
uvx --from git+https://github.com/LuisNavarro93/exif-location-patcher exif-location-patcher
```

**Without uv**, use plain pip (Python 3.10+):

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt     # Windows: .venv\Scripts\pip
.venv/bin/python launcher.py
```

The map tiles come from OpenStreetMap, so the map needs an internet
connection. Without ffmpeg the app still works, but videos show a
placeholder thumbnail and can't be patched.

### Changing dependencies

```bash
uv add <package>      # updates pyproject.toml and uv.lock
uv export --no-hashes --no-dev --no-emit-project --format requirements-txt -o requirements.txt
```

## Supported formats

| Format              | Read location | Write location |
|---------------------|:-------------:|:--------------:|
| JPEG, WebP          | yes           | yes            |
| PNG, TIFF           | yes           | no (read-only) |
| MP4, MOV, M4V       | yes           | yes (ffmpeg)   |
| 3GP                 | yes           | no (read-only) |

## Settings (environment variables)

| Variable                      | Default             |
|-------------------------------|---------------------|
| `PATCHER_START_DIR`           | your home folder    |
| `PATCHER_THUMBNAIL_CACHE_DIR` | `~/.cache/exif-location-patcher/thumbnails` |
| `PATCHER_THUMBNAIL_SIZE_PX`   | `320`               |

## Tests

```bash
uv run python manage.py test patcher
```
