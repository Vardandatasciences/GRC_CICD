import json
import os
import uuid
import datetime
import mysql.connector
import pandas as pd
from io import BytesIO
import xmltodict
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import django
from django.conf import settings

# Import the S3 microservice client
from .s3_fucntions import create_direct_mysql_client

# Initialize Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# Import the AWSCredentials model
from grc.models import AWSCredentials

# Database configuration using Django settings
db_config = settings.DATABASES['default']

# Initialize S3 microservice client
try:
    mysql_config = {
        'host': db_config['HOST'],
        'user': db_config['USER'],
        'password': db_config['PASSWORD'],
        'database': db_config['NAME'],
        'port': db_config.get('PORT', 3306)
    }
    s3_client = create_direct_mysql_client(mysql_config)
    print("S3 microservice client initialized successfully")
except Exception as e:
    print(f"WARNING: S3 microservice client initialization failed: {str(e)}")
    s3_client = None

def get_aws_credentials():
    """Get AWS credentials from database"""
    try:
        credentials = AWSCredentials.get_active_credentials()
        if credentials:
            return {
                'access_key_id': credentials.accessKey,
                'secret_access_key': credentials.secretKey,
                'region_name': credentials.region,
                'bucket_name': credentials.bucketName
            }
        else:
            raise Exception("No AWS credentials found in database")
    except Exception as e:
        print(f"Error getting AWS credentials from database: {str(e)}")
        raise

# Get AWS credentials from database (for reference only)
try:
    aws_config = get_aws_credentials()
    BUCKET_NAME = aws_config['bucket_name']
    print(f"AWS credentials loaded for bucket: {BUCKET_NAME}")
except Exception as e:
    print(f"Warning: Could not load AWS credentials: {str(e)}")
    BUCKET_NAME = None

# Sample data for testing
# SAMPLE_DATA = [
#     {"id": 1, "name": "John Doe", "email": "john@example.com", "department": "IT", "salary": 75000},
#     {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "department": "HR", "salary": 65000},
#     {"id": 3, "name": "Bob Johnson", "email": "bob@example.com", "department": "Marketing", "salary": 60000},
#     {"id": 4, "name": "Alice Brown", "email": "alice@example.com", "department": "Finance", "salary": 80000},
#     {"id": 5, "name": "Charlie Wilson", "email": "charlie@example.com", "department": "IT", "salary": 70000}
# ]

def get_db_connection():
    """Get a database connection using Django settings"""
    return mysql.connector.connect(
        host=db_config['HOST'],
        user=db_config['USER'],
        password=db_config['PASSWORD'],
        database=db_config['NAME'],
        port=db_config.get('PORT', 3306),
        autocommit=True
    )

def save_export_record(export_data):
    """Save export record to database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
        INSERT INTO exported_files 
        (export_data, file_type, user_id, s3_url, file_name, status, metadata, created_at, updated_at) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        now = datetime.datetime.now()
        
        cursor.execute(query, (
            json.dumps(export_data.get('export_data')),
            export_data.get('file_type'),
            export_data.get('user_id'),
            export_data.get('s3_url', ''),  # S3 URL initially empty
            export_data.get('file_name'),
            export_data.get('status', 'pending'),
            json.dumps(export_data.get('metadata', {})),
            now,
            now
        ))
        
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()

def update_export_status(export_id, status, error=None):
    """Update export record status"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
        UPDATE exported_files 
        SET status = %s, error = %s, updated_at = %s
        """
        
        params = [status, error, datetime.datetime.now()]
        
        if status == 'completed':
            query += ", completed_at = %s"
            params.append(datetime.datetime.now())
            
        query += " WHERE id = %s"
        params.append(export_id)
        
        cursor.execute(query, params)
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def update_export_metadata(export_id, metadata):
    """Update export metadata"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get existing metadata
        cursor.execute("SELECT metadata FROM exported_files WHERE id = %s", (export_id,))
        result = cursor.fetchone()
        
        if result:
            existing_metadata = json.loads(result[0] or '{}')
            updated_metadata = {**existing_metadata, **metadata}
            
            cursor.execute(
                "UPDATE exported_files SET metadata = %s, updated_at = %s WHERE id = %s",
                (json.dumps(updated_metadata), datetime.datetime.now(), export_id)
            )
            conn.commit()
    finally:
        cursor.close()
        conn.close()

