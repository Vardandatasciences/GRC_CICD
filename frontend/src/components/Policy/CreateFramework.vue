<template>
  <div class="create-framework-container">
    <h2>Create Framework</h2>
    
    <!-- Framework Form -->
    <div v-if="!showExtractionScreens" class="framework-form-container">
      <form class="form-section" @submit.prevent="handleFrameworkFormSubmit">
        <!-- Framework ID and Name in one row -->
        <div class="form-row">
          <div class="form-group">
            <label>Framework ID</label>
            <div class="input-wrapper">
              <input type="text" v-model="formData.frameworkId" placeholder="Enter framework id" />
            </div>
          </div>
          
          <div class="form-group">
            <label>Framework Name</label>
            <div class="input-wrapper">
              <input type="text" v-model="formData.frameworkName" placeholder="Enter framework name" />
            </div>
          </div>
        </div>
        
        <!-- Version and Upload Document in one row -->
        <div class="form-row">
          <div class="form-group">
            <label>Version</label>
            <div class="input-wrapper">
              <input type="text" v-model="formData.version" placeholder="Enter version" />
            </div>
          </div>
          
          <div class="form-group">
            <label>Upload Document</label>
            <div class="upload-input-container">
              <input type="file" id="framework-doc" class="file-input" @change="handleFileUpload" />
              <label for="framework-doc" class="upload-label">
                <span class="upload-text">Choose File</span>
              </label>
            </div>
          </div>
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label>Effective Start Date</label>
            <div class="input-wrapper">
              <input type="date" v-model="formData.effectiveStartDate" />
            </div>
          </div>
          
          <div class="form-group">
            <label>Effective End Date</label>
            <div class="input-wrapper">
              <input type="date" v-model="formData.effectiveEndDate" />
            </div>
          </div>
        </div>
        
        <div class="form-group">
          <label>Created By</label>
          <div class="input-wrapper">
            <input type="text" v-model="formData.createdBy" placeholder="Enter creator name" />
          </div>
        </div>
        
        <button class="create-btn" type="submit">Submit</button>
      </form>
    </div>

    <!-- Extraction Content (Now Inline) -->
    <div v-if="showExtractionScreens && extractionSlides.length > 0" class="extraction-inline-container">
      <div class="extraction-content">
        <div class="extraction-header">
          <!-- Stepper Navigation Bar as Tabs -->
          <div class="extraction-stepper">
            <div
              v-for="(slide, idx) in extractionSlides"
              :key="idx"
              :class="['extraction-step', { active: extractionStep === idx }]"
              @click="extractionStep = idx"
              :style="{ cursor: extractionStep !== idx ? 'pointer' : 'default' }"
            >
              {{ slide.type === 'framework' ? 'Framework' : 
                 slide.type === 'policy' ? `Policy ${slide.index !== undefined ? slide.index + 1 : ''}` : 
                 'Authorizer' }}
              <span
                class="tab-close"
                v-if="extractionStep === idx"
                @click.stop="showExtractionScreens = false"
              >
                X
              </span>
            </div>
          </div>
        </div>
        <div class="extraction-body">
          <!-- Render slide content based on type -->
          <div v-if="extractionSlides[extractionStep].type === 'framework'">
            <label>Title:</label>
            <input :value="extractionSlides[extractionStep].data.title" readonly />
            <label>Description:</label>
            <textarea :value="extractionSlides[extractionStep].data.description" readonly></textarea>
          </div>
          <div v-else-if="extractionSlides[extractionStep].type === 'policy'">
            <div class="policy-main">
              <b>Policy</b>
              <label>Title:</label>
              <input :value="extractionSlides[extractionStep].data.title" readonly />
              <label>Description:</label>
              <textarea :value="extractionSlides[extractionStep].data.description" readonly></textarea>
              <label v-if="extractionSlides[extractionStep].data.objective">Objective:</label>
              <textarea v-if="extractionSlides[extractionStep].data.objective" :value="extractionSlides[extractionStep].data.objective" readonly></textarea>
              <label v-if="extractionSlides[extractionStep].data.scope">Scope:</label>
              <textarea v-if="extractionSlides[extractionStep].data.scope" :value="extractionSlides[extractionStep].data.scope" readonly></textarea>
            </div>
            <div v-if="extractionSlides[extractionStep].data.subPolicies && extractionSlides[extractionStep].data.subPolicies.length" class="subpolicies-group">
              <div v-for="(sub, i) in extractionSlides[extractionStep].data.subPolicies" :key="i" class="subpolicy-card extraction-subpolicy">
                <b>Sub Policy {{ i + 1 }}</b>
                <label>Title:</label>
                <input :value="sub.title" readonly />
                <label>Description:</label>
                <textarea :value="sub.description" readonly></textarea>
              </div>
            </div>
          </div>
          <div v-else-if="extractionSlides[extractionStep].type === 'authorizer'">
            <label>Title:</label>
            <input :value="extractionSlides[extractionStep].data.title" readonly />
            <label>Description:</label>
            <textarea :value="extractionSlides[extractionStep].data.description" readonly></textarea>
            <label>Created By:</label>
            <input :value="extractionSlides[extractionStep].data.createdBy" readonly />
            <label>Created date:</label>
            <input :value="extractionSlides[extractionStep].data.createdDate" readonly />
            <label>Authorized By:</label>
            <input :value="extractionSlides[extractionStep].data.authorizedBy" readonly />
            <label>Assign task for authorization:</label>
            <input :value="extractionSlides[extractionStep].data.assignTask" readonly />
          </div>
          <div style="text-align: right; margin-top: 24px">
            <button
              v-if="extractionStep < extractionSlides.length - 1"
              class="create-btn"
              style="min-width: 100px"
              @click="extractionStep = extractionStep + 1"
            >
              Next &gt;
            </button>
            <button
              v-else
              class="create-btn"
              style="min-width: 100px"
              @click="handleExtractionComplete"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import frameworkSample from '../../data/frameworkSample.json'
