from botocore.client import Config

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
            timeout=60,
            memory_size=128,
            version=None
    ):
        """
        Create AWS Lambda function
        :param role_name: AWS Lambda function execution role
        :param handler:  handler function
        :param zip_file: source code package
        :param timeout: AWS Lambda execution timeout
        :param memory_size:  power of AWS Lambda instance
        :return:
        """

        iam = BaseAWSClient('iam', **self.instance.settings)
        role = iam.instance.Role(role_name)

        response = self.instance.create_function(
            FunctionName=function_name,
            Runtime='python2.7',
            Role=role.arn,
            Handler=handler,
            Code=dict(
                ZipFile=open(zip_file).read()
            ),
            Timeout=timeout,
            MemorySize=memory_size,
        )
        if version:
            self.publish_version_alias(
                function_name,
                version,
                response['CodeSha256']
            )

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
            iam = BaseAWSClient('iam', **self.settings)
            role = iam.instance.Role(role_name)
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
        response = self.instance.publish_version(
            FunctionName=function_name,
            CodeSha256=code_sha256
        )
        self.instance.create_alias(
            FunctionName=function_name,
            Name=version_name,
            FunctionVersion=response['Version'],
        )
