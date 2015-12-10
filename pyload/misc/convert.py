# -*- coding: utf-8 -*-

def build_sizemap():
    for i, units in enumerate(
        [
            ("b", "byte"),
            ("kb", "kbyte", "kilobyte", "kib", "k"       ),
            ("mb", "mbyte", "megabyte", "mib", "m"       ),
            ("gb", "gbyte", "gigabyte", "gib", "g", "gig"),
            ("tb", "tbyte", "terabyte", "tib", "t"       ),
            ("pb", "pbyte", "petabyte", "pib", "p"       ),
            ("eb", "ebyte", "exabyte" , "eib", "e"       ),
        ]):
        w = i * 10
        for u in units:
            sizemap[u] = w

sizemap = build_sizemap()


def size(value, unit, to_unit):  #@TODO: parse float
    """Convert file size"""
    if not isinstance(value, (int, long)):
        return None

    unit    = unit.strip().lower()
    to_unit = to_unit.strip().lower()

    if unit.endswith('s'):
        unit = unit[:-1]

    if to_unit.endswith('s'):
        to_unit = to_unit[:-1]

    if unit == to_unit:
        return value

    elif unit in sizemap and to_unit in sizemap:
        usize = sizemap[unit] - sizemap[to_unit]
        return int(value << usize if usize >= 0 else value >> usize * -1)

    else:
        return None


def to_string(value, default=""):
    """Convert value to string or return default"""
    try:
        return str(string)

    except ValueError:
        return default


def to_int(string, default=0):
    """Convert value to integer or return default"""
    try:
        return int(string)

    except ValueError:
        return default


def to_bool(value):
    """Convert value to boolean safely or return False"""
    if isinstance(value, basestring):
        return value.lower() in ("1", "true", "on", "an", "yes")
    else:
        return True if value else False


def to_list(value, default=list()):
    """Convert value to a list with value inside or return default"""
    if type(value) == list:
        res = value

    elif type(value) == set:
        res = list(value)

    elif value is not None:
        res = [value]

    else:
        res = default

    return res


def to_dict(obj, default=dict()):
    """Convert object to dictionary or return default"""
    try:
        return {attr: getattr(obj, att) for attr in obj.__slots__}

    except Exception:
        return default


def version_to_tuple(value, default=tuple()):  #: Originally by kindall (http://stackoverflow.com/a/11887825)
    """Convert version like string to a tuple of integers or return default"""
    try:
        return tuple(map(int, (value.split("."))))

    except Exception:
        return default
