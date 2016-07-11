import json

import boto3
from botocore.exceptions import ClientError

from aws_clients.aws_client import BaseAWSClient


class SQSClient(BaseAWSClient):
    """AWS SQS client"""


    def __init__(self,
                 region_name,
                 aws_access_key_id,
                 aws_secret_access_key):
        self.__urls = {}
        super(SQSClient, self).__init__(
            service='sqs',
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )


    def create_queue(self,
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
        :param visibility_timeout: time of lock for reading from another clients
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
                    )
                    )
                )
            self.instance.create_queue(**kwargs)


    def get_queue_url(self, queue_name):
        """
        :param queue_name:
        :type int
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


class SQSQueue(object):
    def __init__(self, queue_name,
                 region_name,
                 aws_access_key_id,
                 aws_secret_access_key,
                 auto_creation=False):
        """
        :param queue_name:
        """
        self.client = SQSClient(region_name,
                 aws_access_key_id,
                 aws_secret_access_key)
        self.queue_url = self.client.get_queue_url(queue_name)
        if not self.queue_url and auto_creation:
            self.client.create_queue(queue_name)
            self.queue_url = self.client.get_queue_url(queue_name)
        if hasattr(self.client, 'settings'):
            self.instance = boto3.resource(
                'sqs', **self.client.settings
            ).Queue(self.queue_url)
        else:
            self.instance = boto3.resource('sqs').Queue(self.queue_url)

    def get_queue_url(self):
        """
        :return: queue_url
         :rtype: str
        """
        return self.queue_url

    def purge(self):
        """
        Delete all messages from queue
        """
        self.instance.purge()

    def receive_messages(self, count=None, wait_timeout=None):
        """
        :param count: must be in range from 1 to 10
        :return: list of Message Object
        :rtype list
        """
        kwargs = dict(
            MaxNumberOfMessages=count
        ) if count else dict(MaxNumberOfMessages=1)
        if wait_timeout:
            kwargs.update(
                WaitTimeSeconds=wait_timeout
            )
        return self.instance.receive_messages(
            **kwargs
        )

    def send_messages(self, message):
        """
        Send messages to SQS
        :param message: one or list of messages string
        :return:
        """
        if not isinstance(message, list):
            message = [message, ]
        self.instance.send_messages(
            Entries=[
                dict(
                    MessageBody=json.dumps(msg) if not isinstance(
                        message, basestring) else msg,
                    Id=str(idx)

                ) for idx, msg in enumerate(message)

                ]
        )

    def delete_messages(self, receipt_handles):
        """
        Delete messages from queue
        :param receipt_handles:
        :rtype delete one or list of messages
        :return:
        """
        if not isinstance(receipt_handles, list):
            receipt_handles = [receipt_handles, ]
        self.instance.delete_messages(
            Entries=[
                dict(
                    ReceiptHandle=handle,
                    Id=str(idx)
                ) for idx, handle in enumerate(receipt_handles)
                ]
        )

    def get_queue_size(self):
        response = self.client.instance.get_queue_attributes(
            QueueUrl=self.queue_url,
            AttributeNames=['ApproximateNumberOfMessages']
        )
        return int(response.get('Attributes', {}).get(
            'ApproximateNumberOfMessages', '0')
        )
