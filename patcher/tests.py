"""Tests for reading/writing locations and the JSON endpoints."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from PIL import Image

from . import gps


def _make_jpeg(obj_path: Path) -> None:
    Image.new("RGB", (64, 48), (200, 80, 40)).save(obj_path, "JPEG")


def _make_video(obj_path: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=64x48:rate=5",
         "-t", "1", "-pix_fmt", "yuv420p", str(obj_path)],
        check=True,
    )


class GpsTests(SimpleTestCase):
    def setUp(self):
        self.obj_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.obj_dir)

    def test_jpeg_without_location_reads_none(self):
        obj_path = self.obj_dir / "a.jpg"
        _make_jpeg(obj_path)
        self.assertIsNone(gps.read_location(obj_path))

    def test_jpeg_write_then_read_round_trips(self):
        obj_path = self.obj_dir / "a.jpg"
        _make_jpeg(obj_path)
        int_mtime_before = obj_path.stat().st_mtime_ns
        gps.write_location(obj_path, 19.432608, -99.133209)
        dict_location = gps.read_location(obj_path)
        self.assertAlmostEqual(dict_location["lat"], 19.432608, places=5)
        self.assertAlmostEqual(dict_location["lon"], -99.133209, places=5)
        self.assertEqual(obj_path.stat().st_mtime_ns, int_mtime_before)
        self.assertEqual(list(self.obj_dir.iterdir()), [obj_path])  # no temp file left

    def test_southern_western_hemisphere(self):
        obj_path = self.obj_dir / "a.jpg"
        _make_jpeg(obj_path)
        gps.write_location(obj_path, -33.8688, -151.2093)
        dict_location = gps.read_location(obj_path)
        self.assertAlmostEqual(dict_location["lat"], -33.8688, places=5)
        self.assertAlmostEqual(dict_location["lon"], -151.2093, places=5)

    def test_empty_gps_block_reads_none(self):
        """Phones without a fix may write 0/0 rationals, which read as NaN."""
        import piexif
        obj_path = self.obj_dir / "a.jpg"
        _make_jpeg(obj_path)
        tup_zero = ((0, 0), (0, 0), (0, 0))
        obj_exif_bytes = piexif.dump({"GPS": {
            piexif.GPSIFD.GPSLatitudeRef: b"\x00", piexif.GPSIFD.GPSLatitude: tup_zero,
            piexif.GPSIFD.GPSLongitudeRef: b"\x00", piexif.GPSIFD.GPSLongitude: tup_zero,
        }})
        piexif.insert(obj_exif_bytes, str(obj_path))
        self.assertIsNone(gps.read_location(obj_path))
        gps.write_location(obj_path, 1.5, 2.5)
        self.assertEqual(gps.read_location(obj_path), {"lat": 1.5, "lon": 2.5})

    def test_read_only_file_you_own_is_patched_and_stays_read_only(self):
        obj_path = self.obj_dir / "a.jpg"
        _make_jpeg(obj_path)
        obj_path.chmod(0o555)
        gps.write_location(obj_path, 19.101288, -99.764464)
        self.assertAlmostEqual(gps.read_location(obj_path)["lat"], 19.101288, places=5)
        self.assertEqual(obj_path.stat().st_mode & 0o777, 0o555)

    def test_png_is_read_only(self):
        obj_path = self.obj_dir / "a.png"
        Image.new("RGB", (8, 8)).save(obj_path)
        self.assertFalse(gps.is_writable_format(obj_path))
        with self.assertRaises(gps.LocationError):
            gps.write_location(obj_path, 1.0, 1.0)

    def test_out_of_range_coordinates_rejected(self):
        with self.assertRaises(gps.LocationError):
            gps.validate_coordinates(91.0, 0.0)

    def test_parse_iso6709(self):
        self.assertEqual(gps.parse_iso6709("+19.4326-099.1332+2240.000/"), {"lat": 19.4326, "lon": -99.1332})
        self.assertIsNone(gps.parse_iso6709("garbage"))

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "needs ffmpeg")
    def test_video_write_then_read_round_trips(self):
        obj_path = self.obj_dir / "clip.mp4"
        _make_video(obj_path)
        self.assertIsNone(gps.read_location(obj_path))
        gps.write_location(obj_path, 48.8584, 2.2945)
        self.assertEqual(gps.read_location(obj_path), {"lat": 48.8584, "lon": 2.2945})


class ApiTests(SimpleTestCase):
    def setUp(self):
        self.obj_dir = Path(tempfile.mkdtemp())
        self.obj_cache = Path(tempfile.mkdtemp())
        _make_jpeg(self.obj_dir / "photo.jpg")
        (self.obj_dir / "notes.txt").write_text("ignored")

    def tearDown(self):
        shutil.rmtree(self.obj_dir)
        shutil.rmtree(self.obj_cache)

    def test_landing_and_workspace_render(self):
        self.assertEqual(self.client.get(reverse("patcher:landing"), {"path": str(self.obj_dir)}).status_code, 200)
        self.assertEqual(self.client.get(reverse("patcher:workspace"), {"folder": str(self.obj_dir)}).status_code, 200)

    def test_media_list_only_includes_media(self):
        dict_data = self.client.get(reverse("patcher:media_list"), {"folder": str(self.obj_dir)}).json()
        self.assertEqual([dict_item["name"] for dict_item in dict_data["items"]], ["photo.jpg"])
        self.assertIsNone(dict_data["items"][0]["location"])
        self.assertTrue(dict_data["items"][0]["writable"])

    def test_thumbnail(self):
        with override_settings(OBJ_PATCHER_THUMBNAIL_CACHE_DIR=self.obj_cache):
            obj_response = self.client.get(
                reverse("patcher:thumbnail"), {"folder": str(self.obj_dir), "name": "photo.jpg"}
            )
        self.assertEqual(obj_response.status_code, 200)
        self.assertEqual(obj_response["Content-Type"], "image/jpeg")

    def test_set_location(self):
        obj_response = self.client.post(
            reverse("patcher:location"),
            data=json.dumps({"folder": str(self.obj_dir), "names": ["photo.jpg"], "lat": 10.5, "lon": -20.25}),
            content_type="application/json",
        )
        dict_result = obj_response.json()["results"][0]
        self.assertTrue(dict_result["ok"], dict_result)
        dict_read = self.client.get(
            reverse("patcher:location"), {"folder": str(self.obj_dir), "name": "photo.jpg"}
        ).json()
        self.assertAlmostEqual(dict_read["location"]["lat"], 10.5, places=5)

    def test_path_traversal_rejected(self):
        obj_response = self.client.get(
            reverse("patcher:location"), {"folder": str(self.obj_dir), "name": "../etc/passwd"}
        )
        self.assertEqual(obj_response.status_code, 400)
