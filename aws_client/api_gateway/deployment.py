from __future__ import unicode_literals

import json
import logging

from ..api_gateway.client import APIGatewayClient

LOGGER = logging.getLogger(__name__)


class APIGatewayDeployer(object):
    def __init__(self,
                 api_name,
                 swagger_file,
                 region_name,
                 aws_access_key_id,
                 aws_secret_access_key,
                 domain_name=None,

                 ):
        """

        :param api_name: API name
         :type str
        :param swagger_file: Swagger json config
         :type file
        :param region_name: AWS region name
         :type str
        :param aws_access_key_id: AWS credentials
         :type str
        :param aws_secret_access_key: AWS credentials
         :type str
        :param domain_name: custom  domain name
         :type str
        """
        LOGGER.info('Initialize client')
        self.client = APIGatewayClient(
            region_name, aws_access_key_id, aws_secret_access_key
        )
        LOGGER.info('Load swagger config')
        self.swagger_json = json.load(swagger_file)

        self.api_name = api_name

        self.swagger_json['info']['title'] = api_name
        LOGGER.info('API name `{}`'.format(api_name))
        if domain_name:
            self.swagger_json['host'] = domain_name
            LOGGER.info('Domain name `{}`'.format(domain_name))
        self.domain_name = domain_name

    def __create_api(self):
        LOGGER.info('Create API')
        self.client.create_api(self.swagger_json)

    def __deploy_stage(self, stage, lambda_function_name, lambda_version=None):
        LOGGER.info('Deploy stage with AWS Lambda `%s` and version `%s`',
                    lambda_function_name, lambda_version
                    )
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
        LOGGER.info('Create custom domain name `%s`', self.domain_name)
        self.client.create_custom_domain_name(
            domain_name=self.domain_name,
            certificate_body=certificate_body,
            certificate_private_key=certificate_private_key,
            certificate_chain=certificate_chain
        )

    def __create_path_mapping(self, stage, base_path):
        LOGGER.info('Create path mapping for stage `%s` with path `%s` ',
                    stage, base_path
                    )
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
        :param stage: stage name
        :type str
        :param lambda_function_name: Lambda function name
        :type str
        :param lambda_version: Lambda function version name
        :type str
        :return:
        """
        self.__create_api()
        self.__deploy_stage(stage, lambda_function_name, lambda_version)

    def deploy_domain(self, stage, base_path,
                      certificate_body,
                      certificate_private_key,
                      certificate_chain):
        """
        Create custom domain name and associate it with stage
        :param stage: stage name
        :type str
        :param base_path: base_path
        :type str
        :param certificate_body: SSL certificate
        :type str
        :param certificate_private_key: SSL certificate private key
        :type str
        :param certificate_chain: SSL certificate chain
        :type str
        :return:
        """
        self.__create_custom_domain_name(
            certificate_body,
            certificate_private_key,
            certificate_chain
        )
        self.__create_path_mapping(stage, base_path)
