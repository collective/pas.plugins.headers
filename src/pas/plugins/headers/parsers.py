# -*- coding: utf-8 -*-
# Define parsers for header values.


# yes, ja, true
_true_chars = 'y j t'.split()


def _boolean(value):
    if not isinstance(value, basestring):
        return bool(value)
    if not value:
        return False
    # Compare the first character.
    first = value[0].lower()
    return first in _true_chars


def _int(value):
    return int(value)


def _lower(value):
    return value.lower()


def _upper(value):
    return value.upper()


# List of parsers.  Internal.  Do not import this.
_parsers = {}


def register_parser(name, fun):
    # Note: this does not warn when overriding a parser.
    _parsers[name] = fun


def get_parser(name):
    return _parsers.get(name)


def parse(parser_name, value):
    parser = get_parser(parser_name)
    if parser is None:
        return value
    try:
        return parser(value)
    except (ValueError, TypeError, AttributeError):
        return value


# Register our own basic parsers.
register_parser('bool', _boolean)
register_parser('int', _int)
register_parser('lower', _lower)
register_parser('upper', _upper)
