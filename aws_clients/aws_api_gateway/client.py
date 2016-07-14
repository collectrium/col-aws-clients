import json

from botocore.exceptions import ClientError

from aws_clients.aws_client import BaseAWSClient


class APIGatewayClient(BaseAWSClient):
    """
     AWS Api Gateway Service client
    """

    def __init__(self,
                 region_name,
                 aws_access_key_id,
                 aws_secret_access_key):
        """
        :param region_name: AWS region
        :param aws_access_key_id: AWS credentials
        :param aws_secret_access_key: AWS credentials
        """
        super(APIGatewayClient, self).__init__(
            service='apigateway',
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

    def __get_api_id(self, api_name):
        api_list = self.instance.get_rest_apis().get('items')
        for item in api_list:
            if item['name'] == api_name:
                return item['id']

    def create_api(self, swagger_json):
        """
        Create API
        :param swagger_json:  AWS API Gateway Swagger config
        :return:
        """
        api_name = swagger_json['info']['title']
        api_id = self.__get_api_id(api_name)
        if not api_id:
            self.instance.import_rest_api(
                body=json.dumps(swagger_json)
            )
        else:
            if (swagger_json['host'].endswith('amazonaws.com') and
                    not swagger_json['host'].startswith(api_id)):
                swagger_json['host'] = '{}.{}'.format(
                    api_id,
                    ".".join(swagger_json['host'].split('.')[1:])
                )

            self.instance.put_rest_api(
                restApiId=api_id,
                mode='overwrite',
                body=json.dumps(swagger_json)
            )

    def deploy_stage(self, api_name, stage, lambda_function_name, version=None):
        """
        Deploy stage
        :param api_name: API Gateway visible name
        :param stage: stage name
        :param lambda_function_name: function name for stage
        :return:
        """
        api_id = self.__get_api_id(api_name)
        self.instance.create_deployment(
            restApiId=api_id,
            stageName=stage,
            stageDescription='',
            variables=dict(
                lambda_function=lambda_function_name if not version else
                '{}:{}'.format(lambda_function_name, version)
            )
        )

    def create_custom_domain_name(
            self,
            domain_name,
            certificate_body,
            certificate_private_key,
            certificate_chain
    ):
        """

        :param domain_name:
        :param certificate_body:
        :param certificate_private_key:
        :param certificate_chain:
        :return:
        """
        response = self.instance.get_domain_names()
        domain_names = [item['domainName'] for item in response.get('items')]
        if not (domain_names and domain_name in domain_names):
            self.instance.create_domain_name(
                domainName=domain_name,
                certificateName=domain_name,
                certificateBody=certificate_body,
                certificatePrivateKey=certificate_private_key,
                certificateChain=certificate_chain
            )

    def create_path_mapping(self, api_name, stage, domain_name, base_path):
        """
        Create path mapping
        :param api_name:  API Gateway visible name
        :param stage:  stage
        :param domain_name:  custom domain name
        :param base_path: base pathn for mapping
        :return:
        """
        try:
            self.instance.delete_base_path_mapping(
                domainName=domain_name,
                basePath=base_path
            )
        except ClientError:
            pass

        self.instance.create_base_path_mapping(
            domainName=domain_name,
            basePath=base_path,
            restApiId=self.__get_api_id(api_name),
            stage=stage
        )
