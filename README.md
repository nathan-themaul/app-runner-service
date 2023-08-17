# App Runner Service

This directory, app_runner_service, contains the specific code and configuration for deploying our application to AWS App Runner. It exists separately from the main application structure to streamline and isolate the deployment process for App Runner.

## Why This Directory Exists

We chose to use AWS App Runner for these components of our application due to AWS Lambda's constraints on payload size. AWS Lambda has a limited upload size, which was insufficient for some of our needs, especially for handling large files. AWS App Runner offers more flexibility in this regard, allowing us to handle bigger payloads without such constraints.

## Deployment to App Runner

To deploy the contents of this directory to AWS App Runner:

npm run deploy



