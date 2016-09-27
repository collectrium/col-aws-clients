import os
import tempfile
import zipfile

from git import Repo
from mock import patch

from aws_clients.lambda_.deployment import LambdaDeployer, LambdaPackage
from aws_clients.lambda_.lambda_function import LambdaFunction
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
        git_repo = Repo.init(path=tempfile.mkdtemp())
        zip_file = LambdaPackage(
            aws_lambda_config, git_repo.git_dir
        ).create_deployment_package()
        lambda_deployer = LambdaDeployer(
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            zip_file=zip_file,
            version='development',
            aws_lambda_config=aws_lambda_config
        )

        lambda_deployer.deploy()
        lambda_deployer.deploy()

    def tearDown(self):
        try:
            os.remove('lambda_.zip')
        except OSError:
            pass
