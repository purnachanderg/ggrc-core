# Copyright (C) 2019 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from sqlalchemy import and_
from sqlalchemy import or_

from ggrc.models import Policy
from ggrc.models import OrgGroup
from ggrc.models import Product
from ggrc.models import Relationship
from ggrc.converters import errors
from integration.ggrc import TestCase
from integration.ggrc.generator import ObjectGenerator


class TestCsvImport(TestCase):

  def setUp(self):
    super(TestCsvImport, self).setUp()
    self.generator = ObjectGenerator()
    self.client.get("/login")

  def tearDown(self):
    pass

  def generate_people(self, people):
    for person in people:
      self.generator.generate_person({
          "name": person,
          "email": "{}@reciprocitylabs.com".format(person),
      }, "Administrator")

  def test_multi_basic_policy_orggroup_product(self):
    filename = "multi_basic_policy_orggroup_product.csv"
    response_json = self.import_file(filename)

    object_counts = {
        "Org Group": (4, 0, 0),
        "Policy": (4, 0, 0),
        "Product": (5, 0, 0),
    }

    for row in response_json:
      created, updated, ignored = object_counts[row["name"]]
      self.assertEqual(created, row["created"])
      self.assertEqual(updated, row["updated"])
      self.assertEqual(ignored, row["ignored"])
      self.assertEqual(set(), set(row["row_warnings"]))

    self.assertEqual(Policy.query.count(), 4)
    self.assertEqual(OrgGroup.query.count(), 4)
    self.assertEqual(Product.query.count(), 5)

  def test_multi_basic_policy_orggroup_product_with_warnings(self):
    """Test multi basic policy orggroup product with warnings"""
    filename = "multi_basic_policy_orggroup_product_with_warnings.csv"
    response_json = self.import_file(filename, safe=False)

    row_messages = []
    object_counts = {
        "Policy": (3, 0, 2),
        "Org Group": (0, 0, 4),
        "Product": (5, 0, 2),
    }
    for row in response_json:
      created, updated, ignored = object_counts[row["name"]]
      self.assertEqual(created, row["created"])
      self.assertEqual(updated, row["updated"])
      self.assertEqual(ignored, row["ignored"])
      row_messages.extend(row["row_warnings"])
      row_messages.extend(row["row_errors"])

    expected_warnings = set([
        errors.DUPLICATE_VALUE_IN_CSV.format(
            line="6", processed_line="5", column_name="Title", value="dolor",
        ),
        errors.DUPLICATE_VALUE_IN_CSV.format(
            line="7", processed_line="6", column_name="Code", value="p-4",
        ),
        errors.DUPLICATE_VALUE_IN_CSV.format(
            line="26", processed_line="21", column_name="Title",
            value="meatloaf",
        ),
        errors.DUPLICATE_VALUE_IN_CSV.format(
            line="26", processed_line="21", column_name="Code", value="pro 1",
        ),
        errors.DUPLICATE_VALUE_IN_CSV.format(
            line="27", processed_line="21", column_name="Code", value="pro 1",
        ),
        errors.OWNER_MISSING.format(line=26, column_name="Admins"),
        errors.MISSING_COLUMN.format(line=13, column_names="Admins", s=""),
        errors.MISSING_COLUMN.format(line=14, column_names="Admins", s=""),
        errors.MISSING_COLUMN.format(line=15, column_names="Admins", s=""),
        errors.MISSING_COLUMN.format(line=16, column_names="Admins", s=""),
    ])

    self.assertEqual(expected_warnings, set(row_messages))
    self.assertEqual(Policy.query.count(), 3)
    self.assertEqual(OrgGroup.query.count(), 0)
    self.assertEqual(Product.query.count(), 5)

  def test_multi_basic_policy_orggroup_product_with_mappings(self):

    def get_relationships_for(obj):
      return Relationship.query.filter(or_(
          and_(Relationship.source_id == obj.id,
               Relationship.source_type == obj.type),
          and_(Relationship.destination_id == obj.id,
               Relationship.destination_type == obj.type),
      ))

    filename = "multi_basic_policy_orggroup_product_with_mappings.csv"
    response_json = self.import_file(filename)

    object_counts = {
        "Policy": (4, 0, 0),
        "Org Group": (4, 0, 0),
        "Product": (5, 0, 0),
    }
    for row in response_json:
      created, updated, ignored = object_counts[row["name"]]
      self.assertEqual(created, row["created"])
      self.assertEqual(updated, row["updated"])
      self.assertEqual(ignored, row["ignored"])
      self.assertEqual(set(), set(row["row_warnings"]))

    self.assertEqual(Policy.query.count(), 4)
    self.assertEqual(OrgGroup.query.count(), 4)
    self.assertEqual(Product.query.count(), 5)
    p1 = Policy.query.filter_by(slug="p-1").first()
    org1 = OrgGroup.query.filter_by(slug="org-1").first()

    self.assertEqual(get_relationships_for(p1).count(), 3)
    self.assertEqual(get_relationships_for(org1).count(), 5)
