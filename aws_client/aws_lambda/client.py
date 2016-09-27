from __future__ import unicode_literals

import hashlib
import logging

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from ..base_client import BaseAWSClient

LOGGER = logging.getLogger(__name__)


class LambdaClient(BaseAWSClient):
    """
    AWS Lambda client
    """

    def __init__(
            self,
            region_name,
            aws_access_key_id,
            aws_secret_access_key
    ):
        """

        :param region_name: AWS region name
        :param aws_access_key_id:  AWS credentials
        :param aws_secret_access_key: AWS credentials
        """

        super(LambdaClient, self).__init__(
            service='lambda',
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            config=Config(read_timeout=300)
        )

    def create_lambda_function(
            self,
            function_name,
            role_name,
            handler,
            zip_file,
            timeout,
            memory_size,
            version=None
    ):
        """
        Create AWS Lambda function
        :param role_name: AWS Lambda function execution role
        :param handler:  handler function
        :param zip_file: source code package filepath
        :param timeout: AWS Lambda execution timeout
        :param memory_size:  power of AWS Lambda instance
        :return:
        """

        LOGGER.info('Create lambda_function `%s`', function_name)
        iam = boto3.resource('iam', **self.settings)
        role = iam.Role(role_name)

        LOGGER.info('Role arn `%s`', role.arn)
        response = self.instance.create_function(
            FunctionName=function_name,
            Runtime='python2.7',
            Role=role.arn,
            Handler=handler,
            Code=dict(
                ZipFile=open(zip_file).read()
            ),
            Timeout=timeout or 60,
            MemorySize=memory_size or 128,
        )
        if version:
            LOGGER.info('Publish version with alias `%s`', version)
            self.publish_version_alias(
                function_name,
                version,
                response['CodeSha256']
            )
        return response['FunctionArn']

    def update_lambda_function_code(self, function_name, zip_file,
                                    version=None):
        """
        Update AWS Lambda function code from zip package
        :param zip_file: source code package
        :return:
        """
        LOGGER.info('Update function code `%s`', function_name)
        response = self.instance.update_function_code(
            FunctionName=function_name,
            ZipFile=open(zip_file).read(),
        )
        if version:
            LOGGER.info('Publish version with alias `%s`', version)
            self.publish_version_alias(
                function_name,
                version,
                response['CodeSha256']
            )
        return response['FunctionArn']

    def update_lambda_function_config(
            self,
            function_name,
            role_name=None,
            memory_size=None,
            timeout=None,
            handler=None,

    ):
        """
        Update AWS Lambda function config
        :param role_name: AWS Lambda function execution role
        :param handler:  handler function
        :param timeout: AWS Lambda execution timeout
        :param memory_size:  power of AWS Lambda instance
        """
        LOGGER.info('Update function configuration `%s`', function_name)
        kwargs = dict(
            FunctionName=function_name
        )
        if role_name:
            iam = boto3.resource('iam', **self.settings)
            role = iam.Role(role_name)
            kwargs.update(
                Role=role.arn
            )
        if memory_size:
            kwargs.update(
                MemorySize=memory_size
            )
        if timeout:
            kwargs.update(
                Timeout=timeout
            )
        if handler:
            kwargs.update(
                Handler=handler
            )
        if len(kwargs.keys()) > 1:
            self.instance.update_function_configuration(
                **kwargs
            )

    def delete_lambda_function(self, function_name):
        """
        Delete AWS Lamda function
        :return:
        """
        LOGGER.info('Delete function  `%s`', function_name)
        self.instance.delete_function(
            FunctionName=function_name
        )

    def publish_version_alias(self, function_name, version_name, code_sha256):
        """
        Publish AWS Lambda function with alias
        :param function_name:
        :param version_name:
        :param code_sha256:
        :return:
        """
        try:
            self.instance.delete_alias(
                FunctionName=function_name,
                Name=version_name,
            )
        except ClientError:
            pass
        response = self.instance.publish_version(
            FunctionName=function_name,
            CodeSha256=code_sha256
        )
        self.instance.create_alias(
            FunctionName=function_name,
            Name=version_name,
            FunctionVersion=response['Version'],
        )

    def get_function_arn(self, function_name, version=None):
        """
        Return function AWS ARN
        :param function_name: name
        :type str
        :param version: version
        :type str
        :return:
        """
        kwargs = dict(
            FunctionName=function_name

        )
        if version:
            kwargs.update(Qualifier=version)

        response = self.instance.get_function(**kwargs)
        return response['FunctionArn']

    def add_api_gateway_invoke_permission(self, function_name):
        """
        :param function_name: Lambda function name
        :return:
        """
        LOGGER.info('Add API Gateway permission `%s`', function_name)
        permission = dict(
            FunctionName=function_name,
            StatementId=hashlib.sha256(function_name).hexdigest(),
            Action="aws_lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
        )
        self.instance.add_permission(**permission)

    def add_s3_invoke_permission(self, function_name, bucket_name):
        """
        :param function_name: Lambda function name
        :param bucket_name:  S3 bucket name
        :return:
        """
        LOGGER.info('Add S3 permission `%s`', function_name)
        permission = dict(
            FunctionName=function_name,
            StatementId=hashlib.sha256(
                function_name + bucket_name
            ).hexdigest(),
            Action="aws_lambda:InvokeFunction",
            Principal="s3.amazonaws.com",
            SourceArn="arn:aws:s3:::{}".format(bucket_name),
        )
        self.instance.add_permission(**permission)

    def add_sns_invoke_permission(self, function_name):
        """
        :param function_name:  Lambda function name
        :return:
        """
        LOGGER.info('Add SNS permission `%s`', function_name)
        permission = dict(
            FunctionName=function_name,
            StatementId=hashlib.sha256(function_name).hexdigest(),
            Action="aws_lambda:InvokeFunction",
            Principal="sns.amazonaws.com",
        )
        self.instance.add_permission(**permission)
