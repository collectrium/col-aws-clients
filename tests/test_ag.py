from __future__ import unicode_literals

import json
from cStringIO import StringIO

from mock import patch

from aws_clients.aws_api_gateway.deployment import APIGatewayDeployer
from tests.base_test import BaseTest
from tests.mock_aws_api import AWSMock


class AGTest(BaseTest):
    swagger_json = {
        "swagger": "2.0",
        "info": {
            "version": "2016-07-13T13:37:46Z",
            "title": "Sample"
        },
        "host": "example.com",
        "basePath": "/dev",
        "schemes": [
            "https"
        ],
        "paths": {
            "/test": {
                "get": {
                    "produces": [
                        "application/json"
                    ],
                    "responses": {
                        "200": {
                            "description": "200 response",
                            "schema": {
                                "$ref": "#/definitions/Empty"
                            }
                        }
                    },
                    "x-amazon-apigateway-integration": {
                        "responses": {
                            "default": {
                                "statusCode": "200"
                            }
                        },
                        "uri": "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:21423412341234:function:${stageVariables.lambda_function}/invocations",
                        "passthroughBehavior": "when_no_match",
                        "httpMethod": "POST",
                        "type": "aws"
                    }
                }
            }
        },
        "definitions": {
            "Empty": {
                "type": "object"
            }
        }
    }
    swagger_file = StringIO(json.dumps(swagger_json))


    @patch('botocore.client.BaseClient._make_api_call', new=AWSMock.mock_make_api_call)
    def test_deployment(self):
        ag_deployer = APIGatewayDeployer(
            api_name='Sample', 
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            swagger_file=StringIO(json.dumps(self.swagger_json)),
            domain_name="example.com"

        )

        ag_deployer.deploy_stage(stage='development',
                                     lambda_function_name='api_lambda',
                                     lambda_version='development')

        ag_deployer.deploy_domain(stage='development', base_path='v1',
                                  certificate_body="", certificate_private_key="", certificate_chain='')

        ag_deployer.deploy_stage(stage='development',
                                     lambda_function_name='api_lambda',
                                     lambda_version='development')

        ag_deployer.deploy_domain(stage='development', base_path='v1',
                                  certificate_body="", certificate_private_key="", certificate_chain='')
