<template>
  <div class="contact-page">
    <div class="contact-container">
      <!-- Header -->
      <div class="contact-header">
        <h1 class="contact-title">
          <i class="fas fa-phone-alt"></i>
          Contact Us
        </h1>
        <p class="contact-subtitle">
          For more information and guidance please contact us
        </p>
      </div>

      <!-- Content -->
      <div class="contact-content">
        <div class="contact-grid">
          <!-- Left Column - Contact Information -->
          <div class="contact-info-section">
            <div class="contact-item">
              <div class="contact-icon">
                <i class="fas fa-envelope"></i>
              </div>
              <div class="contact-details">
                <h3>Email</h3>
                <p>info@vardaanglobal.com</p>
              </div>
            </div>
            
            <div class="contact-item">
              <div class="contact-icon">
                <i class="fas fa-phone"></i>
              </div>
              <div class="contact-details">
                <h3>Phone</h3>
                <p>+91 40-35171118</p>
                <p>+91 40-35171119</p>
              </div>
            </div>
            
            <div class="contact-item">
              <div class="contact-icon">
                <i class="fas fa-globe"></i>
              </div>
              <div class="contact-details">
                <h3>Website</h3>
                <p>https://vardaands.com</p>
              </div>
            </div>
          </div>

          <!-- Right Column - Address -->
          <div class="address-section">
            <div class="contact-item">
              <div class="contact-icon">
                <i class="fas fa-map-marker-alt"></i>
              </div>
              <div class="contact-details">
                <h3>Address</h3>
                <p>Aurum, 1st Floor, Plot No 57,</p>
                <p>Jayabheri Enclave,</p>
                <p>Gachibowli, Hyderabad - 500032,</p>
                <p>INDIA</p>
              </div>
            </div>
          </div>
        </div>
      </div>


    </div>
  </div>
</template>

<script setup>
// Contact Us component - no additional functionality needed
</script>

<style scoped>
.contact-page {
  min-height: 100vh;
  background: #ffffff;
  padding-left: 4rem;
}

.contact-container {
  max-width: 1000px;
  margin: 0 auto;
  background: white;
  overflow: hidden;
}

.contact-header {
  background: white;
  color: #1f2937;
  padding: 2rem;
  border-bottom: 1px solid #e5e7eb;
}

.contact-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.contact-subtitle {
  font-size: 0.9rem;
  opacity: 0.9;
  padding-left: 40px;
  line-height: 1.6;
}

.contact-content {
  padding: 3rem 2rem;
}

.contact-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3rem;
  align-items: start;
}

.contact-info-section,
.address-section {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.contact-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  transition: transform 0.2s, box-shadow 0.2s;
}

.contact-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.contact-icon {
  width: 35px;
  height: 35px;
  background: #3b82f6;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  flex-shrink: 0;
}

.contact-details {
  flex: 1;
}

.contact-details h3 {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.contact-details p {
  font-size: 0.9rem;
  color: #4b5563;
  margin-bottom: 0.25rem;
  line-height: 1.5;
}

.contact-details p:last-child {
  margin-bottom: 0;
}

/* Responsive Design */
@media (max-width: 768px) {
  .contact-page {
    padding: 1rem;
  }
  
  .contact-title {
    font-size: 2rem;
  }
  

  
  .contact-grid {
    grid-template-columns: 1fr;
    gap: 2rem;
  }
  
  .contact-content {
    padding: 2rem 1rem;
  }
  
  .contact-item {
    padding: 1rem;
  }
  
  .contact-icon {
    width: 40px;
    height: 40px;
    font-size: 1rem;
  }
}

@media (max-width: 480px) {
  .contact-header {
    padding: 1.5rem;
  }
  
  .contact-title {
    font-size: 1.75rem;
  }
  
  .contact-subtitle {
    font-size: 1rem;
  }
  

  
  .contact-item {
    flex-direction: column;
    text-align: center;
    gap: 0.75rem;
  }
  
  .contact-icon {
    margin: 0 auto;
  }
}
</style>
