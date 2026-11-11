"""Folder browsing, media listing and thumbnails."""

import getpass
import hashlib
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from PIL import Image, ImageDraw, ImageOps

from . import gps


class InvalidPathError(Exception):
    """Raised for a folder or file path that doesn't exist or isn't allowed."""


@dataclass
class FolderEntry:
    str_name: str
    str_path: str


@dataclass
class MediaItem:
    str_name: str
    str_kind: str  # "image" or "video"
    bool_writable: bool
    dict_location: dict | None

    def to_json(self) -> dict:
        """Plain-keyed dict for the JSON API the workspace page reads."""
        return {
            "name": self.str_name,
            "kind": self.str_kind,
            "writable": self.bool_writable,
            "location": self.dict_location,
        }


# --------------------------------------------------------------------------
# Folders
# --------------------------------------------------------------------------


def resolve_folder(str_folder: str) -> Path:
    """Return the folder as an absolute, existing directory path."""
    if not str_folder:
        raise InvalidPathError("No folder given.")
    obj_path = Path(str_folder).expanduser()
    if not obj_path.is_absolute():
        raise InvalidPathError("The folder must be an absolute path.")
    obj_path = obj_path.resolve()
    if not obj_path.is_dir():
        raise InvalidPathError(f"Not a folder: {obj_path}")
    return obj_path


def resolve_media_file(str_folder: str, str_name: str) -> Path:
    """Return a picture/video that sits directly inside the given folder."""
    obj_folder = resolve_folder(str_folder)
    if not str_name or "/" in str_name or "\\" in str_name or str_name in {".", ".."}:
        raise InvalidPathError("Invalid file name.")
    obj_path = obj_folder / str_name
    if not obj_path.is_file() or obj_path.resolve().parent != obj_folder:
        raise InvalidPathError(f"File not found: {str_name}")
    if not (gps.is_image(obj_path) or gps.is_video(obj_path)):
        raise InvalidPathError(f"Not a picture or video: {str_name}")
    return obj_path


def list_subfolders(obj_folder: Path) -> list[FolderEntry]:
    lst_entries = []
    try:
        for obj_child in obj_folder.iterdir():
            if obj_child.name.startswith("."):
                continue
            try:
                if obj_child.is_dir():
                    lst_entries.append(FolderEntry(obj_child.name, str(obj_child)))
            except OSError:
                continue
    except OSError:
        return []
    return sorted(lst_entries, key=lambda obj_entry: obj_entry.str_name.lower())


def count_media(obj_folder: Path) -> int:
    try:
        return sum(
            1 for obj_child in obj_folder.iterdir()
            if obj_child.is_file() and (gps.is_image(obj_child) or gps.is_video(obj_child))
        )
    except OSError:
        return 0


def quick_places() -> list[FolderEntry]:
    """Home, Pictures/Videos and mounted drives, for one-click navigation."""
    obj_home = Path.home()
    lst_candidates = [
        ("Home", obj_home),
        ("Pictures", obj_home / "Pictures"),
        ("Videos", obj_home / "Videos"),
    ]
    for obj_mount_root in (Path("/media") / getpass.getuser(), Path("/media"), Path("/mnt")):
        try:
            for obj_child in sorted(obj_mount_root.iterdir()):
                if obj_child.is_dir() and obj_child.name != getpass.getuser():
                    lst_candidates.append((obj_child.name, obj_child))
        except OSError:
            continue

    lst_places, obj_seen = [], set()
    for str_label, obj_path in lst_candidates:
        if obj_path.is_dir() and str(obj_path) not in obj_seen:
            obj_seen.add(str(obj_path))
            lst_places.append(FolderEntry(str_label, str(obj_path)))
    return lst_places


# --------------------------------------------------------------------------
# Media listing
# --------------------------------------------------------------------------


def list_media(obj_folder: Path) -> list[dict]:
    """All pictures/videos directly inside the folder, with their locations."""
    lst_paths = sorted(
        (
            obj_child for obj_child in obj_folder.iterdir()
            if not obj_child.name.startswith(".")
            and obj_child.is_file()
            and (gps.is_image(obj_child) or gps.is_video(obj_child))
        ),
        key=lambda obj_path: obj_path.name.lower(),
    )
    # Reading video locations spawns ffprobe, so do the reads in parallel.
    with ThreadPoolExecutor(max_workers=8) as obj_pool:
        lst_locations = list(obj_pool.map(gps.read_location, lst_paths))

    return [
        MediaItem(
            str_name=obj_path.name,
            str_kind="video" if gps.is_video(obj_path) else "image",
            bool_writable=gps.is_writable_format(obj_path),
            dict_location=dict_location,
        ).to_json()
        for obj_path, dict_location in zip(lst_paths, lst_locations)
    ]


# --------------------------------------------------------------------------
# Thumbnails
# --------------------------------------------------------------------------


def get_thumbnail(obj_path: Path) -> Path:
    """Return a cached JPEG thumbnail for the file, creating it if needed."""
    obj_stat = obj_path.stat()
    str_key = hashlib.sha1(
        f"{obj_path}|{obj_stat.st_mtime_ns}|{obj_stat.st_size}".encode()
    ).hexdigest()
    obj_cache_dir = Path(settings.OBJ_PATCHER_THUMBNAIL_CACHE_DIR)
    obj_cache_dir.mkdir(parents=True, exist_ok=True)
    obj_thumb = obj_cache_dir / f"{str_key}.jpg"
    if obj_thumb.exists():
        return obj_thumb

    int_size = settings.INT_PATCHER_THUMBNAIL_SIZE_PX
    if gps.is_video(obj_path):
        if not _extract_video_frame(obj_path, obj_thumb, int_size):
            _draw_placeholder(obj_thumb, int_size, "VIDEO")
    else:
        try:
            with Image.open(obj_path) as obj_image:
                obj_image = ImageOps.exif_transpose(obj_image)
                obj_image.thumbnail((int_size, int_size))
                obj_image.convert("RGB").save(obj_thumb, "JPEG", quality=82)
        except OSError:
            _draw_placeholder(obj_thumb, int_size, "IMAGE")
    return obj_thumb


def _extract_video_frame(obj_src: Path, obj_dst: Path, int_size: int) -> bool:
    for str_seek in ("1", "0"):
        try:
            obj_result = subprocess.run(
                [
                    "ffmpeg", "-v", "error", "-y", "-ss", str_seek, "-i", str(obj_src),
                    "-frames:v", "1",
                    "-vf", f"scale={int_size}:{int_size}:force_original_aspect_ratio=decrease",
                    str(obj_dst),
                ],
                capture_output=True, timeout=60, check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return False
        if obj_result.returncode == 0 and obj_dst.exists() and obj_dst.stat().st_size > 0:
            return True
    return False


def _draw_placeholder(obj_dst: Path, int_size: int, str_label: str) -> None:
    obj_image = Image.new("RGB", (int_size, int_size * 3 // 4), (60, 64, 72))
    obj_draw = ImageDraw.Draw(obj_image)
    obj_draw.text((int_size // 2, int_size * 3 // 8), str_label, fill=(220, 220, 220), anchor="mm")
    obj_image.save(obj_dst, "JPEG", quality=82)
