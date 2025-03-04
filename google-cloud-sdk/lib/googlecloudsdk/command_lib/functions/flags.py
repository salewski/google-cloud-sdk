# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Helpers for flags in commands working with Google Cloud Functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.functions.v1 import util as api_util
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources

API = 'cloudfunctions'
API_VERSION = 'v1'
LOCATIONS_COLLECTION = API + '.projects.locations'

SIGNATURE_TYPES = ['http', 'event', 'cloudevent']
SEVERITIES = ['DEBUG', 'INFO', 'ERROR']
EGRESS_SETTINGS = ['PRIVATE-RANGES-ONLY', 'ALL']
INGRESS_SETTINGS = ['ALL', 'INTERNAL-ONLY', 'INTERNAL-AND-GCLB']
SECURITY_LEVEL = ['SECURE-ALWAYS', 'SECURE-OPTIONAL']
INGRESS_SETTINGS_MAPPING = {
    'ALLOW_ALL': 'all',
    'ALLOW_INTERNAL_ONLY': 'internal-only',
    'ALLOW_INTERNAL_AND_GCLB': 'internal-and-gclb',
}

EGRESS_SETTINGS_MAPPING = {
    'PRIVATE_RANGES_ONLY': 'private-ranges-only',
    'ALL_TRAFFIC': 'all',
}

SECURITY_LEVEL_MAPPING = {
    'SECURE_ALWAYS': 'secure-always',
    'SECURE_OPTIONAL': 'secure-optional',
}

_KMS_KEY_NAME_PATTERN = (
    r'^projects/[^/]+/locations/[^/]+/keyRings/[a-zA-Z0-9_-]+'
    '/cryptoKeys/[a-zA-Z0-9_-]+$')
_KMS_KEY_NAME_ERROR = (
    'KMS key name should match projects/{project}/locations/{location}'
    '/keyRings/{keyring}/cryptoKeys/{cryptokey} and only contain characters '
    'from the valid character set for a KMS key.')
_DOCKER_REPOSITORY_NAME_PATTERN = (
    r'^projects/[^/]+/locations/[^/]+/repositories/[a-z]([a-z0-9-]*[a-z0-9])?$')
_DOCKER_REPOSITORY_NAME_ERROR = (
    'Docker repository name should match projects/{project}'
    '/locations/{location}/repositories/{repository} and only contain '
    'characters from the valid character set for a repository.')


def AddMinLogLevelFlag(parser):
  min_log_arg = base.ChoiceArgument(
      '--min-log-level',
      choices=[x.lower() for x in SEVERITIES],
      help_str='Minimum level of logs to be fetched.')
  min_log_arg.AddToParser(parser)


def AddIngressSettingsFlag(parser):
  ingress_settings_arg = base.ChoiceArgument(
      '--ingress-settings',
      choices=[x.lower() for x in INGRESS_SETTINGS],
      help_str='Ingress settings controls what traffic can reach the '
      'function. By default `all` will be used.')
  ingress_settings_arg.AddToParser(parser)


def AddEgressSettingsFlag(parser):
  egress_settings_arg = base.ChoiceArgument(
      '--egress-settings',
      choices=[x.lower() for x in EGRESS_SETTINGS],
      help_str='Egress settings controls what traffic is diverted through the '
      'VPC Access Connector resource. '
      'By default `private-ranges-only` will be used.')
  egress_settings_arg.AddToParser(parser)


def AddSecurityLevelFlag(parser):
  security_level_arg = base.ChoiceArgument(
      '--security-level',
      choices=[x.lower() for x in SECURITY_LEVEL],
      help_str='Security level controls whether a function\'s URL supports '
      'HTTPS only or both HTTP and HTTPS. By default, `secure-optional` will'
      ' be used, meaning both HTTP and HTTPS are supported.')
  security_level_arg.AddToParser(parser)


def GetLocationsUri(resource):
  registry = resources.REGISTRY.Clone()
  registry.RegisterApiByName(API, API_VERSION)
  ref = registry.Parse(
      resource.name,
      params={'projectsId': properties.VALUES.core.project.GetOrFail},
      collection=LOCATIONS_COLLECTION)
  return ref.SelfLink()


