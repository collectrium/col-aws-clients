import json

from aws_client.aws_lambda.client import LambdaClient
from ..base_client import BaseAWSClient


class SNSClient(BaseAWSClient):
    """AWS SNS client"""

    def __init__(self,
                 region_name,
                 aws_access_key_id,
                 aws_secret_access_key):
        """
        :param region_name: AWS region name
        :param aws_access_key_id:  AWS credentials
        :param aws_secret_access_key: AWS credentials
        """
        self.__arns = {}
        super(SNSClient, self).__init__(
            service='sns',
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

    def get_topic_arn(self, topic_name):
        """
        Get SNS topic AWS ARN
        :param topic_name: SNS topic name
        :return:
        """
        if topic_name not in self.__arns:
            response = self.instance.list_topics()
            exist = False
            if 'Topics' in response:
                for topic in response['Topics']:
                    if topic['TopicArn'].split(':')[-1] == topic_name:
                        self.__arns[topic_name] = topic['TopicArn']
                        exist = True
                        break
            if not exist:
                response = self.instance.create_topic(Name=topic_name)
                self.__arns[topic_name] = response['TopicArn']

        return self.__arns.get(topic_name)

    def publish(self, topic_name, message, protocol):
        """
        Publish message to topic
        :param topic_name: name of SNS topic
        :type str
        :param message: message object, must be JSON serializable
        :type str
        :param protocol: protocol type, it's
        define endpoint for SNS (AWS Lambda, SQS, HTTP and  etc)
        """
        message = json.dumps(
            {'default': 'stub message', protocol: json.dumps(message)})
        self.instance.publish(TopicArn=self.get_topic_arn(topic_name),
                              Message=message, MessageStructure='json')

    def subscribe_to_lambda(self, topic_name, function_name):
        """
        Subscribe AWS aws_lambda to topic
        :param topic_name: SNS topic name
        :type str
        :param function_name: aws_lambda function name
        :type str
        :return:
        """
        lambda_client = LambdaClient(**self.settings)
        self.instance.subscribe(
            TopicArn=self.get_topic_arn(topic_name),
            Protocol='aws_lambda',
            Endpoint=lambda_client.get_function_arn(function_name)
        )
