/**
 * Database Schema Inspector
 * 
 * This script checks the database schema for the audit_findings table
 * to help diagnose issues with saving URLs to the Evidence column.
 */

require("dotenv").config();
const mysql = require('mysql2/promise');

// Configure MySQL
const dbConfig = {
  host: process.env.DB_HOST || 'localhost',
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || 'root',
  database: process.env.DB_NAME || 'grc',
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
};

console.log('Database Configuration:');
console.log(`- Host: ${dbConfig.host}`);
console.log(`- User: ${dbConfig.user}`);
console.log(`- Database: ${dbConfig.database}`);

async function checkSchema() {
  // Create a connection pool
  const pool = mysql.createPool(dbConfig);
  
  try {
    console.log('========== CHECKING DATABASE SCHEMA ==========');
    
    // Get a connection from the pool
    const connection = await pool.getConnection();
    
    try {
      // Get table schema
      console.log('Checking audit_findings table schema...');
      const [columns] = await connection.execute('DESCRIBE audit_findings');
      
      console.log('audit_findings table columns:');
      columns.forEach(column => {
        console.log(`- ${column.Field}: ${column.Type} ${column.Null === 'YES' ? 'NULL' : 'NOT NULL'} ${column.Default ? `DEFAULT ${column.Default}` : ''}`);
        
        // Check if the Evidence column is large enough for URLs
        if (column.Field === 'Evidence') {
          if (column.Type.includes('varchar')) {
            const match = column.Type.match(/varchar\((\d+)\)/i);
            if (match && match[1]) {
              const size = parseInt(match[1]);
              console.log(`  Evidence column size: ${size} characters`);
              
              if (size < 500) {
                console.log(`  WARNING: Evidence column might be too small for long URLs. Consider altering to TEXT type.`);
              }
            }
          } else if (column.Type === 'text') {
            console.log(`  Evidence column is TEXT type which can store up to 65,535 characters.`);
          } else if (column.Type === 'mediumtext') {
            console.log(`  Evidence column is MEDIUMTEXT type which can store up to 16,777,215 characters.`);
          } else if (column.Type === 'longtext') {
            console.log(`  Evidence column is LONGTEXT type which can store up to 4,294,967,295 characters.`);
          }
        }
      });
      
      // Check for indexes
      console.log('\nChecking indexes on audit_findings table...');
      const [indexes] = await connection.execute('SHOW INDEX FROM audit_findings');
      
      console.log('audit_findings table indexes:');
      indexes.forEach(index => {
        console.log(`- ${index.Key_name}: Column ${index.Column_name} (${index.Non_unique === 0 ? 'Unique' : 'Non-unique'})`);
      });
      
      // Check for triggers
      console.log('\nChecking triggers on audit_findings table...');
      const [triggers] = await connection.execute('SHOW TRIGGERS WHERE `Table` = ?', ['audit_findings']);
      
      if (triggers.length > 0) {
        console.log('audit_findings table triggers:');
        triggers.forEach(trigger => {
          console.log(`- ${trigger.Trigger}: ${trigger.Timing} ${trigger.Event}`);
          console.log(`  Statement: ${trigger.Statement}`);
        });
      } else {
        console.log('No triggers found on audit_findings table.');
      }
      
      // Check if we can update the Evidence column with a long URL
      console.log('\nTesting URL update on audit_findings table...');
      const testUrl = 'https://example.com/very-long-test-url-' + '0123456789'.repeat(20);
      
      try {
        // Create a temporary record for testing
        const [insertResult] = await connection.execute(
          'INSERT INTO audit_findings (ComplianceId, AuditId, Evidence, UserId, `Check`) VALUES (?, ?, ?, ?, ?)',
          [999999, 999999, 'Test URL', 1050, '1']
        );
        
        console.log(`Created test record with ID: ${insertResult.insertId}`);
        
        // Try to update with a long URL
        const [updateResult] = await connection.execute(
          'UPDATE audit_findings SET Evidence = ? WHERE ComplianceId = ? AND AuditId = ?',
          [testUrl, 999999, 999999]
        );
        
        console.log(`Update test result: ${updateResult.affectedRows} row(s) affected`);
        
        // Verify the update
        const [verifyRows] = await connection.execute(
          'SELECT Evidence FROM audit_findings WHERE ComplianceId = ? AND AuditId = ?',
          [999999, 999999]
        );
        
        if (verifyRows && verifyRows.length > 0) {
          const savedUrl = verifyRows[0].Evidence;
          console.log(`Test URL length: ${testUrl.length} characters`);
          console.log(`Saved URL length: ${savedUrl.length} characters`);
          
          if (savedUrl === testUrl) {
            console.log('SUCCESS: URL was saved correctly');
          } else {
            console.log('WARNING: URL was truncated or modified');
            console.log(`Expected: ${testUrl}`);
            console.log(`Actual: ${savedUrl}`);
          }
        }
        
        // Clean up the test record
        await connection.execute(
          'DELETE FROM audit_findings WHERE ComplianceId = ? AND AuditId = ?',
          [999999, 999999]
        );
        console.log('Test record deleted');
      } catch (testError) {
        console.error('Error during URL test:', testError.message);
      }
      
      // Suggest schema changes if needed
      console.log('\nRecommended schema changes:');
      let needsChanges = false;
      
      for (const column of columns) {
        if (column.Field === 'Evidence' && !column.Type.includes('text')) {
          console.log('ALTER TABLE audit_findings MODIFY COLUMN Evidence TEXT;');
          needsChanges = true;
        }
        if (column.Field === 'S3Location' && !column.Type.includes('text')) {
          console.log('ALTER TABLE audit_findings MODIFY COLUMN S3Location TEXT;');
          needsChanges = true;
        }
      }
      
      if (!needsChanges) {
        console.log('No schema changes needed.');
      }
      
      console.log('========== DATABASE SCHEMA CHECK COMPLETED ==========');
    } finally {
      // Release the connection
      connection.release();
    }
  } catch (error) {
    console.error('Error:', error);
  } finally {
    // Close the pool
    await pool.end();
  }
}

// Run the schema check
checkSchema().catch(console.error); 