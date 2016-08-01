from __future__ import unicode_literals

import logging
import os
import shutil
import tempfile
import uuid
import zipfile
from random import choice
from string import ascii_lowercase

import boto3
from botocore.exceptions import ClientError
from git import Repo

from ..aws_eb.client import ElasticBeanstalkClient
from ..aws_s3.s3bucket import S3Bucket

LOGGER = logging.getLogger(__name__)


class EBPackage(object):
    def __init__(self, version, repository=None):
        """
        Helper to generate code package
        :param version: package code version, must be like uuid
        :type str
        :param repository: git repository url
        :type str
        """
        self.repository = repository or '.'
        LOGGER.info('Repository `{}`'.format(self.repository))
        self.version = version
        self.workspace = tempfile.gettempdir() + (''.join(choice(
            ascii_lowercase) for _ in range(10)))

        LOGGER.info('Create workspace `{}`'.format(self.workspace))
        self.zip_file = os.path.join(
            self.workspace, self.version + '.zip'
        )

    def create_deployment_package(self, additional_files):
        """
        Create deployment zip package
        :param additional_filesL list of file paths
        :return:
        """
        LOGGER.info('Create deployment package')
        Repo(path=self.repository).clone(path=self.workspace)
        if additional_files:
            for file_path in additional_files:
                shutil.copyfile(file_path,
                                os.path.join(
                                    self.workspace, file_path.split('/')[-1]
                                ))
        shutil.rmtree(os.path.join(self.workspace, '.git'))
        zip_file = zipfile.ZipFile(self.zip_file, "w", zipfile.ZIP_DEFLATED)
        abs_src = os.path.abspath(self.workspace)
        for root, _, files in os.walk(self.workspace):
            for filename in files:
                absname = os.path.abspath(os.path.join(root, filename))
                arcname = absname[len(abs_src) + 1:]
                zip_file.write(absname, arcname)
        zip_file.close()
        return self.zip_file


