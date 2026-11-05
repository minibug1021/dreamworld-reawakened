"""Applies the ActionScript patches to the SWFs with ffdec (JPEXS Free Flash Decompiler).

A SWF is patched by exporting the classes that have a patch, editing the exported
source, and importing it back. That needs Java, and downloads a pinned ffdec the first
time. The results are kept in patches/<name>.patched.swf, so this normally only happens
when one of those files is missing.
"""
import hashlib
import logging
import shutil
import subprocess
from pathlib import Path
from urllib.request import urlretrieve
from zipfile import ZipFile

from config import ROOT_DIR
from utils.patching.swf_patches import INSERTIONS, SWF_PATHS, Insertion

logger = logging.getLogger(__name__)

PATCHES_DIR = ROOT_DIR / "patches"
SCRIPTS_DIR = PATCHES_DIR / "scripts"  # ffdec's temporary export directory

FFDEC_JAR = PATCHES_DIR / "ffdec.jar"
FFDEC_ZIP = PATCHES_DIR / "ffdec.zip"
JAVA      = "java"


FFDEC_URL    = "https://github.com/jindrapetrik/jpexs-decompiler/releases/download/version26.4.0/ffdec_26.4.0.zip"
FFDEC_SHA256 = "56ce960aeafc7caf034e2052ba49f878a883f7c7ca690da6eeffca9587b5e4b9"  # GitHub's release digest


class PatchError(Exception):
    """A patch's original code wasn't found as expected (e.g. a different ffdec version)."""


def _block_end(lines: list[str], header: int) -> int:
    """Return the index of the line after the brace block that starts at lines[header].

    The block includes any `else` branches. ffdec puts braces on their own lines.
    """
    indent = len(lines[header]) - len(lines[header].lstrip())
    i = header
    while True:
        if lines[i + 1].strip() != "{":
            raise PatchError(f"no block after {lines[i].strip()!r}")
        i = next(j for j in range(i + 2, len(lines))
                 if lines[j].strip() == "}" and len(lines[j]) - len(lines[j].lstrip()) == indent)
        if i + 1 < len(lines) and lines[i + 1].strip().startswith("else"):
            i += 1
            continue
        return i + 1


def apply_insertion(source: str, insertion: Insertion) -> str:
    """Return the class source with `insertion` applied.

    Raise PatchError if `old` doesn't occur exactly `insertion.count` times.
    """
    lines = source.splitlines(keepends=True)
    old = [line.strip() for line in insertion.old.splitlines()]
    stripped = [line.strip() for line in lines]
    starts = [i for i in range(len(lines) - len(old) + 1) if stripped[i:i + len(old)] == old]
    if len(starts) != insertion.count:
        raise PatchError(f"{insertion.class_path}: expected {insertion.count} match(es) for "
                         f"{insertion.old!r}, found {len(starts)}")

    for start in reversed(starts):
        end = _block_end(lines, start) if insertion.block else start + len(old)
        padding = len(lines[start]) - len(lines[start].lstrip(" "))
        # an empty replacement leaves one blank line
        lines[start:end] = ["\n".join(" " * padding + line for line in insertion.replacement.splitlines()) + "\n"]
    return "".join(lines)


_PATCHED_CACHE: dict[str, bytes] = {}  # SWF name -> patched bytes


def _patched_path(swf_name: str) -> Path:
    return PATCHES_DIR / f"{Path(swf_name).stem}.patched.swf"


def prewarm() -> None:
    """Load every patched SWF into memory, patching the ones not cached on disk yet."""
    PATCHES_DIR.mkdir(exist_ok=True)

    # only the SWFs missing from disk are regenerated
    missing = [swf_name for swf_name in SWF_PATHS if not _patched_path(swf_name).exists()]

    for swf_name in SWF_PATHS:
        if swf_name not in missing:
            _PATCHED_CACHE[swf_name] = _patched_path(swf_name).read_bytes()

    if not missing:
        logger.info("Loading patched SWFs from disk")
        return

    logger.info("Loading %d cached SWF(s) from disk, patching %d new one(s)", len(SWF_PATHS) - len(missing), len(missing))

    download_ffdec()

    for swf_name in missing:
        logger.info("Patching %s", swf_name)
        _PATCHED_CACHE[swf_name] = _patch_swf(swf_name)

    # remove ffdec's temp export dir and the downloaded zip, but keep the
    # .swf outputs, the ffdec.jar itself, and its lib/ dependencies
    shutil.rmtree(SCRIPTS_DIR, ignore_errors=True)
    FFDEC_ZIP.unlink(missing_ok=True)


def download_ffdec() -> None:
    """Download the pinned ffdec into patches/, checking its SHA-256.

    Do nothing if it's already there.
    """
    if FFDEC_JAR.exists():
        return

    logger.info("Need to download ffdec for swf patching")
    urlretrieve(FFDEC_URL, FFDEC_ZIP)
    digest = hashlib.sha256(FFDEC_ZIP.read_bytes()).hexdigest()
    if digest != FFDEC_SHA256:
        FFDEC_ZIP.unlink()
        raise RuntimeError(f"Downloaded ffdec has SHA-256 {digest}, expected {FFDEC_SHA256}; not using it.")
    with ZipFile(FFDEC_ZIP) as z:
        z.extractall(PATCHES_DIR)


def get_patched_swf(swf_name: str) -> bytes:
    """Return the patched SWF's bytes, which prewarm() loaded."""
    return _PATCHED_CACHE[swf_name]


def _script_path(class_path: str) -> Path:
    """Return where ffdec exports a class's source (a.b.C -> scripts/a/b/C.as)."""
    *module_parts, class_name = class_path.split(".")
    return SCRIPTS_DIR / Path(*module_parts) / f"{class_name}.as"


def _patch_swf(swf_name: str) -> bytes:
    """Patch one SWF with ffdec and return the result.

    The patched SWF is also saved in patches/.
    """
    src_path = SWF_PATHS[swf_name]
    out_path = _patched_path(swf_name)

    shutil.copy(src_path, out_path)

    try:
        # export only the scripts which have a patch
        export_list = ",".join(dict.fromkeys(i.class_path for i in INSERTIONS[swf_name]))
        subprocess.run(
            [JAVA, "-jar", FFDEC_JAR, "-selectclass", export_list, "-export", "script", PATCHES_DIR, out_path],
            stdout=subprocess.DEVNULL, check=True,
        )

        # apply patches to exported .as files
        for insertion in INSERTIONS[swf_name]:
            file_path = _script_path(insertion.class_path)
            file_path.write_text(apply_insertion(file_path.read_text(encoding="UTF-8"), insertion), encoding="UTF-8")

        # reimport .as files into .swf
        subprocess.run(
            [JAVA, "-jar", FFDEC_JAR, "-importScript", out_path, out_path, SCRIPTS_DIR],
            stdout=subprocess.DEVNULL, check=True,
        )

        out_bytes = out_path.read_bytes()
    except Exception:
        # out_path is a bogus (unpatched, or partially-patched) copy at this
        # point - remove it so a failed run can never be mistaken for a
        # valid cache entry on the next prewarm().
        out_path.unlink(missing_ok=True)
        raise
    finally:
        shutil.rmtree(SCRIPTS_DIR, ignore_errors=True)

    return out_bytes
