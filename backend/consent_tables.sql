-- ============================================================================
-- CONSENT MANAGEMENT SYSTEM - SQL TABLE CREATION
-- ============================================================================
-- Execute these SQL statements in your database to create the consent tables
-- ============================================================================

-- Table 1: Consent Configuration
-- Stores consent settings for each action type per framework
-- ============================================================================

CREATE TABLE consent_configuration (
    ConfigId INT AUTO_INCREMENT PRIMARY KEY,
    ActionType VARCHAR(50) NOT NULL,
    ActionLabel VARCHAR(100) NOT NULL,
    IsEnabled BOOLEAN DEFAULT FALSE,
    ConsentText TEXT,
    FrameworkId INT NOT NULL,
    CreatedBy INT NULL,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    UpdatedBy INT NULL,
    UpdatedAt DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    FOREIGN KEY (FrameworkId) REFERENCES frameworks(FrameworkId) ON DELETE CASCADE,
    FOREIGN KEY (CreatedBy) REFERENCES users(UserId) ON DELETE SET NULL,
    FOREIGN KEY (UpdatedBy) REFERENCES users(UserId) ON DELETE SET NULL,
    
    -- Constraints
    UNIQUE KEY unique_action_per_framework (ActionType, FrameworkId),
    INDEX idx_framework (FrameworkId),
    INDEX idx_enabled (IsEnabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Table 2: Consent Acceptance
-- Tracks all user consent acceptances with audit trail
-- ============================================================================

CREATE TABLE consent_acceptance (
    AcceptanceId INT AUTO_INCREMENT PRIMARY KEY,
    UserId INT NOT NULL,
    ConfigId INT NOT NULL,
    ActionType VARCHAR(50) NOT NULL,
    AcceptedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    IpAddress VARCHAR(50) NULL,
    UserAgent TEXT NULL,
    FrameworkId INT NOT NULL,
    
    -- Foreign Keys
    FOREIGN KEY (UserId) REFERENCES users(UserId) ON DELETE CASCADE,
    FOREIGN KEY (ConfigId) REFERENCES consent_configuration(ConfigId) ON DELETE CASCADE,
    FOREIGN KEY (FrameworkId) REFERENCES frameworks(FrameworkId) ON DELETE CASCADE,
    
    -- Indexes for performance
    INDEX idx_user_action_date (UserId, ActionType, AcceptedAt),
    INDEX idx_framework (FrameworkId),
    INDEX idx_config (ConfigId),
    INDEX idx_accepted_at (AcceptedAt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- OPTIONAL: Insert default consent configurations for existing frameworks
-- ============================================================================
-- Run this after creating the tables to populate with default settings
-- Replace {framework_id} with actual framework IDs from your database

/*
-- Example: Insert default configurations for Framework ID 1
INSERT INTO consent_configuration (ActionType, ActionLabel, IsEnabled, ConsentText, FrameworkId) VALUES
('create_policy', 'Create Policy', FALSE, 'I consent to creating a policy. I understand that this action will be recorded and tracked for compliance purposes.', 1),
('create_compliance', 'Create Compliance', FALSE, 'I consent to creating a compliance record. I understand that this action will be recorded and tracked for compliance purposes.', 1),
('create_audit', 'Create Audit', FALSE, 'I consent to creating an audit. I understand that this action will be recorded and tracked for compliance purposes.', 1),
('create_incident', 'Create Incident', FALSE, 'I consent to creating an incident. I understand that this action will be recorded and tracked for compliance purposes.', 1),
('create_risk', 'Create Risk', FALSE, 'I consent to creating a risk. I understand that this action will be recorded and tracked for compliance purposes.', 1),
('create_event', 'Create Event', FALSE, 'I consent to creating an event. I understand that this action will be recorded and tracked for compliance purposes.', 1),
('upload_policy', 'Upload in Policy', FALSE, 'I consent to uploading files in the policy module. I understand that this action will be recorded and tracked for compliance purposes.', 1),
('upload_audit', 'Upload in Audit', FALSE, 'I consent to uploading files in the audit module. I understand that this action will be recorded and tracked for compliance purposes.', 1),
('upload_incident', 'Upload in Incident', FALSE, 'I consent to uploading files in the incident module. I understand that this action will be recorded and tracked for compliance purposes.', 1),
('upload_risk', 'Upload in Risk', FALSE, 'I consent to uploading files in the risk module. I understand that this action will be recorded and tracked for compliance purposes.', 1),
('upload_event', 'Upload in Event', FALSE, 'I consent to uploading files in the event module. I understand that this action will be recorded and tracked for compliance purposes.', 1);
*/

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Run these to verify tables were created successfully

-- Check consent_configuration table structure
DESCRIBE consent_configuration;

-- Check consent_acceptance table structure
DESCRIBE consent_acceptance;

-- Count configurations
SELECT COUNT(*) as total_configurations FROM consent_configuration;

-- Count acceptances
SELECT COUNT(*) as total_acceptances FROM consent_acceptance;

-- View all configurations
SELECT * FROM consent_configuration ORDER BY ActionLabel;

-- View recent acceptances
SELECT 
    ca.AcceptanceId,
    u.UserName,
    cc.ActionLabel,
    ca.AcceptedAt,
    ca.IpAddress
FROM consent_acceptance ca
JOIN users u ON ca.UserId = u.UserId
JOIN consent_configuration cc ON ca.ConfigId = cc.ConfigId
ORDER BY ca.AcceptedAt DESC
LIMIT 20;

