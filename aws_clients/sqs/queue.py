from __future__ import unicode_literals

import json

import boto3

from ..sqs.client import SQSClient


class SQSQueue(object):
    def __init__(self, queue_name,
                 region_name,
                 aws_access_key_id,
                 aws_secret_access_key,
                 auto_creation=False,
                 endpoint_url=None
                 ):
        """
        :param queue_name:
        """
        settings = {'region_name': region_name,
                    'aws_access_key_id': aws_access_key_id,
                    'aws_secret_access_key': aws_secret_access_key,
                    }
        if endpoint_url:
            settings.update(
                endpoint_url=endpoint_url
            )
        self.client = SQSClient(**settings)
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

    def send_messages(self, message, delay_timeout=None):
        """
        Send messages to SQS
        :param message: one or list of messages string
        :param delay_timeout
        :return:
        """
        if not isinstance(message, list):
            message = [message, ]
        entries = [
            dict(
                MessageBody=json.dumps(msg) if not isinstance(
                    message, basestring) else msg,
                Id=str(idx),

            ) for idx, msg in enumerate(message)]

        if delay_timeout:
            [entry.update(DelaySeconds=delay_timeout) for entry in entries]
        self.instance.send_messages(Entries=entries)

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
            'ApproximateNumberOfMessages', '0'))

    def get_queue_not_visible_number(self):
        response = self.client.instance.get_queue_attributes(
            QueueUrl=self.queue_url,
            AttributeNames=['ApproximateNumberOfMessagesNotVisible']
        )
        return int(response.get('Attributes', {}).get(
            'ApproximateNumberOfMessagesNotVisible', '0'))
