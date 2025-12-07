// Script to start the S3 microservice
require('dotenv').config();
const fs = require('fs');
const path = require('path');

console.log('===============================================');
console.log('STARTING S3 MICROSERVICE');
console.log('===============================================\n');

// Check if .env file exists
const envPath = path.join(__dirname, '.env');
if (!fs.existsSync(envPath)) {
  console.error('❌ .env file not found!');
  console.log('Please create a .env file with your AWS and database configuration.');
  console.log('See S3_MICROSERVICE_README.md for details.');
  process.exit(1);
}

// Check required environment variables
const requiredVars = [
  'AWS_BUCKET_NAME',
  'AWS_REGION',
  'AWS_ACCESS_KEY_ID',
  'AWS_SECRET_ACCESS_KEY',
  'DB_HOST',
  'DB_USER',
  'DB_PASSWORD',
  'DB_NAME'
];

const missingVars = requiredVars.filter(varName => !process.env[varName]);
if (missingVars.length > 0) {
  console.error('❌ Missing required environment variables:');
  missingVars.forEach(varName => {
    console.error(`   - ${varName}`);
  });
  console.error('\nPlease update your .env file with these variables.');
  process.exit(1);
}

// Start the microservice
try {
  const port = process.env.AWS_PORT || 5000;
  console.log(`Starting S3 microservice on port ${port}...`);
  
  // Load the microservice
  const s3Service = require('./s3_microservices.js');
  
  console.log(`\n✅ S3 microservice started successfully on port ${port}`);
  console.log('Press Ctrl+C to stop the service.');
  
  // Handle graceful shutdown
  process.on('SIGINT', () => {
    console.log('\nShutting down S3 microservice...');
    process.exit(0);
  });
} catch (error) {
  console.error(`\n❌ Failed to start S3 microservice: ${error.message}`);
  console.error(error.stack);
  process.exit(1);
} 