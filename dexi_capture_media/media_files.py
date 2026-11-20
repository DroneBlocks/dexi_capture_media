"""File helpers for capture_media: naming, listing and HTTP Range parsing.

No ROS imports, so the logic is unit-testable off the drone.
"""
import os
import re
from datetime import datetime

PHOTO_EXTS = ('jpg', 'png')
VIDEO_EXTS = ('mp4',)

# Only files this node wrote are served or deleted. Anything else in the
# directory (including an in-progress *.part recording) is invisible.
_NAME_RE = re.compile(r'^(photo|video)_[0-9_]+\.(jpg|png|mp4)$')

MIME = {'jpg': 'image/jpeg', 'png': 'image/png', 'mp4': 'video/mp4'}


def is_valid_name(name):
    return bool(_NAME_RE.match(name or ''))


def media_type(name):
    return 'photo' if name.startswith('photo_') else 'video'


def mime_type(name):
    return MIME.get(name.rsplit('.', 1)[-1], 'application/octet-stream')


def _stamp(now=None):
    now = now or datetime.now()
    return now.strftime('%Y%m%d_%H%M%S_') + f'{now.microsecond // 1000:03d}'


def photo_name(fmt, now=None):
    """File name for a photo; fmt is CompressedImage.format ('jpeg', 'png', 'rgb8; jpeg ...')."""
    ext = 'png' if 'png' in (fmt or '').lower() else 'jpg'
    return f'photo_{_stamp(now)}.{ext}'


def video_name(now=None):
    return f'video_{_stamp(now)}.mp4'


def list_media(directory):
    """Newest first: [{name, type, size, mtime}]."""
    out = []
    try:
        entries = os.scandir(directory)
    except FileNotFoundError:
        return out
    with entries:
        for e in entries:
            if e.is_file() and is_valid_name(e.name):
                st = e.stat()
                out.append({'name': e.name, 'type': media_type(e.name),
                            'size': st.st_size, 'mtime': st.st_mtime})
    out.sort(key=lambda f: f['mtime'], reverse=True)
    return out


def parse_range(header, size):
    """Parse a single 'bytes=a-b' Range header.

    Returns (start, end) inclusive, None when there is no usable header (serve
    the whole file), or 'unsatisfiable' when the range is outside the file.
    """
    if not header or not header.startswith('bytes=') or ',' in header:
        return None
    a, _, b = header[6:].strip().partition('-')
    try:
        if a == '':                 # suffix: last N bytes
            n = int(b)
            if n <= 0:
                return 'unsatisfiable'
            return max(0, size - n), size - 1
        start = int(a)
        end = int(b) if b else size - 1
    except ValueError:
        return None
    if start >= size or start > end:
        return 'unsatisfiable'
    return start, min(end, size - 1)
