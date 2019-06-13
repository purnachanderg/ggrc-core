# Copyright (C) 2019 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Pluralize admin role

Create Date: 2019-05-31 07:48:12.359629
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

import datetime
import re

from alembic import op
import sqlalchemy as sa

from ggrc.models import all_models
from ggrc.migrations.utils.acr_propagation import propagate_roles
from ggrc.migrations.utils.acr_propagation import remove_propagated_roles
from ggrc.migrations.utils import migrator


# revision identifiers, used by Alembic.
revision = '350d0894b526'
down_revision = '10b40b26d571'


OBJECT_TYPES = (
    "AccountBalance",
    "AccessGroup",
    "Contract",
    "Control",
    "DataAsset",
    "Facility",
    "Issue",
    "KeyReport",
    "Market",
    "Metric",
    "Objective",
    "OrgGroup",
    "Policy",
    "Process",
    "Product",
    "ProductGroup",
    "Project",
    "Regulation",
    "Requirement",
    "Risk",
    "Standard",
    "System",
    "TechnologyEnvironment",
    "Threat",
    "Vendor",
    "Workflow",
)

OLD_ROLE_NAME = "Admin"
NEW_ROLE_NAME = "Admins"

COMMENT_R = {}
REVIEW_RU = {}
PROPOSAL_RU = {}
EXTERNAL_COMMENT_R = {}
DOCUMENT_RU = {
    "Relationship R": {
        "Comment R": COMMENT_R,
    },
}
DOCUMENT_EXTERNALCOMMENT_RU = {
    "Relationship R": {
        "Comment R": COMMENT_R,
        "ExternalComment R": EXTERNAL_COMMENT_R,
    },
}

COMMENT_DOCUMENT_RUD = {
    "Relationship R": {
        "Comment R": COMMENT_R,
        "Document RU": DOCUMENT_RU,
    },
}

COMMENT_DOCUMENT_REVIEW_RUD = {
    "Relationship R": {
        "Comment R": COMMENT_R,
        "Document RU": DOCUMENT_RU,
        "Review RU": REVIEW_RU,
    },
}

COMMENT_DOCUMENT_PROPOSAL_REVIEW_RUD = {
    "Relationship R": {
        "Comment R": COMMENT_R,
        "Document RU": DOCUMENT_RU,
        "Proposal RU": PROPOSAL_RU,
        "Review RU": REVIEW_RU,
    },
}

COMMENT_DOCUMENT_EXTERNALCOMMENT_PROPOSAL_REVIEW_RUD = {
    "Relationship R": {
        "Comment R": COMMENT_R,
        "Document RU": DOCUMENT_EXTERNALCOMMENT_RU,
        "ExternalComment R": EXTERNAL_COMMENT_R,
        "Proposal RU": PROPOSAL_RU,
        "Review RU": REVIEW_RU,
    },
}

CYCLE_CTG_CTGT_COMMENT_RUD = {
    "Relationship RUD": {
        "Cycle RUD": {
            "Relationship RUD": {
                "CycleTaskGroup RUD": {
                    "Relationship RUD": {
                        "CycleTaskGroupObjectTask RUD": {
                            "Relationship RUD": {
                                "Comment RUD": {
                                },
                            },
                        },
                    },
                },
            },
        },
        "TaskGroup RUD": {
            "Relationship RUD": {
                "TaskGroupTask RUD": {
                },
            },
        },
    },
}

