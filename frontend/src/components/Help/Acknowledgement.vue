ack<template>
  <div class="ack-page">
    <div class="ack-container">
      <!-- Header -->
      <div class="ack-header">
        <h1 class="ack-title">
          <i class="fas fa-handshake"></i>
          Acknowledgement
        </h1>
        <p class="ack-subtitle">
          We extend our gratitude to all contributors, partners, and stakeholders who have supported the development and success of the RiskaVaire platform.
        </p>
      </div>

             <!-- Content -->
       <div class="ack-content">
         <!-- Open Source Attribution -->
         <section class="ack-section">
           <div class="pdf-section">
             <h2 class="ack-section-title">
               <i class="fas fa-file-pdf"></i>
               Open Source Attribution
             </h2>
             <p class="pdf-description">
               This document contains detailed information about the open-source libraries, frameworks, and tools used in the development of RiskaVaire, along with their respective licenses and attributions.
             </p>
             <div class="pdf-button-container">
               <button class="view-pdf-button" @click="openPDF">
                 <i class="fas fa-eye"></i>
                 View PDF
               </button>
             </div>
           </div>
         </section>

         <!-- Development Team -->
         <section class="ack-section">
          <h2 class="ack-section-title">
            <i class="fas fa-users"></i>
            Development Team
          </h2>
          <div class="acknowledgement-grid">
            <div class="acknowledgement-card">
              <h3>Core Development</h3>
              <div class="team-list">
                <div class="team-member">
                  <i class="fas fa-code"></i>
                  <div>
                    <h4>Software Engineers</h4>
                    <p>Our dedicated team of developers who built the robust foundation of RiskaVaire with cutting-edge technologies and best practices.</p>
                  </div>
                </div>
                <div class="team-member">
                  <i class="fas fa-palette"></i>
                  <div>
                    <h4>UI/UX Designers</h4>
                    <p>Creative professionals who crafted the intuitive and user-friendly interface that makes GRC management accessible to all users.</p>
                  </div>
                </div>
                <div class="team-member">
                  <i class="fas fa-database"></i>
                  <div>
                    <h4>Data Architects</h4>
                    <p>Experts who designed the scalable and secure data infrastructure that powers our comprehensive GRC solutions.</p>
                  </div>
                </div>
              </div>
            </div>

            <div class="acknowledgement-card">
              <h3>Quality Assurance</h3>
              <div class="team-list">
                <div class="team-member">
                  <i class="fas fa-bug"></i>
                  <div>
                    <h4>QA Engineers</h4>
                    <p>Diligent testers who ensure the platform meets the highest standards of reliability, security, and performance.</p>
                  </div>
                </div>
                <div class="team-member">
                  <i class="fas fa-shield-alt"></i>
                  <div>
                    <h4>Security Specialists</h4>
                    <p>Cybersecurity experts who implemented robust security measures to protect sensitive GRC data and user information.</p>
                  </div>
                </div>
                <div class="team-member">
                  <i class="fas fa-tachometer-alt"></i>
                  <div>
                    <h4>Performance Engineers</h4>
                    <p>Specialists who optimized the platform for speed, efficiency, and seamless user experience across all devices.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Business Partners -->
        <section class="ack-section">
          <h2 class="ack-section-title">
            <i class="fas fa-handshake"></i>
            Business Partners
          </h2>
          <div class="partners-grid">
            <div class="partner-card">
              <i class="fas fa-building"></i>
              <h3>Vardaan Data Sciences</h3>
              <p>Our parent company and strategic partner who provided the vision, resources, and expertise to bring RiskaVaire to life.</p>
            </div>
            <div class="partner-card">
              <i class="fas fa-graduation-cap"></i>
              <h3>Academic Institutions</h3>
              <p>Universities and research institutions that contributed valuable insights and validation to our GRC methodologies.</p>
            </div>
            <div class="partner-card">
              <i class="fas fa-industry"></i>
              <h3>Industry Experts</h3>
              <p>GRC professionals and consultants who shared their domain expertise and real-world experience to shape our platform.</p>
            </div>
          </div>
        </section>

        <!-- Technology Stack -->
        <section class="ack-section">
          <h2 class="ack-section-title">
            <i class="fas fa-cogs"></i>
            Technology Stack
          </h2>
          <div class="tech-grid">
            <div class="tech-category">
              <h3>Frontend Technologies</h3>
              <div class="tech-list">
                <div class="tech-item">
                  <i class="fab fa-vuejs"></i>
                  <span>Vue.js</span>
                </div>
                <div class="tech-item">
                  <i class="fab fa-js"></i>
                  <span>JavaScript</span>
                </div>
                <div class="tech-item">
                  <i class="fab fa-css3-alt"></i>
                  <span>CSS3</span>
                </div>
                <div class="tech-item">
                  <i class="fab fa-html5"></i>
                  <span>HTML5</span>
                </div>
              </div>
            </div>
            <div class="tech-category">
              <h3>Backend Technologies</h3>
              <div class="tech-list">
                <div class="tech-item">
                  <i class="fab fa-python"></i>
                  <span>Python</span>
                </div>
                <div class="tech-item">
                  <i class="fab fa-node-js"></i>
                  <span>Django</span>
                </div>
                <div class="tech-item">
                  <i class="fas fa-database"></i>
                  <span>PostgreSQL</span>
                </div>
                <div class="tech-item">
                  <i class="fab fa-aws"></i>
                  <span>AWS</span>
                </div>
              </div>
            </div>
          </div>
        </section>

                 <!-- Special Thanks -->
         <section class="ack-section">
           <div class="special-thanks">
             <h2>Special Thanks</h2>
             <p>We would like to express our deepest gratitude to all our beta testers, early adopters, and customers who provided invaluable feedback and helped us refine RiskaVaire into the powerful GRC platform it is today.</p>
             <div class="thanks-highlight">
               <i class="fas fa-heart"></i>
               <p>Your trust and support drive us to continuously improve and innovate.</p>
             </div>
           </div>
         </section>
      </div>
    </div>
  </div>
