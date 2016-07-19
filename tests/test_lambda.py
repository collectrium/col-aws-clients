import os
import zipfile

from mock import patch

from aws_clients.aws_lambda.deployment import LambdaDeployer
from aws_clients.aws_lambda.lambda_function import LambdaFunction
from tests.base_test import BaseTest
from tests.mock_aws_api import AWSMock


class LambdaTest(BaseTest):
    @patch('botocore.client.BaseClient._make_api_call',
           new=AWSMock.mock_make_api_call)
    def test_lambda_invoke(self):
        l = LambdaFunction('test_function',
                           self.region_name,
                           self.aws_access_key_id,
                           self.aws_secret_access_key
                           )
        result = l(payload={'test': 1}, async=False)

    @patch('botocore.client.BaseClient._make_api_call',
           new=AWSMock.mock_make_api_call)
    def test_lambda_deployment(self):
        zip_file = zipfile.ZipFile('lambda.zip', "w", zipfile.ZIP_DEFLATED)
        # zip_file.write('examples/lambda_module.py', 'lambda_module.py')
        zip_file.close()
        lambda_deployer = LambdaDeployer(
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            zip_file='lambda.zip',
            version='development',
            aws_lambda_config={
                'roma_api_function': {
                    'role_name': 'lambda_basic_execution',
                    'handler': 'lambda_module.lambda_handler',
                    'event_sources': {
                        'api_gateway': {},
                    },
                    'ignored_packages': ['ipython', 'pudb']
                }
            }
        )

        lambda_deployer.deploy()

    def tearDown(self):
        try:
            os.remove('lambda.zip')
        except OSError:
            pass