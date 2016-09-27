from __future__ import unicode_literals

import logging

from ..base_client import BaseAWSClient

LOGGER = logging.getLogger(__name__)


class S3Client(BaseAWSClient):
    """
     AWS S3 Service client
    """

    def __init__(self,
                 region_name,
                 aws_access_key_id,
                 aws_secret_access_key):
        """

        :param region_name: AWS region name
        :param aws_access_key_id:  AWS credentials
        :param aws_secret_access_key: AWS credentials
        """
        super(S3Client, self).__init__(
            service='s3',
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

    def create_bucket(self, bucket_name):
        pass

    def delete_bucket(self, bucket_name):
        pass
