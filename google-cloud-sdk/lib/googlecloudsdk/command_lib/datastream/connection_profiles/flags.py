# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Flags and helpers for the Datastream related commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def AddTypeFlag(parser):
  """Adds a --type flag to the given parser."""
  help_text = """Type can be MYSQL, ORACLE or GOOGLE-CLOUD-STORAGE"""

  parser.add_argument('--type', help=help_text, required=True)


def AddDisplayNameFlag(parser, required=True):
  """Adds a --display-name flag to the given parser."""
  help_text = """Friendly name for the connection profile."""
  parser.add_argument('--display-name', help=help_text, required=required)


def AddMysqlProfileGroup(parser, required=True):
  """Adds necessary mysql profile flags to the given parser."""
  mysql_profile = parser.add_group()
  mysql_profile.add_argument(
      '--mysql-hostname',
      help="""IP or hostname of the mysql source database.""",
      required=required)
  mysql_profile.add_argument(
      '--mysql-port',
      help="""Network port of the mysql source database.""",
      required=required,
      type=int)
  mysql_profile.add_argument(
      '--mysql-username',
      help="""Username Datastream will use to connect to the database.""",
      required=required)
  password_group = mysql_profile.add_group(required=required, mutex=True)
  password_group.add_argument(
      '--mysql-password',
      help="""\
          Password for the user that Datastream will be using to
          connect to the database.
          This field is not returned on request, and the value is encrypted
          when stored in Datastream.""")
  password_group.add_argument(
      '--mysql-prompt-for-password',
      action='store_true',
      help='Prompt for the password used to connect to the database.')
  ssl_config = mysql_profile.add_group()
  ssl_config.add_argument(
      '--ca-certificate',
      help="""\
          x509 PEM-encoded certificate of the CA that signed the source database
          server's certificate. The replica will use this certificate to verify
          it's connecting to the right host.""",
      required=required)
  ssl_config.add_argument(
      '--client-certificate',
      help="""\
          x509 PEM-encoded certificate that will be used by the replica to
          authenticate against the source database server.""",
      required=required)
  ssl_config.add_argument(
      '--client-key',
      help="""\
          Unencrypted PKCS#1 or PKCS#8 PEM-encoded private key associated with
          the Client Certificate.""",
      required=required)


def AddOracleProfileGroup(parser, required=True):
  """Adds necessary oracle profile flags to the given parser."""
  oracle_profile = parser.add_group()
  oracle_profile.add_argument(
      '--oracle-hostname',
      help="""IP or hostname of the oracle source database.""",
      required=required)
  oracle_profile.add_argument(
      '--oracle-port',
      help="""Network port of the oracle source database.""",
      required=required,
      type=int)
  oracle_profile.add_argument(
      '--oracle-username',
      help="""Username Datastream will use to connect to the database.""",
      required=required)
  oracle_profile.add_argument(
      '--database-service',
      help="""Database service for the Oracle connection.""",
      required=required)
  password_group = oracle_profile.add_group(required=required, mutex=True)
  password_group.add_argument(
      '--oracle-password',
      help="""\
          Password for the user that Datastream will be using to
          connect to the database.
          This field is not returned on request, and the value is encrypted
          when stored in Datastream.""")
  password_group.add_argument(
      '--oracle-prompt-for-password',
      action='store_true',
      help='Prompt for the password used to connect to the database.')


def AddGcsProfileGroup(parser, required=True):
  """Adds necessary GCS profile flags to the given parser."""
  gcs_profile = parser.add_group()
  gcs_profile.add_argument(
      '--bucket-name',
      help="""The full project and resource path for Cloud Storage
      bucket including the name.""",
      required=required)
  gcs_profile.add_argument(
      '--root-path',
      help="""The root path inside the Cloud Storage bucket.""",
      required=False)


def AddDepthGroup(parser):
  """Adds necessary depth flags for discover command parser."""
  depth_parser = parser.add_group(mutex=True)
  depth_parser.add_argument(
      '--recursive',
      action='store_true',
      help="""Whether to retrieve the full hierarchy of data objects (TRUE) or only the current level (FALSE)."""
  )
  depth_parser.add_argument(
      '--recursive-depth',
      help="""The number of hierarchy levels below the current level to be retrieved."""
  )


def AddRdbmsGroup(parser):
  """Adds necessary RDBMS params for discover command parser."""
  rdbms_parser = parser.add_group(mutex=True)
  rdbms_parser.add_argument(
      '--mysql-rdbms-file',
      help="""Path to a YAML (or JSON) file containing the MySQL RDBMS to enrich with child data objects and metadata. If you pass - as the value of the flag the file content will be read from stdin. """
  )
  rdbms_parser.add_argument(
      '--oracle-rdbms-file',
      help="""Path to a YAML (or JSON) file containing the ORACLE RDBMS to enrich with child data objects and metadata. If you pass - as the value of the flag the file content will be read from stdin."""
  )
