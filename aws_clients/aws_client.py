import boto3


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
        settings = {
            "region_name": region_name,
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key
        }

        self.settings = settings
        settings.update(kwargs)
        self.instance = boto3.client(service, **settings)
