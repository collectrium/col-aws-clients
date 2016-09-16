import unittest

import urlparse


class BaseTest(unittest.TestCase):
    """
    Very base class, only to add self.assertEqualsS3Urls method
    """
    account_id = '1234567890'
    region_name = 'us-east-1'
    aws_access_key_id = 'AKIAIOSFODNN7EXAMPLE'
    aws_secret_access_key = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
    private_key = """
    -----BEGIN RSA PRIVATE KEY-----
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
-----END RSA PRIVATE KEY-----
    """

    def assertEqualsS3Urls(self, first_url, second_url):
        first = urlparse.urlparse(first_url)
        second = urlparse.urlparse(second_url)
        self.assertEqual(first.path, second.path)

        first_qs = urlparse.parse_qs(first.query)
        second_qs = urlparse.parse_qs(second.query)
        self.assertEqual(
            first_qs['AWSAccessKeyId'],
            second_qs['AWSAccessKeyId'],
        )
        self.assertIn('Expires', first_qs)
        self.assertIn('Expires', second_qs)
        self.assertIn('Signature', first_qs)
        self.assertIn('Signature', second_qs)
