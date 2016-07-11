from aws_clients.aws_client import BaseAWSClient


class ElasticsearchClient(BaseAWSClient):
    """
     AWS Api Gateway Service client
    """

    def __init__(self,
                 region_name,
                 aws_access_key_id,
                 aws_secret_access_key):
        super(ElasticsearchClient, self).__init__(
            service='es',
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
