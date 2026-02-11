import frappe
from justyol_dashboard.services.realtime_service import push_dashboard_update
from justyol_dashboard.services.cache_service import invalidate_dashboard_cache


def on_sales_order_change(doc, method):
    """Hook called when a Sales Order is created, updated, or submitted.

    Pushes real-time updates to all connected dashboard clients and
    invalidates relevant caches.
    """
    # Invalidate cached data for this company
    invalidate_dashboard_cache(company=doc.company)

    # Push real-time event to dashboards
    push_dashboard_update(
        event_type="sales_order_update",
        data={
            "order_name": doc.name,
            "customer": doc.customer,
            "grand_total": float(doc.grand_total or 0),
            "sales_status": doc.custom_sales_status,
            "logistics_status": doc.custom_logistics_status,
            "shipment_status": doc.custom_track_shipment_status,
            "action": method,  # "after_insert", "on_update", "on_submit"
        },
        company=doc.company,
    )
