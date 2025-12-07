// Script to check if the S3 microservice is running
const http = require('http');

const options = {
  hostname: 'localhost',
  port: 5000,
  path: '/api/health',
  method: 'GET',
  timeout: 3000
};

console.log('Checking if S3 microservice is running...');

const req = http.request(options, (res) => {
  let data = '';
  
  res.on('data', (chunk) => {
    data += chunk;
  });
  
  res.on('end', () => {
    if (res.statusCode === 200) {
      try {
        const response = JSON.parse(data);
        console.log('✅ S3 microservice is running on port 5000');
        console.log(`Response: ${JSON.stringify(response)}`);
      } catch (e) {
        console.log('⚠️ S3 microservice responded with status 200 but invalid JSON');
        console.log(`Raw response: ${data}`);
      }
    } else {
      console.log(`❌ S3 microservice responded with status code: ${res.statusCode}`);
      console.log(`Response: ${data}`);
    }
  });
});

req.on('error', (error) => {
  console.error('❌ S3 microservice is not running or not accessible');
  console.error(`Error details: ${error.message}`);
  console.log('\nTo start the S3 microservice, run:');
  console.log('node start-s3-service.js');
});

req.on('timeout', () => {
  console.error('❌ S3 microservice request timed out. The service might be running but not responding properly.');
  req.destroy();
});

req.end(); 