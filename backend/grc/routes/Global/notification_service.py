import smtplib
import requests
import json
import mysql.connector
import os
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime
import logging
import traceback

# Load environment variables
load_dotenv()

# Configure logger - only console output, no file logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("notification_service")

class NotificationService:
    def __init__(self):
        # Database connection
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', 'root'),
            'database': os.getenv('DB_NAME', 'grc')
        }
        
        # WhatsApp configuration
        self.whatsapp_config = {
            'api_version': 'v17.0',
            'phone_number_id': os.getenv('WHATSAPP_PHONE_NUMBER_ID', ''),
            'access_token': os.getenv('WHATSAPP_ACCESS_TOKEN', ''),
            'default_language': 'en_US',
            'sender_phone': os.getenv('WHATSAPP_SENDER_PHONE', '')
        }
        
        # Email configuration
        self.email_configs = {
            'gmail': {
                'service': 'gmail',
                'host': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                'port': int(os.getenv('SMTP_PORT', 587)),
                'auth': {
                    'user': os.getenv('SMTP_EMAIL', os.getenv('GMAIL_USER')),
                    'pass': os.getenv('SMTP_PASSWORD', os.getenv('GMAIL_APP_PASSWORD'))
                }
            },
            'microsoft': {
                'service': 'outlook',
                'host': 'smtp.office365.com',
                'port': 587,
                'auth': {
                    'user': os.getenv('MICROSOFT_USER', ''),
                    'pass': os.getenv('MICROSOFT_APP_PASSWORD', ''),
                },
                # Microsoft Graph API configuration

                'graph_api': {
                    'client_id': os.getenv('MICROSOFT_CLIENT_ID'),
                    'client_secret': os.getenv('MICROSOFT_CLIENT_SECRET'),
                    'tenant_id': os.getenv('MICROSOFT_TENANT_ID'),
                    'authority': os.getenv('MICROSOFT_AUTHORITY'),
                    'redirect_uri': os.getenv('MICROSOFT_REDIRECT_URI'),
                    'scopes': ['https://graph.microsoft.com/.default'],
                    'endpoint': 'https://graph.microsoft.com/v1.0'
                }
            }
        }
        
        self.default_from = {
            'email': os.getenv('DEFAULT_FROM_EMAIL'),
            'name': os.getenv('DEFAULT_FROM_NAME')
        }
        
        # Initialize templates
        self.init_templates()

        # Mapping for title index in template_data for subject replacement
        self.title_index_map = {
            'frameworkNewVersion': 1,  # index of framework_title in template_data
            'policyNewVersion': 1,     # index of policy_title in template_data
            'frameworkSubmitted': 1,   # index of framework_title in template_data
            'policySubmitted': 1,      # index of policy_title in template_data
            'frameworkResubmitted': 1,
            'frameworkVersionSubmitted': 0,  # index of framework_title in template_data
            'policyVersionSubmitted': 0,     # index of policy_title in template_data
            'subpolicyApproved': 1,
            'subpolicyRejected': 1,
            'frameworkFinalApproved': 1,
            'frameworkRejected': 1,
            'policyApproved': 1,
            'policyRejected': 1,
            'policyResubmitted': 1,
            'subpolicyResubmitted': 1,
            'policyAcknowledgementRequired': 1,  # index of policy_name in template_data
            'complianceAssigned': 1,  # index of item_title in template_data
            'complianceReviewed': 1,  # index of item_title in template_data
            'complianceDueReminder': 1,  # index of item_title in template_data
            'eventCreated': 1,  # index of event_title in template_data
            'eventAssigned': 1,  # index of event_title in template_data
            'eventStatusChanged': 1,  # index of event_title in template_data
            # Add more if needed
        }
    
    def get_db_connection(self):
        """Establish database connection"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            return conn
        except mysql.connector.Error as err:
            logger.error(f"Database connection error: {err}")
            raise
    
    def get_user_email(self, user_id):
        """Get user email by user ID"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Query using the correct field name 'Email' (capital E)
            query = "SELECT Email FROM users WHERE UserId = %s"
            cursor.execute(query, (user_id,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                return result[0]
            else:
                logger.warning(f"No user found with ID: {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching user email for ID {user_id}: {str(e)}")
            return None
    
    def get_user_name(self, user_id):
        """Get user name by user ID"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Query using the correct field name 'UserName' 
            query = "SELECT UserName FROM users WHERE UserId = %s"
            cursor.execute(query, (user_id,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                return result[0]
            else:
                logger.warning(f"No user found with ID: {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching user name for ID {user_id}: {str(e)}")
            return None
    
    def init_templates(self):
        """Initialize notification templates"""
        # Email templates
        self.email_templates = {
            'welcome': {
                'subject': 'Welcome to Our Service!',
                'template': lambda user_name, team_name: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #3498db; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Welcome!</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {user_name},</p>
                    <p style="color: #333333; font-size: 16px;">Welcome to our service! We're excited to have you on board.</p>
                    <p style="color: #333333; margin-top: 20px;">Best regards,<br>The {team_name} Team</p>
                  </div>
                </div>
                """
            },
            'frameworkSubmitted': {
                'subject': 'Framework "{framework_title}" Submitted for Your Review',
                'template': lambda reviewer_name, framework_title, submitter_name: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #3498db; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Framework Review Required</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {reviewer_name},</p>
                    <p style="color: #333333; font-size: 16px;">{submitter_name} has submitted a new framework <strong>"{framework_title}"</strong> for your review.</p>
                    <p style="color: #333333; font-size: 16px;">Please review and either approve or reject this framework.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'frameworkResubmitted': {
                'subject': 'Framework "{framework_title}" Resubmitted for Your Review',
                'template': lambda reviewer_name, framework_title, submitter_name: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #f39c12; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Framework Resubmitted</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {reviewer_name},</p>
                    <p style="color: #333333; font-size: 16px;">{submitter_name} has resubmitted the framework <strong>"{framework_title}"</strong> for your review.</p>
                    <p style="color: #333333; font-size: 16px;">Please review and either approve or reject this framework.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'passwordReset': {
                'subject': 'Password Reset Request',
                'template': lambda user_name, reset_link: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #e74c3c; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Password Reset</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {user_name},</p>
                    <p style="color: #333333; font-size: 16px;">We received a request to reset your password. Click the link below to reset it:</p>
                    <p style="text-align: center; margin: 20px 0;">
                      <a href="{reset_link}" style="background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a>
                    </p>
                    <p style="color: #333333; font-size: 14px;">If you didn't request this, please ignore this email.</p>
                  </div>
                </div>
                """
            },
            'passwordResetOTP': {
                'subject': 'Password Reset OTP - {platform_name}',
                'template': lambda user_name, otp_code, expiry_time, platform_name: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #3b82f6; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Password Reset OTP</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {user_name},</p>
                    <p style="color: #333333; font-size: 16px;">We received a request to reset your password for your {platform_name} account.</p>
                    <p style="color: #333333; font-size: 16px;">Your One-Time Password (OTP) is:</p>
                    <div style="text-align: center; margin: 30px 0;">
                      <div style="background-color: #f8f9fa; border: 2px solid #3b82f6; border-radius: 10px; padding: 20px; display: inline-block;">
                        <span style="font-size: 32px; font-weight: bold; color: #3b82f6; letter-spacing: 5px;">{otp_code}</span>
                      </div>
                    </div>
                    <p style="color: #333333; font-size: 14px;"><strong>Important:</strong></p>
                    <ul style="color: #333333; font-size: 14px;">
                      <li>This OTP is valid for {expiry_time}</li>
                      <li>Do not share this OTP with anyone</li>
                      <li>If you didn't request this, please ignore this email</li>
                    </ul>
                    <p style="color: #333333; font-size: 14px; margin-top: 20px;">Best regards,<br>{platform_name} Team</p>
                  </div>
                </div>
                """
            },
            'accountUpdate': {
                'subject': 'Account Update Notification',
                'template': lambda user_name, update_details: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #2ecc71; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Account Update</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {user_name},</p>
                    <p style="color: #333333; font-size: 16px;">Your account has been updated with the following changes:</p>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                      {update_details}
                    </div>
                    <p style="color: #333333; margin-top: 20px;">Best regards,<br>Support Team</p>
                  </div>
                </div>
                """
            },
            # Policy notification templates
            'policySubmitted': {
                'subject': 'Policy "{policy_title}" Submitted for Your Review',
                'template': lambda reviewer_name, policy_title, submitter_name, due_date: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #3498db; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Policy Review Required</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {reviewer_name},</p>
                    <p style="color: #333333; font-size: 16px;">{submitter_name} has submitted <strong>"{policy_title}"</strong> for approval. Please review and either approve or reject by {due_date}.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'policyApproved': {
                'subject': 'Your Policy "{policy_title}" Has Been Approved',
                'template': lambda submitter_name, policy_title, reviewer_name, date_time: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #2ecc71; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Policy Approved</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hi {submitter_name},</p>
                    <p style="color: #333333; font-size: 16px;">Your policy <strong>"{policy_title}"</strong> was approved by {reviewer_name} on {date_time}. It is now active.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'policyRejected': {
                'subject': 'Your Policy "{policy_title}" Was Rejected',
                'template': lambda submitter_name, policy_title, reviewer_name, reviewer_comment: f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #e74c3c; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Policy Rejected</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {submitter_name},</p>
                    <p style="color: #333333; font-size: 16px;">Your policy <strong>"{policy_title}"</strong> was rejected by {reviewer_name}.</p>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                      <p style="color: #333333; font-style: italic;">Reason: {reviewer_comment}</p>
                    </div>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                '''
            },
            'policyNewVersion': {
                'subject': 'New Version of Policy "{policy_title}" Created',
                'template': lambda reviewer_name, policy_title, version, creator_name: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #3498db; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">New Policy Version</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {reviewer_name},</p>
                    <p style="color: #333333; font-size: 16px;">A new version (v{version}) of policy <strong>"{policy_title}"</strong> has been created by {creator_name}.</p>
                    <p style="color: #333333; font-size: 16px;">Please review the changes and either approve or reject this version.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'policyStatusChange': {
                'subject': 'Policy "{policy_title}" {status}',
                'template': lambda user_name, policy_title, status, actor_name, date_time: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #f39c12; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Policy Status Update</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {user_name},</p>
                    <p style="color: #333333; font-size: 16px;">The policy <strong>"{policy_title}"</strong> has just been <strong>{status}</strong> by {actor_name} on {date_time}.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'complianceAssigned': {
                'subject': 'New Compliance Task: "{item_title}"',
                'template': lambda officer_name, item_title, assignor_name, due_date: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #3498db; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">New Compliance Task</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hi {officer_name},</p>
                    <p style="color: #333333; font-size: 16px;">You've been assigned the compliance item <strong>"{item_title}"</strong> by {assignor_name}. Due by {due_date}.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'complianceDueReminder': {
                'subject': 'Reminder: Compliance "{item_title}" Due in 2 Days',
                'template': lambda officer_name, item_title, due_date: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #f39c12; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Compliance Due Reminder</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {officer_name},</p>
                    <p style="color: #333333; font-size: 16px;">This is a reminder that <strong>"{item_title}"</strong> is due on {due_date}.</p>
                    <p style="color: #333333; font-size: 16px;">Please update your progress.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'complianceCompleted': {
                'subject': 'Compliance "{item_title}" Ready for Review',
                'template': lambda reviewer_name, item_title, officer_name, review_due_date: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #2ecc71; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Compliance Ready for Review</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hi {reviewer_name},</p>
                    <p style="color: #333333; font-size: 16px;"><strong>"{item_title}"</strong> has been completed by {officer_name}.</p>
                    <p style="color: #333333; font-size: 16px;">Please review and approve or reject by {review_due_date}.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'complianceReviewed': {
                'subject': 'Your Compliance "{item_title}" Was {status}',
                'template': lambda officer_name, item_title, status, reviewer_name, reviewer_comment: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: {'#2ecc71' if status == 'Approved' else '#e74c3c'}; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Compliance {status}</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {officer_name},</p>
                    <p style="color: #333333; font-size: 16px;">Your compliance item <strong>"{item_title}"</strong> was <strong>{status}</strong> by {reviewer_name}.</p>
                    {f'<div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;"><p style="color: #333333; font-style: italic;">{reviewer_comment}</p></div>' if reviewer_comment else ''}
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'compliance_creation': {
                'subject': 'Compliance Request: {item_title}',
                'template': lambda reviewer_name, compliance_id, item_title, version, creator_name, created_date: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #3498db; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Compliance Request</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {reviewer_name},</p>
                    <p style="color: #333333; font-size: 16px;">A compliance item with ID <strong>{compliance_id}</strong> has generated a request:</p>
                    <p style="color: #333333; font-size: 16px; margin-top: 10px;"><strong>Title:</strong> {item_title}</p>
                    <p style="color: #333333; font-size: 16px;"><strong>Version:</strong> {version}</p>
                    <p style="color: #333333; font-size: 16px;"><strong>Requested By:</strong> {creator_name}</p>
                    <p style="color: #333333; font-size: 14px; margin-top: 10px;">Request Date: {created_date}</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'exportCompleted': {
                'subject': 'Your Export \"{file_name}\" Is Ready',
                'template': lambda user_name, file_name, file_type, s3_url, completed_at: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #2ecc71; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Export Completed</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {user_name},</p>
                    <p style="color: #333333; font-size: 16px;">Your {file_type.upper()} export <strong>"{file_name}"</strong> has finished processing.</p>
                    {f'<p style="color: #333333; font-size: 14px; margin-top: 10px;">Completed at: {completed_at}</p>' if completed_at else ''}
                    {f'<p style="color: #333333; font-size: 14px; margin-top: 15px;">You can download it from:<br><a href="{s3_url}" style="color: #3498db;">{s3_url}</a></p>' if s3_url else ''}
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'auditAssigned': {
                'subject': 'New Audit Assigned: "{audit_title}"',
                'template': lambda auditor_name, audit_title, scope, start_date: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #3498db; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">New Audit Assignment</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hi {auditor_name},</p>
                    <p style="color: #333333; font-size: 16px;">You have been assigned audit <strong>"{audit_title}"</strong> covering {scope}. Start by {start_date}.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'auditStartReminder': {
                'subject': 'Audit "{audit_title}" Starts Today',
                'template': lambda auditor_name, audit_title: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #f39c12; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Audit Start Reminder</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {auditor_name},</p>
                    <p style="color: #333333; font-size: 16px;">Your audit <strong>"{audit_title}"</strong> begins today. Please begin your fieldwork.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'auditCompleted': {
                'subject': 'Audit "{audit_title}" Ready for Review',
                'template': lambda reviewer_name, audit_title, auditor_name, review_due_date: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #2ecc71; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Audit Ready for Review</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hi {reviewer_name},</p>
                    <p style="color: #333333; font-size: 16px;">{auditor_name} has completed <strong>"{audit_title}"</strong>. Please review the findings by {review_due_date}.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'auditReviewed': {
                'subject': 'Your Audit "{audit_title}" Review Is Complete',
                'template': lambda auditor_name, audit_title, status, reviewer_name, reviewer_comment: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: {'#2ecc71' if status == 'Approved' else '#e74c3c'}; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Audit {status}</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {auditor_name},</p>
                    <p style="color: #333333; font-size: 16px;">Your audit <strong>"{audit_title}"</strong> was <strong>{status}</strong> by {reviewer_name}.</p>
                    {f'<div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;"><p style="color: #333333; font-style: italic;">{reviewer_comment}</p></div>' if reviewer_comment else ''}
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'riskIdentified': {
                'subject': 'New Risk "{risk_title}" Logged',
                'template': lambda risk_mgr, risk_title, category, creator_name: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #e74c3c; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">New Risk Identified</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {risk_mgr},</p>
                    <p style="color: #333333; font-size: 16px;">A new risk <strong>"{risk_title}"</strong> (Category: {category}) was identified by {creator_name}.</p>
                    <p style="color: #333333; font-size: 16px;">Please assess it.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'riskMitigationAssigned': {
                'subject': 'Risk Mitigation Task: "{risk_title}"',
                'template': lambda mitigator, risk_title, due_date: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #3498db; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Risk Mitigation Assigned</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hi {mitigator},</p>
                    <p style="color: #333333; font-size: 16px;">You've been assigned mitigation for risk <strong>"{risk_title}"</strong> due {due_date}.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'riskMitigationCompleted': {
                'subject': 'Mitigation for "{risk_title}" Ready for Review',
                'template': lambda reviewer_name, risk_title, mitigator, review_due_date: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #2ecc71; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Risk Mitigation Completed</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {reviewer_name},</p>
                    <p style="color: #333333; font-size: 16px;">{mitigator} has completed mitigation for <strong>"{risk_title}"</strong>. Review by {review_due_date}.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'riskScoreUpdated': {
                'subject': 'Risk "{risk_title}" Score Updated',
                'template': lambda risk_mgr, risk_title, old_score, new_score, actor_name: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #f39c12; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Risk Score Updated</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Dear {risk_mgr},</p>
                    <p style="color: #333333; font-size: 16px;">The score for <strong>"{risk_title}"</strong> has been updated from {old_score} to {new_score} by {actor_name}.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'incidentEscalated': {
                'subject': 'Incident "{incident_title}" Escalated',
                'template': lambda manager_name, incident_title, escalator_name: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #e74c3c; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Incident Escalated</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {manager_name},</p>
                    <p style="color: #333333; font-size: 16px;">Incident <strong>"{incident_title}"</strong> was escalated by {escalator_name}. Please review immediately.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'incidentAssigned': {
                'subject': 'New Incident Assigned: "{incident_title}"',
                'template': lambda assignee_name, incident_title, due_date: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #3498db; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">New Incident Assignment</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hi {assignee_name},</p>
                    <p style="color: #333333; font-size: 16px;">You've been assigned incident <strong>"{incident_title}"</strong>. Please investigate by {due_date}.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'incidentResolved': {
                'subject': 'Incident "{incident_title}" Resolved',
                'template': lambda incident_title, assignee_name, date_time: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #2ecc71; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Incident Resolved</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello,</p>
                    <p style="color: #333333; font-size: 16px;">Incident <strong>"{incident_title}"</strong> has been resolved by {assignee_name} on {date_time}.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'roleAssignmentChanged': {
                'subject': 'Your GRC Role Has Been Updated',
                'template': lambda user_name, new_role, admin_name: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #3498db; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Role Update</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hi {user_name},</p>
                    <p style="color: #333333; font-size: 16px;">Your role has been updated to <strong>{new_role}</strong> by {admin_name}. Effective immediately.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'systemMaintenance': {
                'subject': 'Scheduled Maintenance on {date}',
                'template': lambda date, start_time, end_time: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #f39c12; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">System Maintenance</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Dear User,</p>
                    <p style="color: #333333; font-size: 16px;">GRC will undergo maintenance from {start_time} to {end_time}. The system will be unavailable during this window.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'frameworkNewVersion': {
                'subject': 'New Version of Framework "{framework_title}" Created',
                'template': lambda reviewer_name, framework_title, version, creator_name: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #3498db; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">New Framework Version</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {reviewer_name},</p>
                    <p style="color: #333333; font-size: 16px;">A new version (v{version}) of framework <strong>"{framework_title}"</strong> has been created by {creator_name}.</p>
                    <p style="color: #333333; font-size: 16px;">Please review the changes and either approve or reject this version.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'policiesBatchSubmitted': {
                'subject': 'Multiple Policies Submitted for Your Review',
                'template': lambda reviewer_name, submitter_name, policy_list_html: f"""
                    <div style=\"font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;\">
                      <div style=\"background-color: #3498db; padding: 20px; text-align: center;\">
                        <h1 style=\"color: #ffffff; margin: 0; font-size: 28px;\">Policy Review Required</h1>
                      </div>
                      <div style=\"padding: 20px;\">
                        <p style=\"color: #333333; font-size: 16px;\">Hello {reviewer_name},</p>
                        <p style=\"color: #333333; font-size: 16px;\">{submitter_name} has submitted the following policies for your review:</p>
                        <ul style=\"color: #333333; font-size: 16px;\">{policy_list_html}</ul>
                        <p style=\"color: #333333; margin-top: 20px;\">– GRC Team</p>
                      </div>
                    </div>
                """
            },
            'frameworkExpiring': {
                'subject': 'Framework "{framework_title}" Will Expire Soon',
                'template': lambda framework_title, end_date: f'''
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                      <div style="background-color: #e74c3c; padding: 20px; text-align: center;">
                        <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Framework Expiry Notice</h1>
                      </div>
                      <div style="padding: 20px;">
                        <p style="color: #333333; font-size: 16px;">The framework <strong>{framework_title}</strong> will expire on <strong>{end_date}</strong>.</p>
                        
                        <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                      </div>
                    </div>
                '''
            },
            'policyExpiring': {
                'subject': 'Policy "{policy_title}" Will Expire Soon',
                'template': lambda policy_title, end_date: f'''
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                      <div style="background-color: #e74c3c; padding: 20px; text-align: center;">
                        <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Policy Expiry Notice</h1>
                      </div>
                      <div style="padding: 20px;">
                        <p style="color: #333333; font-size: 16px;">The policy <strong>{policy_title}</strong> will expire on <strong>{end_date}</strong>.</p>
                        <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                      </div>
                    </div>
                '''
            },
            'frameworkActivate': {
                'subject': 'Framework "{framework_title}" Will Be Activated Soon',
                'template': lambda framework_title, start_date: f'''
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                      <div style="background-color: #3498db; padding: 20px; text-align: center;">
                        <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Framework Activation Notice</h1>
                      </div>
                      <div style="padding: 20px;">
                        <p style="color: #333333; font-size: 16px;">The framework <strong>{framework_title}</strong> will be activated on <strong>{start_date}</strong>.</p>
                        <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                      </div>
                    </div>
                '''
            },
            'policyActivate': {
                'subject': 'Policy "{policy_title}" Will Be Activated Soon',
                'template': lambda policy_title, start_date: f'''
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                      <div style="background-color: #3498db; padding: 20px; text-align: center;">
                        <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Policy Activation Notice</h1>
                      </div>
                      <div style="padding: 20px;">
                        <p style="color: #333333; font-size: 16px;">The policy <strong>{policy_title}</strong> will be activated on <strong>{start_date}</strong>.</p>
                        <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                      </div>
                    </div>
                '''
            },
            'subpolicyApproved': {
                'subject': 'Subpolicy "{subpolicy_title}" Approved',
                'template': lambda submitter_name, subpolicy_title, reviewer_name, policy_title, framework_title: f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #2ecc71; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Subpolicy Approved</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {submitter_name},</p>
                    <p style="color: #333333; font-size: 16px;">Your subpolicy <strong>"{subpolicy_title}"</strong> under policy <strong>"{policy_title}"</strong> in framework <strong>"{framework_title}"</strong> was approved by {reviewer_name}.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                '''
            },
            'subpolicyRejected': {
                'subject': 'Subpolicy "{subpolicy_title}" Rejected',
                'template': lambda submitter_name, subpolicy_title, reviewer_name, policy_title, framework_title, rejection_reason: f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #e74c3c; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Subpolicy Rejected</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {submitter_name},</p>
                    <p style="color: #333333; font-size: 16px;">Your subpolicy <strong>"{subpolicy_title}"</strong> under policy <strong>"{policy_title}"</strong> in framework <strong>"{framework_title}"</strong> was rejected by {reviewer_name}.</p>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                      <p style="color: #333333; font-style: italic;">Reason: {rejection_reason}</p>
                    </div>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                '''
            },
            'subpolicyResubmitted': {
                'subject': 'Subpolicy "{subpolicy_title}" Resubmitted for Your Review',
                'template': lambda reviewer_name, subpolicy_title, submitter_name: f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #f39c12; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Subpolicy Resubmitted</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {reviewer_name},</p>
                    <p style="color: #333333; font-size: 16px;">The subpolicy <strong>"{subpolicy_title}"</strong> has been resubmitted for your review by {submitter_name}.</p>
                    <p style="color: #333333; font-size: 16px;">Please review the updated subpolicy at your earliest convenience.</p>
                  </div>
                </div>
                '''
            },
            'frameworkFinalApproved': {
                'subject': 'Framework "{framework_title}" Approved',
                'template': lambda submitter_name, framework_title, reviewer_name, approval_date: f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #2ecc71; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Framework Approved</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {submitter_name},</p>
                    <p style="color: #333333; font-size: 16px;">Your framework <strong>"{framework_title}"</strong> has been approved by {reviewer_name} on {approval_date} and is now active.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                '''
            },
            'frameworkRejected': {
                'subject': 'Framework "{framework_title}" Was Rejected',
                'template': lambda submitter_name, framework_title, reviewer_name, rejection_reason: f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #e74c3c; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Framework Rejected</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {submitter_name},</p>
                    <p style="color: #333333; font-size: 16px;">Your framework <strong>"{framework_title}"</strong> was rejected by {reviewer_name}.</p>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                      <p style="color: #333333; font-style: italic;">Reason: {rejection_reason}</p>
                    </div>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                '''
            },
            'policyResubmitted': {
                'subject': 'Policy "{policy_title}" Resubmitted for Your Review',
                'template': lambda reviewer_name, policy_title, submitter_name: f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #f39c12; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Policy Resubmitted</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {reviewer_name},</p>
                    <p style="color: #333333; font-size: 16px;">The policy <strong>"{policy_title}"</strong> has been resubmitted for your review by {submitter_name}.</p>
                    <p style="color: #333333; font-size: 16px;">Please review the updated policy at your earliest convenience.</p>
                      </div>
                    </div>
                '''
            },
            'frameworkVersionSubmitted': {
                'subject': 'Framework Version "{framework_title}" v{version} Submitted for Your Review',
                'template': lambda framework_title, reviewer_name, submitter_name, version: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #9b59b6; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">New Framework Version</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {reviewer_name},</p>
                    <p style="color: #333333; font-size: 16px;">{submitter_name} has created a new version (v{version}) of framework <strong>"{framework_title}"</strong> for your review.</p>
                    <p style="color: #333333; font-size: 16px;">Please review the changes and either approve or reject this version.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'frameworkInactiveRequested': {
                'subject': 'Framework "{framework_title}" Inactivation Requested',
                'template': lambda reviewer_name, framework_title, submitter_name, reason: f"""
                <div style=\"font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;\">
                  <div style=\"background-color: #f39c12; padding: 20px; text-align: center;\">
                    <h1 style=\"color: #ffffff; margin: 0; font-size: 28px;\">Framework Inactivation Request</h1>
                  </div>
                  <div style=\"padding: 20px;\">
                    <p style=\"color: #333333; font-size: 16px;\">Hello {reviewer_name},</p>
                    <p style=\"color: #333333; font-size: 16px;\">{submitter_name} has requested to inactivate the framework <strong>\"{framework_title}\"</strong>.</p>
                    <p style=\"color: #333333; font-size: 16px;\"><strong>Reason:</strong> {reason}</p>
                    <p style=\"color: #333333; font-size: 16px;\">Please review and approve or reject this request.</p>
                    <p style=\"color: #333333; margin-top: 20px;\">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'frameworkInactivationApproved': {
                'subject': 'Framework "{framework_title}" Inactivation Approved',
                'template': lambda submitter_name, framework_title, reviewer_name, remarks: f"""
                <div style=\"font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;\">
                  <div style=\"background-color: #2ecc71; padding: 20px; text-align: center;\">
                    <h1 style=\"color: #ffffff; margin: 0; font-size: 28px;\">Framework Inactivation Approved</h1>
                  </div>
                  <div style=\"padding: 20px;\">
                    <p style=\"color: #333333; font-size: 16px;\">Hello {submitter_name},</p>
                    <p style=\"color: #333333; font-size: 16px;\">Your request to inactivate the framework <strong>\"{framework_title}\"</strong> has been <strong>approved</strong> by {reviewer_name}.</p>
                    <p style=\"color: #333333; font-size: 16px;\"><strong>Remarks:</strong> {remarks}</p>
                    <p style=\"color: #333333; margin-top: 20px;\">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'frameworkInactivationRejected': {
                'subject': 'Framework "{framework_title}" Inactivation Rejected',
                'template': lambda submitter_name, framework_title, reviewer_name, remarks: f"""
                <div style=\"font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;\">
                  <div style=\"background-color: #e74c3c; padding: 20px; text-align: center;\">
                    <h1 style=\"color: #ffffff; margin: 0; font-size: 28px;\">Framework Inactivation Rejected</h1>
                  </div>
                  <div style=\"padding: 20px;\">
                    <p style=\"color: #333333; font-size: 16px;\">Hello {submitter_name},</p>
                    <p style=\"color: #333333; font-size: 16px;\">Your request to inactivate the framework <strong>\"{framework_title}\"</strong> has been <strong>rejected</strong> by {reviewer_name}.</p>
                    <p style=\"color: #333333; font-size: 16px;\"><strong>Remarks:</strong> {remarks}</p>
                    <p style=\"color: #333333; margin-top: 20px;\">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'policyVersionSubmitted': {
                'subject': 'Policy Version "{policy_title}" v{version} Submitted for Your Review',
                'template': lambda policy_title, reviewer_name, submitter_name, version: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #9b59b6; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">New Policy Version</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {reviewer_name},</p>
                    <p style="color: #333333; font-size: 16px;">{submitter_name} has created a new version (v{version}) of policy <strong>"{policy_title}"</strong> for your review.</p>
                    <p style="color: #333333; font-size: 16px;">Please review the changes and either approve or reject this version.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'policyAcknowledgementRequired': {
                'subject': 'Action Required: Acknowledge Policy "{policy_name}"',
                'template': lambda user_name, policy_name, policy_version, request_title, description, due_date, acknowledgement_link: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e0e0e0;">
                  <div style="background-color: #4CAF50; padding: 25px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">📋 Policy Acknowledgement Required</h1>
                  </div>
                  <div style="padding: 30px 20px;">
                    <p style="color: #333333; font-size: 16px; margin-bottom: 20px;">Hello <strong>{user_name}</strong>,</p>
                    
                    <p style="color: #333333; font-size: 16px; line-height: 1.6;">
                      You have been assigned to acknowledge the policy <strong>"{policy_name}"</strong> (Version: {policy_version}).
                    </p>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; border-left: 4px solid #4CAF50; margin: 25px 0;">
                      <h3 style="color: #333333; margin-top: 0; font-size: 18px;">Request Details:</h3>
                      <p style="color: #555555; margin: 10px 0;"><strong>Title:</strong> {request_title}</p>
                      <p style="color: #555555; margin: 10px 0;"><strong>Description:</strong> {description}</p>
                      {f'<p style="color: #d32f2f; margin: 10px 0;"><strong>Due Date:</strong> {due_date}</p>' if due_date and due_date != 'No due date' else ''}
                    </div>
                    
                    <p style="color: #333333; font-size: 16px; line-height: 1.6; margin: 25px 0;">
                      You can acknowledge this policy in three ways:
                    </p>
                    
                    <ol style="color: #555555; font-size: 15px; line-height: 1.8;">
                      <li><strong>Via Email Link:</strong> Click the button below to acknowledge directly</li>
                      <li><strong>Via Platform:</strong> Log in to the GRC platform and check your pending acknowledgements</li>
                      <li><strong>Via App Notification:</strong> Check your in-app notifications</li>
                    </ol>
                    
                    <div style="text-align: center; margin: 35px 0;">
                      <a href="{acknowledgement_link}" 
                         style="display: inline-block; background-color: #4CAF50; color: white; 
                                padding: 15px 40px; text-decoration: none; border-radius: 5px; 
                                font-size: 16px; font-weight: bold; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                        Acknowledge Policy
                      </a>
                    </div>
                    
                    <p style="color: #777777; font-size: 13px; line-height: 1.6; margin-top: 25px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
                      <strong>Note:</strong> This link allows you to acknowledge the policy without logging in. 
                      Please do not share this link with others as it is unique to your acknowledgement request.
                    </p>
                    
                    <p style="color: #333333; margin-top: 25px; font-size: 14px;">
                      Best regards,<br>
                      <strong>GRC Team</strong>
                    </p>
                  </div>
                  <div style="background-color: #f5f5f5; padding: 15px; text-align: center; font-size: 12px; color: #777777;">
                    <p style="margin: 0;">This is an automated notification from the GRC Policy Management System</p>
                  </div>
                </div>
                """
            },
            'eventCreated': {
                'subject': 'New Event Created: "{event_title}"',
                'template': lambda user_name, event_title, event_description, creator_name, event_category: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #3498db; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">New Event Created</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {user_name},</p>
                    <p style="color: #333333; font-size: 16px;">A new event <strong>"{event_title}"</strong> has been created by {creator_name}.</p>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                      <p style="color: #555555; margin: 5px 0;"><strong>Category:</strong> {event_category}</p>
                      <p style="color: #555555; margin: 5px 0;"><strong>Description:</strong> {event_description}</p>
                    </div>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'eventAssigned': {
                'subject': 'Event Assigned: "{event_title}"',
                'template': lambda user_name, event_title, event_description, assignor_name, event_category, due_date: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #9b59b6; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Event Assigned</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {user_name},</p>
                    <p style="color: #333333; font-size: 16px;">You have been assigned the event <strong>"{event_title}"</strong> by {assignor_name}.</p>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                      <p style="color: #555555; margin: 5px 0;"><strong>Category:</strong> {event_category}</p>
                      <p style="color: #555555; margin: 5px 0;"><strong>Description:</strong> {event_description}</p>
                      {f'<p style="color: #555555; margin: 5px 0;"><strong>Due Date:</strong> {due_date}</p>' if due_date else ''}
                    </div>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
            'eventStatusChanged': {
                'subject': 'Event Status Updated: "{event_title}"',
                'template': lambda user_name, event_title, old_status, new_status, actor_name: f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                  <div style="background-color: #f39c12; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Event Status Updated</h1>
                  </div>
                  <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {user_name},</p>
                    <p style="color: #333333; font-size: 16px;">The event <strong>"{event_title}"</strong> status has been changed from <strong>{old_status}</strong> to <strong>{new_status}</strong> by {actor_name}.</p>
                    <p style="color: #333333; margin-top: 20px;">– GRC Team</p>
                  </div>
                </div>
                """
            },
        }
        
        # WhatsApp templates
        self.whatsapp_templates = {
            'welcome': {
                'name': 'welcome_message',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['userName', 'teamName'],
                    },
                ],
            },
            'frameworkSubmitted': {
                'name': 'framework_submitted_for_review',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['reviewerName', 'frameworkTitle', 'submitterName'],
                    },
                ],
            },
            'passwordReset': {
                'name': 'password_reset',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['userName', 'resetLink'],
                    },
                ],
            },
            'accountUpdate': {
                'name': 'account_update',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['userName', 'updateDetails'],
                    },
                ],
            },
            'policySubmitted': {
                'name': 'policy_submitted_for_review',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['reviewerName', 'policyTitle', 'submitterName', 'dueDate'],
                    },
                ],
            },
            'policyApproved': {
                'name': 'policy_approved',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['submitterName', 'policyTitle', 'reviewerName', 'dateTime'],
                    },
                ],
            },
            'policyRejected': {
                'name': 'policy_rejected',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['submitterName', 'policyTitle', 'reviewerName', 'reviewerComment'],
                    },
                ],
            },
            'policyNewVersion': {
                'name': 'policy_new_version',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['reviewerName', 'policyTitle', 'version', 'creatorName'],
                    },
                ],
            },
            'policyStatusChange': {
                'name': 'policy_status_change',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['userName', 'policyTitle', 'status', 'actorName', 'dateTime'],
                    },
                ],
            },
            'complianceAssigned': {
                'name': 'compliance_assigned',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['officerName', 'itemTitle', 'assignorName', 'dueDate'],
                    },
                ],
            },
            'complianceDueReminder': {
                'name': 'compliance_due_reminder',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['officerName', 'itemTitle', 'dueDate'],
                    },
                ],
            },
            'complianceCompleted': {
                'name': 'compliance_completed',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['reviewerName', 'itemTitle', 'officerName', 'reviewDueDate'],
                    },
                ],
            },
            'complianceReviewed': {
                'name': 'compliance_reviewed',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['officerName', 'itemTitle', 'status', 'reviewerName', 'reviewerComment'],
                    },
                ],
            },
            'auditAssigned': {
                'name': 'audit_assigned',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['auditorName', 'auditTitle', 'scope', 'startDate'],
                    },
                ],
            },
            'auditStartReminder': {
                'name': 'audit_start_reminder',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['auditorName', 'auditTitle'],
                    },
                ],
            },
            'auditCompleted': {
                'name': 'audit_completed',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['reviewerName', 'auditTitle', 'auditorName', 'reviewDueDate'],
                    },
                ],
            },
            'auditReviewed': {
                'name': 'audit_reviewed',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['auditorName', 'auditTitle', 'status', 'reviewerName', 'reviewerComment'],
                    },
                ],
            },
            'riskIdentified': {
                'name': 'risk_identified',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['riskMgr', 'riskTitle', 'category', 'creatorName'],
                    },
                ],
            },
            'riskMitigationAssigned': {
                'name': 'risk_mitigation_assigned',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['mitigator', 'riskTitle', 'dueDate'],
                    },
                ],
            },
            'riskMitigationCompleted': {
                'name': 'risk_mitigation_completed',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['reviewerName', 'riskTitle', 'mitigator', 'reviewDueDate'],
                    },
                ],
            },
            'riskScoreUpdated': {
                'name': 'risk_score_updated',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['riskMgr', 'riskTitle', 'oldScore', 'newScore', 'actorName'],
                    },
                ],
            },
            'incidentEscalated': {
                'name': 'incident_escalated',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['managerName', 'incidentTitle', 'escalatorName'],
                    },
                ],
            },
            'incidentAssigned': {
                'name': 'incident_assigned',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['assigneeName', 'incidentTitle', 'dueDate'],
                    },
                ],
            },
            'incidentResolved': {
                'name': 'incident_resolved',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['incidentTitle', 'assigneeName', 'dateTime'],
                    },
                ],
            },
            'roleAssignmentChanged': {
                'name': 'role_assignment_changed',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['userName', 'newRole', 'adminName'],
                    },
                ],
            },
            'systemMaintenance': {
                'name': 'system_maintenance',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['date', 'startTime', 'endTime'],
                    },
                ],
            },
            'frameworkNewVersion': {
                'name': 'framework_new_version',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['reviewerName', 'frameworkTitle', 'version', 'creatorName'],
                    },
                ],
            },
            'policyNewVersion': {
                'name': 'policy_new_version',
                'components': [
                    {
                        'type': 'body',
                        'parameters': ['reviewerName', 'policyTitle', 'version', 'creatorName'],
                    },
                ],
            }
        }

    def send_email(self, to, email_type, notification_type, template_data):
        """Send email notification"""
        try:
            logger.info(f"Attempting to send email to {to} using {email_type} for {notification_type}")
            logger.info(f"Template data: {template_data}")
            
            # Get email config based on type
            config = self.email_configs.get(email_type.lower())
            if not config:
                error_msg = f"Unsupported email type: {email_type}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            logger.info(f"Using email config: {config['host']}:{config['port']}")
            
            # Get template
            template = self.email_templates.get(notification_type)
            if not template:
                error_msg = f"Unsupported notification type: {notification_type}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            logger.info(f"Found template for {notification_type}")
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = f"{self.default_from['name']} <{self.default_from['email']}>"
            msg['To'] = to
            
            # Format subject with template data if needed
            subject = template['subject']
            title_index = self.title_index_map.get(notification_type, 0)
            if '{policy_title}' in subject and len(template_data) > title_index:
                subject = subject.replace('{policy_title}', str(template_data[title_index]))
            if '{framework_title}' in subject and len(template_data) > title_index:
                subject = subject.replace('{framework_title}', str(template_data[title_index]))
            if '{subpolicy_title}' in subject and len(template_data) > title_index:
                subject = subject.replace('{subpolicy_title}', str(template_data[title_index]))
            if '{incident_title}' in subject and len(template_data) >= 2:
                subject = subject.replace('{incident_title}', template_data[1])
            # Add version replacement for templates that use it (index 3 in template_data)
            if '{version}' in subject and len(template_data) > 3:
                subject = subject.replace('{version}', str(template_data[3]))
            # Add policy_name replacement for acknowledgement template
            if '{policy_name}' in subject and len(template_data) > title_index:
                subject = subject.replace('{policy_name}', str(template_data[title_index]))
            # Add item_title replacement for compliance templates
            if '{item_title}' in subject and len(template_data) > title_index:
                subject = subject.replace('{item_title}', str(template_data[title_index]))
            # Add event_title replacement for event templates
            if '{event_title}' in subject and len(template_data) > title_index:
                subject = subject.replace('{event_title}', str(template_data[title_index]))
            
            msg['Subject'] = subject
            logger.info(f"Email subject: {subject}")
            
            # Apply template data to create HTML content
            html_content = template['template'](*template_data)
            msg.attach(MIMEText(html_content, 'html'))
            
            logger.info(f"Connecting to SMTP server {config['host']}:{config['port']}")
            
            # Check DNS resolution before attempting connection
            try:
                host_ip = socket.gethostbyname(config['host'])
                logger.info(f"DNS resolution successful: {config['host']} -> {host_ip}")
            except socket.gaierror as dns_error:
                error_msg = (
                    f"DNS resolution failed for {config['host']}. "
                    f"This usually means:\n"
                    f"1. DNS server is not configured properly\n"
                    f"2. Network connectivity issues\n"
                    f"3. Firewall blocking DNS queries\n"
                    f"4. Container/instance has no internet access\n\n"
                    f"Solutions:\n"
                    f"- For Docker: Add DNS servers in docker-compose.yml (dns: [8.8.8.8, 8.8.4.4])\n"
                    f"- For EC2: Check security groups and VPC DNS settings\n"
                    f"- Verify internet connectivity: ping 8.8.8.8\n"
                    f"- Check /etc/resolv.conf for DNS configuration"
                )
                logger.error(error_msg)
                logger.error(f"DNS error details: {str(dns_error)}")
                raise ConnectionError(error_msg) from dns_error
            
            # Connect to SMTP server and send email - handling Microsoft differently
            if email_type.lower() == 'microsoft':
                with smtplib.SMTP(config['host'], config['port']) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    username = config['auth']['user']
                    password = config['auth']['pass']
                    logger.info(f"Attempting Microsoft SMTP auth with username: {username}")
                    server.login(username, password)
                    server.send_message(msg)
                    logger.info(f"Microsoft email sent successfully to {to}")
            else:
                with smtplib.SMTP(config['host'], config['port']) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    username = config['auth']['user']
                    password = config['auth']['pass']
                    logger.info(f"Attempting SMTP auth with username: {username}")
                    try:
                        server.login(username, password)
                        logger.info("SMTP login successful")
                        server.send_message(msg)
                        logger.info(f"Email sent successfully to {to}")
                    except smtplib.SMTPAuthenticationError as auth_error:
                        logger.error(f"SMTP Authentication failed: {str(auth_error)}")
                        raise
                    except Exception as smtp_error:
                        logger.error(f"SMTP error: {str(smtp_error)}")
                        raise
            
            # Log notification in database
            self.log_notification(to, notification_type, 'email', True)
            
            return {"success": True, "to": to, "type": notification_type}
            
        except Exception as e:
            error_msg = f"Error sending email: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Full error details: {traceback.format_exc()}")
            # Log failed notification
            self.log_notification(to, notification_type, 'email', False, str(e))
            return {"success": False, "error": str(e)}
    
    def send_whatsapp(self, to, notification_type, template_parameters):
        """Send WhatsApp notification"""
        try:
            # Get template
            template = self.whatsapp_templates.get(notification_type)
            if not template:
                raise ValueError(f"Unsupported WhatsApp template: {notification_type}")
            
            # Create WhatsApp API client
            url = f"https://graph.facebook.com/{self.whatsapp_config['api_version']}/{self.whatsapp_config['phone_number_id']}/messages"
            headers = {
                'Authorization': f"Bearer {self.whatsapp_config['access_token']}",
                'Content-Type': 'application/json'
            }
            
            # Prepare message payload
            payload = {
                'messaging_product': 'whatsapp',
                'to': to,
                'type': 'template',
                'template': {
                    'name': template['name'],
                    'language': {'code': self.whatsapp_config['default_language']},
                    'components': [
                        {
                            'type': comp['type'],
                            'parameters': [
                                {'type': 'text', 'text': template_parameters[i]}
                                for i, param in enumerate(comp['parameters'])
                            ]
                        } for comp in template['components']
                    ]
                }
            }
            
            # Send message
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            
            response_data = response.json()
            message_id = response_data.get('messages', [{}])[0].get('id', 'unknown')
            
            logger.info(f"WhatsApp message sent successfully to {to}, type: {notification_type}, id: {message_id}")
            
            # Log notification in database
            self.log_notification(to, notification_type, 'whatsapp', True)
            
            return {"success": True, "to": to, "type": notification_type, "messageId": message_id}
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            # Log failed notification
            self.log_notification(to, notification_type, 'whatsapp', False, str(e))
            return {"success": False, "error": str(e)}
    
    def log_notification(self, recipient, notification_type, channel, success, error=None):
        """Log notification in database"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            query = """
            INSERT INTO notifications 
            (recipient, type, channel, success, error, created_at) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            values = (
                recipient, 
                notification_type, 
                channel, 
                success, 
                error, 
                datetime.now()
            )
            
            cursor.execute(query, values)
            conn.commit()
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error logging notification: {str(e)}")
    
    def get_user_email_by_id(self, user_id):
        """
        Convenience wrapper used by various modules (e.g. Compliance) to fetch a user's
        email and display name in one call.
        """
        try:
            email = self.get_user_email(user_id)
            name = self.get_user_name(user_id)
            return email, name
        except Exception as e:
            logger.error(f"Error in get_user_email_by_id for {user_id}: {str(e)}")
            return None, None

    def send_compliance_clone_notification(self, compliance, reviewer_id):
        """
        Send an email to the reviewer when a compliance item is created/cloned
        and assigned for review.
        """
        try:
            reviewer_email, reviewer_name = self.get_user_email_by_id(reviewer_id)
            if not reviewer_email:
                return {"success": False, "error": f"No email found for reviewer_id={reviewer_id}"}

            # Use ComplianceTitle if available, otherwise fall back to ComplianceItemDescription or ID
            item_title = getattr(compliance, "ComplianceTitle", None) or compliance.ComplianceItemDescription or f"Compliance {compliance.ComplianceId}"
            assignor_name = getattr(compliance, "CreatedByName", None) or "System"
            # Approval due date is optional; fall back to 'Not specified'
            due_date = getattr(compliance, "ApprovalDueDate", None)
            due_date_str = due_date.strftime("%Y-%m-%d") if due_date else "Not specified"

            notification_data = {
                "notification_type": "complianceAssigned",
                "email": reviewer_email,
                "email_type": "gmail",
                "template_data": [
                    reviewer_name or reviewer_email.split("@")[0],
                    item_title,
                    assignor_name,
                    due_date_str,
                ],
            }
            return self.send_multi_channel_notification(notification_data)
        except Exception as e:
            logger.error(f"Error in send_compliance_clone_notification: {str(e)}")
            return {"success": False, "error": str(e)}

    def send_compliance_review_notification(self, compliance, reviewer_decision, creator_id, remarks=None):
        """
        Send an email to the compliance creator when a reviewer approves/rejects.
        """
        try:
            creator_email, creator_name = self.get_user_email_by_id(creator_id)
            if not creator_email:
                return {"success": False, "error": f"No email found for creator_id={creator_id}"}

            status = "Approved" if reviewer_decision is True else ("Rejected" if reviewer_decision is False else "Updated")
            # Use ComplianceTitle if available, otherwise fall back to ComplianceItemDescription or ID
            item_title = getattr(compliance, "ComplianceTitle", None) or compliance.ComplianceItemDescription or f"Compliance {compliance.ComplianceId}"
            # Best-effort reviewer name; if not available, use generic label
            reviewer_name = "Reviewer"

            notification_data = {
                "notification_type": "complianceReviewed",
                "email": creator_email,
                "email_type": "gmail",
                "template_data": [
                    creator_name or creator_email.split("@")[0],
                    item_title,
                    status,
                    reviewer_name,
                    remarks or "",
                ],
            }
            return self.send_multi_channel_notification(notification_data)
        except Exception as e:
            logger.error(f"Error in send_compliance_review_notification: {str(e)}")
            return {"success": False, "error": str(e)}

    def send_export_completion_notification(self, user_id, export_details):
        """
        Send an email when an export task has completed.
        """
        try:
            user_email, user_name = self.get_user_email_by_id(user_id)
            if not user_email:
                return {"success": False, "error": f"No email found for user_id={user_id}"}

            file_name = export_details.get("file_name") or f"Export-{export_details.get('id')}"
            file_type = export_details.get("file_type", "file")
            s3_url = export_details.get("s3_url")
            completed_at = export_details.get("completed_at")

            notification_data = {
                "notification_type": "exportCompleted",
                "email": user_email,
                "email_type": "gmail",
                "template_data": [
                    user_name or user_email.split("@")[0],
                    file_name,
                    file_type,
                    s3_url,
                    completed_at,
                ],
            }
            return self.send_multi_channel_notification(notification_data)
        except Exception as e:
            logger.error(f"Error in send_export_completion_notification: {str(e)}")
            return {"success": False, "error": str(e)}

    def send_multi_channel_notification(self, notification_data):
        """Send notification through multiple channels"""
        results = {
            "email": None,
            "whatsapp": None,
            "errors": []
        }
        
        notification_type = notification_data.get('notification_type')
        if not notification_type:
            return {"success": False, "error": "Missing notification_type"}
        
        # Send email if email details provided
        if notification_data.get('email') and notification_data.get('email_type'):
            try:
                email_result = self.send_email(
                    notification_data['email'],
                    notification_data['email_type'],
                    notification_type,
                    notification_data.get('template_data', [])
                )
                
                if email_result.get('success'):
                    results['email'] = {
                        'to': notification_data['email'],
                        'type': notification_data['email_type']
                    }
                else:
                    results['errors'].append({
                        'channel': 'email',
                        'error': email_result.get('error')
                    })
            except Exception as e:
                results['errors'].append({
                    'channel': 'email',
                    'error': str(e)
                })
        
        # Send WhatsApp if number provided
        if notification_data.get('whatsapp_number'):
            try:
                whatsapp_result = self.send_whatsapp(
                    notification_data['whatsapp_number'],
                    notification_type,
                    notification_data.get('template_data', [])
                )
                
                if whatsapp_result.get('success'):
                    results['whatsapp'] = {
                        'to': notification_data['whatsapp_number'],
                        'messageId': whatsapp_result.get('messageId')
                    }
                else:
                    results['errors'].append({
                        'channel': 'whatsapp',
                        'error': whatsapp_result.get('error')
                    })
            except Exception as e:
                results['errors'].append({
                    'channel': 'whatsapp',
                    'error': str(e)
                })
        
        # If both channels failed
        if len(results['errors']) == 2:
            return {
                "success": False,
                "error": "Failed to send notifications to all channels",
                "details": results['errors']
            }
        
        # Return success with results
        return {
            "success": True,
            "message": "Notifications sent successfully",
            "details": {
                "email": results['email'],
                "whatsapp": results['whatsapp'],
                "errors": results['errors'] if results['errors'] else None
            }
        }
    
    # 
    
