"""Acquire the pinned Aalto Typing37K release and reproduce its final filters."""

from __future__ import annotations

import csv
import hashlib
import io
from pathlib import Path
import re
import struct
import tempfile
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZipFile
import zlib

import pandas as pd

SOURCE_URL = "https://userinterfaces.aalto.fi/typing37k/data/csv_raw_and_processed.zip"
SOURCE_SIZE = 5_634_050_894
PARTICIPANTS = "open_participants.csv"
SCHEMA = "open_participants_header.csv"
MEMBERS = (PARTICIPANTS, SCHEMA)
SHA256 = {
    PARTICIPANTS: "26c1abdc46c1f98121b1189969e084a73f9d10228c69e0c8035a4290e82e74ba",
    SCHEMA: "79d7b717343ad61287c36c702998de22dd1f6385e9dc39a9d4da6366acbe87a4",
}
# These consecutive local ZIP records hold the two small participant files.
# Pinning their offsets to this release avoids downloading the 5.6 GB archive.
RANGE_START = 768_305_529
RANGE_END = 772_119_221
SCHEMA_OFFSET = 772_118_793
RECORDS = {
    PARTICIPANTS: (RANGE_START, SCHEMA_OFFSET),
    SCHEMA: (SCHEMA_OFFSET, RANGE_END + 1),
}
LOCAL_HEADER = struct.Struct("<4s5H3I2H")
DATA_DESCRIPTOR = struct.Struct("<4s3I")

COLUMNS = (
    "PARTICIPANT_ID", "BROWSER", "BROWSER_LANGUAGE", "DEVICE", "SCREEN_W",
    "SCREEN_H", "AGE", "GENDER", "HAS_TAKEN_TYPING_COURSE", "LAYOUT", "WPM",
    "ERROR_RATE", "NATIVE_LANGUAGE", "KEYBOARD_TYPE", "USING_APP",
    "USING_FEATURES", "FINGERS", "TIME_SPENT_TYPING", "TYPE_ENGLISH",
    "P_KPD", "P_IKI", "P_BSP", "P_ECPC", "P_UILEN", "P_KSPC", "ITE_SWYPE",
    "ITE_PREDICT", "ITE_AUTOCORR",
)
NUMERIC = (
    "PARTICIPANT_ID", "SCREEN_W", "SCREEN_H", "AGE", "HAS_TAKEN_TYPING_COURSE",
    "WPM", "ERROR_RATE", "P_KPD", "P_IKI", "P_BSP", "P_ECPC", "P_UILEN",
    "P_KSPC", "ITE_SWYPE", "ITE_PREDICT", "ITE_AUTOCORR",
)
LEGACY_POSTURE = {
    "1 hand thumb": "right_hand;thumbs",
    "1 hand pointer": "right_hand;index_fingers",
    "2 hands thumbs": "both_hands;thumbs",
}
# Ordered translations for free-text responses, from the authors' notebook.
FINGER_PATTERNS = (
    (10, r"17|all|10|ten"),
    (8, r"8|eight"),
    (6, r"6|six"),
    (5, r"5|five"),
    (4, r"4|four|2 on both|(thumbs|fingers).*(thumbs|fingers)"),
    (3, r"3|three"),
    (2, r"2|two|both|(thumb|index).*(index|thumb)|(thumb|middle).*(middle|thumb)"
        r"|(index|middle).*(middle|index)|(middle|ring).*(ring|middle)"
        r"|(pinky|middle).*(middle|pinky)|thumbs|thums|thombs|and|thumb,index"),
    (1, r"one|index|middle|thumb|^1$"),
)


def _verify(name: str, content: bytes) -> None:
    if hashlib.sha256(content).hexdigest() != SHA256[name]:
        raise ValueError(f"SHA-256 mismatch for {name}")


