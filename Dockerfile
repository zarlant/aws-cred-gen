FROM python:alpine

WORKDIR /opt/aws_credgen
COPY . .

RUN pip install -r requirements.txt
RUN pip install . 

ENTRYPOINT ["/usr/local/bin/aws-cred-gen"]
