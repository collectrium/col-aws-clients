from __future__ import unicode_literals

import datetime
import json
import random
import string
from cStringIO import StringIO

import botocore
from botocore.exceptions import ClientError

from tests.base_test import BaseTest

orig = botocore.client.BaseClient._make_api_call


def random_string(length):
    return ''.join(
        random.choice(string.ascii_lowercase + string.digits)
        for _ in range(length)
    )


class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


class AWSMock(object):
    api_gateway = AttributeDict(
        api={'items': []},
        stages={'item': []},
        domains={'items': []},
        mappings={'items': []}
    )
    aws_lambda = AttributeDict(
        functions={}
    )
    iam = AttributeDict(
        roles={'lambda_basic_execution':
            'arn:aws:iam::{}:role/lambda_basic_execution'.format(
                BaseTest.account_id
            )}
    )
    beanstalk = AttributeDict(
        applications={'Applications': []},
        environments={'Environments': []}
    )

    @staticmethod
    def mock_make_api_call(self, operation_name, kwarg):
        # self  - it is not a mistake
        def check_exception():
            try:
                orig(self, operation_name, kwarg)
            except ClientError as cle:
                if not (cle.message.endswith(
                        'The security token included in the request is invalid.'
                ) or cle.message.endswith(
                    'The AWS Access Key Id you provided does not exist in our records.')):
                    print cle.message
                    raise cle

        check_exception()
        ### API GATEWAY
        if operation_name == 'GetRestApis':
            return AWSMock.api_gateway.api
        elif operation_name == 'ImportRestApi':
            api_id = random_string(6)
            AWSMock.api_gateway.api['items'].append(
                dict(
                    name=json.loads(kwarg['body'])['info']['title'],
                    id=api_id,
                    createdDate=datetime.datetime.utcnow()
                )
            )
            return dict(
                id=api_id,
                createdDate=datetime.datetime.utcnow().isoformat(),
            )
        elif operation_name == 'CreateDeployment':
            deployment_id = random_string(4)
            AWSMock.api_gateway.stages['item'].append(
                {'stageName': kwarg['stageName'],
                 'deploymentId': deployment_id,
                 'lastUpdatedDate': datetime.datetime.utcnow(),
                 'createdDate': datetime.datetime.utcnow(),
                 'methodSettings': {}
                 }
            )
            return dict(
                id=deployment_id,
                description='',
                createdDate=datetime.datetime.utcnow(),
                apiSummary={
                }
            )
        elif operation_name == 'GetDomainNames':
            return AWSMock.api_gateway.domains
        elif operation_name == 'CreateDomainName':
            distribution_domain_name = '{}.cloudfront.net'.format(
                random_string(14)
            )
            response = {'distributionDomainName': distribution_domain_name,
                        'certificateUploadDate': datetime.datetime.utcnow(),
                        'certificateName': kwarg['domainName'],
                        'domainName': kwarg['domainName']}
            AWSMock.api_gateway.domains['items'].append(response)
            return response
        elif operation_name == 'DeleteBasePathMapping':
            return
        elif operation_name == 'CreateBasePathMapping':
            response = {
                'basePath': kwarg['basePath'],
                'restApiId': kwarg['restApiId'],
                'stage': kwarg['stage']
            }
            AWSMock.api_gateway.mappings['items'].append(response)
            return response

        ### LAMBDA
        elif operation_name == 'Invoke':
            return {'Payload': StringIO('test_result')}
        elif operation_name == 'CreateFunction':
            function_arn = 'arn:aws:lambda:{region_name}:{account_id}:function' \
                           ':{function_name}'.format(
                region_name=BaseTest.region_name,
                account_id=BaseTest.account_id,
                function_name=kwarg['FunctionName']
            )
            AWSMock.aws_lambda.functions.update({
                kwarg['FunctionName']: function_arn
            })
            return {
                'FunctionName': kwarg['FunctionName'],
                'FunctionArn': function_arn,
                'Runtime': 'python2.7',
                'Role': 'arn:aws:iam::{}:role/lambda_basic_execution'.format(
                    BaseTest.account_id
                ),
                'Handler': 'lambda_module.lambda_handler',
                'CodeSize': 123,
                'Description': '',
                'Timeout': 123,
                'MemorySize': 123,
                'CodeSha256': '12341234123478912349172348912304712348',
            }

        elif operation_name == 'UpdateFunctionCode':
            function_arn = AWSMock.aws_lambda.functions.get(
                kwarg['FunctionName'], None)
            if not function_arn:
                raise ClientError(error_response=dict(
                    Error=dict(
                        ErrorMessage='An error occurred (Res   ourceNotFoundException) '
                                     'when calling the UpdateFunctionCode operation: '
                                     'Function not found: arn:aws:lambda:'
                                     '{region_name}:{account_id}:function:{function_name}'.format(
                            region_name=BaseTest.region_name,
                            account_id=BaseTest.account_id,
                            function_name=kwarg['FunctionName']
                        ), ErrorCode='ResourceNotFoundException')),
                    operation_name=operation_name)
            return {
                'FunctionName': kwarg['FunctionName'],
                'FunctionArn': function_arn,
                'Runtime': 'python2.7',
                'Role': 'arn:aws:iam::{}:role/lambda_basic_execution'.format(
                    BaseTest.account_id
                ),
                'Handler': 'lambda_module.lambda_handler',
                'CodeSize': 123,
                'Description': '',
                'Timeout': 123,
                'MemorySize': 123,
                'CodeSha256': '12341234123478912349172348912304712348',
            }
        elif operation_name == 'DeleteAlias':
            return None
        elif operation_name == 'PublishVersion':
            function_arn = AWSMock.aws_lambda.functions.get(
                kwarg['FunctionName'], None)
            if not function_arn:
                raise ClientError(error_response=dict(
                    Error=dict(
                        ErrorMessage='An error occurred (ResourceNotFoundException) '
                                     'when calling the PublishVersion operation: '
                                     'Function not found: arn:aws:lambda:'
                                     '{region_name}:{account_id}:function:{function_name}'.format(
                            region_name=BaseTest.region_name,
                            account_id=BaseTest.account_id,
                            function_name=kwarg['FunctionName']
                        ), ErrorCode='ResourceNotFoundException')),
                    operation_name=operation_name)
            return {
                'FunctionName': kwarg['FunctionName'],
                'FunctionArn': function_arn,
                'Runtime': 'python2.7',
                'Role': 'arn:aws:iam::{}:role/lambda_basic_execution'.format(
                    BaseTest.account_id
                ),
                'Handler': 'lambda_module.lambda_handler',
                'CodeSize': 123,
                'Description': '',
                'Timeout': 123,
                'MemorySize': 123,
                'LastModified': datetime.datetime.utcnow().isoformat(),
                'CodeSha256': '12341234123478912349172348912304712348',
                'Version': '1234123412341234234234',

            }
        elif operation_name == 'CreateAlias':
            function_arn = AWSMock.aws_lambda.functions.get(
                kwarg['FunctionName'], None)
            if not function_arn:
                raise ClientError(error_response=dict(
                    Error=dict(
                        ErrorMessage='An error occurred (ResourceNotFoundException) '
                                     'when calling the CreateAlias operation: '
                                     'Function not found: arn:aws:lambda:'
                                     '{region_name}:{account_id}:function:{function_name}'.format(
                            region_name=BaseTest.region_name,
                            account_id=BaseTest.account_id,
                            function_name=kwarg['FunctionName']
                        ), ErrorCode='ResourceNotFoundException')),
                    operation_name=operation_name)
            return {
                'AliasArn': function_arn + ':{}'.format(kwarg['Name']),
                'Name': kwarg['Name'],
                'FunctionVersion': kwarg['FunctionVersion'],
                'Description': ''
            }
        elif operation_name == 'AddPermission':
            return {
                'Statement': 'test-statement'  # fixme
            }
        ### IAM
        elif operation_name == 'GetRole':
            return {
                'Role': {
                    'Path': '',
                    'RoleName': kwarg['RoleName'],
                    'RoleId': '',
                    'Arn': 'arn:aws:iam::{}:role/{}'.format(
                        BaseTest.account_id,
                        kwarg['RoleName']
                    ),
                    'CreateDate': datetime.datetime.utcnow(),
                    'AssumeRolePolicyDocument': ''
                }
            }
        ### S3
        elif operation_name == 'PutObject':
            return None  # fixme
        ### ElasticBeanstalk
        elif operation_name == 'CreateStorageLocation':
            return {
                'S3Bucket': 'elastic-beanstalk-bucket'
            }
        elif operation_name == 'DescribeApplications':
            return AWSMock.beanstalk.applications
        elif operation_name == 'CreateApplication':
            result = {
                'ApplicationName': kwarg['ApplicationName'],
                'Description': '',
                'DateCreated': datetime.datetime.utcnow(),
                'DateUpdated': datetime.datetime.utcnow(),
                'Versions': [
                ],
                'ConfigurationTemplates': [
                ]
            }
            AWSMock.beanstalk.applications['Applications'].append(
                result
            )
            return {'Application': result}
        elif operation_name == 'CreateApplicationVersion':
            return {
                'ApplicationVersion': {
                    'ApplicationName': kwarg['ApplicationName'],
                    'Description': '',
                    'VersionLabel': kwarg['VersionLabel'],
                    'SourceBundle': {
                        'S3Bucket': kwarg['SourceBundle']['S3Bucket'],
                        'S3Key': kwarg['SourceBundle']['S3Key']
                    },
                    'DateCreated': datetime.datetime.utcnow(),
                    'DateUpdated': datetime.datetime.utcnow(),
                    'Status': 'Processed'
                }
            }
        elif operation_name == 'DescribeEnvironments':
            return AWSMock.beanstalk.environments
        elif operation_name == 'CreateEnvironment':
            response = {
                'EnvironmentName': kwarg['EnvironmentName'],
                'EnvironmentId': random_string(5),
                'ApplicationName': kwarg['ApplicationName'],
                'VersionLabel': kwarg['VersionLabel'],
                'SolutionStackName': kwarg['EnvironmentName'],
                'TemplateName': '',
                'Description': '',
                'EndpointURL': '',
                'CNAME': '',
                'DateCreated': datetime.datetime.utcnow(),
                'DateUpdated': datetime.datetime.utcnow(),
                'Status': 'Ready',
                'AbortableOperationInProgress': False,
                'Health': 'Green',
                'Tier': {
                    'Name': kwarg['Tier']['Name'],
                    'Type': kwarg['Tier']['Type'],
                }

            }
            AWSMock.beanstalk.environments['Environments'].append(response)
            return response
        return orig(self, operation_name, kwarg)
