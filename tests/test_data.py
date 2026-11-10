import csv
import hashlib
import io
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from zipfile import ZIP_DEFLATED, ZipFile

from typing37k.__main__ import load_replication_notebook


data = load_replication_notebook()


def example_participant(identifier, fingers, hours, wpm=36):
    row = dict.fromkeys(data.COLUMNS, "")
    row.update(
        PARTICIPANT_ID=identifier, AGE=29, WPM=wpm, ERROR_RATE=2, DEVICE="mobile",
        FINGERS=fingers, TIME_SPENT_TYPING=hours, BROWSER='clavier français "mobile"',
    )
    return [row[column] for column in data.COLUMNS]


def csv_bytes(rows, encoding="ascii"):
    stream = io.StringIO(newline="")
    csv.writer(stream, escapechar=chr(92), doublequote=False).writerows(rows)
    return stream.getvalue().encode(encoding)


class DataTests(unittest.TestCase):
    def test_local_zip_parse_and_sequential_cleaning(self):
        schema = csv_bytes([["Field"], *[[column] for column in data.COLUMNS]])
        participants = csv_bytes([
            example_participant(1, "2 hands thumbs", "bad answer"),
            example_participant(2, "other", 25),
            example_participant(3, "undefined;thumbs", 25),
            example_participant(4, "left_hand;thumbs", 25),
            example_participant(5, "other", 25, wpm=200),
        ], "latin-1")
        contents = {data.SCHEMA: schema, data.PARTICIPANTS: participants}
        hashes = {name: hashlib.sha256(content).hexdigest() for name, content in contents.items()}

        with TemporaryDirectory() as tmp, patch.dict(data.SHA256, hashes):
            archive = Path(tmp) / "fixture.zip"
            cache = Path(tmp) / "raw"
            with ZipFile(archive, "w", compression=ZIP_DEFLATED) as zipped:
                for name, content in contents.items():
                    zipped.writestr(f"Data_Processed/{name}", content)

            cleaned, audit = data.load_data(cache, archive=archive)
            self.assertEqual(cleaned.PARTICIPANT_ID.tolist(), [1])
            self.assertEqual(cleaned.BROWSER.iloc[0], 'clavier français "mobile"')
            self.assertEqual(cleaned.HAND_FINGER.iloc[0], "both_hands;thumbs")
            self.assertEqual(cleaned.TYPE_ENGLISH.iloc[0], "native")
            self.assertTrue(cleaned.TIME_SPENT_TYPING.isna().all())
            self.assertEqual(audit.removed.tolist(), [0, 1, 0, 1, 0, 0, 1, 1])
            offline, _ = data.load_data(cache, offline=True)
            self.assertTrue(offline.equals(cleaned))

            (cache / data.PARTICIPANTS).write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "No verified"):
                data.load_data(cache, offline=True)

    def test_wrong_width_is_rejected(self):
        schema = csv_bytes([["Field"], *[[column] for column in data.COLUMNS]])
        with self.assertRaisesRegex(ValueError, "Expected 28 columns"):
            data._read_participants({data.SCHEMA: schema, data.PARTICIPANTS: b"1,2\n"})