import './CreateFramework.css'

export default {
  name: 'CreateFramework',
  props: {
    sendPushNotification: {
      type: Function,
      required: true
    }
  },
  setup(props) {
    const showExtractionScreens = ref(false)
    const extractionStep = ref(0)
    const extractionSlides = ref([])
    const formData = ref({
      frameworkId: '',
      frameworkName: '',
      version: '',
      document: null,
      effectiveStartDate: '',
      effectiveEndDate: '',
      createdBy: ''
    })

    const handleFileUpload = (event) => {
      formData.value.document = event.target.files[0]
    }

    const handleFrameworkFormSubmit = async () => {
      try {
        // Validate form data
        if (!formData.value.frameworkId || !formData.value.frameworkName || !formData.value.version) {
          await props.sendPushNotification({
            title: 'Framework Creation Failed',
            message: 'Please fill in all required fields (Framework ID, Framework Name, and Version)',
            category: 'framework',
            priority: 'high',
            user_id: formData.value.createdBy || 'default_user'
          });
          return;
        }

        if (!formData.value.document) {
          await props.sendPushNotification({
            title: 'Framework Creation Failed',
            message: 'Please upload a framework document',
            category: 'framework',
            priority: 'high',
            user_id: formData.value.createdBy || 'default_user'
          });
          return;
        }

        // Simulate framework creation process
        // In a real application, you would make an API call here
        console.log('Processing framework creation...', formData.value);

        // Send success notification
        await props.sendPushNotification({
          title: 'Framework Created Successfully',
          message: `Framework "${formData.value.frameworkName}" has been created successfully. Document processing initiated.`,
          category: 'framework',
          priority: 'medium',
          user_id: formData.value.createdBy || 'default_user'
        });

        // Build slides dynamically based on JSON structure
        const slides = []
        if (frameworkSample.framework) {
          slides.push({
            type: 'framework',
            data: frameworkSample.framework
          })
        }
        if (frameworkSample.policies && Array.isArray(frameworkSample.policies)) {
          frameworkSample.policies.forEach((policy, idx) => {
            slides.push({
              type: 'policy',
              data: policy,
              index: idx
            })
          })
        }
        if (frameworkSample.authorizer) {
          slides.push({
            type: 'authorizer',
            data: frameworkSample.authorizer
          })
        }
        extractionSlides.value = slides
        showExtractionScreens.value = true
        extractionStep.value = 0

      } catch (error) {
        console.error('Error creating framework:', error);
        await props.sendPushNotification({
          title: 'Framework Creation Failed',
          message: `Failed to create framework: ${error.message || 'Unknown error occurred'}`,
          category: 'framework',
          priority: 'high',
          user_id: formData.value.createdBy || 'default_user'
        });
      }
    }

    const handleExtractionComplete = async () => {
      try {
        // Send notification when extraction is completed
        await props.sendPushNotification({
          title: 'Framework Processing Complete',
          message: `Framework "${formData.value.frameworkName}" has been processed and extracted successfully.`,
          category: 'framework',
          priority: 'medium',
          user_id: formData.value.createdBy || 'default_user'
        });
        
        showExtractionScreens.value = false;
      } catch (error) {
        console.error('Error completing extraction:', error);
        await props.sendPushNotification({
          title: 'Framework Processing Error',
          message: `Error completing framework processing: ${error.message || 'Unknown error occurred'}`,
          category: 'framework',
          priority: 'high',
          user_id: formData.value.createdBy || 'default_user'
        });
      }
    }

    return {
      showExtractionScreens,
      extractionStep,
      extractionSlides,
      formData,
      handleFileUpload,
      handleFrameworkFormSubmit,
      handleExtractionComplete
    }
  }
}
</script> 