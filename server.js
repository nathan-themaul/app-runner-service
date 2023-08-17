const express = require('express');
const uploadRouter = require('./uploadRouter'); // Importing your upload route
const config = require('./config.json');

const app = express();
const PORT = process.env.PORT || 3000;

const environment = process.env.NODE_ENV || 'development';

const environmentConfig = config[environment];
Object.entries(environmentConfig).forEach(([key, value]) => {
  process.env[key] = value;
});

// Middleware to parse JSON requests
app.use(express.json());

// Use the upload route
app.use('/large-files-api/dev', uploadRouter);

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
