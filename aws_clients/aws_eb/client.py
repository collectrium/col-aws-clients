from aws_clients.aws_client import BaseAWSClient


class ElasticBeanstalkClient(BaseAWSClient):
    """
     AWS Elasticsearch  Service client
    """

    def __init__(self,
                 region_name,
                 aws_access_key_id,
                 aws_secret_access_key):
        """

        :param region_name:
        :param aws_access_key_id:
        :param aws_secret_access_key:
        """
        super(ElasticBeanstalkClient, self).__init__(
            service='elasticbeanstalk',
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
