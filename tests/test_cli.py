import unittest
from mock import patch
import io
from chickenham import cli


class TestGreeting(unittest.TestCase):
    greeting_output = "\n".join([r"       ___          _        _   ",
                                 r"      | _ \_ _ ___ (_)___ __| |_ ",
                                 r"      |  _/ '_/ _ \| / -_) _|  _|",
                                 r"      |_| |_| \___// \___\__|\__|",
                                 r"  ___ _    _    _ |__/       _  _ ",
                                 r" / __| |_ (_)__| |_____ _ _ | || |__ _ _ __  ",
                                 r"| (__| ' \| / _| / / -_) ' \| __ / _` | '  \ ",
                                 r" \___|_||_|_\__|_\_\___|_||_|_||_\__,_|_|_|_|",
                                 "\n"])

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_greeting(self, mock_stdout):
        cli.greeting()
        self.assertEqual(mock_stdout.getvalue(), self.greeting_output)
