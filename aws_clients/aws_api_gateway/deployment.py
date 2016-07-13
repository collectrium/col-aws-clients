import json
import logging

from botocore.exceptions import ClientError

from aws_clients.aws_api_gateway.client import ApiGatewayClient
from aws_clients.aws_lambda.client import LambdaClient

logger = logging.getLogger('AWSApiGateway')


class Swagger():
    @classmethod
    def create_swagger_config(cls,
                              swagger_template_file,
                              domain_name,
                              base_path,

                              ):
        with open(swagger_template_file) as tmp:
            swagger_json = json.load(tmp)
        swagger_json['host'] = domain_name
        swagger_json['basePath'] = '/{}'.format(base_path)

        return swagger_json


class ApiGatewayDeployer(object):
    def __init__(self,
                 swagger_template_file,
                 domain_name,
                 base_path,
                 region_name,
                 aws_access_key_id,
                 aws_secret_access_key,
                 certificate_body,
                 certificate_private_key,
                 certificate_chain

                 ):

        self.client = ApiGatewayClient(
            region_name, aws_access_key_id, aws_secret_access_key
        )

        self.certificate_body = certificate_body
        self.certificate_private_key = certificate_private_key
        self.certificate_chain = certificate_chain
        self.swagger_json = Swagger.create_swagger_config(
            swagger_template_file,
            domain_name,
            base_path
        )
        self.api_name = self.swagger_json['info']['title']
        self.domain_name = domain_name
        self.base_path = base_path

    def __create_api(self):
        self.client.create_api(self.swagger_json)

    def __deploy_stage(self, stage, lambda_function_name, lambda_version=None):
        self.__add_lambda_permission(lambda_function_name)
        if lambda_version:
            lambda_function_name = "{}:{}".format(
                lambda_function_name, lambda_version
            )
        self.client.deploy_stage(self.api_name, stage, lambda_function_name)

    def __add_lambda_permission(self, lambda_function_name):
        permission = dict(
            FunctionName=lambda_function_name,
            StatementId="58f7cfba-2278-4583-baae-227c582c2023",
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
        )
        try:
            lambda_client = LambdaClient(**self.client.settings)
            lambda_client.instance.add_permission(**permission)
        except ClientError as exc:
            logger.exception(exc)

    def __create_custom_domain_name(
            self,
            certificate_body,
            certificate_private_key,
            certificate_chain

    ):
        self.client.create_custom_domain_name(
            domain_name=self.domain_name,
            certificate_body=certificate_body,
            certificate_private_key=certificate_private_key,
            certificate_chain=certificate_chain
        )

    def __create_path_mapping(self, stage):
        self.client.create_path_mapping(
            self.api_name,
            stage,
            self.domain_name,
            self.base_path
        )

    def deploy(self, stage, lambda_function_name, lambda_version=None):
        self.__create_api()
        self.__add_lambda_permission(lambda_function_name)
        self.__deploy_stage(stage, lambda_function_name, lambda_version)
        self.__create_custom_domain_name(
            self.certificate_body,
            self.certificate_private_key,
            self.certificate_chain
        )
        self.__create_path_mapping()
