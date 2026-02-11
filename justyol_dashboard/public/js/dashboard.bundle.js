import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";

// Global Frappe UI styles
import "frappe-ui/src/style.css";

const pinia = createPinia();

function setupDashboardApp(wrapper) {
  const app = createApp(App);
  app.use(pinia);
  app.use(router);

  // Make frappe available in all components
  app.config.globalProperties.$frappe = window.frappe;

  SetupRealtime(app);
  app.mount(wrapper.get ? wrapper.get(0) : wrapper);
  return app;
}

function SetupRealtime(app) {
  // Global realtime event bus
  if (window.frappe && window.frappe.realtime) {
    window.frappe.realtime.on("dashboard_update", (data) => {
      window.dispatchEvent(
        new CustomEvent("dashboard-update", { detail: data })
      );
    });
  }
}

// Export for Frappe page loader
window.justyol_dashboard = { setup: setupDashboardApp };
frappe.ui.setup_justyol_dashboard = setupDashboardApp;
