from __future__ import unicode_literals

from ..base_client import BaseAWSClient


class ElasticBeanstalkClient(BaseAWSClient):
    """
     AWS Elasticsearch  Service client
    """

    def __init__(self,
                 region_name,
                 aws_access_key_id,
                 aws_secret_access_key):
        """
        :param region_name:  AWS region name
        :type str
        :param aws_access_key_id: AWS credentials
        :type str
        :param aws_secret_access_key: AWS credentials
        :type str
        """
        super(ElasticBeanstalkClient, self).__init__(
            service='elasticbeanstalk',
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

    def get_environment_state(self, app_name, env_name):
        response = self.instance.describe_environments(
            ApplicationName=app_name,
            EnvironmentNames=[
                env_name,
            ],
        )
        return (
            response['Environments'][0]['Status'],
            response['Environments'][0]['Health']
        )
