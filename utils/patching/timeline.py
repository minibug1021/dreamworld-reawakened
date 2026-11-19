"""Cuts a SWF's main timeline down to its first frame.

Ruffle plays the main timeline of every SWF it loads, even one whose document class is a
Sprite and so has no stop().
"""
import struct
import zlib
from collections.abc import Iterator

SHOW_FRAME = 1
END = 0

DROPPABLE_TAGS = {SHOW_FRAME, END, 26, 28, 70}


def _tags(body: bytes, offset: int) -> Iterator[tuple[int, int]]:
    """Yield (code, end) for each tag from `offset`, stopping after the End tag."""
    while offset < len(body):
        code_and_length = struct.unpack_from("<H", body, offset)[0]
        offset += 2
        code, length = code_and_length >> 6, code_and_length & 0x3F
        if length == 0x3F:
            length = struct.unpack_from("<I", body, offset)[0]
            offset += 4
        offset += length
        yield code, offset
        if code == END:
            return


def keep_first_frame(swf: bytes) -> bytes:
    """Return `swf` with only the first frame of its main timeline.

    Raise ValueError if the SWF is LZMA-compressed, has no frame, or its later frames
    contain anything besides placing and removing objects (such as code or graphics).
    """
    signature, version = swf[:3], swf[3]
    if signature == b"CWS":
        body = zlib.decompress(swf[8:])
    elif signature == b"FWS":
        body = swf[8:]
    else:
        raise ValueError(f"Unsupported SWF signature {signature!r}.")

    rect_bits = 5 + 4 * (body[0] >> 3)
    frame_count_at = (rect_bits + 7) // 8 + 2

    first_frame_end = None
    for code, end in _tags(body, frame_count_at + 2):
        if first_frame_end is None:
            if code == SHOW_FRAME:
                first_frame_end = end
        elif code not in DROPPABLE_TAGS:
            raise ValueError(f"Frame 2 or later has tag {code}, which can't be dropped safely.")
    if first_frame_end is None:
        raise ValueError("The SWF has no frame.")

    new_body = bytearray(body[:first_frame_end] + struct.pack("<H", END << 6))
    struct.pack_into("<H", new_body, frame_count_at, 1)
    header = signature + bytes([version]) + struct.pack("<I", 8 + len(new_body))
    return header + (zlib.compress(bytes(new_body)) if signature == b"CWS" else bytes(new_body))
