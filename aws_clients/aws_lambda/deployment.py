import itertools
import logging
import os
import shutil
import subprocess
import tempfile
import zipfile
from distutils.sysconfig import get_python_lib

import boto3
from botocore.exceptions import ClientError
from git import Repo

logger = logging.getLogger("AWSLambda")

LIB_DIRS = (
    "/lib/", "/lib64/",
    "/usr/lib/", "/usr/lib64/",
    "/usr/lib/x86_64-linux-gnu/",
    "/lib/x86_64-linux-gnu/"
)


class LambdaPackage(object):
    def __init__(self, aws_lambda_config, repository=None):
        self.workspace = tempfile.mkdtemp()
        self.zipfile = os.path.join(self.workspace, 'lambda.zip')
        self.pkg_venv = os.path.join(self.workspace, 'env')
        self.venv_pip = 'bin/pip'
        self.repo = repository or '.'
        self.requirements = (aws_lambda_config.pop('binary_requirements') if
                             'binary_requirements' in aws_lambda_config else None)
        self.lambda_config = aws_lambda_config

    def create_deployment_package(self):
        self.add_env_libs_and_src()
        self.add_shared_lib(self.requirements)
        self.add_recompiled_libs(self.requirements)
        self.create_zip_package()
        return self.zipfile

    def add_env_libs_and_src(self):
        Repo(path=self.repo).clone(path=self.workspace)
        shutil.rmtree(os.path.join(self.workspace, '.git'))
        package_path = get_python_lib()
        self.__add_package_from_path(package_path)

    def add_shared_lib(self, requirements):
        if requirements:
            so_dir = os.path.join(self.workspace, 'lib')
            os.mkdir(so_dir)
            so_files = []
            for lib_dir in LIB_DIRS:
                if os.path.isdir(lib_dir):
                    modules = [os.path.join(lib_dir, path)
                               for path in os.listdir(lib_dir)]
                    for module in modules:
                        for shared_object in itertools.chain(
                                requirements.values()
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

    def add_recompiled_libs(self, requirements):
        if requirements:
            subprocess.call(['virtualenv {}'.format(self.pkg_venv)], shell=True)
            subprocess.call(['find . -name "*.pyc" -exec rm -rf {} \\;'],
                            shell=True)
            for package in requirements.keys():
                cmd = [os.path.join(self.pkg_venv, self.venv_pip), ]
                cmd.append(' install --upgrade --force-reinstall ')
                cmd.extend(('--global-option=build_ext',
                            '--global-option="--rpath=/var/task/lib"'))
                cmd.append(package)
                subprocess.call([' '.join(cmd)], shell=True)

            self.__add_package_from_path(
                os.path.join(self.pkg_venv, 'lib/python2.7/site-packages')
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

    def create_zip_package(self):
        zip_file = zipfile.ZipFile(self.zipfile, "w", zipfile.ZIP_DEFLATED)
        abs_src = os.path.abspath(self.workspace)
        for root, _, files in os.walk(self.workspace):
            for filename in files:
                absname = os.path.abspath(os.path.join(root, filename))
                arcname = absname[len(abs_src) + 1:]
                zip_file.write(absname, arcname)
        zip_file.close()


class Deployer(object):
    def __init__(
            self,
            aws_lambda_config,
            aws_lambda_client,
            version=None,
            repository=None
    ):
        """
        :param aws_lambda_config:
        Sample lambda config:

        [  'function_1': {  # function name
                 'role_name':'lambda_basic_execution', # IAM role for lambda
                 'handler': 'lambda_module.function_1',  # handler, must receive event  and context as argument
                 'shedule_expression': "rate(5 minutes)", # set for periodic lambda call
                 'memory_size': 128,
                 'timeout': 60,

             },
             'binary_requirements':{
                    'psycopg2==2.5.3': ("libpq.so",)
             }
        ]
        :param aws_lambda_client:
        :type aws_clients.aws_lambda.LambdaClient
        """
        self.zipfile = LambdaPackage(aws_lambda_config, repository)
        self.client = aws_lambda_client
        self.lambda_config = aws_lambda_config
        self.version = version
        self.arns = {}

    def deploy(self):
        self.upload()
        self.set_shedule()
        # TODO: add SNS and S3 source

    def upload(self):
        for function_name, function_config in self.lambda_config.items():
            try:
                response = self.client.update_lambda_function_code(
                    function_name,
                    self.zipfile,
                    self.version
                )
            except ClientError:
                response = self.client.create_lambda_function(
                    function_name,
                    role_name=function_config['role_name'],
                    handler=function_config['handler'],
                    zip_file=self.zipfile,
                    timeout=function_config.get('timeout'),
                    memory_size=function_config.get('memory_size'),
                    version=self.version
                )
            self.arns[function_name] = response['FunctionArn']

    def set_shedule(self):
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
                        {'Id': 'b5b5e45d-87ad-491f-82f9-e387dd4bc247',
                         'Arn': self.arns[function_name]
                         }
                    ]
                )
                permission = dict(
                    FunctionName=function_name,
                    StatementId='b5b5e45d-87ad-491f-82f9-e387dd4bc247',
                    Action="lambda:InvokeFunction",
                    Principal="events.amazonaws.com",
                    SourceArn=response['RuleArn'],
                )

                try:
                    self.client.add_permission(**permission)
                except ClientError:
                    pass
