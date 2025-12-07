<template>
  <div class="consent-overlay" v-if="showConsent">
    <div class="consent-container">
      <div class="consent-header">
        <div class="consent-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2"/>
            <polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="2"/>
            <line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" stroke-width="2"/>
            <line x1="16" y1="17" x2="8" y2="17" stroke="currentColor" stroke-width="2"/>
          </svg>
        </div>
        <h2>Review & Accept</h2>
        <p>Please review each section carefully. You must scroll through the full documents before confirming acceptance. All checkboxes must be selected before continuing.</p>
        <div class="scroll-instruction">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 5v14M5 12l7 7 7-7" stroke="currentColor" stroke-width="2"/>
          </svg>
          Scroll through each document to enable its checkbox.
        </div>
      </div>

      <div class="consent-content">
        <!-- Legal Agreements Card -->
        <div class="consent-card">
          <div class="card-header">
            <h3>Legal Agreements</h3>
            <p>Please review both documents completely</p>
          </div>

          <!-- EULA Section -->
          <div class="document-section">
            <div class="document-header" @click="toggleDocument('eula')">
              <h4>End User Licensing Agreement (EULA)</h4>
              <svg :class="{ rotated: expandedSections.eula }" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <polyline points="6 9 12 15 18 9" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            
            <div v-if="expandedSections.eula" class="document-content">
              <div class="document-text" @scroll="onDocumentScroll('eula', $event)" ref="eulaScrollArea">
                
                <h6>END USER LICENSE AGREEMENT (EULA)</h6>
                
                <p>This End User License Agreement ("Agreement" or "EULA") is a legally binding contract between:</p>
                
                <p><strong>Licensor:</strong> Vardaan Data Sciences Pvt. Ltd., a company incorporated under the Companies Act, 2013, with its registered office in Hyderabad, Telangana, India ("Vardaan").</p>
                
                <p><strong>AND</strong></p>
                
                <p><strong>Licensee:</strong> The individual or legal entity identified in the purchase documentation who has acquired the right to use the Software under this Agreement ("Customer").</p>
                
                <p>This Agreement governs the use of the RiskaVaire governance, risk, and compliance (GRC) software platform and associated services. By installing, accessing, or using the Software, the Customer acknowledges that they have read, understood, and agreed to all the terms herein.</p>
                
                <p>This Agreement becomes effective as of the date the Customer accepts it, either by electronic acceptance or by signing it physically ("Effective Date").</p>
                
                <h6>1. Definitions</h6>
                <p>For the purposes of this Agreement, the following terms shall have the meanings assigned below:</p>
                
                <p><strong>Software:</strong> The RiskaVaire GRC software platform developed by Vardaan, including all its components, modules, updates, patches, enhancements, compliance templates, documentation, and associated technology delivered under this Agreement.</p>
                
                <p><strong>Customer:</strong> The individual or organization that has lawfully purchased or otherwise acquired a license to use the Software under this Agreement.</p>
                
                <p><strong>License Term:</strong> The fixed period for which the Software is licensed to the Customer, as stated in the relevant invoice, order form, or purchase document.</p>
                
                <p><strong>Renewal Date:</strong> The date on which the License Term is extended for a further period upon mutual confirmation and payment of applicable fees.</p>
                
                <p><strong>Subscription Plan:</strong> The level of service and support chosen by the Customer (e.g., Basic, Professional, Premium), determining the nature and scope of assistance, features, and response times.</p>
                
                <p><strong>Confidential Information:</strong> All non-public information disclosed by one party to the other, including business strategies, trade secrets, risk assessment methods, compliance templates, customer lists, and technical data.</p>
                
                <p><strong>GRC Data:</strong> All governance, risk, compliance, audit, control, and related information processed, stored, or managed in the Software by the Customer.</p>
                
                <h6>2. Third-Party Involvement and Reseller Obligations</h6>
                <p>If a reseller is involved in facilitating the sale or deployment of the Software, their name must be explicitly stated in the sales agreement.</p>
                
                <p>The reseller must enter into a separate agreement with Vardaan to ensure:</p>
                <ul>
                  <li>No overselling or over-provisioning of licenses beyond agreed limits.</li>
                  <li>No unauthorized promises, guarantees, or contractual obligations are made to the Customer that contradict this EULA.</li>
                </ul>
                
                <p>In the event of a conflict between this EULA and any agreement between the reseller and Customer, this EULA shall take precedence unless expressly amended in writing by Vardaan.</p>
                
                <h6>3. Grant of License</h6>
                <p>Vardaan grants the Customer a limited, non-exclusive, non-transferable, and non-sublicensable license to use the Software strictly for internal business purposes related to GRC management.</p>
                
                <p>The license is subscription-based and issued on a per-user basis. Role-based access control may be implemented to differentiate access levels (e.g., Administrator, Auditor, Compliance Officer).</p>
                
                <p>The Software can be deployed on supported environments including cloud, on-premises, or hybrid infrastructure.</p>
                
                <p>The Customer may not reverse engineer, decompile, disassemble, or otherwise attempt to derive source code, nor circumvent licensing or security mechanisms.</p>
                
                <h6>4. Scope of Use and Prohibited Activities</h6>
                <p>The Software may be used only by employees or authorized contractors of the Customer, and only for legitimate GRC functions such as compliance monitoring, audit tracking, and policy management.</p>
                
                <p>The following activities are strictly prohibited:</p>
                <ul>
                  <li>Sharing the Software with unauthorized third parties.</li>
                  <li>Using the Software for personal or non-business purposes.</li>
                  <li>Deploying the Software in managed service environments for third parties without written consent.</li>
                </ul>
                
                <p><strong>Security Breach & Tampering Penalty:</strong> Any fraudulent use, including duplication of licenses, circumvention of usage restrictions, hacking, or exploitation of vulnerabilities, will result in immediate license termination, forfeiture of all fees paid, a penalty of up to 10 times the gross license value before discounts, and legal proceedings (civil and/or criminal).</p>
                
                <h6>5. Confidentiality</h6>
                <p>Each party shall maintain the strict confidentiality of all Confidential Information disclosed during the course of this Agreement.</p>
                
                <p>Confidential Information may only be used to perform obligations under this Agreement and may not be disclosed to third parties without prior written consent.</p>
                
                <p><strong>Exceptions:</strong> Confidential Information does not include information that is publicly available, lawfully obtained from a third party, already known prior to disclosure, or independently developed without reference to the disclosing party's data.</p>
                
                <p>Confidentiality obligations survive for five (5) years after the termination or expiry of this Agreement.</p>
                
                <h6>6. Payment Terms</h6>
                <p>All fees must be paid in full to Vardaan's designated bank account via approved methods (bank transfer, cheque).</p>
                
                <p>Licenses will only be activated after full payment is received.</p>
                
                <p>Partial payments, post-dated cheques, or informal confirmations do not qualify as payment.</p>
                
                <p>Failure to pay in accordance with agreed terms is a material breach of this Agreement.</p>
                
                <p>In cases involving resellers, the reseller is fully responsible for collecting and remitting license fees to Vardaan.</p>
                
                <h6>7. Grace Period Post Expiry</h6>
                <p>If the Customer does not renew their license before the expiry date, a grace period of seven (7) calendar days will be provided.</p>
                
                <p>During this grace period, access to the Software will continue.</p>
                
                <p>If payment is not received by the end of this period, access will be revoked automatically and without further notice.</p>
                
                <p>Vardaan shall not be responsible for any data loss, operational impact, or business disruption resulting from such termination.</p>
                
                <h6>8. Return and Refund Policy</h6>
                <p>Licenses, once issued, are non-refundable and non-returnable.</p>
                
                <p>No refunds or credits will be provided for unused portions of a license term.</p>
                
                <p>The Customer must evaluate and confirm the suitability of the Software for their needs prior to purchase.</p>
                
                <h6>9. Intellectual Property and Ownership</h6>
                <p>The Software, including its source code, features, algorithms, compliance frameworks, and documentation, remains the exclusive intellectual property of Vardaan.</p>
                
                <p>Purchasing a license grants only a right to use the Software; no ownership rights are transferred.</p>
                
                <p>All Customer GRC Data remains the Customer's property. However, any feedback, suggestions, or enhancement ideas provided by the Customer may be incorporated into future versions of the Software and will become the sole property of Vardaan.</p>
                
                <h6>10. Software Restrictions and Audit Rights</h6>
                <p>The Customer must not:</p>
                <ul>
                  <li>Modify, copy, reverse engineer, or tamper with the Software.</li>
                  <li>Misuse APIs or create unauthorized integrations.</li>
                  <li>Export GRC data in insecure or non-compliant formats.</li>
                </ul>
                
                <p>Vardaan reserves the right to audit Customer usage to ensure compliance. Audits may include requesting system logs, user activity reports, or conducting remote/on-site inspections with reasonable notice.</p>
                
                <p>If significant violations are found, the Customer must correct them within 10 business days and will bear the full cost of the audit.</p>
                
                <h6>11. Support, Updates, and Product Changes</h6>
                <p>Support will be provided according to the Customer's chosen Subscription Plan:</p>
                <ul>
                  <li><strong>Basic:</strong> Email/chat support for GRC queries.</li>
                  <li><strong>Professional:</strong> Dedicated GRC consultant access.</li>
                  <li><strong>Premium:</strong> Priority response times, account management, and advisory services.</li>
                </ul>
                
                <p>Vardaan may issue updates, patches, or upgrades to maintain security and compliance. These may be mandatory for continued usage.</p>
                
                <p>Features may be changed, improved, or discontinued with reasonable advance notice.</p>
                
                <h6>12. Limitation of Liability</h6>
                <p>To the fullest extent permitted by law, Vardaan is not liable for any direct, indirect, incidental, consequential, punitive, or special damages arising from the use of the Software.</p>
                
                <p>The Customer acknowledges that all decisions based on data or recommendations from the Software are their sole responsibility.</p>
                
                <p>The Software is provided "as is" without any warranties, express or implied, including warranties of merchantability or fitness for a particular purpose.</p>
                
                <h6>13. Data Access, Hosting, and Security Compliance</h6>
                <p>Customer GRC Data will be hosted in the geographic region specified at purchase.</p>
                
                <p>Vardaan will not access Customer data unless explicitly granted temporary credentials for support purposes.</p>
                
                <p>The Customer is responsible for ensuring compliance with applicable data protection laws (e.g., GDPR, HIPAA) and for implementing necessary security controls.</p>
                
                <p>Both parties shall employ industry-standard encryption for data storage and transfer, and promptly report any security incident involving Customer data.</p>
                
                <h6>14. Mutual Indemnification</h6>
                <p><strong>Customer Indemnification:</strong> The Customer shall indemnify, defend, and hold harmless Vardaan, its officers, directors, employees, agents, and affiliates from and against any and all claims, damages, losses, liabilities, costs, and expenses (including reasonable attorneys' fees) arising from:</p>
                <ul>
                  <li>The Customer's misuse of the Software;</li>
                  <li>Any violation of applicable laws or regulations by the Customer;</li>
                  <li>Any breach of this Agreement by the Customer;</li>
                  <li>Any third-party claim alleging that the Customer's GRC Data, configurations, or integrations infringe such third party's intellectual property rights or other rights.</li>
                </ul>
                
                <p><strong>Vardaan Indemnification:</strong> Vardaan shall indemnify, defend, and hold harmless the Customer, its officers, directors, employees, agents, and affiliates from and against any and all claims, damages, losses, liabilities, costs, and expenses (including reasonable attorneys' fees) arising from:</p>
                <ul>
                  <li>Any third-party claim alleging that the unmodified Software (as provided by Vardaan) infringes or misappropriates such third party's intellectual property rights;</li>
                  <li>Any gross negligence or willful misconduct by Vardaan in the performance of its obligations under this Agreement.</li>
                </ul>
                
                <p><strong>Indemnification Conditions:</strong></p>
                <ul>
                  <li>The indemnified party must promptly notify the indemnifying party of any claim in writing;</li>
                  <li>The indemnifying party shall have sole control of the defense and settlement of the claim, provided that such settlement does not impose any admission of liability or financial obligation on the indemnified party without its prior written consent;</li>
                  <li>The indemnified party shall provide reasonable assistance, at the indemnifying party's expense, in defending the claim.</li>
                </ul>
                
                <p><strong>Limitations on Vardaan's IP Indemnity Obligations:</strong> Vardaan shall have no obligation under Clause 14.2 if the claim arises from:</p>
                <ul>
                  <li>Use of the Software in combination with any hardware, software, or data not supplied by Vardaan, where the claim would not have arisen but for such combination;</li>
                  <li>Modification of the Software by anyone other than Vardaan or its authorized representatives;</li>
                  <li>Use of the Software after Vardaan has provided a non-infringing substitute or modification.</li>
                </ul>
                
                <p><strong>Remedies for IP Infringement:</strong> If the Software is found or believed by Vardaan to infringe third-party rights, Vardaan may, at its sole option and expense:</p>
                <ul>
                  <li>Modify the Software so that it becomes non-infringing;</li>
                  <li>Replace the Software with non-infringing software of substantially similar functionality; or</li>
                  <li>Terminate the affected licenses and refund the unused portion of prepaid license fees.</li>
                </ul>
                
                <h6>15. Dispute Resolution and Governing Law</h6>
                <p>This Agreement is governed by the laws of India.</p>
                
                <p>All disputes shall be subject to the exclusive jurisdiction of the courts at Hyderabad, Telangana.</p>
                
                <p>Vardaan may, at its discretion, choose arbitration under the Arbitration and Conciliation Act, 1996, with Hyderabad as the seat.</p>
                
                <h6>16. Termination and Suspension Rights</h6>
                <p>Upon termination of the Agreement, Customer data will be securely retained for 12 months, after which it will be permanently deleted unless otherwise agreed in writing.</p>
                
                <p>The Customer is liable for all fees up to the date of termination.</p>
                
                <p>Vardaan may immediately suspend access in cases of payment default, suspected breach, or security threats, and reinstate access only after resolution.</p>
                
                <h6>17. Technology and Policy Impacts</h6>
                <p>If government regulations or compliance standards require functional changes, Vardaan will implement them but is not liable for resulting business impacts.</p>
                
                <p>A 12-month advance notice will be given before discontinuing the Software, along with assistance for data migration.</p>
                
                <h6>18. Revisions, Upgrades, and Versioning</h6>
                <p>Vardaan may release new versions or security updates to improve performance or address vulnerabilities.</p>
                
                <p>Certain upgrades may be mandatory for continued use of the Software.</p>
                
                <h6>19. Non-Solicitation</h6>
                <p>The Customer shall not solicit, hire, or attempt to hire any Vardaan employee or contractor involved with the Software during the license term and for 12 months thereafter, without Vardaan's written consent.</p>
                
                <h6>20. Miscellaneous Provisions</h6>
                <p><strong>Entire Agreement:</strong> This Agreement constitutes the entire understanding between the parties.</p>
                
                <p><strong>Amendments:</strong> Any amendment must be in writing and signed by both parties.</p>
                
                <p><strong>Severability:</strong> If any provision is invalid, the remaining provisions remain in effect.</p>
                
                <p><strong>Assignment:</strong> Neither party may assign this Agreement without written consent, except to a successor entity.</p>
                
                <p><strong>Force Majeure:</strong> Neither party shall be liable for failure to perform due to events beyond reasonable control.</p>
                
                <p><strong>Notices:</strong> All notices must be in writing and are deemed delivered upon receipt.</p>
                
                <p><strong>Survival:</strong> Provisions intended to survive termination will remain in force.</p>
                
                <p><strong>Governing Priority:</strong> In the event of a conflict between this EULA and any purchase order, proposal, or agreement, this EULA prevails unless amended in writing by Vardaan.</p>
                
                <h6>IN WITNESS WHEREOF, the Parties have executed this Agreement as of the Effective Date.</h6>
                
                <p><strong>For Vardaan Data Sciences Pvt. Ltd.</strong></p>
                <p>Authorized Signatory: ___________________</p>
                <p>Designation: __________________________</p>
                <p>Date: _________________________________</p>
                
                <p><strong>For Customer</strong></p>
                <p>Signature: _____________________________</p>
                <p>Name: __________________________________</p>
                <p>Designation: ____________________________</p>
                <p>Date: __________________________________</p>
                
                <p><em>By checking the box below, you confirm you have read and agree to this End User License Agreement.</em></p>
              </div>
              
              <div class="checkbox-section">
                                 <label class="checkbox-container" :class="{ disabled: !scrollStatus.eula }">
                   <input 
                     type="checkbox" 
                     v-model="agreements.eula" 
                     :disabled="!scrollStatus.eula"
                     @change="updateCheckboxStatus"
                   >
                   <span class="checkmark"></span>
                   I confirm I have read and agree to the End User Licensing Agreement.
                   <span v-if="!scrollStatus.eula" class="scroll-hint">(Please scroll to the end first)</span>
                 </label>
               </div>
               
               <div class="document-actions">
                 <button type="button" class="download-btn" @click="downloadDocument('eula')">
                   <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                     <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" stroke-width="2"/>
                     <polyline points="7 10 12 15 17 10" stroke="currentColor" stroke-width="2"/>
                     <line x1="12" y1="15" x2="12" y2="3" stroke="currentColor" stroke-width="2"/>
                   </svg>
                   Download Document
                 </button>
               </div>
            </div>
          </div>

          <!-- Privacy Policy Section -->
          <div class="document-section">
            <div class="document-header" @click="toggleDocument('privacy')">
              <h4>Privacy & Security Policy</h4>
              <svg :class="{ rotated: expandedSections.privacy }" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <polyline points="6 9 12 15 18 9" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            
            <div v-if="expandedSections.privacy" class="document-content">
              <div class="document-text" @scroll="onDocumentScroll('privacy', $event)" ref="privacyScrollArea">
                
                <h6>Privacy and Security Policy</h6>
                
                <h6>RiskaVaire GRC Platform</h6>
                
                <p><strong>Company:</strong> Vardaan Data Sciences PVT LTD</p>
                <p><strong>Product:</strong> RiskaVaire - Governance, Risk & Compliance Platform</p>
                <p><strong>Address:</strong> Aurum, 1st Floor, Plot No 57, Jayabheri Enclave, Gachibowli Hyderabad-500032 INDIA</p>
                <p><strong>Email:</strong> info@vardaanglobal.com</p>
                <p><strong>Phone:</strong> +91 40-35171118, +91 40-35171119</p>
                <p><strong>Effective Date:</strong> 25/08/2025</p>
                <p><strong>Version:</strong> 1.0</p>
                
                <h6>1. Introduction and Scope</h6>
                <p>This Privacy and Security Policy governs the collection, use, processing, storage, and protection of personal and organizational data within the RiskaVaire Governance, Risk & Compliance (GRC) platform. This policy applies to all users, administrators, and stakeholders who access or interact with the RiskaVaire system.</p>
                <p><strong>Scope:</strong> This policy covers all data processed through RiskaVaire modules including Policy Management, Compliance Management, Audit Management, Incident Management, and Risk Management functionalities.</p>
                
                <h6>2. Data Collection and Processing</h6>
                
                <p><strong>2.1 Types of Data Collected</strong></p>
                
                <p><strong>Personal Data:</strong></p>
                <ul>
                  <li>User account information (username, email, phone number)</li>
                  <li>Professional information (department, business unit, role, location)</li>
                  <li>Authentication credentials and Multi-Factor Authentication data</li>
                  <li>User activity logs and system interaction records</li>
                </ul>
                
                <p><strong>Organizational Data:</strong></p>
                <ul>
                  <li>Policy documents and frameworks</li>
                  <li>Compliance records and audit findings</li>
                  <li>Incident reports and risk assessments</li>
                  <li>Business unit and departmental information</li>
                  <li>Financial impact assessments and cost analyses</li>
                </ul>
                
                <p><strong>2.2 Data Collection Methods</strong></p>
                <p>Data is collected through:</p>
                <ul>
                  <li>User registration and profile management</li>
                  <li>Document uploads and AI-assisted content extraction</li>
                  <li>System-generated logs and automated data capture</li>
                  <li>Manual data entry through forms and interfaces</li>
                  <li>Integration with external systems and frameworks</li>
                </ul>
                
                <p><strong>2.3 Legal Basis for Processing</strong></p>
                <p>Data processing is conducted based on:</p>
                <ul>
                  <li>Contractual necessity for service provision</li>
                  <li>Legitimate business interests in GRC management</li>
                  <li>Compliance with legal and regulatory obligations</li>
                  <li>User consent where explicitly provided</li>
                </ul>
                
                <h6>3. Data Security Measures</h6>
                
                <p><strong>3.1 Technical Safeguards</strong></p>
                
                <p><strong>Access Controls:</strong></p>
                <ul>
                  <li>Role-based access control with 22 predefined roles and customizable permissions</li>
                  <li>Multi-Factor Authentication (MFA) for enhanced security</li>
                  <li>Least-privilege access principles across all modules</li>
                </ul>
                
                <p><strong>Data Protection:</strong></p>
                <ul>
                  <li>End-to-end encryption for data in transit and at rest</li>
                  <li>Secure API endpoints with authentication tokens</li>
                  <li>Regular security patches and system updates</li>
                </ul>
                
                <p><strong>System Security:</strong></p>
                <ul>
                  <li>Network segmentation and firewall protection</li>
                  <li>Intrusion detection and prevention systems</li>
                  <li>Regular vulnerability assessments and penetration testing</li>
                  <li>Security monitoring and incident response capabilities</li>
                </ul>
                
                <p><strong>3.2 Operational Safeguards</strong></p>
                
                <p><strong>Access Management:</strong></p>
                <ul>
                  <li>Regular access reviews and privilege audits</li>
                  <li>Segregation of duties for sensitive operations</li>
                  <li>Audit trails for all user activities and data modifications</li>
                </ul>
                
                <p><strong>Data Handling:</strong></p>
                <ul>
                  <li>Secure data transmission protocols</li>
                  <li>Controlled data export and download functions</li>
                  <li>Data anonymization and pseudonymization where applicable</li>
                  <li>Secure deletion procedures for obsolete data</li>
                </ul>
                
                <h6>4. Data Retention and Disposal</h6>
                
                <p><strong>4.1 Retention Periods</strong></p>
                <p><strong>User Account Data:</strong> Retained for the duration of active subscription and more years as mentioned in the End user licensing agreement</p>
                <p><strong>Policy and Compliance Data, System Logs, Incident Reports, Audit Records:</strong> Retained per regulatory requirements and organizational policies</p>
                
                <p><strong>4.2 Secure Disposal</strong></p>
                <p>Data disposal includes:</p>
                <ul>
                  <li>Secure deletion using industry-standard methods</li>
                  <li>Certificate of destruction for physical media</li>
                  <li>Verification of complete data removal</li>
                  <li>Documentation of disposal activities</li>
                </ul>
                
                <h6>5. User Rights and Controls</h6>
                
                <p><strong>5.1 Data Subject Rights</strong></p>
                <p>Users have the right to:</p>
                <ul>
                  <li>Access their personal data and processing activities</li>
                  <li>Rectify inaccurate or incomplete information</li>
                  <li>Request data portability in standard formats</li>
                  <li>Withdraw consent where applicable</li>
                  <li>Lodge complaints with supervisory authorities</li>
                </ul>
                
                <p><strong>5.2 User Controls</strong></p>
                
                <p><strong>Profile Management:</strong></p>
                <ul>
                  <li>Update personal and business information</li>
                  <li>Manage notification preferences (email, WhatsApp, platform alerts)</li>
                  <li>Change passwords with email verification</li>
                  <li>Request role changes through approval workflows</li>
                </ul>
                
                <p><strong>Data Access:</strong></p>
                <ul>
                  <li>View personal data through profile sections</li>
                  <li>Download reports and documents as permitted by role</li>
                  <li>Access audit trails of personal data processing</li>
                </ul>
                
                <h6>6. Third-Party Integrations and Sharing</h6>
                
                <p><strong>6.1 Data Sharing</strong></p>
                <p>Data may be shared with:</p>
                <ul>
                  <li>Authorized third-party service providers for platform functionality</li>
                  <li>External auditors as required for compliance verification</li>
                  <li>Regulatory bodies as mandated by law</li>
                  <li>Business partners with explicit user consent</li>
                </ul>
                
                <p><strong>6.2 Third-Party Security</strong></p>
                <p>All third-party integrations must:</p>
                <ul>
                  <li>Maintain equivalent security standards</li>
                  <li>Sign data processing agreements</li>
                  <li>Undergo regular security assessments</li>
                  <li>Provide transparency in data handling practices</li>
                </ul>
                
                <h6>7. Incident Management and Breach Response</h6>
                
                <p><strong>7.1 Security Incident Response</strong></p>
                <p>In case of security incidents:</p>
                <ul>
                  <li>Immediate containment and impact assessment</li>
                  <li>Notification to affected users within 72 hours</li>
                  <li>Regulatory reporting as required by law</li>
                  <li>Forensic investigation and remediation measures</li>
                  <li>Post-incident review and system improvements</li>
                </ul>
                
                <p><strong>7.2 Data Breach Procedures</strong></p>
                <p><strong>Detection:</strong> Automated monitoring and manual reporting mechanisms</p>
                <p><strong>Assessment:</strong> Impact evaluation and risk classification</p>
                <p><strong>Containment:</strong> Immediate steps to prevent further data exposure</p>
                <p><strong>Notification:</strong> Timely communication to users and authorities</p>
                <p><strong>Recovery:</strong> System restoration and security enhancement</p>
                
                <h6>8. AI and Automated Processing</h6>
                
                <p><strong>8.1 AI Data Processing</strong></p>
                <p>The RiskaVaire platform uses AI for:</p>
                <ul>
                  <li>Automated policy and framework content extraction</li>
                  <li>Risk analysis and predictive assessments</li>
                  <li>Compliance gap identification</li>
                  <li>Incident impact analysis and mitigation suggestions</li>
                </ul>
                
                <p><strong>8.2 AI Governance</strong></p>
                <ul>
                  <li>Transparency in AI decision-making processes</li>
                  <li>Human oversight for critical determinations</li>
                  <li>Regular algorithm auditing and bias testing</li>
                  <li>User notification of automated processing activities</li>
                </ul>
                
                <h6>9. International Data Transfers</h6>
                
                <p><strong>9.1 Cross-Border Transfers</strong></p>
                <p>When data is transferred internationally:</p>
                <ul>
                  <li>Adequate protection measures are implemented</li>
                  <li>Standard Contractual Clauses (SCCs) are executed</li>
                  <li>Data localization requirements are respected</li>
                  <li>Users are informed of transfer destinations and safeguards</li>
                </ul>
                
                <p><strong>9.2 Data Sovereignty</strong></p>
                <ul>
                  <li>Data residency options based on customer requirements</li>
                  <li>Compliance with local data protection laws</li>
                  <li>Regular assessment of international transfer mechanisms</li>
                </ul>
                
                <h6>10. Training and Awareness</h6>
                
                <p><strong>10.1 Staff Training</strong></p>
                <p>All personnel receive:</p>
                <ul>
                  <li>Initial privacy and security training</li>
                  <li>Regular updates on policy changes</li>
                  <li>Role-specific security awareness sessions</li>
                  <li>Incident response training and exercises</li>
                </ul>
                
                <p><strong>10.2 User Education</strong></p>
                <p>Users are provided with:</p>
                <ul>
                  <li>Privacy policy explanations and guides</li>
                  <li>Regular security awareness communications</li>
                  <li>Self-service privacy management tools</li>
                </ul>
                
                <h6>11. Contact Information and Complaints</h6>
                
                <p><strong>11.1 Data Protection Officer</strong></p>
                <p>For privacy-related inquiries:</p>
                <ul>
                  <li><strong>Email:</strong> info@vardaanglobal.com</li>
                  <li><strong>Phone:</strong> +91 40-35171118</li>
                  <li><strong>Address:</strong> Aurum, 1st Floor, Plot No 57, Jayabheri Enclave, Gachibowli Hyderabad-500032 INDIA</li>
                </ul>
                
                <p><strong>11.2 Complaint Resolution</strong></p>
                <p>Users may:</p>
                <ul>
                  <li>Contact our Data Protection Officer directly</li>
                  <li>Use the platform's built-in support features</li>
                  <li>Escalate to relevant supervisory authorities</li>
                  <li>Seek legal remedies as provided by applicable law</li>
                </ul>
                
                <h6>12. Policy Updates and Notifications</h6>
                
                <p><strong>12.1 Policy Changes</strong></p>
                <ul>
                  <li>Material changes require 30 days advance notice</li>
                  <li>Users will be notified through email and platform notifications</li>
                  <li>Continued use constitutes acceptance of updated terms</li>
                  <li>Previous versions maintained for reference</li>
                </ul>
                
                <p><strong>12.2 Regular Review</strong></p>
                <p>This policy is reviewed:</p>
                <ul>
                  <li>Annually or as required by regulatory changes</li>
                  <li>Following significant security incidents</li>
                  <li>Upon major platform updates or feature additions</li>
                  <li>Based on user feedback and compliance requirements</li>
                </ul>
                
                <h6>13. Regulatory Compliance</h6>
                
                <p><strong>13.1 Applicable Laws</strong></p>
                <p>This policy ensures compliance with:</p>
                <ul>
                  <li>Information Technology (Reasonable Security Practices and Procedures and Sensitive Personal Data or Information) Rules, 2011</li>
                  <li>Personal Data Protection Bill (when enacted)</li>
                  <li>General Data Protection Regulation (GDPR) for EU users</li>
                  <li>Other applicable international privacy laws</li>
                </ul>
                
                <h6>14. Law Enforcement and Government Requests</h6>
                
                <p><strong>14.1 Compliance with Legal Requests</strong></p>
                <p>We may disclose personal or organizational data to law enforcement authorities, regulatory bodies, or government agencies when required by applicable law, regulation, legal process, or enforceable governmental request.</p>
                
                <p><strong>14.2 Safeguards and Transparency</strong></p>
                <p>Where legally permissible, we will notify affected users or organizations of such requests prior to disclosure. We will ensure that any disclosure is limited to the minimum information necessary to comply with the request.</p>
                
                <p><strong>14.3 Challenging Unlawful Requests</strong></p>
                <p>If we reasonably believe that a request for information is unlawful, overbroad, or not properly authorized, we reserve the right to challenge or refuse such requests, to the extent permitted by law.</p>
                
                <h6>15. Liability and Limitations</h6>
                
                <p><strong>15.1 Platform Responsibility</strong></p>
                <p>We implement industry-standard technical and organizational measures to protect data. However, no system can be guaranteed to be completely secure.</p>
                
                <p><strong>15.2 User Responsibilities</strong></p>
                <p>Users are responsible for:</p>
                <ul>
                  <li>Maintaining the confidentiality of their login credentials and authentication methods.</li>
                  <li>Ensuring accuracy and legality of the data they upload or process through the platform.</li>
                  <li>Using the platform in compliance with applicable laws and organizational policies.</li>
                </ul>
                
                <p><strong>15.3 Limitations of Liability</strong></p>
                <p>To the maximum extent permitted by applicable law, Vardaan Data Sciences Pvt. Ltd. shall not be held liable for:</p>
                <ul>
                  <li>Loss or damage resulting from unauthorized access due to user negligence (e.g., weak passwords, sharing credentials).</li>
                  <li>Incidents or breaches caused by third-party integrations, applications, or services not under our direct control.</li>
                  <li>Indirect, incidental, or consequential damages arising from the use or inability to use the platform.</li>
                </ul>
                
                <h6>16. Governing Law and Jurisdiction</h6>
                
                <p><strong>16.1 Applicable Law</strong></p>
                <p>This Privacy and Security Policy shall be governed by and construed in accordance with the laws of India, without regard to its conflict of laws principles.</p>
                
                <p><strong>16.2 Dispute Resolution</strong></p>
                <p>Any disputes, controversies, or claims arising from or relating to this Policy shall first be attempted to be resolved amicably through good-faith negotiations.</p>
                
                <p><strong>16.3 Jurisdiction</strong></p>
                <p>In the event that disputes cannot be resolved amicably, they shall be subject to the exclusive jurisdiction of the competent courts located in Hyderabad, Telangana, India.</p>
                
                <p><strong>Acknowledgment:</strong> By using the RiskaVaire platform, users acknowledge that they have read, understood, and agree to be bound by this Privacy and Security Policy.</p>
                
                <p><strong>Document Control:</strong></p>
                <p><strong>Prepared by:</strong> Vardaan Data Sciences Legal and Compliance Team</p>
                <p><strong>Approved by:</strong> Chief Privacy Officer</p>
                <p><strong>Distribution:</strong> All RiskaVaire Users and Stakeholders</p>
                
                <p><em>By checking the box below, you confirm you have read and agree to this Privacy & Security Policy.</em></p>
              </div>
              
              <div class="checkbox-section">
                                 <label class="checkbox-container" :class="{ disabled: !scrollStatus.privacy }">
                   <input 
                     type="checkbox" 
                     v-model="agreements.privacy" 
                     :disabled="!scrollStatus.privacy"
                     @change="updateCheckboxStatus"
                   >
                   <span class="checkmark"></span>
                   I confirm I have read and agree to the Privacy & Security Policy.
                   <span v-if="!scrollStatus.privacy" class="scroll-hint">(Please scroll to the end first)</span>
                 </label>
               </div>
               
               <div class="document-actions">
                 <button type="button" class="download-btn" @click="downloadDocument('privacy')">
                   <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                     <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" stroke-width="2"/>
                     <polyline points="7 10 12 15 17 10" stroke="currentColor" stroke-width="2"/>
                     <line x1="12" y1="15" x2="12" y2="3" stroke="currentColor" stroke-width="2"/>
                   </svg>
                   Download Document
                 </button>
               </div>
            </div>
          </div>
        </div>

        <!-- License Verification Card -->
        <div class="consent-card">
          <div class="card-header">
            <h3>License Verification</h3>
            <p>Your license has been verified and is active</p>
          </div>
          
          <div class="license-verification">
            <div class="license-status">
              <div class="status-icon success">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" stroke-width="2"/>
                  <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
              <div class="status-content">
                <h4>License Verified Successfully</h4>
                <p>Your RiskaVaire GRC platform license has been validated and is currently active. You may proceed with accepting the terms and conditions.</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Required Acknowledgments Card -->
        <div class="consent-card">
          <div class="card-header">
            <h3>Required Acknowledgments</h3>
            <p>Please confirm your understanding of these important points</p>
          </div>

          <div class="acknowledgments">
            <div class="acknowledgment-item">
              <label class="checkbox-container">
                <input 
                  type="checkbox" 
                  v-model="acknowledgments.dataHosting" 
                  @change="updateCheckboxStatus"
                >
                <span class="checkmark"></span>
                I understand that all application data is hosted either on my organization's server or in the designated cloud environment, and the vendor does not have access to it.
              </label>
            </div>

            <div class="acknowledgment-item">
              <label class="checkbox-container">
                <input 
                  type="checkbox" 
                  v-model="acknowledgments.backupResponsibility" 
                  @change="updateCheckboxStatus"
                >
                <span class="checkmark"></span>
                I understand that setting up and maintaining backups is my sole responsibility as the buyer/administrator.
              </label>
            </div>

            <div class="acknowledgment-item">
              <label class="checkbox-container">
                <input 
                  type="checkbox" 
                  v-model="acknowledgments.complianceResponsibility" 
                  @change="updateCheckboxStatus"
                >
                <span class="checkmark"></span>
                I understand that compliance with all applicable laws, regulations, and internal organizational policies in my jurisdiction is my responsibility.
              </label>
            </div>

            <div class="acknowledgment-item">
              <label class="checkbox-container">
                <input 
                  type="checkbox" 
                  v-model="acknowledgments.softwareLimitation" 
                  @change="updateCheckboxStatus"
                >
                <span class="checkmark"></span>
                I understand that the Software is an enabling tool and does not, by itself, guarantee compliance with any specific regulatory, legal, or industry requirements.
              </label>
            </div>

            <div class="acknowledgment-item">
              <label class="checkbox-container">
                <input 
                  type="checkbox" 
                  v-model="acknowledgments.unauthorizedSharing" 
                  @change="updateCheckboxStatus"
                >
                <span class="checkmark"></span>
                I understand that unauthorized sharing, sublicensing, or tampering with the Software is strictly prohibited and may result in immediate termination and legal action.
              </label>
            </div>

            <div class="acknowledgment-item">
              <label class="checkbox-container">
                <input 
                  type="checkbox" 
                  v-model="acknowledgments.accessRevocation" 
                  @change="updateCheckboxStatus"
                >
                <span class="checkmark"></span>
                I understand that upon non-payment or expiry of the subscription, access to the Software may be automatically revoked, and the vendor bears no responsibility for data loss or operational impact thereafter.
              </label>
            </div>
          </div>
        </div>

        <!-- Final Actions -->
        <div class="actions-section">
          <div class="actions-divider"></div>

                     <div class="final-actions">
             <button 
               type="button" 
               class="agree-btn" 
               :disabled="!allAgreed || isSubmitting"
               @click="acceptConsent"
             >
               <span v-if="!isSubmitting">
                 Agree & Continue
               </span>
               <span v-else class="loading-content">
                 <div class="spinner">
                   <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                     <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" stroke="currentColor" stroke-width="2"/>
                   </svg>
                 </div>
                 Processing...
               </span>
             </button>

             <button type="button" class="cancel-btn" @click="cancelConsent" :disabled="isSubmitting">
               <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                 <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2"/>
                 <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2"/>
               </svg>
               Cancel
             </button>

             <button type="button" class="decline-btn" @click="declineConsent" :disabled="isSubmitting">
               Decline & Logout
             </button>
           </div>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="errorMessage" class="error-alert">
        <div class="error-icon">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2"/>
            <line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" stroke-width="2"/>
          </svg>
        </div>
        <span>{{ errorMessage }}</span>
        <div class="error-close" @click="errorMessage = ''">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2"/>
            <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2"/>
          </svg>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'
import { API_BASE_URL } from '../../config/api.js'

// Props
defineProps({
  showConsent: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['consent-accepted', 'consent-declined'])

// Reactive data
const expandedSections = ref({
  eula: true,
  privacy: false
})

const agreements = ref({
  eula: false,
  privacy: false
})

const acknowledgments = ref({
  dataHosting: false,
  backupResponsibility: false,
  complianceResponsibility: false,
  softwareLimitation: false,
  unauthorizedSharing: false,
  accessRevocation: false
})

const scrollStatus = ref({
  eula: false,
  privacy: false
})

const isSubmitting = ref(false)
const errorMessage = ref('')

// Computed
const allAgreed = computed(() => {
  return agreements.value.eula && 
         agreements.value.privacy && 
         acknowledgments.value.dataHosting &&
         acknowledgments.value.backupResponsibility &&
         acknowledgments.value.complianceResponsibility &&
         acknowledgments.value.softwareLimitation &&
         acknowledgments.value.unauthorizedSharing &&
         acknowledgments.value.accessRevocation
})

// Methods
const toggleDocument = (section) => {
  expandedSections.value[section] = !expandedSections.value[section]
}

const updateCheckboxStatus = () => {
  // This method is called when checkboxes change to trigger reactivity
}

const onDocumentScroll = (docType, event) => {
  const element = event.target
  const scrollTop = element.scrollTop
  const scrollHeight = element.scrollHeight
  const clientHeight = element.clientHeight
  
  // Consider scrolled to bottom if within 10px of the bottom
  const isScrolledToBottom = scrollTop + clientHeight >= scrollHeight - 10
  
  if (isScrolledToBottom) {
    scrollStatus.value[docType] = true
  }
}

const acceptConsent = async () => {
  try {
    isSubmitting.value = true
    errorMessage.value = ''

    const token = localStorage.getItem('access_token')
    if (!token) {
      throw new Error('No access token found')
    }

    const response = await axios.post(
      `${API_BASE_URL}/api/jwt/accept-consent/`,
      {},
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    )

    if (response.data.status === 'success') {
      // Update user data in localStorage
      const userData = JSON.parse(localStorage.getItem('user') || '{}')
      userData.consent_accepted = '1'
      localStorage.setItem('user', JSON.stringify(userData))
      
      emit('consent-accepted')
    } else {
      throw new Error(response.data.message || 'Failed to accept consent')
    }
  } catch (error) {
    console.error('Error accepting consent:', error)
    errorMessage.value = error.response?.data?.message || 'Failed to accept consent. Please try again.'
  } finally {
    isSubmitting.value = false
  }
}

const declineConsent = () => {
  emit('consent-declined')
}

const cancelConsent = () => {
  // Simply close the consent form without accepting or declining
  // This allows the user to return to the login page
  emit('consent-declined')
}

const downloadDocument = (docType) => {
  try {
    const baseUrl = API_BASE_URL || 'http://localhost:8000'
    const fileUrl = `${baseUrl}/api/documents/${docType}/?download=true`
    
    // Create a temporary link element for download
    const link = document.createElement('a')
    link.href = fileUrl
    link.style.display = 'none'
    
    // Add to DOM, click, and remove
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    console.log(`📥 Downloading ${docType} document`)
  } catch (error) {
    console.error('Error downloading document:', error)
  }
}
</script>

<style scoped>
.consent-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

.consent-container {
  background: #f8f9fa;
  border-radius: 12px;
  max-width: 900px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
}

.consent-header {
  padding: 32px 32px 24px;
  background: #1e3a8a;
  color: white;
  text-align: center;
  border-radius: 12px 12px 0 0;
}

.consent-icon {
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  color: white;
}

.consent-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: white;
  margin: 0 0 8px;
}

.consent-header p {
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 16px;
  line-height: 1.5;
}

.scroll-instruction {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.1);
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.95);
}

