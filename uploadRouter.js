// App Runner Service
const express = require('express');
const axios = require('axios'); // For making HTTP calls
const router = express.Router();
const multer = require('multer');
const upload = multer();

const fileFields = [
  { name: 'rawLog', maxCount: 1 },
  { name: 'nmeaTimestampedLog', maxCount: 1 },
  { name: 'ubxTimestampedLog', maxCount: 1 },
  { name: 'systemLog', maxCount: 1 },
  { name: 'debugLog', maxCount: 1 },
];

const uploadMiddleware = upload.fields(fileFields);

router.post('/logbook/upload', uploadMiddleware, async (req, res) => {
    try {
        const files = [
            req.files['rawLog'][0],
            req.files['nmeaTimestampedLog'][0],
            req.files['ubxTimestampedLog'][0],
            req.files['systemLog'][0],
            req.files['debugLog'][0],
        ];

        // Process the files to create unique filenames
        const processedFiles = await Promise.all(files.map(getUniqueFilename));

        // Upload files to S3
        await Promise.all(processedFiles.map(uploadToS3));

        const dataToSendToLambda = {
            fileNames: {
                rawLogFilename: processedFiles[0].newFilename,
                nmeaTimestampedLogFilename: processedFiles[1].newFilename,
                ubxTimestampedLogFilename: processedFiles[2].newFilename,
                systemLogFilename: processedFiles[3].newFilename,
                debugLogFilename: processedFiles[4].newFilename,
            },
            body: req.body  // Including other request details you might need for processing
        };

        // Now, make an HTTP call to your Lambda API Gateway endpoint
        const lambdaResponse = await axios.post('https://yswxkz0r41.execute-api.eu-central-1.amazonaws.com/dev/logbook/upload-with-app-runner', dataToSendToLambda);

        res.status(lambdaResponse.status).send(lambdaResponse.data);

    } catch (error) {
        console.log(error);
        res.status(500).send(`Error processing the request: ${error.message}`);
    }
});

module.exports = router;
