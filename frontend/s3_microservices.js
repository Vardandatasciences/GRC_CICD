require("dotenv").config();
const express = require('express');
const multer = require('multer');
const fs = require("fs");
const S3 = require("aws-sdk/clients/s3");
const mysql = require('mysql2/promise');
const bodyParser = require('body-parser');

// Configure AWS S3
const bucketName = process.env.AWS_BUCKET_NAME;
const region = process.env.AWS_REGION;
const accessKeyId = process.env.AWS_ACCESS_KEY_ID;
const secretAccessKey = process.env.AWS_SECRET_ACCESS_KEY;

const s3 = new S3({
  region,
  accessKeyId,
  secretAccessKey,
});

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

const pool = mysql.createPool(dbConfig);

// Test DB connection
async function testConnection() {
  try {
    const connection = await pool.getConnection();
    console.log('MySQL connected successfully');
    connection.release();
  } catch (error) {
    console.error('MySQL connection failed:', error);
  }
}

testConnection();

// Content type mapping
const CONTENT_TYPES = {
  // Images
  'jpg': 'image/jpeg',
  'jpeg': 'image/jpeg',
  'png': 'image/png',
  'gif': 'image/gif',
  'webp': 'image/webp',
  
  // Documents
  'pdf': 'application/pdf',
  'doc': 'application/msword',
  'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'xls': 'application/vnd.ms-excel',
  'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'ppt': 'application/vnd.ms-powerpoint',
  'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  
  // Videos
  'mp4': 'video/mp4',
  'mov': 'video/quicktime',
  'avi': 'video/x-msvideo',
  'webm': 'video/webm',
  
  // Audio
  'mp3': 'audio/mpeg',
  'wav': 'audio/wav',
  'ogg': 'audio/ogg',
  
  // Archives
  'zip': 'application/zip',
  'rar': 'application/x-rar-compressed',
  '7z': 'application/x-7z-compressed',
  
  // Text
  'txt': 'text/plain',
  'csv': 'text/csv',
  'json': 'application/json',
  
  // Other
  'xml': 'application/xml',
  'html': 'text/html',
  'css': 'text/css',
  'js': 'application/javascript'
};

// Check if file type should be downloadable
function isDownloadable(extension) {
  const downloadableTypes = [
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'zip', 'rar', '7z', 'txt', 'csv', 'json', 'xml'
  ];
  return downloadableTypes.includes(extension.toLowerCase());
}

// Express app setup
const app = express();
const PORT = process.env.AWS_PORT || 5000;

// Configure multer for file uploads
const storage = multer.memoryStorage();
const upload = multer({
  storage: storage,
  limits: {
    fileSize: 50 * 1024 * 1024, // 50MB limit
  }
});

// Middleware
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Helper function to generate file name with parameters
function generateFileName(baseFileName, params) {
  const timestamp = Date.now();
  let paramString = '';
  
  if (params && Object.keys(params).length > 0) {
    paramString = '_' + Object.entries(params)
      .map(([key, value]) => `${key}-${value}`)
      .join('_');
  }
  
  return `${timestamp}_${baseFileName}${paramString}`;
}

// Upload file
async function uploadFile(file, fileType, fileName, userId, params = {}) {
  const connection = await pool.getConnection();
  
  try {
    // Get content type based on file extension
    const extension = fileType.toLowerCase();
    const contentType = CONTENT_TYPES[extension] || 'application/octet-stream';

    // Generate unique file name with parameters
    const uniqueFileName = generateFileName(fileName, params);

    // Prepare upload parameters
    const uploadParams = {
      Bucket: bucketName,
      Body: file.buffer || fs.createReadStream(file.path),
      Key: uniqueFileName,
      ContentType: contentType,
      ...(isDownloadable(extension) && {
        ContentDisposition: `attachment; filename="${fileName}"`
      })
    };

    // Upload to S3
    const uploadResult = await s3.upload(uploadParams).promise();
    
    // Check if metadata column exists in the database
    try {
      // Try to insert with metadata first
      const metadataJson = JSON.stringify(params);
      const [result] = await connection.execute(
        'INSERT INTO s3_files (url, file_type, file_name, user_id, metadata) VALUES (?, ?, ?, ?, ?)',
        [uploadResult.Location, extension, fileName, userId, metadataJson]
      );
      
      // Get the inserted record
      const [rows] = await connection.execute(
        'SELECT * FROM s3_files WHERE id = ?',
        [result.insertId]
      );

      const insertedFile = rows[0];
      
      return {
        success: true,
        file: {
          id: insertedFile.id,
          url: insertedFile.url,
          fileType: insertedFile.file_type,
          fileName: insertedFile.file_name,
          uploadedAt: insertedFile.uploaded_at,
          metadata: params,
          s3Key: uniqueFileName
        }
      };
    } 
    catch (dbError) {
      // If metadata column doesn't exist, insert without it
      if (dbError.code === 'ER_BAD_FIELD_ERROR' && dbError.message.includes('metadata')) {
        console.log('Metadata column not found, inserting without metadata');
        
        // Insert without metadata
        const [result] = await connection.execute(
          'INSERT INTO s3_files (url, file_type, file_name, user_id) VALUES (?, ?, ?, ?)',
          [uploadResult.Location, extension, fileName, userId]
        );
        
        // Get the inserted record
        const [rows] = await connection.execute(
          'SELECT * FROM s3_files WHERE id = ?',
          [result.insertId]
        );
  
        const insertedFile = rows[0];
        
        return {
          success: true,
          file: {
            id: insertedFile.id,
            url: insertedFile.url,
            fileType: insertedFile.file_type,
            fileName: insertedFile.file_name,
            uploadedAt: insertedFile.uploaded_at,
            metadata: params,  // Still return the metadata in the response
            s3Key: uniqueFileName
          }
        };
      } else {
        // If it's a different error, rethrow it
        throw dbError;
      }
    }
  } catch (error) {
    console.error('Error uploading file:', error);
    throw new Error(`Failed to upload file: ${error.message}`);
  } finally {
    connection.release();
  }
}

