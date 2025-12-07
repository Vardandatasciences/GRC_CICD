from django.db import models
from django.utils import timezone
# from ...routes.Global.logging_service import send_log



from django.contrib.auth.models import User

 
# Users model (Django built-in User model is used)
class Users(models.Model):
    UserId = models.AutoField(primary_key=True)
    UserName = models.CharField(max_length=255)
    Password = models.CharField(max_length=255)
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)
    Email = models.EmailField(max_length=100)
    FirstName=models.CharField(max_length=255)
    LastName=models.CharField(max_length=255)
    IsActive=models.CharField(max_length=1, default='Y', choices=[('Y', 'Yes'), ('N', 'No')])
    DepartmentId=models.CharField(max_length=50)
    session_token=models.CharField(max_length=1045, null=True, blank=True)
    consent_accepted=models.CharField(max_length=1, default='0', choices=[('0', 'Not Accepted'), ('1', 'Accepted')])
    license_key=models.CharField(max_length=100, null=True, blank=True, unique=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return f"User {self.UserId} - {self.UserName}"
    
    @property
    def is_active(self):
        """Django REST Framework compatibility - maps IsActive to is_active"""
        if isinstance(self.IsActive, str):
            return self.IsActive.upper() == 'Y'
        elif isinstance(self.IsActive, bool):
            return self.IsActive
        else:
            return False
    
    @property
    def is_authenticated(self):
        """Django REST Framework compatibility - always returns True if user exists"""
        return True
    
    @property
    def username(self):
        """Django REST Framework compatibility - maps UserName to username"""
        return self.UserName
    
    @property
    def id(self):
        """Django REST Framework compatibility - maps UserId to id"""
        return self.UserId
    
    def get_full_name(self):
        """Django REST Framework compatibility - returns full name"""
        return f"{self.FirstName} {self.LastName}".strip()
 




class CategoryBusinessUnit(models.Model):
    id = models.AutoField(primary_key=True)
    source = models.CharField(max_length=50)
    value = models.CharField(max_length=255)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    class Meta:
        db_table = 'categoryunit'

    def __str__(self):
        return f"{self.source} - {self.value}"


class Framework(models.Model):
    FrameworkId = models.AutoField(primary_key=True)
    FrameworkName = models.CharField(max_length=255)
    CurrentVersion = models.FloatField(default=1.0)
    FrameworkDescription = models.TextField()
    EffectiveDate = models.DateField(null=True, blank=True)
    CreatedByName = models.CharField(max_length=255)
    CreatedByDate = models.DateField()
    Category = models.CharField(max_length=100, null=True, blank=True)
    DocURL = models.CharField(max_length=255, null=True, blank=True)
    Identifier = models.CharField(max_length=45, null=True, blank=True)
    StartDate = models.DateField(null=True, blank=True)
    EndDate = models.DateField(null=True, blank=True)
    Status = models.CharField(max_length=45, null=True, blank=True)
    ActiveInactive = models.CharField(max_length=45, null=True, blank=True)
    Reviewer = models.CharField(max_length=255)
    InternalExternal= models.CharField(max_length=45, null=True, blank=True)
    Amendment = models.JSONField(null=True, blank=True, default=list)  # Store amendment history
    latestAmmendmentDate= models.DateField(null=True, blank=True)
    latestComparisionCheckDate= models.DateField(null=True, blank=True)
    
 
    class Meta:
        db_table = 'frameworks'
 

class Kpi(models.Model):
    KpiId = models.AutoField(primary_key=True, db_column='Id')
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId', null=True, blank=True)
    FrameworkName = models.CharField(max_length=255, null=True, blank=True)
    Name = models.CharField(max_length=255)
    Description = models.TextField(null=True, blank=True)
    Value = models.TextField(null=True, blank=True)
    DataType = models.CharField(max_length=100, null=True, blank=True)
    FromWhereToAccessData = models.TextField(null=True, blank=True)
    Formula = models.TextField(null=True, blank=True)
    DisplayType = models.CharField(max_length=100, null=True, blank=True)
    AuditTrail = models.TextField(null=True, blank=True)
    CreatedAt = models.DateTimeField(null=True, blank=True)
    UpdatedAt = models.DateTimeField(null=True, blank=True)
    Module = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'kpis'

    def __str__(self):
        return f"{self.Name} ({self.FrameworkName or 'No Framework'})"


class FrameworkVersion(models.Model):
    VersionId = models.AutoField(primary_key=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    Version = models.FloatField()
    FrameworkName = models.CharField(max_length=255)
    CreatedBy = models.CharField(max_length=255)
    CreatedDate = models.DateField()
    PreviousVersionId = models.IntegerField(null=True, blank=True)
 
    class Meta:
        db_table = 'frameworkversions'
 
 
class Policy(models.Model):
    PolicyId = models.AutoField(primary_key=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    CurrentVersion = models.CharField(max_length=20, default='1.0')
    Status = models.CharField(max_length=50)
    PolicyDescription = models.TextField()
    PolicyName = models.CharField(max_length=255)
    StartDate = models.DateField()
    EndDate = models.DateField(null=True, blank=True)
    Department = models.CharField(max_length=255, null=True, blank=True)
    CreatedByName = models.CharField(max_length=255, null=True, blank=True)
    CreatedByDate = models.DateField(null=True, blank=True)
    Applicability = models.CharField(max_length=450, null=True, blank=True)
    DocURL = models.CharField(max_length=255, null=True, blank=True)
    Scope = models.TextField(null=True, blank=True)
    Objective = models.TextField(null=True, blank=True)
    Identifier = models.CharField(max_length=45, null=True, blank=True)
    PermanentTemporary = models.CharField(max_length=45, null=True, blank=True)
    ActiveInactive = models.CharField(max_length=45, null=True, blank=True)
    Reviewer=models.CharField(max_length=255, null=True, blank=True)
    CoverageRate = models.FloatField(null=True, blank=True)
    AcknowledgedUserIds = models.JSONField(default=list, blank=True, null=True)  # Allow null and use empty list as default
    AcknowledgementCount = models.IntegerField(default=0)
    PolicyType = models.CharField(max_length=255, null=True, blank=True)
    PolicyCategory = models.CharField(max_length=255, null=True, blank=True)
    PolicySubCategory = models.CharField(max_length=255, null=True, blank=True)
    Reviewer = models.CharField(max_length=255, null=True, blank=True)
    Entities = models.JSONField(default=list, blank=True, null=True)  # Store entity IDs or "all"
 
 
    class Meta:
        db_table = 'policies'
 
 
class PolicyVersion(models.Model):
    VersionId = models.AutoField(primary_key=True)
    PolicyId = models.ForeignKey('Policy', on_delete=models.CASCADE, db_column='PolicyId')
    Version = models.CharField(max_length=20)
    PolicyName = models.CharField(max_length=255)
    CreatedBy = models.CharField(max_length=255)
    CreatedDate = models.DateField()
    PreviousVersionId = models.IntegerField(null=True, blank=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    class Meta:
        db_table = 'policyversions'

class PolicyCategory(models.Model):
    Id = models.AutoField(primary_key=True)
    PolicyType = models.CharField(max_length=255)
    PolicyCategory = models.CharField(max_length=255)
    PolicySubCategory = models.CharField(max_length=255)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    class Meta:
        db_table = 'policycategories'
        unique_together = ('PolicyType', 'PolicyCategory', 'PolicySubCategory')

    def __str__(self):
        return f"{self.PolicyType} - {self.PolicyCategory} - {self.PolicySubCategory}"

 
 
class SubPolicy(models.Model):
    SubPolicyId = models.AutoField(primary_key=True)
    PolicyId = models.ForeignKey('Policy', on_delete=models.CASCADE, db_column='PolicyId')
    SubPolicyName = models.CharField(max_length=255)
    CreatedByName = models.CharField(max_length=255)
    CreatedByDate = models.DateField()
    Identifier = models.CharField(max_length=45)
    Description = models.TextField()
    Status = models.CharField(max_length=50, null=True, blank=True)
    PermanentTemporary = models.CharField(max_length=50, null=True, blank=True)
    Control = models.TextField(null=True, blank=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    class Meta:
        db_table = 'subpolicies'
 
 
class PolicyApproval(models.Model):
    ApprovalId = models.AutoField(primary_key=True)
    Identifier = models.CharField(max_length=45, db_column='Identifier')
    ExtractedData = models.JSONField(null=True, blank=True)
    UserId = models.IntegerField()
    ReviewerId = models.IntegerField()
    Version = models.CharField(max_length=50, null=True, blank=True)
    ApprovedNot = models.BooleanField(null=True)
    ApprovedDate = models.DateField(null=True, blank=True)
    PolicyId = models.ForeignKey('Policy', on_delete=models.CASCADE, db_column='PolicyId', null=True, blank=True)
    ApprovalDueDate = models.DateField(null=True, blank=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    def __str__(self):
        return f"PolicyApproval {self.Identifier} (Version {self.Version})"
 
    class Meta:
        db_table = 'policyapproval'

class ComplianceApproval(models.Model):
    ApprovalId = models.AutoField(primary_key=True)
    Identifier = models.CharField(max_length=45, db_column='Identifier')
    ExtractedData = models.JSONField(null=True, blank=True)
    UserId = models.IntegerField()
    ReviewerId = models.IntegerField()
    Version = models.CharField(max_length=50, null=True, blank=True)
    ApprovedNot = models.BooleanField(null=True)
    ApprovedDate = models.DateField(null=True, blank=True)
    PolicyId = models.ForeignKey('Policy', on_delete=models.CASCADE, db_column='PolicyId', null=True, blank=True)
    ApprovalDueDate = models.DateField(null=True, blank=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    def __str__(self):
        return f"complianceApproval {self.Identifier} (Version {self.Version})"
 
    class Meta:
        db_table = 'complianceapproval'

class FrameworkApproval(models.Model):
    ApprovalId = models.AutoField(primary_key=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId', null=True)
    # Identifier field is optional, uncomment if needed
    # Identifier = models.CharField(max_length=45, null=True, blank=True)
    ExtractedData = models.JSONField(null=True, blank=True)
    UserId = models.IntegerField()
    ReviewerId = models.IntegerField(null=True, blank=True)
    Version = models.CharField(max_length=50, null=True, blank=True)
    ApprovedNot = models.BooleanField(null=True)
    ApprovedDate = models.DateField(null=True, blank=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    def __str__(self):
        return f"FrameworkApproval {self.FrameworkId_id} (Version {self.Version})"

    class Meta:
        db_table = 'frameworkapproval'

# Users model (Django built-in User model is used)
class Compliance(models.Model):
    ComplianceId = models.AutoField(primary_key=True)
    SubPolicy = models.ForeignKey(SubPolicy, on_delete=models.CASCADE, db_column='SubPolicyId', related_name='compliances')
    ComplianceTitle = models.CharField(max_length=145, null=True, blank=True)
    ComplianceItemDescription = models.TextField(null=True, blank=True)
    ComplianceType = models.CharField(max_length=100, null=True, blank=True)
    Scope = models.TextField(null=True, blank=True)
    Objective = models.TextField(null=True, blank=True)
    BusinessUnitsCovered = models.CharField(max_length=225, null=True, blank=True)
    IsRisk = models.BooleanField(null=True, blank=True)
    PossibleDamage = models.TextField(null=True, blank=True)
    mitigation = models.JSONField(null=True, blank=True)
    Criticality = models.CharField(max_length=50, null=True, blank=True)
    MandatoryOptional = models.CharField(max_length=50, null=True, blank=True)
    ManualAutomatic = models.CharField(max_length=50, null=True, blank=True)
    Impact = models.CharField(max_length=50, null=True, blank=True)
    Probability = models.CharField(max_length=50, null=True, blank=True)
    MaturityLevel = models.CharField(max_length=50, choices=[
        ('Initial', 'Initial'),
        ('Developing', 'Developing'),
        ('Defined', 'Defined'),
        ('Managed', 'Managed'),
        ('Optimizing', 'Optimizing')
    ], default='Initial', null=True, blank=True)
    ActiveInactive = models.CharField(max_length=45, default='Inactive', null=True, blank=True)
    PermanentTemporary = models.CharField(max_length=45, null=True, blank=True)
    CreatedByName = models.CharField(max_length=250, null=True, blank=True)
    CreatedByDate = models.DateField(null=True, blank=True)
    ComplianceVersion = models.CharField(max_length=50, null=False)
    Status = models.CharField(max_length=50, default='Under Review', null=True, blank=True)
    Identifier = models.CharField(max_length=45, null=True, blank=True)
    Applicability = models.CharField(max_length=450, null=True, blank=True)
    PreviousComplianceVersionId = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='next_versions',
        db_column='PreviousComplianceVersionId'
    )
    PotentialRiskScenarios = models.TextField(null=True, blank=True)
    RiskType = models.CharField(max_length=45, choices=[
        ('Current', 'Current'),
        ('Residual', 'Residual'),
        ('Inherent', 'Inherent'),
        ('Emerging', 'Emerging'),
        ('Accepted', 'Accepted')
    ], null=True, blank=True)
    RiskCategory = models.CharField(max_length=45, null=True, blank=True)
    RiskBusinessImpact = models.CharField(max_length=45, null=True, blank=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    class Meta:
        db_table = 'compliance'

    def __str__(self):
        return f"Compliance {self.ComplianceId} - Version {self.ComplianceVersion}"
    
    def save(self, *args, **kwargs):
        # First save the compliance record
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Only create/update risk record when compliance is approved and active
        if self.Status == 'Approved' and self.ActiveInactive == 'Active':
            try:
                print(f"Compliance {self.ComplianceId} is approved and active, ensuring risk record exists")
                
                # Find the corresponding risk record
                risk = Risk.objects.filter(ComplianceId=self.ComplianceId).first()
                
                if not risk:
                    # Create a new risk record if one doesn't exist
                    print(f"Creating new risk record for approved and active compliance {self.ComplianceId}")
                    
                    # Get Impact and Probability from compliance data
                    try:
                        risk_impact = int(float(self.Impact)) if self.Impact else 5
                    except:
                        risk_impact = 5
                    
                    try:
                        risk_probability = int(float(self.Probability)) if self.Probability else 5
                    except:
                        risk_probability = 5
                    
                    # Calculate exposure rating
                    risk_exposure = risk_impact * risk_probability
                    
                    # Start with ALL required fields to avoid null errors
                    risk_data = {
                        'ComplianceId': self.ComplianceId,
                        'RiskDescription': self.ComplianceItemDescription or self.ComplianceTitle or 'Auto-generated risk from compliance',
                        'RiskTitle': self.ComplianceTitle or 'Risk from Compliance',
                        'RiskLikelihood': risk_probability,
                        'RiskImpact': risk_impact,
                        'RiskExposureRating': float(risk_exposure),
                        'RiskMultiplierX': 0.1,
                        'RiskMultiplierY': 0.1,
                        'Criticality': self.Criticality or 'Medium',
                        'PossibleDamage': self.PotentialRiskScenarios or self.PossibleDamage or '',
                        'Category': self.RiskCategory or 'Operational',
                        'RiskType': self.RiskType or 'Current',
                        'BusinessImpact': self.RiskBusinessImpact or '',
                        'RiskPriority': self.Criticality or 'Medium',
                        'FrameworkId': self.FrameworkId.FrameworkId if hasattr(self.FrameworkId, 'FrameworkId') else None
                    }
                    
                    print(f"Risk data to create: {risk_data}")
                    
                    risk = Risk.objects.create(**risk_data)
                    print(f"Successfully created risk record with ID: {risk.RiskId}")
                else:
                    # Update existing risk record with latest compliance data
                    print(f"Updating existing risk record {risk.RiskId} for approved and active compliance {self.ComplianceId}")
                    if self.Criticality:
                        risk.Criticality = self.Criticality
                    if self.PotentialRiskScenarios:
                        risk.PossibleDamage = self.PotentialRiskScenarios
                    if self.RiskCategory:
                        risk.Category = self.RiskCategory
                    if self.RiskType:
                        risk.RiskType = self.RiskType
                    if self.RiskBusinessImpact:
                        risk.BusinessImpact = self.RiskBusinessImpact
                    risk.save()
                    print(f"Successfully updated risk record {risk.RiskId}")
                        
            except Exception as e:
                print(f"Error handling risk record for approved and active compliance {self.ComplianceId}: {str(e)}")
                import traceback
                print(f"Full traceback: {traceback.format_exc()}")
    

class ExportTask(models.Model):
    id = models.AutoField(primary_key=True)
    export_data = models.JSONField(null=True, blank=True)
    file_type = models.CharField(max_length=10)
    user_id = models.CharField(max_length=100)
    s3_url = models.CharField(max_length=255, null=True, blank=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed')
        ],
        default='pending'
    )
    error = models.TextField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    class Meta:
        db_table = 'exported_files'



# Audit model
class Audit(models.Model):
    AuditId = models.AutoField(primary_key=True)
    Title = models.CharField(max_length=255, null=True, blank=True)
    Scope = models.TextField(null=True, blank=True)
    Objective = models.TextField(null=True, blank=True)
    BusinessUnit = models.CharField(max_length=255, null=True, blank=True)
    Role = models.CharField(max_length=100, null=True, blank=True)
    Responsibility = models.CharField(max_length=255, null=True, blank=True)
    Assignee = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='assignee', db_column='assignee')
    Auditor = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='auditor', db_column='auditor')
    Reviewer = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='reviewer', null=True, db_column='reviewer')
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    PolicyId = models.ForeignKey('Policy', on_delete=models.CASCADE, db_column='PolicyId', null=True)
    SubPolicyId = models.ForeignKey('SubPolicy', on_delete=models.CASCADE, db_column='SubPolicyId', null=True)
    DueDate = models.DateField()
    Frequency = models.IntegerField(null=True)
    Status = models.CharField(max_length=45)
    CompletionDate = models.DateTimeField(null=True)
    ReviewStatus = models.CharField(max_length=45, null=True)
    ReviewerComments = models.CharField(max_length=255, null=True)
    AuditType = models.CharField(max_length=10, default='R')  # R for Regular, A for AI, I for Internal, E for External, S for Self-Audit
    Evidence = models.TextField(null=True, blank=True)
    Comments = models.TextField(null=True, blank=True)
    AssignedDate = models.DateTimeField(null=True, db_column='AssignedDate')
    Reports = models.JSONField(null=True, blank=True)
    ReviewStartDate = models.DateTimeField(null=True)
    ReviewDate = models.DateTimeField(null=True)

    class Meta:
        db_table = 'audit'


# AuditFinding model
class AuditFinding(models.Model):
    AuditFindingsId = models.AutoField(primary_key=True)
    AuditId = models.ForeignKey(Audit, on_delete=models.CASCADE, db_column='AuditId', related_name='findings')
    ComplianceId = models.ForeignKey(Compliance, on_delete=models.CASCADE, db_column='ComplianceId')
    UserId = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='UserId')
    Evidence = models.TextField()
    Check = models.CharField(max_length=1, choices=[
        ('0', 'Not Started'), 
        ('1', 'In Progress'), 
        ('2', 'Completed'),
        ('3', 'Not Applicable')
    ], default='0')
    MajorMinor = models.CharField(max_length=1, choices=[
        ('0', 'Minor'),
        ('1', 'Major'),
        ('2', 'Not Applicable')
    ], null=True, blank=True)
    HowToVerify = models.TextField(null=True, blank=True)
    Impact = models.TextField(null=True, blank=True)
    Recommendation = models.TextField(null=True, blank=True)
    DetailsOfFinding = models.TextField(null=True, blank=True)
    Comments = models.TextField(null=True, blank=True)
    CheckedDate = models.DateTimeField(null=True, blank=True)
    AssignedDate = models.DateTimeField()
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    class Meta:
        db_table = 'audit_findings'
        
    def save(self, *args, **kwargs):
        """Override save to ensure AuditId consistency"""
        print(f"DEBUG: Saving AuditFinding {self.AuditFindingsId} with AuditId {self.AuditId.AuditId}")
        super().save(*args, **kwargs)
        # send_log(f"AuditFinding saved: {self.AuditFindingsId}", self.AuditId.AuditId)
 
class Incident(models.Model):
    IncidentId = models.AutoField(primary_key=True)
    IncidentTitle = models.CharField(max_length=255)
    Description = models.TextField()
    Mitigation = models.JSONField(null=True, blank=True)
    FrameworkId = models.IntegerField(null=True, blank=True)
    AuditId = models.ForeignKey('Audit', on_delete=models.CASCADE, null=True, blank=True, db_column='AuditId')
    ComplianceId = models.ForeignKey('Compliance', on_delete=models.CASCADE, null=True, blank=True, db_column='ComplianceId')
    
    Date = models.DateField()
    Time = models.TimeField()
    UserId = models.ForeignKey('Users', on_delete=models.CASCADE, null=True, blank=True, db_column='UserId')
    
    Origin = models.CharField(max_length=50)
    Comments = models.TextField(null=True, blank=True)
    RiskCategory = models.CharField(max_length=100, null=True, blank=True)
    IncidentCategory = models.CharField(max_length=100, null=True, blank=True)
    RiskPriority = models.CharField(max_length=20, null=True, blank=True)
    Attachments = models.TextField(null=True, blank=True)
    
    CreatedAt = models.DateTimeField(auto_now_add=True)
    Status = models.CharField(max_length=45, null=True, blank=True)
    IdentifiedAt = models.DateTimeField(null=True, blank=True)
    
    RepeatedNot = models.BooleanField(null=True, blank=True)
    CostOfIncident = models.CharField(max_length=45, null=True, blank=True)
    ReopenedNot = models.BooleanField(null=True, blank=True)
    
    RejectionSource = models.CharField(max_length=20, null=True, blank=True, choices=[
        ('INCIDENT', 'Rejected as Incident'),
        ('RISK', 'Rejected from Risk')
    ])
    
    AffectedBusinessUnit = models.CharField(max_length=100, null=True, blank=True)
    SystemsAssetsInvolved = models.TextField(null=True, blank=True)
    GeographicLocation = models.CharField(max_length=100, null=True, blank=True)
    Criticality = models.CharField(max_length=20, null=True, blank=True)
    InitialImpactAssessment = models.TextField(null=True, blank=True)
    InternalContacts = models.TextField(null=True, blank=True)
    ExternalPartiesInvolved = models.TextField(null=True, blank=True)
    RegulatoryBodies = models.TextField(null=True, blank=True)
    RelevantPoliciesProceduresViolated = models.TextField(null=True, blank=True)
    ControlFailures = models.TextField(null=True, blank=True)
    LessonsLearned = models.TextField(null=True, blank=True)
    IncidentClassification = models.CharField(max_length=100, null=True, blank=True)
    PossibleDamage = models.TextField(null=True, blank=True)
    AssignerId = models.IntegerField(null=True, blank=True)
    ReviewerId = models.IntegerField(null=True, blank=True)
    MitigationDueDate = models.DateTimeField(null=True, blank=True)
    AssignedDate = models.DateTimeField(null=True, blank=True)
    AssignmentNotes = models.TextField(null=True, blank=True)
    IncidentFormDetails = models.JSONField(null=True, blank=True)
    MitigationCompletedDate = models.DateTimeField(null=True, blank=True)
    class Meta:
        db_table = 'incidents'


class IncidentApproval(models.Model):
    IncidentId = models.IntegerField()
    version = models.CharField(max_length=45)
    ExtractedInfo = models.JSONField(null=True)
    AssigneeId = models.CharField(max_length=45, null=True)
    ReviewerId = models.CharField(max_length=45, null=True)
    ApprovedRejected = models.CharField(max_length=45, null=True)
    Date = models.DateTimeField(null=True, auto_now_add=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    class Meta:
        db_table = 'incident_approval'
        managed = False  # Since we're connecting to an existing table


class AuditReport(models.Model):
    ReportId = models.AutoField(primary_key=True)
    AuditId = models.ForeignKey(Audit, on_delete=models.CASCADE, db_column='AuditId')
    Report = models.TextField()
    PolicyId = models.ForeignKey('Policy', on_delete=models.CASCADE, db_column='PolicyId', null=True)
    SubPolicyId = models.ForeignKey('SubPolicy', on_delete=models.CASCADE, db_column='SubPolicyId', null=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')

    class Meta:
        db_table = 'audit_report'

class AuditDocument(models.Model):
    """
    Model for storing documents uploaded for AI audits
    Links documents to specific audits, policiels, and sub-policies
    """
    DocumentId = models.AutoField(primary_key=True)
    AuditId = models.ForeignKey(Audit, on_delete=models.CASCADE, db_column='AuditId', related_name='documents')
    PolicyId = models.ForeignKey('Policy', on_delete=models.CASCADE, db_column='PolicyId', null=True, blank=True)
    SubPolicyId = models.ForeignKey('SubPolicy', on_delete=models.CASCADE, db_column='SubPolicyId', null=True, blank=True)
    ComplianceId = models.ForeignKey('Compliance', on_delete=models.CASCADE, db_column='ComplianceId', null=True, blank=True)
    
    # Document details
    DocumentName = models.CharField(max_length=255)
    DocumentType = models.CharField(max_length=50, choices=[
        ('evidence', 'Evidence'),
        ('policy_doc', 'Policy Document'),
        ('compliance_doc', 'Compliance Document'),
        ('audit_doc', 'Audit Document'),
        ('other', 'Other')
    ], default='evidence')
    FilePath = models.CharField(max_length=500)  # S3 path or local path
    FileSize = models.BigIntegerField()  # File size in bytes
    FileExtension = models.CharField(max_length=10)  # .pdf, .docx, etc.
    MimeType = models.CharField(max_length=100)  # application/pdf, etc.
    
    # Upload metadata
    UploadedBy = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='UploadedBy')
    UploadedDate = models.DateTimeField(auto_now_add=True)
    UploadStatus = models.CharField(max_length=20, choices=[
        ('uploading', 'Uploading'),
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('processed', 'Processed'),
        ('failed', 'Failed')
    ], default='uploading')
    
    # AI Processing metadata
    ProcessingStatus = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='pending')
    ProcessingResults = models.JSONField(null=True, blank=True)  # AI analysis results
    ProcessingError = models.TextField(null=True, blank=True)
    ProcessedDate = models.DateTimeField(null=True, blank=True)
    
    # Compliance mapping
    ComplianceMapping = models.JSONField(null=True, blank=True)  # Maps document sections to compliance requirements
    ExtractedText = models.TextField(null=True, blank=True)  # Extracted text for AI processing
    DocumentSummary = models.TextField(null=True, blank=True)  # AI-generated summary
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    # External integrations
    ExternalSource = models.CharField(max_length=50, null=True, blank=True, choices=[
        ('jira', 'Jira'),
        ('log360', 'Log 360'),
        ('teams', 'Microsoft Teams'),
        ('manual', 'Manual Upload')
    ], default='manual')
    ExternalId = models.CharField(max_length=100, null=True, blank=True)  # External system ID
    
    class Meta:
        db_table = 'audit_documents'
        indexes = [
            models.Index(fields=['AuditId', 'PolicyId']),
            models.Index(fields=['AuditId', 'SubPolicyId']),
            models.Index(fields=['UploadedBy', 'UploadedDate']),
            models.Index(fields=['ProcessingStatus']),
        ]
    
    def __str__(self):
        return f"Document {self.DocumentId} - {self.DocumentName} (Audit {self.AuditId})"

class AuditDocumentMapping(models.Model):
    """
    Maps specific sections of uploaded documents to compliance requirements
    """
    MappingId = models.AutoField(primary_key=True)
    DocumentId = models.ForeignKey(AuditDocument, on_delete=models.CASCADE, db_column='DocumentId', related_name='mappings')
    ComplianceId = models.ForeignKey('Compliance', on_delete=models.CASCADE, db_column='ComplianceId')
    
    # Document section details
    SectionTitle = models.CharField(max_length=255, null=True, blank=True)
    SectionContent = models.TextField(null=True, blank=True)
    PageNumber = models.IntegerField(null=True, blank=True)
    StartPosition = models.IntegerField(null=True, blank=True)  # Character position in document
    EndPosition = models.IntegerField(null=True, blank=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    # Compliance mapping
    ComplianceStatus = models.CharField(max_length=20, choices=[
        ('compliant', 'Compliant'),
        ('non_compliant', 'Non-Compliant'),
        ('partially_compliant', 'Partially Compliant'),
        ('not_applicable', 'Not Applicable'),
        ('requires_review', 'Requires Review')
    ], default='requires_review')
    
    # AI Analysis
    ConfidenceScore = models.FloatField(null=True, blank=True)  # AI confidence in mapping
    AIRecommendations = models.TextField(null=True, blank=True)
    RiskLevel = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], null=True, blank=True)
    
    # Review metadata
    ReviewedBy = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='ReviewedBy', null=True, blank=True)
    ReviewedDate = models.DateTimeField(null=True, blank=True)
    ReviewComments = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'audit_document_mappings'
        unique_together = ['DocumentId', 'ComplianceId']
    
    def __str__(self):
        return f"Mapping {self.MappingId} - Doc {self.DocumentId} to Compliance {self.ComplianceId}"
        # Risk model

# Workflow model
class Workflow(models.Model):
    Id = models.AutoField(primary_key=True)
    FindingId = models.ForeignKey(AuditFinding, on_delete=models.CASCADE, db_column='finding_id')
    IncidentId = models.ForeignKey(Incident, on_delete=models.CASCADE, db_column='IncidentId')
    AssigneeId = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='assignee_id', related_name='workflow_assignee')
    ReviewerId = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='reviewer_id', related_name='workflow_reviewer')
    AssignedAt = models.DateTimeField()
 
    class Meta:
        db_table = 'workflow'
 
