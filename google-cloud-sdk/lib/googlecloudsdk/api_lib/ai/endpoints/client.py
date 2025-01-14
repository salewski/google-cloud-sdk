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
"""Utilities for dealing with AI Platform endpoints API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import extra_types
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.ai.models import client as model_client
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import errors
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.credentials import http
from googlecloudsdk.core.credentials import requests
from six.moves import http_client


def _ParseModel(model_id, location_id):
  """Parses a model ID into a model resource object."""
  return resources.REGISTRY.Parse(
      model_id,
      params={
          'locationsId': location_id,
          'projectsId': properties.VALUES.core.project.GetOrFail
      },
      collection='aiplatform.projects.locations.models')


def _ConvertPyListToMessageList(message_type, values):
  return [encoding.PyValueToMessage(message_type, v) for v in values]


def _GetModelDeploymentResourceType(model_ref, client):
  """Gets the deployment resource type of a model.

  Each model resource belongs to exactly one supported deployment resource type.
  The value is the first item in the list, the length of which must be one.

  Args:
    model_ref: a model resource object.
    client: an apis.GetClientInstance object.

  Returns:
    A string which value must be 'DEDICATED_RESOURCES' or 'AUTOMATIC_RESOURCES'.

  Raises:
    ArgumentError: if the model resource object is not found.
  """
  try:
    model_msg = model_client.ModelsClient(client=client).Get(model_ref)
  except apitools_exceptions.HttpError:
    raise errors.ArgumentError(
        ('There is an error while getting the model information. '
         'Please make sure the model %r exists.' % model_ref.RelativeName()))
  model_resource = encoding.MessageToPyValue(model_msg)
  return model_resource['supportedDeploymentResourcesTypes'][0]


def _DoHttpPost(url, headers, body):
  """Makes an http POST request."""
  if base.UseRequests():
    response = requests.GetSession().request(
        'POST', url, data=body, headers=headers)
    return getattr(response, 'status_code'), getattr(response,
                                                     'headers'), getattr(
                                                         response, 'content')
  else:
    response, response_body = http.Http().request(
        uri=url, method='POST', body=body, headers=headers)
    return int(response.get('status')), response, response_body


class EndpointsClient(object):
  """High-level client for the AI Platform endpoints surface."""

  def __init__(self, client=None, messages=None, version=None):
    self.client = client or apis.GetClientInstance(
        constants.AI_PLATFORM_API_NAME,
        constants.AI_PLATFORM_API_VERSION[version])
    self.messages = messages or self.client.MESSAGES_MODULE

  def Create(self, location_ref, display_name, labels, description=None):
    """Creates a new endpoint using v1 API.

    Args:
      location_ref: Resource, the parsed location to create an endpoint.
      display_name: str, the display name of the new endpoint.
      labels: list, the labels to organize the new endpoint.
      description: str or None, the description of the new endpoint.

    Returns:
      A long-running operation for Create.
    """
    req = self.messages.AiplatformProjectsLocationsEndpointsCreateRequest(
        parent=location_ref.RelativeName(),
        googleCloudAiplatformV1Endpoint=self.messages
        .GoogleCloudAiplatformV1Endpoint(
            displayName=display_name, description=description, labels=labels))
    return self.client.projects_locations_endpoints.Create(req)

  def CreateBeta(self,
                 location_ref,
                 display_name,
                 labels,
                 description=None,
                 network=None):
    """Creates a new endpoint using v1beta1 API.

    Args:
      location_ref: Resource, the parsed location to create an endpoint.
      display_name: str, the display name of the new endpoint.
      labels: list, the labels to organize the new endpoint.
      description: str or None, the description of the new endpoint.
      network: str, the full name of the Google Compute Engine network.

    Returns:
      A long-running operation for Create.
    """
    req = self.messages.AiplatformProjectsLocationsEndpointsCreateRequest(
        parent=location_ref.RelativeName(),
        googleCloudAiplatformV1beta1Endpoint=self.messages
        .GoogleCloudAiplatformV1beta1Endpoint(
            displayName=display_name,
            description=description,
            labels=labels,
            network=network))
    return self.client.projects_locations_endpoints.Create(req)

  def Delete(self, endpoint_ref):
    """Deletes an existing endpoint."""
    req = self.messages.AiplatformProjectsLocationsEndpointsDeleteRequest(
        name=endpoint_ref.RelativeName())
    return self.client.projects_locations_endpoints.Delete(req)

  def Get(self, endpoint_ref):
    """Gets details about an endpoint."""
    req = self.messages.AiplatformProjectsLocationsEndpointsGetRequest(
        name=endpoint_ref.RelativeName())
    return self.client.projects_locations_endpoints.Get(req)

  def List(self, location_ref):
    """Lists endpoints in the project."""
    req = self.messages.AiplatformProjectsLocationsEndpointsListRequest(
        parent=location_ref.RelativeName())
    return list_pager.YieldFromList(
        self.client.projects_locations_endpoints,
        req,
        field='endpoints',
        batch_size_attribute='pageSize')

  def Patch(self,
            endpoint_ref,
            labels_update,
            display_name=None,
            description=None,
            traffic_split=None,
            clear_traffic_split=False):
    """Updates an endpoint using v1 API.

    Args:
      endpoint_ref: Resource, the parsed endpoint to be updated.
      labels_update: UpdateResult, the result of applying the label diff
        constructed from args.
      display_name: str or None, the new display name of the endpoint.
      description: str or None, the new description of the endpoint.
      traffic_split: dict or None, the new traffic split of the endpoint.
      clear_traffic_split: bool, whether or not clear traffic split of the
        endpoint.

    Returns:
      The response message of Patch.

    Raises:
      NoFieldsSpecifiedError: An error if no updates requested.
    """
    endpoint = self.messages.GoogleCloudAiplatformV1Endpoint()
    update_mask = []

    if labels_update.needs_update:
      endpoint.labels = labels_update.labels
      update_mask.append('labels')

    if display_name is not None:
      endpoint.displayName = display_name
      update_mask.append('display_name')

    if traffic_split is not None:
      additional_properties = []
      for key, value in sorted(traffic_split.items()):
        additional_properties.append(
            endpoint.TrafficSplitValue().AdditionalProperty(
                key=key, value=value))
      endpoint.trafficSplit = endpoint.TrafficSplitValue(
          additionalProperties=additional_properties)
      update_mask.append('traffic_split')

    if clear_traffic_split:
      endpoint.trafficSplit = None
      update_mask.append('traffic_split')

    if description is not None:
      endpoint.description = description
      update_mask.append('description')

    if not update_mask:
      raise errors.NoFieldsSpecifiedError('No updates requested.')

    req = self.messages.AiplatformProjectsLocationsEndpointsPatchRequest(
        name=endpoint_ref.RelativeName(),
        googleCloudAiplatformV1Endpoint=endpoint,
        updateMask=','.join(update_mask))
    return self.client.projects_locations_endpoints.Patch(req)

  def PatchBeta(self,
                endpoint_ref,
                labels_update,
                display_name=None,
                description=None,
                traffic_split=None,
                clear_traffic_split=False):
    """Updates an endpoint using v1beta1 API.

    Args:
      endpoint_ref: Resource, the parsed endpoint to be updated.
      labels_update: UpdateResult, the result of applying the label diff
        constructed from args.
      display_name: str or None, the new display name of the endpoint.
      description: str or None, the new description of the endpoint.
      traffic_split: dict or None, the new traffic split of the endpoint.
      clear_traffic_split: bool, whether or not clear traffic split of the
        endpoint.

    Returns:
      The response message of Patch.

    Raises:
      NoFieldsSpecifiedError: An error if no updates requested.
    """
    endpoint = self.messages.GoogleCloudAiplatformV1beta1Endpoint()
    update_mask = []

    if labels_update.needs_update:
      endpoint.labels = labels_update.labels
      update_mask.append('labels')

    if display_name is not None:
      endpoint.displayName = display_name
      update_mask.append('display_name')

    if traffic_split is not None:
      additional_properties = []
      for key, value in sorted(traffic_split.items()):
        additional_properties.append(
            endpoint.TrafficSplitValue().AdditionalProperty(
                key=key, value=value))
      endpoint.trafficSplit = endpoint.TrafficSplitValue(
          additionalProperties=additional_properties)
      update_mask.append('traffic_split')

    if clear_traffic_split:
      endpoint.trafficSplit = None
      update_mask.append('traffic_split')

    if description is not None:
      endpoint.description = description
      update_mask.append('description')

    if not update_mask:
      raise errors.NoFieldsSpecifiedError('No updates requested.')

    req = self.messages.AiplatformProjectsLocationsEndpointsPatchRequest(
        name=endpoint_ref.RelativeName(),
        googleCloudAiplatformV1beta1Endpoint=endpoint,
        updateMask=','.join(update_mask))
    return self.client.projects_locations_endpoints.Patch(req)

  def Predict(self, endpoint_ref, instances_json):
    """Sends online prediction request to an endpoint using v1 API."""
    predict_request = self.messages.GoogleCloudAiplatformV1PredictRequest(
        instances=_ConvertPyListToMessageList(extra_types.JsonValue,
                                              instances_json['instances']))
    if 'parameters' in instances_json:
      predict_request.parameters = encoding.PyValueToMessage(
          extra_types.JsonValue, instances_json['parameters'])

    req = self.messages.AiplatformProjectsLocationsEndpointsPredictRequest(
        endpoint=endpoint_ref.RelativeName(),
        googleCloudAiplatformV1PredictRequest=predict_request)
    return self.client.projects_locations_endpoints.Predict(req)

  def PredictBeta(self, endpoint_ref, instances_json):
    """Sends online prediction request to an endpoint using v1beta1 API."""
    predict_request = self.messages.GoogleCloudAiplatformV1beta1PredictRequest(
        instances=_ConvertPyListToMessageList(
            extra_types.JsonValue, instances_json['instances']))
    if 'parameters' in instances_json:
      predict_request.parameters = encoding.PyValueToMessage(
          extra_types.JsonValue, instances_json['parameters'])

    req = self.messages.AiplatformProjectsLocationsEndpointsPredictRequest(
        endpoint=endpoint_ref.RelativeName(),
        googleCloudAiplatformV1beta1PredictRequest=predict_request)
    return self.client.projects_locations_endpoints.Predict(req)

  def RawPredict(self, endpoint_ref, headers, request):
    """Sends online raw prediction request to an endpoint."""
    url = '{}{}/{}:rawPredict'.format(self.client.url,
                                      getattr(self.client, '_VERSION'),
                                      endpoint_ref.RelativeName())

    status, response_headers, response = _DoHttpPost(url, headers, request)
    if status != http_client.OK:
      raise core_exceptions.Error('HTTP request failed. Response:\n' +
                                  response.decode())

    return response_headers, response

  def Explain(self, endpoint_ref, instances_json, args):
    """Sends online explanation request to an endpoint using v1beta1 API."""
    explain_request = self.messages.GoogleCloudAiplatformV1ExplainRequest(
        instances=_ConvertPyListToMessageList(extra_types.JsonValue,
                                              instances_json['instances']))
    if 'parameters' in instances_json:
      explain_request.parameters = encoding.PyValueToMessage(
          extra_types.JsonValue, instances_json['parameters'])
    if args.deployed_model_id is not None:
      explain_request.deployedModelId = args.deployed_model_id

    req = self.messages.AiplatformProjectsLocationsEndpointsExplainRequest(
        endpoint=endpoint_ref.RelativeName(),
        googleCloudAiplatformV1ExplainRequest=explain_request)
    return self.client.projects_locations_endpoints.Explain(req)

  def ExplainBeta(self, endpoint_ref, instances_json, args):
    """Sends online explanation request to an endpoint using v1beta1 API."""
    explain_request = self.messages.GoogleCloudAiplatformV1beta1ExplainRequest(
        instances=_ConvertPyListToMessageList(
            extra_types.JsonValue, instances_json['instances']))
    if 'parameters' in instances_json:
      explain_request.parameters = encoding.PyValueToMessage(
          extra_types.JsonValue, instances_json['parameters'])
    if args.deployed_model_id is not None:
      explain_request.deployedModelId = args.deployed_model_id

    req = self.messages.AiplatformProjectsLocationsEndpointsExplainRequest(
        endpoint=endpoint_ref.RelativeName(),
        googleCloudAiplatformV1beta1ExplainRequest=explain_request)
    return self.client.projects_locations_endpoints.Explain(req)

  def DeployModel(self,
                  endpoint_ref,
                  model,
                  region,
                  display_name,
                  machine_type=None,
                  accelerator_dict=None,
                  min_replica_count=None,
                  max_replica_count=None,
                  enable_access_logging=False,
                  disable_container_logging=False,
                  service_account=None,
                  traffic_split=None):
    """Deploys a model to an existing endpoint using v1 API.

    Args:
      endpoint_ref: Resource, the parsed endpoint that the model is deployed to.
      model: str, Id of the uploaded model to be deployed.
      region: str, the location of the endpoint and the model.
      display_name: str, the display name of the new deployed model.
      machine_type: str or None, the type of the machine to serve the model.
      accelerator_dict: dict or None, the accelerator attached to the deployed
        model from args.
      min_replica_count: int or None, the minimum number of replicas the
        deployed model will be always deployed on.
      max_replica_count: int or None, the maximum number of replicas the
        deployed model may be deployed on.
      enable_access_logging: bool, whether or not enable access logs.
      disable_container_logging: bool, whether or not disable container logging.
      service_account: str or None, the service account that the deployed model
        runs as.
      traffic_split: dict or None, the new traffic split of the endpoint.

    Returns:
      A long-running operation for DeployModel.
    """
    model_ref = _ParseModel(model, region)

    resource_type = _GetModelDeploymentResourceType(model_ref, self.client)
    deployed_model = None
    if resource_type == 'DEDICATED_RESOURCES':
      # dedicated resources
      machine_spec = self.messages.GoogleCloudAiplatformV1MachineSpec()
      if machine_type is not None:
        machine_spec.machineType = machine_type
      accelerator = flags.ParseAcceleratorFlag(accelerator_dict,
                                               constants.GA_VERSION)
      if accelerator is not None:
        machine_spec.acceleratorType = accelerator.acceleratorType
        machine_spec.acceleratorCount = accelerator.acceleratorCount

      dedicated = self.messages.GoogleCloudAiplatformV1DedicatedResources(
          machineSpec=machine_spec)
      # min-replica-count is required and must be >= 1 if models use dedicated
      # resources. Default to 1 if not specified.
      dedicated.minReplicaCount = min_replica_count or 1
      if max_replica_count is not None:
        dedicated.maxReplicaCount = max_replica_count

      deployed_model = self.messages.GoogleCloudAiplatformV1DeployedModel(
          dedicatedResources=dedicated,
          displayName=display_name,
          model=model_ref.RelativeName())
    else:
      # automatic resources
      automatic = self.messages.GoogleCloudAiplatformV1AutomaticResources()
      if min_replica_count is not None:
        automatic.minReplicaCount = min_replica_count
      if max_replica_count is not None:
        automatic.maxReplicaCount = max_replica_count

      deployed_model = self.messages.GoogleCloudAiplatformV1DeployedModel(
          automaticResources=automatic,
          displayName=display_name,
          model=model_ref.RelativeName())

    deployed_model.enableAccessLogging = enable_access_logging
    deployed_model.disableContainerLogging = disable_container_logging

    if service_account is not None:
      deployed_model.serviceAccount = service_account

    deployed_model_req = \
        self.messages.GoogleCloudAiplatformV1DeployModelRequest(
            deployedModel=deployed_model)

    if traffic_split is not None:
      additional_properties = []
      for key, value in sorted(traffic_split.items()):
        additional_properties.append(
            deployed_model_req.TrafficSplitValue().AdditionalProperty(
                key=key, value=value))
      deployed_model_req.trafficSplit = deployed_model_req.TrafficSplitValue(
          additionalProperties=additional_properties)

    req = self.messages.AiplatformProjectsLocationsEndpointsDeployModelRequest(
        endpoint=endpoint_ref.RelativeName(),
        googleCloudAiplatformV1DeployModelRequest=deployed_model_req)
    return self.client.projects_locations_endpoints.DeployModel(req)

  def DeployModelBeta(self,
                      endpoint_ref,
                      model,
                      region,
                      display_name,
                      machine_type=None,
                      accelerator_dict=None,
                      min_replica_count=None,
                      max_replica_count=None,
                      autoscaling_metric_specs=None,
                      enable_access_logging=False,
                      enable_container_logging=False,
                      service_account=None,
                      traffic_split=None):
    """Deploys a model to an existing endpoint using v1beta1 API.

    Args:
      endpoint_ref: Resource, the parsed endpoint that the model is deployed to.
      model: str, Id of the uploaded model to be deployed.
      region: str, the location of the endpoint and the model.
      display_name: str, the display name of the new deployed model.
      machine_type: str or None, the type of the machine to serve the model.
      accelerator_dict: dict or None, the accelerator attached to the deployed
        model from args.
      min_replica_count: int or None, the minimum number of replicas the
        deployed model will be always deployed on.
      max_replica_count: int or None, the maximum number of replicas the
        deployed model may be deployed on.
      autoscaling_metric_specs: dict or None, the metric specification that
        defines the target resource utilization for calculating the desired
        replica count.
      enable_access_logging: bool, whether or not enable access logs.
      enable_container_logging: bool, whether or not enable container logging.
      service_account: str or None, the service account that the deployed model
        runs as.
      traffic_split: dict or None, the new traffic split of the endpoint.

    Returns:
      A long-running operation for DeployModel.
    """
    model_ref = _ParseModel(model, region)

    resource_type = _GetModelDeploymentResourceType(model_ref, self.client)
    deployed_model = None
    if resource_type == 'DEDICATED_RESOURCES':
      # dedicated resources
      machine_spec = self.messages.GoogleCloudAiplatformV1beta1MachineSpec()
      if machine_type is not None:
        machine_spec.machineType = machine_type
      accelerator = flags.ParseAcceleratorFlag(accelerator_dict,
                                               constants.BETA_VERSION)
      if accelerator is not None:
        machine_spec.acceleratorType = accelerator.acceleratorType
        machine_spec.acceleratorCount = accelerator.acceleratorCount

      dedicated = self.messages.GoogleCloudAiplatformV1beta1DedicatedResources(
          machineSpec=machine_spec)
      # min-replica-count is required and must be >= 1 if models use dedicated
      # resources. Default to 1 if not specified.
      dedicated.minReplicaCount = min_replica_count or 1
      if max_replica_count is not None:
        dedicated.maxReplicaCount = max_replica_count

      if autoscaling_metric_specs is not None:
        autoscaling_metric_specs_list = []
        for name, target in sorted(autoscaling_metric_specs.items()):
          autoscaling_metric_specs_list.append(
              self.messages.GoogleCloudAiplatformV1beta1AutoscalingMetricSpec(
                  metricName=constants.OP_AUTOSCALING_METRIC_NAME_MAPPER[name],
                  target=target))
        dedicated.autoscalingMetricSpecs = autoscaling_metric_specs_list

      deployed_model = self.messages.GoogleCloudAiplatformV1beta1DeployedModel(
          dedicatedResources=dedicated,
          displayName=display_name,
          model=model_ref.RelativeName())
    else:
      # automatic resources
      automatic = self.messages.GoogleCloudAiplatformV1beta1AutomaticResources()
      if min_replica_count is not None:
        automatic.minReplicaCount = min_replica_count
      if max_replica_count is not None:
        automatic.maxReplicaCount = max_replica_count

      deployed_model = self.messages.GoogleCloudAiplatformV1beta1DeployedModel(
          automaticResources=automatic,
          displayName=display_name,
          model=model_ref.RelativeName())

    deployed_model.enableAccessLogging = enable_access_logging
    deployed_model.enableContainerLogging = enable_container_logging

    if service_account is not None:
      deployed_model.serviceAccount = service_account

    deployed_model_req = \
        self.messages.GoogleCloudAiplatformV1beta1DeployModelRequest(
            deployedModel=deployed_model)

    if traffic_split is not None:
      additional_properties = []
      for key, value in sorted(traffic_split.items()):
        additional_properties.append(
            deployed_model_req.TrafficSplitValue().AdditionalProperty(
                key=key, value=value))
      deployed_model_req.trafficSplit = deployed_model_req.TrafficSplitValue(
          additionalProperties=additional_properties)

    req = self.messages.AiplatformProjectsLocationsEndpointsDeployModelRequest(
        endpoint=endpoint_ref.RelativeName(),
        googleCloudAiplatformV1beta1DeployModelRequest=deployed_model_req)
    return self.client.projects_locations_endpoints.DeployModel(req)

  def UndeployModel(self, endpoint_ref, deployed_model_id, traffic_split=None):
    """Undeploys a model from an endpoint using v1 API.

    Args:
      endpoint_ref: Resource, the parsed endpoint that the model is undeployed
        from.
      deployed_model_id: str, Id of the deployed model to be undeployed.
      traffic_split: dict or None, the new traffic split of the endpoint.

    Returns:
      A long-running operation for UndeployModel.
    """
    undeployed_model_req = \
        self.messages.GoogleCloudAiplatformV1UndeployModelRequest(
            deployedModelId=deployed_model_id)

    if traffic_split is not None:
      additional_properties = []
      for key, value in sorted(traffic_split.items()):
        additional_properties.append(
            undeployed_model_req.TrafficSplitValue().AdditionalProperty(
                key=key, value=value))
      undeployed_model_req.trafficSplit = \
          undeployed_model_req.TrafficSplitValue(
              additionalProperties=additional_properties)

    req = \
        self.messages.AiplatformProjectsLocationsEndpointsUndeployModelRequest(
            endpoint=endpoint_ref.RelativeName(),
            googleCloudAiplatformV1UndeployModelRequest= \
            undeployed_model_req)
    return self.client.projects_locations_endpoints.UndeployModel(req)

  def UndeployModelBeta(self,
                        endpoint_ref,
                        deployed_model_id,
                        traffic_split=None):
    """Undeploys a model from an endpoint using v1beta1 API.

    Args:
      endpoint_ref: Resource, the parsed endpoint that the model is undeployed
        from.
      deployed_model_id: str, Id of the deployed model to be undeployed.
      traffic_split: dict or None, the new traffic split of the endpoint.

    Returns:
      A long-running operation for UndeployModel.
    """
    undeployed_model_req = \
        self.messages.GoogleCloudAiplatformV1beta1UndeployModelRequest(
            deployedModelId=deployed_model_id)

    if traffic_split is not None:
      additional_properties = []
      for key, value in sorted(traffic_split.items()):
        additional_properties.append(
            undeployed_model_req.TrafficSplitValue().AdditionalProperty(
                key=key, value=value))
      undeployed_model_req.trafficSplit = \
          undeployed_model_req.TrafficSplitValue(
              additionalProperties=additional_properties)

    req = \
        self.messages.AiplatformProjectsLocationsEndpointsUndeployModelRequest(
            endpoint=endpoint_ref.RelativeName(),
            googleCloudAiplatformV1beta1UndeployModelRequest= \
            undeployed_model_req)
    return self.client.projects_locations_endpoints.UndeployModel(req)
