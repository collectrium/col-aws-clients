from __future__ import unicode_literals

import datetime

from freezefrog import FreezeTime

from aws_clients.aws_s3.s3bucket import S3Bucket
from tests.base_test import BaseTest


class S3Test(BaseTest):
    def test_url_generate(self):
        with FreezeTime(datetime.datetime(2014, 1, 1)):
            s3 = S3Bucket(
                bucket_name="test-bucket",
                region_name=self.region_name,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key
            )
            key1 = "/key/path"
            key2 = "key/path"
            url = s3.generate_url(key1)
            self.assertEqual(
                url,
                "https://test-bucket.s3.amazonaws.com/key/path?AWSAccessKeyId="
                "AKIAIOSFODNN7EXAMPLE&Expires=1389139200&Signature=GMgha1idQv3t"
                "OKeGkYuH2EadL4s%3D")
            self.assertEqual(key1, s3.reduce_url(url))
            url1 = s3.generate_url(key1)
            url2 = s3.generate_url(key2)
            self.assertEqual(url1, url2)
            self.assertEqual(
                s3.reduce_url(url1),
                s3.reduce_url(url2)
            )
            url1 = s3.generate_url(key1, content_type="application/json")
            self.assertEqual(
                url1,
                "https://test-bucket.s3.amazonaws.com/key/path?Signature=8D%2B"
                "P0gUjgrRfX9YHNyTBdFVlVOE%3D&Expires=1389139200&AWSAccessKeyId"
                "=AKIAIOSFODNN7EXAMPLE")

    def test_cloudfront_url_generate(self):
        with FreezeTime(datetime.datetime(2014, 1, 1)):
            s3 = S3Bucket(
                bucket_name="test-bucket",
                region_name=self.region_name,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key
            )
            key1 = "/key/path"
            url = s3.generate_cloudfront_url(key=key1,
                                             cloudfront_domain='test.domain',
                                             cloudfront_key_id=self.aws_access_key_id,
                                             cloudfront_private_key=self.private_key
                                             )
            self.assertEqual(
                s3.reduce_url(url),
                s3.reduce_url("""https://test.domain/key/path?Expires=1469117341
&Signature=TM3frFRhnwYA9nOgpXPBKYowryd4TE16GRbpVW67NCQnoN~zqB3uQAAsMkR7q9eSifQsF
kFoTs-9pcu6x79ssScTL8qUkR108ib9gwMRahoq6aTxuPcUY70ML1A3xGhBZ45caxieTF8BfaoqciZ7Y
SSwfHLno49Ctn5FTLVerzTVpBzMaM6U64CHyFNkJMA2pABE65Jg6Yhm2I~xeMG4FJhc7~zfSUjnvjtAa
7w6hN4CWguFv2Zs4ozVvb6gmEnH8iN259mL0-0tTpqrZWKWU0Is5cw5TdRFvVViDTHzl8wbicuwtHZdE
fTjj~7h7subhzx2hYCJnBvwmXDY7D8o8W1IwzeE5qsQInTr8kaL1fD-TTLGU9PLw-dGE9vaFJU29EA2p
ozOGXTvNWPC2hd76XJD9TTAaj~rchijZUe7wzTw4-tmkZ~QzBx7bcDs8Fm6YYZIzctb4jDMGU3uoZOqX
PCVtpEG-T8Zi4pzO3YcnoEh-XgUMwn23IjxzH7PEKAgsaOAtByT8HitDYMCEHEuSJU4qEgbhuEInU3j9
ka68s47iep~k8QJFMoB6zyBz8~D6sw3DqWtS1swscs1JvEQamb3lgeBv8qYVW4IoPouOwpZo~igwUhBu
mcLYQkGmOB~oLaWC6SnfyYUKUyH~lhaot5Kj1wP9Nw8u090WPUkYYc_&Key-Pair-Id=AKIAIOSFODNN
7EXAMPLE"""))
