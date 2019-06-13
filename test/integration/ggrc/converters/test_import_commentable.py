# Copyright (C) 2019 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

# pylint: disable=maybe-no-member, invalid-name

"""Test import of commentable fields."""

from collections import OrderedDict
import ddt

from ggrc.models import all_models
from integration.ggrc import TestCase


@ddt.ddt
class TestImportCommentable(TestCase):
  """Class with tests of importing fields of Commentable mixin."""

  @ddt.data(
      all_models.Objective,
      all_models.Requirement,
      all_models.Regulation,
      all_models.Policy,
      all_models.Standard,
      all_models.Threat,
      all_models.Contract,
  )
  def test_model_import(self, model):
    """Test import commentable model {}."""
    recipients = model.VALID_RECIPIENTS
    model_name = model.__name__
    import_data = [
        ("object_type", model_name),
        ("Code", "{}-2".format(model_name)),
        ("Title", "{}-Title".format(model_name)),
        ("Admins", "user@example.com"),
        ("Recipients", ','.join(recipients)),
        ("Send by default", True),
    ]
    response = self.import_data(OrderedDict(import_data))
    self._check_csv_response(response, {})
    obj = model.query.first()
    self.assertEqual(obj.send_by_default, True)
    self.assertEqual(sorted(obj.recipients.split(",")), sorted(recipients))

  def test_program_import(self):
    """Test import of program recipients."""
    recipients = all_models.Program.VALID_RECIPIENTS
    model_name = "Program"
    import_data = [
        ("object_type", model_name),
        ("Code", "{}-2".format(model_name)),
        ("Title", "{}-Title".format(model_name)),
        ("Program Managers", "user@example.com"),
        ("Recipients", ','.join(recipients)),
        ("Send by default", True),
    ]
    response = self.import_data(OrderedDict(import_data))
    self._check_csv_response(response, {})
    obj = all_models.Program.query.first()
    self.assertEqual(obj.send_by_default, True)
    self.assertEqual(sorted(obj.recipients.split(",")), sorted(recipients))

  @ddt.data(*all_models.get_scope_models())
  def test_scoping_import(self, model):
    """Test import scoping commentable object {}."""
    recipients = model.VALID_RECIPIENTS
    model_name = model.__name__
    import_data = [
        ("object_type", model_name),
        ("Code", "{}-1".format(model_name)),
        ("Title", "{}-Title".format(model_name)),
        ("Admins", "user@example.com"),
        ("Recipients", ','.join(recipients)),
        ("Send by default", True),
        ("Assignee", "user@example.com"),
        ("Verifier", "user@example.com"),
    ]
    response = self.import_data(OrderedDict(import_data))
    self._check_csv_response(response, {})
    obj = model.query.first()
    self.assertEqual(sorted(obj.recipients.split(",")), sorted(recipients))
    self.assertEqual(obj.send_by_default, True)
