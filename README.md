# SERVERLESS

This backend is built on [Serverless](https://www.serverless.com//). 

### Requirements

- Serverless account [Register in servless](https://app.serverless.com/)
- Docker & Docker-Compose
- AWS CLI (if you dont know how to put AWS keys in enviroment variables)
- NPM
### Installation

```bash
# Installs serverless-python-requirements package to bundle your python dependencies specified in your requirements.txt
$ npm install -g serverless
$ serverless
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