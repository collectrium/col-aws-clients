from __future__ import unicode_literals

import distutils
import hashlib
import logging
import os
import shutil
import subprocess
import tempfile
import zipfile
from random import choice
from string import ascii_lowercase

import boto3
from botocore.exceptions import ClientError
from git import Repo

from ..aws_lambda.client import LambdaClient
from ..s3.client import S3Client

LIB_DIRS = (
    "/lib/", "/lib64/",
    "/usr/lib/", "/usr/lib64/",
    "/usr/lib/x86_64-linux-gnu/",
    "/lib/x86_64-linux-gnu/"
)

LOGGER = logging.getLogger(__name__)


class LambdaPackage(object):
    """
    Helper to generate code package
    """

    def __init__(self, aws_lambda_config, repository=None):
        """

        :param aws_lambda_config:
         Sample aws_lambda config:

        [  'function_1': {  # function name
                 'role_name':'lambda_basic_execution', # IAM role for aws_lambda
                 'handler': 'lambda_module.function_1',  # handler
                 'shedule_expression': "rate(5 minutes)", # set for periodic
                 'event_sources':{
                    'api_gateway':{},
                    's3':{'bucket': 'test', 'prefix':'upload'},
                    'sns':{}

                 },
                 'memory_size': 128,
                 'timeout': 60,

             },
             'binary_requirements':{
                    'psycopg2==2.5.3': ("libpq.so",)
             },
             'ignored_packages': ('tests', 'testlib', 'debug')
        ]
        :type list
        :param repository:
        :type str
        """
        self.workspace = os.path.join(tempfile.gettempdir(), (''.join(choice(
            ascii_lowercase) for _ in range(10))))

        LOGGER.info('Create workspace `{}`'.format(self.workspace))
        self.zip_file = os.path.join(tempfile.gettempdir(), 'lambda.zip')
        self.repository = repository or '.'
        LOGGER.info('Repository `{}`'.format(self.repository))
        self.requirements = (aws_lambda_config.pop('binary_requirements')
                             if 'binary_requirements' in aws_lambda_config
                             else None)
        self.ignored_packages = (aws_lambda_config.pop('ignored_packages')
                                 if 'ignored_packages' in aws_lambda_config
                                 else [])
        LOGGER.info('Ignored packages `{}`'.format(self.ignored_packages))
        self.lambda_config = aws_lambda_config

    def create_deployment_package(self, additional_files=None):
        """
        Create package
        :param additional_files: list of filepaths
        :type str
        :return:
        """
        self._add_env_libs_and_src()
        self._add_shared_lib(self.requirements)
        self._add_recompiled_libs(self.requirements)
        self._create_zip_package(additional_files)
        return self.zip_file

    def _add_env_libs_and_src(self):
        LOGGER.info('Add sources and libraries from current environment')
        Repo(path=self.repository).clone(path=self.workspace)
        shutil.rmtree(os.path.join(self.workspace, '.git'))
        package_path = distutils.sysconfig.get_python_lib()
        self.__add_package_from_path(package_path)
        for package in self.ignored_packages:
            try:
                shutil.rmtree(os.path.join(self.workspace, package))
            except OSError:
                pass

    def _add_shared_lib(self, requirements):
        if requirements:
            LOGGER.info('Add shared libraries')
            so_dir = os.path.join(self.workspace, 'lib')
            os.mkdir(so_dir)
            so_files = []
            for lib_dir in LIB_DIRS:
                if os.path.isdir(lib_dir):
                    modules = [os.path.join(lib_dir, path)
                               for path in os.listdir(lib_dir)]
                    for module in modules:
                        for shared_object in (
                                lib for libs
                                in requirements.values() for lib in libs
                        ):
                            if shared_object in module:
                                so_files.append(os.path.join(lib_dir, module))
            for shared_object in so_files:
                shutil.copy(
                    shared_object,
                    os.path.join(
                        self.workspace, 'lib', shared_object.split('/')[-1]
                    )
                )

    def _add_recompiled_libs(self, requirements):
        if requirements:
            LOGGER.info('Recompile and add binary requirements')
            pkg_venv = os.path.join(self.workspace, 'env')
            venv_pip = 'bin/pip'

            subprocess.call(['virtualenv {}'.format(pkg_venv)], shell=True)
            subprocess.call(['find . -name "*.pyc" -exec rm -rf {} \\;'],
                            shell=True)
            for package in requirements.keys():
                cmd = [os.path.join(pkg_venv, venv_pip), ]
                cmd.append(' install --upgrade --force-reinstall ')
                cmd.extend(('--global-option=build_ext',
                            '--global-option="--rpath=/var/task/lib"'))
                cmd.append(package)
                subprocess.call([' '.join(cmd)], shell=True)

            self.__add_package_from_path(
                os.path.join(pkg_venv, 'lib/python2.7/site-packages')
            )

    def __add_package_from_path(self, package_path):
        list_dir = [path for path in os.listdir(package_path)
                    if "-info" not in path and "egg" not in path]
        for path in list_dir:
            src = os.path.join(package_path, path)
            dst = os.path.join(self.workspace, path)
            if os.path.isdir(src):
                try:
                    shutil.rmtree(dst)
                except OSError:
                    pass
                shutil.copytree(src, dst)
            else:
                try:
                    os.remove(path)
                except OSError:
                    pass
                shutil.copy(src, dst)

    def _create_zip_package(self, additional_files):
        LOGGER.info('Pack files ')
        if additional_files:
            for file_path in additional_files:
                shutil.copyfile(file_path,
                                os.path.join(
                                    self.workspace, file_path.split('/')[-1]
                                ))
        zip_file = zipfile.ZipFile(self.zip_file, "w", zipfile.ZIP_DEFLATED)
        abs_src = os.path.abspath(self.workspace)
        for root, _, files in os.walk(self.workspace):
            for filename in files:
                absname = os.path.abspath(os.path.join(root, filename))
                arcname = absname[len(abs_src) + 1:]
                zip_file.write(absname, arcname)
        zip_file.close()


