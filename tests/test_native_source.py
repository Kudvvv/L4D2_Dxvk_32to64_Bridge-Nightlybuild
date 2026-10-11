# SPDX-License-Identifier: MIT
import unittest

from scripts.native_source import function, function_bounds


class NativeSourceTests(unittest.TestCase):
    def test_function_try_keeps_all_handlers_without_next_function(self):
        expected = '''HRESULT create() try {
  const char* text = "} catch (...) {";
  // } is not a delimiter
  auto result = [] { return 3; }();
  return result;
} catch (const ReadFailure&) { return -1; }
catch (...) { /* { */ return -2; }'''
        source = expected + '\nvoid unrelated() { abort(); }\n'
        self.assertEqual(function(source, 'HRESULT create()'), expected + '\n')
        _, _, body_end, _ = function_bounds(source, 'HRESULT create()')
        self.assertTrue(source[body_end:].startswith(' catch (const ReadFailure&)'))

    def test_plain_function_with_internal_try_has_no_outer_handlers(self):
        expected = 'void release() { try { work(); } catch (...) {} }'
        self.assertEqual(function(expected + '\nvoid next() {}', 'void release()'), expected + '\n')

    def test_missing_outer_handler_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Function-try handler missing'):
            function('int create() try { return 0; }\nint next() {}', 'int create()')

    def test_duplicate_or_unclosed_function_is_rejected(self):
        for source in ['int create() {}\nint create() {}', 'int create() { if (true) { return 0; }']:
            with self.assertRaises(ValueError):
                function(source, 'int create()')


if __name__ == '__main__':
    unittest.main()
