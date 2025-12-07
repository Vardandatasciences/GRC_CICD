// Script to verify MySQL database connection
require("dotenv").config();
const mysql = require('mysql2/promise');

// Check if required environment variables are set
const requiredVars = [
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
  console.error('\nPlease create or update your .env file with these variables.');
  process.exit(1);
}

// Configure MySQL
const dbConfig = {
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
};

console.log('Database Configuration:');
console.log(`- Host: ${dbConfig.host}`);
console.log(`- User: ${dbConfig.user}`);
console.log(`- Database: ${dbConfig.database}`);

// Create connection pool
const pool = mysql.createPool(dbConfig);

// Test database connection
console.log('\nTesting database connection...');

async function testConnection() {
  try {
    const connection = await pool.getConnection();
    console.log('✅ Successfully connected to MySQL database!');
    
    // Check if s3_files table exists
    console.log('\nChecking if s3_files table exists...');
    const [tables] = await connection.query(
      "SHOW TABLES LIKE 's3_files'"
    );
    
    if (tables.length === 0) {
      console.log('❌ s3_files table does not exist.');
      console.log('\nCreating s3_files table...');
      
      try {
        await connection.query(`
          CREATE TABLE s3_files (
            id INT AUTO_INCREMENT PRIMARY KEY,
            url VARCHAR(255) NOT NULL,
            file_type VARCHAR(50) NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            user_id VARCHAR(100) NOT NULL,
            metadata JSON,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
          )
        `);
        console.log('✅ s3_files table created successfully!');
      } catch (createError) {
        console.error(`❌ Failed to create s3_files table: ${createError.message}`);
      }
    } else {
      console.log('✅ s3_files table exists.');
      
      // Check table structure
      console.log('\nChecking s3_files table structure...');
      const [columns] = await connection.query(
        "SHOW COLUMNS FROM s3_files"
      );
      
      const columnNames = columns.map(col => col.Field);
      console.log('Table columns:', columnNames.join(', '));
      
      // Check if metadata column exists
      if (!columnNames.includes('metadata')) {
        console.log('❌ metadata column is missing.');
        console.log('\nAdding metadata column...');
        
        try {
          await connection.query(
            "ALTER TABLE s3_files ADD COLUMN metadata JSON AFTER user_id"
          );
          console.log('✅ metadata column added successfully!');
        } catch (alterError) {
          console.error(`❌ Failed to add metadata column: ${alterError.message}`);
        }
      } else {
        console.log('✅ metadata column exists.');
      }
    }
    
    connection.release();
  } catch (error) {
    console.error(`❌ Database connection failed: ${error.message}`);
    
    if (error.code === 'ER_ACCESS_DENIED_ERROR') {
      console.error('\nAccess denied. Please check your username and password.');
    } else if (error.code === 'ER_BAD_DB_ERROR') {
      console.error(`\nDatabase '${dbConfig.database}' does not exist. Please create it first.`);
    } else if (error.code === 'ECONNREFUSED') {
      console.error(`\nConnection refused. Please check if MySQL is running on ${dbConfig.host}.`);
    }
  } finally {
    // Close the pool
    await pool.end();
  }
}

testConnection(); 