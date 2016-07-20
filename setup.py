#!/usr/bin/env python
import pip
from setuptools import setup, find_packages
from pip.req import parse_requirements


try:
    install_reqs = parse_requirements(
        "requirements.txt",
        session=pip.download.PipSession(),
    )
except AttributeError:
    #for pip==1.4.1
    install_reqs = parse_requirements("requirements.txt")

reqs = [str(ir.req) for ir in install_reqs if ir.req]


packages = find_packages(
    exclude=[
        '*.tests', '*.tests.*', 'tests.*', 'tests',
        '*.test', '*.test.*', 'test.*', 'test',
    ]
)


setup(
    name='col_aws_clients',
    packages=['col_aws_clients'],  # this must be the same as the name above
    version='0.1',
    description='Collectrium AWS clients',
    url='https://github.com/collectrium/col-aws-clients',
    # use the URL to the github repo
    download_url='https://github.com/collectrium/col-aws-clients/tarball/0.1',
    # I'll explain this in a second
    keywords=['AWS', 'Amazon Web Services', 'SQS', "S3", "Lambda", "APIGateway"],
    # arbitrary keywords
    classifiers=[],
)
