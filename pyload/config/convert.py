# -*- coding: utf-8 -*-

from collections import namedtuple
from gettext import gettext

from pyload.utils import decode, to_bool

__all__ = ["from_string", "to_configdata", "to_input"]


#@TODO: Temp stuff... move to api/apitypes.py #################################

class BaseObject(object):
    __version__ = (0, 4, 10)
    __slots__ = []

    def __str__(self):
        return "<%s %s>" % (self.__class__.__name__, ", ".join("%s=%s" % (k,getattr(self,k)) for k in self.__slots__))


class Input(BaseObject):
    __slots__ = ['type', 'default_value', 'data']

    def __init__(self, type=None, default_value=None, data=None):
        self.type = type
        self.default_value = default_value
        self.data = data


class InputType:
    NA = 0
    Text = 1
    Int = 2
    File = 3
    Folder = 4
    Textbox = 5
    Password = 6
    Time = 7
    TimeSpan = 8
    ByteSize = 9
    Bool = 10
    Click = 11
    Select = 12
    Multiple = 13
    List = 14
    PluginList = 15
    Table = 16

###############################################################################


ConfigData = namedtuple("ConfigData", "label description input")

# Maps old config formats to new values
input_dict = {
    "int": InputType.Int,
    "bool": InputType.Bool,
    "time": InputType.Time,
    "file": InputType.File,
    "list": InputType.List,
    "folder": InputType.Folder
}


def to_input(typ):
    """ Converts old config format to input type """
    return input_dict.get(typ, InputType.Text)


def to_configdata(entry):
    if len(entry) != 4:
        raise ValueError("Config entry must be of length 4")

    # Values can have different roles depending on the two config formats
    conf_name, type_label, label_desc, default_input = entry

    # name, label, desc, input
    if isinstance(default_input, Input):
        _input = default_input
        conf_label = type_label
        conf_desc = label_desc
    # name, type, label, default
    else:
        _input = Input(to_input(type_label))
        _input.default_value = from_string(default_input, _input.type)
        conf_label = label_desc
        conf_desc = ""

    return conf_name, ConfigData(gettext(conf_label), gettext(conf_desc), _input)


def from_string(value, typ=None):
    """ cast value to given type, unicode for strings """

    # value is no string
    if not isinstance(value, basestring):
        return value

    value = decode(value)

    if typ == InputType.Int:
        return int(value)
    elif typ == InputType.Bool:
        return to_bool(value)
    elif typ == InputType.Time:
        if not value: value = "0:00"
        if not ":" in value: value += ":00"
        return value
    else:
        return value