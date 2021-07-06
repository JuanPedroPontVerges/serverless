# SERVERLESS

This backend is built on [Serverless](https://www.serverless.com//). 

### Requirements

- Serverless
- Docker & Docker-Compose
- AWS CLI (if you dont know how to put AWS keys in enviroment variables)

### Installation

```bash
# Installs serverless-python-requirements package to bundle your python dependencies specified in your requirements.txt
$ npm install
# Configures your AWS Keys for creating a Lambda service
$ aws configure
```

### Running Locally

```bash
# Starts the service
$ serverless deploy

# Stop the service
$ serverless remove
```

### Notes
You must have your AWS Keys in your env variables

```bash
$ aws configure
```