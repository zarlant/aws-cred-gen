# AWS Cred Gen

A utility script for generating new AWS credentials with STS and saving them under a new profile.

## Examples

Assume into a target role using the profile example and saving the resulting credentials as target-creds

`aws-cred-gen --profile example role assume -r arn:aws:iam::123412341234:role/MyExampleRole -s identifying-session -p target-creds`

Assume into the OrganizationAccountAccessRole from the main payer account:

`aws-cred-gen --profile payer-profile role assume-org -a 123412314123 -p target-account`

## Build with Docker:
`docker build -t aws-cred-gen .`

## Run locally as a sandboxed CLI:
`alias aws-cred-gen="docker run -it --rm -v ~/.aws/:/root/.aws aws-cred-gen`