class AuditVersion(models.Model):
    AuditId = models.IntegerField()
    Version = models.CharField(max_length=45)
    ExtractedInfo = models.JSONField()
    UserId = models.IntegerField()
    ApprovedRejected = models.CharField(max_length=45, null=True, blank=True)
    Date = models.DateTimeField(auto_now_add=True)
    ActiveInactive = models.CharField(max_length=1, default='1')
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    class Meta:
        db_table = 'audit_version'
        unique_together = ('AuditId', 'Version')

    def __str__(self):
        return f"AuditVersion(AuditId={self.AuditId}, Version={self.Version})"
    



class Notification(models.Model):
    id = models.AutoField(primary_key=True)
    recipient = models.CharField(max_length=255)
    type = models.CharField(max_length=100)
    channel = models.CharField(max_length=20)  # 'email' or 'whatsapp'
    success = models.BooleanField()
    error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    class Meta:
        db_table = 'notifications'


class S3File(models.Model):
    url = models.TextField()
    file_type = models.CharField(max_length=50, null=True, blank=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    user_id = models.CharField(max_length=100, null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    class Meta:
        db_table = 's3_files'

    def __str__(self):
        return f"{self.file_name} ({self.file_type}) - {self.user_id}"


class Risk(models.Model):
    RiskId = models.AutoField(primary_key=True)  # Primary Key
    ComplianceId = models.IntegerField(null=True)
    RiskTitle = models.TextField(null=True)
    Criticality = models.CharField(max_length=50, null=True)
    PossibleDamage = models.TextField(null=True)
    Category = models.CharField(max_length=100, null=True)
    RiskType = models.TextField(null=True)
    BusinessImpact = models.TextField(null=True)
    RiskDescription = models.TextField(null=True)
    RiskLikelihood = models.IntegerField(null=True)
    RiskImpact = models.IntegerField(null=True)
    RiskExposureRating = models.FloatField(null=True)
    RiskMultiplierX = models.FloatField(default=0.1, help_text="Impact multiplier (1-10, stored as 0.1-1.0)")
    RiskMultiplierY = models.FloatField(default=0.1, help_text="Likelihood multiplier (1-10, stored as 0.1-1.0)")
    RiskPriority = models.CharField(max_length=50, null=True)
    RiskMitigation = models.TextField(null=True)
    CreatedAt = models.DateField(auto_now_add=True)
    FrameworkId = models.IntegerField(null=True)
    class Meta:
        db_table = 'risk'  # Ensure Django uses the correct table in the database

    def __str__(self):
        return f"Risk {self.RiskId}"

class RiskInstance(models.Model):
    # Define choices for RiskStatus
    STATUS_NOT_ASSIGNED = 'Not Assigned'
    STATUS_ASSIGNED = 'Assigned'
    STATUS_APPROVED = 'Approved'
    STATUS_REJECTED = 'Rejected'
    
    RISK_STATUS_CHOICES = [
        (STATUS_NOT_ASSIGNED, 'Not Assigned'),
        (STATUS_ASSIGNED, 'Assigned'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]
    
    # Define choices for MitigationStatus - including "Pending" that frontend sends
    MITIGATION_PENDING = 'Pending'
    MITIGATION_YET_TO_START = 'Yet to Start'
    MITIGATION_IN_PROGRESS = 'Work In Progress'
    MITIGATION_REVISION_REVIEWER = 'Revision Required by Reviewer'
    MITIGATION_REVISION_USER = 'Revision Required by User'
    MITIGATION_COMPLETED = 'Completed'
    
    MITIGATION_STATUS_CHOICES = [
        (MITIGATION_PENDING, 'Pending'),
        (MITIGATION_YET_TO_START, 'Yet to Start'),
        (MITIGATION_IN_PROGRESS, 'Work In Progress'),
        (MITIGATION_REVISION_REVIEWER, 'Revision Required by Reviewer'),
        (MITIGATION_REVISION_USER, 'Revision Required by User'),
        (MITIGATION_COMPLETED, 'Completed'),
    ]

    RiskInstanceId = models.AutoField(primary_key=True)
    RiskId = models.IntegerField(null=True)
    IncidentId = models.IntegerField(null=True)
    ComplianceId = models.IntegerField(null=True)
    RiskTitle = models.TextField(null=True)
    RiskDescription = models.TextField(null=True)
    PossibleDamage = models.TextField(null=True)
    RiskPriority = models.CharField(max_length=50, null=True)
    Criticality = models.CharField(max_length=100, null=True)
    Category = models.CharField(max_length=100, null=True)
    Origin = models.CharField(max_length=50, null=True)
    ReportedBy = models.IntegerField(null=True)
    RiskLikelihood = models.IntegerField(null=True)
    RiskImpact = models.IntegerField(null=True)
    RiskExposureRating = models.FloatField(null=True)
    RiskMultiplierX = models.FloatField(default=0.1, help_text="Impact multiplier (1-10, stored as 0.1-1.0)")
    RiskMultiplierY = models.FloatField(default=0.1, help_text="Likelihood multiplier (1-10, stored as 0.1-1.0)")
    Appetite = models.CharField(max_length=100, null=True)
    RiskResponseType = models.CharField(max_length=100, null=True)
    RiskResponseDescription = models.TextField(null=True)
    RiskMitigation = models.JSONField(null=True, blank=True)
    RiskType = models.TextField(null=True)
    RiskOwner = models.CharField(max_length=255, null=True)
    BusinessImpact = models.TextField(null=True)
    UserId = models.IntegerField(null=True)
    MitigationDueDate = models.DateField(null=True)
    ModifiedMitigations = models.JSONField(null=True)
    MitigationCompletedDate = models.DateField(null=True)
    ReviewerCount = models.IntegerField(null=True)
    RiskFormDetails = models.JSONField(null=True, blank=True)
    RecurrenceCount = models.IntegerField(default=1, null=True)
    CreatedAt = models.DateField(auto_now_add=True)
    Reviewer = models.CharField(max_length=45, null=True)
    ReviewerId = models.IntegerField(null=True)
    FirstResponseAt = models.DateTimeField(null=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    # Field definitions with choices
    RiskStatus = models.CharField(max_length=50, choices=RISK_STATUS_CHOICES, default=STATUS_NOT_ASSIGNED, null=True)
    MitigationStatus = models.CharField(max_length=45, choices=MITIGATION_STATUS_CHOICES, default=MITIGATION_PENDING, null=True)
    
    def __str__(self):
        return f"Risk Instance {self.RiskInstanceId}"

    class Meta:
        db_table = 'risk_instance'  # Ensure Django uses the correct table name in the database
        managed = False  # Since we're connecting to an existing table

    def save(self, *args, **kwargs):
        # Custom save to update related Incident status when mitigation is completed
        super().save(*args, **kwargs)
        try:
            if self.MitigationStatus == self.MITIGATION_COMPLETED and self.IncidentId:
                from . import Incident
                try:
                    incident = Incident.objects.get(IncidentId=self.IncidentId)
                    if incident.Status != 'Risk Mitigated':
                        incident.Status = 'Risk Mitigated'
                        incident.save()
                except Incident.DoesNotExist:
                    pass  # No related incident found, do nothing
        except Exception as e:
            import traceback
            print(f"Error updating Incident status for RiskInstance {self.RiskInstanceId}: {e}")
            print(traceback.format_exc())


class RiskAssignment(models.Model):
    risk = models.ForeignKey('Risk', on_delete=models.CASCADE, related_name='assignments')
    assigned_to = models.ForeignKey(Users, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='risk_assignments_created')
    assigned_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'risk_assignments'
    
    def __str__(self):
        return f"Risk {self.risk.RiskId} assigned to {self.assigned_to.UserName}"


class RiskApproval(models.Model):
    RiskInstanceId = models.IntegerField()
    version = models.CharField(max_length=45)
    ExtractedInfo = models.JSONField(null=True)
    UserId = models.CharField(max_length=45, null=True)
    ApproverId = models.CharField(max_length=45, null=True)
    ApprovedRejected = models.CharField(max_length=45, null=True)
    Date = models.DateTimeField(null=True, auto_now_add=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    class Meta:
        db_table = 'grc.risk_approval'
        managed = False  # Since we're connecting to an existing table


class GRCLog(models.Model):
    LogId = models.AutoField(primary_key=True)
    Timestamp = models.DateTimeField(auto_now_add=True)
    UserId = models.CharField(max_length=50, null=True)
    UserName = models.CharField(max_length=100, null=True)
    Module = models.CharField(max_length=100, null=True)
    ActionType = models.CharField(max_length=50, null=True)
    EntityId = models.CharField(max_length=50, null=True)
    EntityType = models.CharField(max_length=50, null=True)
    LogLevel = models.CharField(max_length=20, default='INFO')
    Description = models.TextField(null=True)
    IPAddress = models.CharField(max_length=45, null=True)
    AdditionalInfo = models.JSONField(null=True, blank=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    class Meta:
        db_table = 'grc_logs'

    def __str__(self):
        return f"Log {self.LogId}: {self.ActionType} on {self.Module}"





class Entity(models.Model):
    Id = models.AutoField(primary_key=True)
    EntityName = models.CharField(max_length=255)
    Location = models.CharField(max_length=255)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    class Meta:
        db_table = 'entities'
        verbose_name_plural = 'Entities'

    def __str__(self):
        return f"{self.EntityName} ({self.Location})"

class LastChecklistItemVerified(models.Model):
    # Id = models.AutoField(primary_key=True)
    ComplianceId = models.IntegerField(primary_key=True)
    SubPolicyId = models.IntegerField()
    PolicyId = models.IntegerField()
    FrameworkId = models.IntegerField()
    Date = models.DateField(null=True, blank=True)
    Time = models.TimeField(null=True, blank=True)
    User = models.IntegerField(null=True, blank=True)
    Complied = models.CharField(max_length=1, null=True, blank=True)
    Comments = models.TextField(null=True, blank=True)
    Count = models.IntegerField(default=0, null=True, blank=True)
    AuditFindingsId = models.IntegerField(null=True, blank=True)
 
    class Meta:
        db_table = 'lastchecklistitemverified'
        unique_together = (('ComplianceId', 'SubPolicyId', 'PolicyId', 'FrameworkId'),)




# =====================================================
# SINGLE RBAC MODEL - Add this to your models.py
# =====================================================

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError

class RBAC(models.Model):
    """
    Role-Based Access Control model for GRC system
    Maps users to their specific permissions across all modules
    """
    
    # Role choices
    ROLE_CHOICES = [
        ('GRC Administrator', 'GRC Administrator'),
        ('Compliance Manager', 'Compliance Manager'),
        ('Compliance Officer', 'Compliance Officer'),
        ('Compliance Approver', 'Compliance Approver'),
        ('Executive/Senior Management', 'Executive/Senior Management'),
        ('Policy Manager', 'Policy Manager'),
        ('Policy Approver', 'Policy Approver'),
        ('Audit Manager', 'Audit Manager'),
        ('Internal Auditor', 'Internal Auditor'),
        ('External Auditor', 'External Auditor'),
        ('Audit Reviewer', 'Audit Reviewer'),
        ('Risk Manager', 'Risk Manager'),
        ('Risk Analyst', 'Risk Analyst'),
        ('Risk Reviewer', 'Risk Reviewer'),
        ('Incident Response Manager', 'Incident Response Manager'),
        ('Incident Analyst', 'Incident Analyst'),
        ('Department Manager', 'Department Manager'),
        ('End User', 'End User'),
    ]

    rbac_id = models.AutoField(primary_key=True, db_column='RBACId')
    user = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='UserId')
    username = models.CharField(max_length=255, db_column='UserName')
    role = models.CharField(max_length=100, choices=ROLE_CHOICES, db_column='Role')
    
    # Compliance Module Permissions
    create_compliance = models.BooleanField(default=False, db_column='CreateCompliance')
    edit_compliance = models.BooleanField(default=False, db_column='EditCompliance')
    approve_compliance = models.BooleanField(default=False, db_column='ApproveCompliance')
    view_all_compliance = models.BooleanField(default=False, db_column='ViewAllCompliance')
    compliance_performance_analytics = models.BooleanField(default=False, db_column='CompliancePerformanceAnalytics')
    
    # Policy Module Permissions
    create_policy = models.BooleanField(default=False, db_column='CreatePolicy')
    edit_policy = models.BooleanField(default=False, db_column='EditPolicy')
    approve_policy = models.BooleanField(default=False, db_column='ApprovePolicy')
    create_framework = models.BooleanField(default=False, db_column='CreateFramework')
    approve_framework = models.BooleanField(default=False, db_column='ApproveFramework')
    view_all_policy = models.BooleanField(default=False, db_column='ViewAllPolicy')
    policy_performance_analytics = models.BooleanField(default=False, db_column='PolicyPerformanceAnalytics')
    
    # Audit Module Permissions
    assign_audit = models.BooleanField(default=False, db_column='AssignAudit')
    conduct_audit = models.BooleanField(default=False, db_column='ConductAudit')
    review_audit = models.BooleanField(default=False, db_column='ReviewAudit')
    view_audit_reports = models.BooleanField(default=False, db_column='ViewAuditReports')
    audit_performance_analytics = models.BooleanField(default=False, db_column='AuditPerformanceAnalytics')
    
    # Risk Module Permissions
    create_risk = models.BooleanField(default=False, db_column='CreateRisk')
    edit_risk = models.BooleanField(default=False, db_column='EditRisk')
    approve_risk = models.BooleanField(default=False, db_column='ApproveRisk')
    assign_risk = models.BooleanField(default=False, db_column='AssignRisk')
    evaluate_assigned_risk = models.BooleanField(default=False, db_column='EvaluateAssignedRisk')
    view_all_risk = models.BooleanField(default=False, db_column='ViewAllRisk')
    risk_performance_analytics = models.BooleanField(default=False, db_column='RiskPerformanceAnalytics')
    
    # Incident Module Permissions
    create_incident = models.BooleanField(default=False, db_column='CreateIncident')
    edit_incident = models.BooleanField(default=False, db_column='EditIncident')
    assign_incident = models.BooleanField(default=False, db_column='AssignIncident')
    evaluate_assigned_incident = models.BooleanField(default=False, db_column='EvaluateAssignedIncident')
    escalate_to_risk = models.BooleanField(default=False, db_column='EscalateToRisk')
    view_all_incident = models.BooleanField(default=False, db_column='ViewAllIncident')
    incident_performance_analytics = models.BooleanField(default=False, db_column='IncidentPerformanceAnalytics')
    create_event = models.BooleanField(default=False, db_column='CreateEvent')
    edit_event = models.BooleanField(default=False, db_column='EditEvent')
    approve_event = models.BooleanField(default=False, db_column='ApproveEvent')
    reject_event = models.BooleanField(default=False, db_column='RejectEvent')
    archive_event = models.BooleanField(default=False, db_column='ArchiveEvent')
    view_all_event = models.BooleanField(default=False, db_column='ViewAllEvents')
    view_module_event = models.BooleanField(default=False, db_column='ViewModuleEvents')
    event_performance_analytics = models.BooleanField(default=False, db_column='EventPerformanceAnalytics')
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='UpdatedAt')
    is_active = models.CharField(max_length=1, default='Y', choices=[('Y', 'Yes'), ('N', 'No')], db_column='IsActive')
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    class Meta:
        db_table = 'rbac'
        ordering = ['username', 'role']
        verbose_name = 'RBAC Permission'
        verbose_name_plural = 'RBAC Permissions'
        unique_together = ['user', 'role']

    def __str__(self):
        return f"{self.username} - {self.role}"

    def save(self, *args, **kwargs):
        # Auto-populate username from user if not provided
        if self.user and not self.username:
            self.username = self.user.username
        super().save(*args, **kwargs)

    # Module Access Checker Methods
    def has_compliance_access(self):
        """Check if user has any compliance module access"""
        return any([
            self.create_compliance,
            self.edit_compliance,
            self.approve_compliance,
            self.view_all_compliance,
            self.compliance_performance_analytics
        ])

    def has_policy_access(self):
        """Check if user has any policy module access"""
        return any([
            self.create_policy,
            self.edit_policy,
            self.approve_policy,
            self.create_framework,
            self.approve_framework,
            self.view_all_policy,
            self.policy_performance_analytics
        ])

    def has_audit_access(self):
        """Check if user has any audit module access"""
        return any([
            self.assign_audit,
            self.conduct_audit,
            self.review_audit,
            self.view_audit_reports,
            self.audit_performance_analytics
        ])

    def has_risk_access(self):
        """Check if user has any risk module access"""
        return any([
            self.create_risk,
            self.edit_risk,
            self.approve_risk,
            self.assign_risk,
            self.evaluate_assigned_risk,
            self.view_all_risk,
            self.risk_performance_analytics
        ])

    def has_incident_access(self):
        """Check if user has any incident module access"""
        return any([
            self.create_incident,
            self.edit_incident,
            self.assign_incident,
            self.evaluate_assigned_incident,
            self.escalate_to_risk,
            self.view_all_incident,
            self.incident_performance_analytics
        ])

    def has_event_access(self):
        """Check if user has any event module access"""
        return any([
            self.create_event,
            self.edit_event,
            self.approve_event,
            self.reject_event,
            self.archive_event,
            self.view_all_event,
            self.view_module_event,
            self.event_performance_analytics
        ])

    # Permission Checker Methods
    def can_create_in_module(self, module):
        """Check if user can create items in specified module"""
        create_permissions = {
            'compliance': self.create_compliance,
            'policy': self.create_policy,
            'risk': self.create_risk,
            'incident': self.create_incident,
            'event': self.create_event,
        }
        return create_permissions.get(module.lower(), False)

    def can_approve_in_module(self, module):
        """Check if user can approve items in specified module"""
        approve_permissions = {
            'compliance': self.approve_compliance,
            'policy': self.approve_policy,
            'risk': self.approve_risk,
            'event': self.approve_event,
        }
        return approve_permissions.get(module.lower(), False)

    def can_view_analytics_in_module(self, module):
        """Check if user can view analytics in specified module"""
        analytics_permissions = {
            'compliance': self.compliance_performance_analytics,
            'policy': self.policy_performance_analytics,
            'audit': self.audit_performance_analytics,
            'risk': self.risk_performance_analytics,
            'incident': self.incident_performance_analytics,
            'event': self.event_performance_analytics,
        }
        return analytics_permissions.get(module.lower(), False)

    def is_module_admin(self, module):
        """Check if user has admin-level access to a module"""
        if module.lower() == 'compliance':
            return all([
                self.create_compliance,
                self.edit_compliance,
                self.approve_compliance,
                self.view_all_compliance,
                self.compliance_performance_analytics
            ])
        elif module.lower() == 'policy':
            return all([
                self.create_policy,
                self.edit_policy,
                self.approve_policy,
                self.create_framework,
                self.approve_framework,
                self.view_all_policy,
                self.policy_performance_analytics
            ])
        elif module.lower() == 'audit':
            return all([
                self.assign_audit,
                self.conduct_audit,
                self.review_audit,
                self.view_audit_reports,
                self.audit_performance_analytics
            ])
        elif module.lower() == 'risk':
            return all([
                self.create_risk,
                self.edit_risk,
                self.approve_risk,
                self.assign_risk,
                self.evaluate_assigned_risk,
                self.view_all_risk,
                self.risk_performance_analytics
            ])
        elif module.lower() == 'incident':
            return all([
                self.create_incident,
                self.edit_incident,
                self.assign_incident,
                self.evaluate_assigned_incident,
                self.escalate_to_risk,
                self.view_all_incident,
                self.incident_performance_analytics
            ])
        elif module.lower() == 'event':
            return all([
                self.create_event,
                self.edit_event,
                self.approve_event,
                self.reject_event,
                self.archive_event,
                self.view_all_event,
                self.view_module_event,
                self.event_performance_analytics
            ])
        return False

    def is_grc_administrator(self):
        """Check if user is a GRC Administrator with full access"""
        return self.role == 'GRC Administrator'

    def get_accessible_modules(self):
        """Return list of modules the user has access to"""
        modules = []
        if self.has_compliance_access():
            modules.append('compliance')
        if self.has_policy_access():
            modules.append('policy')
        if self.has_audit_access():
            modules.append('audit')
        if self.has_risk_access():
            modules.append('risk')
        if self.has_incident_access():
            modules.append('incident')
        if self.has_event_access():
            modules.append('event')
        return modules

    def get_permissions_summary(self):
        """Return a dictionary summarizing user's permissions"""
        return {
            'compliance': {
                'has_access': self.has_compliance_access(),
                'can_create': self.create_compliance,
                'can_edit': self.edit_compliance,
                'can_approve': self.approve_compliance,
                'can_view_all': self.view_all_compliance,
                'can_view_analytics': self.compliance_performance_analytics,
            },
            'policy': {
                'has_access': self.has_policy_access(),
                'can_create': self.create_policy,
                'can_edit': self.edit_policy,
                'can_approve': self.approve_policy,
                'can_create_framework': self.create_framework,
                'can_approve_framework': self.approve_framework,
                'can_view_all': self.view_all_policy,
                'can_view_analytics': self.policy_performance_analytics,
            },
            'audit': {
                'has_access': self.has_audit_access(),
                'can_assign': self.assign_audit,
                'can_conduct': self.conduct_audit,
                'can_review': self.review_audit,
                'can_view_reports': self.view_audit_reports,
                'can_view_analytics': self.audit_performance_analytics,
            },
            'risk': {
                'has_access': self.has_risk_access(),
                'can_create': self.create_risk,
                'can_edit': self.edit_risk,
                'can_approve': self.approve_risk,
                'can_assign': self.assign_risk,
                'can_evaluate': self.evaluate_assigned_risk,
                'can_view_all': self.view_all_risk,
                'can_view_analytics': self.risk_performance_analytics,
            },
            'incident': {
                'has_access': self.has_incident_access(),
                'can_create': self.create_incident,
                'can_edit': self.edit_incident,
                'can_assign': self.assign_incident,
                'can_evaluate': self.evaluate_assigned_incident,
                'can_escalate': self.escalate_to_risk,
                'can_view_all': self.view_all_incident,
                'can_view_analytics': self.incident_performance_analytics,
            },
            'event': {
                'has_access': self.has_event_access(),
                'can_create': self.create_event,
                'can_edit': self.edit_event,
                'can_approve': self.approve_event,
                'can_reject': self.reject_event,
                'can_archive': self.archive_event,
                'can_view_all': self.view_all_event,
                'can_view_module': self.view_module_event,
                'can_view_analytics': self.event_performance_analytics,
            }
        }

        
# Manager for common RBAC queries
class RBACManager(models.Manager):
    def get_users_by_permission(self, permission_field):
        """Get all users who have a specific permission"""
        filter_kwargs = {permission_field: True, 'is_active': 'Y'}
        return self.filter(**filter_kwargs)

    def get_users_by_role(self, role):
        """Get all users with a specific role"""
        return self.filter(role=role, is_active='Y')

    def get_users_by_module_access(self, module):
        """Get all users who have access to a specific module"""
        if module.lower() == 'compliance':
            return self.filter(
                models.Q(create_compliance=True) |
                models.Q(edit_compliance=True) |
                models.Q(approve_compliance=True) |
                models.Q(view_all_compliance=True) |
                models.Q(compliance_performance_analytics=True),
                is_active='Y'
            )
        elif module.lower() == 'policy':
            return self.filter(
                models.Q(create_policy=True) |
                models.Q(edit_policy=True) |
                models.Q(approve_policy=True) |
                models.Q(create_framework=True) |
                models.Q(approve_framework=True) |
                models.Q(view_all_policy=True) |
                models.Q(policy_performance_analytics=True),
                is_active='Y'
            )
        elif module.lower() == 'audit':
            return self.filter(
                models.Q(assign_audit=True) |
                models.Q(conduct_audit=True) |
                models.Q(review_audit=True) |
                models.Q(view_audit_reports=True) |
                models.Q(audit_performance_analytics=True),
                is_active='Y'
            )
        elif module.lower() == 'risk':
            return self.filter(
                models.Q(create_risk=True) |
                models.Q(edit_risk=True) |
                models.Q(approve_risk=True) |
                models.Q(assign_risk=True) |
                models.Q(evaluate_assigned_risk=True) |
                models.Q(view_all_risk=True) |
                models.Q(risk_performance_analytics=True),
                is_active='Y'
            )
        elif module.lower() == 'incident':
            return self.filter(
                models.Q(create_incident=True) |
                models.Q(edit_incident=True) |
                models.Q(assign_incident=True) |
                models.Q(evaluate_assigned_incident=True) |
                models.Q(escalate_to_risk=True) |
                models.Q(view_all_incident=True) |
                models.Q(incident_performance_analytics=True),
                is_active='Y'
            )
        elif module.lower() == 'event':
            return self.filter(
                models.Q(create_event=True) |
                models.Q(edit_event=True) |
                models.Q(approve_event=True) |
                models.Q(reject_event=True) |
                models.Q(archive_event=True) |
                models.Q(view_all_event=True) |
                models.Q(view_module_event=True) |
                models.Q(event_performance_analytics=True),
                is_active='Y'
            )
        return self.none()

    def get_grc_administrators(self):
        """Get all GRC Administrators"""
        return self.filter(role='GRC Administrator', is_active='Y')




class BusinessUnit(models.Model):
    BusinessUnitId = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=255)
    Code = models.CharField(max_length=50)
    Description = models.TextField()
    EntityId = models.IntegerField()
    IsActive = models.BooleanField(default=True)
    CreatedDate = models.DateTimeField()
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    class Meta:
        db_table = 'businessunits'

    def __str__(self):
        return self.Name


class Category(models.Model):
    CategoryId = models.AutoField(primary_key=True)
    CategoryName = models.CharField(max_length=255)
    Description = models.TextField()
    IsActive = models.BooleanField(default=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    class Meta:
        db_table = 'category'

    def __str__(self):
        return self.CategoryName


class Department(models.Model):
    DepartmentId = models.AutoField(primary_key=True)
    EntityId = models.IntegerField()
    DepartmentName = models.CharField(max_length=255)
    DepartmentHead = models.IntegerField()
    IsActive = models.BooleanField(default=True)
    CreatedDate = models.DateTimeField()
    BusinessUnitId = models.IntegerField()
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    class Meta:
        db_table = 'department'

    def __str__(self):
        return self.DepartmentName


class Entity(models.Model):
    Id = models.AutoField(primary_key=True)
    EntityName = models.CharField(max_length=255)
    EntityType = models.CharField(max_length=255)
    ParentEntityId = models.IntegerField(null=True, blank=True)
    LocationId = models.IntegerField()
    IsActive = models.BooleanField(default=True)
    CreatedDate = models.DateTimeField()
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    class Meta:
        db_table = 'mainentities'

    def __str__(self):
        return self.EntityName


class Holiday(models.Model):
    HolidayId = models.AutoField(primary_key=True)
    EntityId = models.IntegerField()
    HolidayDate = models.DateField()
    HolidayName = models.CharField(max_length=255)
    IsNational = models.BooleanField(default=True)

    class Meta:
        db_table = 'holidays'

    def __str__(self):
        return self.HolidayName


class Location(models.Model):
    LocationID = models.AutoField(primary_key=True)
    AddressLine = models.CharField(max_length=255)
    City = models.CharField(max_length=255)
    State = models.CharField(max_length=255, null=True, blank=True)
    Country = models.CharField(max_length=255)
    PostalCode = models.CharField(max_length=45, null=True, blank=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    class Meta:
        db_table = 'locations'

    def __str__(self):
        return self.AddressLine


class Applicability(models.Model):
    ApplicabilityId = models.AutoField(primary_key=True)
    EntityId = models.IntegerField()
    DepartmentId = models.IntegerField()
    CategoryId = models.IntegerField()
    StartDate = models.DateField()
    EndDate = models.DateField(null=True, blank=True)
    IsMandatory = models.BooleanField(default=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    class Meta:
        db_table = 'applicability'

    def __str__(self):
        return f'{self.EntityId} - {self.DepartmentId} - {self.CategoryId}'


# Signal handlers for automatic risk record management
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Compliance)
def handle_compliance_risk_sync(sender, instance, created, **kwargs):
    """
    Signal handler to ensure risk records are created/updated when compliance records change
    """
    try:
        if created:
            # New compliance created - risk should already be created in the save method
            print(f"Signal: New compliance {instance.ComplianceId} created")
        else:
            # Existing compliance updated - check if status is 'Approved' and 'Active'
            if instance.Status == 'Approved' and instance.ActiveInactive == 'Active':
                print(f"Signal: Compliance {instance.ComplianceId} is approved and active, ensuring risk record exists")
                
                # Check if risk record exists
                risk = Risk.objects.filter(ComplianceId=instance.ComplianceId).first()
                
                if not risk:
                    # Create risk record if it doesn't exist
                    print(f"Signal: Creating missing risk record for approved and active compliance {instance.ComplianceId}")
                    
                    # Start with just ComplianceId to ensure it works
                    risk_data = {
                        'ComplianceId': instance.ComplianceId
                    }
                    
                    # Add other fields only if they have values
                    if instance.Criticality:
                        risk_data['Criticality'] = instance.Criticality
                    if instance.PotentialRiskScenarios:
                        risk_data['PossibleDamage'] = instance.PotentialRiskScenarios
                    if instance.RiskCategory:
                        risk_data['Category'] = instance.RiskCategory
                    if instance.RiskType:
                        risk_data['RiskType'] = instance.RiskType
                    if instance.RiskBusinessImpact:
                        risk_data['BusinessImpact'] = instance.RiskBusinessImpact
                    
                    print(f"Signal: Risk data to create: {risk_data}")
                    Risk.objects.create(**risk_data)
                    print(f"Signal: Successfully created risk record for compliance {instance.ComplianceId}")
                else:
                    # Update existing risk record
                    print(f"Signal: Updating existing risk record {risk.RiskId} for compliance {instance.ComplianceId}")
                    if instance.Criticality:
                        risk.Criticality = instance.Criticality
                    if instance.PotentialRiskScenarios:
                        risk.PossibleDamage = instance.PotentialRiskScenarios
                    if instance.RiskCategory:
                        risk.Category = instance.RiskCategory
                    if instance.RiskType:
                        risk.RiskType = instance.RiskType
                    if instance.RiskBusinessImpact:
                        risk.BusinessImpact = instance.RiskBusinessImpact
                    risk.save()
                    print(f"Signal: Successfully updated risk record {risk.RiskId}")
                    
    except Exception as e:
        print(f"Signal error handling compliance {instance.ComplianceId}: {str(e)}")
        import traceback
        print(f"Signal full traceback: {traceback.format_exc()}")


class Event(models.Model):
    """
    Event model for GRC Event Management
    """
    EventId = models.AutoField(primary_key=True)
    EventTitle = models.CharField(max_length=255)
    EventId_Generated = models.CharField(max_length=50, unique=True)  # Auto-generated ID like EVT-2025-1188
    Description = models.TextField(null=True, blank=True)
    
    # Framework and Module Information
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId', null=True, blank=True)
    FrameworkName = models.CharField(max_length=255, null=True, blank=True)
    Module = models.CharField(max_length=255, null=True, blank=True)
    
    # Linked Records (can link to different types of records)
    LinkedRecordType = models.CharField(max_length=50, choices=[
        ('policy', 'Policy'),
        ('compliance', 'Compliance'),
        ('audit', 'Audit'),
        ('risk', 'Risk'),
        ('incident', 'Incident'),
        ('subpolicy', 'SubPolicy'),
        ('Jira Issue', 'Jira Issue')
    ], null=True, blank=True)
    LinkedRecordId = models.IntegerField(null=True, blank=True)
    LinkedRecordName = models.CharField(max_length=255, null=True, blank=True)
    
    # Event Details
    Category = models.CharField(max_length=100, null=True, blank=True)
    EventType = models.ForeignKey('EventType', on_delete=models.SET_NULL, null=True, blank=True, db_column='EventTypeId')
    SubEventType = models.CharField(max_length=100, null=True, blank=True)
    Owner = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='event_owner', db_column='OwnerId', null=True, blank=True)
    Reviewer = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='event_reviewer', db_column='ReviewerId', null=True, blank=True)
    
    # Recurrence Information
    RecurrenceType = models.CharField(max_length=20, choices=[
        ('Non-Recurring', 'Non-Recurring'),
        ('Recurring', 'Recurring')
    ], default='Non-Recurring')
    Frequency = models.CharField(max_length=50, null=True, blank=True)
    StartDate = models.DateField(null=True, blank=True)
    EndDate = models.DateField(null=True, blank=True)
    
    # Status and Dates
    Status = models.CharField(max_length=50, choices=[
        ('Draft', 'Draft'),
        ('Pending Review', 'Pending Review'),
        ('Submitted', 'Submitted'),
        ('Under Review', 'Under Review'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('Archived', 'Archived')
    ], default='Under Review')
    
    # Evidence and Attachments
    Evidence = models.JSONField(blank=True, null=True)  # Store S3 URLs as semicolon-separated string
    
    # Dynamic Fields Data
    DynamicFieldsData = models.JSONField(blank=True, null=True)  # Store user-entered dynamic fields data
    
    # Metadata
    CreatedBy = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='event_created_by', db_column='CreatedById', null=True, blank=True)
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)
    ApprovedAt = models.DateTimeField(null=True, blank=True)
    
    # Additional Fields
    Comments = models.CharField(max_length=255, null=True, blank=True, db_column='comments')
    Priority = models.CharField(max_length=20, choices=[
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical')
    ], default='Medium')
    
    # Template Information
    IsTemplate = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'events'
        ordering = ['-CreatedAt']
        verbose_name = 'Event'
        verbose_name_plural = 'Events'

    def __str__(self):
        return f"{self.EventId_Generated} - {self.EventTitle}"

    def save(self, *args, **kwargs):
        # Auto-generate EventId_Generated if not provided
        if not self.EventId_Generated:
            from django.db import IntegrityError
            max_retries = 5
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    year = self.CreatedAt.year if self.CreatedAt else timezone.now().year
                    
                    # Get the last event for this year and extract the number
                    last_event = Event.objects.filter(
                        EventId_Generated__startswith=f'EVT-{year}-'
                    ).order_by('-EventId_Generated').first()
                    
                    if last_event:
                        try:
                            last_number = int(last_event.EventId_Generated.split('-')[-1])
                            next_number = last_number + 1
                        except (ValueError, IndexError):
                            next_number = 1
                    else:
                        next_number = 1
                    
                    self.EventId_Generated = f'EVT-{year}-{next_number:04d}'
                    
                    # Try to save
                    super().save(*args, **kwargs)
                    break
                    
                except IntegrityError as e:
                    # If duplicate key error, retry with incremented number
                    if 'EventId_Generated' in str(e) or 'Duplicate entry' in str(e):
                        retry_count += 1
                        if retry_count < max_retries:
                            # Increment the number and try again
                            try:
                                if hasattr(self, 'EventId_Generated') and self.EventId_Generated:
                                    current_number = int(self.EventId_Generated.split('-')[-1])
                                    next_number = current_number + 1
                                else:
                                    # If we don't have a current number, query again
                                    last_event = Event.objects.filter(
                                        EventId_Generated__startswith=f'EVT-{year}-'
                                    ).order_by('-EventId_Generated').first()
                                    if last_event:
                                        try:
                                            current_number = int(last_event.EventId_Generated.split('-')[-1])
                                            next_number = current_number + 1
                                        except (ValueError, IndexError):
                                            next_number = 1
                                    else:
                                        next_number = 1
                                
                                self.EventId_Generated = f'EVT-{year}-{next_number:04d}'
                                continue
                            except Exception:
                                # If parsing fails, use timestamp-based fallback
                                year = self.CreatedAt.year if self.CreatedAt else timezone.now().year
                                timestamp_suffix = int(timezone.now().timestamp() * 1000) % 10000
                                self.EventId_Generated = f'EVT-{year}-{timestamp_suffix:04d}'
                                continue
                        else:
                            # Max retries reached, use timestamp-based ID as fallback
                            year = self.CreatedAt.year if self.CreatedAt else timezone.now().year
                            timestamp_suffix = int(timezone.now().timestamp() * 1000) % 10000
                            self.EventId_Generated = f'EVT-{year}-{timestamp_suffix:04d}'
                            try:
                                super().save(*args, **kwargs)
                                break
                            except IntegrityError:
                                # Even timestamp failed, use random
                                import random
                                random_suffix = random.randint(10000, 99999)
                                self.EventId_Generated = f'EVT-{year}-{random_suffix:05d}'
                                super().save(*args, **kwargs)
                                break
                    else:
                        # Other integrity error, re-raise
                        raise
                except Exception as e:
                    # Other errors, re-raise
                    raise
        else:
            # EventId_Generated already set, just save
            super().save(*args, **kwargs)

    @property
    def owner_name(self):
        return f"{self.Owner.FirstName} {self.Owner.LastName}" if self.Owner else "Not Assigned"
    
    @property
    def reviewer_name(self):
        return f"{self.Reviewer.FirstName} {self.Reviewer.LastName}" if self.Reviewer else "Not Assigned"



class EventType(models.Model):
    """
    Event Type model for categorizing events by framework
    """
    eventtype_id = models.AutoField(primary_key=True)
    FrameworkName = models.CharField(max_length=500)
    eventtype = models.TextField()
    eventSubtype = models.JSONField(null=True, blank=True)  # This matches the database column name
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    class Meta:
        db_table = 'eventtype'
        verbose_name = 'Event Type'
        verbose_name_plural = 'Event Types'

    def __str__(self):
        return f"{self.FrameworkName} - {self.eventtype}"


class Module(models.Model):
    """
    Module model for GRC system modules
    """
    moduleid = models.AutoField(primary_key=True, db_column='moduleid')
    modulename = models.CharField(max_length=255, db_column='modulename')
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    class Meta:
        db_table = 'modules'
        verbose_name = 'Module'
        verbose_name_plural = 'Modules'

    def __str__(self):
        return self.modulename


class AWSCredentials(models.Model):
    """
    AWS Credentials model for storing S3 configuration
    """
    id = models.AutoField(primary_key=True)
    accessKey = models.CharField(max_length=145)
    secretKey = models.CharField(max_length=145)
    region = models.CharField(max_length=45)
    bucketName = models.CharField(max_length=45)
    microServiceUrl = models.CharField(max_length=45)

    class Meta:
        db_table = 'aws_credentials'
        verbose_name = 'AWS Credential'
        verbose_name_plural = 'AWS Credentials'

    def __str__(self):
        return f"AWS Credentials {self.id} - {self.bucketName}"

    @classmethod
    def get_active_credentials(cls):
        """Get the first (and typically only) set of AWS credentials"""
        return cls.objects.first()


class FileOperations(models.Model):
    """
    File Operations model for tracking file operations in the system
    """
    OPERATION_TYPE_CHOICES = [
        ('upload', 'Upload'),
        ('download', 'Download'),
        ('export', 'Export'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.AutoField(primary_key=True)
    operation_type = models.CharField(max_length=10, choices=OPERATION_TYPE_CHOICES)
    module = models.CharField(max_length=45, null=True, blank=True)
    user_id = models.CharField(max_length=255)
    file_name = models.CharField(max_length=500)
    original_name = models.CharField(max_length=500, null=True, blank=True)
    stored_name = models.CharField(max_length=500, null=True, blank=True)
    s3_url = models.TextField(null=True, blank=True)
    s3_key = models.CharField(max_length=1000, null=True, blank=True)
    s3_bucket = models.CharField(max_length=255, null=True, blank=True)
    file_type = models.CharField(max_length=50, null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    content_type = models.CharField(max_length=255, null=True, blank=True)
    export_format = models.CharField(max_length=20, null=True, blank=True)
    record_count = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    error = models.TextField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    platform = models.CharField(max_length=50, default='Render')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    summary = models.TextField(null=True, blank=True)
    class Meta:
        db_table = 'file_operations'
        verbose_name = 'File Operation'
        verbose_name_plural = 'File Operations'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.operation_type.title()} - {self.file_name} ({self.status})"

    @property
    def formatted_file_size(self):
        """Return formatted file size"""
        if not self.file_size:
            return "Unknown size"
        
        # Convert bytes to human readable format
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"

    @property
    def display_name(self):
        """Return the best available name for display"""
        return self.original_name or self.file_name or "Unknown File"
# =====================================================
# EXTERNAL APPLICATIONS MODELS
# =====================================================

class ExternalApplication(models.Model):
    """
    External Applications model for managing external platform integrations
    """
    STATUS_CHOICES = [
        ('connected', 'Connected'),
        ('disconnected', 'Disconnected'),
        ('pending', 'Pending'),
        ('error', 'Error'),
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    category = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    description = models.TextField()
    icon_class = models.CharField(max_length=100)
    version = models.CharField(max_length=50, default='v1.0.0')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='disconnected')
    last_sync = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    configuration = models.JSONField(null=True, blank=True)
    api_endpoint = models.URLField(max_length=500, null=True, blank=True)
    oauth_url = models.URLField(max_length=500, null=True, blank=True)
    features = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'external_applications'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"

    def get_connection_count(self):
        """Get number of active connections for this application"""
        return self.connections.filter(connection_status='active').count()

    def get_last_connection(self):
        """Get the most recent connection for this application"""
        return self.connections.filter(connection_status='active').order_by('-last_used').first()


class ExternalApplicationConnection(models.Model):
    """
    External Application Connections model for user-specific connections
    """
    CONNECTION_STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
        ('error', 'Error'),
    ]

    id = models.AutoField(primary_key=True)
    application = models.ForeignKey(ExternalApplication, on_delete=models.CASCADE, related_name='connections')
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='external_connections')
    connection_token = models.TextField(null=True, blank=True)
    refresh_token = models.TextField(null=True, blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    connection_status = models.CharField(max_length=20, choices=CONNECTION_STATUS_CHOICES, default='active')
    last_used = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    projects_data = models.JSONField(null=True, blank=True, help_text="Stores all retrieved project data in JSON format")

    class Meta:
        db_table = 'external_application_connections'
        unique_together = ['application', 'user']
        indexes = [
            models.Index(fields=['user', 'application']),
            models.Index(fields=['connection_status']),
        ]

    def __str__(self):
        return f"{self.user.UserName} - {self.application.name} ({self.get_connection_status_display()})"

    def is_token_expired(self):
        """Check if the connection token is expired"""
        if not self.token_expires_at:
            return False
        return timezone.now() > self.token_expires_at

    def update_last_used(self):
        """Update the last used timestamp"""
        self.last_used = timezone.now()
        self.save(update_fields=['last_used'])


class ExternalApplicationSyncLog(models.Model):
    """
    External Application Sync Logs model for tracking sync activities
    """
    SYNC_TYPE_CHOICES = [
        ('full', 'Full Sync'),
        ('incremental', 'Incremental Sync'),
        ('manual', 'Manual Sync'),
    ]

    SYNC_STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('partial', 'Partial'),
    ]

    id = models.AutoField(primary_key=True)
    application = models.ForeignKey(ExternalApplication, on_delete=models.CASCADE, related_name='sync_logs')
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='external_sync_logs')
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPE_CHOICES)
    sync_status = models.CharField(max_length=20, choices=SYNC_STATUS_CHOICES)
    records_synced = models.IntegerField(default=0)
    error_message = models.TextField(null=True, blank=True)
    sync_started_at = models.DateTimeField()
    sync_completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'external_application_sync_logs'
        ordering = ['-sync_started_at']
        indexes = [
            models.Index(fields=['application', 'sync_started_at']),
            models.Index(fields=['user', 'sync_started_at']),
        ]

    def __str__(self):
        return f"{self.application.name} - {self.get_sync_type_display()} ({self.get_sync_status_display()})"

    @property
    def duration_seconds(self):
        """Calculate sync duration in seconds"""
        if self.sync_completed_at and self.sync_started_at:
            return (self.sync_completed_at - self.sync_started_at).total_seconds()
        return None


