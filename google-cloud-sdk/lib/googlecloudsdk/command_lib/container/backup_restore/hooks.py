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
"""Hooks for Backup for GKE command line arguments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.backup_restore import util as api_util
from googlecloudsdk.calliope.exceptions import InvalidArgumentException


def AddForceToDeleteRequest(ref, args, request):
  # Unused arguments.
  del ref
  del args

  # Add force=true to delete requests for backup and restore resources.
  request.force = True
  return request


def ProcessSelectedApplications(selected_applications):
  """Processes selected-applications flag."""
  if not selected_applications:
    return None
  message = api_util.GetMessagesModule()
  sa = message.NamespacedNames()
  try:
    for namespaced_name in selected_applications.split(','):
      namespace, name = namespaced_name.split('/')
      if not namespace:
        raise InvalidArgumentException(
            '--selected-applications',
            'Namespace of selected application {0} is empty.'.format(
                namespaced_name))
      if not name:
        raise InvalidArgumentException(
            '--selected-applications',
            'Name of selected application {0} is empty.'.format(
                namespaced_name))
      nn = message.NamespacedName()
      nn.name = name
      nn.namespace = namespace
      sa.namespacedNames.append(nn)
    return sa
  except ValueError:
    raise InvalidArgumentException(
        '--selected-applications',
        'Selected applications {0} is invalid.'.format(selected_applications))


def PreprocessUpdateBackupPlan(ref, args, request):
  """Preprocesses request and update mask for backup update command."""
  del ref

  # Clear other fields in the backup scope mutex group.
  if args.IsSpecified('selected_namespaces'):
    request.backupPlan.backupConfig.selectedApplications = None
    request.backupPlan.backupConfig.allNamespaces = None
  if args.IsSpecified('selected_applications'):
    request.backupPlan.backupConfig.selectedNamespaces = None
    request.backupPlan.backupConfig.allNamespaces = None
  if args.IsSpecified('all_namespaces'):
    request.backupPlan.backupConfig.selectedApplications = None
    request.backupPlan.backupConfig.selectedNamespaces = None

  # Correct update mask for backup scope mutex group.
  new_masks = []
  for mask in request.updateMask.split(','):
    if mask.startswith('backupConfig.selectedNamespaces'):
      mask = 'backupConfig.selectedNamespaces'
    elif mask.startswith('backupConfig.selectedApplications'):
      mask = 'backupConfig.selectedApplications'
    # Other masks are unchanged.
    new_masks.append(mask)
  request.updateMask = ','.join(new_masks)
  return request
