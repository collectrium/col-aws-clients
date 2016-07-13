from botocore.exceptions import ClientError

from aws_clients.aws_client import BaseAWSClient


class ApiGatewayClient(BaseAWSClient):
    """
     AWS Api Gateway Service client
    """

    def __init__(self,
                 region_name,
                 aws_access_key_id,
                 aws_secret_access_key):
        super(ApiGatewayClient, self).__init__(
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
        api_name = swagger_json['info']['title']
        api_id = self.__get_api_id(api_name)
        if not api_id:
            self.instance.import_rest_api(
                body=swagger_json
            )
        else:
            self.instance.put_rest_api(
                restApiId=api_id,
                mode='overwrite',
                body=swagger_json
            )

    def deploy_stage(self, api_name, stage, lambda_function_name):
        api_id = self.__get_api_id(api_name)
        self.instance.create_deployment(
            restApiId=api_id,
            stageName=stage,
            stageDescription='',
            variables=dict(
                lambda_function=lambda_function_name
            )
        )

    def create_custom_domain_name(
            self,
            domain_name,
            certificate_body,
            certificate_private_key,
            certificate_chain
    ):
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
