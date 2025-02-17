# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Common flags for artifacts print-settings commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys
import textwrap

from googlecloudsdk.api_lib.artifacts import exceptions as ar_exceptions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers

_PACKAGE_TYPE_CHOICES = {
    'MAVEN': 'Maven package.',
}

_EXPERIMENTAL_PACKAGE_TYPE_CHOICES = {
    'GO': 'Go third party package.',
}


def RepoAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='repository', help_text='Repository of the {resource}.')


def LocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='location', help_text='Location of the {resource}.')


def GetRepoResourceSpec():
  return concepts.ResourceSpec(
      'artifactregistry.projects.locations.repositories',
      resource_name='repository',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      repositoriesId=RepoAttributeConfig())


def GetBetaRepoResourceSpec():
  return concepts.ResourceSpec(
      'artifactregistry.projects.locations.repositories',
      resource_name='repository',
      api_version='v1beta1',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      repositoriesId=RepoAttributeConfig())


def GetLocationResourceSpec():
  return concepts.ResourceSpec(
      'artifactregistry.projects.locations',
      resource_name='location',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig())


def GetScopeFlag():
  return base.Argument(
      '--scope',
      help=('The scope to associate with the Artifact Registry registry. '
            'If not specified, Artifact Registry is set as the default '
            'registry.'))


def GetImagePathOptionalArg():
  """Gets IMAGE_PATH optional positional argument."""
  help_txt = textwrap.dedent("""\
  An Artifact Registry repository or a container image.
  If not specified, default config values are used.

  A valid docker repository has the format of
    LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID

  A valid image has the format of
    LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE_PATH
""")
  return base.Argument('IMAGE_PATH', help=help_txt, nargs='?')


def GetImageRequiredArg():
  """Gets IMAGE required positional argument."""
  help_txt = textwrap.dedent("""\
  A container image.

  A valid container image has the format of
    LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE

  A valid container image that can be referenced by tag or digest, has the format of
    LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE:tag
    LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE@sha256:digest
""")
  return base.Argument('IMAGE', help=help_txt)


def GetDockerImageRequiredArg():
  help_txt = textwrap.dedent("""\
  Docker image - The container image that you want to tag.

A valid container image can be referenced by tag or digest, has the format of
  LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE:tag
  LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE@sha256:digest
""")
  return base.Argument('DOCKER_IMAGE', help=help_txt)


def GetTagRequiredArg():
  help_txt = textwrap.dedent("""\
  Image tag - The container image tag.

A valid Docker tag has the format of
  LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY-ID/IMAGE:tag
""")
  return base.Argument('DOCKER_TAG', help=help_txt)


def GetRepoFlag():
  return concept_parsers.ConceptParser.ForResource(
      '--repository',
      GetRepoResourceSpec(),
      ('The Artifact Registry repository. If not specified, '
       'the current artifacts/repository is used.'),
      required=False)


def GetLocationFlag():
  return concept_parsers.ConceptParser.ForResource(
      '--location',
      GetLocationResourceSpec(),
      ('The Artifact Registry repository location. If not specified, '
       'the current artifacts/location is used.'),
      required=True)


def GetRepoArgFromBeta():
  return concept_parsers.ConceptParser.ForResource(
      'repository',
      GetBetaRepoResourceSpec(),
      ('The Artifact Registry repository. If not specified, '
       'the current artifacts/repository is used.'),
      required=True)


def GetOptionalLocationFlag():
  return concept_parsers.ConceptParser.ForResource(
      '--location',
      GetLocationResourceSpec(),
      ('The Artifact Registry repository location. You can also set '
       '--location=all to list repositories across all locations. '
       'If you omit this flag, the default location is used if you set the '
       'artifacts/location property. Otherwise, omitting this flag '
       'lists repositories across all locations.'),
      required=False)


def GetIncludeTagsFlag():
  return base.Argument(
      '--include-tags',
      help=('If specified, all tags associated with each image digest are '
            'displayed.'),
      action='store_true',
      required=False)


def GetDeleteTagsFlag():
  return base.Argument(
      '--delete-tags',
      help='If specified, all tags associated with the image are deleted.',
      action='store_true',
      required=False)