# Example usage
if __name__ == "__main__":
    # Initialize notification service
    notification_service = NotificationService()
    
    # # Create database tables
    # try:
    #     notification_service.create_database_tables()
    # except Exception as e:
    #     logger.error(f"Failed to create database tables: {str(e)}")
    
    # Example 1: Welcome email
    welcome_data = {
        'notification_type': 'welcome',
        'email': 'syammuni916@gmail.com',
        'email_type': 'gmail',
        'template_data': ['Muni syam putthuru', 'GRC']
    }
    
    # Example 2: Policy submitted notification (both email and WhatsApp)
    policy_data = {
        'notification_type': 'policySubmitted',
        'email': 'syammuni916@gmail.com',
        'email_type': 'gmail',
        # 'whatsapp_number': '1234567890',
        'template_data': ['Jane Smith', 'Data Privacy Policy', 'John Doe', '2023-08-15']
    }
    
    # Example 3: Incident assigned notification
    incident_data = {
        'notification_type': 'incidentAssigned',
        'email': 'security@example.com',
        'email_type': 'gmail',
        'whatsapp_number': '9876543210',
        'template_data': ['Security Team', 'Data Breach Investigation', '2023-08-10']
    }
    
    # Send notifications using multi-channel method
    # print("Sending welcome notification...")
    # result1 = notification_service.send_multi_channel_notification(welcome_data)
    # print(f"Result: {result1}")
    
    print("\nSending policy notification...")
    result2 = notification_service.send_multi_channel_notification(policy_data)
    print(f"Result: {result2}")
    
    # print("\nSending incident notification...")
    # result3 = notification_service.send_multi_channel_notification(policy_data)
    # print(f"Result: {result3}")