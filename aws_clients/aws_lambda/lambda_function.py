import json
import logging
import time

from botocore.exceptions import ClientError

from aws_clients.aws_client import BaseAWSClientException
from .client import LambdaClient

logger = logging.getLogger("AWSLambda")


class LambdaFunctionNotFound(BaseAWSClientException):
    pass


class LambdaFunction(object):
    """
        AWS Lambda wrapper
    """

    def __init__(self,
                 function_name,
                 region_name,
                 aws_access_key_id,
                 aws_secret_access_key,
                 version=None):
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
        self.version = version
        try:
            response = self.client.instance.get_function(
                FunctionName=function_name,
            )
            self.function_arn = response.get('Configuration', {}).get(
                'FunctionArn'
            )
        except ClientError as exc:
            logger.exception("[AWS Lambda] {}".format(exc.message))
            raise LambdaFunctionNotFound

    def __call__(self, payload, async=True):
        """
        :param payload: payload object, must be json serializable
        :param async: Flag for async call
        :return: None for async call or AWS Lambda function result
        """

        invocation = "Event" if async else "RequestResponse"
        start_time = time.time()
        kwargs = dict(
            FunctionName=self.function_name,
            Payload=json.dumps(payload),
            InvocationType=invocation
        )
        if self.version:
            kwargs.update(Qualifier=self.version)

        response = self.client.instance.invoke(**kwargs)
        logger.info("[AWS Lambda]Lambda)invoking time %s",
                    str(time.time() - start_time))
        if not async and 'Payload' in response:
            result = response['Payload'].read()
            logger.info('[AWS Lambda]Receive result %s', str((result)))
            return result