class LambdaDeployer(object):
    def __init__(
            self,
            aws_lambda_config,
            region_name,
            aws_access_key_id,
            aws_secret_access_key,
            version=None,
            zip_file=None
    ):
        """
        :param aws_lambda_config:
        Sample aws_lambda config:

        [  'function_1': {  # function name
                 'role_name':'lambda_basic_execution', # IAM role for aws_lambda
                 'handler': 'lambda_module.function_1',  # handler
                 'shedule_expression': "rate(5 minutes)", # set for periodic
                 'event_sources':{
                    'api_gateway':{},
                    's3':{'bucket': 'test', 'prefix':'upload'}
                    'sns':{}
                 },
                 'memory_size': 128,
                 'timeout': 60,

             },
             'binary_requirements':{
                    'psycopg2==2.5.3': ("libpq.so",)
             },
             'ignored_packages': ('tests', 'testlib', 'debug')
        ]
        :param region_name: AWS region
        :param aws_access_key_id:  AWS credentials
        :param aws_secret_access_key: AWS credentials
        :param version: AWS Lambda function version alias
        """
        self.zipfile = zip_file

        self.client = LambdaClient(region_name,
                                   aws_access_key_id,
                                   aws_secret_access_key)
        self.lambda_config = aws_lambda_config
        self.version = version
        self.arns = {}

    def deploy(self):
        """

        :return:
        """
        self._upload()
        self._set_shedule()
        self._add_permissions()
        self._add_triggers()

    def _upload(self):
        for function_name, function_config in self.lambda_config.items():
            try:
                function_arn = self.client.update_lambda_function_code(
                    function_name,
                    self.zipfile,
                    self.version
                )
            except ClientError:
                function_arn = self.client.create_lambda_function(
                    function_name,
                    role_name=function_config['role_name'],
                    handler=function_config['handler'],
                    zip_file=self.zipfile,
                    timeout=function_config.get('timeout'),
                    memory_size=function_config.get('memory_size'),
                    version=self.version
                )
            self.arns[function_name] = function_arn

    def _set_shedule(self):
        settings = self.client.settings
        client = boto3.client('events', **settings)
        for function_name, function_config in self.lambda_config.items():
            expression = function_config.get('shedule_expression')
            if expression:
                response = client.put_rule(
                    Name=function_name,
                    ScheduleExpression=expression,
                    State='ENABLED'
                )

                client.put_targets(
                    Rule=function_name,
                    Targets=[
                        {'Id': hashlib.sha256(function_name).hexdigest(),
                         'Arn': self.arns[function_name]
                         }
                    ]
                )
                permission = dict(
                    FunctionName=function_name,
                    StatementId=hashlib.sha256(function_name).hexdigest(),
                    Action="lambda:InvokeFunction",
                    Principal="events.amazonaws.com",
                    SourceArn=response['RuleArn'],
                )

                try:
                    self.client.instance.add_permission(**permission)
                except ClientError:
                    pass

    def _add_permissions(self):
        for function_name, function_config in self.lambda_config.items():
            event_sources = function_config.get('event_sources', None)
            try:
                if event_sources and 's3' in event_sources:
                    self.client.add_s3_invoke_permission(
                        function_name,
                        event_sources['s3']['bucket_name']
                    )

                elif event_sources and 'api_gateway' in event_sources:
                    self.client.add_api_gateway_invoke_permission(
                        function_name
                    )
                elif event_sources and 'sns' in event_sources:
                    self.client.add_sns_invoke_permission(function_name)
            except ClientError:
                pass

    def _add_triggers(self):
        s3 = None
        notifications_specs = {}
        for function_name, function_config in self.lambda_config.items():
            event_sources = function_config.get('event_sources', None)
            if event_sources and 's3' in event_sources:
                s3 = s3 or S3Client(
                    region_name=self.client.settings['region_name'],
                    aws_access_key_id=self.client.settings[
                        'aws_access_key_id'],
                    aws_secret_access_key=self.client.settings[
                        'aws_secret_access_key'
                    ],

                )
                notifications_specs.setdefault(
                    event_sources['s3']['bucket_name'], []).append(
                    {
                        'Events': ['s3:ObjectCreated:*', ],
                        'LambdaFunctionArn': self.arns[function_name],
                        'Filter': {
                            'Key': {
                                'FilterRules': [
                                    {
                                        'Name': 'prefix',
                                        'Value': event_sources['s3'][
                                            'prefix']
                                    },
                                ]
                            }
                        }
                    }
                )

        for bucket_name, configurations in notifications_specs.items():
            try:
                s3.instance.put_bucket_notification_configuration(
                    Bucket=bucket_name,
                    NotificationConfiguration={
                        'LambdaFunctionConfigurations': configurations
                    }
                )
            except ClientError:
                pass
