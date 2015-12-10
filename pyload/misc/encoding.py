# -*- coding: utf-8 -*-

import os
import sys
import urllib


def decode(string):
    """Decode string to unicode with utf8"""
    if type(string) == str:
        return string.decode("utf8", "replace")
    else:
        return string


def encode(string):
    """Decode string to utf8"""
    if type(string) == unicode:
        return string.encode("utf8", "replace")
    else:
        return string


def remove_chars(string, repl):
    """Removes all chars in repl from string"""
    if type(repl) == unicode:
        for badc in list(repl):
            string = string.replace(badc, "")

        return string

    else:
        if type(string) == str:
            return string.translate(string.maketrans("", ""), repl)

        elif type(string) == unicode:
            return string.translate(dict((ord(s), None) for s in repl))


def safe_filename(name):
    """Remove bad chars"""
    name = urllib.unquote(name).encode('ascii', 'replace')  #: Non-ASCII chars usually breaks file saving. Replacing.
    if os.name == 'nt':
        return remove_chars(name, u'\00\01\02\03\04\05\06\07\10\11\12\13\14\15\16\17\20\21\22\23\24\25\26\27\30\31\32'
                                  u'\33\34\35\36\37/?%*|"<>')
    else:
        return remove_chars(name, u'\0\\"')


def fs_join(*args):
    """Joins a path, encoding aware"""
    return fs_encode(os.path.join(*[x if type(x) == unicode else decode(x) for x in args]))


# Use fs_encode before accesing files on disk, it will encode the string properly
if sys.getfilesystemencoding().startswith('ANSI'):
    def fs_encode(string):
        return safe_filename(encode(string))

    fs_decode = decode  #: decode utf8
else:
    fs_encode = fs_decode = lambda x: x  #: do nothing


def get_console_encoding(enc):
    if os.name == "nt":
        if enc == "cp65001":  #: aka UTF-8
            enc = "cp850"
            print "WARNING: Windows codepage 65001 (UTF-8) is not supported. Used \"%s\" instead." % enc
    else:
        enc = "utf8"

    return enc
