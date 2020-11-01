# pylint: disable=invalid-name,line-too-long,missing-module-docstring,missing-class-docstring,missing-function-docstring

import unittest

from _regview.utils import pretty_date, pretty_size


class Test_utils(unittest.TestCase):
    def test_pretty_date(self):
        self.assertEqual(pretty_date("2020-03-04T06:39:52Z"), "Wed Mar 04 07:39:52 CET 2020")
        self.assertEqual(pretty_date("2020-09-09T01:38:02.334927351Z"), "Wed Sep 09 03:38:02 CEST 2020")

    def test_pretty_size(self):
        self.assertEqual(pretty_size(20983074), "20.01MB")