// Delete file
async function deleteFile(fileId) {
  const connection = await pool.getConnection();
  
  try {
    // Get file metadata from MySQL
    const [rows] = await connection.execute(
      'SELECT * FROM s3_files WHERE id = ?',
      [fileId]
    );

    if (rows.length === 0) {
      throw new Error('File not found');
    }

    const file = rows[0];

    // Extract S3 key from URL
    const s3Key = file.url.split('/').pop();

    // Delete from S3
    const deleteParams = {
      Bucket: bucketName,
      Key: s3Key
    };
    await s3.deleteObject(deleteParams).promise();

    // Delete from MySQL
    await connection.execute(
      'DELETE FROM s3_files WHERE id = ?',
      [fileId]
    );

    return {
      success: true,
      message: 'File deleted successfully'
    };
  } catch (error) {
    console.error('Error deleting file:', error);
    throw new Error(`Failed to delete file: ${error.message}`);
  } finally {
    connection.release();
  }
}

// Get file metadata
async function getFileMetadata(fileId) {
  const connection = await pool.getConnection();
  
  try {
    const [rows] = await connection.execute(
      'SELECT * FROM s3_files WHERE id = ?',
      [fileId]
    );

    if (rows.length === 0) {
      throw new Error('File not found');
    }

    const file = rows[0];
    const metadata = file.metadata ? JSON.parse(file.metadata) : {};

    return {
      success: true,
      file: {
        id: file.id,
        url: file.url,
        fileType: file.file_type,
        fileName: file.file_name,
        uploadedAt: file.uploaded_at,
        metadata: metadata
      }
    };
  } catch (error) {
    console.error('Error getting file metadata:', error);
    throw new Error(`Failed to get file metadata: ${error.message}`);
  } finally {
    connection.release();
  }
}

// Get user files
async function getUserFiles(userId, filters = {}) {
  const connection = await pool.getConnection();
  
  try {
    // Check if the metadata column exists by querying the table structure
    const [columns] = await connection.execute(
      "SHOW COLUMNS FROM s3_files LIKE 'metadata'"
    );
    
    const hasMetadataColumn = columns.length > 0;
    
    let query = 'SELECT * FROM s3_files WHERE user_id = ?';
    const queryParams = [userId];
    
    // Add filter by metadata only if the column exists
    if (hasMetadataColumn && filters && Object.keys(filters).length > 0) {
      query += ' AND metadata LIKE ?';
      queryParams.push(`%${JSON.stringify(filters).slice(1, -1)}%`);
    }
    
    query += ' ORDER BY uploaded_at DESC';
    
    const [rows] = await connection.execute(query, queryParams);

    return {
      success: true,
      files: rows.map(file => ({
        id: file.id,
        url: file.url,
        fileType: file.file_type,
        fileName: file.file_name,
        uploadedAt: file.uploaded_at,
        metadata: hasMetadataColumn && file.metadata ? JSON.parse(file.metadata) : {}
      }))
    };
  } catch (error) {
    console.error('Error getting user files:', error);
    throw new Error(`Failed to get user files: ${error.message}`);
  } finally {
    connection.release();
  }
}

