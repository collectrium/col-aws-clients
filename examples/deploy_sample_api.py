import getopt
import sys
import zipfile

from aws_clients.aws_api_gateway.deployment import APIGatewayDeployer
from aws_clients.aws_lambda.deployment import LambdaDeployer


def debug_deploy(aws_access_key_id, aws_secret_access_key):
    zip_file = zipfile.ZipFile('lambda.zip', "w", zipfile.ZIP_DEFLATED)
    zip_file.write('examples/lambda_module.py', 'lambda_module.py')
    zip_file.close()

    lambda_deployer = LambdaDeployer(
        region_name='us-east-1',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
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

    ag_deployer = APIGatewayDeployer(
        api_name='Sample',
        region_name='us-east-1',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        swagger_file='examples/sample_config.json'
    )

    ag_deployer.deploy_stage(
        'test',
        'roma_api_function',
        'development'
    )


if __name__ == '__main__':
    _, args = getopt.getopt(sys.argv[1:], 'h')
    try:
        aws_access_key_id = args[0].split('=')[1]
        aws_secret_access_key = args[1].split('=')[1]
        debug_deploy(aws_access_key_id, aws_secret_access_key)
    except Exception as exc:
        print 'Invalid usage {}'.format(exc.message)