def AddFunctionMemoryFlag(parser, track=None):
  """Add flag for specifying function memory to the parser."""
  ga_help_text = """\
  Limit on the amount of memory the function can use.

  Allowed values are: 128MB, 256MB, 512MB, 1024MB, 2048MB, 4096MB, and
  8192MB. By default, a new function is limited to 256MB of memory. When
  deploying an update to an existing function, the function keeps its old
  memory limit unless you specify this flag."""

  alpha_help_text = """\
  Limit on the amount of memory the function can use.

  Allowed values for v1 are: 128MB, 256MB, 512MB, 1024MB, 2048MB, 4096MB,
  and 8192MB.

  Allowed values for v2 are in the format: <number><unit> with allowed units
  of "k", "M", "G", "Ki", "Mi", "Gi". Ending 'b' or 'B' is allowed.

  Examples: 100000k, 128M, 10Mb, 1024Mi, 750K, 4Gi.

  By default, a new function is limited to 256MB of memory. When
  deploying an update to an existing function, the function keeps its old
  memory limit unless you specify this flag."""

  help_text = (
      ga_help_text if track is not base.ReleaseTrack.ALPHA else alpha_help_text)

  parser.add_argument('--memory', type=str, help=help_text)


def ParseMemoryStrToNumBytes(binary_size):
  """Parse binary size to number of bytes.

  Args:
    binary_size: str, memory with size suffix

  Returns:
    num_bytes: int, the number of bytes
  """

  binary_size_parser = arg_parsers.BinarySize(
      suggested_binary_size_scales=['KB', 'MB', 'MiB', 'GB', 'GiB'],
      default_unit='MB')
  return binary_size_parser(binary_size)


def ValidateV1TimeoutFlag(args):
  if args.timeout and args.timeout > 540:
    raise arg_parsers.ArgumentTypeError(
        '--timeout: value must be less than or equal to 540s; received: {}s'
        .format(args.timeout))


def AddFunctionTimeoutFlag(parser, track=None):
  """Add flag for specifying function timeout to the parser.

  Args:
    parser: the argparse parser for the command.
    track: base.ReleaseTrack, calliope release track.

  Returns:
    None
  """

  ga_help_text = """\
      The function execution timeout, e.g. 30s for 30 seconds. Defaults to
      original value for existing function or 60 seconds for new functions.
      Cannot be more than 540s.
      See $ gcloud topic datetimes for information on duration formats."""

  alpha_help_text = """\
      The function execution timeout, e.g. 30s for 30 seconds. Defaults to
      original value for existing function or 60 seconds for new functions.

      For GCF first generation functions, cannot be more than 540s.

      For GCF second generation functions, cannot be more than 3600s.

      See $ gcloud topic datetimes for information on duration formats."""

  parser.add_argument(
      '--timeout',
      help=ga_help_text
      if track is not base.ReleaseTrack.ALPHA else alpha_help_text,
      type=arg_parsers.Duration(lower_bound='1s'))


def AddFunctionRetryFlag(parser):
  """Add flag for specifying function retry behavior to the parser."""
  parser.add_argument(
      '--retry',
      help=('If specified, then the function will be retried in case of a '
            'failure.'),
      action='store_true',
  )


def AddAllowUnauthenticatedFlag(parser):
  """Add the --allow-unauthenticated flag."""
  parser.add_argument(
      '--allow-unauthenticated',
      default=False,
      action='store_true',
      help=('If set, makes this a public function. This will allow all '
            'callers, without checking authentication.'))


def AddGen2Flag(parser, track):
  """Add the --gen2 flag."""
  help_text = (
      'If enabled, this command will use Cloud Functions (Second generation). '
      'If disabled, Cloud Functions (First generation) will be used. If not '
      'specified, the value of this flag will be taken from the '
      '`functions/gen2` configuration property.')
  parser.add_argument(
      '--gen2',
      default=False,
      hidden=_ShouldHideV2Flags(track),
      action=actions.StoreBooleanProperty(properties.VALUES.functions.gen2),
      help=help_text)

  if track is base.ReleaseTrack.ALPHA:
    parser.add_argument(
        '--v2',
        help=help_text,
        default=False,
        hidden=True,
        action=actions.DeprecationAction(
            '--v2',
            warn='The {flag_name} option is deprecated; use --gen2 instead.',
            removed=False,
            action=actions.StoreBooleanProperty(
                properties.VALUES.functions.gen2)),
    )


def ShouldUseGen2():
  gen2 = properties.VALUES.functions.gen2.GetBool()
  v2 = properties.VALUES.functions.v2.GetBool()
  return gen2 if gen2 is not None else bool(v2)


def _ShouldHideV2Flags(track):
  return track is not base.ReleaseTrack.ALPHA


def ShouldEnsureAllUsersInvoke(args):
  if args.allow_unauthenticated:
    return True
  else:
    return False


