from aws_clients.aws_client import BaseAWSClient


class ApiGatewayClient(BaseAWSClient):
    """
     AWS Api Gateway Service client
    """

    def __init__(self,
                 region_name,
                 aws_access_key_id,
                 aws_secret_access_key):
        super(ApiGatewayClient, self).__init__(
            service='apigateway',
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
