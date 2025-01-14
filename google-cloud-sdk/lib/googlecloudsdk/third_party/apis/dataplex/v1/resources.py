# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Resource definitions for cloud platform apis."""

import enum


BASE_URL = 'https://dataplex.googleapis.com/v1/'
DOCS_URL = 'https://cloud.google.com/dataplex/docs'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  PROJECTS = (
      'projects',
      'projects/{projectsId}',
      {},
      ['projectsId'],
      True
  )
  PROJECTS_LOCATIONS = (
      'projects.locations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_LAKES = (
      'projects.locations.lakes',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/lakes/{lakesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_LAKES_ACTIONS = (
      'projects.locations.lakes.actions',
      'projects/{projectsId}/locations/{locationsId}/lakes/{lakesId}/actions/'
      '{actionsId}',
      {},
      ['projectsId', 'locationsId', 'lakesId', 'actionsId'],
      True
  )
  PROJECTS_LOCATIONS_LAKES_TASKS = (
      'projects.locations.lakes.tasks',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/lakes/{lakesId}/'
              'tasks/{tasksId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_LAKES_TASKS_JOBS = (
      'projects.locations.lakes.tasks.jobs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/lakes/{lakesId}/'
              'tasks/{tasksId}/jobs/{jobsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_LAKES_ZONES = (
      'projects.locations.lakes.zones',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/lakes/{lakesId}/'
              'zones/{zonesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_LAKES_ZONES_ACTIONS = (
      'projects.locations.lakes.zones.actions',
      'projects/{projectsId}/locations/{locationsId}/lakes/{lakesId}/zones/'
      '{zonesId}/actions/{actionsId}',
      {},
      ['projectsId', 'locationsId', 'lakesId', 'zonesId', 'actionsId'],
      True
  )
  PROJECTS_LOCATIONS_LAKES_ZONES_ASSETS = (
      'projects.locations.lakes.zones.assets',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/lakes/{lakesId}/'
              'zones/{zonesId}/assets/{assetsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_LAKES_ZONES_ASSETS_ACTIONS = (
      'projects.locations.lakes.zones.assets.actions',
      'projects/{projectsId}/locations/{locationsId}/lakes/{lakesId}/zones/'
      '{zonesId}/assets/{assetsId}/actions/{actionsId}',
      {},
      ['projectsId', 'locationsId', 'lakesId', 'zonesId', 'assetsId', 'actionsId'],
      True
  )
  PROJECTS_LOCATIONS_LAKES_ZONES_ENTITIES = (
      'projects.locations.lakes.zones.entities',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/lakes/{lakesId}/'
              'zones/{zonesId}/entities/{entitiesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_LAKES_ZONES_ENTITIES_PARTITIONS = (
      'projects.locations.lakes.zones.entities.partitions',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/lakes/{lakesId}/'
              'zones/{zonesId}/entities/{entitiesId}/partitions/'
              '{partitionsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_OPERATIONS = (
      'projects.locations.operations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/operations/'
              '{operationsId}',
      },
      ['name'],
      True
  )

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
