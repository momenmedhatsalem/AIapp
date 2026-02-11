import frappe
import json

CACHE_TTL = 120  # 2 minutes default


def get_cached(key, compute_fn, ttl=CACHE_TTL, **kwargs):
    """Generic cache-or-compute helper.

    Args:
        key: Redis cache key
        compute_fn: Function to call if cache miss
        ttl: Cache TTL in seconds
        **kwargs: Passed to compute_fn
    """
    cached = frappe.cache().get_value(key)
    if cached:
        return cached

    result = compute_fn(**kwargs)
    frappe.cache().set_value(key, result, expires_in_sec=ttl)
    return result


def invalidate_dashboard_cache(company=None):
    """Invalidate all dashboard caches, optionally for a specific company."""
    if company:
        keys = frappe.cache().get_keys(f"dashboard:*:{company}:*")
    else:
        keys = frappe.cache().get_keys("dashboard:*")

    for key in keys:
        frappe.cache().delete_value(key)


def refresh_dashboard_cache():
    """Scheduled task: pre-compute and cache dashboard data for all companies."""
    companies = ["Justyol Morocco", "Justyol China", "Justyol Holding", "Maslak LTD"]

    for company in companies:
        try:
            # Import here to avoid circular imports
            from justyol_dashboard.api.executive import get_executive_dashboard
            get_executive_dashboard(company=company, period="today")
        except Exception as e:
            frappe.log_error(f"Cache refresh failed for {company}: {str(e)}")
