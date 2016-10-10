from __future__ import unicode_literals

import boto3

from aws_client.sns.client import SNSClient
from ..base_client import BaseAWSClient


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
            width=1920,
            height=1080,
            thumbnail_width=480,
            thumbnail_height=270,
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

        if not self.get_preset_id(preset_name):
            self.instance.create_preset(
                Name=preset_name,
                Description='',
                Container='mp4',
                Video={
                    'Codec': 'H.264',
                    'MaxWidth': str(width) or '1920',
                    'MaxHeight': str(height) or '1080',
                    'SizingPolicy': 'ShrinkToFit',
                    'BitRate': 'auto',
                    'FrameRate': 'auto',
                    'PaddingPolicy': 'NoPad',
                    'DisplayAspectRatio': 'auto',
                    'FixedGOP': 'false',
                    'KeyframesMaxDist': '90',
                    'CodecOptions': {
                        'Profile': 'baseline',
                        'MaxReferenceFrames': '3',
                        'Level': '4',
                    }
                },
                Audio={
                    'Codec': 'AAC',
                    'Channels': 'auto',
                    'SampleRate': 'auto',
                    'BitRate': '160',
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
        if not self.get_pipeline_id(pipeline_name):
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
                ThumbnailConfig={'Bucket': bucket_name},
                ContentConfig={'Bucket': bucket_name},
            )
            if notifications:
                kwargs.update(Notifications=notifications)

            self.instance.create_pipeline(**kwargs)

    def get_pipeline_id(self, pipeline_name):
        """

        :param pipeline_name: pipeline name
        :return: pipeline id
        """
        response = self.instance.list_pipelines()
        ids = [
            pipeline['Id'] for pipeline in response['Pipelines']
            if pipeline['Name'] == pipeline_name
            ]
        return ids and ids[0] or None

    def get_preset_id(self, preset_name):
        """
        :param preset_name: name
        :return: preset id
        """
        response = self.instance.list_presets()
        ids = [
            preset['Id'] for preset in response['Presets']
            if preset['Name'] == preset_name
            ]
        return ids and ids[0] or None

    def create_job(self, pipeline_id, input_key, output_key, preset_id):
        """
        Create transcoding job
        :param pipeline_id: pipeline id
        :param input_key:
        :param output_key:
        :param preset:
        :return:
        """
        kwargs = dict(
            PipelineId=pipeline_id,
            Input={
                'Key': input_key,

            },
            Output={
                'Key': output_key,
                'ThumbnailPattern': "{}-{}".format(
                    output_key.rsplit('.', 1)[0], '{count}'
                ),
                'PresetId': preset_id,
            },
        )
        response = self.instance.create_job(**kwargs)
        return response['Job']['Id']

    def get_job_status(self, job_id):
        """
        :param job_id:
        :return:
        """
        response = self.instance.read_job(Id=job_id)['Job']
        return dict(
            status=response['Status'].lower(),
            runtime=response.get(
                'Input', {}
            ).get('DetectedProperties', {}).get('DurationMillis'),
            height_original=response.get(
                'Input', {}
            ).get('DetectedProperties', {}).get('Height'),
            width_original=response.get(
                'Input', {}
            ).get('DetectedProperties', {}).get('Width'),
            size_original=response.get(
                'Input', {}
            ).get('DetectedProperties', {}).get('FileSize'),
            size_transcoded=response.get(
                'Output', {}
            ).get('FileSize'),
            aspect_ratio=response.get('Input', {}).get('AspectRatio')
        )