def _fetch_members() -> dict[str, bytes]:
    requested_range = f"{RANGE_START}-{RANGE_END}"
    expected_size = RANGE_END - RANGE_START + 1
    request = Request(SOURCE_URL, headers={
        "Range": f"bytes={requested_range}",
        "Accept-Encoding": "identity",
    })
    with urlopen(request, timeout=60) as response:
        expected_header = f"bytes {requested_range}/{SOURCE_SIZE}"
        if response.status != 206 or response.headers.get("Content-Range") != expected_header:
            raise ValueError("Aalto did not return the expected ZIP byte range")
        segment = response.read(expected_size + 1)
    if len(segment) != expected_size:
        raise ValueError("Aalto returned an incomplete ZIP byte range")

    files = {}
    for name, (record_start, record_end) in RECORDS.items():
        offset = record_start - RANGE_START
        (signature, _, flags, method, _, _, _, _, _,
         name_size, extra_size) = LOCAL_HEADER.unpack_from(segment, offset)
        name_start = offset + LOCAL_HEADER.size
        data_start = name_start + name_size + extra_size
        expected_name = f"Data_Processed/{name}".encode("ascii")
        if (
            signature != b"PK\x03\x04"
            or flags != 0x08
            or method != 8
            or segment[name_start:name_start + name_size] != expected_name
        ):
            raise ValueError(f"Unexpected ZIP header for {name}")
        # This release stores lengths and CRC in the trailing data descriptor.
        data_end = record_end - RANGE_START - DATA_DESCRIPTOR.size
        marker, crc, compressed_size, size = DATA_DESCRIPTOR.unpack_from(segment, data_end)
        if marker != b"PK\x07\x08" or data_end - data_start != compressed_size:
            raise ValueError(f"Unexpected ZIP data descriptor for {name}")
        content = zlib.decompress(segment[data_start:data_end], -zlib.MAX_WBITS)
        if len(content) != size or zlib.crc32(content) != crc:
            raise ValueError(f"ZIP member failed its CRC or length check for {name}")
        files[name] = content
    return files


def _read_archive(archive: Path) -> dict[str, bytes]:
    # ZipFile checks the uncompressed CRC when reading a complete member.
    with ZipFile(archive) as source:
        return {name: source.read(f"Data_Processed/{name}") for name in MEMBERS}


def _cache_member(raw_dir: Path, name: str, content: bytes) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=raw_dir, delete=False) as temporary:
        temporary_path = Path(temporary.name)
        try:
            temporary.write(content)
            temporary.close()
            temporary_path.replace(raw_dir / name)
        finally:
            temporary_path.unlink(missing_ok=True)


def _acquire(raw_dir: Path, offline: bool, archive: Path | None) -> dict[str, bytes]:
    if archive is None:
        try:
            cached = {name: (raw_dir / name).read_bytes() for name in MEMBERS}
            for name, content in cached.items():
                _verify(name, content)
        except (FileNotFoundError, ValueError) as exc:
            if offline:
                raise ValueError(
                    f"No verified Typing37K cache in {raw_dir}. "
                    "Run online once or pass the official archive with --archive."
                ) from exc
        else:
            return cached

    try:
        files = _read_archive(archive) if archive is not None else _fetch_members()
        for name, content in files.items():
            _verify(name, content)
    except (OSError, ValueError, KeyError, BadZipFile, zlib.error) as exc:
        if archive is not None:
            raise ValueError(f"Could not verify the official CSV archive {archive}: {exc}") from exc
        raise ValueError(
            f"Could not fetch the Typing37K participant files: {exc}. "
            "Download the official CSV ZIP separately and pass it with --archive."
        ) from exc

    for name, content in files.items():
        _cache_member(raw_dir, name, content)
    return files


