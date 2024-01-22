const express = require('express');
const { spawn } = require('child_process');

const router = express.Router();


const runClustering = async (method) => {
    return new Promise((resolve, reject) => {
        const pythonProcess = spawn('python', ['./boundaries_clustering/main.py', 'all', method]);

        let outputData = '';
        let errorData = '';

        pythonProcess.stdout.on('data', (data) => {
            outputData += data.toString();
        });

        pythonProcess.stderr.on('data', (data) => {
            errorData += data.toString();
        });

        pythonProcess.on('close', (code) => {
        if (code !== 0 || errorData) {
            reject(`stderr: ${errorData}`);
        } else {
            try {
                const result = JSON.parse(outputData);
                resolve(result);
            } catch (parseError) {
                reject(`Error parsing JSON from Python script: ${parseError}`);
            }
        }
        });
    });
};


const runStep = async (step, data = null, method = null) => {
    return new Promise((resolve, reject) => {
      const pythonProcess = spawn('python', ['./boundaries_clustering/main.py', step]);
      // Write data and method to the stdin of the Python process
      pythonProcess.stdin.write(JSON.stringify({ data, method }));
      pythonProcess.stdin.end();
  
      let outputData = '';
      let errorData = '';
  
      pythonProcess.stdout.on('data', (data) => {
        outputData += data.toString();
      });
  
      pythonProcess.stderr.on('data', (data) => {
        errorData += data.toString();
      });
  
      pythonProcess.on('close', (code) => {
        if (code !== 0 || errorData) {
          reject(`stderr: ${errorData}`);
        } else {
          try {
            const result = JSON.parse(outputData);
            resolve(result);
          } catch (parseError) {
            reject(`Error parsing JSON from Python script: ${parseError}`);
          }
        }
      });
    });
  };
  
router.get('/boundaries', async (req, res) => {
    // Extract all method query parameters
    console.log('req.query:', req.query);
    const methods = Object.keys(req.query).filter(key => key.startsWith('method')).map(key => req.query[key]);
    try {
        const results = await Promise.all(methods.map(method => runClustering(method)));
        console.log('results:', results);
        res.send(results);
    } catch (error) {
        res.status(500).send(error);
    }
});

router.get('/test', (req, res) => {
  res.send('Test endpoint is working');
});

router.post('/step/:step', async (req, res) => {
    const { step } = req.params;
    const { data, method } = req.body;
    try {
        const result = await runStep(step, data, method);
        res.send(result);
    } catch (error) {
        res.status(500).send(error);
    }
});

module.exports = router;