ADMINS_PERMISSIONS = {
    "AccountBalance": {
        "Admins": COMMENT_DOCUMENT_RUD
    },
    "AccessGroup": {
        "Admins": COMMENT_DOCUMENT_RUD
    },
    "Contract": {
        "Admins": COMMENT_DOCUMENT_REVIEW_RUD
    },
    "Control": {
        "Admins": COMMENT_DOCUMENT_EXTERNALCOMMENT_PROPOSAL_REVIEW_RUD
    },
    "DataAsset": {
        "Admins": COMMENT_DOCUMENT_RUD
    },
    "Facility": {
        "Admins": COMMENT_DOCUMENT_RUD
    },
    "Issue": {
        "Admins": COMMENT_DOCUMENT_RUD
    },
    "KeyReport": {
        "Admins": COMMENT_DOCUMENT_RUD
    },
    "Market": {
        "Admins": COMMENT_DOCUMENT_RUD
    },
    "Metric": {
        "Admins": COMMENT_DOCUMENT_RUD
    },
    "Objective": {
        "Admins": COMMENT_DOCUMENT_REVIEW_RUD
    },
    "OrgGroup": {
        "Admins": COMMENT_DOCUMENT_RUD
    },
    "Policy": {
        "Admins": COMMENT_DOCUMENT_REVIEW_RUD
    },
    "Process": {
        "Admins": COMMENT_DOCUMENT_RUD
    },
    "Product": {
        "Admins": COMMENT_DOCUMENT_RUD
    },
    "ProductGroup": {
        "Admins": COMMENT_DOCUMENT_RUD
    },
    "Project": {
        "Admins": COMMENT_DOCUMENT_RUD
    },
    "Regulation": {
        "Admins": COMMENT_DOCUMENT_REVIEW_RUD
    },
    "Requirement": {
        "Admins": COMMENT_DOCUMENT_REVIEW_RUD
    },
    "Risk": {
        "Admins": COMMENT_DOCUMENT_PROPOSAL_REVIEW_RUD
    },
    "Standard": {
        "Admins": COMMENT_DOCUMENT_REVIEW_RUD
    },
    "System": {
        "Admins": COMMENT_DOCUMENT_RUD
    },
    "TechnologyEnvironment": {
        "Admins": COMMENT_DOCUMENT_RUD
    },
    "Threat": {
        "Admins": COMMENT_DOCUMENT_REVIEW_RUD
    },
    "Vendor": {
        "Admins": COMMENT_DOCUMENT_RUD
    },
    "Workflow": {
        "Admins": CYCLE_CTG_CTGT_COMMENT_RUD
    },
}


def update_role_names(connection, migrator_id):
  """Updates role names for objects defined in OBJECT_TYPES. """
  roles_table = all_models.AccessControlRole.__table__

  for object_type in OBJECT_TYPES:
    connection.execute(
        roles_table.update().where(
            roles_table.c.object_type == object_type
        ).where(
            roles_table.c.name == OLD_ROLE_NAME
        ).values(name=NEW_ROLE_NAME,
                 updated_at=datetime.datetime.utcnow(),
                 modified_by_id=migrator_id)
    )


def remove_old_propagated_roles():
  """Removes existing propagated roles of Admin"""
  for object_type in OBJECT_TYPES:
    remove_propagated_roles(object_type, ["Admins"])


def update_document_recipients(connection, migrator_id):
  """Replaces 'Admin', found in recipients column of documents table,
     with 'Admins'.
  """
  documents_table = all_models.Document.__table__
  pattern = re.compile(r'Admin')

  documents = connection.execute(
      documents_table.select().where(
          documents_table.c.recipients.ilike("%Admin%")
      )
  ).fetchall()

  document_recipients = [(document.id, document.recipients)
                         for document in documents]

  for document_id, recipients in document_recipients:
    modified_recipients = pattern.sub("Admins", recipients)
    connection.execute(documents_table.update()
                       .where(documents_table.c.id == document_id)
                       .values(recipients=modified_recipients,
                               modified_by=migrator_id)
                       )


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  connection = op.get_bind()
  migrator_id = migrator.get_migration_user_id(connection)
  op.alter_column('documents', 'recipients',
                  existing_type=sa.String(), server_default='Admins')
  update_document_recipients(connection, migrator_id)
  update_role_names(connection, migrator_id)
  remove_old_propagated_roles()
  propagate_roles(ADMINS_PERMISSIONS, with_update=True)


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  raise NotImplementedError("Downgrade is not supported")
