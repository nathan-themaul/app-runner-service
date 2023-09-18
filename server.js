const express = require('express');
const uploadRouter = require('./uploadRouter'); // Importing your upload route
const clusteringRouter = require('./clusteringRouter'); // Importing the new clustering route
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware to parse JSON requests
app.use(express.json());

// Enable CORS for all routes
app.use(cors());

app.use('/dev/upload', uploadRouter);

app.use('/dev/clustering', clusteringRouter);

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
