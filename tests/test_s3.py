import datetime

from aws_clients.s3 import S3Bucket
from freezefrog import FreezeTime
from tests.base_test import BaseTest


class S3Test(BaseTest):

    def test_url_generate(self):
        with FreezeTime(datetime.datetime(2014, 1, 1)):
            s3 = S3Bucket(bucket_name="test-bucket")
            key1  = "/key/path"
            key2 = "key/path"
            url = s3.generate_url(key1)
            self.assertEqual(
                url,
                u'https://test-bucket.s3.amazonaws.com/key/path?AWSAccessKeyId=&Expires=1389139200&Signature=q7J9Al5P7L7A1sEkox8xGTp3ctc%3D'
            )
            self.assertEqual(key1, s3.reduce_url(url))
            url1 = s3.generate_url(key1)
            url2 = s3.generate_url(key2)
            self.assertEqual(url1, url2)
            self.assertEqual(
                s3.reduce_url(url1),
                s3.reduce_url(url2)
            )
            url1  = s3.generate_url(key1, content_type="application/json")
            self.assertEqual(
                url1,
                u"https://test-bucket.s3.amazonaws.com/key/path?Signature=nxK%2BwZ69tQ7NHb0genrCgwW66Yg%3D&Expires=1389139200&AWSAccessKeyId="
            )