class EBDeployer(object):
    def __init__(self,
                 region_name,
                 aws_access_key_id,
                 aws_secret_access_key,
                 applications_config,
                 environment,
                 zip_file):
        """

        :param region_name: AWS region_name
        :type str
        :param aws_access_key_id: AWS credentials
        :type str
        :param aws_secret_access_key: AWS credentials
        :type str
        :param applications_config:

        Sample config:
        {
            'eb_reindex_worker': {
                'type': 'worker',
                'stack': '64bit Amazon Linux 2015.09 v2.0.8 running Python 2.7',

            }
        }
        :param environment: environment name
        :type str
        :param zip_file: path to code package
        :type str
        """
        self.applications_config = applications_config
        self.client = ElasticBeanstalkClient(
            region_name,
            aws_access_key_id,
            aws_secret_access_key
        )
        self.version = str(uuid.uuid4())
        bucket_name = self.client.instance.create_storage_location()['S3Bucket']
        self.bucket = S3Bucket(
            bucket_name,
            region_name,
            aws_access_key_id,
            aws_secret_access_key
        )
        self.bucket.upload_from_path(zip_file, self.version + '.zip')
        self.environment = environment
        LOGGER.info('Environment `{}`'.format(self.environment))

    def upload_certificate(self,
                           certificate_name,
                           certificate_body,
                           certificate_private_key,
                           certificate_chain):
        """

        :param certificate_body: SSL certificate
        :type str
        :param certificate_private_key: SSL private key
        :type str
        :param certificate_chain: SSL certificate chain
        :type str
        :return: IAM certificate id
        :rtype str
        """
        LOGGER.info('Upload certificate')
        iam = boto3.client('iam', **self.client.settings)
        try:
            response = iam.delete_server_certificate(
                ServerCertificateName=certificate_name
            )
        except ClientError:
            pass

        response = iam.upload_server_certificate(
            Path='/elasticbeanstalk/',
            ServerCertificateName=certificate_name,
            CertificateBody=certificate_body,
            PrivateKey=certificate_private_key,
            CertificateChain=certificate_chain
        )

        certificate_id = response[
            'ServerCertificate'
        ]['ServerCertificateMetadata']['Arn']
        LOGGER.info('IAM certificate id `{}`'.format(certificate_id))
        return certificate_id

    def __create_applications(self, application_name):
        if not self.client.instance.describe_applications(
                ApplicationNames=[application_name]
        )['Applications']:
            LOGGER.info('Create application `{}`'.format(application_name))
            self.client.instance.create_application(
                ApplicationName=application_name
            )

    def __deploy_environments(self, application_name, app_config,
                              certificate_id=None):
        LOGGER.info('Deploy environment')
        option_settings = [
            dict(OptionName="NumProcesses",
                 Namespace="aws:elasticbeanstalk:container:python",
                 Value=str(app_config.get('processes_number', 1))),
            dict(OptionName="NumThreads",
                 Namespace="aws:elasticbeanstalk:container:python",
                 Value=str(app_config.get('threads_number', 15))),
            dict(OptionName="MinSize",
                 ResourceName="AWSEBAutoScalingGroup",
                 Namespace="aws:autoscaling:asg",
                 Value=
                 str(app_config.get('instances_autoscaling_range',
                                    (1, 1))[0])),
            dict(OptionName="MaxSize",
                 ResourceName="AWSEBAutoScalingGroup",
                 Namespace="aws:autoscaling:asg",
                 Value=
                 str(app_config.get('instances_autoscaling_range',
                                    (1, 1))[1])),
            dict(OptionName="InstanceType",
                 Namespace="aws:autoscaling:launchconfiguration",
                 Value=app_config.get('instance_type', 't2.micro')),
            dict(Namespace='aws:elasticbeanstalk:container:python',
                 OptionName='WSGIPath',
                 Value=app_config.get('wsgi', 'application.py')
                 ),

        ]

        if certificate_id:
            option_settings.append(
                dict(Namespace="aws:elb:listener:80",
                     OptionName="ListenerEnabled",
                     Value="false"))
            option_settings.append(
                dict(Namespace="aws:elb:listener:443",
                     OptionName="ListenerProtocol",
                     Value="HTTPS"))
            option_settings.append(
                dict(Namespace="aws:elb:listener:443",
                     OptionName="SSLCertificateId",
                     Value=certificate_id))

        if not self.client.instance.describe_environments(
                ApplicationName=application_name,
                EnvironmentNames=[self.environment],
                IncludeDeleted=False
        )['Environments']:
            tier = {
                'Name': 'Worker',
                'Type': 'SQS/HTTP',
            } if app_config.get('type') == 'worker' else {
                'Name': 'WebServer',
                'Type': 'Standard',
            }
            self.client.instance.create_environment(
                ApplicationName=application_name,
                EnvironmentName=self.environment,
                Tier=tier,
                SolutionStackName=app_config['stack'],
                OptionSettings=option_settings,
                VersionLabel=self.version
            )
        else:
            self.client.instance.update_environment(
                ApplicationName=application_name,
                EnvironmentName=self.environment,
                VersionLabel=self.version,
                OptionSettings=option_settings

            )

    def __create_applications_version(self, application_name):
        self.client.instance.create_application_version(
            ApplicationName=application_name,
            Process=False,
            SourceBundle={
                'S3Bucket': self.bucket.bucket_name,
                'S3Key': self.version + ".zip",
            },
            VersionLabel=self.version,
        )

    def deploy(self, certificate_id=None):
        """
        :param certificate_id: IAM certificate id
        :type str
        :return:
        """
        for app_name, app_config in self.applications_config.items():
            self.__create_applications(app_name)
            self.__create_applications_version(app_name)
            args = [app_name, app_config]
            if certificate_id:
                args.append(certificate_id)
            self.__deploy_environments(*args)