</template>

<script setup>
// Component name to satisfy vue/multi-word-component-names rule
defineOptions({
  name: 'HelpAcknowledgement'
})

// Function to open the PDF file
const openPDF = () => {
  const pdfUrl = '/assets/help_docs/RiskaVaire Open-Source Attribution.pdf';
  window.open(pdfUrl, '_blank')
}
</script>

<style scoped>
.ack-page {
  min-height: 100vh;
  background: #ffffff;
  padding: 0.6rem 2rem 2rem 240px;
}

.ack-container {
  max-width: 1200px;
  margin: 0 auto;
  margin-left: 10px;
  background: white;
  overflow: hidden;
}

.ack-header {
  background: white;
  color: #1f2937;
  padding: 1.5rem 2rem 1rem;
  border-bottom: 1px solid #e5e7eb;
  text-align: left;
}

.ack-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 1rem;
}

.ack-subtitle {
  font-size: 0.9rem;
  opacity: 0.9;
  line-height: 1.6;
  margin-left: 40px;
}

.ack-content {
  padding: 1.5rem 2rem 2rem 2rem;
}

.ack-section {
  margin-bottom: 3rem;
}

.ack-section-title {
  font-size: 1.3rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.ack-section-title i {
  color: #000000;
}

.acknowledgement-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2rem;
}

.acknowledgement-card {
  background: #f8fafc;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.acknowledgement-card h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1.5rem;
}

.team-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.team-member {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}

.team-member i {
  color: #3b82f6;
  font-size: 1.25rem;
  margin-top: 0.125rem;
}

.team-member h4 {
  font-size: 0.95rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
}

.team-member p {
  color: #6b7280;
  line-height: 1.5;
}

.partners-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.partner-card {
  background: #f8fafc;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  text-align: center;
}

.partner-card i {
  color: #3b82f6;
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.partner-card h3 {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1rem;
}

.partner-card p {
  color: #6b7280;
  line-height: 1.5;
}

.tech-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
}

.tech-category {
  background: #f8fafc;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.tech-category h3 {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1.5rem;
  text-align: center;
}

.tech-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
}

.tech-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background: white;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  transition: transform 0.2s;
}

.tech-item:hover {
  transform: translateY(-2px);
}

.tech-item i {
  font-size: 2rem;
  color: #3b82f6;
}

.tech-item span {
  font-size: 0.8rem;
  font-weight: 500;
  color: #374151;
}

.special-thanks {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  padding: 2rem;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  text-align: center;
}

.special-thanks h2 {
  font-size: 1.3rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1rem;
}

.special-thanks p {
  color: #6b7280;
  margin-bottom: 1.5rem;
  line-height: 1.5;
}

.thanks-highlight {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.thanks-highlight i {
  color: #ef4444;
  font-size: 1.5rem;
}

 .thanks-highlight p {
   color: #374151;
   font-weight: 500;
   margin: 0;
 }

   /* PDF Section Styles */
  .pdf-section {
    margin-top: 2rem;
    text-align: center;
  }

  .pdf-description {
    color: #6b7280;
    line-height: 1.5;
    margin-bottom: 1.5rem;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
  }

  .pdf-button-container {
    display: flex;
    justify-content: center;
    margin-top: 1rem;
  }

  .view-pdf-button {
    background: #3b82f6;
    color: white;
    border: none;
    padding: 0.6rem 1.1rem;
    border-radius: 8px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.9rem;
  }

  .view-pdf-button:hover {
    background: #2563eb;
    transform: translateY(-1px);
  }

  .view-pdf-button:active {
    transform: translateY(0);
  }

  .view-pdf-button i {
    font-size: 0.9rem;
  }

 @media (max-width: 768px) {
  .ack-page {
    padding: 1rem;
  }
  
  .ack-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .ack-title {
    font-size: 2rem;
  }
  
  .acknowledgement-grid,
  .partners-grid,
  .tech-grid {
    grid-template-columns: 1fr;
  }
  
  .tech-list {
    grid-template-columns: repeat(2, 1fr);
  }
  
           .thanks-highlight {
        flex-direction: column;
        text-align: center;
      }
      
      .pdf-description {
        max-width: 100%;
        padding: 0 1rem;
      }
      
      .view-pdf-button {
        width: auto;
        min-width: 200px;
      }
 }
</style>