class UsersProjectList(models.Model):
    """
    Users Project List model for managing project assignments to users
    """
    LIST_TYPE_CHOICES = [
        ('single', 'Single User'),
        ('multiple', 'Multiple Users'),
    ]

    id = models.AutoField(primary_key=True)
    project_id = models.CharField(max_length=100, help_text="Jira project ID")
    project_name = models.CharField(max_length=255, help_text="Jira project name")
    project_key = models.CharField(max_length=50, help_text="Jira project key")
    project_details = models.JSONField(null=True, blank=True, help_text="Complete project details from Jira")
    users_list = models.JSONField(help_text="List of user IDs assigned to this project")
    list_type = models.CharField(max_length=20, choices=LIST_TYPE_CHOICES, default='multiple')
    assigned_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='assigned_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'users_project_list'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project_id']),
            models.Index(fields=['assigned_by']),
            models.Index(fields=['is_active']),
        ]
        unique_together = ['project_id', 'assigned_by']

    def __str__(self):
        return f"{self.project_name} ({self.project_key}) - {self.get_list_type_display()}"

    def get_assigned_users(self):
        """Get the actual User objects for the assigned user IDs"""
        if not self.users_list:
            return []
        return Users.objects.filter(UserId__in=self.users_list)

    def get_assigned_users_count(self):
        """Get the count of assigned users"""
        return len(self.users_list) if self.users_list else 0

    def add_user(self, user_id):
        """Add a user to the project list"""
        if not self.users_list:
            self.users_list = []
        if user_id not in self.users_list:
            self.users_list.append(user_id)
            self.save()

    def remove_user(self, user_id):
        """Remove a user from the project list"""
        if self.users_list and user_id in self.users_list:
            self.users_list.remove(user_id)
            self.save()

    def is_user_assigned(self, user_id):
        """Check if a user is assigned to this project"""
        return user_id in (self.users_list or [])