def ShouldDenyAllUsersInvoke(args):
  if (args.IsSpecified('allow_unauthenticated') and
      not args.allow_unauthenticated):
    return True
  else:
    return False


def AddSourceFlag(parser):
  """Add flag for specifying function source code to the parser."""
  parser.add_argument(
      '--source',
      help="""\
      Location of source code to deploy.

      Location of the source can be one of the following three options:

      * Source code in Google Cloud Storage (must be a `.zip` archive),
      * Reference to source repository or,
      * Local filesystem path (root directory of function source).

      Note that, depending on your runtime type, Cloud Functions will look
      for files with specific names for deployable functions. For Node.js,
      these filenames are `index.js` or `function.js`. For Python, this is
      `main.py`.

      If you do not specify the `--source` flag:

      * The current directory will be used for new function deployments.
      * If the function was previously deployed using a local filesystem path,
      then the function's source code will be updated using the current
      directory.
      * If the function was previously deployed using a Google Cloud Storage
      location or a source repository, then the function's source code will not
      be updated.

      The value of the flag will be interpreted as a Cloud Storage location, if
      it starts with `gs://`.

      The value will be interpreted as a reference to a source repository, if it
      starts with `https://`.

      Otherwise, it will be interpreted as the local filesystem path. When
      deploying source from the local filesystem, this command skips files
      specified in the `.gcloudignore` file (see `gcloud topic gcloudignore` for
      more information). If the `.gcloudignore` file doesn't exist, the command
      will try to create it.

      The minimal source repository URL is:
      `https://source.developers.google.com/projects/${PROJECT}/repos/${REPO}`

      By using the URL above, sources from the root directory of the
      repository on the revision tagged `master` will be used.

      If you want to deploy from a revision different from `master`, append one
      of the following three sources to the URL:

      * `/revisions/${REVISION}`,
      * `/moveable-aliases/${MOVEABLE_ALIAS}`,
      * `/fixed-aliases/${FIXED_ALIAS}`.

      If you'd like to deploy sources from a directory different from the root,
      you must specify a revision, a moveable alias, or a fixed alias, as above,
      and append `/paths/${PATH_TO_SOURCES_DIRECTORY}` to the URL.

      Overall, the URL should match the following regular expression:

      ```
      ^https://source\\.developers\\.google\\.com/projects/
      (?<accountId>[^/]+)/repos/(?<repoName>[^/]+)
      (((/revisions/(?<commit>[^/]+))|(/moveable-aliases/(?<branch>[^/]+))|
      (/fixed-aliases/(?<tag>[^/]+)))(/paths/(?<path>.*))?)?$
      ```

      An example of a validly formatted source repository URL is:

      ```
      https://source.developers.google.com/projects/123456789/repos/testrepo/
      moveable-aliases/alternate-branch/paths/path-to=source
      ```

      """)


def AddStageBucketFlag(parser):
  """Add flag for specifying stage bucket to the parser."""
  parser.add_argument(
      '--stage-bucket',
      help=('When deploying a function from a local directory, this flag\'s '
            'value is the name of the Google Cloud Storage bucket in which '
            'source code will be stored. Note that if you set the '
            '`--stage-bucket` flag when deploying a function, you will need to '
            'specify `--source` or `--stage-bucket` in subsequent deployments '
            'to update your source code. To use this flag successfully, the '
            'account in use must have permissions to write to this bucket. For '
            'help granting access, refer to this guide: '
            'https://cloud.google.com/storage/docs/access-control/'),
      type=api_util.ValidateAndStandarizeBucketUriOrRaise)


def AddRuntimeFlag(parser):
  # TODO(b/110148388): Do not hardcode list of choices in the help text.
  parser.add_argument(
      '--runtime',
      help="""\
          Runtime in which to run the function.

          Required when deploying a new function; optional when updating
          an existing function.

          Choices:

          - `nodejs10`: Node.js 10
          - `nodejs12`: Node.js 12
          - `nodejs14`: Node.js 14
          - `nodejs16`: Node.js 16 (preview)
          - `php74`: PHP 7.4
          - `python37`: Python 3.7
          - `python38`: Python 3.8
          - `python39`: Python 3.9
          - `go111`: Go 1.11
          - `go113`: Go 1.13
          - `go116`: Go 1.16 (preview)
          - `java11`: Java 11
          - `dotnet3`: .NET Framework 3
          - `ruby26`: Ruby 2.6
          - `ruby27`: Ruby 2.7
          - `nodejs6`: Node.js 6 (deprecated)
          - `nodejs8`: Node.js 8 (deprecated)
          """)


