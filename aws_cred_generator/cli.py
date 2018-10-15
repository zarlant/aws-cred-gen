import click
import json
import boto3
import getpass
from botocore.exceptions import ClientError, ProfileNotFound, NoCredentialsError
from os import makedirs
from os.path import expanduser, exists as path_exists
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

class Config(object):
    aws_profile = None
    outputformat = "json"
    region = "us-west-2"
    awsconfig_dir = '/.aws/'
    awsconfigfile = '{config_dir}credentials'.format(config_dir=awsconfig_dir)

@click.group()
@click.option("--profile", required=True, help="The AWS credential profile to use when assuming the new role")
@click.option("--output", default="json", help="AWS Output format")
@click.option("--region", default="us-west-2")
def cli(profile, output, region):
    Config.aws_profile = profile
    Config.outputformat = output
    Config.region = region

@click.group()
def role():
    """Assume into AWS Roles"""

@click.command("assume")
@click.option("--role-arn", "-r", required=True)
@click.option("--session", "-s", required=True)
@click.option("--save-profile", "-p", required=True)
@click.option("--stdout", is_flag=True, default=False, help="Print the credentials to standard out")
@click.option("--external-id", "-e", required=False, default=None)
def assume_role(role_arn, session, save_profile, stdout, external_id):
    if not stdout:
        click.echo("Creating session with profile: {profile}".format(profile=Config.aws_profile))
    try:
        boto_session = boto3.Session(profile_name=Config.aws_profile)
    except ProfileNotFound:
        boto_session = boto3.Session()
    sts_client = boto_session.client("sts")
    if not stdout:
        click.echo("Assuming role: {role} with session: {session}".format(role=role_arn, session=session))

    assume_kwargs = {
        "RoleArn": role_arn,
        "RoleSessionName": session
    }
    if external_id is not None and external_id != "":
        assume_kwargs["ExternalId"] = external_id

    try:
        credentials = sts_client.assume_role(**assume_kwargs)
        if stdout:
            print(json.dumps(credentials["Credentials"], default=lambda x: str(x)))
        file_name = write_config(credentials, save_profile)
        if not stdout:
            click.echo("Credentials saved to {filename} under profile: {profile}"
                       .format(filename=file_name, profile=save_profile))
    except ClientError as e:
        click.echo("Error assuming role: {e}".format(e=e))
        click.get_current_context().exit(2)
    except NoCredentialsError as ne:
        click.echo("{e}: '{p}'".format(p=Config.aws_profile, e=ne))
        click.get_current_context().exit(3)

@click.command("assume-org")
@click.option("--account-number", "-a", required=True)
@click.option("--session", "-s")
@click.option("--save-profile", "-p", required=True, help="The profile in\
              which the generated credentials will be saved")
@click.option("--stdout", is_flag=True, default=False, help="Print the credentials to standard out")
@click.option("--external-id", "-e", required=False, default=None)
def assume_org_role(account_number, session, save_profile, stdout, external_id):
    """Used to assume the default OrganizationAccountAccessRole in the given account"""
    if not stdout:
        click.echo("Creating session with profile: {profile}".format(profile=Config.aws_profile))
    try:
        boto_session = boto3.Session(profile_name=Config.aws_profile)
    except ProfileNotFound:
        # We'll try and use the default session if we can't find the one passed
        # to us
        boto_session = boto3.Session()
    sts_client = boto_session.client("sts")
    role_arn = "arn:aws:iam::{account}:role/OrganizationAccountAccessRole".format(account=account_number)
    if session is None:
        session = getpass.getuser()
    if not stdout:
        click.echo("Assuming role: {role} with session: {session}".format(role=role_arn, session=session))
    try:
        assume_kwargs = {
            "RoleArn": role_arn,
            "RoleSessionName": session
        }
        if external_id is not None and external_id != "":
            assume_kwargs["ExternalId"] = external_id

        credentials = sts_client.assume_role(**assume_kwargs)
        if stdout:
            print(json.dumps(credentials["Credentials"], default=lambda x: str(x)))
        file_name = write_config(credentials, save_profile)
        if not stdout:
            click.echo("Credentials saved to {filename} under profile: {profile}"
                       .format(filename=file_name, profile=save_profile))
    except ClientError as e:
        click.echo("Error assuming role: {e}".format(e=e))
        click.get_current_context().exit(2)
    except NoCredentialsError as ne:
        click.echo("{e}: '{p}'".format(p=Config.aws_profile, e=ne))
        click.get_current_context().exit(3)


def write_config(credentials, save_profile):
    home = expanduser("~")

    if not path_exists(home + Config.awsconfig_dir):
        makedirs(home + Config.awsconfig_dir)

    filename = home + Config.awsconfigfile

    # Read in the existing config file
    config = configparser.RawConfigParser()
    config.read(filename)

    # Put the credentials into a specific profile instead of clobbering
    # the default credentials
    if not config.has_section(save_profile):
        config.add_section(save_profile)
    config.set(save_profile, 'output', Config.outputformat)
    config.set(save_profile, 'region', Config.region)
    config.set(save_profile, 'aws_access_key_id', credentials['Credentials']['AccessKeyId'])
    config.set(save_profile, 'aws_secret_access_key', credentials['Credentials']['SecretAccessKey'])
    config.set(save_profile, 'aws_session_token', credentials['Credentials']['SessionToken'])
    config.set(save_profile, 'expiration', credentials['Credentials']['Expiration'])

    # Write the updated config file
    with open(filename, 'w+') as configfile:
        config.write(configfile)

    return filename

cli.add_command(role)
role.add_command(assume_role)
role.add_command(assume_org_role)