class IntegrationDataList(models.Model):
    id = models.BigAutoField(primary_key=True)
    heading = models.CharField(max_length=255)
    source = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    time = models.DateTimeField()  # event time
    data = models.JSONField()      # full JSON payload
    metadata = models.JSONField(blank=True, null=True)  # extra JSON
 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    class Meta:
        db_table = "integration_data_list"
        indexes = [
            models.Index(fields=["source"], name="idx_source"),
            models.Index(fields=["username"], name="idx_username"),
            models.Index(fields=["time"], name="idx_time"),
        ]

    def __str__(self):
        return f"{self.id} — {self.heading}"


class OAuthState(models.Model):
    """
    OAuth State model for storing OAuth state during external OAuth flows
    """
    state = models.CharField(max_length=255, unique=True, db_index=True)
    user_id = models.IntegerField()
    subdomain = models.CharField(max_length=255, null=True, blank=True)
    provider = models.CharField(max_length=50, default='bamboohr')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'oauth_states'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['state']),
            models.Index(fields=['user_id', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.provider} state for user {self.user_id}"
    
    def is_expired(self):
        """Check if state has expired"""
        return timezone.now() > self.expires_at


# =====================================================
# POLICY ACKNOWLEDGEMENT MODELS
# =====================================================

class PolicyAcknowledgementRequest(models.Model):
    """
    Policy Acknowledgement Request model for tracking acknowledgement campaigns
    """
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    AcknowledgementRequestId = models.AutoField(primary_key=True)
    PolicyId = models.ForeignKey('Policy', on_delete=models.CASCADE, db_column='PolicyId')
    PolicyVersion = models.CharField(max_length=20)
    
    # Request details
    Title = models.CharField(max_length=255, help_text="Title of the acknowledgement request")
    Description = models.TextField(null=True, blank=True, help_text="Description or message for users")
    DueDate = models.DateField(null=True, blank=True, help_text="Optional due date for acknowledgement")
    
    # Assignment details
    TargetUserIds = models.JSONField(help_text="List of user IDs who must acknowledge")
    TargetGroups = models.JSONField(null=True, blank=True, help_text="List of groups/roles who must acknowledge")
    
    # Status tracking
    Status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    TotalUsers = models.IntegerField(default=0, help_text="Total number of users assigned")
    AcknowledgedCount = models.IntegerField(default=0, help_text="Number of users who acknowledged")
    PendingCount = models.IntegerField(default=0, help_text="Number of users pending")
    
    # Metadata
    CreatedBy = models.ForeignKey('Users', on_delete=models.CASCADE, related_name='acknowledgement_requests_created', db_column='CreatedBy')
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)
    CompletedAt = models.DateTimeField(null=True, blank=True)
    
    # Notifications
    EmailNotificationSent = models.BooleanField(default=False)
    
    FrameworkId = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    
    class Meta:
        db_table = 'policy_acknowledgement_requests'
        ordering = ['-CreatedAt']
        indexes = [
            models.Index(fields=['PolicyId', 'PolicyVersion']),
            models.Index(fields=['Status', 'CreatedAt']),
            models.Index(fields=['CreatedBy']),
        ]
    
    def __str__(self):
        return f"Acknowledgement Request {self.AcknowledgementRequestId} - Policy {self.PolicyId.PolicyId}"
    
    def update_counts(self):
        """Update acknowledged and pending counts"""
        acknowledged = self.user_acknowledgements.filter(Status='Acknowledged').count()
        pending = self.user_acknowledgements.filter(Status='Pending').count()
        
        self.AcknowledgedCount = acknowledged
        self.PendingCount = pending
        
        # Mark as completed if all users acknowledged
        if self.TotalUsers > 0 and self.AcknowledgedCount >= self.TotalUsers:
            self.Status = 'Completed'
            if not self.CompletedAt:
                self.CompletedAt = timezone.now()
        
        self.save()
    
    @property
    def completion_percentage(self):
        """Calculate completion percentage"""
        if self.TotalUsers == 0:
            return 0
        return round((self.AcknowledgedCount / self.TotalUsers) * 100, 2)


