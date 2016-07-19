from distutils.core import setup

setup(
    name='col-aws-clients',
    packages=['col-aws-clients'],  # this must be the same as the name above
    version='0.1',
    description='Collectrium AWS clients',
    url='https://github.com/collectrium/col-aws-clients',
    # use the URL to the github repo
    download_url='https://github.com/collectrium/col-aws-clients/tarball/0.1',
    # I'll explain this in a second
    keywords=['AWS', 'Amazon Web Services', 'SQS', "S3", "Lambda"],
    # arbitrary keywords
    classifiers=[],
)
