#!/usr/bin/env python
from collections import namedtuple

from setuptools import find_packages, setup


def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    Requirements = namedtuple('Requirements', ('pypi', 'links'))
    lineiter = (line.strip() for line in open(filename))
    parsed_reqs = [line for line in lineiter if
                   line and not line.startswith("#")]

    result = Requirements(pypi=[], links=[])

    for _l in parsed_reqs:
        if _l.startswith('git+'):
            result.links.append(_l)
        else:
            result.pypi.append(_l)

    return result


reqs = parse_requirements('requirements.txt')

packages = find_packages(
    exclude=[
        '*.tests', '*.tests.*', 'tests.*', 'tests',
        '*.test', '*.test.*', 'test.*', 'test', 'examples'
    ]
)

setup(
    name='aws_client',
    author='collectrium',
    author_email='support@collectrium.com',
    packages=packages,
    install_requires=reqs.pypi,
    dependency_links=reqs.links,
    package_data={'': ['*.ini', '*.txt', '*.html', '*.json', '*.yml', '*.csv']},
    version='0.10',
    description='Collectrium AWS clients',
    url='https://github.com/collectrium/col-aws-clients',
    keywords=['AWS', 'Amazon Web Services', 'SQS', "S3", "Lambda",
              "APIGateway"],
    classifiers=[
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
)
