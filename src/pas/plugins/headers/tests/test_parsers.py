# -*- coding: utf-8 -*-
import unittest


class ParsersUnitTests(unittest.TestCase):

    def test_boolean(self):
        from pas.plugins.headers.parsers import _boolean
        self.assertEqual(_boolean(None), False)
        self.assertEqual(_boolean(0), False)
        self.assertEqual(_boolean(1), True)
        self.assertEqual(_boolean(2), True)
        self.assertEqual(_boolean('1'), True)
        self.assertEqual(_boolean('2'), False)
        self.assertEqual(_boolean(object()), True)
        self.assertEqual(_boolean(''), False)
        self.assertEqual(_boolean('no'), False)
        self.assertEqual(_boolean('nee'), False)
        self.assertEqual(_boolean('false'), False)
        self.assertEqual(_boolean('yes'), True)
        self.assertEqual(_boolean('ja'), True)
        self.assertEqual(_boolean('true'), True)
        self.assertEqual(_boolean('y'), True)
        self.assertEqual(_boolean('j'), True)
        self.assertEqual(_boolean('t'), True)
        self.assertEqual(_boolean('t at the beginning'), True)
        self.assertEqual(_boolean('123 - one at the beginning'), True)
        self.assertEqual(_boolean(' true with space'), True)
        self.assertEqual(_boolean(' false with space'), False)
        self.assertEqual(_boolean('\n\t  true with any whitespace '), True)
        self.assertEqual(_boolean('random'), False)
        self.assertEqual(_boolean(' random'), False)

    def test_int(self):
        from pas.plugins.headers.parsers import _int
        self.assertEqual(_int(None), 0)
        self.assertEqual(_int(0), 0)
        self.assertEqual(_int(1), 1)
        self.assertEqual(_int(object()), 0)
        self.assertEqual(_int(''), 0)
        self.assertEqual(_int('no'), 0)
        self.assertEqual(_int('nee'), 0)
        self.assertEqual(_int('42'), 42)
        self.assertEqual(_int('1.0'), 0)
        self.assertEqual(_int('1,0'), 0)
        self.assertEqual(_int('1.'), 0)
        self.assertEqual(_int(' \n  7   '), 7)
        self.assertEqual(_int('-81'), -81)

    def test_lower(self):
        from pas.plugins.headers.parsers import _lower
        self.assertEqual(_lower(None), '')
        self.assertEqual(_lower(0), '')
        self.assertEqual(_lower(1), '')
        self.assertEqual(_lower(object()), '')
        self.assertEqual(_lower(''), '')
        self.assertEqual(_lower('    '), '')
        self.assertEqual(_lower('no'), 'no')
        self.assertEqual(_lower('No'), 'no')
        self.assertEqual(_lower('NO'), 'no')
        self.assertEqual(_lower('  \n\t\r  NO   '), 'no')
        self.assertEqual(_lower('ONE  two\n THRee'), 'one  two\n three')
        self.assertEqual(_lower('42'), '42')

    def test_upper(self):
        from pas.plugins.headers.parsers import _upper
        self.assertEqual(_upper(None), '')
        self.assertEqual(_upper(0), '')
        self.assertEqual(_upper(1), '')
        self.assertEqual(_upper(object()), '')
        self.assertEqual(_upper(''), '')
        self.assertEqual(_upper('    '), '')
        self.assertEqual(_upper('no'), 'NO')
        self.assertEqual(_upper('No'), 'NO')
        self.assertEqual(_upper('NO'), 'NO')
        self.assertEqual(_upper('  \n\t\r  NO   '), 'NO')
        self.assertEqual(_upper('ONE  two\n THRee'), 'ONE  TWO\n THREE')
        self.assertEqual(_upper('42'), '42')

    def test_split(self):
        from pas.plugins.headers.parsers import _split
        self.assertEqual(_split(None), [])
        self.assertEqual(_split(0), [])
        self.assertEqual(_split(1), [])
        self.assertEqual(_split(object()), [])
        self.assertEqual(_split(''), [])
        self.assertEqual(_split('    '), [])
        self.assertEqual(_split('no'), ['no'])
        self.assertEqual(_split('No'), ['No'])
        self.assertEqual(_split('NO'), ['NO'])
        self.assertEqual(_split('  \n\t\r  NO   '), ['NO'])
        self.assertEqual(_split('ONE  two\n THRee'), ['ONE', 'two', 'THRee'])
        self.assertEqual(_split('42'), ['42'])

    def test_parse(self):
        from pas.plugins.headers.parsers import parse
        self.assertEqual(parse(None, 'Value'), 'Value')
        self.assertEqual(parse('bool', 'Value'), False)
        self.assertEqual(parse('int', 'Value'), 0)
        self.assertEqual(parse('lower', 'Value'), 'value')
        self.assertEqual(parse('upper', 'Value'), 'VALUE')
        self.assertEqual(parse('split', 'Value'), ['Value'])

        self.assertEqual(parse('bool', 'y'), True)
        self.assertEqual(parse('int', 'y'), 0)
        self.assertEqual(parse('lower', 'y'), 'y')
        self.assertEqual(parse('upper', 'y'), 'Y')
        self.assertEqual(parse('split', 'y'), ['y'])

        self.assertEqual(parse('bool', '1'), True)
        self.assertEqual(parse('int', '1'), 1)
        self.assertEqual(parse('lower', '1'), '1')
        self.assertEqual(parse('upper', '1'), '1')
        self.assertEqual(parse('split', '1'), ['1'])

        self.assertEqual(parse('bool', 'AB CD'), False)
        self.assertEqual(parse('int', 'AB CD'), 0)
        self.assertEqual(parse('lower', 'AB CD'), 'ab cd')
        self.assertEqual(parse('upper', 'AB CD'), 'AB CD')
        self.assertEqual(parse('split', 'AB CD'), ['AB', 'CD'])

        # Test a corner case of the parse function:
        # catch some errors in parsers.
        def simple_lower(value):
            return value.no_such_attribute

        from pas.plugins.headers.parsers import register_parser
        register_parser('simple', simple_lower)
        self.assertEqual(parse('simple', 'foo'), 'foo')

    def test_register_parser_and_get_parser(self):
        # They only make sense to test in combination.
        from pas.plugins.headers.parsers import register_parser
        from pas.plugins.headers.parsers import get_parser
        from pas.plugins.headers.parsers import parse

        def duplicator(value):
            return value + value

        self.assertEqual(get_parser('dup'), None)
        self.assertEqual(parse('dup', 'foo'), 'foo')
        self.assertEqual(register_parser('dup', duplicator), None)
        self.assertEqual(get_parser('dup'), duplicator)
        self.assertEqual(parse('dup', 'foo'), 'foofoo')

        # Overriding a parser is possible.

        def triplicator(value):
            return value + value + value

        self.assertEqual(register_parser('dup', triplicator), None)
        self.assertEqual(get_parser('dup'), triplicator)
        self.assertEqual(parse('dup', 'foo'), 'foofoofoo')
