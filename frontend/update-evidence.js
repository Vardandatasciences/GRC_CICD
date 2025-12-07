/**
 * Direct Database Update for Evidence URL
 * 
 * This script directly updates the database with the specific S3 URL
 * for the evidence file that was uploaded.
 */

require("dotenv").config();
const mysql = require('mysql2/promise');

// The specific URL to save
const S3_URL = "https://grc-files-vardaan.s3.amazonaws.com/1749549561613_cakes.pdf_compliance_id-12_documentType-evidence_table_name-audit_findings_storage_column-Evidence_audit_id-33_document_type-pdf_file_type-pdf";
const COMPLIANCE_ID = 12;
const AUDIT_ID = 33;

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

async function updateDatabase() {
  // Create a connection pool
  const pool = mysql.createPool(dbConfig);
  
  try {
    console.log('========== STARTING DIRECT DATABASE UPDATE ==========');
    console.log(`ComplianceId: ${COMPLIANCE_ID}`);
    console.log(`AuditId: ${AUDIT_ID}`);
    console.log(`URL: ${S3_URL}`);
    
    // Get a connection from the pool
    const connection = await pool.getConnection();
    
    try {
      // First check if the record exists
      console.log('Checking if record exists...');
      const [rows] = await connection.execute(
        'SELECT * FROM audit_findings WHERE ComplianceId = ? AND AuditId = ?',
        [COMPLIANCE_ID, AUDIT_ID]
      );
      
      if (rows && rows.length > 0) {
        console.log(`Found ${rows.length} matching record(s)`);
        
        // Update the record with the S3 URL
        console.log('Updating record with direct SQL query...');
        
                 // Method 1: Using prepared statement
         const [result1] = await connection.execute(
           'UPDATE audit_findings SET Evidence = ? WHERE ComplianceId = ? AND AuditId = ?',
           [S3_URL, COMPLIANCE_ID, AUDIT_ID]
         );
         
         console.log(`Method 1 result: ${result1.affectedRows} row(s) affected`);
         
         // Method 2: Using direct SQL with single quotes
         const updateSql = `UPDATE audit_findings SET Evidence = '${S3_URL}' WHERE ComplianceId = ${COMPLIANCE_ID} AND AuditId = ${AUDIT_ID}`;
         const [result2] = await connection.query(updateSql);
         
         console.log(`Method 2 result: ${result2.affectedRows} row(s) affected`);
         
         // Method 3: Using direct SQL with double quotes
         const updateSql2 = `UPDATE audit_findings SET Evidence = "${S3_URL}" WHERE ComplianceId = ${COMPLIANCE_ID} AND AuditId = ${AUDIT_ID}`;
         const [result3] = await connection.query(updateSql2);
        
        console.log(`Method 3 result: ${result3.affectedRows} row(s) affected`);
        
        // Verify the update
        console.log('Verifying update...');
        const [verifyRows] = await connection.execute(
          'SELECT * FROM audit_findings WHERE ComplianceId = ? AND AuditId = ?',
          [COMPLIANCE_ID, AUDIT_ID]
        );
        
                 if (verifyRows && verifyRows.length > 0) {
           console.log('Updated record:');
           console.log(`- Evidence: ${verifyRows[0].Evidence}`);
           
           if (verifyRows[0].Evidence === S3_URL) {
             console.log('SUCCESS: Evidence column contains the full URL');
           } else {
             console.log('WARNING: Evidence column does not contain the full URL');
             console.log(`Expected: ${S3_URL}`);
             console.log(`Actual: ${verifyRows[0].Evidence}`);
           }
         }
      } else {
        console.log('No matching records found, creating new record');
        
        // Insert a new record
        const [insertResult] = await connection.execute(
          'INSERT INTO audit_findings (ComplianceId, AuditId, Evidence, UserId, `Check`) VALUES (?, ?, ?, ?, ?)',
          [COMPLIANCE_ID, AUDIT_ID, S3_URL, 1050, '1']
        );
        
        console.log(`Inserted ${insertResult.affectedRows} new record(s)`);
        
        // Verify the insert
        const [verifyRows] = await connection.execute(
          'SELECT * FROM audit_findings WHERE ComplianceId = ? AND AuditId = ?',
          [COMPLIANCE_ID, AUDIT_ID]
        );
        
        if (verifyRows && verifyRows.length > 0) {
          console.log('Inserted record:');
          console.log(`- Evidence: ${verifyRows[0].Evidence}`);
          console.log(`- S3Location: ${verifyRows[0].S3Location}`);
        }
      }
      
             // Try a raw SQL update as a last resort
       try {
         console.log('Attempting raw SQL update...');
         await connection.query(`
           UPDATE audit_findings 
           SET Evidence = '${S3_URL}'
           WHERE ComplianceId = ${COMPLIANCE_ID} 
           AND AuditId = ${AUDIT_ID}
         `);
         console.log('Raw SQL update completed');
       } catch (rawSqlError) {
         console.error('Raw SQL update failed:', rawSqlError.message);
       }
      
      console.log('========== DATABASE UPDATE COMPLETED ==========');
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

// Run the update
updateDatabase().catch(console.error); 