from __future__ import unicode_literals

import json

from botocore.exceptions import ClientError

from ..base_client import BaseAWSClient


class SQSClient(BaseAWSClient):
    """AWS SQS client"""

    def __init__(self,
                 region_name,
                 aws_access_key_id,
                 aws_secret_access_key,
                 endpoint_url=None
                 ):
        """
        :param region_name: AWS region name
        :param aws_access_key_id:  AWS credentials
        :param aws_secret_access_key: AWS credentials
        """
        self.__urls = {}
        settings = dict(
            service='sqs',
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        if endpoint_url:
            settings.update(
                endpoint_url=endpoint_url
            )
        super(SQSClient, self).__init__(
            **settings
        )

    def create_queue(
            self,
            queue_name,
            retention_time=345600,
            visibility_timeout=300,
            delay_seconds=0,
            dead_letter_queue=None,
            max_receive_count=None
    ):
        """
        :param queue_name: name of SQS queue
        :type str
        :param retention_time: life time for sqs task in  queue
        :type int
        :param visibility_timeout: time of lock for  another clients
        :type int
        :param delay_seconds: delay before new task stay visible in queue
        :type int
        :dead_queue_letter: dead_letter_queue_name
        :type str
        :param max_receive_count: value between 1 and 1,000
        :type int
        """

        response = self.instance.list_queues()

        for url in response.get('QueueUrls', []):
            if url.split('/')[-1] == queue_name:
                break
        else:
            kwargs = dict(
                QueueName=queue_name,
                Attributes=dict(
                    DelaySeconds=str(delay_seconds),
                    MessageRetentionPeriod=str(retention_time),
                    VisibilityTimeout=str(visibility_timeout)
                ))

            if dead_letter_queue and max_receive_count:
                dead_letter_queue_arn = self.instance.get_queue_attributes(
                    QueueUrl=self.get_queue_url(dead_letter_queue),
                    AttributeNames=['QueueArn']
                ).get('Attributes', {}).get("QueueArn")
                kwargs.setdefault('Attributes', {}).update(
                    RedrivePolicy=json.dumps(dict(
                        deadLetterTargetArn=dead_letter_queue_arn,
                        maxReceiveCount=max_receive_count
                    ))
                )
            self.instance.create_queue(**kwargs)

    def get_queue_url(self, queue_name):
        """
        :param queue_name:
        :type str
        :return: queue url
        :rtype str
        """
        if queue_name not in self.__urls or not self.__urls[queue_name]:
            try:
                self.__urls[queue_name] = self.instance.get_queue_url(
                    QueueName=queue_name
                ).get('QueueUrl')
            except ClientError:
                self.__urls[queue_name] = None
            # workaround https://github.com/boto/boto3/issues/630
            if self.__urls[queue_name]:
                self.__urls[queue_name] = self.__urls[queue_name].replace(
                    "queue.amazonaws.com",
                    "sqs.{}.amazonaws.com".format(
                        self.settings['region_name']
                    )
                )
        return self.__urls.get(queue_name)
