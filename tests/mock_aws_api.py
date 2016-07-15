import botocore
from botocore.exceptions import ClientError

orig = botocore.client.BaseClient._make_api_call


def mock_make_api_call(self, operation_name, kwarg):
    def check_exception():
        try:
            orig(self, operation_name, kwarg)
        except ClientError as cle:
            if not cle.message.endswith(
                    'The security token included in the request is invalid.'):
                raise cle

    check_exception()
    if operation_name == u'GetRestApis':
        if not getattr(mock_make_api_call, 'api_gateway', False):
            return {'items': []}
        else:
            return {'items': [{'name': 'Sample', 'id': 'APP_ID'}]}
    elif operation_name == u'ImportRestApi':
        setattr(mock_make_api_call, 'api_gateway', True)
        return {'id': 'APP_ID'}
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
    return orig(self, operation_name, kwarg)
