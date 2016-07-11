import unittest
import urlparse


class BaseTest(unittest.TestCase):
    """
    Very base class, only to add self.assertEqualsS3Urls method
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