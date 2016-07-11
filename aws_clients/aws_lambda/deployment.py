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

binary_requirements = [

]

"""
Sample lambda config:

[  'function_1': {  # function name
         'role_name':'lambda_basic_execution', # IAM role for lambda
         'handler': 'lambda_module.function_1',  # handler, must receive event  and context as argument
         'shedule_expression': "rate(5 minutes)", # set for periodic lambda call
         'memory_size': 128,
         'timeout': 60,
         'binary_requirements':[
            {'psycopg2==2.5.3': ("libpq.so", "libssl.so", "libcrypto.so", "libjpeg.so")}
         ]

     },
]
"""


class Deployment(object):
    def __init__(
            self,
            aws_lambda_config,
            aws_lambda_client
    ):
        """
        :param aws_lambda_config:
        :param aws_lambda_client:
        :type aws_clients.aws_lambda.LambdaClient
        """
        self.workspace = tempfile.mkdtemp()
        self.zipfile = os.path.join(self.workspace, 'lambda.zip')
        self.pkg_venv = os.path.join(self.workspace, 'env')
        self.venv_pip = 'bin/pip'
        self.arns = {}
        self.repo = '.'
        self.lambda_config = aws_lambda_config
        self.client = aws_lambda_client
        """:type aws_clients.aws_lambda.LambdaClient """

    def add_env_libs_and_src(self):
        Repo(path=self.repo).clone(path=self.workspace)
        shutil.rmtree(os.path.join(self.workspace, '.git'))
        package_path = get_python_lib()
        self.__add_package_from_path(package_path)

    def add_shared_lib(self, requirements):
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

    def set_shedule(self):
        settings = self.client.settings
        client = boto3.client('events', **settings)
        for lambda_name, lambda_config in self.lambda_config.items():
            expression = lambda_config.get('shedule_expression')
            if expression:
                response = client.put_rule(
                    Name=lambda_name,
                    ScheduleExpression=expression,
                    State='ENABLED'
                )

                client.put_targets(
                    Rule=lambda_name,
                    Targets=[
                        {'Id': 'b5b5e45d-87ad-491f-82f9-e387dd4bc247',
                         'Arn': self.arns[lambda_name]
                         }
                    ]
                )
                permission = dict(
                    FunctionName=lambda_name,
                    StatementId='b5b5e45d-87ad-491f-82f9-e387dd4bc247',
                    Action="lambda:InvokeFunction",
                    Principal="events.amazonaws.com",
                    SourceArn=response['RuleArn'],
                )

                try:
                    self.client.add_permission(**permission)
                except ClientError:
                    pass

    #TODO: add SNS and S3 source

    def upload(self, function_name):
        try:
            self.client.update_function_code()
        except ClientError:
            self.client
        iam = boto3.resource('iam', **self.client.settings)
        role = iam.Role(role_name)

        for lambda_name, lambda_config in self.lambda_config.items():
            try:
                response = self.client.update_function_code(
                    FunctionName=lambda_name,
                    ZipFile=open(self.zipfile).read(),
                )
            except ClientError:
                response = self.client.create_function(
                    FunctionName=lambda_name,
                    Runtime='python2.7',
                    Role=role.arn,
                    Handler=lambda_config.get('handler'),
                    Code=dict(
                        ZipFile=open(self.zipfile).read()
                    ),
                    Timeout=lambda_config.get('timeout', 60),
                    MemorySize=lambda_config.get('memory_size', 1024),

                )

            lambda_arn = response['FunctionArn']
            self.arns[lambda_name] = lambda_arn
            print "Lambda ARN {}".format(lambda_arn)
