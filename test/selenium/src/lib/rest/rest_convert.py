# Copyright (C) 2019 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Conversions from App entity to REST."""
from lib.app_entity import person_entity
from lib.constants import roles

_COMMON_ACCESS_CONTROL_ROLE_MAPPING = {
    "admins": roles.ADMINS
}


def build_access_control_list(obj, acr_mapping=None):
  """Builds access_control_list from obj.
  `acr_mapping` is a mapping between `app_entity`'s attributes and values of
  `name` column in `access_control_roles` DB table.
  """
  if acr_mapping:
    acr_mapping = acr_mapping.copy()
  else:
    acr_mapping = {}
  acr_mapping.update(_COMMON_ACCESS_CONTROL_ROLE_MAPPING)
  obj_type = obj.obj_type()
  access_control_list = []
  for attr_name, attr_value in obj.__dict__.iteritems():
    if attr_name in acr_mapping:
      acr_name = acr_mapping[attr_name]
      access_control_list.extend(_person_list_to_acl_entries(
          obj_type, acr_name, person_list=attr_value))
    else:
      _raise_if_value_is_person(attr_name, attr_value)
  return access_control_list


def _person_list_to_acl_entries(obj_type, acr_name, person_list):
  """Returns a list of ACL entries built from the list of `Person`s."""
  role_id = roles.ACLRolesIDs.id_of_role(
      object_type=obj_type, name=acr_name)
  return [{"ac_role_id": role_id, "person": to_basic_rest_obj(person)}
          for person in person_list]


def _raise_if_value_is_person(key, value):
  """Raises an error if value is a person or a list of people.
  The goal is to prevent possibility to add an ACL attribute to `app_entity`
  but to forget to add it to REST conversion code.
  """
  def is_person(maybe_person):
    """Returns whether the argument is a person."""
    return isinstance(maybe_person, person_entity.Person)

  def should_convert(maybe_whitelisted_key):
    """Returns whether the key should be considered a name of ACR."""
    return maybe_whitelisted_key != "modified_by"

  def is_list_of_people(maybe_list):
    """Returns whether the argument is a list."""
    is_list = isinstance(maybe_list, list)
    return is_list and maybe_list and all(is_person(item) for item in value)
  if (is_person(value) or is_list_of_people(value)) and should_convert(key):
    raise ValueError("Value with key `{}` is a person or a list of people but "
                     "is not present in ACR mapping.".format(key))


def to_basic_rest_obj(obj):
  """Return basic REST dict based on `obj`."""
  return {"type": obj.obj_type(), "id": obj.obj_id}


def default_context():
  """Returns default value for `context`."""
  return {"id": None}
