const AWS = require('aws-sdk');

// Use this code snippet in your app.
// If you need more information about configurations or implementing the sample code, visit the AWS docs:
// https://docs.aws.amazon.com/sdk-for-javascript/v3/developer-guide/getting-started.html

const {
    SecretsManagerClient,
    GetSecretValueCommand,
  } = require("@aws-sdk/client-secrets-manager");
  
const secret_name = "app-runner-service/development/access-key";

const client = new SecretsManagerClient({
region: "eu-central-1",
});

let response;

try {
response = await client.send(
    new GetSecretValueCommand({
    SecretId: secret_name,
    VersionStage: "AWSCURRENT", // VersionStage defaults to AWSCURRENT if unspecified
    })
);
} catch (error) {
// For a list of exceptions thrown, see
// https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
throw error;
}

const secretObject = JSON.parse(response.SecretString);
const ACCESS_KEY_ID = secretObject.ACCESS_KEY_ID;
const SECRET_ACCESS_KEY = secretObject.SECRET_ACCESS_KEY;

// Load AWS credentials from file
AWS.config.update({
  accessKeyId: ACCESS_KEY_ID,
  secretAccessKey: SECRET_ACCESS_KEY,
  region: process.env.AWS_COGNITO_REGION,
});

module.exports = {
  s3: new AWS.S3(),
  cognitoIdentityServiceProvider: new AWS.CognitoIdentityServiceProvider(),
};