def AddVPCConnectorMutexGroup(parser):
  """Add flag for specifying VPC connector to the parser."""
  mutex_group = parser.add_group(mutex=True)
  mutex_group.add_argument(
      '--vpc-connector',
      help="""\
        The VPC Access connector that the function can connect to. It can be
        either the fully-qualified URI, or the short name of the VPC Access
        connector resource. If the short name is used, the connector must
        belong to the same project. The format of this field is either
        `projects/${PROJECT}/locations/${LOCATION}/connectors/${CONNECTOR}`
        or `${CONNECTOR}`, where `${CONNECTOR}` is the short name of the VPC
        Access connector.
      """)
  mutex_group.add_argument(
      '--clear-vpc-connector',
      action='store_true',
      help="""\
        Clears the VPC connector field.
      """)


def AddBuildWorkerPoolMutexGroup(parser):
  """Add flag for specifying Build Worker Pool to the parser."""
  mutex_group = parser.add_group(mutex=True)
  mutex_group.add_argument(
      '--build-worker-pool',
      help="""\
        Name of the Cloud Build Custom Worker Pool that should be used to build
        the function. The format of this field is
        `projects/${PROJECT}/locations/${LOCATION}/workerPools/${WORKERPOOL}`
        where ${PROJECT} is the project id and ${LOCATION} is the location where
        the worker pool is defined and ${WORKERPOOL} is the short name of the
        worker pool.
      """)
  mutex_group.add_argument(
      '--clear-build-worker-pool',
      action='store_true',
      help="""\
        Clears the Cloud Build Custom Worker Pool field.
      """)


def AddEntryPointFlag(parser):
  """Add flag for specifying entry point to the parser."""
  parser.add_argument(
      '--entry-point',
      help="""\
      Name of a Google Cloud Function (as defined in source code) that will
      be executed. Defaults to the resource name suffix, if not specified. For
      backward compatibility, if function with given name is not found, then
      the system will try to use function named "function". For Node.js this
      is name of a function exported by the module specified in
      `source_location`.
""")


def AddMaxInstancesFlag(parser):
  """Add flag for specifying the max instances for a function."""
  mutex_group = parser.add_group(mutex=True)
  mutex_group.add_argument(
      '--max-instances',
      type=arg_parsers.BoundedInt(lower_bound=1),
      help="""\
        Sets the maximum number of instances for the function. A function
        execution that would exceed max-instances times out.
      """)
  mutex_group.add_argument(
      '--clear-max-instances',
      action='store_true',
      help="""\
        Clears the maximum instances setting for the function.
      """)


def AddMinInstancesFlag(parser):
  """Add flag for specifying the min instances for a function."""
  mutex_group = parser.add_group(mutex=True)
  mutex_group.add_argument(
      '--min-instances',
      type=arg_parsers.BoundedInt(lower_bound=0),
      help="""\
        Sets the minimum number of instances for the function. This is helpful
        for reducing cold start times. Defaults to zero.
      """)
  mutex_group.add_argument(
      '--clear-min-instances',
      action='store_true',
      help="""\
        Clears the minimum instances setting for the function.
      """)