.consent-content {
  padding: 24px 32px 32px;
}

.consent-card {
  background: white;
  border-radius: 12px;
  margin-bottom: 24px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
}

.consent-card:last-child {
  margin-bottom: 0;
}

.card-header {
  padding: 24px 24px 16px;
  border-bottom: 2px solid #e5e7eb;
  background: #6b7280;
  color: white;
  border-radius: 12px 12px 0 0;
}

.card-header h3 {
  font-size: 20px;
  font-weight: 600;
  color: white;
  margin: 0 0 8px;
}

.card-header p {
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
  font-size: 14px;
}

.document-section {
  margin: 24px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin-bottom: 16px;
}

.document-section:last-child {
  margin-bottom: 24px;
}

.document-header {
  padding: 16px 20px;
  background: #f9fafb;
  border-radius: 8px 8px 0 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: background-color 0.2s;
}

.document-header:hover {
  background: #f3f4f6;
}

.document-header h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
  flex: 1;
}

.document-header svg {
  transition: transform 0.2s;
  color: #6b7280;
}

.document-header svg.rotated {
  transform: rotate(180deg);
}

.document-content {
  padding: 20px;
  border-top: 1px solid #e5e7eb;
}

.document-text {
  margin-bottom: 20px;
  max-height: 300px;
  overflow-y: auto;
  padding-right: 8px;
  -webkit-overflow-scrolling: touch;
}

