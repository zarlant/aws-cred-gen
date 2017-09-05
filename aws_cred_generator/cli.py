import click
import boto3
import getpass
from botocore.exceptions import ClientError
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
    """Manage AWS Roles"""

@click.command("assume")
@click.option("--role-arn", "-r", required=True)
@click.option("--session", "-s", required=True)
@click.option("--save-profile", "-p", required=True)
def assume_role(role_arn, session, save_profile):
    click.echo("Creating session with profile: {profile}".format(profile=Config.aws_profile))
    boto_session = boto3.Session(profile_name=Config.aws_profile)
    sts_client = boto_session.client("sts")
    click.echo("Assuming role: {role} with session: {session}".format(role=role_arn, session=session))
    try:
        credentials = sts_client.assume_role(RoleArn=role_arn, RoleSessionName=session)
        file_name = write_config(credentials, save_profile)
        click.echo("Credentials saved to {filename} under profile: {profile}"
                   .format(filename=file_name, profile=save_profile))
    except ClientError as e:
        click.echo("Error assuming role: {e}".format(e=e))
        click.get_current_context().exit(2)

@click.command("assume-org")
@click.option("--account-number", "-a", required=True)
@click.option("--session", "-s")
@click.option("--save-profile", "-p", required=True, help="The profile in\
              which the generated credentials will be saved")
def assume_org_role(account_number, session, save_profile):
    """Used to assume the default OrganizationAccountAccessRole in the given account"""
    click.echo("Creating session with profile: {profile}".format(profile=Config.aws_profile))
    boto_session = boto3.Session(profile_name=Config.aws_profile)
    sts_client = boto_session.client("sts")
    role_arn = "arn:aws:iam::{account}:role/OrganizationAccountAccessRole".format(account=account_number)
    if session is None:
        session = getpass.getuser()
    click.echo("Assuming role: {role} with session: {session}".format(role=role_arn, session=session))
    try: 
        credentials = sts_client.assume_role(RoleArn=role_arn, RoleSessionName=session)
        file_name = write_config(credentials, save_profile)
        click.echo("Credentials saved to {filename} under profile: {profile}"
                   .format(filename=file_name, profile=save_profile))
    except ClientError as e:
        click.echo("Error assuming role: {e}".format(e=e))
        click.get_current_context().exit(2)


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