def AddTriggerFlagGroup(parser, track=None):
  """Add arguments specifying functions trigger to the parser.

  Args:
    parser: the argparse parser for the command.
    track: base.ReleaseTrack, calliope release track.
  """
  trigger_flags = ['--trigger-topic', '--trigger-bucket', '--trigger-http']
  gen2_tracks = [base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA]
  if not _ShouldHideV2Flags(track):
    trigger_flags.append('--trigger-event-filters')
  formatted_trigger_flags = ', '.join(['`{}`'.format(f) for f in trigger_flags])

  trigger_group = parser.add_mutually_exclusive_group(
      help=('If you don\'t specify a trigger when deploying an update to an '
            'existing function it will keep its current trigger. '
            'You must specify {formatted_trigger_flags} or '
            '(`--trigger-event` AND `--trigger-resource`) when deploying a '
            'new function.'.format(
                formatted_trigger_flags=formatted_trigger_flags)))
  trigger_group.add_argument(
      '--trigger-topic',
      help=('Name of Pub/Sub topic. Every message published in this topic '
            'will trigger function execution with message contents passed as '
            'input data. Note that this flag does not accept the format of '
            'projects/PROJECT_ID/topics/TOPIC_ID. Use this flag to specify the '
            'final element TOPIC_ID. The PROJECT_ID will be read from the '
            'active configuration.'),
      type=api_util.ValidatePubsubTopicNameOrRaise)
  trigger_group.add_argument(
      '--trigger-bucket',
      help=('Google Cloud Storage bucket name. Every change in files in this '
            'bucket will trigger function execution.'),
      type=api_util.ValidateAndStandarizeBucketUriOrRaise)
  trigger_group.add_argument(
      '--trigger-http',
      action='store_true',
      help="""\
      Function will be assigned an endpoint, which you can view by using
      the `describe` command. Any HTTP request (of a supported type) to the
      endpoint will trigger function execution. Supported HTTP request
      types are: POST, PUT, GET, DELETE, and OPTIONS.""")
  if track in gen2_tracks:
    trigger_group.add_argument(
        '--trigger-event-filters',
        type=arg_parsers.ArgDict(),
        action=arg_parsers.UpdateAction,
        hidden=_ShouldHideV2Flags(track),
        metavar='ATTRIBUTE=VALUE',
        help=(
            'The Eventarc matching criteria for the trigger. The criteria can '
            'be specified either as a single comma-separated argument or as '
            'multiple arguments. This is only relevant when `--gen2` is provided.'
        ),
    )

  trigger_provider_spec_group = trigger_group.add_argument_group()
  # check later as type of applicable input depends on options above
  trigger_provider_spec_group.add_argument(
      '--trigger-event',
      metavar='EVENT_TYPE',
      help=('Specifies which action should trigger the function. For a '
            'list of acceptable values, call '
            '`gcloud functions event-types list`.'))
  trigger_provider_spec_group.add_argument(
      '--trigger-resource',
      metavar='RESOURCE',
      help=('Specifies which resource from `--trigger-event` is being '
            'observed. E.g. if `--trigger-event` is  '
            '`providers/cloud.storage/eventTypes/object.change`, '
            '`--trigger-resource` must be a bucket name. For a list of '
            'expected resources, call '
            '`gcloud functions event-types list`.'),
  )


class LocationsCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(LocationsCompleter, self).__init__(
        collection=LOCATIONS_COLLECTION,
        list_command='alpha functions regions list --uri',
        **kwargs)


def AddRegionFlag(parser, help_text):
  parser.add_argument(
      '--region',
      help=help_text,
      completer=LocationsCompleter,
      action=actions.StoreProperty(properties.VALUES.functions.region),
  )


def RegionAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='region',
      help_text=(
          'The Cloud region for the {resource}. Overrides the default '
          '`functions/region` property value for this command invocation.'),
      completer=LocationsCompleter,
      fallthroughs=[
          deps.PropertyFallthrough(properties.VALUES.functions.region),
      ],
  )


def AddTriggerLocationFlag(parser, track):
  """Add flag for specifying trigger location to the parser."""
  parser.add_argument(
      '--trigger-location',
      hidden=_ShouldHideV2Flags(track),
      help=('The location of the trigger, which must be a region or multi-'
            'region where the relevant events originate. This is only '
            'relevant when `--gen2` is provided.'),
      completer=LocationsCompleter,
  )


def FunctionAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='function',
      help_text='The Cloud functon name.',
      value_type=api_util.ValidateFunctionNameOrRaise,
  )


def GetFunctionResourceSpec():
  return concepts.ResourceSpec(
      'cloudfunctions.projects.locations.functions',
      resource_name='function',
      disable_auto_completers=False,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=RegionAttributeConfig(),
      functionsId=FunctionAttributeConfig(),
  )


def AddFunctionResourceArg(parser, verb, positional=True):
  """Adds a Cloud function resource argument.

  NOTE: May be used only if it's the only resource arg in the command.

  Args:
    parser: the argparse parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, if True, means that the instance ID is a positional rather
      than a flag.
  """
  name = 'NAME' if positional else '--function'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetFunctionResourceSpec(),
      'The Cloud function name {}.'.format(verb),
      required=True).AddToParser(parser)


def AddServiceAccountFlag(parser):
  parser.add_argument(
      '--service-account',
      help="""\
      The email address of the IAM service account associated with the
      function at runtime. The service account represents the identity of the
      running function, and determines what permissions the function has.

      If not provided, the function will use the project's default service
      account.
      """)


