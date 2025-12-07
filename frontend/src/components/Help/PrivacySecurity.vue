<template>
  <div class="privacy-security-page">
    <div class="privacy-security-container">
                    <!-- Header -->
       <div class="privacy-security-header">
         <h1 class="privacy-security-title">
           <i class="fas fa-shield-alt"></i>
           Privacy & Security
         </h1>
         <p class="privacy-security-subtitle">
           Learn about our data privacy practices, security measures, and how we protect your information in the RiskaVaire platform.
         </p>
       </div>

       <!-- View Document Button - Moved down and to the left -->
       <div class="privacy-security-content-section">
         <div class="download-section">
           <button class="download-button" @click="downloadPDF">
             <i class="fas fa-eye"></i>
             View Document
           </button>
         </div>
       </div>

      <!-- Content -->
      <div class="privacy-security-content">
        <!-- Data Privacy -->      
       <!-- Security Best Practices -->
        <section class="privacy-security-section">
          <h2 class="privacy-security-section-title">
            <i class="fas fa-user-secret"></i>
            Security Best Practices
          </h2>
          <div class="best-practices">
            <div class="practice-card">
              <h3>For Users</h3>
              <div class="practice-list">
                <div class="practice-item">
                  <i class="fas fa-key"></i>
                  <div>
                    <h4>Strong Passwords</h4>
                    <p>Use complex passwords with a mix of letters, numbers, and special characters. Change passwords regularly.</p>
                  </div>
                </div>
                <div class="practice-item">
                  <i class="fas fa-mobile-alt"></i>
                  <div>
                    <h4>Enable MFA</h4>
                    <p>Always enable multi-factor authentication for additional security protection.</p>
                  </div>
                </div>
                <div class="practice-item">
                  <i class="fas fa-sign-out-alt"></i>
                  <div>
                    <h4>Secure Logout</h4>
                    <p>Always log out when finished, especially on shared or public computers.</p>
                  </div>
                </div>
                <div class="practice-item">
                  <i class="fas fa-eye-slash"></i>
                  <div>
                    <h4>Be Aware</h4>
                    <p>Never share your credentials and be cautious of phishing attempts.</p>
                  </div>
                </div>
              </div>
            </div>

            <div class="practice-card">
              <h3>For Administrators</h3>
              <div class="practice-list">
                <div class="practice-item">
                  <i class="fas fa-users-cog"></i>
                  <div>
                    <h4>User Management</h4>
                    <p>Regularly review and update user access permissions. Remove access for inactive users.</p>
                  </div>
                </div>
                <div class="practice-item">
                  <i class="fas fa-chart-line"></i>
                  <div>
                    <h4>Monitor Activity</h4>
                    <p>Regularly review audit logs and system activity for suspicious behavior.</p>
                  </div>
                </div>
                <div class="practice-item">
                  <i class="fas fa-download"></i>
                  <div>
                    <h4>Regular Backups</h4>
                    <p>Ensure regular backups are performed and test recovery procedures.</p>
                  </div>
                </div>
                <div class="practice-item">
                  <i class="fas fa-graduation-cap"></i>
                  <div>
                    <h4>Security Training</h4>
                    <p>Provide regular security awareness training to all users.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

                 <!-- Contact Security Team -->
         <section class="privacy-security-section">
           <div class="security-contact">
             <h2>Security Concerns?</h2>
             <p>If you have security concerns or suspect a security incident, contact our security team immediately.</p>
             <div class="contact-boxes">
               <div class="contact-box">
                 <i class="fas fa-envelope"></i>
                 <h4>Email</h4>
                 <p>info@vardaanglobal.com</p>
               </div>
               <div class="contact-box">
                 <i class="fas fa-phone"></i>
                 <h4>Phone 1</h4>
                 <p>+91 40-35171118</p>
               </div>
               <div class="contact-box">
                 <i class="fas fa-phone"></i>
                 <h4>Phone 2</h4>
                 <p>+91 40-35171119</p>
               </div>
             </div>
           </div>
         </section>
      </div>
    </div>
  </div>
</template>

<script setup>
const downloadPDF = () => {
  const pdfUrl = '/assets/help_docs/Privacy and Security Policy1.pdf';
  window.open(pdfUrl, '_blank');
};
</script>

<style scoped>
.privacy-security-page {
  min-height: 100vh;
  background: #ffffff;
  padding: 0.6rem 2rem 2rem 240px;
}

.privacy-security-container {
  max-width: 1200px;
  margin-left: 70px;
  margin: 0 auto;
  background: white;
  overflow: hidden;
  position: relative;
}

.privacy-security-header {
  background: white;
  color: #1f2937;
  padding: 2rem;
  border-bottom: 1px solid #e5e7eb;
  text-align: left;
}

.privacy-security-header-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}

.privacy-security-breadcrumb {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
}

.privacy-security-breadcrumb-link {
  color: #6b7280;
  text-decoration: none;
  transition: color 0.2s;
}

.privacy-security-breadcrumb-link:hover {
  color: #3b82f6;
}

.privacy-security-breadcrumb-separator {
  color: #d1d5db;
  font-size: 0.75rem;
}

.privacy-security-breadcrumb-current {
  color: #1f2937;
  font-weight: 600;
}