def update_export_url(export_id, s3_url):
    """Update export record with S3 URL"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE exported_files SET s3_url = %s, updated_at = %s WHERE id = %s",
            (s3_url, datetime.datetime.now(), export_id)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def export_to_excel(data):
    """Export data to Excel format with enhanced formatting"""
    try:
        # Convert data to DataFrame
        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            df = pd.DataFrame(data)
        
        # Clean the data: Replace NaN, None, and INF values with empty string
        import numpy as np
        df = df.replace([np.nan, np.inf, -np.inf, None], '')
        
        # Convert all data to string to avoid type issues, then back to appropriate types
        for col in df.columns:
            try:
                # Try to convert to numeric if possible, otherwise keep as string
                # Suppress the FutureWarning by using try-except instead
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(df[col])
            except:
                pass
        
        output = BytesIO()
        
        # Try to use xlsxwriter engine first (preferred for formatting)
        try:
            print("Attempting Excel export with xlsxwriter...")
            # Since we've already cleaned the data, we can use a simple ExcelWriter
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                workbook = writer.book
                worksheet = workbook.add_worksheet('Export')
                
                # Format the header
                header_format = workbook.add_format({
                    'bold': True, 
                    'bg_color': '#4F6CFF',
                    'font_color': 'white',
                    'border': 1,
                    'align': 'center',
                    'valign': 'vcenter'
                })
                
                # Add alternating row colors for better readability
                row_format_even = workbook.add_format({'bg_color': '#F8F9FA'})
                row_format_odd = workbook.add_format({'bg_color': '#FFFFFF'})
                
                # Write headers
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, str(value), header_format)
                    
                # Adjust column widths dynamically
                for i, col in enumerate(df.columns):
                    try:
                        max_length = max(
                            df[col].astype(str).map(len).max(),
                            len(str(col))
                        )
                        worksheet.set_column(i, i, min(max_length + 3, 50))
                    except:
                        worksheet.set_column(i, i, 15)
                
                # Write data with safe handling - write cell by cell
                for row_num in range(len(df)):
                    row_format = row_format_even if (row_num + 1) % 2 == 0 else row_format_odd
                    for col_num in range(len(df.columns)):
                        cell_value = df.iloc[row_num, col_num]
                        # Convert any remaining problematic values to empty string
                        if cell_value is None or cell_value == '':
                            cell_value = ''
                        elif pd.isna(cell_value):
                            cell_value = ''
                        elif isinstance(cell_value, (float, np.floating)):
                            if np.isnan(cell_value) or np.isinf(cell_value):
                                cell_value = ''
                        # Write to row_num + 1 because row 0 is the header
                        worksheet.write(row_num + 1, col_num, cell_value, row_format)
                        
            print(f"✅ Excel export successful with xlsxwriter. File size: {len(output.getvalue())} bytes")
            
        except ImportError as xlsxwriter_error:
            # Fall back to openpyxl if xlsxwriter is not available
            print(f"xlsxwriter not found ({xlsxwriter_error}), trying openpyxl instead...")
            try:
                from openpyxl import Workbook
                from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
                
                output = BytesIO()
                # Clean data again for openpyxl
                df_clean = df.replace([np.nan, np.inf, -np.inf, None], '')
                
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_clean.to_excel(writer, sheet_name='Export', index=False)
                    
                    # Get the worksheet
                    worksheet = writer.sheets['Export']
                    
                    # Style the header row
                    header_fill = PatternFill(start_color='4F6CFF', end_color='4F6CFF', fill_type='solid')
                    header_font = Font(bold=True, color='FFFFFF')
                    header_alignment = Alignment(horizontal='center', vertical='center')
                    
                    for cell in worksheet[1]:
                        cell.fill = header_fill
                        cell.font = header_font
                        cell.alignment = header_alignment
                    
                    # Adjust column widths
                    for i, col in enumerate(df.columns):
                        try:
                            max_length = max(
                                df_clean[col].astype(str).map(len).max(),
                                len(str(col))
                            )
                            worksheet.column_dimensions[chr(65 + i)].width = min(max_length + 3, 50)
                        except:
                            worksheet.column_dimensions[chr(65 + i)].width = 15
                
                print(f"✅ Excel export successful with openpyxl. File size: {len(output.getvalue())} bytes")
                
            except ImportError as openpyxl_error:
                print(f"❌ Both xlsxwriter and openpyxl not available. Error: {openpyxl_error}")
                raise ImportError(f"Excel export requires either xlsxwriter or openpyxl library. Please install one: pip install xlsxwriter or pip install openpyxl")
    
        output.seek(0)
        return output.getvalue()
        
    except Exception as e:
        print(f"❌ Excel export error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise Exception(f"Excel export failed: {str(e)}")

def export_to_csv(data):
    """Export data to CSV format"""
    df = pd.DataFrame(data)
    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return output.getvalue()

def export_to_json(data):
    """Export data to JSON format"""
    return json.dumps(data, indent=2).encode('utf-8')

def export_to_xml(data):
    """Export data to XML format"""
    root_name = 'export'
    if isinstance(data, list):
        xml_data = {root_name: {'item': data}}
    else:
        xml_data = {root_name: data}
    
    xml_string = xmltodict.unparse(xml_data, pretty=True)
    return xml_string.encode('utf-8')

def export_to_pdf(data):
    """Export data to PDF format"""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Add title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(width/2 - 50, height - 50, "Export Report")
    
    # Add data
    c.setFont("Helvetica", 12)
    y_position = height - 100
    
    if isinstance(data, list):
        for i, item in enumerate(data):
            c.drawString(50, y_position, f"Item {i+1}:")
            y_position -= 20
            
            for key, value in item.items():
                c.drawString(70, y_position, f"{key}: {value}")
                y_position -= 20
                
                if y_position < 50:  # Add a new page if needed
                    c.showPage()
                    y_position = height - 50
    else:
        for key, value in data.items():
            c.drawString(50, y_position, f"{key}: {value}")
            y_position -= 20
            
            if y_position < 50:  # Add a new page if needed
                c.showPage()
                y_position = height - 50
    
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

def export_to_txt(data):
    """Export data to Text format"""
    buffer = BytesIO()
    
    buffer.write(b"Export Report\n")
    buffer.write(b"=" * 50 + b"\n\n")
    buffer.write(f"Generated: {datetime.datetime.now().isoformat()}\n\n".encode('utf-8'))
    
    def format_item(item, level=0):
        indent = "  " * level
        
        if isinstance(item, list):
            for i, element in enumerate(item):
                buffer.write(f"{indent}Item {i+1}:\n".encode('utf-8'))
                format_item(element, level + 1)
        elif isinstance(item, dict):
            for key, value in item.items():
                if isinstance(value, (dict, list)):
                    buffer.write(f"{indent}{key}:\n".encode('utf-8'))
                    format_item(value, level + 1)
                else:
                    buffer.write(f"{indent}{key}: {value}\n".encode('utf-8'))
        else:
            buffer.write(f"{indent}{item}\n".encode('utf-8'))
    
    format_item(data)
    
    buffer.write(b"\n" + b"=" * 50 + b"\n")
    buffer.write(b"End of Report")
    
    buffer.seek(0)
    return buffer.getvalue()

def upload_to_s3(file_buffer, file_name, content_type):
    """Upload file to S3 bucket using microservice"""
    if not s3_client:
        raise Exception("S3 microservice client not initialized")
    
    try:
        # Convert file buffer to temporary file for upload
        import tempfile
        # Extract extension from filename
        file_extension = file_name.split('.')[-1] if '.' in file_name else 'bin'
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
            temp_file.write(file_buffer)
            temp_file_path = temp_file.name
        
        # Upload using S3 microservice
        upload_result = s3_client.upload(temp_file_path, user_id="export_user", custom_file_name=file_name)
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        if upload_result['success']:
            return {
                'url': upload_result['file_info']['url'],
                'bucket': upload_result['file_info'].get('bucket', ''),
                'key': upload_result['file_info']['s3Key'],
                'region': 'ap-south-1'  # Default region for microservice
            }
        else:
            raise Exception(f"Upload failed: {upload_result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"S3 upload failed: {str(e)}")
        # Save locally as fallback
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        local_path = os.path.join(downloads_path, file_name)
        
        with open(local_path, 'wb') as f:
            f.write(file_buffer)
            
        print(f"File saved locally instead at: {local_path}")
        return {
            'url': f"file://{local_path}",
            'bucket': 'local',
            'key': local_path,
            'region': 'local'
        }

def get_content_type(file_type):
    """Get content type based on file extension"""
    content_types = {
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'csv': 'text/csv',
        'json': 'application/json',
        'xml': 'application/xml',
        'txt': 'text/plain'
    }
    
    return content_types.get(file_type, 'application/octet-stream')

def local_export_fallback(data, file_format, user_id, options):
    """Local export fallback when S3 microservice is not available"""
    try:
        print(f"🔄 Using local export fallback for format: {file_format}")
        
        # Generate filename
        timestamp = datetime.datetime.now().timestamp()
        if options and options.get('file_name'):
            base_name = options.get('file_name')
            if '.' in base_name:
                base_name = base_name.rsplit('.', 1)[0]
            file_name = f"{base_name}.{file_format}"
        else:
            file_name = f"export_{user_id}_{int(timestamp)}.{file_format}"
        
        # Export locally
        export_functions = {
            'xlsx': export_to_excel,
            'pdf': export_to_pdf,
            'csv': export_to_csv,
            'json': export_to_json,
            'xml': export_to_xml,
            'txt': export_to_txt
        }
        
        if file_format.lower() not in export_functions:
            return {
                'success': False,
                'error': f'Unsupported export format: {file_format}. Supported: {list(export_functions.keys())}'
            }
        
        file_buffer = export_functions[file_format.lower()](data)
        
        # Save locally as fallback
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        local_path = os.path.join(downloads_path, file_name)
        
        with open(local_path, 'wb') as f:
            f.write(file_buffer)
        
        print(f"✅ Local export successful: {local_path}")
        
        return {
            'success': True,
            'file_url': f"file://{local_path}",
            'file_name': file_name,
            'file_size': len(file_buffer),
            'metadata': {
                'file_size': len(file_buffer),
                'format': file_format,
                'record_count': len(data) if isinstance(data, list) else 1,
                'method': 'local_fallback',
                'local_path': local_path
            }
        }
        
    except Exception as e:
        print(f"❌ Local export fallback failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': f'Local export failed: {str(e)}'
        }

def export_data(data=None, file_format='xlsx', user_id='user123', options=None):
    """
    Export data to the specified format using S3 microservice
    
    Args:
        data: The data to export (uses sample data if None)
        file_format: Format to export (xlsx, pdf, csv, json, xml, txt)
        user_id: ID of the user requesting the export
        options: Additional export options
        
    Returns:
        Dictionary with export results
    """
    if data is None:
        data = []
        
    if options is None:
        options = {}
    
    # Validate data size to prevent 413 errors
    data_size = len(str(data))
    max_size = 40 * 1024 * 1024  # 40MB limit
    if data_size > max_size:
        return {
            'success': False,
            'error': f'Data too large for export ({data_size} bytes). Maximum allowed: {max_size} bytes. Please reduce the data size or use pagination.'
        }
    
    print(f"📊 Export data validation:")
    print(f"   Data size: {data_size} bytes")
    print(f"   Records: {len(data) if isinstance(data, list) else 1}")
    print(f"   Format: {file_format}")
    
    export_id = None
    timestamp = datetime.datetime.now().timestamp()
    
    # Generate filename with proper extension
    if options.get('file_name'):
        base_name = options.get('file_name')
        # Remove any existing extension
        if '.' in base_name:
            base_name = base_name.rsplit('.', 1)[0]
        # Add the correct extension
        file_name = f"{base_name}.{file_format}"
    else:
        file_name = f"export_{user_id}_{int(timestamp)}.{file_format}"
    
    try:
        # Check if S3 microservice client is available
        if not s3_client:
            print("⚠️  S3 microservice client not available, using local export fallback")
            # Use local export without S3 upload
            return local_export_fallback(data, file_format, user_id, options)
        
        # Validate format - check what formats are supported by microservice
        microservice_supported_formats = ['json', 'csv', 'xml', 'txt', 'pdf']
        all_supported_formats = ['json', 'csv', 'xml', 'txt', 'pdf', 'xlsx']
        
        if file_format.lower() not in all_supported_formats:
            raise ValueError(f"Unsupported export format: {file_format}. Supported: {all_supported_formats}")
        
        # Check if format is supported by microservice OR if dataset is too large
        # For large datasets (>1000 records or >1MB), use local export to avoid timeout
        record_count = len(data) if isinstance(data, list) else 1
        data_size_mb = data_size / (1024 * 1024)
        use_local_export = (
            file_format.lower() not in microservice_supported_formats or
            record_count > 1000 or  # More than 1000 records
            data_size_mb > 1.0  # More than 1MB of data
        )
        
        if use_local_export:
            # Use local export for unsupported formats OR large datasets to avoid timeout
            if file_format.lower() not in microservice_supported_formats:
                print(f"Format {file_format} not supported by microservice, using local export + upload")
            else:
                print(f"Large dataset detected ({record_count} records, {data_size_mb:.2f}MB), using local export + upload to avoid timeout")
            
            # Create export record
            export_id = save_export_record({
                'export_data': data,
                'file_type': file_format,
                'user_id': user_id,
                'file_name': file_name,
                'status': 'pending',
                'metadata': {
                    'record_count': len(data) if isinstance(data, list) else 1,
                    'filters': options.get('filters', {}),
                    'columns': options.get('columns', []),
                    'method': 'local_export_upload'
                }
            })
            
            # Update status to processing
            update_export_status(export_id, 'processing')
            
            # Export to file locally
            print(f"Converting data to {file_format} format locally...")
            print(f"📁 Final filename will be: {file_name}")
            start_time = datetime.datetime.now()
            
            export_functions = {
                'xlsx': export_to_excel,
                'pdf': export_to_pdf,
                'csv': export_to_csv,
                'json': export_to_json,
                'xml': export_to_xml,
                'txt': export_to_txt
            }
            
            file_buffer = export_functions[file_format](data)
            print(f"Data converted successfully. File size: {len(file_buffer)} bytes")
            
            # Upload to S3 using microservice
            try:
                print(f"Attempting to upload file to S3: {file_name}")
                content_type = get_content_type(file_format)
                s3_result = upload_to_s3(file_buffer, file_name, content_type)
                print(f"File uploaded successfully to S3: {s3_result['url']}")
                
                # Update the S3 URL in the database
                update_export_url(export_id, s3_result['url'])
                
                # Update export record with metadata
                duration = (datetime.datetime.now() - start_time).total_seconds() * 1000
                update_export_metadata(export_id, {
                    'file_size': len(file_buffer),
                    'export_duration': duration,
                    's3_metadata': {
                        'bucket': s3_result['bucket'],
                        'key': s3_result['key'],
                        'region': s3_result['region'],
                        'upload_time': datetime.datetime.now().isoformat()
                    }
                })
                
                # Update status to completed
                update_export_status(export_id, 'completed')
                
                return {
                    'success': True,
                    'export_id': export_id,
                    'file_url': s3_result['url'],
                    'file_name': file_name,
                    'metadata': {
                        'file_size': len(file_buffer),
                        'format': file_format,
                        'record_count': len(data) if isinstance(data, list) else 1,
                        'export_duration': duration,
                        'method': 'local_export_upload'
                    }
                }
                
            except Exception as s3_error:
                print(f"S3 upload failed: {str(s3_error)}")
                update_export_status(export_id, 'failed', str(s3_error))
                update_export_metadata(export_id, {
                    'error': {
                        'message': str(s3_error),
                        'timestamp': datetime.datetime.now().isoformat(),
                    }
                })
                return {
                    'success': False,
                    'error': f"S3 upload failed: {str(s3_error)}"
                }
        
        else:
            # Use microservice directly for supported formats
            print(f"Using S3 microservice for {file_format} export...")
            
            # Create export record
            export_id = save_export_record({
                'export_data': data,
                'file_type': file_format,
                'user_id': user_id,
                'file_name': file_name,
                'status': 'pending',
                'metadata': {
                    'record_count': len(data) if isinstance(data, list) else 1,
                    'filters': options.get('filters', {}),
                    'columns': options.get('columns', []),
                    'method': 'microservice_direct'
                }
            })
            
            # Update status to processing
            update_export_status(export_id, 'processing')
            
            # Export using microservice
            start_time = datetime.datetime.now()
            export_result = s3_client.export(data, file_format, file_name, user_id)
            
            if export_result['success']:
                export_info = export_result['export_info']
                
                # Update the S3 URL in the database
                update_export_url(export_id, export_info['url'])
                
                # Update export record with metadata
                duration = (datetime.datetime.now() - start_time).total_seconds() * 1000
                update_export_metadata(export_id, {
                    'file_size': export_info.get('size', 0),
                    'export_duration': duration,
                    's3_metadata': {
                        'bucket': export_info.get('bucket', ''),
                        'key': export_info.get('s3Key', ''),
                        'region': 'ap-south-1',
                        'upload_time': datetime.datetime.now().isoformat()
                    }
                })
                
                # Update status to completed
                update_export_status(export_id, 'completed')
                
                return {
                    'success': True,
                    'export_id': export_id,
                    'file_url': export_info['url'],
                    'file_name': export_info.get('storedName', file_name),
                    'metadata': {
                        'file_size': export_info.get('size', 0),
                        'format': file_format,
                        'record_count': len(data) if isinstance(data, list) else 1,
                        'export_duration': duration,
                        'method': 'microservice_direct'
                    }
                }
            else:
                # Update MySQL with failure
                error_msg = export_result.get('error', 'Unknown error')
                update_export_status(export_id, 'failed', error_msg)
                update_export_metadata(export_id, {
                    'error': {
                        'message': error_msg,
                        'timestamp': datetime.datetime.now().isoformat(),
                    }
                })
                return {
                    'success': False,
                    'error': error_msg
                }
        
    except Exception as e:
        print(f"Export error: {str(e)}")
        if export_id:
            update_export_status(export_id, 'failed', str(e))
            update_export_metadata(export_id, {
                'error': {
                    'message': str(e),
                    'timestamp': datetime.datetime.now().isoformat(),
                }
            })
        return {
            'success': False,
            'error': str(e)
        }

# # Example usage with sample data
# if __name__ == "__main__":
#     result = export_data(SAMPLE_DATA, 'xlsx', 'test_user')
#     print(f"Export successful. File URL: {result['file_url']}") 

def test_export_service():
    """Test the updated export service with S3 microservice"""
    print("🧪 Testing updated export service with S3 microservice...")
    
    # Test data
    test_data = [
        {"id": 1, "name": "Test User", "email": "test@example.com", "department": "IT"},
        {"id": 2, "name": "Another User", "email": "another@example.com", "department": "HR"}
    ]
    
    try:
        # Test JSON export (supported by microservice)
        print("\n📊 Testing JSON export...")
        result = export_data(test_data, 'json', 'test_user', {'file_name': 'test_export.json'})
        
        if result['success']:
            print(f"✅ JSON export successful!")
            print(f"   File URL: {result['file_url']}")
            print(f"   File name: {result['file_name']}")
            print(f"   Method: {result['metadata']['method']}")
        else:
            print(f"❌ JSON export failed: {result['error']}")
        
        # Test XLSX export (requires local export + upload)
        print("\n📊 Testing XLSX export...")
        result = export_data(test_data, 'xlsx', 'test_user', {'file_name': 'test_export.xlsx'})
        
        if result['success']:
            print(f"✅ XLSX export successful!")
            print(f"   File URL: {result['file_url']}")
            print(f"   File name: {result['file_name']}")
            print(f"   Method: {result['metadata']['method']}")
        else:
            print(f"❌ XLSX export failed: {result['error']}")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")

if __name__ == "__main__":
    test_export_service() 