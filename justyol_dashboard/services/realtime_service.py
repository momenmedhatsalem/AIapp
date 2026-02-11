import frappe


def push_dashboard_update(event_type, data, company=None):
    """Push real-time update to dashboard clients.

    Args:
        event_type: Event name (e.g., 'sales_update', 'inventory_alert')
        data: Dict of event data
        company: Optional - only push to users viewing this company
    """
    payload = {
        "type": event_type,
        "company": company,
        "data": data,
        "timestamp": frappe.utils.now(),
    }

    frappe.publish_realtime(
        event="dashboard_update",
        message=payload,
    )


def push_to_user(user, event_type, data):
    """Push real-time update to a specific user."""
    frappe.publish_realtime(
        event="dashboard_update",
        message={"type": event_type, "data": data},
        user=user,
    )
