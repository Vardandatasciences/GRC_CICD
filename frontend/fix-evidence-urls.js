/**
 * Fix Evidence URLs in audit_findings table
 * 
 * This script directly updates the database to ensure S3 URLs are properly stored
 * in the Evidence column of the audit_findings table.
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

// Initialize database pool
const pool = mysql.createPool(dbConfig);

async function fixEvidenceUrl(complianceId, auditId, s3Url) {
  const connection = await pool.getConnection();
  
  try {
    console.log(`Fixing evidence URL for ComplianceId=${complianceId}, AuditId=${auditId || 'N/A'}`);
    console.log(`URL to save: ${s3Url}`);
    
    // First check if the record exists
    let selectQuery, selectParams;
    
    if (auditId) {
      selectQuery = 'SELECT * FROM audit_findings WHERE ComplianceId = ? AND AuditId = ?';
      selectParams = [complianceId, auditId];
    } else {
      selectQuery = 'SELECT * FROM audit_findings WHERE ComplianceId = ?';
      selectParams = [complianceId];
    }
    
    const [rows] = await connection.execute(selectQuery, selectParams);
    
    if (rows && rows.length > 0) {
      console.log(`Found ${rows.length} matching record(s)`);
      
      // Update existing record(s)
      let updateQuery, updateParams;
      
      if (auditId) {
        updateQuery = 'UPDATE audit_findings SET Evidence = ?, S3Location = ? WHERE ComplianceId = ? AND AuditId = ?';
        updateParams = [s3Url, s3Url, complianceId, auditId];
      } else {
        updateQuery = 'UPDATE audit_findings SET Evidence = ?, S3Location = ? WHERE ComplianceId = ?';
        updateParams = [s3Url, s3Url, complianceId];
      }
      
      const [updateResult] = await connection.execute(updateQuery, updateParams);
      console.log(`Updated ${updateResult.affectedRows} record(s)`);
      
      // Verify the update
      const [verifyRows] = await connection.execute(selectQuery, selectParams);
      verifyRows.forEach((row, index) => {
        console.log(`Record ${index + 1}:`);
        console.log(`- Evidence: ${row.Evidence}`);
        console.log(`- S3Location: ${row.S3Location}`);
      });
      
      return updateResult.affectedRows > 0;
    } else {
      console.log('No matching records found, creating new record');
      
      // Insert new record
      const insertQuery = 'INSERT INTO audit_findings (ComplianceId, AuditId, Evidence, S3Location, UserId, `Check`) VALUES (?, ?, ?, ?, ?, ?)';
      const insertParams = [complianceId, auditId || null, s3Url, s3Url, 1050, '1'];
      
      const [insertResult] = await connection.execute(insertQuery, insertParams);
      console.log(`Inserted ${insertResult.affectedRows} record(s)`);
      
      return insertResult.affectedRows > 0;
    }
  } catch (error) {
    console.error('Database error:', error);
    return false;
  } finally {
    connection.release();
  }
}

async function main() {
  try {
    // Get parameters from command line
    const args = process.argv.slice(2);
    
    if (args.length < 2) {
      console.error('Usage: node fix-evidence-urls.js <complianceId> <s3Url> [auditId]');
      process.exit(1);
    }
    
    const complianceId = args[0];
    const s3Url = args[1];
    const auditId = args.length > 2 ? args[2] : null;
    
    console.log('========== STARTING EVIDENCE URL FIX ==========');
    const result = await fixEvidenceUrl(complianceId, auditId, s3Url);
    
    if (result) {
      console.log('========== EVIDENCE URL FIXED SUCCESSFULLY ==========');
    } else {
      console.error('========== EVIDENCE URL FIX FAILED ==========');
    }
  } catch (error) {
    console.error('Error:', error);
  } finally {
    // Close the connection pool
    await pool.end();
  }
}

// Run the script
main().catch(console.error); 