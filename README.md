# App Runner Service

This directory, app_runner_service, contains the specific code and configuration for deploying our application to AWS App Runner. It exists separately from the main application structure to streamline and isolate the deployment process for App Runner.

## Why This Directory Exists

We chose to use AWS App Runner for these components of our application due to AWS Lambda's constraints on payload size. AWS Lambda has a limited upload size, which was insufficient for some of our needs, especially for handling large files. AWS App Runner offers more flexibility in this regard, allowing us to handle bigger payloads without such constraints.

## Deployment to App Runner

To deploy the contents of this directory to AWS App Runner:

npm run deploy

To deploy to ECR :
1)
aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin 163137052994.dkr.ecr.eu-central-1.amazonaws.com
2) 
docker build -t agbo-app-runner .
3)
docker tag agbo-app-runner:latest 163137052994.dkr.ecr.eu-central-1.amazonaws.com/agbo-app-runner:latest
4)
docker push 163137052994.dkr.ecr.eu-central-1.amazonaws.com/agbo-app-runner:latest