// Generate download URL - fix the URL encoding issue
async function getDownloadUrl(fileId, expiresIn = 3600) {
  const connection = await pool.getConnection();
  
  try {
    const [rows] = await connection.execute(
      'SELECT * FROM s3_files WHERE id = ?',
      [fileId]
    );

    if (rows.length === 0) {
      throw new Error('File not found');
    }

    const file = rows[0];
    
    // Extract S3 key from URL and fully decode it to avoid double-encoding
    const urlParts = file.url.split('/');
    const encodedKey = urlParts[urlParts.length - 1];
    
    // Make sure to properly decode the key
    let s3Key;
    try {
      // First try to decode it in case it's encoded
      s3Key = decodeURIComponent(encodedKey);
    } catch (e) {
      // If decoding fails, use the original key
      s3Key = encodedKey;
      console.log('Key could not be decoded, using as is');
    }
    
    console.log('Original S3 key from URL:', encodedKey);
    console.log('Decoded S3 key for download:', s3Key);

    // Generate pre-signed URL
    const params = {
      Bucket: bucketName,
      Key: s3Key,
      Expires: expiresIn,
      ResponseContentDisposition: `attachment; filename="${file.file_name}"`
    };

    const downloadUrl = s3.getSignedUrl('getObject', params);
    console.log('Generated download URL:', downloadUrl);

    return {
      success: true,
      downloadUrl: downloadUrl,
      fileName: file.file_name,
      s3Key: s3Key
    };
  } catch (error) {
    console.error('Error generating download URL:', error);
    throw new Error(`Failed to generate download URL: ${error.message}`);
  } finally {
    connection.release();
  }
}

// API Routes
app.get('http://15.207.108.158:8000/api/health', (req, res) => {
  // Check S3 connection
  let s3Status = "unknown";
  let dbStatus = "unknown";
  
  // Check database connection
  pool.getConnection()
    .then(connection => {
      dbStatus = "connected";
      connection.release();
      
      // Now check S3 connection
      const params = {
        Bucket: bucketName,
        MaxKeys: 1
      };
      
      s3.listObjects(params, function(err, data) {
        if (err) {
          s3Status = `error: ${err.code}`;
          res.status(200).json({ 
            status: 'warning', 
            message: 'S3 microservice is running with issues',
            s3: s3Status,
            database: dbStatus,
            timestamp: new Date().toISOString()
          });
        } else {
          s3Status = "connected";
          res.status(200).json({ 
            status: 'ok', 
            message: 'S3 microservice is running properly',
            s3: s3Status,
            database: dbStatus,
            timestamp: new Date().toISOString()
          });
        }
      });
    })
    .catch(err => {
      dbStatus = `error: ${err.code || err.message}`;
      res.status(200).json({ 
        status: 'warning', 
        message: 'S3 microservice is running with issues',
        s3: s3Status,
        database: dbStatus,
        timestamp: new Date().toISOString()
      });
    });
});

app.post('http://15.207.108.158:8000/api/upload', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    const { originalname, mimetype } = req.file;
    const userId = req.body.userId || 'default-user';
    const fileExtension = originalname.split('.').pop().toLowerCase();
    const fileName = req.body.fileName || originalname;
    
    // Extract all parameters from the request body
    const params = {};
    for (const key in req.body) {
      if (key !== 'userId' && key !== 'fileName') {
        params[key] = req.body[key];
      }
    }

    const result = await uploadFile(req.file, fileExtension, fileName, userId, params);
    res.json(result);
  } catch (error) {
    console.error('Upload error:', error);
    res.status(500).json({ error: error.message });
  }
});

app.get('http://15.207.108.158:8000/api/files/:userId', async (req, res) => {
  try {
    const { userId } = req.params;
    // Get filters from query parameters
    const filters = req.query;
    const result = await getUserFiles(userId, filters);
    res.json(result);
  } catch (error) {
    console.error('Get files error:', error);
    res.status(500).json({ error: error.message });
  }
});

app.get('http://15.207.108.158:8000/api/file/:fileId', async (req, res) => {
  try {
    const { fileId } = req.params;
    const result = await getFileMetadata(fileId);
    res.json(result);
  } catch (error) {
    console.error('Get file metadata error:', error);
    res.status(500).json({ error: error.message });
  }
});

app.get('http://15.207.108.158:8000/api/download/:fileId', async (req, res) => {
  try {
    const { fileId } = req.params;
    const expiresIn = req.query.expiresIn ? parseInt(req.query.expiresIn) : 3600;
    const result = await getDownloadUrl(fileId, expiresIn);
    
    if (req.query.redirect === 'true') {
      res.redirect(result.downloadUrl);
    } else {
      res.json(result);
    }
  } catch (error) {
    console.error('Download error:', error);
    res.status(500).json({ error: error.message });
  }
});

app.delete('http://15.207.108.158:8000/api/file/:fileId', async (req, res) => {
  try {
    const { fileId } = req.params;
    const result = await deleteFile(fileId);
    res.json(result);
  } catch (error) {
    console.error('Delete error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Error handler
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ 
    error: 'Internal Server Error',
    message: err.message 
  });
});

app.listen(PORT, () => {
  console.log(`S3 Microservice running on port ${PORT}`);
});

module.exports = {
  uploadFile,
  deleteFile,
  getFileMetadata,
  getUserFiles,
  getDownloadUrl
};