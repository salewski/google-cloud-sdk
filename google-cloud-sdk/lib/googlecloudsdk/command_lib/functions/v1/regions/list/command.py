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

"""List regions available to Google Cloud Functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as api_exceptions
from apitools.base.py import list_pager

from googlecloudsdk.api_lib.functions.v1 import util
from googlecloudsdk.calliope import exceptions as base_exceptions
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties


def Run(args):
  """Lists regions available with the given args."""
  del args  # unused by list command
  client = util.GetApiClientInstance()
  list_generator = list_pager.YieldFromList(
      service=client.projects_locations,
      request=_BuildRequest(),
      field='locations',
      batch_size_attribute='pageSize')
  try:
    for item in list_generator:
      yield item
  except api_exceptions.HttpError as error:
    msg = util.GetHttpErrorMessage(error)
    exceptions.reraise(base_exceptions.HttpException(msg))


def _BuildRequest():
  messages = util.GetApiMessagesModule()
  project = properties.VALUES.core.project.GetOrFail()
  return messages.CloudfunctionsProjectsLocationsListRequest(
      name='projects/' + project)