const express = require('express');
const { spawn } = require('child_process');

const router = express.Router();

router.post('/boundaries', (req, res) => {
    const pythonProcess = spawn('python', ['python/clustering.py']);
    
    let output = "";
    
    pythonProcess.stdout.on('data', (data) => {
        output += data.toString();
    });
    
    pythonProcess.stderr.on('data', (data) => {
        console.error(`Python stderr: ${data}`);
    });
    
    pythonProcess.on('close', (code) => {
        if (code !== 0) {
            return res.status(500).send(`Python script failed to execute. Code: ${code}`);
        }
        res.status(200).json(JSON.parse(output));
    });
    
    pythonProcess.stdin.write(JSON.stringify(req.body));
    pythonProcess.stdin.end();
});

module.exports = router;
