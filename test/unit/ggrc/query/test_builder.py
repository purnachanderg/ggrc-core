# Copyright (C) 2019 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Tests for the ggrc.query.builder module."""

import unittest
import mock

from ggrc.query import builder


class TestQueryHelper(unittest.TestCase):
  """Tests for QueryHelper Class"""

  def test_expression_keys(self):
    """ test expression keys function

    Make sure it works with:
      empty query
      simple query
      complex query
      invalid complex query
    """
    # pylint: disable=protected-access
    # needed for testing protected function inside the query helper
    query = mock.MagicMock()
    helper = builder.QueryHelper(query)

    expressions = [
        (set(), {}),
        (set(["key_1"]), {
            "left": "key_1",
            "op": {"name": "="},
            "right": "",
        }),
        (set(["key_1", "key_2"]), {
            "left": {
                "left": "key_2",
                "op": {"name": "="},
                "right": "",
            },
            "op": {"name": "AND"},
            "right": {
                "left": "key_1",
                "op": {"name": "!="},
                "right": "",
            },
        }),
        (set(), {
            "left": {
                "left": "5",
                "op": {"name": "="},
                "right": "",
            },
            "op": {"name": "="},
            "right": {
                "left": "key_1",
                "op": {"name": "!="},
                "right": "",
            },
        }),
    ]

    for expected_result, expression in expressions:
      self.assertEqual(expected_result, helper._expression_keys(expression))
