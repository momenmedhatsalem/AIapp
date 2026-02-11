frappe.pages["justyol-hub"].on_page_load = function (wrapper) {
  frappe.ui.make_app_page({
    parent: wrapper,
    title: "Justyol Dashboard",
    single_column: true,
  });
};

frappe.pages["justyol-hub"].on_page_show = function (wrapper) {
  load_justyol_dashboard(wrapper);
};

let _app_mounted = false;

async function load_justyol_dashboard(wrapper) {
  const $parent = $(wrapper).find(".layout-main-section");

  // Only mount once — Vue Router handles subsequent navigation
  if (_app_mounted && window.__justyol_app) {
    return;
  }

  $parent.empty();

  // Create mount point
  const mountEl = $('<div id="justyol-dashboard-mount"></div>');
  $parent.append(mountEl);

  // Load CSS + JS bundles from dist
  try {
    await Promise.all([
      frappe.require("/assets/justyol_dashboard/dist/js/dashboard.bundle.js"),
      frappe.require("/assets/justyol_dashboard/dist/js/dashboard.bundle.css"),
    ]);

    if (window.justyol_dashboard && window.justyol_dashboard.setup) {
      window.__justyol_app = window.justyol_dashboard.setup(mountEl);
      _app_mounted = true;
    } else {
      console.error("Justyol Dashboard: Bundle loaded but setup function not found");
      mountEl.html(
        '<div style="padding:40px;text-align:center;color:#94a3b8;">Failed to initialize dashboard. Check console for errors.</div>'
      );
    }
  } catch (err) {
    console.error("Justyol Dashboard: Failed to load bundle", err);
    mountEl.html(
      '<div style="padding:40px;text-align:center;color:#ef4444;">Failed to load dashboard. Please refresh the page.</div>'
    );
  }
}
