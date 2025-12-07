// Comprehensive troubleshooting script for S3 microservice
require("dotenv").config();
const http = require('http');
const fs = require('fs');
const path = require('path');
const S3 = require("aws-sdk/clients/s3");
const mysql = require('mysql2/promise');

console.log('===============================================');
console.log('S3 MICROSERVICE TROUBLESHOOTING TOOL');
console.log('===============================================\n');

// Step 1: Check if .env file exists
console.log('Step 1: Checking .env file...');
const envPath = path.join(__dirname, '.env');

if (!fs.existsSync(envPath)) {
  console.error('❌ .env file not found!');
  console.log('Please create a .env file with your AWS and database configuration.');
  console.log('Example:');
  console.log(`
# AWS S3 Configuration
AWS_BUCKET_NAME=your-s3-bucket-name
AWS_REGION=your-aws-region
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_PORT=5000

# Database Configuration
DB_HOST=localhost
DB_USER=your-db-username
DB_PASSWORD=your-db-password
DB_NAME=grc
  `);
  process.exit(1);
} else {
  console.log('✅ .env file found');
  
  // Check required variables
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
  } else {
    console.log('✅ All required environment variables are set');
  }
}

// Step 2: Check if S3 microservice is running
console.log('\nStep 2: Checking if S3 microservice is running...');

function checkServiceRunning() {
  return new Promise((resolve) => {
    const options = {
      hostname: 'localhost',
      port: process.env.AWS_PORT || 5000,
      path: '/api/health',
      method: 'GET',
      timeout: 3000
    };
    
    const req = http.request(options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        if (res.statusCode === 200) {
          try {
            const response = JSON.parse(data);
            console.log('✅ S3 microservice is running');
            console.log(`Status: ${response.status}`);
            console.log(`Message: ${response.message}`);
            if (response.s3) console.log(`S3 Connection: ${response.s3}`);
            if (response.database) console.log(`Database Connection: ${response.database}`);
            resolve(true);
          } catch (e) {
            console.log('⚠️ S3 microservice responded with status 200 but invalid JSON');
            console.log(`Raw response: ${data}`);
            resolve(false);
          }
        } else {
          console.log(`❌ S3 microservice responded with status code: ${res.statusCode}`);
          console.log(`Response: ${data}`);
          resolve(false);
        }
      });
    });
    
    req.on('error', (error) => {
      console.error('❌ S3 microservice is not running or not accessible');
      console.error(`Error details: ${error.message}`);
      console.log('\nTo start the S3 microservice, run:');
      console.log('node start-s3-service.js');
      resolve(false);
    });
    
    req.on('timeout', () => {
      console.error('❌ S3 microservice request timed out. The service might be running but not responding properly.');
      req.destroy();
      resolve(false);
    });
    
    req.end();
  });
}

// Step 3: Check AWS S3 configuration
async function checkAwsConfig() {
  console.log('\nStep 3: Checking AWS S3 configuration...');
  
  // Configure AWS S3
  const bucketName = process.env.AWS_BUCKET_NAME;
  const region = process.env.AWS_REGION;
  const accessKeyId = process.env.AWS_ACCESS_KEY_ID;
  const secretAccessKey = process.env.AWS_SECRET_ACCESS_KEY;
  
  if (!bucketName || !region || !accessKeyId || !secretAccessKey) {
    console.error('❌ Missing AWS configuration variables');
    return false;
  }
  
  console.log(`- Region: ${region}`);
  console.log(`- Bucket: ${bucketName}`);
  console.log(`- Access Key ID: ${accessKeyId.substring(0, 4)}...${accessKeyId.substring(accessKeyId.length - 4)}`);
  
  // Create S3 client
  const s3 = new S3({
    region,
    accessKeyId,
    secretAccessKey,
  });
  
  // Test S3 connection
  console.log('Testing S3 connection...');
  
  const params = {
    Bucket: bucketName,
    MaxKeys: 1
  };
  
  try {
    const data = await s3.listObjects(params).promise();
    console.log('✅ Successfully connected to S3!');
    console.log(`Bucket "${bucketName}" exists and is accessible.`);
    return true;
  } catch (err) {
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
    
    return false;
  }
}