def _read_participants(files: dict[str, bytes]) -> pd.DataFrame:
    schema = csv.DictReader(io.StringIO(files[SCHEMA].decode("ascii"), newline=""))
    columns = tuple(row["Field"] for row in schema)
    if columns != COLUMNS:
        raise ValueError("Unexpected Typing37K participant schema")

    # This MySQL export is headerless and uses backslash-escaped quotes. Its
    # free-text fields contain bytes that do not decode as UTF-8.
    stream = io.StringIO(files[PARTICIPANTS].decode("latin-1"), newline="")
    reader = csv.reader(stream, escapechar="\\", strict=True)
    rows = []
    for row in reader:
        if len(row) != len(columns):
            raise ValueError(f"Expected {len(columns)} columns at source line {reader.line_num}")
        rows.append(row)
    frame = pd.DataFrame.from_records(rows, columns=columns)

    # MySQL NULL markers and empty numeric fields represent missing values.
    for column in NUMERIC:
        values = frame[column].replace({"": None, "NULL": None, "N": None})
        frame[column] = pd.to_numeric(values, errors="raise")
    if frame["PARTICIPANT_ID"].isna().any() or not frame["PARTICIPANT_ID"].is_unique:
        raise ValueError("Participant identifiers must be present and unique")
    if frame[["AGE", "WPM", "ERROR_RATE"]].isna().any().any():
        raise ValueError("Age, WPM and error rate must be present in the released sample")
    return frame


def _finger_count(report: str, hand: str) -> float:
    report = report.strip().lower()
    for count, pattern in FINGER_PATTERNS:
        if re.search(pattern, report):
            return count
    if report == "0":
        return {"both_hands": 2, "left_hand": 1, "right_hand": 1}.get(hand, 0)
    return pd.to_numeric(report, errors="coerce")


def _clean_participants(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = frame.copy()
    frame["FINGERS"] = frame["FINGERS"].replace(LEGACY_POSTURE)
    posture = frame["FINGERS"].str.split(";", n=2, expand=True).reindex(columns=range(3))
    frame[["HAND", "FINGER"]] = posture[[0, 1]].fillna("0")
    frame["NUM_FINGERS"] = [
        _finger_count(report, hand)
        for report, hand in zip(posture[2].fillna("0"), frame["HAND"])
    ]
    frame["HAND_FINGER"] = frame["HAND"] + ";" + frame["FINGER"]
    frame["TIME_SPENT_TYPING"] = pd.to_numeric(frame["TIME_SPENT_TYPING"], errors="coerce")
    frame["TYPE_ENGLISH"] = frame["TYPE_ENGLISH"].replace("", "native")

    filters = (
        ("wpm_outliers", (frame["WPM"] <= 0) | (frame["WPM"] >= 200)),
        ("error_rate_outliers", (frame["ERROR_RATE"] < 0) | (frame["ERROR_RATE"] >= 25)),
        ("unspecified_posture", frame["FINGERS"].isin(["undefined;undefined", "false", "other"])),
        ("missing_device", frame["DEVICE"].isin(["", "0", "N", "NULL"])),
        ("desktop_device", frame["DEVICE"].eq("desktop")),
        ("incomplete_hand_finger", frame["HAND"].eq("undefined")
         | frame["FINGER"].isin(["undefined", "false"])),
        ("invalid_typing_hours", (frame["TIME_SPENT_TYPING"] < 0) | (frame["TIME_SPENT_TYPING"] > 24)),
    )
    audit = [("source", 0, len(frame))]
    for step, excluded in filters:
        before = len(frame)
        frame = frame.loc[~excluded.loc[frame.index]]
        audit.append((step, before - len(frame), len(frame)))

    frame = frame.reset_index(drop=True)
    age_decade = (frame["AGE"] // 10 * 10).astype(int)
    frame["AGE_BAND"] = age_decade.astype(str) + "-" + (age_decade + 9).astype(str)
    return frame, pd.DataFrame(audit, columns=["step", "removed", "remaining"])


def load_data(
    raw_dir: Path, *, offline: bool = False, archive: Path | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return the clean participant frame and sequential exclusion audit."""
    files = _acquire(raw_dir, offline, archive)
    return _clean_participants(_read_participants(files))
