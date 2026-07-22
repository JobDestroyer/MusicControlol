#!/usr/bin/env python3
"""Unit tests for MPRIS metadata normalization (Strawberry-shaped payloads)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mpris_util import metadata_to_dict, unwrap_variant


class TestUnwrapVariant(unittest.TestCase):
    def test_simple_variant(self):
        self.assertEqual(unwrap_variant(("s", "hello")), "hello")

    def test_nested(self):
        self.assertEqual(unwrap_variant(("v", ("s", "x"))), "x")

    def test_array(self):
        self.assertEqual(unwrap_variant([("s", "a"), ("s", "b")]), ["a", "b"])


class TestStrawberryMetadata(unittest.TestCase):
    def test_multi_artist_and_file_art(self):
        # Shape similar to jeepney-decoded Strawberry Metadata
        raw = {
            "mpris:trackid": (
                "o",
                "/org/strawberrymusicplayer/strawberry/Track/abcdef01_2345",
            ),
            "mpris:length": ("x", 245000000),
            "mpris:artUrl": (
                "s",
                "file:///home/deck/.var/app/org.strawberrymusicplayer.strawberry/cache/cover.jpg",
            ),
            "xesam:title": ("s", "Song Title With | Pipe"),
            "xesam:album": ("s", "Album Name"),
            "xesam:artist": ("as", ["Artist One", "Artist Two"]),
            "xesam:url": ("s", "file:///home/deck/Music/song.flac"),
        }
        out = metadata_to_dict(raw)
        self.assertEqual(
            out["trackid"],
            "/org/strawberrymusicplayer/strawberry/Track/abcdef01_2345",
        )
        self.assertEqual(out["length"], 245000000)
        self.assertTrue(out["artUrl"].startswith("file:///"))
        self.assertEqual(out["title"], "Song Title With | Pipe")
        self.assertEqual(out["artist"], "Artist One, Artist Two")
        self.assertEqual(out["album"], "Album Name")

    def test_spotify_like(self):
        raw = {
            "mpris:trackid": ("s", "spotify:track:abc123"),
            "mpris:length": ("t", 200000000),
            "mpris:artUrl": ("s", "https://i.scdn.co/image/xyz"),
            "xesam:title": ("s", "Blinding Lights"),
            "xesam:artist": ("as", ["The Weeknd"]),
        }
        out = metadata_to_dict(raw)
        self.assertEqual(out["trackid"], "spotify:track:abc123")
        self.assertEqual(out["artist"], "The Weeknd")
        self.assertEqual(out["title"], "Blinding Lights")
        self.assertTrue(out["artUrl"].startswith("https://"))

    def test_empty(self):
        self.assertEqual(metadata_to_dict({}), {})
        self.assertEqual(metadata_to_dict(None), {})


class TestBusDiscoveryHelpers(unittest.TestCase):
    def test_prefix_filter(self):
        names = [
            "org.freedesktop.DBus",
            "org.mpris.MediaPlayer2.strawberry",
            "org.mpris.MediaPlayer2.spotify",
            ":1.42",
        ]
        mpris = sorted(n for n in names if n.startswith("org.mpris.MediaPlayer2"))
        self.assertEqual(
            mpris,
            [
                "org.mpris.MediaPlayer2.spotify",
                "org.mpris.MediaPlayer2.strawberry",
            ],
        )


if __name__ == "__main__":
    unittest.main()
