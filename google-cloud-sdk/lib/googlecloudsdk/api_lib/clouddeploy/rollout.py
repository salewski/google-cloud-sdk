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
"""Support library to handle the rollout subcommands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.clouddeploy import client_util
from googlecloudsdk.command_lib.deploy import deploy_util
from googlecloudsdk.core import log


class RolloutClient(object):
  """Client for release service in the Cloud Deploy API."""

  def __init__(self, client=None, messages=None):
    """Initialize a release.ReleaseClient.

    Args:
      client: base_api.BaseApiClient, the client class for Cloud Deploy.
      messages: module containing the definitions of messages for Cloud Deploy.
    """
    self.client = client or client_util.GetClientInstance()
    self.messages = messages or client_util.GetMessagesModule(client)
    self._service = self.client.projects_locations_deliveryPipelines_releases_rollouts

  def Approve(self, name, approved):
    """Calls the approve API to approve or reject a rollout..

    Args:
      name: Name of the Rollout. Format is
        projects/{project}/locations/{location}/deliveryPipelines/{deliveryPipeline}/releases/{release}/rollouts/{rollout}.
      approved: True = approve; False = reject

    Returns:
      ApproveRolloutResponse message.
    """
    request = self.messages.ClouddeployProjectsLocationsDeliveryPipelinesReleasesRolloutsApproveRequest(
        name=name,
        approveRolloutRequest=self.messages.ApproveRolloutRequest(
            approved=approved))
    return self._service.Approve(request)

  def Get(self, name):
    """Gets a rollout resource.

    Args:
      name: rollout resource name.

    Returns:
      rollout message.
    """
    request = self.messages.ClouddeployProjectsLocationsDeliveryPipelinesReleasesRolloutsGetRequest(
        name=name)
    return self._service.Get(request)

  def List(self, release_name, filter_str=None):
    """Lists rollout resources that belongs to a release.

    Args:
      release_name: str, name of the release.
      filter_str: optional[str], list filter.

    Returns:
      Rollout list response.
    """
    request = self.messages.ClouddeployProjectsLocationsDeliveryPipelinesReleasesRolloutsListRequest(
        parent=release_name, filter=filter_str)
    return self._service.List(request)

  def Create(self, rollout_ref, rollout_obj, annotations=None, labels=None):
    """Creates a rollout resource.

    Args:
      rollout_ref: protorpc.messages.Message, rollout resource object.
      rollout_obj: apitools.base.protorpclite.messages.Message, rollout message.
      annotations: dict[str,str], a dict of annotation (key,value) pairs that
        allow clients to store small amounts of arbitrary data in cloud deploy
        resources.
      labels: dict[str,str], a dict of label (key,value) pairs that can be used
        to select cloud deploy resources and to find collections of cloud deploy
        resources that satisfy certain conditions.

    Returns:
      The operation message.
    """
    log.debug('Creating rollout: %r', rollout_obj)
    deploy_util.SetMetadata(self.messages, rollout_obj,
                            deploy_util.ResourceType.ROLLOUT, annotations,
                            labels)
    request = self.messages.ClouddeployProjectsLocationsDeliveryPipelinesReleasesRolloutsCreateRequest(
        parent=rollout_ref.Parent().RelativeName(),
        rollout=rollout_obj,
        rolloutId=rollout_ref.Name())

    return self._service.Create(request)
