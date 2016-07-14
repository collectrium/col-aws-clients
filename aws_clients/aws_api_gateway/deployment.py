import json

from aws_clients.aws_api_gateway.client import APIGatewayClient


class APIGatewayDeployer(object):
    def __init__(self,
                 api_name,
                 swagger_file,
                 region_name,
                 aws_access_key_id,
                 aws_secret_access_key,
                 domain_name=None,

                 ):
        self.client = APIGatewayClient(
            region_name, aws_access_key_id, aws_secret_access_key
        )
        with open(swagger_file) as tmp:
            self.swagger_json = json.load(tmp)

        self.api_name = api_name
        self.swagger_json['info']['title'] = api_name
        if domain_name:
            self.swagger_json['host'] = domain_name
        self.domain_name = domain_name

    def __create_api(self):
        self.client.create_api(self.swagger_json)

    def __deploy_stage(self, stage, lambda_function_name, lambda_version=None):
        if lambda_version:
            lambda_function_name = "{}:{}".format(
                lambda_function_name, lambda_version
            )
        self.client.deploy_stage(self.api_name, stage, lambda_function_name)

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

    def __create_path_mapping(self, stage, base_path):
        self.client.create_path_mapping(
            self.api_name,
            stage,
            self.domain_name,
            base_path
        )

    def deploy_stage(self, stage, lambda_function_name, lambda_version=None):
        """
        Create API by swagger file and deploy stage with
        variable `lambda_function`
        :param stage:
        :param lambda_function_name:
        :param lambda_version:
        :return:
        """
        self.__create_api()
        self.__deploy_stage(stage, lambda_function_name, lambda_version)

    def deploy_domain(self, stage, base_path,
                      certificate_body,
                      certificate_private_key,
                      certificate_chain):
        """

        :param stage:
        :param base_path:
        :param certificate_body:
        :param certificate_private_key:
        :param certificate_chain:
        :return:
        """
        self.__create_custom_domain_name(
            certificate_body,
            certificate_private_key,
            certificate_chain
        )
        self.__create_path_mapping(stage, base_path)