class PolicyAcknowledgementUser(models.Model):
    """
    Policy Acknowledgement User model for tracking individual user acknowledgements
    """
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Acknowledged', 'Acknowledged'),
        ('Overdue', 'Overdue'),
    ]

    AcknowledgementUserId = models.AutoField(primary_key=True)
    AcknowledgementRequest = models.ForeignKey(
        'PolicyAcknowledgementRequest', 
        on_delete=models.CASCADE, 
        related_name='user_acknowledgements',
        db_column='AcknowledgementRequestId'
    )
    
    # User details
    UserId = models.ForeignKey('Users', on_delete=models.CASCADE, db_column='UserId')
    
    # Status
    Status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    
    # Acknowledgement details
    AcknowledgedAt = models.DateTimeField(null=True, blank=True)
    IPAddress = models.CharField(max_length=45, null=True, blank=True)
    UserAgent = models.CharField(max_length=255, null=True, blank=True)
    Comments = models.TextField(null=True, blank=True, help_text="Optional user comments")
    
    # Metadata
    AssignedAt = models.DateTimeField(auto_now_add=True)
    NotifiedAt = models.DateTimeField(null=True, blank=True)
    ReminderCount = models.IntegerField(default=0)
    LastReminderAt = models.DateTimeField(null=True, blank=True)
    
    # External access token for acknowledging without login
    Token = models.CharField(max_length=255, unique=True, null=True, blank=True, 
                            help_text="Unique token for external acknowledgement access")
    
    class Meta:
        db_table = 'policy_acknowledgement_users'
        ordering = ['-AssignedAt']
        unique_together = ['AcknowledgementRequest', 'UserId']
        indexes = [
            models.Index(fields=['UserId', 'Status']),
            models.Index(fields=['Status', 'AssignedAt']),
            models.Index(fields=['AcknowledgementRequest', 'Status']),
            models.Index(fields=['Token']),
        ]
    
    def __str__(self):
        return f"User {self.UserId.UserId} - Request {self.AcknowledgementRequest.AcknowledgementRequestId} - {self.Status}"
    
    def acknowledge(self, ip_address=None, user_agent=None, comments=None):
        """Mark as acknowledged"""
        self.Status = 'Acknowledged'
        self.AcknowledgedAt = timezone.now()
        self.IPAddress = ip_address
        self.UserAgent = user_agent
        if comments:
            self.Comments = comments
        self.save()
        
        # Update request counts
        self.AcknowledgementRequest.update_counts()
    
    @property
    def is_overdue(self):
        """Check if acknowledgement is overdue"""
        if not self.AcknowledgementRequest.DueDate:
            return False
        if self.Status == 'Acknowledged':
            return False
        return timezone.now().date() > self.AcknowledgementRequest.DueDate
    
    def save(self, *args, **kwargs):
        # Auto-update overdue status
        if self.is_overdue and self.Status == 'Pending':
            self.Status = 'Overdue'
        super().save(*args, **kwargs)


