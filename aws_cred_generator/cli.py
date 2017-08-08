import click
import boto3
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
@click.option("--profile", help="The AWS credential profile to use when assuming the new role")
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
    credentials = sts_client.assume_role(RoleArn=role_arn, RoleSessionName=session)
    write_config(credentials, save_profile)

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

    # Write the updated config file
    with open(filename, 'w+') as configfile:
        config.write(configfile)

cli.add_command(role)
role.add_command(assume_role)
