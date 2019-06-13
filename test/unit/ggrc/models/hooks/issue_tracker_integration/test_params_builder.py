# Copyright (C) 2019 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Test Issue tracker query builder."""

# pylint: disable=protected-access
# pylint: disable=invalid-name

import unittest

import ddt
import mock

from ggrc.models import exceptions
from ggrc.models.hooks.issue_tracker import integration_utils
from ggrc.integrations.constants import DEFAULT_ISSUETRACKER_VALUES
from ggrc.integrations import client
from ggrc.models.hooks.issue_tracker import issue_tracker_params_builder \
    as params_builder
from unit.ggrc.integrations import test_client


@ddt.ddt
class TestBaseIssueTrackerParamsBuilder(unittest.TestCase):
  """Test base class for issue tracker params builder."""

  def setUp(self):
    """Perform initialisation for each test cases."""
    self.builder = params_builder.BaseIssueTrackerParamsBuilder()

  @ddt.data(
      {"component_id": "not float number"},
      {"hotlist_id": "not float number"},
  )
  def test_handle_issue_tracker_info_for_failure(self, issue_tracker_info):
    """Test 'handle_issue_tracker_info' method for failure cases."""
    mock_object = mock.MagicMock()
    with self.assertRaises(exceptions.ValidationError):
      self.builder.handle_issue_tracker_info(mock_object, issue_tracker_info)

  def test_handle_issue_tracker_info(self):
    """Test 'handle_issue_tracker_info' method."""
    mock_object = mock.MagicMock()
    issue_tracker_info = {
        "component_id": "123",
        "hotlist_id": 321,
        "title": "test_title",
        "issue_type": "test_type",
        "issue_priority": "P2",
        "issue_severity": "S2",
    }
    expected_result = {
        "component_id": 123,
        "hotlist_ids": [321, ],
        "title": "test_title",
        "type": "test_type",
        "priority": "P2",
        "severity": "S2",
    }

    self.builder.handle_issue_tracker_info(mock_object, issue_tracker_info)

    self.assertEquals(
        self.builder.params.get_issue_tracker_params(),
        expected_result
    )

  def test_handle_issue_tracker_info_default_values(self):
    """Test handle_issue_tracker_info method set default values.

    If we created issue_tracker_issue with missed parameters, we should set
    this parameters with default values. Now we have default values for
    component_id, hotlist_id, issue_type, priority and severity.
    """
    mock_object = mock.MagicMock()
    issue_tracker_info = {
        "title": "test_title",
    }
    expected_result = {
        "component_id": DEFAULT_ISSUETRACKER_VALUES["issue_component_id"],
        "hotlist_ids": [DEFAULT_ISSUETRACKER_VALUES["issue_hotlist_id"], ],
        "title": "test_title",
        "type": DEFAULT_ISSUETRACKER_VALUES["issue_type"],
        "priority": DEFAULT_ISSUETRACKER_VALUES["issue_priority"],
        "severity": DEFAULT_ISSUETRACKER_VALUES["issue_severity"],
    }

    self.builder.handle_issue_tracker_info(mock_object, issue_tracker_info)

    self.assertEquals(
        self.builder.params.get_issue_tracker_params(),
        expected_result
    )

  def test_turning_off_integration(self):
    """Test turning off Issue tracker integration.

    No changes should be sent to issue tracker except comment.
    """
    # Arrange test data.
    current_issue_tracker_info = {
        "enabled": True,
        "component_id": "123",
        "hotlist_id": 321,
        "title": "test_title",
        "issue_type": "test_type",
        "issue_priority": "P2",
        "issue_severity": "S2",
    }

    new_issue_tracker_info = {
        "enabled": False,
        "component_id": "12345",
        "hotlist_id": 54321,
        "title": "new_test_title",
        "issue_type": "new_test_type",
        "issue_priority": "P3",
        "issue_severity": "S3",
    }

    expected_result = {
        "comment": u"Changes to this GGRC object will no longer be "
                   u"tracked within this bug."
    }

    # Perform action.
    self.builder._update_issue_tracker_info(
        new_issue_tracker_info,
        current_issue_tracker_info
    )

    # Assert results.
    self.assertEquals(
        self.builder.params.get_issue_tracker_params(),
        expected_result
    )


