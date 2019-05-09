# Copyright (C) 2019 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Helper to use /query api endpoint."""

import json
import operator

from integration.ggrc import TestCase
from ggrc.query import builder


class WithQueryApi(object):
  """Used to construct and perform requests to /query endpoint."""

  class SORTING_KEYS(object):
    """Keys for sorting sublists of the results

    To be used with assertEqual() when results contain sublists
    """
    BY_ID = operator.itemgetter("id")
    BY_EMAIL = operator.itemgetter("email")

  @classmethod
  def _sort_sublists(cls, data_list):
    """Sort lists contained in result list.

    This function is meant to sort sublists in a list of results. Those
    sublists can only be a list of stubs from given objects. So when testing
    an order for a list, if sub elements such as related_sources, don't have
    the same order they must not raise an exception.
    """
    for line in data_list:
      for value in line.viewvalues():
        if isinstance(value, list) and len(value) > 1:
          if "email" in value[0]:
            sorting_key = cls.SORTING_KEYS.BY_EMAIL
          else:
            sorting_key = cls.SORTING_KEYS.BY_ID
          value.sort(key=sorting_key)
    return data_list

  def assertEqual(self,
                  first,
                  second,
                  msg=None,
                  sort_sublists=False):
    """Assert Equality of 2 objects

    with possibility of sorting values inside"""
    if sort_sublists:
      first = self._sort_sublists(first)
      second = self._sort_sublists(second)
    super(WithQueryApi, self).assertEqual(first, second, msg)

  def _post(self, data):
    """Make a POST to /query endpoint."""
    if not isinstance(data, list):
      data = [data]
    headers = {"Content-Type": "application/json", }
    return self.client.post("/query", data=json.dumps(data), headers=headers)

  def _get_first_result_set(self, data, *keys):
    """Post data, get response, get values from it like in obj["a"]["b"]."""
    response = self._post(data)
    self.assert200(response)
    result = json.loads(response.data)[0]
    for key in keys:
      result = result.get(key)
      self.assertIsNot(result, None)
    return result

  def _get_all_result_sets(self, data, *keys):
    """Post data, get response, get values for provided models."""
    response = self._post(data)
    self.assert200(response)
    resp_data = json.loads(response.data)

    result = []
    for obj in resp_data:
      result.extend(obj for key in keys if obj.get(key))
    return result

  @classmethod
  def _clean_query_string(cls, query):
    """Cleans input query string"""
    if not isinstance(query, list):
      query = [query]
    query_helper = builder.QueryHelper(query)
    return query_helper.query

  @staticmethod
  def _make_query_dict_base(object_name, type_=None, filters=None,
                            limit=None, order_by=None):
    """Make a dict with query for object_name with optional parameters."""
    query = {
        "object_name": object_name,
        "filters": filters if filters else {"expression": {}},
    }
    if type_:
      query["type"] = type_
    if limit:
      query["limit"] = limit
    if order_by:
      query["order_by"] = order_by
    return query

  @staticmethod
  def make_filter_expression(expression):
    """Convert a three-tuple to a simple expression filter."""
    left, op_name, right = expression
    return {"left": left, "op": {"name": op_name}, "right": right}

  @classmethod
  def _make_query_dict(cls, object_name, expression=None, *args, **kwargs):
    """Make a dict with query for object_name with expression shortcut.

    expression should be in format: (left, op_name, right), like
    ("title", "=", "hello").
    """

    if expression:
      filters = {"expression": cls.make_filter_expression(expression)}
    else:
      filters = None

    return cls._make_query_dict_base(object_name, filters=filters, *args,
                                     **kwargs)

  @classmethod
  def _make_snapshot_query_dict(cls, child_type, expression=None, *args,
                                **kwargs):
    """Make a dict with query for Snapshots of child_type."""
    child_type_filter = cls.make_filter_expression(("child_type", "=",
                                                    child_type))
    if expression:
      snapshot_filter = cls.make_filter_expression(expression)
      filters = {"expression": {"op": {"name": "AND"},
                                "left": snapshot_filter,
                                "right": child_type_filter}}
    else:
      filters = {"expression": child_type_filter}

    return cls._make_query_dict_base("Snapshot", filters=filters, *args,
                                     **kwargs)

  def simple_query(self, model_name, expression=None, field="values",
                   *args, **kwargs):
    return self._get_first_result_set(
        self._make_query_dict(
            model_name,
            expression=expression,
            *args,
            **kwargs
        ),
        model_name, field
    )


class TestQueryHelper(TestCase, WithQueryApi):
  """Test utils from ggrc.query_helper"""

  def test_assert_qual_with_sublists(self):
    """Test assertEqual util from ggrc.query_helper"""
    unordered_list = [{
        "id": 1,
        "related_sources": [{"id": 4, "title": "lkhtdgg"},
                            {"id": 7, "title": "qwedq"},
                            {"id": 3, "title": "cxzvqw"}],
        "acl_people": [{"email": "c@d.e", "name": "cde"},
                       {"email": "a@b.c", "name": "abc"},
                       {"email": "b@c.d", "name": "bcd"}],
    }, {
        "id": 2,
        "related_sources": [{"id": 2, "title": "sfasdf"},
                            {"id": 1, "title": "wrter"},
                            {"id": 3, "title": "bxcvb"}],
        "acl_people": [{"email": "a@b.c", "name": "abc"},
                       {"email": "c@d.e", "name": "cde"},
                       {"email": "b@c.d", "name": "bcd"}],
    }]

    ordered_list = [{
        "id": 1,
        "related_sources": [{"id": 3, "title": "cxzvqw"},
                            {"id": 4, "title": "lkhtdgg"},
                            {"id": 7, "title": "qwedq"}],
        "acl_people": [{"email": "a@b.c", "name": "abc"},
                       {"email": "b@c.d", "name": "bcd"},
                       {"email": "c@d.e", "name": "cde"}],
    }, {
        "id": 2,
        "related_sources": [{"id": 1, "title": "wrter"},
                            {"id": 2, "title": "sfasdf"},
                            {"id": 3, "title": "bxcvb"}],
        "acl_people": [{"email": "a@b.c", "name": "abc"},
                       {"email": "b@c.d", "name": "bcd"},
                       {"email": "c@d.e", "name": "cde"}],
    }]

    with self.assertRaises(AssertionError):
      self.assertEqual(unordered_list, ordered_list)
    self.assertEqual(self._sort_sublists(unordered_list),
                     self._sort_sublists(ordered_list))
