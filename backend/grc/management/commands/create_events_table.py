from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Create the events table in the database'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Create events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    EventId INT AUTO_INCREMENT PRIMARY KEY,
                    EventTitle VARCHAR(255) NOT NULL,
                    EventId_Generated VARCHAR(50) UNIQUE NOT NULL,
                    Description TEXT,
                    
                    -- Framework and Module Information
                    FrameworkId INT,
                    FrameworkName VARCHAR(255),
                    Module VARCHAR(255),
                    
                    -- Linked Records
                    LinkedRecordType VARCHAR(50),
                    LinkedRecordId INT,
                    LinkedRecordName VARCHAR(255),
                    
                    -- Event Details
                    Category VARCHAR(100),
                    OwnerId INT,
                    ReviewerId INT,
                    
                    -- Recurrence Information
                    RecurrenceType VARCHAR(20) DEFAULT 'Non-Recurring',
                    Frequency VARCHAR(50),
                    StartDate DATE,
                    EndDate DATE,
                    
                    -- Status and Dates
                    Status VARCHAR(50) DEFAULT 'Draft',
                    
                    -- Evidence and Attachments
                    Evidence JSON,
                    Attachments JSON,
                    
                    -- Metadata
                    CreatedById INT,
                    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    SubmittedAt TIMESTAMP NULL,
                    ApprovedAt TIMESTAMP NULL,
                    CompletedAt TIMESTAMP NULL,
                    
                    -- Additional Fields
                    Comments TEXT,
                    Priority VARCHAR(20) DEFAULT 'Medium',
                    
                    -- Template Information
                    IsTemplate BOOLEAN DEFAULT FALSE,
                    TemplateId INT,
                    
                    -- Foreign Key Constraints
                    FOREIGN KEY (FrameworkId) REFERENCES frameworks(FrameworkId) ON DELETE SET NULL,
                    FOREIGN KEY (OwnerId) REFERENCES users(UserId) ON DELETE SET NULL,
                    FOREIGN KEY (ReviewerId) REFERENCES users(UserId) ON DELETE SET NULL,
                    FOREIGN KEY (CreatedById) REFERENCES users(UserId) ON DELETE SET NULL,
                    FOREIGN KEY (TemplateId) REFERENCES events(EventId) ON DELETE SET NULL,
                    
                    -- Indexes for better performance
                    INDEX idx_framework (FrameworkId),
                    INDEX idx_module (Module),
                    INDEX idx_status (Status),
                    INDEX idx_owner (OwnerId),
                    INDEX idx_reviewer (ReviewerId),
                    INDEX idx_created_at (CreatedAt),
                    INDEX idx_template (IsTemplate)
                )
            """)
            
            # Insert sample templates
            cursor.execute("""
                INSERT IGNORE INTO events (
                    EventTitle, EventId_Generated, FrameworkName, Module, Category, 
                    OwnerId, ReviewerId, Status, IsTemplate, CreatedAt
                ) VALUES 
                (
                    'Q4 Access Review - IT', 'EVT-2025-1188', 'ISO 27001', 'Compliance → A.9.2.3', 
                    'Access Review', 1, 2, 'Approved', TRUE, NOW()
                ),
                (
                    'Annual DR Drill', 'EVT-2025-1123', 'SOC 2', 'BCP → DR Plan', 
                    'DR Drill', 3, 4, 'Approved', TRUE, NOW()
                )
            """)
            
            # Insert sample recurring events for calendar
            cursor.execute("""
                INSERT IGNORE INTO events (
                    EventTitle, EventId_Generated, FrameworkName, Module, Category, 
                    OwnerId, ReviewerId, Status, IsTemplate, RecurrenceType, Frequency, 
                    StartDate, EndDate, CreatedAt
                ) VALUES 
                (
                    'Q1 Access Review - Finance Dept', 'EVT-2025-2001', 'ISO 27001', 'Access Control', 
                    'Access Review', 1, 2, 'Pending Review', FALSE, 'Recurring', 'Weekly', 
                    '2025-01-07', '2025-12-31', NOW()
                ),
                (
                    'DR Drill - Data Center', 'EVT-2025-2002', 'SOC 2', 'Business Continuity', 
                    'DR Drill', 3, 4, 'Pending Review', FALSE, 'Recurring', 'Weekly', 
                    '2025-01-07', '2025-12-31', NOW()
                ),
                (
                    'Monthly Security Training', 'EVT-2025-2003', 'ISO 27001', 'Awareness Training', 
                    'Training', 1, 2, 'Pending Review', FALSE, 'Recurring', 'Monthly', 
                    '2025-01-15', '2025-12-31', NOW()
                ),
                (
                    'Quarterly Risk Assessment', 'EVT-2025-2004', 'ISO 27001', 'Risk Management', 
                    'Risk Assessment', 3, 4, 'Pending Review', FALSE, 'Recurring', 'Quarterly', 
                    '2025-01-01', '2025-12-31', NOW()
                )
            """)
            
            self.stdout.write(
                self.style.SUCCESS('Successfully created events table and sample data')
            )
