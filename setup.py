# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

try:
    long_description = open("README.rst").read()
except IOError:
    long_description = ""

setup(
    name="aws-cred-gen",
    version="0.0.6",
    description="Package uses sts to assume a role based on AWS profile passed in",
    license="MIT",
    author="Zacharias Thompson",
    packages=find_packages(),
    install_requires=["click", "boto3"],
    keywords = ["aws", "credentials", "aws sts"],
    long_description=long_description,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
    ],
    entry_points={"console_scripts": ["aws-cred-gen=aws_cred_generator.cli:cli", "aws_cred_gen=aws_cred_generator.cli:cli"]}
)
