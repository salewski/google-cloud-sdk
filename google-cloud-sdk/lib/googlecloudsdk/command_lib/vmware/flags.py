# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Flags for data-catalog commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


def AddPrivatecloudArgToParser(parser, positional=False):
  """Sets up an argument for the privatecloud resource."""
  name = '--privatecloud'
  if positional:
    name = 'privatecloud'
  privatecloud_data = yaml_data.ResourceYAMLData.FromPath('vmware.privatecloud')
  resource_spec = concepts.ResourceSpec.FromYaml(privatecloud_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help='privatecloud.'
      )
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddOperationArgToParser(parser):
  """Sets up an argument for the operation resource."""
  operation_data = yaml_data.ResourceYAMLData.FromPath('vmware.operation')
  resource_spec = concepts.ResourceSpec.FromYaml(operation_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name='operation',
      concept_spec=resource_spec,
      required=True,
      group_help='operation.'
      )
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddClusterArgToParser(parser, positional=False):
  """Sets up an argument for the cluster resource."""
  if positional:
    name = 'cluster'
  else:
    name = '--cluster'
  cluster_data = yaml_data.ResourceYAMLData.FromPath('vmware.cluster')
  resource_spec = concepts.ResourceSpec.FromYaml(cluster_data.GetData())
  flag_name_overrides = {'location': '', 'privatecloud': ''}

  if positional:
    flag_name_overrides = None
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help='cluster.',
      flag_name_overrides=flag_name_overrides
      )
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddLocationArgToParser(parser, positional=False):
  """Parses location flag."""
  location_data = yaml_data.ResourceYAMLData.FromPath('vmware.location')
  resource_spec = concepts.ResourceSpec.FromYaml(location_data.GetData())
  name = '--location'
  if positional:
    name = 'location'
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help='location.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddNodeTypeArgToParser(parser, positional=False):
  """Parses node type flag."""

  if positional:
    name = 'nodetype'
    flag_name_overrides = None
  else:
    name = '--node-type'
    flag_name_overrides = {'location': ''}

  location_data = yaml_data.ResourceYAMLData.FromPath('vmware.nodetype')
  resource_spec = concepts.ResourceSpec.FromYaml(location_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help='nodetype.',
      flag_name_overrides=flag_name_overrides)
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddProjectArgToParser(parser, positional=False):
  """Parses project flag."""
  name = '--project'
  if positional:
    name = 'project'

  project_data = yaml_data.ResourceYAMLData.FromPath('vmware.project')
  resource_spec = concepts.ResourceSpec.FromYaml(project_data.GetData())

  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help='project.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddLabelsToMessage(labels, message):
  """Parses labels into a specific message."""

  # set up for call to ParseCreateArgs, which expects labels as an
  # attribute on an object.
  class LabelHolder(object):

    def __init__(self, labels):
      self.labels = labels

  message.labels = labels_util.ParseCreateArgs(
      LabelHolder(labels),
      type(message).LabelsValue)