def GetJsonKeyFlag(tool):
  """Gets Json Key Flag text based on specified tool."""
  if tool == 'pypi' or tool == 'python':
    return base.Argument(
        '--json-key',
        help=('Path to service account JSON key. If not specified, '
              'output returns either credentials for an active service account '
              'or a placeholder for the current user account.'))
  elif tool in ('gradle', 'maven', 'npm'):
    return base.Argument(
        '--json-key',
        help=('Path to service account JSON key. If not specified, '
              'current active service account credentials or a placeholder for '
              'gcloud credentials is used.'))
  else:
    raise ar_exceptions.ArtifactRegistryError(
        'Invalid tool type: {}'.format(tool))


def GetShowAllMetadataFlag():
  return base.Argument(
      '--show-all-metadata',
      action='store_true',
      help='Include all metadata in the output.')


def GetShowDeploymentFlag():
  return base.Argument(
      '--show-deployment',
      action='store_true',
      help='Include deployment metadata in the output.')


def GetShowImageBasisFlag():
  return base.Argument(
      '--show-image-basis',
      action='store_true',
      help='Include base image metadata in the output.')


def GetShowPackageVulnerabilityFlag():
  return base.Argument(
      '--show-package-vulnerability',
      action='store_true',
      help='Include vulnerability metadata in the output.')


def GetShowBuildDetailsFlag():
  return base.Argument(
      '--show-build-details',
      action='store_true',
      help='Include build metadata in the output.')


def GetMetadataFilterFlag():
  return base.Argument(
      '--metadata-filter',
      help=('Additional filter to fetch metadata for a given '
            'qualified image reference.'))


def GetShowOccurrencesFlag():
  return base.Argument(
      '--show-occurrences',
      action='store_true',
      help='Show summaries of the various Occurrence types.')


def GetShowOccurrencesFromFlag():
  return base.Argument(
      '--show-occurrences-from',
      type=arg_parsers.BoundedInt(1, sys.maxsize, unlimited=True),
      default=10,
      help=('The number of the most recent images for which to '
            'summarize Occurences.'))


def GetOccurrenceFilterFlag():
  return base.Argument(
      '--occurrence-filter',
      default='kind="BUILD" OR kind="IMAGE" OR kind="DISCOVERY"',
      help='A filter for the Occurrences which will be summarized.')


def GetShowProvenanceFlag():
  return base.Argument(
      '--show-provenance',
      action='store_true',
      hidden=True,
      help='Include provenance metadata in the output.')


def GetResourceURIArg():
  """Gets RESOURCE_URI required positional argument."""
  return base.Argument(
      'RESOURCE_URI',
      help=('A container image in a Google Cloud registry (Artifact Registry '
            'or Container Registry), or a local container image.'))


def GetRemoteFlag():
  return base.Argument(
      '--remote',
      action='store_true',
      default=False,
      help=('Whether the container image is located remotely or '
            'on your local machine.'))


def GetOnDemandScanningLocationFlag():
  return base.Argument(
      '--location',
      choices={
          'us': 'Perform analysis in the US',
          'europe': 'Perform analysis in Europe',
          'asia': 'Perform analysis in Asia',
      },
      default='us',
      help=('The API location in which to perform package analysis. Consider '
            'choosing a location closest to where you are located. Proximity '
            'to the container image does not affect response time.'))


def GetOnDemandScanningFakeExtractionFlag():
  return base.Argument(
      '--fake-extraction',
      action='store_true',
      default=False,
      hidden=True,
      help=('Whether to use fake packages/versions instead of performing '
            'extraction. This flag is for test purposes only.'))


def GetOnDemandIncludeOSVDataFlag():
  return base.Argument(
      '--include-osv-data',
      action='store_true',
      default=False,
      hidden=True,
      help=('Whether to include OSV data in the scan.'))


def GetAdditionalPackageTypesFlag():
  return base.Argument(
      '--additional-package-types',
      type=arg_parsers.ArgList(
          choices=_PACKAGE_TYPE_CHOICES,
          element_type=lambda package_type: package_type.upper()),
      metavar='ADDITIONAL_PACKAGE_TYPES',
      help=(
          'A comma-separated list of package types to scan in addition to OS packages.'
      ))


def GetExperimentalPackageTypesFlag():
  return base.Argument(
      '--experimental-package-types',
      type=arg_parsers.ArgList(
          choices=_EXPERIMENTAL_PACKAGE_TYPE_CHOICES,
          element_type=lambda package_type: package_type.upper()),
      hidden=True,
      metavar='EXPERIMENTAL_PACKAGE_TYPES',
      help=(
          'A comma-separated list of experimental package types to scan in addition to OS packages and officially supported third party packages.'
      ))
