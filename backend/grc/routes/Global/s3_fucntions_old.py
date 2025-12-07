#!/usr/bin/env python3
"""
S3 Microservice Client for Direct Deployment with Local MySQL Database
Direct URL: http://13.233.147.73:3000
Local MySQL Database for operation tracking
No AWS credentials required - handled by the microservice
"""

import requests
import os
import json
import mimetypes
from typing import Dict, List, Optional, Union, Any
import datetime
import mysql.connector
from mysql.connector import pooling

def convert_safe_string(value):
    """Convert Django SafeString objects to regular strings for MySQL compatibility"""
    if value is None:
        return None
    
    # Import Django's SafeString to check instance
    try:
        from django.utils.safestring import SafeString
        if isinstance(value, SafeString):
            return str(value)
    except ImportError:
        pass
    
    # Handle HTML escaped strings
    if hasattr(value, '__html__'):
        return str(value)
    
    # Handle Django SafeString specifically
    if hasattr(value, 'mark_safe'):
        return str(value)
    
    # Handle other types that might cause issues
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    
    # Convert any object to string, ensuring it's a regular Python string
    return str(value)

class RenderS3Client:
    """
    Python client for S3 microservice deployed on Direct
    With local MySQL database for operation tracking
    AWS credentials are handled by the microservice itself
    """
    
    def __init__(self, 
                 api_base_url: str = "http://13.233.147.73:3000",
                 mysql_config: Optional[Dict] = None):
        """
        Initialize the Direct S3 client with local MySQL
        
        Args:
            api_base_url: Your Direct deployment URL
            mysql_config: MySQL database configuration (optional)
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.db_pool = None
        
        # Initialize MySQL connection if config provided
        if mysql_config:
            self._setup_mysql_database(mysql_config)
        else:
            self._setup_default_mysql()
    
    def _setup_default_mysql(self):
        """Setup MySQL with default/environment configuration"""
        try:
            mysql_config = {
                'host': os.environ.get('DB_HOST', 'localhost'),
                'user': os.environ.get('DB_USER', 'root'),
                'password': os.environ.get('DB_PASSWORD', 'root'),
                'database': os.environ.get('DB_NAME', 'grc'),
                'port': int(os.environ.get('DB_PORT', 3306)),
                'autocommit': True,
                'charset': 'utf8mb4',
                'collation': 'utf8mb4_unicode_ci'
            }
            
            self._setup_mysql_database(mysql_config)
            
        except Exception as e:
            print(f"MySQL setup with defaults failed: {str(e)}")
            self.db_pool = None
    
    def _setup_mysql_database(self, mysql_config: Dict):
        """Setup MySQL connection pool"""
        try:
            # Test connection first
            test_conn = mysql.connector.connect(**mysql_config)
            test_conn.close()
            
            # Create connection pool
            self.db_pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="render_s3_pool",
                pool_size=5,
                pool_reset_session=True,
                **mysql_config
            )
            
            print("✅ MySQL connection pool initialized successfully")
            
            # Create table if it doesn't exist
            self._create_table_if_not_exists()
            
        except mysql.connector.Error as e:
            print(f"❌ MySQL connection failed: {str(e)}")
            print("💡 Make sure MySQL is running and credentials are correct")
            self.db_pool = None
        except Exception as e:
            print(f"❌ Database setup error: {str(e)}")
            self.db_pool = None
    
    def _create_table_if_not_exists(self):
        """Create the file_operations table if it doesn't exist"""
        if not self.db_pool:
            return
        
        conn = self._get_db_connection()
        if not conn:
            return
        
        cursor = conn.cursor()
        
        try:
            # Create unified file_operations table
            create_table_query = """
            CREATE TABLE IF NOT EXISTS file_operations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                operation_type ENUM('upload', 'download', 'export') NOT NULL,
                user_id VARCHAR(255) NOT NULL,
                file_name VARCHAR(500) NOT NULL,
                original_name VARCHAR(500),
                stored_name VARCHAR(500),
                s3_url TEXT,
                s3_key VARCHAR(1000),
                s3_bucket VARCHAR(255),
                file_type VARCHAR(50),
                file_size BIGINT,
                content_type VARCHAR(255),
                export_format VARCHAR(20),
                record_count INT,
                status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
                error TEXT,
                metadata JSON,
                platform VARCHAR(50) DEFAULT 'Render',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                completed_at TIMESTAMP NULL,
                
                INDEX idx_user_id (user_id),
                INDEX idx_operation_type (operation_type),
                INDEX idx_status (status),
                INDEX idx_created_at (created_at),
                INDEX idx_file_type (file_type),
                INDEX idx_platform (platform),
                INDEX idx_s3_key (s3_key(255))
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            cursor.execute(create_table_query)
            conn.commit()
            print("✅ Database table verified/created successfully")
            
        except mysql.connector.Error as e:
            print(f"❌ Table creation error: {str(e)}")
        except Exception as e:
            print(f"❌ Unexpected error creating table: {str(e)}")
        finally:
            cursor.close()
            conn.close()
    

    
    def _get_db_connection(self):
        """Get database connection from pool"""
        if not self.db_pool:
            return None
        
        try:
            return self.db_pool.get_connection()
        except Exception as e:
            print(f"❌ Failed to get DB connection: {str(e)}")
            return None
    
    def _save_operation_record(self, operation_type: str, operation_data: Dict) -> Optional[int]:
        """Save operation record to MySQL database"""
        if not self.db_pool:
            return None
        
        conn = self._get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        
        try:
            query = """
            INSERT INTO file_operations 
            (operation_type, user_id, file_name, original_name, stored_name, s3_url, s3_key, s3_bucket,
             file_type, file_size, content_type, export_format, record_count, status, metadata, platform,
             created_at, updated_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            now = datetime.datetime.now()
            
            params = (
                operation_type,
                convert_safe_string(operation_data.get('user_id')),
                convert_safe_string(operation_data.get('file_name')),
                convert_safe_string(operation_data.get('original_name')),
                convert_safe_string(operation_data.get('stored_name')),
                convert_safe_string(operation_data.get('s3_url', '')),
                convert_safe_string(operation_data.get('s3_key', '')),
                convert_safe_string(operation_data.get('s3_bucket', '')),
                convert_safe_string(operation_data.get('file_type')),
                operation_data.get('file_size'),
                convert_safe_string(operation_data.get('content_type')),
                convert_safe_string(operation_data.get('export_format')),
                operation_data.get('record_count'),
                convert_safe_string(operation_data.get('status', 'pending')),
                json.dumps(operation_data.get('metadata', {})),
                'Direct',
                now,
                now
            )
            
            cursor.execute(query, params)
            conn.commit()
            operation_id = cursor.lastrowid
            
            print(f"📝 Operation recorded in MySQL: ID {operation_id}")
            return operation_id
            
        except mysql.connector.Error as e:
            print(f"❌ MySQL save error: {str(e)}")
            return None
        except Exception as e:
            print(f"❌ Database save error: {str(e)}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def _update_operation_record(self, operation_id: int, operation_data: Dict):
        """Update operation record with complete information"""
        if not self.db_pool or not operation_id:
            return
        
        conn = self._get_db_connection()
        if not conn:
            return
        
        cursor = conn.cursor()
        
        try:
            # Build dynamic update query
            update_fields = []
            update_values = []
            
            field_mapping = {
                'stored_name': 'stored_name',
                's3_url': 's3_url', 
                's3_key': 's3_key',
                's3_bucket': 's3_bucket',
                'file_type': 'file_type',
                'file_size': 'file_size',
                'content_type': 'content_type',
                'export_format': 'export_format',
                'record_count': 'record_count',
                'status': 'status',
                'error': 'error'
            }
            
            for key, db_field in field_mapping.items():
                if key in operation_data:
                    update_fields.append(f"{db_field} = %s")
                    # Convert SafeString objects to regular strings for MySQL compatibility
                    value = operation_data[key]
                    if key in ['stored_name', 's3_url', 's3_key', 's3_bucket', 'file_type', 'content_type', 'export_format', 'status', 'error']:
                        value = convert_safe_string(value)
                    update_values.append(value)
            
            # Always update metadata and timestamp
            if 'metadata' in operation_data:
                update_fields.append("metadata = %s")
                update_values.append(json.dumps(operation_data['metadata']))
            
            update_fields.append("updated_at = %s")
            update_values.append(datetime.datetime.now())
            
            # Add completed_at if status is completed
            if operation_data.get('status') == 'completed':
                update_fields.append("completed_at = %s")
                update_values.append(datetime.datetime.now())
            
            # Add operation_id at the end
            update_values.append(operation_id)
            
            query = f"UPDATE file_operations SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(query, update_values)
            conn.commit()
            
            print(f"📝 Operation {operation_id} updated in MySQL")
            
        except mysql.connector.Error as e:
            print(f"❌ MySQL update error: {str(e)}")
        except Exception as e:
            print(f"❌ Database update error: {str(e)}")
        finally:
            cursor.close()
            conn.close()
    
    def get_operation_history(self, user_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get recent operation history from MySQL"""
        if not self.db_pool:
            return []
        
        conn = self._get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            if user_id:
                query = """
                SELECT * FROM file_operations 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
                """
                cursor.execute(query, (user_id, limit))
            else:
                query = """
                SELECT * FROM file_operations 
                ORDER BY created_at DESC 
                LIMIT %s
                """
                cursor.execute(query, (limit,))
            
            results = cursor.fetchall()
            
            # Convert datetime objects to strings for JSON serialization
            for result in results:
                for key, value in result.items():
                    if isinstance(value, datetime.datetime):
                        result[key] = value.isoformat()
            
            return results
            
        except mysql.connector.Error as e:
            print(f"❌ MySQL query error: {str(e)}")
            return []
        except Exception as e:
            print(f"❌ Database query error: {str(e)}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def get_operation_stats(self) -> Dict:
        """Get operation statistics from MySQL"""
        if not self.db_pool:
            return {}
        
        conn = self._get_db_connection()
        if not conn:
            return {}
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Get overall stats
            cursor.execute("""
                SELECT 
                    operation_type,
                    COUNT(*) as total_count,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
                    AVG(file_size) as avg_file_size,
                    SUM(file_size) as total_file_size
                FROM file_operations 
                GROUP BY operation_type
            """)
            
            stats = {
                'operations_by_type': cursor.fetchall(),
                'total_operations': 0,
                'total_completed': 0,
                'total_failed': 0
            }
            
            # Calculate totals
            for op_stat in stats['operations_by_type']:
                stats['total_operations'] += op_stat['total_count']
                stats['total_completed'] += op_stat['completed_count']
                stats['total_failed'] += op_stat['failed_count']
            
            # Get recent activity
            cursor.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as operations
                FROM file_operations 
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """)
            
            stats['recent_activity'] = cursor.fetchall()
            
            return stats
            
        except mysql.connector.Error as e:
            print(f"❌ MySQL stats query error: {str(e)}")
            return {}
        except Exception as e:
            print(f"❌ Database stats error: {str(e)}")
            return {}
        finally:
            cursor.close()
            conn.close()
    
    def test_connection(self) -> Dict:
        """Test connection to Render microservice and MySQL database"""
        result = {
            'render_status': 'unknown',
            'mysql_status': 'unknown',
            'overall_success': False
        }
        
        # Test Direct microservice
        try:
            print("🧪 Testing Direct microservice connection...")
            response = requests.get(f"{self.api_base_url}/health", timeout=30)
            response.raise_for_status()
            
            health_info = response.json()
            result['direct_status'] = 'connected'
            result['direct_info'] = health_info
            print("✅ Direct microservice: Connected")
            
        except requests.exceptions.Timeout:
            result['direct_status'] = 'timeout'
            result['direct_error'] = 'Connection timed out (Direct service may be unavailable)'
            print("⏳ Direct microservice: Timeout (may be unavailable)")
        except Exception as e:
            result['direct_status'] = 'failed'
            result['direct_error'] = str(e)
            print(f"❌ Direct microservice: Failed - {str(e)}")
        
        # Test MySQL database
        try:
            print("🧪 Testing MySQL database connection...")
            if self.db_pool:
                conn = self._get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                    cursor.close()
                    conn.close()
                    
                    result['mysql_status'] = 'connected'
                    print("✅ MySQL database: Connected")
                else:
                    result['mysql_status'] = 'failed'
                    result['mysql_error'] = 'Failed to get connection from pool'
                    print("❌ MySQL database: Connection pool failed")
            else:
                result['mysql_status'] = 'not_configured'
                result['mysql_error'] = 'Database pool not initialized'
                print("⚠️  MySQL database: Not configured")
                
        except mysql.connector.Error as e:
            result['mysql_status'] = 'failed'
            result['mysql_error'] = str(e)
            print(f"❌ MySQL database: Failed - {str(e)}")
        except Exception as e:
            result['mysql_status'] = 'failed'
            result['mysql_error'] = str(e)
            print(f"❌ MySQL database: Error - {str(e)}")
        
        # Overall success
        result['overall_success'] = (
            result['direct_status'] == 'connected' and 
            result['mysql_status'] in ['connected', 'not_configured']
        )
        
        return result
    
    def upload(self, file_path: str, user_id: str = "default-user", 
               custom_file_name: Optional[str] = None) -> Dict:
        """Upload a file to S3 via Render microservice with MySQL tracking"""
        operation_id = None
        
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            file_name = custom_file_name or os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            print(f"📤 Uploading {file_name} ({file_size} bytes) via Direct...")
            
            # Save initial operation record
            operation_data = {
                'user_id': user_id,
                'file_name': file_name,
                'original_name': os.path.basename(file_path),
                'file_type': os.path.splitext(file_name)[1][1:].lower() if '.' in file_name else '',
                'file_size': file_size,
                'content_type': mimetypes.guess_type(file_path)[0],
                'status': 'pending',
                'metadata': {
                    'original_path': file_path,
                    'platform': 'Direct',
                    'direct_url': self.api_base_url
                }
            }
            operation_id = self._save_operation_record('upload', operation_data)
            
            # Upload to Direct service
            url = f"{self.api_base_url}/api/upload/{user_id}/{file_name}"
            
            print(f"📍 Upload URL: {url}")
            
            with open(file_path, 'rb') as file:
                files = {'file': (file_name, file, mimetypes.guess_type(file_path)[0])}
                
                print(f"📁 File details: name={file_name}, size={file_size}, type={mimetypes.guess_type(file_path)[0]}")
                
                try:
                    response = requests.post(url, files=files, timeout=300)
                    print(f"📊 Response status: {response.status_code}")
                    print(f"📝 Response headers: {dict(response.headers)}")
                    
                    if response.status_code != 200:
                        print(f"❌ Response content: {response.text}")
                        
                    response.raise_for_status()
                    result = response.json()
                    print(f"✅ Upload response: {result}")
                    
                except requests.exceptions.RequestException as e:
                    print(f"❌ Request failed: {str(e)}")
                    if hasattr(e.response, 'text'):
                        print(f"❌ Error response: {e.response.text}")
                    raise
            
            if result.get('success'):
                file_info = result['file']
                
                # Update MySQL with success
                if operation_id:
                    update_data = {
                        'stored_name': file_info['storedName'],
                        's3_url': file_info['url'],
                        's3_key': file_info['s3Key'],
                        's3_bucket': file_info.get('bucket', ''),
                        'status': 'completed',
                        'metadata': {
                            'original_path': file_path,
                            'platform': 'Direct',
                            'direct_url': self.api_base_url,
                            'upload_response': file_info
                        }
                    }
                    self._update_operation_record(operation_id, update_data)
                
                print(f"✅ Upload successful! File: {file_info['storedName']}")
                
                return {
                    'success': True,
                    'operation_id': operation_id,
                    'file_info': file_info,
                    'platform': 'Direct',
                    'database': 'MySQL',
                    'message': 'File uploaded successfully to Direct/S3'
                }
            else:
                # Update MySQL with failure
                if operation_id:
                    self._update_operation_record(operation_id, {
                        'status': 'failed', 
                        'error': result.get('error')
                    })
                
                return result
                
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Upload failed: {error_msg}")
            
            if operation_id:
                self._update_operation_record(operation_id, {
                    'status': 'failed',
                    'error': error_msg
                })
            
            return {
                'success': False,
                'operation_id': operation_id,
                'error': error_msg
            }
    
    def download(self, s3_key: str, file_name: str, 
                 destination_path: str = "./downloads", 
                 user_id: str = "default-user") -> Dict:
        """Download a file from S3 via Direct with MySQL tracking"""
        operation_id = None
        
        try:
            print(f"⬇️  Downloading {file_name} via Direct...")
            
            # Save initial operation record
            operation_data = {
                'user_id': user_id,
                'file_name': file_name,
                'original_name': file_name,
                's3_key': s3_key,
                'status': 'pending',
                'metadata': {
                    'destination_path': destination_path,
                    'platform': 'Direct',
                    'direct_url': self.api_base_url
                }
            }
            operation_id = self._save_operation_record('download', operation_data)
            
            # Get download URL from Direct service
            url = f"{self.api_base_url}/api/download/{s3_key}/{file_name}"
            
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            download_info = response.json()
            
            if not download_info.get('success'):
                raise Exception(f"Failed to get download URL: {download_info.get('error')}")
            
            # Download file
            download_url = download_info['downloadUrl']
            file_response = requests.get(download_url, timeout=300)
            file_response.raise_for_status()
            
            # Save locally
            os.makedirs(destination_path, exist_ok=True)
            local_file_path = os.path.join(destination_path, file_name) if os.path.isdir(destination_path) else destination_path
            
            with open(local_file_path, 'wb') as f:
                f.write(file_response.content)
            
            # Update MySQL with success
            if operation_id:
                self._update_operation_record(operation_id, {
                    'status': 'completed',
                    'file_size': len(file_response.content),
                                            'metadata': {
                            'destination_path': destination_path,
                            'local_file_path': local_file_path,
                            'platform': 'Direct',
                            'direct_url': self.api_base_url,
                            'download_info': download_info
                        }
                })
            
            print(f"✅ Download successful! Saved to: {local_file_path}")
            
            return {
                'success': True,
                'operation_id': operation_id,
                'file_path': local_file_path,
                'file_size': len(file_response.content),
                'platform': 'Direct',
                'database': 'MySQL',
                'message': 'File downloaded successfully from Direct/S3'
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Download failed: {error_msg}")
            
            if operation_id:
                self._update_operation_record(operation_id, {
                    'status': 'failed',
                    'error': error_msg
                })
            
            return {
                'success': False,
                'operation_id': operation_id,
                'error': error_msg
            }
    
    def export(self, data: Union[List[Dict], Dict], export_format: str, 
               file_name: str, user_id: str = "default-user") -> Dict:
        """Export data via Direct microservice with MySQL tracking"""
        operation_id = None
        
        try:
            # Validate format - only formats actually supported by the microservice
            microservice_supported_formats = ['json', 'csv', 'xml', 'txt']
            all_supported_formats = ['json', 'csv', 'xml', 'txt', 'pdf', 'xlsx']
            
            if export_format.lower() not in all_supported_formats:
                raise ValueError(f"Unsupported format: {export_format}. Supported: {all_supported_formats}")
            
            # Check if format is supported by microservice
            if export_format.lower() not in microservice_supported_formats:
                raise ValueError(f"Format {export_format} is not supported by the S3 microservice. Use local export instead.")
            
            record_count = len(data) if isinstance(data, list) else 1
            print(f"📊 Exporting {record_count} records as {export_format.upper()} via Direct...")
            
            # Save initial operation record
            operation_data = {
                'user_id': user_id,
                'file_name': file_name,
                'original_name': file_name,
                'export_format': export_format,
                'record_count': record_count,
                'status': 'pending',
                'metadata': {
                    'export_format': export_format,
                    'data_size': len(str(data)),
                    'platform': 'Direct',
                    'direct_url': self.api_base_url
                }
            }
            operation_id = self._save_operation_record('export', operation_data)
            
            # Export via Direct
            url = f"{self.api_base_url}/api/export/{export_format}/{user_id}/{file_name}"
            
            # Format data based on export type (similar to test file)
            if export_format.lower() in ['csv', 'xlsx']:
                # For CSV/XLSX exports, send just the records array
                payload = {'data': data if isinstance(data, list) else [data]}
            else:
                # For other formats, send the full data structure
                payload = {'data': data}
            
            # Include AWS credentials in payload (required by the microservice)
            aws_credentials = {
                'awsAccessKey': 'AKIAW76SP14WHQGXV47T',
                'awsSecretKey': 'wJLUGFOQtXYOqzhyvmM2ljZPVbW+LTLJo2ft3A',
                'awsRegion': 'ap-south-1',
                'bucketName': 'vardaanwebsites'
            }
            payload.update(aws_credentials)
            
            print(f"🔗 Export URL: {url}")
            print(f"📦 Payload size: {len(str(payload))} characters")
            print(f"🔑 Using AWS credentials: {aws_credentials['awsAccessKey'][:10]}...")
            
            response = requests.post(url, json=payload, timeout=300)
            print(f"📊 Response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Response content: {response.text}")
                response.raise_for_status()
            
            result = response.json()
            
            if result.get('success'):
                export_info = result.get('export') or result.get('file') or result
                
                # Update MySQL with success
                if operation_id:
                    update_data = {
                        'stored_name': export_info.get('storedName') or export_info.get('fileName') or file_name,
                        's3_url': export_info.get('url') or export_info.get('fileUrl') or export_info.get('downloadUrl'),
                        's3_key': export_info.get('s3Key') or export_info.get('key') or export_info.get('fileKey'),
                        's3_bucket': export_info.get('bucket') or export_info.get('bucketName'),
                        'file_size': export_info.get('size') or export_info.get('fileSize'),
                        'content_type': export_info.get('contentType') or export_info.get('mimeType'),
                        'status': 'completed',
                        'metadata': {
                            'export_format': export_format,
                            'data_size': len(str(data)),
                            'platform': 'Direct',
                            'direct_url': self.api_base_url,
                            'export_response': export_info
                        }
                    }
                    self._update_operation_record(operation_id, update_data)
                
                print(f"✅ Export successful! File: {export_info['storedName']}")
                
                return {
                    'success': True,
                    'operation_id': operation_id,
                    'export_info': export_info,
                    'platform': 'Direct',
                    'database': 'MySQL',
                    'message': f'Data exported successfully as {export_format.upper()} via Direct'
                }
            else:
                # Update MySQL with failure
                error_msg = result.get('error') or result.get('message') or 'Unknown error'
                if operation_id:
                    self._update_operation_record(operation_id, {
                        'status': 'failed',
                        'error': error_msg
                    })
                
                return {
                    'success': False,
                    'operation_id': operation_id,
                    'error': error_msg,
                    'response': result
                }
                
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Export failed: {error_msg}")
            print(f"📝 Full error details: {type(e).__name__}: {error_msg}")
            
            if operation_id:
                self._update_operation_record(operation_id, {
                    'status': 'failed',
                    'error': error_msg
                })
            
            return {
                'success': False,
                'operation_id': operation_id,
                'error': error_msg,
                'error_type': type(e).__name__
            }

def create_direct_mysql_client(mysql_config: Optional[Dict] = None) -> RenderS3Client:
    """Create RenderS3Client with your Direct URL and local MySQL - Enhanced with error handling"""
    try:
        if not mysql_config:
            # Use environment variables or defaults
            mysql_config = {
                'host': os.environ.get('DB_HOST', 'localhost'),
                'user': os.environ.get('DB_USER', 'root'),
                'password': os.environ.get('DB_PASSWORD', 'root'),
                'database': os.environ.get('DB_NAME', 'grc'),
                'port': int(os.environ.get('DB_PORT', 3306))
            }
        
        print(f"🔧 Creating S3 client with MySQL config: {mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}")
        client = RenderS3Client("http://13.233.147.73:3000", mysql_config)
        print("✅ S3 client created successfully")
        return client
        
    except ImportError as import_e:
            print(f"❌ Import error creating S3 client: {import_e}")
            print("💡 Trying to create client without MySQL...")
            try:
                client = RenderS3Client("http://13.233.147.73:3000", None)
                print("⚠️  S3 client created without MySQL (fallback mode)")
                return client
            except Exception as fallback_e:
                print(f"❌ Fallback S3 client creation failed: {fallback_e}")
                raise Exception(f"S3 client creation failed: {import_e}, Fallback failed: {fallback_e}")
        
    except mysql.connector.Error as mysql_e:
        print(f"❌ MySQL connection error: {mysql_e}")
        print("💡 Creating S3 client without MySQL...")
        try:
            client = RenderS3Client("http://13.233.147.73:3000", None)
            print("⚠️  S3 client created without MySQL (fallback mode)")
            return client
        except Exception as fallback_e:
            print(f"❌ Fallback S3 client creation failed: {fallback_e}")
            raise Exception(f"MySQL error: {mysql_e}, Fallback failed: {fallback_e}")
    
    except Exception as e:
        print(f"❌ General error creating S3 client: {e}")
        print("💡 Trying to create client without MySQL...")
        try:
            client = RenderS3Client("http://13.233.147.73:3000", None)
            print("⚠️  S3 client created without MySQL (fallback mode)")
            return client
        except Exception as fallback_e:
            print(f"❌ Fallback S3 client creation failed: {fallback_e}")
            raise Exception(f"S3 client creation failed: {e}, Fallback failed: {fallback_e}")

def quick_test():
    """Quick test function"""
    print("🚀 Quick Test: Direct S3 Client with Local MySQL")
    print("=" * 60)
    
    # Create client
    client = create_direct_mysql_client()
    
    # Test connections
    result = client.test_connection()
    
    if result['overall_success']:
        print("✅ All systems operational!")
        
        # Show operation stats
        stats = client.get_operation_stats()
        if stats:
            print(f"\n📊 Database Stats:")
            print(f"   Total operations: {stats.get('total_operations', 0)}")
            print(f"   Completed: {stats.get('total_completed', 0)}")
            print(f"   Failed: {stats.get('total_failed', 0)}")
    else:
        print("❌ Some systems need attention")
        if result['direct_status'] != 'connected':
            print(f"   Direct: {result.get('direct_error', 'Unknown error')}")
        if result['mysql_status'] != 'connected':
            print(f"   MySQL: {result.get('mysql_error', 'Unknown error')}")

# Example usage
def main():
    """Example usage of Direct S3 Client with Local MySQL"""
    
    print("🚀 Direct S3 Microservice Client with Local MySQL")
    print("🌐 Direct URL: http://13.233.147.73:3000")
    print("🗄️  Database: Local MySQL")
    print("🔐 AWS Credentials: Handled by microservice")
    print("=" * 60)
    
    # Configure MySQL (adjust these settings for your local MySQL)
    mysql_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'root',  # Change this
        'database': 'grc',
        'port': 3306
    }
    
    # Create client
    client = RenderS3Client("http://13.233.147.73:3000", mysql_config)
    
    # Test connections
    print("1. Testing connections...")
    result = client.test_connection()
    
    if not result['overall_success']:
        print("❌ Cannot proceed - fix connection issues first")
        return
    
    # Example operations
    sample_data = [
        {"id": 1, "name": "MySQL Test", "platform": "Render", "status": "active"},
        {"id": 2, "name": "S3 Integration", "platform": "AWS", "status": "deployed"},
        {"id": 3, "name": "Database Tracking", "platform": "MySQL", "status": "operational"}
    ]
    
    print("\n2. Testing export functionality...")
    export_result = client.export(sample_data, 'json', 'mysql_render_test', 'test_user')
    
    if export_result['success']:
        print(f"✅ Export successful!")
        print(f"   Operation ID: {export_result['operation_id']}")
        print(f"   File: {export_result['export_info']['storedName']}")
        print(f"   URL: {export_result['export_info']['url']}")
        
        # Test download
        print("\n3. Testing download functionality...")
        s3_key = export_result['export_info']['s3Key']
        file_name = export_result['export_info']['storedName']
        
        download_result = client.download(s3_key, file_name, './mysql_downloads', 'test_user')
        
        if download_result['success']:
            print(f"✅ Download successful!")
            print(f"   Operation ID: {download_result['operation_id']}")
            print(f"   File saved: {download_result['file_path']}")
        else:
            print(f"❌ Download failed: {download_result['error']}")
    else:
        print(f"❌ Export failed: {export_result['error']}")
    
    # Show operation history
    print("\n4. Operation history from MySQL:")
    history = client.get_operation_history('test_user', 5)
    
    if history:
        for i, op in enumerate(history, 1):
            print(f"   {i}. {op['operation_type']} - {op['file_name']} - {op['status']} ({op['created_at']})")
    else:
        print("   No operations found in database")
    
    # Show statistics
    print("\n5. Database statistics:")
    stats = client.get_operation_stats()
    
    if stats:
        print(f"   Total operations: {stats.get('total_operations', 0)}")
        print(f"   Completed: {stats.get('total_completed', 0)}")
        print(f"   Failed: {stats.get('total_failed', 0)}")
        
        if stats.get('operations_by_type'):
            print("   Operations by type:")
            for op_stat in stats['operations_by_type']:
                print(f"     - {op_stat['operation_type']}: {op_stat['total_count']} total")
    
    print("\n🎉 Render + MySQL integration test completed!")

if __name__ == "__main__":
    main()