# -*- coding: utf-8 -*-
# Define parsers for header values.
import logging


logger = logging.getLogger(__name__)
# yes, ja, true
_true_chars = 'y j t 1'.split()


def _boolean(value):
    if not isinstance(value, basestring):
        return bool(value)
    value = value.strip()
    if not value:
        return False
    # Compare the first character.
    first = value[0].lower()
    return first in _true_chars


def _int(value):
    try:
        return int(value)
    except (ValueError, TypeError, AttributeError):
        return 0


def _lower(value):
    if not isinstance(value, basestring):
        return ''
    value = value.strip()
    return value.lower()


def _upper(value):
    if not isinstance(value, basestring):
        return ''
    value = value.strip()
    return value.upper()


def _split(value):
    if not isinstance(value, basestring):
        return []
    return value.split()


# List of parsers.  Internal.  Do not import this.
_parsers = {}


def register_parser(name, fun):
    if name in _parsers:
        logger.warning('Overriding parser "%s".', name)
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
register_parser('split', _split)
