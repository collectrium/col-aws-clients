from __future__ import unicode_literals

import boto3

from col_aws_clients.aws_sns.client import SNSClient
from ..aws_client import BaseAWSClient


class ElasticTranscoderClient(BaseAWSClient):
    """
     AWS ElasticTranscoder  Service client
    """

    def __init__(self,
                 region_name,
                 aws_access_key_id,
                 aws_secret_access_key):
        """
        :param region_name: AWS region name
        :param aws_access_key_id: AWS credentials
        :param aws_secret_access_key: AWS credentials
        """
        super(ElasticTranscoderClient, self).__init__(
            service='elastictranscoder',
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

    def create_video_preset(
            self,
            preset_name,
            width=None,
            height=None,
            thumbnail_width=None,
            thumbnail_height=None,
    ):
        """
        Create video trnsforming presets
        :param preset_name: name
        :type str
        :param width: max output video width
        :type int
        :param height: max output video height
        :type int
        :param thumbnail_width: max thumbnail video width
        :type int
        :param thumbnail_height:  max thumbnail video height
        :type int
        :return:
        """
        response = self.instance.create_preset(
            Name=preset_name,
            Container='mp4',
            Video={
                'Codec': 'H.264',
                'MaxWidth': str(width) or '1920',
                'MaxHeight': str(height) or '1080',
                'SizingPolicy': 'ShrinkToFit',
            },
            Audio={
                'Codec': 'aac',
            },
            Thumbnails={
                'Format': 'png',
                'Interval': '60',
                'MaxWidth': str(thumbnail_width) or '480',
                'MaxHeight': str(thumbnail_height) or '270',
                'SizingPolicy': 'ShrinkToFit',
                'PaddingPolicy': 'NoPad'
            }
        )

    def create_pipeline(
            self,
            pipeline_name,
            bucket_name,
            role_name,
            progressing_sns_topic=None,
            completed_sns_topic=None,
            warning_sns_topic=None,
            error_sns_topic=None,
    ):
        """
        Create pipeline
        :param pipeline_name: name
        :type str
        :param bucket_name: working bucket name
        :type str
        :param role_name:  IAM role name for transcoding
        :type  str
          SNS topic for sending notifications
        :param progressing_sns_topic: for progressing
        :type str
        :param completed_sns_topic:  for completed
        :type str
        :param warning_sns_topic:  for warning
        :type str
        :param error_sns_topic:  for error
        :return:
        """
        iam = boto3.resource('iam', **self.settings)
        role = iam.Role(role_name)
        notifications = {}
        sns = SNSClient(**self.settings)
        if progressing_sns_topic:
            notifications['Progressing'] = sns.get_topic_arn(
                progressing_sns_topic
            )
        if completed_sns_topic:
            notifications['Completed'] = sns.get_topic_arn(
                completed_sns_topic
            )
        if warning_sns_topic:
            notifications['Warning'] = sns.get_topic_arn(
                warning_sns_topic
            )
        if error_sns_topic:
            notifications['Error'] = sns.get_topic_arn(
                error_sns_topic
            )
        kwargs = dict(
            Name=pipeline_name,
            InputBucket=bucket_name,
            Role=role.arn,
            ThumbnailConfig={u'Bucket': bucket_name, u'Permissions': []},
        )
        if notifications:
            kwargs.update(Notifications=notifications)

        self.instance.create_pipeline(**kwargs)
