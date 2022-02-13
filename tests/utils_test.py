# pylint: disable=invalid-name,line-too-long,missing-module-docstring,missing-class-docstring,missing-function-docstring

import unittest
from unittest.mock import patch, mock_open

from regview.utils import pretty_date, pretty_size, get_docker_credentials


class Test_utils(unittest.TestCase):
    def test_pretty_date(self):
        self.assertEqual(pretty_date("2020-03-04T06:39:52Z"), "Wed Mar 04 07:39:52 CET 2020")
        self.assertEqual(pretty_date("2020-09-09T01:38:02.334927351Z"), "Wed Sep 09 03:38:02 CEST 2020")

    def test_pretty_size(self):
        self.assertEqual(pretty_size(20983074), "20.01MB")

    @patch('builtins.open', mock_open(read_data='{"auths": {"https://localhost:5000": {"auth": "dGVzdHVzZXI6dGVzdHBhc3N3b3Jk"}}}'))
    def test_get_docker_credentials1(self):
        self.assertEqual(get_docker_credentials("localhost:5000"), ("testuser", "testpassword"))
        self.assertEqual(get_docker_credentials("https://localhost:5000"), ("testuser", "testpassword"))

    @patch('builtins.open', mock_open(read_data='{"auths": {"localhost:5000": {"auth": "dGVzdHVzZXI6dGVzdHBhc3N3b3Jk"}}}'))
    def test_get_docker_credentials2(self):
        self.assertEqual(get_docker_credentials("localhost:5000"), ("testuser", "testpassword"))
        self.assertEqual(get_docker_credentials("https://localhost:5000"), ("testuser", "testpassword"))

    @patch('builtins.open', mock_open(read_data='{"auths": {"http://localhost:5000": {"auth": "dGVzdHVzZXI6dGVzdHBhc3N3b3Jk"}}}'))
    def test_get_docker_credentials3(self):
        self.assertEqual(get_docker_credentials("localhost:5000"), ("testuser", "testpassword"))
        self.assertEqual(get_docker_credentials("http://localhost:5000"), ("testuser", "testpassword"))
