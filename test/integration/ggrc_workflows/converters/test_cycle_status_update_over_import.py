# Copyright (C) 2019 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Test on Cycle Task status update over import."""

import datetime
from collections import OrderedDict

import mock
import ddt

from ggrc import db
from ggrc.models import all_models
from ggrc.converters import errors

from integration import ggrc as ggrc_test
from integration.ggrc_workflows.models import factories
from integration.ggrc.models import factories as ggrc_factories


@ddt.ddt
class TestCycleTaskStatusUpdate(ggrc_test.TestCase):
  """Test cases for update status on import cycle tasks"""

  @classmethod
  def setUpClass(cls):
    """Setup special hooks to that test class."""
    cls._current_user_wfo_or_assignee = (
        all_models.CycleTaskGroupObjectTask.current_user_wfa_or_assignee
    )
    all_models.CycleTaskGroupObjectTask.current_user_wfa_or_assignee = (
        mock.MagicMock(return_value=True))

  @classmethod
  def tearDownClass(cls):
    all_models.CycleTaskGroupObjectTask.current_user_wfa_or_assignee = (
        cls._current_user_wfo_or_assignee
    )

  DEFAULT_TASK_STATUSES = [all_models.CycleTaskGroupObjectTask.ASSIGNED] * 3

  ALIAS = "Cycle Task"

  def setUp(self):
    with ggrc_factories.single_commit():
      self.workflow = factories.WorkflowFactory(
          status=all_models.Workflow.ACTIVE
      )
      self.cycle = factories.CycleFactory(workflow=self.workflow)
      self.group = factories.CycleTaskGroupFactory(
          cycle=self.cycle,
          context=self.cycle.workflow.context
      )
      self.tasks = []
      for ind, task_status in enumerate(self.DEFAULT_TASK_STATUSES):
        self.tasks.append(factories.CycleTaskGroupObjectTaskFactory(
            title='task{}'.format(ind),
            cycle=self.cycle,
            cycle_task_group=self.group,
            context=self.cycle.workflow.context,
            status=task_status,
        ))
    # Emulate that current user is assignee for all test CycleTasks.
    self.task_ids = [t.id for t in self.tasks]

  VERIFIED_STRUCTURE = {
      "task_statuses": [all_models.CycleTaskGroupObjectTask.VERIFIED] * 3,
      "group_status": all_models.CycleTaskGroup.VERIFIED,
      "cycle_status": all_models.Cycle.VERIFIED,
      "workflow_status": all_models.Workflow.INACTIVE,
  }
  ASSIGNED_STRUCTURE = {
      "task_statuses": [all_models.CycleTaskGroupObjectTask.ASSIGNED] * 3,
      "group_status": all_models.CycleTaskGroup.IN_PROGRESS,
      "cycle_status": all_models.Cycle.IN_PROGRESS,
      "workflow_status": all_models.Workflow.ACTIVE
  }
  IN_PROGRESS_STRUCTURE = {
      "task_statuses": [all_models.CycleTaskGroupObjectTask.IN_PROGRESS] * 3,
      "group_status": all_models.CycleTaskGroup.IN_PROGRESS,
      "cycle_status": all_models.Cycle.IN_PROGRESS,
      "workflow_status": all_models.Workflow.ACTIVE
  }
  DECLINED_STRUCTURE = {
      "task_statuses": [all_models.CycleTaskGroupObjectTask.DECLINED] * 3,
      "group_status": all_models.CycleTaskGroup.IN_PROGRESS,
      "cycle_status": all_models.Cycle.IN_PROGRESS,
      "workflow_status": all_models.Workflow.ACTIVE,
  }
  FINISHED_STRUCTURE = {
      "task_statuses": [all_models.CycleTaskGroupObjectTask.FINISHED] * 3,
      "group_status": all_models.CycleTaskGroup.FINISHED,
      "cycle_status": all_models.Cycle.FINISHED,
      "workflow_status": all_models.Workflow.ACTIVE,
  }

  def _update_structure(self, structure=None):
    """Update structure of setuped objects."""
    if not structure:
      return
    structure = structure or {}
    start_statuses = structure.get("task_statuses") or []
    if start_statuses:
      for idx, status in enumerate(start_statuses):
        self.tasks[idx].status = status
    self.group.status = structure.get("group_status", self.group.status)
    self.cycle.status = structure.get("cycle_status", self.cycle.status)
    self.cycle.is_verification_needed = structure.get(
        "cycle_is_verification_needed",
        self.cycle.is_verification_needed)
    self.workflow.status = structure.get("workflow_status",
                                         self.workflow.status)
    db.session.commit()

  def _get_start_tasks_statuses(self, start_structure=None):
    start_statuses = (start_structure or {}).get("task_statuses", [])
    return (start_statuses + self.DEFAULT_TASK_STATUSES)[:3]

  def build_import_data(self, task_statuses):
    return [OrderedDict([("object_type", self.ALIAS),
                         ("Code*", self.tasks[idx].slug),
                         ("Task State", status)])
            for idx, status in enumerate(task_statuses)]

  @ddt.unpack
  @ddt.data(
      {"update_structure": VERIFIED_STRUCTURE},
      {"update_structure": IN_PROGRESS_STRUCTURE},
      {"update_structure": FINISHED_STRUCTURE},
      # verified few tasks
      {"update_structure": {
          "task_statuses": [all_models.CycleTaskGroupObjectTask.VERIFIED] * 2,
          "group_status": all_models.CycleTaskGroup.IN_PROGRESS,
          "cycle_status": all_models.Cycle.IN_PROGRESS,
          "workflow_status": all_models.Workflow.ACTIVE,
      }},
      {"update_structure": DECLINED_STRUCTURE},
      {"update_structure": VERIFIED_STRUCTURE,
       "start_structure": IN_PROGRESS_STRUCTURE},
      {"update_structure": IN_PROGRESS_STRUCTURE,
       "start_structure": VERIFIED_STRUCTURE},
      {"update_structure": DECLINED_STRUCTURE,
       "start_structure": IN_PROGRESS_STRUCTURE},
      {"update_structure": IN_PROGRESS_STRUCTURE,
       "start_structure": DECLINED_STRUCTURE},
  )
  def test_update_status(self, update_structure, start_structure=None):
    """Simple update task status to {update_structure[task_statuses]}"""
    self._update_structure(start_structure)
    start_statuses = self._get_start_tasks_statuses(start_structure)
    task_count = len(all_models.CycleTaskGroupObjectTask.query.all())
    self.assertEqual(start_statuses, [t.status for t in self.tasks])
    task_statuses = update_structure["task_statuses"]
    group_status = update_structure["group_status"]
    cycle_status = update_structure["cycle_status"]
    workflow_status = update_structure["workflow_status"]
    response = self.import_data(*self.build_import_data(task_statuses))
    self._check_csv_response(response, {})
    self.tasks = all_models.CycleTaskGroupObjectTask.query.filter(
        all_models.CycleTaskGroupObjectTask.id.in_(self.task_ids)
    ).all()
    self.assertEqual(task_statuses + start_statuses[len(task_statuses):],
                     [t.status for t in self.tasks])
    group = self.tasks[0].cycle_task_group
    self.assertEqual(group_status, group.status)
    self.assertEqual(len(all_models.CycleTaskGroupObjectTask.query.all()),
                     task_count)
    self.assertEqual(cycle_status, group.cycle.status)
    self.assertEqual(workflow_status, group.cycle.workflow.status)

  @ddt.data(ASSIGNED_STRUCTURE,
            IN_PROGRESS_STRUCTURE,
            DECLINED_STRUCTURE)
  def test_update_to_verified(self, start_structure):
    """Update task status to verified from {0[task_statuses]} and back"""
    self._update_structure(start_structure)
    start_statuses = self._get_start_tasks_statuses(start_structure)
    self.assertEqual(start_statuses, [t.status for t in self.tasks])
    self.assertEqual([None] * len(self.tasks),
                     [t.finished_date for t in self.tasks])
    self.assertEqual([None] * len(self.tasks),
                     [t.verified_date for t in self.tasks])
    task_statuses = self.VERIFIED_STRUCTURE["task_statuses"]
    response = self.import_data(*self.build_import_data(task_statuses))
    self._check_csv_response(response, {})
    self.tasks = all_models.CycleTaskGroupObjectTask.query.filter(
        all_models.CycleTaskGroupObjectTask.id.in_(self.task_ids)
    ).all()
    self.assertEqual(task_statuses + start_statuses[len(task_statuses):],
                     [t.status for t in self.tasks])
    finished_dates = [t.finished_date for t in self.tasks]
    self.assertNotEqual([None] * len(self.tasks), finished_dates)
    verified_dates = [t.verified_date for t in self.tasks]
    self.assertNotEqual([None] * len(self.tasks), verified_dates)
    self.assertFalse(self.tasks[0].cycle.is_current)

  @ddt.data(1, 2, 3)
  def test_finished_to_verified(self, number_of_tasks):
    """Update {0} tasks status from finished from verified and back"""
    finished_date = datetime.date.today()
    start_statuses = self._get_start_tasks_statuses(self.FINISHED_STRUCTURE)
    with ggrc_factories.single_commit():
      for task in self.tasks:
        task.finished_date = finished_date
    self._update_structure(self.FINISHED_STRUCTURE)
    self.tasks = all_models.CycleTaskGroupObjectTask.query.filter(
        all_models.CycleTaskGroupObjectTask.id.in_(self.task_ids)
    ).all()
    self.assertEqual([finished_date] * len(self.tasks),
                     [t.finished_date for t in self.tasks])
    self.assertEqual([None] * len(self.tasks),
                     [t.verified_date for t in self.tasks])
    task_statuses = [
        all_models.CycleTaskGroupObjectTask.VERIFIED
    ] * number_of_tasks
    response = self.import_data(*self.build_import_data(task_statuses))
    self._check_csv_response(response, {})
    self.tasks = all_models.CycleTaskGroupObjectTask.query.filter(
        all_models.CycleTaskGroupObjectTask.id.in_(self.task_ids)
    ).all()
    self.assertEqual(task_statuses + start_statuses[len(task_statuses):],
                     [t.status for t in self.tasks])
    self.assertEqual([finished_date] * len(self.tasks),
                     [t.finished_date for t in self.tasks])
    verified_dates = [t.verified_date for t in self.tasks][:number_of_tasks]
    self.assertNotEqual([None] * number_of_tasks, verified_dates)
    verified_dates += [t.verified_date for t in self.tasks][number_of_tasks:]
    self.assertEqual(
        [None] * (len(self.tasks) - number_of_tasks),
        [t.verified_date for t in self.tasks][number_of_tasks:])
    self.assertEqual(len(self.tasks) != number_of_tasks,
                     self.tasks[0].cycle.is_current)

  @staticmethod
  def __build_error_tmpl(error_tmpl, **context):
    """Create simple temaplte from base error tmpl."""
    if "line" not in context:
      context["line"] = "{}"
    return error_tmpl.format(**context)

  def __build_status_error_resp(self, key, error_tmpl, exception_statuses):
    """Return expected response dict based on sent arguments."""
    error_tmpl = self.__build_error_tmpl(error_tmpl,
                                         column_name="Task State",
                                         message="Invalid state '{}'")
    return {
        self.ALIAS: {
            key: {error_tmpl.format(3 + idx, status)
                  for idx, status in enumerate(exception_statuses)},
        }
    }

  def __assert_error_message(self,
                             sending_data,
                             expected_messages,
                             start_structure=None):
    """Assert validation error message on import cycle task statuses."""
    start_statuses = self._get_start_tasks_statuses(start_structure)

    group_status = self.group.status
    cycle_status = self.cycle.status
    workflow_status = self.workflow.status
    self.assertEqual(start_statuses, [t.status for t in self.tasks])
    response = self.import_data(*sending_data)
    self._check_csv_response(response, expected_messages)
    self.tasks = all_models.CycleTaskGroupObjectTask.query.filter(
        all_models.CycleTaskGroupObjectTask.id.in_(self.task_ids)
    ).all()
    group = self.tasks[0].cycle_task_group
    self.assertEqual(start_statuses, [t.status for t in self.tasks])
    self.assertEqual(group_status, group.status)
    self.assertEqual(cycle_status, group.cycle.status)
    self.assertEqual(workflow_status, group.cycle.workflow.status)

  @ddt.data(
      VERIFIED_STRUCTURE["task_statuses"],
      DECLINED_STRUCTURE["task_statuses"],
  )
  def test_validation_error(self, exception_statuses):
    """Validation cycle task status update to {0} if no verification needed."""
    self._update_structure({"cycle_is_verification_needed": False})
    error_msgs = self.__build_status_error_resp("row_errors",
                                                errors.VALIDATION_ERROR,
                                                exception_statuses)
    send_data = self.build_import_data(exception_statuses)
    self.__assert_error_message(send_data, error_msgs)

  @ddt.unpack
  @ddt.data(
      {"start_structure": IN_PROGRESS_STRUCTURE,
       "exception_statuses": ["Absolutely Wrong Status"] * 3},
      {"start_structure": IN_PROGRESS_STRUCTURE,
       "exception_statuses": [""] * 3},
      {"exception_statuses": [""] * 3},
      {"exception_statuses": ["Absolutely Wrong Status"] * 3},
      {"start_structure": FINISHED_STRUCTURE,
       "exception_statuses": ["Absolutely Wrong Status"] * 3},
      {"start_structure": FINISHED_STRUCTURE,
       "exception_statuses": [""] * 3},
  )
  def test_simple_send_invalid_status(self,
                                      exception_statuses,
                                      start_structure=None):
    """Validation cycle task status update to {exception_statuses}."""
    self._update_structure(start_structure)
    warn_msgs = self.__build_status_error_resp("row_warnings",
                                               errors.WRONG_VALUE_CURRENT,
                                               exception_statuses)
    send_data = self.build_import_data(exception_statuses)
    self.__assert_error_message(send_data,
                                warn_msgs,
                                start_structure=start_structure)

  @ddt.data(
      ("Task Start Date", "Task Due Date"),
  )
  def test_for_date_compare_error(self, columns):
    """Validate task import data where {0[0]} bigger than {0[1]}."""
    self._update_structure(self.VERIFIED_STRUCTURE)
    today = datetime.date.today()
    dates = (today, today - datetime.timedelta(7))
    error_tmpl = self.__build_error_tmpl(errors.INVALID_START_END_DATES,
                                         start_date=columns[0],
                                         end_date=columns[1])
    # line format
    error_resp = {self.ALIAS: {"row_errors": {error_tmpl.format(3)}}}
    data_to_import = OrderedDict([("object_type", self.ALIAS),
                                  ("Code*", self.tasks[0].slug)])
    for column, date in zip(columns, dates):
      data_to_import[column] = date
    response = self.import_data(data_to_import)
    self._check_csv_response(response, error_resp)
