from __future__ import unicode_literals
import json
import logging

from botocore.exceptions import ClientError

from ..base_client import BaseAWSClient

LOGGER = logging.getLogger(__name__)


class APIGatewayClient(BaseAWSClient):
    """
     AWS Api Gateway Service client
    """

    def __init__(self,
                 region_name,
                 aws_access_key_id,
                 aws_secret_access_key):
        """
        :param region_name: AWS region name
        :type str
        :param aws_access_key_id: AWS credentials
        :type str
        :param aws_secret_access_key: AWS credentials
        :type str
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
                LOGGER.info('Found API `{}` with id `{}`'.format(
                    api_name, item['id']
                ))
                return item['id']
        LOGGER.info('API `{}` not found'.format(api_name))

    def create_api(self, swagger_json):
        """
        Create API
        :param swagger_json:  AWS API Gateway Swagger config
        :return:
        """
        api_name = swagger_json['info']['title']
        api_id = self.__get_api_id(api_name)
        if not api_id:
            LOGGER.info('Create API')
            response = self.instance.import_rest_api(
                body=json.dumps(swagger_json)
            )
            LOGGER.info('API created with id `{}`'.format(response['id']))
        else:
            if (swagger_json['host'].endswith('amazonaws.com') and
                    not swagger_json['host'].startswith(api_id)):
                swagger_json['host'] = '{}.{}'.format(
                    api_id,
                    ".".join(swagger_json['host'].split('.')[1:])
                )
            LOGGER.info('Overwrite API with id `{}`')
            self.instance.put_rest_api(
                restApiId=api_id,
                mode='overwrite',
                body=json.dumps(swagger_json)
            )

    def deploy_stage(
            self, api_name, stage, lambda_function_name, version=None
    ):
        """
        Deploy stage
        :param api_name: API Gateway visible name
        :type str
        :param stage: stage name
        :type str
        :param lambda_function_name: function name for stage
        :type str
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
        Create cusom domain name
        :param domain_name: custom domain name
        :type str
        :param certificate_body:   SSL certificate
        :type str
        :param certificate_private_key: SSL private key
        :type str
        :param certificate_chain: SSL certificate chain
        :type str
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
        :type str
        :param stage:  stage
        :type str
        :param domain_name:  custom domain name
        :type str
        :param base_path: base pathn for mapping
        :type str
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
