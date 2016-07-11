import json
import logging
import time

from botocore.client import Config
from botocore.exceptions import ClientError
from aws_clients.aws_client import BaseAWSClient, BaseAWSClientException

logger = logging.getLogger("AWSLambda")


class LambdaFunctionNotFound(BaseAWSClientException):
    pass


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
            memory_size=128
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

        self.instance.create_function(
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

    def update_lambda_function_code(self, function_name, zip_file, ):
        """
        Update AWS Lambda function code from zip package
        :param zip_file: source code package
        :return:
        """
        self.instance.update_function_code(
            FunctionName=function_name,
            ZipFile=open(zip_file).read(),
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


class LambdaFunction(object):
    """
        AWS Lambda wrapper
    """

    def __init__(self,
                 function_name,
                 region_name,
                 aws_access_key_id,
                 aws_secret_access_key):
        """
        :param function_name: AWS Lambda function name
        :type str
        :param region_name  AWS region
        :type str
        :param aws_access_key_id
        :type str
        :param aws_secret_access_key
        :type str
         :rtype str
        """
        self.client = LambdaClient(
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        self.function_name = function_name
        self.function_arn = None
        try:
            response = self.client.instance.get_function(
                FunctionName=function_name,
            )
            self.function_arn = response.get('Configuration', {}).get(
                'FunctionArn'
            )
        except ClientError as exc:
            logger.exception("[AWS Lambda] {}".format(exc.message))

    def __call__(self, payload, async=True):
        """
        :param payload: payload object, must be json serializable
        :param async: Flag for async call
        :return: None for async call or AWS Lambda function result
        """
        if not self.function_arn:
            raise LambdaFunctionNotFound
        invocation = "Event" if async else "RequestResponse"
        start_time = time.time()
        response = self.client.instance.invoke(
            FunctionName=self.function_name,
            Payload=json.dumps(payload),
            InvocationType=invocation
        )
        logger.info("[AWS Lambda]Lambda invoking time %s",
                    str(time.time() - start_time))
        if not async and 'Payload' in response:
            result = response['Payload'].read()
            logger.info('[AWS Lambda]Receive result %s', str((result)))
            return result


