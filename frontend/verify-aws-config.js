// Script to verify AWS credentials and configuration
require("dotenv").config();
const S3 = require("aws-sdk/clients/s3");

// Check if required environment variables are set
const requiredVars = [
  'AWS_BUCKET_NAME',
  'AWS_REGION',
  'AWS_ACCESS_KEY_ID',
  'AWS_SECRET_ACCESS_KEY'
];

const missingVars = requiredVars.filter(varName => !process.env[varName]);

if (missingVars.length > 0) {
  console.error('❌ Missing required environment variables:');
  missingVars.forEach(varName => {
    console.error(`   - ${varName}`);
  });
  console.error('\nPlease create or update your .env file with these variables.');
  process.exit(1);
}

// Configure AWS S3
const bucketName = process.env.AWS_BUCKET_NAME;
const region = process.env.AWS_REGION;
const accessKeyId = process.env.AWS_ACCESS_KEY_ID;
const secretAccessKey = process.env.AWS_SECRET_ACCESS_KEY;

console.log('AWS Configuration:');
console.log(`- Region: ${region}`);
console.log(`- Bucket: ${bucketName}`);
console.log(`- Access Key ID: ${accessKeyId.substring(0, 4)}...${accessKeyId.substring(accessKeyId.length - 4)}`);
console.log(`- Secret Access Key: ${'*'.repeat(secretAccessKey.length)}`);

// Create S3 client
const s3 = new S3({
  region,
  accessKeyId,
  secretAccessKey,
});

// Test S3 connection
console.log('\nTesting S3 connection...');

const params = {
  Bucket: bucketName,
  MaxKeys: 1
};

s3.listObjects(params, function(err, data) {
  if (err) {
    console.error(`❌ S3 connection failed: ${err.code}`);
    console.error(`Error message: ${err.message}`);
    
    if (err.code === 'InvalidAccessKeyId') {
      console.error('\nThe AWS Access Key ID you provided is invalid. Please check your credentials.');
    } else if (err.code === 'SignatureDoesNotMatch') {
      console.error('\nThe AWS Secret Access Key you provided is invalid. Please check your credentials.');
    } else if (err.code === 'NoSuchBucket') {
      console.error(`\nThe bucket "${bucketName}" does not exist. Please create it or check the name.`);
    } else if (err.code === 'NetworkingError') {
      console.error('\nNetwork error. Please check your internet connection.');
    }
    
    process.exit(1);
  } else {
    console.log('✅ Successfully connected to S3!');
    console.log(`Bucket "${bucketName}" exists and is accessible.`);
    
    // Show a few objects in the bucket if any
    if (data.Contents && data.Contents.length > 0) {
      console.log(`\nFound ${data.Contents.length} object(s) in the bucket.`);
      console.log('First few objects:');
      data.Contents.slice(0, 5).forEach((object, i) => {
        console.log(`${i+1}. ${object.Key} (${formatBytes(object.Size)})`);
      });
    } else {
      console.log('\nThe bucket is empty.');
    }
  }
});

// Helper function to format bytes
function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];
  
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
} 