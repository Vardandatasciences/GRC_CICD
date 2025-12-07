import popupService, { PopupService } from './popupService';
import PopupModal from './PopupModal.vue';

const Popup = {
  install(app) {
    // Add the service to the Vue prototype
    app.config.globalProperties.$popup = popupService;
  }
};

export default Popup;
export { popupService, PopupService, PopupModal }; 
