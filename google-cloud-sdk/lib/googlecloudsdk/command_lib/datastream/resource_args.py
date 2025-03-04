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
"""Shared resource flags for Datastream commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


def ConnectionProfileAttributeConfig(name='connection_profile'):
  return concepts.ResourceParameterAttributeConfig(
      name=name,
      help_text='The connection profile of the {resource}.',
      completion_request_params={'fieldMask': 'name'},
      completion_id_field='id')


def PrivateConnectionAttributeConfig(name='private_connection'):
  return concepts.ResourceParameterAttributeConfig(
      name=name,
      help_text='The private connection of the {resource}.',
      completion_request_params={'fieldMask': 'name'},
      completion_id_field='id')


def StreamAttributeConfig(name='stream'):
  return concepts.ResourceParameterAttributeConfig(
      name=name,
      help_text='The stream of the {resource}.',
      completion_request_params={'fieldMask': 'name'},
      completion_id_field='id')


def RouteAttributeConfig(name='route'):
  return concepts.ResourceParameterAttributeConfig(
      name=name,
      help_text='The route of the {resource}.',
      completion_request_params={'fieldMask': 'name'},
      completion_id_field='id')


def LocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='location', help_text='The Cloud location for the {resource}.')


def GetLocationResourceSpec(resource_name='location'):
  return concepts.ResourceSpec(
      'datastream.projects.locations',
      resource_name=resource_name,
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def GetConnectionProfileResourceSpec(resource_name='connection_profile'):
  return concepts.ResourceSpec(
      'datastream.projects.locations.connectionProfiles',
      resource_name=resource_name,
      connectionProfilesId=ConnectionProfileAttributeConfig(name=resource_name),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def GetPrivateConnectionResourceSpec(resource_name='private_connection'):
  return concepts.ResourceSpec(
      'datastream.projects.locations.privateConnections',
      resource_name=resource_name,
      privateConnectionsId=PrivateConnectionAttributeConfig(name=resource_name),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def GetStreamResourceSpec(resource_name='stream'):
  return concepts.ResourceSpec(
      'datastream.projects.locations.streams',
      resource_name=resource_name,
      streamsId=StreamAttributeConfig(name=resource_name),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def GetRouteResourceSpec(resource_name='route'):
  return concepts.ResourceSpec(
      'datastream.projects.locations.privateConnections.routes',
      resource_name=resource_name,
      routesId=RouteAttributeConfig(name=resource_name),
      privateConnectionsId=PrivateConnectionAttributeConfig(
          'private-connection'),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def AddConnectionProfileResourceArg(parser,
                                    verb,
                                    positional=True,
                                    required=True):
  """Add a resource argument for a Datastream connection profile.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, if True, means that the resource is a positional rather
      than a flag.
    required: bool, if True, means that a flag is required.
  """
  if positional:
    name = 'connection_profile'
  else:
    name = '--connection-profile'

  connectivity_parser = parser.add_group(mutex=True)
  connectivity_parser.add_argument(
      '--static-ip-connectivity',
      action='store_true',
      help="""use static ip connectivity""")
  connectivity_parser.add_argument(
      '--no-connectivity', action='store_true', help="""no connectivity""")
  forward_ssh_parser = connectivity_parser.add_group()
  forward_ssh_parser.add_argument(
      '--forward-ssh-hostname',
      help="""Hostname for the SSH tunnel.""",
      required=required)
  forward_ssh_parser.add_argument(
      '--forward-ssh-username',
      help="""Username for the SSH tunnel.""",
      required=required)
  forward_ssh_parser.add_argument(
      '--forward-ssh-port',
      help="""Port for the SSH tunnel, default value is 22.\
      """,
      default=22)
  password_group = forward_ssh_parser.add_group(required=required, mutex=True)
  password_group.add_argument(
      '--forward-ssh-password', help="""\
          SSH password.
          """)
  password_group.add_argument(
      '--forward-ssh-private-key', help='SSH private key..')

  resource_specs = [
      presentation_specs.ResourcePresentationSpec(
          name,
          GetConnectionProfileResourceSpec(),
          'The connection profile {}.'.format(verb),
          required=True),
      presentation_specs.ResourcePresentationSpec(
          '--private-connection-name',
          GetPrivateConnectionResourceSpec(),
          'Resource ID of the private connection.',
          flag_name_overrides={'location': ''},
          group=connectivity_parser)
  ]
  concept_parsers.ConceptParser(
      resource_specs,
      command_level_fallthroughs={
          '--private-connection-name.location': ['--location'],
      }).AddToParser(parser)


def AddConnectionProfileDiscoverResourceArg(parser):
  """Add a resource argument for a Datastream connection profile discover command.

  Args:
    parser: the parser for the command.
  """
  connection_profile_parser = parser.add_group(mutex=True, required=True)
  connection_profile_parser.add_argument(
      '--connection-profile-object-file',
      help="""Path to a YAML (or JSON) file containing the configuration
      for a connection profile object. If you pass - as the value of the
      flag the file content will be read from stdin."""
  )

  resource_specs = [
      presentation_specs.ResourcePresentationSpec(
          '--connection-profile-name',
          GetConnectionProfileResourceSpec(),
          'Resource ID of the connection profile.',
          flag_name_overrides={'location': ''},
          group=connection_profile_parser)
  ]
  concept_parsers.ConceptParser(
      resource_specs,
      command_level_fallthroughs={
          '--connection-profile-name.location': ['--location'],
      }).AddToParser(parser)


def GetVpcResourceSpec():
  """Constructs and returns the Resource specification for VPC."""

  def VpcAttributeConfig():
    return concepts.ResourceParameterAttributeConfig(
        name='vpc',
        help_text="""fully qualified name of the VPC Datastream will peer to."""
    )

  return concepts.ResourceSpec(
      'compute.networks',
      resource_name='vpc',
      network=VpcAttributeConfig(),
      project=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def AddPrivateConnectionResourceArg(parser, verb, positional=True):
  """Add a resource argument for a Datastream private connection.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, if True, means that the resource is a positional rather
      than a flag.
  """
  if positional:
    name = 'private_connection'
  else:
    name = '--private-connection'

  vpc_peering_config_parser = parser.add_group(required=True)

  vpc_peering_config_parser.add_argument(
      '--subnet',
      help="""A free subnet for peering. (CIDR of /29).""",
      required=True)

  resource_specs = [
      presentation_specs.ResourcePresentationSpec(
          name,
          GetPrivateConnectionResourceSpec(),
          'The private connection {}.'.format(verb),
          required=True),
      presentation_specs.ResourcePresentationSpec(
          '--vpc-name',
          GetVpcResourceSpec(),
          'Resource ID of the private connection.',
          group=vpc_peering_config_parser, required=True)
  ]
  concept_parsers.ConceptParser(
      resource_specs).AddToParser(parser)


def AddStreamResourceArg(parser, verb, required=True):
  """Add resource arguments for creating/updating a stream.

  Args:
    parser: argparse.ArgumentParser, the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    required: bool, if True, means that a flag is required.
  """
  source_parser = parser.add_group(required=required)
  source_config_parser_group = source_parser.add_group(
      required=required, mutex=True)
  source_config_parser_group.add_argument(
      '--oracle-source-config',
      help="""\
          Path to a YAML (or JSON) file containing the configuration for Oracle Source Config.

          The JSON file is formatted as follows, with snake_case field naming:

          ```
            {
              "allowlist": {},
              "rejectlist": {
                "oracle_schemas": [
                  {
                    "schema_name": "SAMPLE",
                    "oracle_tables": [
                      {
                        "table_name": "SAMPLE_TABLE",
                        "oracle_columns": [
                          {
                            "column_name": "COL",
                          }
                        ]
                      }
                    ]
                  }
                ]
              }
            }
          ```
       """
      )
  source_config_parser_group.add_argument(
      '--mysql-source-config',
      help="""\
          Path to a YAML (or JSON) file containing the configuration for Mysql Source Config.

          The JSON file is formatted as follows, with snake_case field naming:

          ```
            {
              "allowlist": {},
              "rejectlist":  {
                "mysql_databases": [
                    {
                      "database_name":"sample_database",
                      "mysql_tables": [
                        {
                          "table_name": "sample_table",
                          "mysql_columns": [
                            {
                              "column_name": "sample_column",
                            }
                           ]
                        }
                      ]
                    }
                  ]
                }
            }
          ```
       """
      )

  destination_parser = parser.add_group(required=required)
  destination_config_parser_group = destination_parser.add_group(
      required=required, mutex=True)
  destination_config_parser_group.add_argument(
      '--gcs-destination-config',
      help="""\
      Path to a YAML (or JSON) file containing the configuration for Google Cloud Storage Destination Config.

      The JSON file is formatted as follows:

      ```
       {
       "path": "some/path",
       "file_rotation_mb":5,
       "file_rotation_interval":"15s",
       "avro_file_format": {}
       }
      ```
        """)

  resource_specs = [
      presentation_specs.ResourcePresentationSpec(
          'stream',
          GetStreamResourceSpec(),
          'The stream {}.'.format(verb),
          required=True
      ),
      presentation_specs.ResourcePresentationSpec(
          '--source-name',
          GetConnectionProfileResourceSpec(),
          'Resource ID of the source connection profile.',
          required=required,
          flag_name_overrides={'location': ''},
          group=source_parser
      ),
      presentation_specs.ResourcePresentationSpec(
          '--destination-name',
          GetConnectionProfileResourceSpec(),
          'Resource ID of the destination connection profile.',
          required=required,
          flag_name_overrides={'location': ''},
          group=destination_parser
      )
  ]
  concept_parsers.ConceptParser(
      resource_specs,
      command_level_fallthroughs={
          '--source-name.location': ['--location'],
          '--destination-name.location': ['--location']
      }).AddToParser(parser)


def AddRouteResourceArg(parser, verb, positional=True):
  """Add a resource argument for a Datastream route.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to create'.
    positional: bool, if True, means that the resource is a positional rather
      than a flag.
  """
  if positional:
    name = 'route'
  else:
    name = '--route'

  resource_specs = [
      presentation_specs.ResourcePresentationSpec(
          name,
          GetRouteResourceSpec(),
          'The route {}.'.format(verb),
          required=True)
  ]
  concept_parsers.ConceptParser(
      resource_specs).AddToParser(parser)

