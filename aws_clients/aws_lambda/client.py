import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from aws_clients.aws_client import BaseAWSClient


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

        :param region_name: AWS region
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

        iam = boto3.resource('iam', **self.settings)
        role = iam.Role(role_name)

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
        response = self.instance.update_function_code(
            FunctionName=function_name,
            ZipFile=open(zip_file).read(),
        )
        if version:
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

    def add_api_gateway_invoke_permission(self, function_name, ):
        """
        :param function_name:
        :return:
        """
        permission = dict(
            FunctionName=function_name+':development',
            StatementId="58f7cfba-2278-4583-baae-227c582c2023",
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
        )
        self.instance.add_permission(**permission)

    def add_s3_invoke_permission(self, function_name, bucket_name):
        permission = dict(
            FunctionName=function_name,
            StatementId='275fcfb4-9220-4f69-a069-915e258d11a0',
            Action="lambda:InvokeFunction",
            Principal="s3.amazonaws.com",
            SourceArn="arn:aws:s3:::{}".format(bucket_name),
        )
        self.instance.add_permission(**permission)
