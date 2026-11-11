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

> **Files are modified in place.** The write is atomic and keeps the file's
> modification time, but make a backup of anything irreplaceable first.

## Setup

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
python3 launcher.py          # or: python3 launcher.py 8080
```

`launcher.py` runs `manage.py runserver` with the project's `.venv` and
opens <http://127.0.0.1:8000/> in your browser once the server is up. The map tiles come from OpenStreetMap, so an
internet connection is needed for the map.

`ffmpeg`/`ffprobe` must be on the `PATH` for video thumbnails and video
locations.

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
| `PATCHER_THUMBNAIL_CACHE_DIR` | `.thumbnail_cache/` |
| `PATCHER_THUMBNAIL_SIZE_PX`   | `320`               |

## Tests

```bash
.venv/bin/python manage.py test patcher
```
