import datetime
import json
import random
import string
from cStringIO import StringIO

import botocore
from botocore.exceptions import ClientError

orig = botocore.client.BaseClient._make_api_call


def random_string(length):
    return ''.join(
        random.choice(string.ascii_lowercase + string.digits)
        for _ in range(length)
    )

#TODO: create detailed requests and responses

class AWSMock(object):
    api_gateway = {'api': {'items': []}}

    @staticmethod
    def mock_make_api_call(self, operation_name, kwarg):
        # self  - it is not a mistake
        def check_exception():
            try:
                orig(self, operation_name, kwarg)
            except ClientError as cle:
                if not cle.message.endswith(
                        'The security token included in the request is invalid.'):
                    raise cle

        check_exception()
        if operation_name == u'GetRestApis':
            return AWSMock.api_gateway['api']
        elif operation_name == u'ImportRestApi':
            api_id = random_string(6)
            AWSMock.api_gateway['api']['items'].append(
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
        elif operation_name == u'CreateDeployment':
            return
        elif operation_name == u'GetDomainNames':
            return {'items': []}
        elif operation_name == u'CreateDomainName':
            return
        elif operation_name == u'DeleteBasePathMapping':
            return
        elif operation_name == u'CreateBasePathMapping':
            return
        elif operation_name == u'GetFunction':
            return {'Configuration': {
                'FunctionArn': 'arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:21423412341234:function:test'}}
        elif operation_name == u'Invoke':
            return {'Payload': StringIO('test_result')}
        elif operation_name == u'UpdateFunctionCode':
            return {'CodeSha256': '12341234123478912349172348912304712348',
                    'FunctionArn': 'arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:21423412341234:function:test'
                    }
        elif operation_name == u'DeleteAlias':
            return
        elif operation_name == u'PublishVersion':
            return {'Version': '1234123412341234234234'}
        elif operation_name == u'CreateAlias':
            return
        elif operation_name == u'AddPermission':
            return
        return orig(self, operation_name, kwarg)