# =====================================================
# CONSENT MANAGEMENT MODELS
# =====================================================

class ConsentConfiguration(models.Model):
    """
    Stores configuration for which actions require user consent
    Managed by GRC Administrator
    """
    ACTION_CHOICES = [
        ('create_policy', 'Create Policy'),
        ('create_compliance', 'Create Compliance'),
        ('create_audit', 'Create Audit'),
        ('create_incident', 'Create Incident'),
        ('create_risk', 'Create Risk'),
        ('create_event', 'Create Event'),
        ('upload_policy', 'Upload in Policy'),
        ('upload_audit', 'Upload in Audit'),
        ('upload_incident', 'Upload in Incident'),
        ('upload_risk', 'Upload in Risk'),
        ('upload_event', 'Upload in Event'),
    ]
    
    config_id = models.AutoField(primary_key=True, db_column='ConfigId')
    action_type = models.CharField(max_length=50, unique=True, choices=ACTION_CHOICES, db_column='ActionType')
    action_label = models.CharField(max_length=100, db_column='ActionLabel')
    is_enabled = models.BooleanField(default=False, db_column='IsEnabled')
    consent_text = models.TextField(null=True, blank=True, db_column='ConsentText', 
                                     help_text='Custom consent text to display to users')
    framework = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    created_by = models.ForeignKey('Users', on_delete=models.SET_NULL, null=True, 
                                   related_name='consent_configs_created', db_column='CreatedBy')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    updated_by = models.ForeignKey('Users', on_delete=models.SET_NULL, null=True, 
                                   related_name='consent_configs_updated', db_column='UpdatedBy')
    updated_at = models.DateTimeField(auto_now=True, db_column='UpdatedAt')
    
    class Meta:
        db_table = 'consent_configuration'
        ordering = ['action_label']
    
    def __str__(self):
        return f"{self.action_label} - {'Enabled' if self.is_enabled else 'Disabled'}"


class ConsentAcceptance(models.Model):
    """
    Tracks when users accept consent for specific actions
    """
    acceptance_id = models.AutoField(primary_key=True, db_column='AcceptanceId')
    user = models.ForeignKey('Users', on_delete=models.CASCADE, db_column='UserId')
    config = models.ForeignKey('ConsentConfiguration', on_delete=models.CASCADE, db_column='ConfigId')
    action_type = models.CharField(max_length=50, db_column='ActionType')
    accepted_at = models.DateTimeField(auto_now_add=True, db_column='AcceptedAt')
    ip_address = models.CharField(max_length=50, null=True, blank=True, db_column='IpAddress')
    user_agent = models.TextField(null=True, blank=True, db_column='UserAgent')
    framework = models.ForeignKey('Framework', on_delete=models.CASCADE, db_column='FrameworkId')
    
    class Meta:
        db_table = 'consent_acceptance'
        ordering = ['-accepted_at']
        indexes = [
            models.Index(fields=['user', 'action_type', 'accepted_at']),
        ]
    
    def __str__(self):
        return f"{self.user.UserName} accepted {self.action_type} at {self.accepted_at}"