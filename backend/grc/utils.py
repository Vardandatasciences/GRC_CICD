from django.utils.dateparse import parse_date as django_parse_date
from datetime import datetime
import requests
from .models import GRCLog

def parse_date(date_str):
    """Safely parse a date string into a date object"""
    if not date_str:
        return None
    return django_parse_date(date_str)

def safe_isoformat(val):
    """Safely convert a date to ISO format string"""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.isoformat()
    if hasattr(val, 'isoformat'):
        return val.isoformat()
    return str(val)

# Logging service configuration
LOGGING_SERVICE_URL = None  # Disabled external logging service

def send_log(module, actionType, description=None, userId=None, userName=None,
             userRole=None, entityType=None, logLevel='INFO', ipAddress=None,
             additionalInfo=None, entityId=None):
   
    # Create log entry in database
    try:
        # Prepare data for GRCLog model
        log_data = {
            'Timestamp': datetime.now(),
            'Module': module,
            'ActionType': actionType,
            'Description': description,
            'UserId': str(userId) if userId else None,
            'UserName': userName,
            'EntityType': entityType,
            'EntityId': str(entityId) if entityId else None,
            'LogLevel': logLevel,
            'IPAddress': ipAddress,
            'AdditionalInfo': additionalInfo
        }
       
        # Remove None values
        log_data = {k: v for k, v in log_data.items() if v is not None}
       
        # Create and save the log entry
        log_entry = GRCLog(**log_data)
        log_entry.save()
       
        # Optionally still send to logging service if needed
        try:
            if LOGGING_SERVICE_URL:
                # Format for external service (matches expected format in loggingservice.js)
                api_log_data = {
                    "module": module,
                    "actionType": actionType,  # This is exactly what the service expects
                    "description": description,
                    "userId": userId,
                    "userName": userName,
                    "userRole": userRole,
                    "entityType": entityType,
                    "logLevel": logLevel,
                    "ipAddress": ipAddress,
                    "additionalInfo": additionalInfo
                }
                # Clean out None values
                api_log_data = {k: v for k, v in api_log_data.items() if v is not None}
               
                response = requests.post(LOGGING_SERVICE_URL, json=api_log_data)
                if response.status_code != 200:
                    print(f"Failed to send log to service: {response.text}")
        except Exception as e:
            print(f"Error sending log to service: {str(e)}")
           
        return log_entry.LogId  # Return the ID of the created log
    except Exception as e:
        print(f"Error saving log to database: {str(e)}")
        # Try to capture the error itself
        try:
            error_log = GRCLog(
                Timestamp=datetime.now(),
                Module=module,
                ActionType='LOG_ERROR',
                Description=f"Error logging {actionType} on {module}: {str(e)}",
                LogLevel='ERROR'
            )
            error_log.save()
        except:
            pass  # If we can't even log the error, just continue
        return None

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip 