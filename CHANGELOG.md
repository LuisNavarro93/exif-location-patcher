# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.4] - 2026-11-11

### Fixed

- "No permission to modify this file" on photos you own that are marked
  read-only (common for pictures copied off phones, e.g. WhatsApp images).
  The location is written by swapping in an updated copy, which only needs
  the folder to be writable; such files now get patched and keep their
  read-only mode. Read-only files owned by another user are still refused.

## [0.1.3] - 2026-11-11

### Changed

- Every variable, field and constant the project defines now carries its
  type prefix (`str_`, `int_`, `flt_`, `bool_`, `dict_`, `lst_`, `obj_`,
  `tup_`), including the Django settings `OBJ_PATCHER_THUMBNAIL_CACHE_DIR`,
  `INT_PATCHER_THUMBNAIL_SIZE_PX` and `OBJ_PATCHER_START_DIR`. Environment
  variable names and JSON API keys are unchanged.

## [0.1.2] - 2026-11-10

### Fixed

- Thumbnails rendered as thin empty lines in large folders: the grid's
  rows collapsed to 0px when there were more rows than fit the pane.
- For a file with no location, the coordinates line showed the map
  centre (e.g. `20.000000, 0.000000`) as if it were real; it now reads
  "No location yet" until the pin is moved.

## [0.1.1] - 2026-11-10

### Fixed

- The thumbnail pane stayed empty with a `JSON.parse` error when a folder
  held photos whose GPS block was present but empty (0/0 values, written by
  some phones without a fix). Those now count as "no location".
- The map showed "403 Access blocked" tiles: OpenStreetMap rejects tile
  requests without a Referer header, and Django's default referrer policy
  stripped it. The app now sends `strict-origin-when-cross-origin`.
- The folder path in the header lost its leading `/` and showed the
  slash at the end.

## [0.1.0] - 2026-11-10

### Added

- Landing page with a folder browser (quick links to Home, Pictures, Videos
  and mounted drives, or type a path) to pick a folder of pictures/videos.
- Workspace page with two side-by-side panes: a thumbnail grid of the
  folder's pictures and videos, and a pan/zoom OpenStreetMap map with a
  draggable location pin.
- Selecting a thumbnail moves the pin to the location stored in the file
  (EXIF GPS for pictures, ISO 6709 location tag for videos).
- Button under the map: "Refresh location" re-reads the location from the
  selected file(s); after dragging the pin or clicking the map it becomes
  "Set new location" and writes the new spot into the file(s).
- Ctrl/Shift-click to select several files and set one location for all.
- Location writing for JPEG/WebP (piexif) and MP4/MOV/M4V (ffmpeg remux,
  no re-encoding); other formats are shown as read-only. Writes are atomic
  and keep the file's permissions and modification time.
