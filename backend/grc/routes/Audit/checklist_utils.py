from django.db import connection
from django.utils import timezone
import logging
from ...routes.Global.notification_service import NotificationService
from ...routes.Global.logging_service import send_log
from datetime import timedelta
from django.db import connection
from datetime import datetime
from django.utils import timezone
from...rbac.decorators import audit_conduct_required

logger = logging.getLogger(__name__)

def check_audit_findings(audit_id):
    """
    Check what audit findings exist for a specific audit ID
    """
    print(f"DEBUG: ==========================================")
    print(f"DEBUG: Checking audit findings for audit_id: {audit_id}")
    print(f"DEBUG: ==========================================")
    
    try:
        with connection.cursor() as cursor:
            # Check if audit exists
            cursor.execute("SELECT COUNT(*) FROM audit WHERE AuditId = %s", [audit_id])
            audit_exists = cursor.fetchone()[0] > 0
            print(f"DEBUG: Audit exists: {audit_exists}")
            
            if not audit_exists:
                print(f"DEBUG: Audit {audit_id} does not exist!")
                return False
            
            # Get audit findings count
            cursor.execute("SELECT COUNT(*) FROM audit_findings WHERE AuditId = %s", [audit_id])
            findings_count = cursor.fetchone()[0]
            print(f"DEBUG: Found {findings_count} audit findings")
            
            if findings_count == 0:
                print(f"DEBUG: No audit findings found for audit {audit_id}")
                return False
            
            # Get detailed audit findings
            cursor.execute("""
                SELECT 
                    af.AuditFindingsId,
                    af.ComplianceId,
                    af.UserId,
                    af.`Check`,
                    af.Comments,
                    c.SubPolicyId,
                    sp.PolicyId,
                    p.FrameworkId
                FROM 
                    audit_findings af
                JOIN 
                    compliance c ON af.ComplianceId = c.ComplianceId
                JOIN 
                    subpolicies sp ON c.SubPolicyId = sp.SubPolicyId
                JOIN 
                    policies p ON sp.PolicyId = p.PolicyId
                WHERE 
                    af.AuditId = %s
            """, [audit_id])
            
            findings = cursor.fetchall()
            print(f"DEBUG: Detailed findings:")
            for i, finding in enumerate(findings):
                audit_findings_id, compliance_id, user_id, check_value, comments, subpolicy_id, policy_id, framework_id = finding
                print(f"DEBUG:   Finding {i+1}:")
                print(f"DEBUG:     AuditFindingsId: {audit_findings_id}")
                print(f"DEBUG:     ComplianceId: {compliance_id}")
                print(f"DEBUG:     UserId: {user_id}")
                print(f"DEBUG:     Check: '{check_value}'")
                print(f"DEBUG:     Comments: {comments}")
                print(f"DEBUG:     SubPolicyId: {subpolicy_id}")
                print(f"DEBUG:     PolicyId: {policy_id}")
                print(f"DEBUG:     FrameworkId: {framework_id}")
            
            return True
            
    except Exception as e:
        print(f"DEBUG: Error checking audit findings: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_update_function(audit_id):
    """
    Test function to call update_lastchecklistitem_verified with a specific audit ID
    """
    print(f"DEBUG: ==========================================")
    print(f"DEBUG: TESTING update_lastchecklistitem_verified with audit_id: {audit_id}")
    print(f"DEBUG: ==========================================")
    
    try:
        result = update_lastchecklistitem_verified(audit_id)
        print(f"DEBUG: Test result: {result}")
        return result
    except Exception as e:
        print(f"DEBUG: Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_insert_record():
    """
    Test inserting a simple record into lastchecklistitemverified table
    """
    print(f"DEBUG: ==========================================")
    print(f"DEBUG: Testing manual insert into lastchecklistitemverified...")
    print(f"DEBUG: ==========================================")
    
    try:
        with connection.cursor() as cursor:
            # Test data
            test_compliance_id = 999999  # Use a high number to avoid conflicts
            test_subpolicy_id = 1
            test_policy_id = 1
            test_framework_id = 1
            test_date = timezone.now().date()
            test_time = timezone.now().time()
            test_user = 1
            test_complied = "1"
            test_comments = "Test record"
            test_count = 1
            test_audit_findings_id = 999999
            
            print(f"DEBUG: Attempting to insert test record...")
            print(f"DEBUG: ComplianceId: {test_compliance_id}")
            
            # First check if record exists
            cursor.execute("SELECT COUNT(*) FROM lastchecklistitemverified WHERE ComplianceId = %s", [test_compliance_id])
            exists = cursor.fetchone()[0] > 0
            print(f"DEBUG: Record exists: {exists}")
            
            if exists:
                # Update existing record
                cursor.execute("""
                    UPDATE lastchecklistitemverified
                    SET SubPolicyId = %s, PolicyId = %s, FrameworkId = %s, Date = %s, Time = %s,
                        User = %s, Complied = %s, Comments = %s, Count = %s, AuditFindingsId = %s
                    WHERE ComplianceId = %s
                """, [
                    test_subpolicy_id, test_policy_id, test_framework_id, test_date, test_time,
                    test_user, test_complied, test_comments, test_count, test_audit_findings_id,
                    test_compliance_id
                ])
                print(f"DEBUG: Updated test record")
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO lastchecklistitemverified (
                        ComplianceId, SubPolicyId, PolicyId, FrameworkId, Date, Time,
                        User, Complied, Comments, Count, AuditFindingsId
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    test_compliance_id, test_subpolicy_id, test_policy_id, test_framework_id,
                    test_date, test_time, test_user, test_complied, test_comments, test_count,
                    test_audit_findings_id
                ])
                print(f"DEBUG: Inserted test record")
            
            # Verify the record
            cursor.execute("SELECT * FROM lastchecklistitemverified WHERE ComplianceId = %s", [test_compliance_id])
            record = cursor.fetchone()
            print(f"DEBUG: Verification - Record: {record}")
            
            return True
            
    except Exception as e:
        print(f"DEBUG: Error in test insert: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_table_structure():
    """
    Check the actual structure of the lastchecklistitemverified table
    """
    print(f"DEBUG: ==========================================")
    print(f"DEBUG: Checking lastchecklistitemverified table structure...")
    print(f"DEBUG: ==========================================")
    
    try:
        with connection.cursor() as cursor:
            # Get table structure
            cursor.execute("DESCRIBE lastchecklistitemverified")
            columns = cursor.fetchall()
            print(f"DEBUG: Table structure:")
            for col in columns:
                print(f"DEBUG:   Column: {col[0]}, Type: {col[1]}, Null: {col[2]}, Key: {col[3]}, Default: {col[4]}, Extra: {col[5]}")
            
            # Check if table has any data
            cursor.execute("SELECT COUNT(*) FROM lastchecklistitemverified")
            row_count = cursor.fetchone()[0]
            print(f"DEBUG: Current row count: {row_count}")
            
            if row_count > 0:
                # Show sample data
                cursor.execute("SELECT * FROM lastchecklistitemverified LIMIT 3")
                sample_data = cursor.fetchall()
                print(f"DEBUG: Sample data:")
                for row in sample_data:
                    print(f"DEBUG:   {row}")
            
            return True
    except Exception as e:
        print(f"DEBUG: Error checking table structure: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    """
    Test database connection and table structure
    """
    print(f"DEBUG: ==========================================")
    print(f"DEBUG: Testing database connection...")
    print(f"DEBUG: ==========================================")
    
    try:
        with connection.cursor() as cursor:
            # Test basic connection
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"DEBUG: Database connection test: {result}")
            
            # Check if lastchecklistitemverified table exists
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = 'lastchecklistitemverified'
            """)
            table_exists = cursor.fetchone()[0] > 0
            print(f"DEBUG: lastchecklistitemverified table exists: {table_exists}")
            
            if table_exists:
                # Get table structure
                cursor.execute("DESCRIBE lastchecklistitemverified")
                columns = cursor.fetchall()
                print(f"DEBUG: Table structure:")
                for col in columns:
                    print(f"DEBUG:   {col}")
                
                # Check if table has any data
                cursor.execute("SELECT COUNT(*) FROM lastchecklistitemverified")
                row_count = cursor.fetchone()[0]
                print(f"DEBUG: Current row count: {row_count}")
                
                if row_count > 0:
                    # Show sample data
                    cursor.execute("SELECT * FROM lastchecklistitemverified LIMIT 3")
                    sample_data = cursor.fetchall()
                    print(f"DEBUG: Sample data:")
                    for row in sample_data:
                        print(f"DEBUG:   {row}")
            
            return True
    except Exception as e:
        print(f"DEBUG: Database connection test failed: {str(e)}")
        return False

def update_lastchecklistitem_verified(audit_id):
    """
    Update the last checklist item verified timestamp for an audit
    """
    print(f"DEBUG: ==========================================")
    print(f"DEBUG: Starting update_lastchecklistitem_verified for audit_id: {audit_id}")
    print(f"DEBUG: ==========================================")
    
    # First test database connection
    if not test_database_connection():
        print(f"ERROR: Database connection test failed")
        return False
    
    # Check table structure
    if not check_table_structure():
        print(f"ERROR: Table structure check failed")
        return False
    
    # Test basic insert operation
    if not test_insert_record():
        print(f"ERROR: Test insert failed")
        return False
    
    try:
        # Log the start of the update process
        send_log(
            module="Checklist",
            actionType="UPDATE_CHECKLIST_START",
            description=f"Starting update of lastchecklistitemverified for audit ID {audit_id}",
            entityType="Audit",
            entityId=str(audit_id)
        )
        
        current_datetime = timezone.now()
        current_date = current_datetime.date()
        current_time = current_datetime.time()
        
        print(f"DEBUG: Current datetime: {current_datetime}")
        print(f"DEBUG: Current date: {current_date}")
        print(f"DEBUG: Current time: {current_time}")

        with connection.cursor() as cursor:
            # Get audit and user details for notification
            print(f"DEBUG: Fetching audit and user details...")
            cursor.execute("""
                SELECT 
                    a.assignee,
                    a.auditor,
                    a.reviewer,
                    u_assignee.Email as assignee_email,
                    u_auditor.Email as auditor_email,
                    u_reviewer.Email as reviewer_email,
                    u_assignee.UserName as assignee_name,
                    u_auditor.UserName as auditor_name,
                    u_reviewer.UserName as reviewer_name
                FROM 
                    audit a
                LEFT JOIN users u_assignee ON a.assignee = u_assignee.UserId
                LEFT JOIN users u_auditor ON a.auditor = u_auditor.UserId
                LEFT JOIN users u_reviewer ON a.reviewer = u_reviewer.UserId
                WHERE 
                    a.AuditId = %s
            """, [audit_id])
            
            user_row = cursor.fetchone()
            print(f"DEBUG: User row fetched: {user_row}")
            
            if user_row:
                assignee_id, auditor_id, reviewer_id, assignee_email, auditor_email, reviewer_email, assignee_name, auditor_name, reviewer_name = user_row
                
                print(f"DEBUG: Assignee ID: {assignee_id}, Auditor ID: {auditor_id}, Reviewer ID: {reviewer_id}")
                print(f"DEBUG: Assignee Email: {assignee_email}, Auditor Email: {auditor_email}")
                
                # Log user details retrieved
                send_log(
                    module="Checklist",
                    actionType="AUDIT_USERS_RETRIEVED",
                    description=f"Retrieved user details for audit ID {audit_id}",
                    userId=auditor_id,  # Use auditor as the actor
                    entityType="Audit",
                    entityId=str(audit_id),
                    additionalInfo={
                        "assignee_id": assignee_id,
                        "auditor_id": auditor_id,
                        "reviewer_id": reviewer_id
                    }
                )
            
            # First get all the audit findings for this audit
            print(f"DEBUG: Fetching audit findings for audit_id: {audit_id}")
            cursor.execute("""
                SELECT 
                    af.AuditFindingsId,
                    af.ComplianceId,
                    af.UserId,
                    af.`Check`,
                    af.Comments,
                    c.SubPolicyId,
                    sp.PolicyId,
                    p.FrameworkId
                FROM 
                    audit_findings af
                JOIN 
                    compliance c ON af.ComplianceId = c.ComplianceId
                JOIN 
                    subpolicies sp ON c.SubPolicyId = sp.SubPolicyId
                JOIN 
                    policies p ON sp.PolicyId = p.PolicyId
                WHERE 
                    af.AuditId = %s
            """, [audit_id])
            
            findings = cursor.fetchall()
            print(f"DEBUG: Found {len(findings)} audit findings")
            
            # Log findings retrieved
            send_log(
                module="Checklist",
                actionType="FINDINGS_RETRIEVED",
                description=f"Retrieved {len(findings)} findings for audit ID {audit_id}",
                entityType="Audit",
                entityId=str(audit_id),
                additionalInfo={"finding_count": len(findings)}
            )
            
            # Count non-compliant findings
            non_compliant_count = 0
            compliant_count = 0
            updated_records = 0
            inserted_records = 0
            
            print(f"DEBUG: Processing {len(findings)} findings...")
            
            for i, finding in enumerate(findings):
                audit_findings_id, compliance_id, user_id, check_value, comments, subpolicy_id, policy_id, framework_id = finding
                
                print(f"DEBUG: Processing finding {i+1}/{len(findings)}:")
                print(f"DEBUG:   AuditFindingsId: {audit_findings_id}")
                print(f"DEBUG:   ComplianceId: {compliance_id}")
                print(f"DEBUG:   UserId: {user_id}")
                print(f"DEBUG:   Check value: '{check_value}'")
                print(f"DEBUG:   Comments: {comments}")
                print(f"DEBUG:   SubPolicyId: {subpolicy_id}")
                print(f"DEBUG:   PolicyId: {policy_id}")
                print(f"DEBUG:   FrameworkId: {framework_id}")
                
                # Count non-compliant findings
                if check_value == "0":
                    non_compliant_count += 1
                    print(f"DEBUG:   -> Non-compliant finding")
                elif check_value == "1":
                    compliant_count += 1
                    print(f"DEBUG:   -> Compliant finding")
                else:
                    print(f"DEBUG:   -> Other status: {check_value}")
                
                # Check if a record already exists for this compliance
                print(f"DEBUG:   Checking if record exists for ComplianceId: {compliance_id}")
                cursor.execute("""
                    SELECT COUNT(*), Count 
                    FROM lastchecklistitemverified 
                    WHERE ComplianceId = %s
                """, [compliance_id])
                
                result = cursor.fetchone()
                exists = result[0] > 0
                current_count = result[1] if exists else 0
                
                print(f"DEBUG:   Record exists: {exists}")
                print(f"DEBUG:   Current count: {current_count}")
                
                # Increment count if check value is "0" or "1"
                new_count = current_count
                if check_value in ["0", "1"]:
                    new_count = current_count + 1
                    print(f"DEBUG:   Incrementing count to: {new_count}")
                
                try:
                    if exists:
                        # Update existing record
                        print(f"DEBUG:   Updating existing record...")
                        update_query = """
                            UPDATE lastchecklistitemverified
                            SET 
                                SubPolicyId = %s,
                                PolicyId = %s,
                                FrameworkId = %s,
                                Date = %s,
                                Time = %s,
                                User = %s,
                                Complied = %s,
                                Comments = %s,
                                Count = %s,
                                AuditFindingsId = %s
                            WHERE ComplianceId = %s
                        """
                        update_values = [
                            subpolicy_id,
                            policy_id,
                            framework_id,
                            current_date,
                            current_time,
                            user_id,
                            check_value,
                            comments,
                            new_count,
                            audit_findings_id,
                            compliance_id
                        ]
                        
                        print(f"DEBUG:   Update query: {update_query}")
                        print(f"DEBUG:   Update values: {update_values}")
                        
                        cursor.execute(update_query, update_values)
                        rows_affected = cursor.rowcount
                        print(f"DEBUG:   -> Rows affected by update: {rows_affected}")
                        updated_records += 1
                        print(f"DEBUG:   -> Record updated successfully")
                        
                        # Log record update
                        if check_value in ["0", "1"]:
                            send_log(
                                module="Checklist",
                                actionType="CHECKLIST_RECORD_UPDATED",
                                description=f"Updated checklist record for compliance ID {compliance_id}",
                                userId=user_id,
                                entityType="Compliance",
                                entityId=str(compliance_id),
                                additionalInfo={
                                    "audit_id": audit_id,
                                    "complied": check_value,
                                    "count": new_count
                                }
                            )
                    else:
                        # Insert new record
                        print(f"DEBUG:   Inserting new record...")
                        insert_query = """
                            INSERT INTO lastchecklistitemverified (
                                ComplianceId,
                                SubPolicyId,
                                PolicyId,
                                FrameworkId,
                                Date,
                                Time,
                                User,
                                Complied,
                                Comments,
                                Count,
                                AuditFindingsId
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        insert_values = [
                            compliance_id,
                            subpolicy_id,
                            policy_id,
                            framework_id,
                            current_date,
                            current_time,
                            user_id,
                            check_value,
                            comments,
                            new_count,
                            audit_findings_id
                        ]
                        
                        print(f"DEBUG:   Insert query: {insert_query}")
                        print(f"DEBUG:   Insert values: {insert_values}")
                        
                        cursor.execute(insert_query, insert_values)
                        rows_affected = cursor.rowcount
                        print(f"DEBUG:   -> Rows affected by insert: {rows_affected}")
                        inserted_records += 1
                        print(f"DEBUG:   -> Record inserted successfully")
                        
                        # Log record insertion
                        if check_value in ["0", "1"]:
                            send_log(
                                module="Checklist",
                                actionType="CHECKLIST_RECORD_INSERTED",
                                description=f"Inserted new checklist record for compliance ID {compliance_id}",
                                userId=user_id,
                                entityType="Compliance",
                                entityId=str(compliance_id),
                                additionalInfo={
                                    "audit_id": audit_id,
                                    "complied": check_value,
                                    "count": new_count
                                }
                            )
                    
                    # Print record if check value is "0" or "1"
                    if check_value in ["0", "1"]:
                        cursor.execute("""
                            SELECT * FROM lastchecklistitemverified
                            WHERE ComplianceId = %s
                        """, [compliance_id])
                        record = cursor.fetchone()
                        print(f"DEBUG:   Final record for ComplianceId {compliance_id}: {record}")
                        
                except Exception as e:
                    print(f"DEBUG:   ERROR processing finding {i+1}: {str(e)}")
                    print(f"DEBUG:   ComplianceId: {compliance_id}")
                    print(f"DEBUG:   Check value: {check_value}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            print(f"DEBUG: ==========================================")
            print(f"DEBUG: Summary:")
            print(f"DEBUG:   Updated records: {updated_records}")
            print(f"DEBUG:   Inserted records: {inserted_records}")
            print(f"DEBUG:   Compliant count: {compliant_count}")
            print(f"DEBUG:   Non-compliant count: {non_compliant_count}")
            print(f"DEBUG: ==========================================")
            
            # Log summary of updates
            send_log(
                module="Checklist",
                actionType="CHECKLIST_UPDATE_SUMMARY",
                description=f"Completed checklist updates for audit ID {audit_id}",
                entityType="Audit",
                entityId=str(audit_id),
                additionalInfo={
                    "updated_records": updated_records,
                    "inserted_records": inserted_records,
                    "compliant_count": compliant_count,
                    "non_compliant_count": non_compliant_count
                }
            )
            
            # Send notification about audit completion with findings summary
            try:
                if assignee_email and auditor_email:
                    notification_service = NotificationService()
                    
                    # Notify assignee about audit completion
                    notification_data = {
                        'notification_type': 'auditCompleted',
                        'email': assignee_email,
                        'email_type': 'gmail',
                        'template_data': [
                            reviewer_name or "Reviewer",
                            f"Audit #{audit_id}",
                            auditor_name or "Auditor",
                            (current_datetime + timedelta(days=7)).strftime('%Y-%m-%d')
                        ]
                    }
                    notification_service.send_multi_channel_notification(notification_data)
                    
                    # Log notification sent
                    send_log(
                        module="Checklist",
                        actionType="NOTIFICATION_SENT",
                        description=f"Sent audit completion notification to assignee for audit ID {audit_id}",
                        entityType="Notification",
                        entityId=str(audit_id),
                        additionalInfo={"recipient": assignee_email}
                    )
                    
                    # Notify management if there are non-compliant findings
                    if non_compliant_count > 0:
                        # Get management emails (you can customize this logic)
                        cursor.execute("""
                            SELECT Email FROM users WHERE Role = 'Manager' OR Role = 'Admin'
                        """)
                        
                        managers = cursor.fetchall()
                        for manager in managers:
                            manager_email = manager[0]
                            notification_data = {
                                'notification_type': 'auditNonCompliance',
                                'email': manager_email,
                                'email_type': 'gmail',
                                'template_data': [
                                    "Manager",
                                    f"Audit #{audit_id}",
                                    str(non_compliant_count),
                                    auditor_name or "Auditor"
                                ]
                            }
                            notification_service.send_multi_channel_notification(notification_data)
                            
                            # Log management notification
                            send_log(
                                module="Checklist",
                                actionType="MANAGEMENT_NOTIFICATION_SENT",
                                description=f"Sent non-compliance notification to management for audit ID {audit_id}",
                                entityType="Notification",
                                entityId=str(audit_id),
                                additionalInfo={
                                    "recipient": manager_email,
                                    "non_compliant_count": non_compliant_count
                                }
                            )
            except Exception as e:
                logger.error(f"Failed to send notification: {str(e)}")
                send_log(
                    module="Checklist",
                    actionType="NOTIFICATION_ERROR",
                    description=f"Failed to send notifications: {str(e)}",
                    entityType="Notification",
                    entityId=str(audit_id),
                    logLevel="ERROR",
                    additionalInfo={"error": str(e)}
                )
        
        # Log successful completion
        send_log(
            module="Checklist",
            actionType="UPDATE_CHECKLIST_COMPLETE",
            description=f"Successfully updated lastchecklistitemverified for audit ID {audit_id}",
            entityType="Audit",
            entityId=str(audit_id)
        )
        
        print(f"DEBUG: ==========================================")
        print(f"DEBUG: SUCCESS: update_lastchecklistitem_verified completed for audit_id: {audit_id}")
        print(f"DEBUG: ==========================================")
        
        return True
    except Exception as e:
        logger.error(f"Error in update_lastchecklistitem_verified: {str(e)}")
        print(f"ERROR: Failed to update lastchecklistitemverified table: {str(e)}")
        print(f"DEBUG: ==========================================")
        print(f"DEBUG: ERROR: update_lastchecklistitem_verified failed for audit_id: {audit_id}")
        print(f"DEBUG: Error details: {str(e)}")
        print(f"DEBUG: ==========================================")
        
        # Log error
        send_log(
            module="Checklist",
            actionType="UPDATE_CHECKLIST_ERROR",
            description=f"Error updating lastchecklistitemverified: {str(e)}",
            entityType="Audit",
            entityId=str(audit_id) if 'audit_id' in locals() else None,
            logLevel="ERROR",
            additionalInfo={"error": str(e)}
        )
        
        return False 