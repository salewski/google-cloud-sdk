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

"""Task iterator for copy functionality."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import plurality_checkable_iterator
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import wildcard_iterator
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.command_lib.storage.tasks.cp import copy_task_factory
from googlecloudsdk.core import log


_RELATIVE_PATH_SYMBOLS = frozenset(['.', '..'])


def _expand_destination_wildcards(destination_string):
  """Expands destination wildcards.

  Ensures that only one resource matches the wildcard expanded string. Much
  like the unix cp command, the storage surface only supports copy operations
  to one user-specified destination.

  Args:
    destination_string (str): A string representing the destination url.

  Returns:
    A resource_reference.Resource, or None if no matching resource is found.

  Raises:
    ValueError if more than one resource is matched, or the source contained
    an unescaped wildcard and no resources were matched.
  """
  destination_iterator = (
      plurality_checkable_iterator.PluralityCheckableIterator(
          wildcard_iterator.get_wildcard_iterator(destination_string)))

  if destination_iterator.is_plural():
    raise ValueError('Destination ({}) must match exactly one URL.'.format(
        destination_string))

  contains_unexpanded_wildcard = (
      destination_iterator.is_empty() and
      wildcard_iterator.contains_wildcard(destination_string))

  if contains_unexpanded_wildcard:
    raise ValueError('Destination ({}) contains an unexpected wildcard.'.format(
        destination_string))

  if not destination_iterator.is_empty():
    return next(destination_iterator)


def _get_raw_destination(destination_string):
  """Converts self._destination_string to a destination resource.

  Args:
    destination_string (str): A string representing the destination url.

  Returns:
    A resource_reference.Resource. Note that this resource may not be a valid
    copy destination if it is a BucketResource, PrefixResource,
    FileDirectoryResource or UnknownResource.

  Raises:
    ValueError if the destination url is a cloud provider or if it specifies
    a version.
  """
  destination_url = storage_url.storage_url_from_string(destination_string)

  if isinstance(destination_url, storage_url.CloudUrl):
    if destination_url.is_provider():
      raise ValueError(
          'The cp command does not support provider-only destination URLs.')
    elif destination_url.generation is not None:
      raise ValueError(
          'The destination argument of the cp command cannot be a '
          'version-specific URL ({}).'
          .format(destination_string))

  raw_destination = _expand_destination_wildcards(destination_string)
  if raw_destination:
    return raw_destination
  return resource_reference.UnknownResource(destination_url)


def _destination_is_container(destination):
  """Returns True is the destination can be treated as a container.

  For a CloudUrl, a container is a bucket or a prefix. If the destination does
  not exist, we determine this based on the delimiter.
  For a FileUrl, A container is an existing dir. For non existing path, we
  return False.

  Args:
    destination (resource_reference.Resource): The destination container.

  Returns:
    bool: True if destination is a valid container.
  """
  try:
    if destination.is_container():
      return True
  except errors.ValueCannotBeDeterminedError:
    # Some resource classes are not clearly containers, like objects with names
    # ending in a delimiter. However, we want to treat them as containers anways
    # so that nesting at copy destinations will work as expected.
    pass

  destination_url = destination.storage_url
  if isinstance(destination_url, storage_url.FileUrl):
    # We don't want to treat non-existing file paths as valid containers.
    return os.path.isdir(destination_url.object_name)

  return (destination_url.versionless_url_string.endswith(
      destination_url.delimiter) or
          (isinstance(destination_url, storage_url.CloudUrl) and
           destination_url.is_bucket()))


def _has_valid_parent_dir(url_object):
  """Returns true if FileUrl with relative path symbol as parent directory."""
  if not isinstance(url_object, storage_url.FileUrl):
    return True

  _, _, after_last_delimiter = (
      url_object.versionless_url_string.rpartition(url_object.delimiter))

  return after_last_delimiter not in _RELATIVE_PATH_SYMBOLS and (
      after_last_delimiter not in [
          url_object.scheme.value + '://' + symbol
          for symbol in _RELATIVE_PATH_SYMBOLS
      ])


class CopyTaskIterator:
  """Iterates over each expanded source and creates an appropriate copy task."""

  def __init__(self,
               source_name_iterator,
               destination_string,
               custom_md5_digest=None,
               do_not_decompress=False,
               task_status_queue=None,
               user_request_args=None):
    """Initializes a CopyTaskIterator instance.

    Args:
      source_name_iterator (name_expansion.NameExpansionIterator):
        yields resource_reference.Resource objects with expanded source URLs.
      destination_string (str): The copy destination path or url.
      custom_md5_digest (str|None): User-added MD5 hash output to send to server
        for validating a single resource upload.
      do_not_decompress (bool): Prevents automatically decompressing
        downloaded gzips.
      task_status_queue (multiprocessing.Queue|None): Used for estimating total
        workload from this iterator.
      user_request_args (UserRequestArgs|None): Values for RequestConfig.
    """
    self._source_name_iterator = (
        plurality_checkable_iterator.PluralityCheckableIterator(
            source_name_iterator))
    self._multiple_sources = self._source_name_iterator.is_plural()
    self._do_not_decompress = do_not_decompress
    self._custom_md5_digest = custom_md5_digest
    self._task_status_queue = task_status_queue
    self._user_request_args = user_request_args

    self._total_file_count = 0
    self._total_size = 0

    self._raw_destination = _get_raw_destination(destination_string)
    if self._multiple_sources:
      self._raise_if_destination_is_file_url_and_not_a_directory()

    if self._multiple_sources and self._custom_md5_digest:
      raise ValueError('Received multiple objects to upload, but only one'
                       'custom MD5 digest is allowed.')

  def _raise_if_destination_is_file_url_and_not_a_directory(self):
    if (isinstance(self._raw_destination.storage_url, storage_url.FileUrl) and
        not _destination_is_container(self._raw_destination)):
      raise errors.InvalidUrlError(
          'Destination URL must name an existing directory.'
          ' Provided: {}.'.format(
              self._raw_destination.storage_url.object_name))

  def _update_workload_estimation(self, resource):
    """Updates total_file_count and total_size.

    Args:
      resource (resource_reference.Resource): Any type of resource. Parse to
        help estimate total workload.
    """
    if self._total_file_count == -1 or self._total_size == -1:
      # -1 is signal that data is corrupt and not worth tracking.
      return
    try:
      if resource.is_container():
        return
      if isinstance(resource, resource_reference.FileObjectResource):
        size = os.path.getsize(resource.storage_url.object_name)
      elif (isinstance(resource, resource_reference.ObjectResource) and
            resource.size is not None):
        size = resource.size
      else:
        raise errors.ValueCannotBeDeterminedError
    except (OSError, errors.ValueCannotBeDeterminedError):
      log.error('Could not get size of resource {}.'.format(resource))
      self._total_file_count = -1
      self._total_size = -1
    else:
      self._total_file_count += 1
      self._total_size += size

  def __iter__(self):
    for source in self._source_name_iterator:

      destination_resource = self._get_copy_destination(self._raw_destination,
                                                        source)

      source_url = source.resource.storage_url
      destination_url = destination_resource.storage_url
      if (isinstance(source.resource, resource_reference.ObjectResource) and
          isinstance(destination_url, storage_url.FileUrl) and
          destination_url.object_name.endswith(destination_url.delimiter)):
        log.debug('Skipping downloading {} to {} since the destination ends in'
                  ' a file system delimiter.'.format(
                      source_url.versionless_url_string,
                      destination_url.versionless_url_string))
        continue

      if source_url != source.expanded_url and not self._multiple_sources:
        # Multiple sources have been already validated in __init__.
        # This check is required for cases where recursion has been requested,
        # but there is only one object that needs to be copied over.
        self._raise_if_destination_is_file_url_and_not_a_directory()

      if source.original_url.generation:
        source_url_string = source_url.url_string
      else:
        source_url_string = source_url.versionless_url_string

      if self._custom_md5_digest:
        source.resource.md5_hash = self._custom_md5_digest

      log.status.Print('Copying {} to {}'.format(
          source_url_string, destination_url.versionless_url_string))
      if self._task_status_queue:
        self._update_workload_estimation(source.resource)

      yield copy_task_factory.get_copy_task(
          source.resource,
          destination_resource,
          do_not_decompress=self._do_not_decompress,
          user_request_args=self._user_request_args)

    if (self._task_status_queue and
        (self._total_file_count > 0 or self._total_size > 0)):
      # Show fraction of total copies completed now that we know totals.
      progress_callbacks.workload_estimator_callback(
          self._task_status_queue,
          item_count=self._total_file_count,
          size=self._total_size)

  def _get_copy_destination(self, raw_destination, source):
    """Returns the final destination StorageUrl instance."""
    completion_is_necessary = (
        _destination_is_container(raw_destination) or
        self._multiple_sources or
        source.resource.storage_url != source.expanded_url  # Recursion case.
    )

    if completion_is_necessary:
      return self._complete_destination(raw_destination, source)
    else:
      return raw_destination

  def _complete_destination(self, destination_container, source):
    """Gets a valid copy destination incorporating part of the source's name.

    When given a source file or object and a destination resource that should
    be treated as a container, this function uses the last part of the source's
    name to get an object or file resource representing the copy destination.

    For example: given a source `dir/file` and a destination `gs://bucket/`, the
    destination returned is a resource representing `gs://bucket/file`. Check
    the recursive helper function docstring for details on recursion handling.

    Args:
      destination_container (resource_reference.Resource): The destination
        container.
      source (NameExpansionResult): Represents the source resource and the
        expanded parent url in case of recursion.

    Returns:
      The completed destination, a resource_reference.Resource.
    """
    destination_url = destination_container.storage_url
    source_url = source.resource.storage_url
    if source_url != source.expanded_url:
      # In case of recursion, the expanded_url can be the expanded wildcard URL
      # representing the container, and the source url can be the file/object.
      destination_suffix = self._get_destination_suffix_for_recursion(
          destination_container, source)
    else:
      # Schema might give us incorrect suffix for Windows.
      # TODO(b/169093672) This will not be required if we get rid of file://
      schemaless_url = source_url.versionless_url_string.rpartition(
          source_url.scheme.value + '://')[2]

      destination_suffix = schemaless_url.rpartition(source_url.delimiter)[2]

    new_destination_url = destination_url.join(destination_suffix)
    return resource_reference.UnknownResource(new_destination_url)

  def _get_destination_suffix_for_recursion(self, destination_container,
                                            source):
    """Returns the suffix required to complete the destination URL.

    Let's assume the following:
      User command => cp -r */base_dir gs://dest/existing_prefix
      source.resource.storage_url => a/base_dir/c/d.txt
      source.expanded_url => a/base_dir
      destination_container.storage_url => gs://dest/existing_prefix

    If the destination container exists, the entire directory gets copied:
    Result => gs://dest/existing_prefix/base_dir/c/d.txt

    Args:
      destination_container (resource_reference.Resource): The destination
        container.
      source (NameExpansionResult): Represents the source resource and the
        expanded parent url in case of recursion.

    Returns:
      (str) The suffix to be appended to the destination container.
    """
    source_prefix_to_ignore = storage_url.rstrip_one_delimiter(
        source.expanded_url.versionless_url_string,
        source.expanded_url.delimiter)

    if (not isinstance(destination_container,
                       resource_reference.UnknownResource) and
        _has_valid_parent_dir(source.expanded_url) and
        destination_container.is_container()):
      # Destination container exists. This means we need to preserve the
      # top-level source directory.
      # Remove the leaf name so that it gets added to the destination.
      source_prefix_to_ignore, _, _ = source_prefix_to_ignore.rpartition(
          source.expanded_url.delimiter)
      if not source_prefix_to_ignore:
        # In case of Windows, the source URL might not contain any Windows
        # delimiter if it was a single directory (e.g file://dir) and
        # source_prefix_to_ignore will be empty. Set it to <scheme>://.
        # TODO(b/169093672) This will not be required if we get rid of file://
        source_prefix_to_ignore = source.expanded_url.scheme.value + '://'

    full_source_url = source.resource.storage_url.versionless_url_string
    suffix_for_destination = full_source_url.split(source_prefix_to_ignore)[1]

    # Windows uses \ as a delimiter. Force the suffix to use the same
    # delimiter used by the destination container.
    source_delimiter = source.resource.storage_url.delimiter
    destination_delimiter = destination_container.storage_url.delimiter
    if source_delimiter != destination_delimiter:
      return suffix_for_destination.replace(source_delimiter,
                                            destination_delimiter)
    return suffix_for_destination
