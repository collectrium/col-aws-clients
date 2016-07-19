import zipfile

from mock import patch

from aws_clients.aws_eb.deployment import EBDeployer
from tests.base_test import BaseTest
from tests.mock_aws_api import AWSMock


class EBTest(BaseTest):
    @patch('botocore.client.BaseClient._make_api_call',
           new=AWSMock.mock_make_api_call)
    def test_eb_deployment(self):
        zip_file = zipfile.ZipFile('aws.zip', "w", zipfile.ZIP_DEFLATED)
        zip_file.close()
        eb_deployer = EBDeployer(
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            zip_file='aws.zip',
            environment='development',
            applications_config={
                'eb_reindex_worker': {
                    'type': 'worker',
                    'stack': '64bit Amazon Linux 2015.09 v2.0.8 running Python 2.7',

                }
            }
        )

        eb_deployer.deploy()
