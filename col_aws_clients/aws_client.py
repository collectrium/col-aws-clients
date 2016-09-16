import logging

import boto3

LOGGER = logging.getLogger(__name__)


class BaseAWSClientException(Exception):
    """
    Base AWS CLient Exception
    """
    pass


class BaseAWSClient(object):
    """
    Default client for AWS
    """

    def __init__(self, service,
                 region_name,
                 aws_access_key_id,
                 aws_secret_access_key,
                 **kwargs
                 ):
        """

        :param service: AWS service ('ec2','es' etc.)
        :param region_name: AWS region
        :param aws_access_key_id: AWS credentials
        :param aws_secret_access_key: AWS credentials
        :param kwargs: additional keywords arguments
        """
        settings = {
            "region_name": region_name,
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key
        }
        LOGGER.info('Initialize AWS client for service `%s`', service)

        self.settings = settings
        settings.update(kwargs)
        self.instance = boto3.client(service, **settings)
