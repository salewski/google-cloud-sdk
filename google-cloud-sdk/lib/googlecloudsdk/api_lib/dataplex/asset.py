# -*- coding: utf-8 -*- #
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""Client for interaction with Asset API CRUD DATAPLEX."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import util as dataplex_api
from googlecloudsdk.command_lib.iam import iam_util


def SetIamPolicy(asset_ref, policy):
  """Set Iam Policy request."""
  set_iam_policy_req = dataplex_api.GetMessageModule(
  ).DataplexProjectsLocationsLakesZonesAssetsSetIamPolicyRequest(
      resource=asset_ref.RelativeName(),
      googleIamV1SetIamPolicyRequest=dataplex_api.GetMessageModule()
      .GoogleIamV1SetIamPolicyRequest(policy=policy))
  return dataplex_api.GetClientInstance(
  ).projects_locations_lakes_zones_assets.SetIamPolicy(set_iam_policy_req)


def GetIamPolicy(asset_ref):
  """Get Iam Policy request."""
  get_iam_policy_req = dataplex_api.GetMessageModule(
  ).DataplexProjectsLocationsLakesZonesAssetsGetIamPolicyRequest(
      resource=asset_ref.RelativeName())
  return dataplex_api.GetClientInstance(
  ).projects_locations_lakes_zones_assets.GetIamPolicy(get_iam_policy_req)


def AddIamPolicyBinding(asset_ref, member, role):
  """Add IAM policy binding request."""
  policy = GetIamPolicy(asset_ref)
  iam_util.AddBindingToIamPolicy(
      dataplex_api.GetMessageModule().GoogleIamV1Binding, policy, member, role)
  return SetIamPolicy(asset_ref, policy)


def RemoveIamPolicyBinding(zone_ref, member, role):
  """Remove IAM policy binding request."""
  policy = GetIamPolicy(zone_ref)
  iam_util.RemoveBindingFromIamPolicy(policy, member, role)
  return SetIamPolicy(zone_ref, policy)


def SetIamPolicyFromFile(asset_ref, policy_file):
  """Set IAM policy binding request from file."""
  policy = iam_util.ParsePolicyFile(
      policy_file,
      dataplex_api.GetMessageModule().GoogleIamV1Policy)
  return SetIamPolicy(asset_ref, policy)


def GenerateAssetForCreateRequest(args):
  """Create Asset for Message Create Requests."""
  module = dataplex_api.GetMessageModule()
  resource_spec_field = module.GoogleCloudDataplexV1AssetResourceSpec
  resource_spec = module.GoogleCloudDataplexV1AssetResourceSpec(
      name=args.resource_name,
      type=resource_spec_field.TypeValueValuesEnum(args.resource_type),
      creationPolicy=resource_spec_field.CreationPolicyValueValuesEnum(
          args.creation_policy))
  if args.deletion_policy:
    setattr(
        resource_spec, 'deletionPolicy',
        resource_spec_field.DeletionPolicyValueValuesEnum(args.deletion_policy))
  return module.GoogleCloudDataplexV1Asset(
      description=args.description,
      displayName=args.display_name,
      labels=dataplex_api.CreateLabels(module.GoogleCloudDataplexV1Asset, args),
      resourceSpec=resource_spec,
      discoverySpec=GenerateDiscoverySpec(args))


def GenerateAssetForUpdateRequest(args):
  """Create Asset for Message Update Requests."""
  module = dataplex_api.GetMessageModule()
  resource_spec = module.GoogleCloudDataplexV1AssetResourceSpec()
  if args.deletion_policy:
    setattr(
        resource_spec, 'deletionPolicy',
        module.GoogleCloudDataplexV1AssetResourceSpec
        .DeletionPolicyValueValuesEnum(args.deletion_policy))
  return module.GoogleCloudDataplexV1Asset(
      description=args.description,
      displayName=args.display_name,
      labels=dataplex_api.CreateLabels(module.GoogleCloudDataplexV1Asset, args),
      resourceSpec=resource_spec,
      discoverySpec=GenerateDiscoverySpec(args))


def GenerateDiscoverySpec(args):
  """Create Discovery Spec for Assets."""
  discovery_spec = dataplex_api.GetMessageModule(
  ).GoogleCloudDataplexV1AssetDiscoverySpec(
      enabled=args.discovery_enabled,
      includePatterns=args.discovery_include_patterns,
      excludePatterns=args.discovery_exclude_patterns,
      schedule=args.discovery_schedule)
  return discovery_spec


def GenerateUpdateMask(args):
  """Create Update Mask for Assets."""
  update_mask = []
  if args.IsSpecified('description'):
    update_mask.append('description')
  if args.IsSpecified('display_name'):
    update_mask.append('displayName')
  if args.IsSpecified('labels'):
    update_mask.append('labels')
  if args.IsSpecified('discovery_enabled'):
    update_mask.append('discoverySpec.enabled')
  if args.IsSpecified('discovery_include_patterns'):
    update_mask.append('discoverySpec.includePatterns')
  if args.IsSpecified('discovery_exclude_patterns'):
    update_mask.append('discoverySpec.excludePatterns')
  if args.IsSpecified('deletion_policy'):
    update_mask.append('resourceSpec.deletion_policy')
  if args.IsSpecified('discovery_schedule'):
    update_mask.append('discoverySpec.schedule')
  return update_mask


def WaitForOperation(operation):
  """Waits for the given google.longrunning.Operation to complete."""
  return dataplex_api.WaitForOperation(
      operation,
      dataplex_api.GetClientInstance().projects_locations_lakes_zones_assets)
