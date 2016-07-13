import zipfile

from aws_clients.aws_api_gateway.deployment import ApiGatewayDeployer
from aws_clients.aws_lambda.deployment import LambdaDeployer

AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""


def debug_deploy():
    zip_file = zipfile.ZipFile('lambda.zip', "w", zipfile.ZIP_DEFLATED)
    zip_file.write('examples/lambda_module.py', 'lambda_module.py')
    zip_file.close()

    lambda_deployer = LambdaDeployer(
        region_name='us-east-1',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        zip_file='lambda.zip',
        version='development',
        aws_lambda_config={
            'roma_api_function': {
                'role_name': 'lambda_basic_execution',
                'handler': 'lambda_module.lambda_handler',
                'event_sources': {
                    'api_gateway': {},
                },
            }
        }
    )
    lambda_deployer.deploy()

    ag_deployer = ApiGatewayDeployer(
        region_name='us-east-1',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        swagger_file='examples/sample_config.json'
    )

    ag_deployer.deploy(
        'test',
        'roma_api_function',
        'development'
    )


if __name__ == '__main__':
    debug_deploy()
