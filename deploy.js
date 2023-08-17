const AWS = require('aws-sdk');
const archiver = require('archiver');
const fs = require('fs');

const { BUCKET_NAME, S3_PATH, SERVICE_NAME, awsProfile, awsRegion } = require('./package.json').appRunnerConfig;

// Configuring the AWS SDK
AWS.config.credentials = new AWS.SharedIniFileCredentials({ profile: awsProfile });
AWS.config.region = awsRegion;

const s3 = new AWS.S3();
const appRunner = new AWS.AppRunner();

async function zipDirectory(source, out) {
  const archive = archiver('zip', { zlib: { level: 9 } });
  const stream = fs.createWriteStream(out);

  return new Promise((resolve, reject) => {
    archive
      .directory(source, false)
      .on('error', err => reject(err))
      .pipe(stream);

    stream.on('close', () => resolve());
    archive.finalize();
  });
}

async function uploadToS3(bucket, key, filePath) {
  const fileStream = fs.createReadStream(filePath);
  const params = {
    Bucket: bucket,
    Key: key,
    Body: fileStream,
  };

  return s3.upload(params).promise();
}

async function doesServiceExist(serviceName) {
  try {
    await appRunner.describeService({ ServiceName: serviceName }).promise();
    return true;
  } catch (err) {
    if (err.code === 'ResourceNotFoundException') {
      return false;
    }
    throw err;
  }
}

async function deployToAppRunner() {
  await zipDirectory('./app_runner_service', 'app_runner_service.zip');
  await uploadToS3(BUCKET_NAME, `${S3_PATH}app_runner_service.zip`, 'app_runner_service.zip');

  const commonParams = {
    ServiceName: SERVICE_NAME,
    SourceConfiguration: {
      AuthenticationConfiguration: {},
      CodeRepository: {
        RepositoryUrl: `s3://${BUCKET_NAME}/${S3_PATH}app_runner_service.zip`,
        SourceType: 'S3'
      }
    },
    InstanceConfiguration: {
      Cpu: '1 vCPU',
      Memory: '2 GB'
    }
  };

  if (await doesServiceExist(SERVICE_NAME)) {
    return appRunner.updateService(commonParams).promise();
  } else {
    return appRunner.createService(commonParams).promise();
  }
}

deployToAppRunner()
  .then(() => {
    console.log('Deployment completed!');
  })
  .catch(error => {
    console.error('Error during deployment:', error);
  });
