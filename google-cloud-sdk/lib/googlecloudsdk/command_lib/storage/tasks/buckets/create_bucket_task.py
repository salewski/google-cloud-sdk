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
"""Task for creating a bucket."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.core import log


class CreateBucketTask(task.Task):
  """Creates a cloud storage bucket."""

  def __init__(self, bucket_resource):
    """Initializes task.

    Args:
      bucket_resource (resource_reference.BucketResource): Should contain
        desired metadata for bucket.
    """
    super(CreateBucketTask, self).__init__()
    self._bucket_resource = bucket_resource

  def execute(self, task_status_queue=None):
    log.status.Print('Creating {}...'.format(self._bucket_resource))
    provider = self._bucket_resource.storage_url.scheme
    api_factory.get_api(provider).create_bucket(self._bucket_resource)
