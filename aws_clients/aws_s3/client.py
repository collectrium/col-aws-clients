from aws_clients.aws_client import BaseAWSClient


class S3Client(BaseAWSClient):
    """
     AWS S3 Service client
    """

    def __init__(self,
                 region_name,
                 aws_access_key_id,
                 aws_secret_access_key):
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