.document-text h6 {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin: 16px 0 8px;
}

.document-text h6:first-of-type {
  margin-top: 0;
}

.document-text p {
  color: #4b5563;
  line-height: 1.6;
  margin: 0 0 12px;
}

.document-text ul {
  margin: 8px 0 12px 20px;
  color: #4b5563;
  line-height: 1.6;
}

.document-text li {
  margin-bottom: 4px;
}

.checkbox-section {
  margin-bottom: 20px;
}

.checkbox-container {
  display: flex;
  align-items: flex-start;
  cursor: pointer;
  font-size: 14px;
  line-height: 1.5;
  color: #374151;
}

.checkbox-container input[type="checkbox"] {
  display: none;
}

.checkmark {
  width: 20px;
  height: 20px;
  border: 2px solid #d1d5db;
  border-radius: 4px;
  margin-right: 12px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  margin-top: 2px;
}

.checkbox-container input[type="checkbox"]:checked + .checkmark {
  background: #3b82f6;
  border-color: #3b82f6;
}

.checkbox-container input[type="checkbox"]:checked + .checkmark::after {
  content: '✓';
  color: white;
  font-weight: bold;
  font-size: 12px;
}

.checkbox-container.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.checkbox-container.disabled .checkmark {
  border-color: #d1d5db;
  background: #f3f4f6;
}

