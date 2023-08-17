// utils/awsUtils.js
const { s3 } = require('./AWSconfig');
const path = require('path');

async function uploadToS3(file) {
  const folderName = 'payloads'; 

  const params = {
    Bucket: 'alphaground-uploads',
    Key: `${folderName}/${file.fieldname}/${file.newFilename}`,
    Body: file.buffer,
  };

  return s3.upload(params).promise();
}

async function getUniqueFilename(file) {
  const folderName = 'payloads';

  let counter = 0;
  let baseFilename = path.parse(file.originalname).name;
  let extension = path.parse(file.originalname).ext;
  let newFilename = `${baseFilename}${extension}`;

  // check if file already exists
  while (true) {
    try {
      const paramsHead = {
        Bucket: 'alphaground-uploads',
        Key: `${folderName}/${file.fieldname}/${newFilename}`,
      };

      // Check if file already exists
      await s3.headObject(paramsHead).promise();

      // If the previous promise didn't reject, the object exists so we increment the counter
      counter++;
      newFilename = `${baseFilename}-${counter}${extension}`;
    } catch (err) {
      if (err.code === 'NotFound') {
        // If the object does not exist, we can break the loop and use this filename
        break;
      } else {
        // If the error is not 'NotFound', it's another unexpected error so we should throw it
        throw err;
      }
    }
  }

  // Add new filename to the file object
  file.newFilename = newFilename;

  return file;
}