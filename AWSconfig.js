const AWS = require('aws-sdk');
const {
    SecretsManagerClient,
    GetSecretValueCommand,
} = require("@aws-sdk/client-secrets-manager");

const { awsRegion } = require('./package.json').appRunnerConfig;
const secret_name = "app-runner-service/development/access-key";

const client = new SecretsManagerClient({
    region: "eu-central-1",
});

async function fetchSecrets() {
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
    return JSON.parse(response.SecretString);
}

// You can now call the fetchSecrets function and use the results as required:
fetchSecrets().then(secrets => {
    const ACCESS_KEY_ID = secrets.ACCESS_KEY_ID;
    const SECRET_ACCESS_KEY = secrets.SECRET_ACCESS_KEY;

    // Load AWS credentials from file
    AWS.config.update({
        accessKeyId: ACCESS_KEY_ID,
        secretAccessKey: SECRET_ACCESS_KEY,
        region: "eu-central-1",
    });
}).catch(error => {
    console.error("Error fetching secrets:", error);
});

module.exports = {
    s3: new AWS.S3(),
    cognitoIdentityServiceProvider: new AWS.CognitoIdentityServiceProvider(),
};