def AddRunServiceAccountFlag(parser, track):
  parser.add_argument(
      '--run-service-account',
      hidden=_ShouldHideV2Flags(track),
      help="""\
      The email address of the IAM service account associated with the Cloud
      Run service for the function. The service account represents the identity
      of the running function, and determines what permissions the function
      has.

      If not provided, the function will use the project's default service
      account for Compute Engine.

      This is only relevant when `--gen2` is provided.
      """)


def AddTriggerServiceAccountFlag(parser, track):
  parser.add_argument(
      '--trigger-service-account',
      hidden=_ShouldHideV2Flags(track),
      help="""\
      The email address of the IAM service account associated with the Eventarc
      trigger for the function. This is used for authenticated invocation.

      If not provided, the function will use the project's default service
      account for Compute Engine.

      This is only relevant when `--gen2` is provided.
      """)


def AddDataFlag(parser):
  parser.add_argument(
      '--data',
      help="""JSON string with data that will be passed to the function.""")


def AddCloudEventsFlag(parser, track):
  parser.add_argument(
      '--cloud-event',
      hidden=_ShouldHideV2Flags(track),
      help="""
      JSON encoded string with a CloudEvent in structured content mode.

      Mutually exclusive with --data flag.

      Use for Cloud Functions V2 CloudEvent functions. The CloudEvent
      object will be sent to your function as a binary content mode message with
      the top-level 'data' field set as the HTTP body and all other JSON fields
      sent as HTTP headers.
      """)


def AddIAMPolicyFileArg(parser):
  parser.add_argument(
      'policy_file',
      metavar='POLICY_FILE',
      help='Path to a local JSON or YAML formatted file '
      'containing a valid policy.')


def AddIgnoreFileFlag(parser):
  parser.add_argument(
      '--ignore-file',
      help='Override the .gcloudignore file and use the specified file instead.'
  )


def AddSignatureTypeFlag(parser, track):
  base.ChoiceArgument(
      '--signature-type',
      choices=SIGNATURE_TYPES,
      hidden=_ShouldHideV2Flags(track),
      help_str=(
          'The type of event signature for the function. `http` '
          'indicates that the function is triggered by HTTP requests. '
          '`event` indicates that the function consumes legacy events. '
          '`cloudevent` indicates that the function consumes events in '
          'the new CloudEvent format. This is only relevant when `--gen2` '
          'is provided.'),
  ).AddToParser(parser)


# Flags for CMEK
def AddKMSKeyFlags(parser):
  """Adds flags for configuring the CMEK key."""
  kmskey_group = parser.add_group(mutex=True)
  kmskey_group.add_argument(
      '--kms-key',
      type=arg_parsers.RegexpValidator(_KMS_KEY_NAME_PATTERN,
                                       _KMS_KEY_NAME_ERROR),
      help="""\
        Sets the user managed KMS crypto key used to encrypt the Cloud Function
        and its resources.

        The KMS crypto key name should match the pattern
        `projects/${PROJECT}/locations/${LOCATION}/keyRings/${KEYRING}/cryptoKeys/${CRYPTOKEY}`
        where ${PROJECT} is the project, ${LOCATION} is the location of the key
        ring, and ${KEYRING} is the key ring that contains the ${CRYPTOKEY}
        crypto key.

        If this flag is set, then a Docker repository created in Artifact
        Registry must be specified using the `--docker-repository` flag and the
        repository must be encrypted using the `same` KMS key.
      """)
  kmskey_group.add_argument(
      '--clear-kms-key',
      action='store_true',
      help="""\
        Clears the KMS crypto key used to encrypt the function.
      """)


def AddDockerRepositoryFlags(parser):
  """Adds flags for configuring the Docker repository for Cloud Function."""
  kmskey_group = parser.add_group(mutex=True)
  kmskey_group.add_argument(
      '--docker-repository',
      type=arg_parsers.RegexpValidator(_DOCKER_REPOSITORY_NAME_PATTERN,
                                       _DOCKER_REPOSITORY_NAME_ERROR),
      help="""\
        Sets the Docker repository to be used for storing the Cloud Function's
        Docker images while the function is being deployed. `DOCKER_REPOSITORY`
        must be an Artifact Registry Docker repository present in the `same`
        project and location as the Cloud Function.

        The repository name should match the pattern
        `projects/${PROJECT}/locations/${LOCATION}/repositories/${REPOSITORY}`
        where ${PROJECT} is the project, ${LOCATION} is the location of the
        repository and ${REPOSITORY} is a valid repository ID.
      """)
  kmskey_group.add_argument(
      '--clear-docker-repository',
      action='store_true',
      help="""\
        Clears the Docker repository configuration of the function.
      """)
