# -*- coding: utf-8 -*-

# Copyright (C) 2019 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Comprehensive import tests.

These tests should eventually contain all good imports and imports with all
possible errors and warnings.
"""

import collections
import ddt

from ggrc import db
from ggrc.models import Program, Audit
from ggrc.converters import errors
from ggrc_basic_permissions import Role
from ggrc_basic_permissions import UserRole
from integration.ggrc import TestCase
from integration.ggrc.generator import ObjectGenerator


@ddt.ddt
class TestComprehensiveSheets(TestCase):

  """
  test sheet from:
    https://docs.google.com/spreadsheets/d/1Jg8jum2eQfvR3kZNVYbVKizWIGZXvfqv3yQpo2rIiD8/edit#gid=0

  """

  def setUp(self):
    super(TestComprehensiveSheets, self).setUp()
    self.generator = ObjectGenerator()
    self.client.get("/login")

  def test_comprehensive_with_ca(self):
    """Test comprehensive sheet with custom attributes."""
    self.create_custom_attributes()
    response = self.import_file("comprehensive_sheet1.csv", safe=False)
    indexed = {r["name"]: r for r in response}

    expected = {
        "Objective": {
            "created": 8,
            "ignored": 7,
            "row_errors": 7,
            "row_warnings": 4,
            "rows": 15,
        },
        "Program": {
            "created": 13,
            "ignored": 3,
            "row_errors": 3,
            "row_warnings": 4,
            "rows": 16,
        },
        "Policy": {
            "created": 13,
            "ignored": 3,
            "row_errors": 3,
            "row_warnings": 4,
            "rows": 16,
        },
        "Regulation": {
            "created": 13,
            "ignored": 2,
            "row_errors": 2,
            "row_warnings": 3,
            "rows": 15,
        },
        "Standard": {
            "created": 14,
            "ignored": 2,
            "row_errors": 2,
            "row_warnings": 4,
            "rows": 16,
        },
        "Contract": {
            "created": 14,
            "ignored": 2,
            "row_errors": 2,
            "row_warnings": 4,
            "rows": 16,
        },
        "System": {
            "created": 14,
            "ignored": 2,
            "row_errors": 2,
            "row_warnings": 4,
            "rows": 16,
        },
        "Requirement": {
            "created": 14,
            "ignored": 2,
            "row_errors": 2,
            "row_warnings": 4,
            "rows": 16,
        },
        "Process": {
            "created": 14,
            "ignored": 2,
            "row_errors": 2,
            "row_warnings": 4,
            "rows": 16,
        },
        "Data Asset": {
            "created": 14,
            "ignored": 2,
            "row_errors": 2,
            "row_warnings": 4,
            "rows": 16,
        },
        "Product": {
            "created": 14,
            "ignored": 2,
            "row_errors": 2,
            "row_warnings": 4,
            "rows": 16,
        },
        "Project": {
            "created": 13,
            "ignored": 2,
            "row_errors": 2,
            "row_warnings": 7,
            "rows": 15,
        },
        "Facility": {
            "created": 14,
            "ignored": 2,
            "row_errors": 2,
            "row_warnings": 4,
            "rows": 16,
        },
        "Market": {
            "created": 13,
            "ignored": 2,
            "row_errors": 2,
            "row_warnings": 3,
            "rows": 15,
        },
        "Org Group": {
            "created": 13,
            "ignored": 2,
            "row_errors": 2,
            "row_warnings": 3,
            "rows": 15,
        },
        "Vendor": {
            "created": 13,
            "ignored": 2,
            "row_errors": 2,
            "row_warnings": 3,
            "rows": 15,
        },
        "Person": {
            "created": 13,
            "ignored": 1,
            "row_errors": 1,
            "row_warnings": 0,
            "rows": 14,
        },
        "Metric": {
            "created": 14,
            "ignored": 2,
            "row_errors": 2,
            "row_warnings": 4,
            "rows": 16,
        },
        "Technology Environment": {
            "created": 14,
            "ignored": 2,
            "row_errors": 2,
            "row_warnings": 4,
            "rows": 16,
        },
        "Product Group": {
            "created": 14,
            "ignored": 2,
            "row_errors": 2,
            "row_warnings": 4,
            "rows": 16,
        },
    }

    # general numbers check
    for name, data in expected.items():
      current = indexed[name]

      current_dict = {
          "created": current["created"],
          "ignored": current["ignored"],
          "row_errors": len(current["row_errors"]),
          "row_warnings": len(current["row_warnings"]),
          "rows": current["rows"],
      }

      self.assertDictEqual(
          current_dict,
          data,
          u"Numbers don't match for {}: expected {!r}, got {!r}".format(
              name,
              data,
              current_dict,
          ),
      )

    prog = Program.query.filter_by(title="program 8").first()
    self.assertEqual(prog.status, "Draft")
    self.assertEqual(prog.description, "test")

    custom_vals = [v.attribute_value for v in prog.custom_attribute_values]
    expected_custom_vals = ['0', 'a', '2015-12-12', 'test1']
    self.assertEqual(set(custom_vals), set(expected_custom_vals))

  def test_full_good_import(self):
    """Test import of all objects with no warnings or errors."""
    filename = "full_good_import_no_warnings.csv"
    response = self.import_file(filename)
    self._check_csv_response(response, {})

    admin = db.session.query(Role.id).filter(Role.name == "Administrator")
    reader = db.session.query(Role.id).filter(Role.name == "Reader")
    creator = db.session.query(Role.id).filter(Role.name == "Creator")
    admins = UserRole.query.filter(UserRole.role_id == admin).all()
    readers = UserRole.query.filter(UserRole.role_id == reader).all()
    creators = UserRole.query.filter(UserRole.role_id == creator).all()
    self.assertEqual(len(admins), 12)
    self.assertEqual(len(readers), 5)
    self.assertEqual(len(creators), 6)

    audit_data = collections.OrderedDict([
        ("object_type", "Audit"),
        ("Code*", ""),
        ("State", "Planned"),
        ("Audit Captains", "user1@ggrc.com"),
        ("Auditors", "user2@ggrc.com"),

    ])

    assessment_data = collections.OrderedDict([
        ("object_type", "Assessment"),
        ("Code*", ""),
        ("Assignees", "user1@ggrc.com"),
        ("Creators", "user1@ggrc.com"),
        ("Verifiers", "user1@ggrc.com"),
    ])

    for i in range(1, 11):
      program = db.session.query(Program).filter_by(
          title="program {}".format(i)).first()
      audit_data["Title"] = "Audit - {}".format(i)
      audit_data["Program"] = program.slug
      response = self.import_data(audit_data)
      self._check_csv_response(response, {})
      audit = db.session.query(Audit).filter_by(
          title="Audit - {}".format(i)).first()
      assessment_data["Title"] = "Assessment - {}".format(i)
      assessment_data["Audit*"] = audit.slug
      response = self.import_data(assessment_data)
      self._check_csv_response(response, {})

  @ddt.data(
      (
          [
              collections.OrderedDict([
                  ("object_type", "Program"),
                  ("Code*", ""),
                  ("Program managers", "user@example.com"),
                  ("Title", "P1"),
                  ("map:Program", ""),
                  ("Effective Date", "7_1_2015"),
                  ("Last Deprecated Date", "2015-7-15"),
              ]),
              collections.OrderedDict([
                  ("object_type", "Program"),
                  ("Code*", ""),
                  ("Program managers", ""),
                  ("Title", "P2"),
                  ("Effective Date", "55/55/2015"),
                  ("Last Deprecated Date", "2015-7-15"),
              ])
          ],
          {
              "Program": {
                  "block_warnings": {
                      errors.UNSUPPORTED_MAPPING.format(
                          line=2,
                          obj_a="Program",
                          obj_b="Program",
                          column_name="map:program"
                      ),
                  },
                  "row_warnings": {
                      errors.OWNER_MISSING.format(
                          line=7, column_name="Program Managers"),
                      errors.EXPORT_ONLY_WARNING.format(
                          line=3, column_name="Last Deprecated Date"),
                      errors.EXPORT_ONLY_WARNING.format(
                          line=7, column_name="Last Deprecated Date"),
                  },
                  "row_errors": {
                      errors.UNKNOWN_DATE_FORMAT.format(
                          line=3, column_name="Effective Date"),
                      errors.WRONG_VALUE_ERROR.format(
                          line=7, column_name="Effective Date"),
                  },
              },
          }
      ),
      (
          [
              collections.OrderedDict([
                  ("object_type", "Assessment"),
                  ("Code*", ""),
                  ("Audit", ""),
                  ("Assignees", "user@example.com"),
                  ("Creators", "user@example.com"),
                  ("Title", "Asmt1"),
              ]),
              collections.OrderedDict([
                  ("object_type", "Assessment"),
                  ("Code*", ""),
                  ("Audit", "x"),
                  ("Assignees", "user@example.com"),
                  ("Creators", "user@example.com"),
                  ("Title", "Asmt2"),
              ])
          ],
          {
              "Assessment": {
                  "row_warnings": {
                      errors.UNKNOWN_OBJECT.format(
                          line=4, object_type="Audit", slug="x"),
                  },
                  "row_errors": {
                      errors.MISSING_VALUE_ERROR.format(
                          line=3, column_name="Audit"),
                      errors.MISSING_VALUE_ERROR.format(
                          line=4, column_name="Audit"),
                  },
              },
          }
      ),
      (
          [
              collections.OrderedDict([
                  ("object_type", "Regulation"),
                  ("Code*", ""),
                  ("Admin*", "user@example.com"),
                  ("Title", "R1"),
                  ("Reference URL", "double-url.com\n"
                                    "www.foo-bar\ndouble-url.com"),
                  ("New Column", "some value"),
              ]),
              collections.OrderedDict([
                  ("object_type", "Regulation"),
                  ("Code*", ""),
                  ("Admin*", "user@example.com"),
                  ("Title", "R1"),
              ])
          ],
          {
              "Regulation": {
                  "row_warnings": {
                      errors.DUPLICATE_IN_MULTI_VALUE.format(
                          line=3,
                          column_name=u"Reference URL",
                          duplicates=u"double-url.com"
                      )
                  },
                  "row_errors": {
                      errors.DUPLICATE_VALUE_IN_CSV.format(
                          line=7, column_name="Title",
                          value="R1", processed_line=3),
                  },
                  "block_warnings": {
                      errors.UNKNOWN_COLUMN.format(
                          line=2, column_name="new column"),
                  }
              }
          }
      ),
      (
          [
              collections.OrderedDict([
                  ("object_type", "Risk"),
                  ("Code*", ""),
                  ("Admin", "user@example.com"),
                  ("Title", "R1"),
                  ("Effective Date", "7/1/2015"),
                  ("Last Deprecated Date", "7/15/2015"),
              ]),
          ],
          {
              "Risk": {
                  "row_errors": {
                      errors.EXTERNAL_MODEL_IMPORT_RESTRICTION.format(
                          line=3,
                          external_model_name="Risk"
                      ),
                  },
                  "row_warnings": {
                      errors.EXPORT_ONLY_WARNING.format(
                          line=3, column_name="Last Deprecated Date"),
                  }
              }
          }
      ),
  )
  @ddt.unpack
  def test_errors_and_warnings(self, object_data, expected_errors):
    """Tests errors and warnings with the following objects:

    * Program
    * Assessment
    * Regulation
    * Risk
    """

    response = self.import_data(*object_data)
    self._check_csv_response(response, expected_errors)

  def create_custom_attributes(self):
    """Generate custom attributes needed for comprehensive sheet."""
    gen = self.generator.generate_custom_attribute
    gen("risk", title="my custom text", mandatory=True)
    gen("program", title="my_text", mandatory=True)
    gen("program", title="my_date", attribute_type="Date")
    gen("program", title="my_checkbox", attribute_type="Checkbox")
    gen("program", title="my_dropdown", attribute_type="Dropdown",
        options="a,b,c,d")
    gen("program", title="my_multiselect", attribute_type="Multiselect",
        options="yes,no")
    # gen("program", title="my_description", attribute_type="Rich Text")

  def test_case_sensitive_slugs(self):
    """Test that mapping with case sensitive slugs work."""
    programs_data = [
        collections.OrderedDict([
            ("object_type", "Program"),
            ("Code*", ""),
            ("Program managers", "user@example.com"),
            ("Title", "SOME TITLE"),
        ]),
        collections.OrderedDict([
            ("object_type", "Program"),
            ("Code*", ""),
            ("Program managers", "user@example.com"),
            ("Title", "some title"),
        ])
    ]
    response = self.import_data(*programs_data)
    expected_errors = {
        "Program": {
            "row_errors": {
                errors.DUPLICATE_VALUE_IN_CSV.format(
                    line="4",
                    processed_line="3",
                    column_name="Title",
                    value="some title",
                ),
            }
        }
    }
    self._check_csv_response(response, expected_errors)