// Step 4: Check database configuration
async function checkDbConfig() {
  console.log('\nStep 4: Checking database configuration...');
  
  // Configure MySQL
  const dbConfig = {
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME,
    waitForConnections: true,
    connectionLimit: 1,
    queueLimit: 0
  };
  
  if (!dbConfig.host || !dbConfig.user || !dbConfig.password || !dbConfig.database) {
    console.error('❌ Missing database configuration variables');
    return false;
  }
  
  console.log(`- Host: ${dbConfig.host}`);
  console.log(`- User: ${dbConfig.user}`);
  console.log(`- Database: ${dbConfig.database}`);
  
  // Create connection pool
  const pool = mysql.createPool(dbConfig);
  
  try {
    const connection = await pool.getConnection();
    console.log('✅ Successfully connected to MySQL database!');
    
    // Check if s3_files table exists
    console.log('Checking if s3_files table exists...');
    const [tables] = await connection.query(
      "SHOW TABLES LIKE 's3_files'"
    );
    
    if (tables.length === 0) {
      console.log('❌ s3_files table does not exist.');
      console.log('Please run verify-db-config.js to create the table.');
      connection.release();
      await pool.end();
      return false;
    } else {
      console.log('✅ s3_files table exists.');
      
      // Check table structure
      console.log('Checking s3_files table structure...');
      const [columns] = await connection.query(
        "SHOW COLUMNS FROM s3_files"
      );
      
      const columnNames = columns.map(col => col.Field);
      console.log('Table columns:', columnNames.join(', '));
      
      // Check if metadata column exists
      if (!columnNames.includes('metadata')) {
        console.log('❌ metadata column is missing.');
        console.log('Please run verify-db-config.js to add the metadata column.');
        connection.release();
        await pool.end();
        return false;
      } else {
        console.log('✅ metadata column exists.');
      }
    }
    
    connection.release();
    await pool.end();
    return true;
  } catch (error) {
    console.error(`❌ Database connection failed: ${error.message}`);
    
    if (error.code === 'ER_ACCESS_DENIED_ERROR') {
      console.error('\nAccess denied. Please check your username and password.');
    } else if (error.code === 'ER_BAD_DB_ERROR') {
      console.error(`\nDatabase '${dbConfig.database}' does not exist. Please create it first.`);
    } else if (error.code === 'ECONNREFUSED') {
      console.error(`\nConnection refused. Please check if MySQL is running on ${dbConfig.host}.`);
    }
    
    try {
      await pool.end();
    } catch (e) {
      // Ignore pool end errors
    }
    
    return false;
  }
}

// Run all checks
async function runAllChecks() {
  const serviceRunning = await checkServiceRunning();
  
  if (!serviceRunning) {
    console.log('\n❌ S3 microservice is not running. Please start it with:');
    console.log('node start-s3-service.js');
    console.log('\nThen run this troubleshooting script again.');
    return;
  }
  
  const awsConfigOk = await checkAwsConfig();
  const dbConfigOk = await checkDbConfig();
  
  if (awsConfigOk && dbConfigOk) {
    console.log('\n✅ All checks passed! Your S3 microservice configuration is correct.');
    console.log('You can now use file uploads in the CreatePolicy.vue component.');
  } else {
    console.log('\n❌ Configuration issues detected. Please fix them before proceeding.');
    
    if (!awsConfigOk) {
      console.log('- AWS S3 configuration issues need to be fixed');
    }
    
    if (!dbConfigOk) {
      console.log('- Database configuration issues need to be fixed');
    }
  }
}

runAllChecks(); 