.scroll-hint {
  color: #6b7280;
  font-style: italic;
  font-size: 12px;
}

.document-actions {
  display: flex;
  gap: 12px;
}

.download-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: 1px solid #d1d5db;
  background: white;
  color: #374151;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.download-btn:hover {
  background: #f9fafb;
  border-color: #9ca3af;
}

.license-verification {
  padding: 24px;
}

.license-status {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px;
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
}

.status-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.status-icon.success {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.status-content h4 {
  font-size: 16px;
  font-weight: 600;
  color: #065f46;
  margin: 0 0 8px;
}

.status-content p {
  color: #047857;
  line-height: 1.5;
  margin: 0;
  font-size: 14px;
}

.acknowledgments {
  padding: 24px;
}

.acknowledgment-item {
  margin-bottom: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #e5e7eb;
}

.acknowledgment-item:last-child {
  margin-bottom: 0;
}

.actions-section {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
}

.actions-divider {
  height: 2px;
  background: #e5e7eb;
  margin: 0;
}

.final-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  align-items: center;
  padding: 24px;
  flex-wrap: wrap;
}

.agree-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 40px;
  background: #1e3a8a;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 16px;
  box-shadow: 0 4px 6px rgba(30, 58, 138, 0.2);
}

.agree-btn:hover:not(:disabled) {
  background: #1e40af;
  transform: translateY(-1px);
  box-shadow: 0 6px 8px rgba(30, 58, 138, 0.3);
}

.agree-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.cancel-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: #f3f4f6;
  color: #4b5563;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 16px;
}

.cancel-btn:hover:not(:disabled) {
  background: #e5e7eb;
  border-color: #9ca3af;
  color: #374151;
}

.cancel-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.decline-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 32px;
  background: transparent;
  color: #dc2626;
  border: 1px solid #fca5a5;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 16px;
}

.decline-btn:hover:not(:disabled) {
  background: #fef2f2;
  border-color: #f87171;
  color: #b91c1c;
}

.decline-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.error-alert {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  margin-top: 16px;
}

.error-icon {
  flex-shrink: 0;
}

.error-close {
  margin-left: auto;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.error-close:hover {
  background: rgba(220, 38, 38, 0.1);
}

/* Scrollbar styling for webkit browsers */
.document-text::-webkit-scrollbar {
  width: 6px;
}

.document-text::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.document-text::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.document-text::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}

.consent-container::-webkit-scrollbar {
  width: 8px;
}

.consent-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.consent-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.consent-container::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}
</style>