# Copyright (C) 2019 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Utils for filter operations."""
import itertools

from dateutil import parser

from lib.constants import value_aliases as alias
from lib.constants.element import AdminWidgetCustomAttributes
from lib.entities.entity import Representation
from lib.utils.string_utils import StringMethods


class FilterUtils(object):
  """Class for work with filter utils."""

  @classmethod
  def _get_filter_exp(cls, criteria, grouping_operator=alias.OR_OP):
    """Get filter expression for single and multiple criteria used grouping
    operator. Grouping operator can be "OR" or "AND".
    """
    def get_exp(criterion):
      """Get one filter expression according to criterion.
      Example:
      criterion = ("field", "=", "value")
      :return '"field" = "value"'
      """
      field, operator, value = criterion
      return u'"{}" {} "{}"'.format(field, operator, value)
    return u" {} ".format(grouping_operator).join(
        get_exp(criterion) for criterion in criteria)

  @staticmethod
  def get_filter_exp(field, operator, list_values):
    """Get filter expression to search data by title according to field, operator
    and list of values.
    Example:
    field = "field"
    operator = "="
    list_values = ["value1", "value2"]
    :return '"field" = "value1" OR "field" = "value2"'
    """
    return FilterUtils._get_filter_exp(
        [(field, operator, value) for value in list_values])

  @staticmethod
  def get_filter_exp_by_title(titles):
    """Get filter expression to search data by title according to title(s).
    Example:
    for single title
    titles = "title1"
    :return '"title" = "title1"'

    for list of titles
    titles = ["title1", "title2"]
    :return '"title" = "title1" OR "title" = "title2"'
    """
    list_values = [titles] if type(titles) not in [list, tuple] else titles
    return FilterUtils.get_filter_exp(field="title",
                                      operator=alias.EQUAL_OP,
                                      list_values=list_values)

  def get_filter_exprs_by_ca(self, cad, cav, operator):
    """Return all possible filter expressions for CA according to CA type"""
    ca_type = cad.attribute_type
    if ca_type == AdminWidgetCustomAttributes.CHECKBOX:
      value = alias.YES_VAL if StringMethods.get_bool_value_from_arg(
          cav.attribute_value) else alias.NO_VAL
      values_to_filter = StringMethods.get_list_of_all_cases(value)
    elif ca_type == AdminWidgetCustomAttributes.PERSON:
      from lib.service import rest_service
      person = rest_service.ObjectsInfoService().get_obj(
          obj=Representation.repr_dict_to_obj(cav.attribute_object))
      values_to_filter = [person.name, person.email]
    elif ca_type == AdminWidgetCustomAttributes.DATE:
      date_formats = ["%m/%d/%Y", "%m/%Y", "%Y-%m-%d", "%Y-%m", "%Y"]
      date = parser.parse(cav.attribute_value).date()
      values_to_filter = [date.strftime(_format) for _format in date_formats]
    elif ca_type == AdminWidgetCustomAttributes.RICH_TEXT:
      if operator == alias.EQUAL_OP:
        values_to_filter = ['<p>' + cav.attribute_value + '</p>']
      else:
        values_to_filter = [cav.attribute_value]
    else:
      values_to_filter = [cav.attribute_value]
    return [self.get_filter_exp(cad.title, operator, [val])
            for val in values_to_filter]

  def get_filter_exprs_by_cavs(self, cads, cavs, operator):
    """Return all possible filters expressions for passed Custom Attributes
    Definitions and CAs values.
    """
    return list(itertools.chain.from_iterable(
        self.get_filter_exprs_by_ca(cad, cav, operator=operator)
        for cad in cads
        for cav in cavs
        if cav.custom_attribute_id == cad.id))
