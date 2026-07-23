#!/usr/bin/env python3
"""
tests/test_metadata.py
======================

Unit tests for MPRIS parsing helpers.

These do **not** require a live D-Bus session or Decky — they feed canned
dbus-send-shaped text (and typed-variant structures) into the pure parsers
and check the output dicts.

Run with::

    python3 tests/test_metadata.py -v
"""

import os
import sys
import unittest

# Allow `import mpris_parse` from the plugin root when run as a script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mpris_parse import parse_metadata, parse_player_get_all, parse_variant_string
from mpris_util import metadata_to_dict, unwrap_variant


class TestUnwrapVariant(unittest.TestCase):
    """Typed D-Bus variant unwrapping (for potential native D-Bus backends)."""

    def test_simple_variant(self):
        self.assertEqual(unwrap_variant(("s", "hello")), "hello")

    def test_nested(self):
        self.assertEqual(unwrap_variant(("v", ("s", "x"))), "x")

    def test_array(self):
        self.assertEqual(unwrap_variant([("s", "a"), ("s", "b")]), ["a", "b"])


class TestMetadataToDict(unittest.TestCase):
    """metadata_to_dict on jeepney-style nested tuples."""

    def test_multi_artist(self):
        raw = {
            "mpris:trackid": ("o", "/org/strawberry/Track/abc"),
            "mpris:length": ("x", 245000000),
            "mpris:artUrl": ("s", "file:///tmp/cover.jpg"),
            "xesam:title": ("s", "Song Title With | Pipe"),
            "xesam:artist": ("as", ["Artist One", "Artist Two"]),
        }
        out = metadata_to_dict(raw)
        self.assertEqual(out["trackid"], "/org/strawberry/Track/abc")
        self.assertEqual(out["artist"], "Artist One, Artist Two")
        self.assertEqual(out["title"], "Song Title With | Pipe")


# ---------------------------------------------------------------------------
# Canned dbus-send --print-reply text (simplified but representative)
# ---------------------------------------------------------------------------

STRAWBERRY_META = r"""
method return time=1 sender=:1.99 -> destination=:1.100
   variant       array [
         dict entry(
            string "mpris:trackid"
            variant                object path "/org/strawberrymusicplayer/strawberry/Track/abcdef01_2345"
         )
         dict entry(
            string "mpris:length"
            variant                int64 245000000
         )
         dict entry(
            string "mpris:artUrl"
            variant                string "file:///home/deck/cover.jpg"
         )
         dict entry(
            string "xesam:title"
            variant                string "Song Title With | Pipe"
         )
         dict entry(
            string "xesam:artist"
            variant                array [
                  string "Artist One"
                  string "Artist Two"
               ]
         )
      ]
"""

GET_ALL_SAMPLE = r"""
method return
   array [
      dict entry(
         string "PlaybackStatus"
         variant             string "Playing"
      )
      dict entry(
         string "Position"
         variant             int64 12345000
      )
      dict entry(
         string "Volume"
         variant             double 0.75
      )
      dict entry(
         string "CanSeek"
         variant             boolean true
      )
      dict entry(
         string "Metadata"
         variant             array [
               dict entry(
                  string "mpris:trackid"
                  variant                      object path "/org/mpris/MediaPlayer2/Track/1"
               )
               dict entry(
                  string "xesam:title"
                  variant                      string "Hello"
               )
               dict entry(
                  string "xesam:artist"
                  variant                      array [
                        string "Band"
                     ]
               )
               dict entry(
                  string "mpris:length"
                  variant                      int64 180000000
               )
            ]
      )
   ]
"""


class TestParseMetadataText(unittest.TestCase):
    """Text scrapers used on the live dbus-send path."""

    def test_strawberry_shaped(self):
        out = parse_metadata(STRAWBERRY_META)
        self.assertIn("Track/abcdef01", out.get("trackid", ""))
        self.assertEqual(out.get("title"), "Song Title With | Pipe")
        self.assertEqual(out.get("artist"), "Artist One, Artist Two")
        self.assertEqual(out.get("length"), 245000000)
        self.assertTrue(str(out.get("artUrl", "")).startswith("file://"))

    def test_get_all(self):
        out = parse_player_get_all(GET_ALL_SAMPLE)
        self.assertEqual(out["playbackStatus"], "Playing")
        self.assertEqual(out["position"], 12345000)
        self.assertEqual(out["volume"], 0.75)
        self.assertTrue(out["canSeek"])
        self.assertTrue(out["canControlVolume"])
        self.assertEqual(out["metadata"].get("title"), "Hello")
        self.assertEqual(out["metadata"].get("artist"), "Band")


class TestParseVariantString(unittest.TestCase):
    def test_quoted(self):
        s = 'variant       string "Strawberry"\n'
        self.assertEqual(parse_variant_string(s), "Strawberry")


if __name__ == "__main__":
    unittest.main()
