<template>
  <div class="feedback-page">
    <div class="feedback-container">
      <!-- Header -->
      <div class="feedback-header">
        <h1 class="feedback-title">
          <i class="fas fa-lightbulb"></i>
          Feedback
        </h1>
        <p class="feedback-subtitle">
          We value your input to make RiskaVaire more effective and user-friendly. Share your experience, report issues, or suggest new features.
        </p>
      </div>

      <!-- Content -->
      <div class="feedback-content">
        <!-- Simple Feedback Section -->
        <div class="simple-feedback-section">
          <h2>Help Us Improve</h2>
          <p>
            We value your input to make RiskaVaire more effective and user-friendly. Use the feedback form to share your experience, report issues, or suggest new features. Your feedback will be reviewed by our product team and, where relevant, integrated into our roadmap.
          </p>
          <div class="feedback-button-container">
            <button class="feedback-button" @click="openFeedbackForm">
              <i class="fas fa-comment-alt"></i>
              Share Feedback
            </button>
          </div>
        </div>

        <div class="feedback-section">
         

          


           

            

          

          <div class="feedback-info">
            <h3>What Happens Next?</h3>
            <div class="info-grid">
              <div class="info-item">
                <i class="fas fa-eye"></i>
                <h4>Review</h4>
                <p>Our team reviews all feedback within 48 hours</p>
              </div>
              <div class="info-item">
                <i class="fas fa-reply"></i>
                <h4>Response</h4>
                <p>We'll acknowledge your feedback and provide updates</p>
              </div>
              <div class="info-item">
                <i class="fas fa-road"></i>
                <h4>Roadmap</h4>
                <p>Valuable suggestions are considered for future releases</p>
              </div>
              <div class="info-item">
                <i class="fas fa-check-circle"></i>
                <h4>Implementation</h4>
                <p>Approved features are developed and released</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// Function to open feedback form in new tab
const openFeedbackForm = () => {
  window.open('https://forms.office.com/r/wGG9gwkkXN', '_blank');
};
</script>

<style scoped>
.feedback-page {
  min-height: 100vh;
  background: #ffffff;
  padding: 0.6rem 2rem 2rem 240px;
}

.feedback-container {
  max-width: 1200px;
  margin: 0 auto;
  margin-left: 10px;
  background: white;
  overflow: hidden;
}

.feedback-header {
  background: white;
  color: #1f2937;
  padding: 1.5rem 2rem 1rem;
  border-bottom: 1px solid #e5e7eb;
  text-align: left;
}

.feedback-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 1rem;
}

.feedback-subtitle {
  font-size: 0.9rem;
  opacity: 0.9;
  line-height: 1.6;
  margin-left: 40px;
  margin-bottom: 2rem;
}

.feedback-content {
  padding: 1.5rem 2rem 2rem 2rem;
}

.simple-feedback-section {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  margin-bottom: 3rem;
}

.simple-feedback-section h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1rem;
}

.simple-feedback-section p {
  font-size: 0.9rem;
  color: #4b5563;
  line-height: 1.5;
  margin-bottom: 1.5rem;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
}

.feedback-button-container {
  display: flex;
  justify-content: center;
}

.feedback-button {
  background-color: #3b82f6;
  color: white;
  padding: 0.6rem 1.1rem;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.feedback-button:hover {
  background-color: #2563eb;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.feedback-button i {
  font-size: 0.9rem;
}

.feedback-section {
  max-width: 1000px;
  margin: 0 auto;
}

.feedback-intro {
  text-align: center;
  margin-bottom: 3rem;
}

.feedback-intro h2 {
  font-size: 2rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1rem;
}

.feedback-intro p {
  font-size: 1.125rem;
  color: #6b7280;
  line-height: 1.6;
}

.feedback-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.feedback-card {
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  transition: all 0.3s ease;
}

.feedback-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  border-color: #3b82f6;
}

.feedback-icon {
  width: 60px;
  height: 60px;
  background: #3b82f6;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
  color: white;
  font-size: 1.5rem;
}

.feedback-card h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.75rem;
}

.feedback-card p {
  color: #6b7280;
  line-height: 1.5;
  font-size: 0.9rem;
}

.feedback-action {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  margin-bottom: 3rem;
}

.feedback-action h3 {
  font-size: 1.3rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1rem;
}

.feedback-action p {
  color: #6b7280;
  line-height: 1.5;
  margin-bottom: 1.5rem;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.feedback-button {
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

.feedback-button:hover {
  background: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.feedback-info {
  margin-top: 3rem;
}

.feedback-info h3 {
  font-size: 1.3rem;
  font-weight: 600;
  color: #1f2937;
  text-align: center;
  margin-bottom: 2rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.info-item {
  text-align: center;
  padding: 1.5rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.info-item i {
  font-size: 2rem;
  color: #3b82f6;
  margin-bottom: 1rem;
}

.info-item h4 {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.info-item p {
  color: #6b7280;
  line-height: 1.5;
  font-size: 0.8rem;
}

@media (max-width: 768px) {
  .feedback-page {
    padding: 1rem;
  }
  
  .feedback-header {
    padding: 1.5rem;
  }

  .feedback-content {
    padding: 1.5rem;
  }

  .feedback-title {
    font-size: 2rem;
  }
  
  .feedback-options {
    grid-template-columns: 1fr;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .feedback-action {
    padding: 1.5rem;
  }
  
  .simple-feedback-section {
    padding: 1.5rem;
  }
  
  .simple-feedback-section h2 {
    font-size: 1.25rem;
  }
  
  .simple-feedback-section p {
    font-size: 0.9375rem;
  }
  
  .feedback-button {
    width: 100%;
    max-width: 250px;
  }
}
</style>
