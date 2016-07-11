import urllib
import urlparse
from datetime import datetime, timedelta

import boto
import boto3
import rsa
from botocore.exceptions import ClientError
from botocore.signers import CloudFrontSigner

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


class S3Bucket(object):
    """
    Implements interface to S3 bucket resource
    """

    def __init__(
            self,
            bucket_name,
            region_name,
            aws_access_key_id,
            aws_secret_access_key,
    ):
        """
        :param bucket_name: bucket's name
        :param cloudfront_domain: Cloudfront domain
        """
        self.bucket_name = bucket_name
        self.client = S3Client(
            region_name,
            aws_access_key_id,
            aws_secret_access_key)

        self.instance = boto3.resource(
            's3', **self.client.settings
        ).Bucket(bucket_name)

    def list_objects(self, prefix=''):
        """
        List objects on bucket
        :param prefix:  key prefix
        :type str
        :return:
        """
        return self.client.instance.list_objects(
            Bucket=self.bucket_name, Prefix=prefix
        )

    def copy(self, source, destination):
        """
        Copy object on bucket
        :param source: path to source on bucket
        :type str
        :param destination: path to destination on bucket
        :type str
        :return:
        """
        kwargs = dict(
            Bucket=self.bucket_name,
            CopySource="{}/{}".format(self.bucket_name, source),
            Key=destination,
        )
        self.client.instance.copy_object(**kwargs)
        return self.generate_url(destination)

    def outer_copy(self, source_bucket, source, destination):
        """
        Copy from another S3 bucket
        :param source_bucket: source bucket's name
        :type str
        :param source: path  to object on source bucket
        :type str
        :param destination:  path to destination on self bucket
         :type str
        :return:
        """
        kwargs = dict(
            Bucket=self.bucket_name,
            CopySource="{}/{}".format(source_bucket, source),
            Key=destination,
        )
        self.client.instance.copy_object(**kwargs)

    def generate_url(self, key,
                     url_expiration_time=604800,  # 60*60*24*7s
                     force_http_url=False,
                     content_type=None,
                     cloudfront_domain=None
                     ):
        """
        Generate presigned url for object on bucket
        :param key:  path to object on bucket
        :type str
        :param content_type: content-type for object
        :type str
        :return: url
        :rtype str
        """
        if key is None:
            return
        if cloudfront_domain:
            return self._generate_cloudfront_url(
                key, cloudfront_domain, url_expiration_time, force_http_url

            )

        if not content_type:
            key = key.lstrip('/')
            params = {'Bucket': self.bucket_name, 'Key': key}
            presigned_url = self.client.instance.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=url_expiration_time
            )

            if force_http_url:
                presigned_url = presigned_url.replace('https://', 'http://')
        else:
            # workaround for https://github.com/boto/boto3/issues/610
            conn = boto.connect_s3(
                self.client.settings['aws_access_key_id'],
                self.client.settings['aws_secret_access_key'],
            )
            presigned_url = conn.generate_url(
                expires_in=url_expiration_time,
                method='GET',
                bucket=self.bucket_name,
                key=key,
                headers={'Content-Type': content_type},
            )
        return presigned_url

    def _generate_cloudfront_url(self,
                                 key,
                                 cloudfront_domain,
                                 url_expiration_time=604800,  # 60*60*24*7s
                                 force_http_url=False
                                 ):
        """
        Generate presigned url for object on bucket
        :param key:  path to object on bucket
        :param cloudfront:  return url to cloudfront instead of s3
        :type str
        :return: url
        :rtype str
        """
        if key is None:
            return

        cloudfront_key_id = self.client.settings['aws_access_key_id']
        cloudfront_private_key = self.client.settings['aws_secret_access_key']

        key = key.lstrip('/')

        url = 'https://{}/{}'.format(cloudfront_domain, key)

        def rsa_signer(message):
            private_key = cloudfront_private_key
            return rsa.sign(
                message,
                rsa.PrivateKey.load_pkcs1(private_key.encode('utf8')),
                'SHA-1'
            )  # CloudFront requires SHA-1 hash

        cloudfront_signer = CloudFrontSigner(cloudfront_key_id,
                                             rsa_signer)
        expiry_datetime = (
            datetime.utcnow() +
            timedelta(seconds=url_expiration_time)
        )
        presigned_url = cloudfront_signer.generate_presigned_url(
            url, date_less_than=expiry_datetime
        )

        if force_http_url:
            presigned_url = presigned_url.replace('https://', 'http://')
        return presigned_url

    def upload_from_path(self, filepath, key):
        """
        Upload file on bucket from local storage
        :param filepath: path to file on local storage
        :type str
        :param key: path to object on bucket
        :type str
        :return: presigned url for object
        :rtype str
        """
        self.instance.upload_file(filepath, key)
        return self.generate_url(key)

    def upload_from_string(self, payload, key):
        """
        Create object on bucket and put payload data or stream data to it
        :param payload: byte string or file object
        :param key: path to object on bucket
        :type str
        :return:
        """
        kwargs = dict(
            Body=payload,
            Bucket=self.bucket_name,
            Key=key,
        )
        self.instance.put_object(**kwargs)
        return self.generate_url(key)

    def exist(self, key):
        """
        Check if key exists on bucket
        :param key: path to object on bucket
        :type key: str
        :return: True if object exists
        :rtype : bool
        """
        try:
            self.client.instance.head_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
        except ClientError:
            return False

    def get_object(self, key):
        """
        Return stream(file object) and content-length
        :param key: path to object on bucket
        :type key: str
        :return: stream, content-length
        :rtype : tuple
        """
        response = self.client.instance.get_object(
            Bucket=self.bucket_name,
            Key=key
        )
        return response['Body'], response['ContentLength']

    def _remove(self, key):
        """
        Remove object from bucket
        :param key:  path to object on bucket
        :type str
        """
        self.client.instance.delete_object(Bucket=self.bucket_name, Key=key)

    def reduce_url(self, url):
        """
        Get path to object on bucket from presigned url
        :param url: presigned url
        :type: str
        :return: path to object on bucket
        :rtype str
        """
        if (url is None) or (urlparse.urlparse(url).path == url):
            return url
        up = urlparse.urlparse(url)
        if not up.scheme:
            path = url
        else:
            path = urllib.unquote(up.path.encode('utf-8'))
        return path

    def make_public(self, key):
        """
        Set public-read ACL for key
        :param key: path to objecton bucket
        :type str
        """
        self.client.instance.put_object_acl(
            ACL='public-read',
            Bucket=self.bucket_name,
            Key=key
        )

    def make_private(self, key):
        """
        Set bucket-owner-full-control ACL for key
        :param key: path to objecton bucket
        :type str
        """
        self.client.instance.put_object_acl(
            ACL='bucket-owner-full-control',
            Bucket=self.bucket_name,
            Key=key
        )