.privacy-security-content-section {
  padding: 2rem 2rem 0 2rem;
}

.download-section {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 0;
}

.download-button {
  background-color: #3b82f6;
  color: white;
  padding: 0.6rem 0.9rem;
  border-radius: 8px;
  margin-left:45px;
  border: 1px solid #3b82f6;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  transition: background-color 0.2s, border-color 0.2s;
}

.download-button:hover {
  background-color: #2563eb;
  border-color: #2563eb;
}

.download-button i {
  color: white;
}

.privacy-security-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.privacy-security-subtitle {
  font-size: 0.9rem;
  opacity: 0.9;
  margin-left: 40px;
  line-height: 1.6;
}

.privacy-security-content {
  padding: 1rem 2rem 2rem 2rem;
}

.privacy-security-section {
  margin-bottom: 3rem;
}

.privacy-security-section-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-top: 40px;
  color: #1f2937;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.privacy-security-section-title i {
  color: #000000;
}

.privacy-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2rem;
}

.privacy-card {
  background: #f8fafc;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.privacy-card h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1rem;
}

.privacy-card p {
  color: #4b5563;
  margin-bottom: 1.5rem;
  line-height: 1.6;
}

.data-types, .data-usage, .retention-policy, .data-rights {
  margin-bottom: 1.5rem;
}

.data-types h4, .data-usage h4, .retention-policy h4, .data-rights h4 {
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.75rem;
}

.data-types ul, .data-usage ul, .retention-policy ul, .data-rights ul {
  padding-left: 1.5rem;
}

.data-types li, .data-usage li, .retention-policy li, .data-rights li {
  margin-bottom: 0.5rem;
  color: #4b5563;
}

.security-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.security-card {
  background: #f8fafc;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  text-align: center;
}

.security-icon {
  width: 60px;
  height: 60px;
  background: #3b82f6;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
  font-size: 1.5rem;
}

.security-card h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1rem;
}

.security-card p {
  color: #6b7280;
  margin-bottom: 1rem;
  line-height: 1.6;
}

.security-card ul {
  text-align: left;
  padding-left: 1.5rem;
}

.security-card li {
  margin-bottom: 0.5rem;
  color: #4b5563;
}

.compliance-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.compliance-card {
  background: #f8fafc;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.compliance-card h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1rem;
}

.certification-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.certification-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.certification-item i {
  color: #10b981;
  font-size: 1.125rem;
}

.certification-item span {
  color: #4b5563;
}

.recovery-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2rem;
}

.recovery-card {
  background: #f8fafc;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.recovery-card h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1rem;
}

.recovery-card p {
  color: #4b5563;
  margin-bottom: 1.5rem;
  line-height: 1.6;
}

.backup-details, .recovery-times, .recovery-steps {
  margin-bottom: 1.5rem;
}

.backup-details h4, .recovery-times h4, .recovery-steps h4 {
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.75rem;
}

.backup-details ul, .recovery-times ul, .recovery-steps ol {
  padding-left: 1.5rem;
}

.backup-details li, .recovery-times li, .recovery-steps li {
  margin-bottom: 0.5rem;
  color: #4b5563;
}

.best-practices {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2rem;
}

.practice-card {
  background: #f8fafc;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.practice-card h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1.5rem;
}

.practice-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.practice-item {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}

.practice-item i {
  color: #3b82f6;
  font-size: 1.25rem;
  margin-top: 0.125rem;
}

.practice-item h4 {
  font-size: 0.95rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
}

.practice-item p {
  color: #6b7280;
  line-height: 1.5;
}

.security-contact {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  padding: 2rem;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  text-align: center;
}

.security-contact h2 {
  font-size: 1.3rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1rem;
}

.security-contact p {
  color: #6b7280;
  margin-bottom: 1.5rem;
  line-height: 1.5;
}

.contact-boxes {
  display: flex;
  justify-content: center;
  gap: 1.5rem;
  flex-wrap: wrap;
  margin-top: 2rem;
}

.contact-box {
  background: white;
  padding: 1.5rem;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  text-align: center;
  min-width: 200px;
  max-width: 250px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s, box-shadow 0.2s;
}

.contact-box:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.contact-box i {
  color: #3b82f6;
  font-size: 2rem;
  margin-bottom: 0.75rem;
}

.contact-box h4 {
  font-size: 0.95rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.contact-box p {
  color: #6b7280;
  font-size: 0.8rem;
  margin: 0;
  word-break: break-word;
}

@media (max-width: 768px) {
  .privacy-security-page {
    padding: 1rem;
  }
  
  .privacy-security-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .privacy-security-content-section {
    padding: 1rem;
  }

  .download-section {
    justify-content: center;
  }

  .download-button {
    width: 100%;
    max-width: 300px;
  }

  .privacy-security-title {
    font-size: 2rem;
  }
  
  .privacy-content,
  .recovery-content,
  .best-practices {
    grid-template-columns: 1fr;
  }
  
  .security-grid,
  .compliance-grid {
    grid-template-columns: 1fr;
  }
  
  .contact-boxes {
    flex-direction: column;
    align-items: center;
  }
  
  .contact-box {
    width: 100%;
    max-width: 300px;
  }
}
</style>