@ddt.ddt
class TestIssueQueryBuilder(unittest.TestCase):
  """Test issue tracker builder for iisue object."""

  def setUp(self):
    """Perform initialisation for each test cases."""
    self.builder = params_builder.IssueParamsBuilder()

  def test_handle_issue_attributes(self):
    """Test '_handle_issue_attributes' method."""
    # pylint: disable=protected-access
    # Arrange test data.
    mock_object = mock.MagicMock()
    mock_object.description = "<p>test_description</p>"
    mock_object.test_plan = "<p>test_plan</p>"
    expected_result = {
        "comment": "Following is the issue Description from GGRC: "
                   "test_description\n\n"
                   "Following is the issue Remediation Plan from GGRC: "
                   "test_plan"
    }

    # Perform action.
    self.builder._handle_issue_comment_attributes(mock_object)

    # Assert results.
    self.assertEquals(
        self.builder.params.get_issue_tracker_params(),
        expected_result
    )

  def test_handle_people_emails_without_ccs(self):
    """Test '_handle_people_emails' method without emails in ccs list."""
    mock_object = mock.MagicMock()
    mock_object.modified_by.email = "reporter_email"

    verifier = mock.MagicMock()
    verifier_acl = mock.MagicMock()
    verifier.name = "admin_name"
    verifier.email = "verifier_email"
    verifier_acl.ac_role.name = "Admins"

    assignee = mock.MagicMock()
    assignee_acl = mock.MagicMock()
    assignee.name = "assignee_name"
    assignee.email = "assignee_email"
    assignee_acl.ac_role.name = "Primary Contacts"

    access_control_list = [
        (verifier, verifier_acl),
        (assignee, assignee_acl),
    ]
    mock_object.access_control_list = access_control_list
    allowed_emails = {person.email for person, _ in access_control_list}

    expected_result = {
        "verifier": "verifier_email",
        "assignee": "assignee_email",
        "reporter": "reporter_email",
        "ccs": [],
    }

    # Perform action.
    self.builder._handle_people_emails(mock_object, allowed_emails)

    # Assert results.
    self.assertDictEqual(
        self.builder.params.get_issue_tracker_params(),
        expected_result
    )

  def test_handle_people_emails_with_ccs(self):
    """Test '_handle_people_emails' method with emails in ccs list."""
    # Arrange test data.
    mock_object = mock.MagicMock()
    mock_object.modified_by.email = "reporter_email"

    admin = mock.MagicMock()
    admin.ac_role.name = "Admins"
    primary_contact = mock.MagicMock()
    primary_contact.ac_role.name = "Primary Contacts"

    custom_role = mock.MagicMock()
    custom_role.ac_role.name = "Custom Role"

    verifier_1 = mock.MagicMock()
    verifier_1.name = "admin_name"
    verifier_1.email = "verifier_email_1"
    verifier_1.ac_role.name = "Admins"

    verifier_2 = mock.MagicMock()
    verifier_2.name = "verifier_name"
    verifier_2.email = "verifier_email_2"
    verifier_2.ac_role.name = "Admins"

    assignee_1 = mock.MagicMock()
    assignee_1.name = "assignee_name"
    assignee_1.email = "assignee_email_1"
    assignee_1.ac_role.name = "Primary Contacts"

    assignee_2 = mock.MagicMock()
    assignee_2.name = "primary_contact_name"
    assignee_2.email = "assignee_email_2"
    assignee_2.ac_role.name = "Primary Contacts"

    custom_role_1 = mock.MagicMock()
    custom_role_1.name = "reporter_name"
    custom_role_1.email = "reporter_email"
    custom_role_1.ac_role.name = "Custom Role"

    custom_role_2 = mock.MagicMock()
    custom_role_2.name = "custom_name"
    custom_role_2.email = "custom_email"
    custom_role_2.ac_role.name = "Custom Role"

    custom_role_3 = mock.MagicMock()
    custom_role_3.name = "admin_name"
    custom_role_3.email = "verifier_email_1"
    custom_role_3.ac_role.name = "Custom Role"

    access_control_list = [
        (verifier_1, admin),
        (verifier_2, admin),
        (assignee_1, primary_contact),
        (assignee_2, primary_contact),
        (custom_role_1, custom_role),
        (custom_role_2, custom_role),
        (custom_role_3, custom_role),
    ]
    allowed_emails = {person.email for person, _ in access_control_list}
    mock_object.access_control_list = access_control_list

    expected_result = {
        "verifier": "verifier_email_1",
        "assignee": "assignee_email_1",
        "reporter": "reporter_email",
        "ccs": ["custom_email", "verifier_email_2", "assignee_email_2"],
    }

    # Perform action.
    self.builder._handle_people_emails(mock_object, allowed_emails)

    # Assert results.
    self.assertDictEqual(
        self.builder.params.get_issue_tracker_params(),
        expected_result
    )

  def test_update_issue_comment_attributes(self):
    """Test '_update_issue_comment_attributes' method."""
    # Arrange test data.
    mock_current_object = mock.MagicMock()
    mock_current_object.description = "description"
    mock_current_object.test_plan = "test plan"

    mock_new_object = mock.MagicMock()
    mock_new_object.description = "new description"
    mock_new_object.test_plan = "new test plan"

    expected_result = {
        "comment": "Issue Description has been updated.\nnew description\n\n"
        "Issue Remediation Plan has been updated.\nnew test plan"
    }

    # Perform action.
    self.builder._update_issue_comment_attributes(mock_new_object,
                                                  mock_current_object)

    # Assert results.
    self.assertEquals(
        self.builder.params.get_issue_tracker_params(),
        expected_result
    )

  @mock.patch.object(params_builder.BaseIssueTrackerParamsBuilder,
                     "get_ggrc_object_url",
                     return_value="http://issue_url.com")
  def test_build_create_issue_tracker_params(self, url_builder_mock):
    """Test 'build_create_issue_tracker_params' method."""
    # Arrange test data.
    mock_object = mock.MagicMock()
    mock_object.modified_by.email = "reporter@email.com"
    mock_object.test_plan = "<p>test plan</p>"
    mock_object.description = "<p>description</p>"

    issue_tracker_info = {
        "enabled": True,
        "component_id": "1234",
        "hotlist_id": "4321",
        "issue_type": "PROCESS",
        "issue_priority": "P2",
        "issue_severity": "S2",
        "title": "Issue title",
    }
    expected_result = {
        "comment": "This bug was auto-generated to track a GGRC Issue. "
                   "Use the following link to find the Issue - "
                   "http://issue_url.com.\n\n"
                   "Following is the issue Description from GGRC: "
                   "description\n\n"
                   "Following is the issue Remediation Plan from GGRC: "
                   "test plan",
        "component_id": 1234,
        "hotlist_ids": [4321, ],
        "priority": "P2",
        "reporter": "reporter@email.com",
        "assignee": "",
        "verifier": "",
        "ccs": [],
        "severity": "S2",
        "status": "ASSIGNED",
        "title": "Issue title",
        "type": "PROCESS",
    }

    # Perform action.
    with mock.patch.object(
        integration_utils,
        "exclude_auditor_emails",
        return_value={"reporter@email.com", }
    ) as exclude_emails_mock:
      params = self.builder.build_create_issue_tracker_params(
          mock_object,
          issue_tracker_info
      )

    # Assert results.
    exclude_emails_mock.assert_called_with({"reporter@email.com", })
    url_builder_mock.assert_called_once()
    self.assertDictEqual(params.get_issue_tracker_params(), expected_result)

  def test_build_delete_params(self):
    """Test 'build_delete_params' method."""
    expected_result = {
        "comment": "GGRC object has been deleted. GGRC changes will "
                   "no longer be tracked within this bug."
    }
    self.builder.build_delete_issue_tracker_params()
    self.assertEquals(
        self.builder.params.get_issue_tracker_params(),
        expected_result
    )

  @ddt.data(400, 401, 403, 404, 405, 406, 500)
  @mock.patch('ggrc.integrations.client.urlfetch.fetch')
  def test_link_builder_catch_exception(self, error_code, fetch_mock):
    """Test builder catches client {} error exception"""
    obj = mock.MagicMock()
    fetch_mock.return_value = test_client.ObjectDict({
        'status_code': error_code,
        'content': '{"status": "content"}'
    })
    with mock.patch.multiple(client.BaseClient, ENDPOINT='endpoint'):
      with mock.patch.object(params_builder.IssueParamsBuilder,
                             "_build_allowed_emails",
                             return_value=[]):
        result = self.builder.build_params_for_issue_link(obj, 12, {})
    self.assertTrue(result.is_empty())
