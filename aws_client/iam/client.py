from __future__ import unicode_literals

from botocore.exceptions import ClientError

from ..base_client import BaseAWSClient


class IAMClient(BaseAWSClient):
    """
     AWS IAM  Service client
    """

    def __init__(self,
                 region_name,
                 aws_access_key_id,
                 aws_secret_access_key):
        """
        :param region_name: AWS region name
        :param aws_access_key_id: AWS credentials
        :param aws_secret_access_key: AWS credentials
        """
        super(IAMClient, self).__init__(
            service='iam',
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

    def upload_certificate(self,
                           certificate_name,
                           certificate_path,
                           certificate_body,
                           certificate_private_key,
                           certificate_chain):
        """
        :param certificate_name: Name for certificate
        :type str
        :param certificate_path: Upload path
        :type str
        :param certificate_body: SSL certificate
        :type str
        :param certificate_private_key: SSL private key
        :type str
        :param certificate_chain: SSL certificate chain
        :type str
        :return: IAM certificate id
        :rtype str
        """

        try:
            self.instance.delete_server_certificate(
                ServerCertificateName=certificate_name,
            )
        except ClientError:
            pass
        response = None
        try:
            response = self.instance.upload_server_certificate(
                Path='/{}/{}/'.format(certificate_path, certificate_name),
                ServerCertificateName=certificate_name,
                CertificateBody=certificate_body,
                PrivateKey=certificate_private_key,
                CertificateChain=certificate_chain
            )
        except ClientError:
            certificate_arn = response and \
                              response['ServerCertificateMetadata'][
                                  'Arn']
            return certificate_arn

    def get_certificate_arn(self, certificate_name):
        """

        :param certificate_name:
        :return:
        """
        response = self.instance.get_server_certificate(
            ServerCertificateName=certificate_name
        )
        return response[
            'ServerCertificate'
        ]['ServerCertificateMetadata']['Arn']
