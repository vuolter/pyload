# -*- coding: utf-8 -*-
# @author: vuolter

"""Store all useful functions here"""

from __future__ import with_statement

import __builtin__
import bitmath
import htmlentitydefs
import os
import re
import string
import subprocess
import time
import traceback

from pyload.utils import convert, pylgettext as gettext
from pyload.utils.encoding import *

# abstraction layer for json operations
try:
    import simplejson as json
except ImportError:
    import json

from bottle import json_loads, json_dumps


def compare_time(start, end):
    start = map(int, start)
    end   = map(int, end)

    if start == end:
        return True

    now = list(time.localtime()[3:5])
    if start < now < end \
       or start < now > end < start \
       or start > end and (now > start or now < end):
        return True

    return False


def format_size(size):
    """Formats size of bytes"""
    return bitmath.Byte(int(size)).best_prefix()


def format_speed(speed):
    return format_size(speed) + "/s"


def free_space(folder):
    if os.name == "nt":
        import ctypes

        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder), None, None, ctypes.pointer(free_bytes))
        return free_bytes.value
    else:
        s = os.statvfs(folder)
        return s.f_frsize * s.f_bavail


def fs_bsize(path):
    """Get optimal file system buffer size (in bytes) for I/O calls"""
    path = fs_encode(path)

    if os.name == "nt":
        import ctypes

        drive = "%s\\" % os.path.splitdrive(path)[0]
        cluster_sectors, sector_size = ctypes.c_longlong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceW(ctypes.c_wchar_p(drive), ctypes.pointer(cluster_sectors), ctypes.pointer(sector_size), None, None)
        return cluster_sectors * sector_size
    else:
        return os.statvfs(path).f_frsize


def uniqify(seq):  #: Originally by Dave Kirby
    """Remove duplicates from list preserving order"""
    seen     = set()
    seen_add = seen.add
    return [x for x in seq if x not in seen and not seen_add(x)]


def parse_size(string, unit=None):  #: returns bytes
    if not unit:
        m = re.match(r"([\d.,]+) *([a-zA-Z]*)", string.strip().lower())
        if m:
            traffic = float(m.group(1).replace(",", "."))
            unit = m.group(2)
        else:
            return 0
    else:
        if isinstance(string, basestring):
            traffic = float(string.replace(",", "."))
        else:
            traffic = string

    return convert.size(traffic, unit.lower().strip(), "byte")


def bits_set(bits, compare):
    """Checks if all bits are set in compare, or bits is 0"""
    return bits == (bits & compare)


def fixup(m):
    text = m.group(0)
    if text[:2] == "&#":
        # character reference
        try:
            if text[:3] == "&#x":
                return unichr(int(text[3:-1], 16))
            else:
                return unichr(int(text[2:-1]))
        except ValueError:
            pass
    else:
        # named entity
        try:
            name = text[1:-1]
            text = unichr(htmlentitydefs.name2codepoint[name])
        except KeyError:
            pass

    return text  #: leave as is


def has_method(obj, name):
    """Check if "name" was defined in obj, (false if it was inhereted)"""
    return hasattr(obj, '__dict__') and name in obj.__dict__


def accumulate(it, inv_map=None):
    """Accumulate (key, value) data to {value : [keylist]} dictionary"""
    if inv_map is None:
        inv_map = {}

    for key, value in it:
        if value in inv_map:
            inv_map[value].append(key)
        else:
            inv_map[value] = [key]

    return inv_map


def get_index(l, value):
    """.index method that also works on tuple and python 2.5"""
    for pos, t in enumerate(l):
        if t == value:
            return pos

    # Matches behavior of list.index
    raise ValueError("list.index(x): x not in list")


def html_unescape(text):
    """Removes HTML or XML character references and entities from a text string"""
    return re.sub("&#?\w+;", fixup, text)


def load_translation(name, locale, default="en"):
    """Load language and return its translation object or None"""

    try:
        gettext.setpaths([os.path.join(os.sep, "usr", "share", "pyload", "locale"), None])
        translation = gettext.translation(name, os.path.join(pypath, "locale"),
                                          languages=[locale, default], fallback=True)
    except Exception:
        traceback.print_exc()
        return None
    else:
        translation.install(True)
        return translation


def chunks(iterable, size):
    it   = iter(iterable)
    item = list(itertools.islice(it, size))
    while item:
        yield item
        item = list(itertools.islice(it, size))


def set_configdir(self, configdir, persistent=False):
    dirname = os.path.abspath(configdir)
    try:
        if not os.path.exists(os.path.dirname):
            os.makedirs(os.path.dirname, 0700)

        os.chdir(os.path.dirname)

        if persistent:
            c = os.path.join(rootdir, "config", "configdir")
            if not os.path.exists(c):
                os.makedirs(c, 0700)

            with open(c, "wb") as f:
                f.write(os.path.dirname)

    except IOError:
        return False

    else:
        __builtin__.configdir = dirname
        return dirname  #: return always abspath


def check_module(self, module):
    try:
        __import__(module)
        return True

    except Exception:
        return False


def check_prog(self, command):
    pipe = subprocess.PIPE
    try:
        subprocess.call(command, stdout=pipe, stderr=pipe)
        return True

    except Exception:
        return False
