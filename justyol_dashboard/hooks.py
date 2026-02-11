app_name = "justyol_dashboard"
app_title = "Justyol Dashboard"
app_publisher = "Ahmed Badran"
app_description = "Justyol Unified Dashboard System - COD E-Commerce Operations"
app_email = "ahmed@justyol.com"
app_license = "MIT"
required_apps = ["frappe", "erpnext"]

# --- Frontend Build (Vite + Vue 3) ---
# Built with: cd apps/justyol_dashboard && npm run build
# Output: public/dist/js/dashboard.bundle.js + dashboard.bundle.css

# --- App Includes ---
# These are loaded on ALL Frappe pages (not recommended for large bundles).
# Instead, we load via frappe.require() in the Desk Page JS.
# app_include_css = "/assets/justyol_dashboard/dist/js/dashboard.bundle.css"
# app_include_js = "/assets/justyol_dashboard/dist/js/dashboard.bundle.js"

# --- Desk Page Bundle ---
# Frappe will make this available via frappe.require("dashboard.bundle.js")
page_js = {"justyol-hub": "public/dist/js/dashboard.bundle.js"}
page_css = {"justyol-hub": "public/dist/js/dashboard.bundle.css"}

# --- Real-time Events (Socket.IO) ---
# Push live updates to dashboards when Sales Orders change
doc_events = {
    "Sales Order": {
        "after_insert": "justyol_dashboard.api.realtime.on_sales_order_change",
        "on_update": "justyol_dashboard.api.realtime.on_sales_order_change",
        "on_submit": "justyol_dashboard.api.realtime.on_sales_order_change",
    }
}

# --- Scheduled Tasks ---
scheduler_events = {
    # Refresh dashboard cache every 2 minutes
    "cron": {
        "*/2 * * * *": [
            "justyol_dashboard.services.cache_service.refresh_dashboard_cache"
        ]
    },
}

# --- Jinja Methods (available in templates) ---
# jinja = {
#     "methods": [],
#     "filters": [],
# }

# --- Fixtures ---
# fixtures = []

# --- Override Whitelisted Methods ---
# override_whitelisted_methods = {}

# --- Override DocType Class ---
# override_doctype_class = {}
