import frappe
from justyol_dashboard.services.kpi_service import get_period_dates
from justyol_dashboard.services.cache_service import get_cached


@frappe.whitelist()
def get_confirmation_dashboard(company="Justyol Morocco", period="today"):
    """Single API call returning all confirmation center data."""
    dates = get_period_dates(period)
    cache_key = f"dashboard:confirmation:{company}:{dates['from']}:{dates['to']}"

    def compute():
        from_date = dates["from"]
        to_date = dates["to"] + " 23:59:59"

        # Overall confirmation KPIs
        kpis = frappe.db.sql("""
            SELECT
                COUNT(name) as total_orders,
                SUM(CASE WHEN custom_sales_status = 'Confirmed' THEN 1 ELSE 0 END) as confirmed,
                SUM(CASE WHEN custom_sales_status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled,
                SUM(CASE WHEN custom_sales_status = 'Pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN custom_sales_status = 'Draft' THEN 1 ELSE 0 END) as draft,
                SUM(CASE WHEN custom_sales_status = 'No Response' THEN 1 ELSE 0 END) as no_response
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
        """, (company, from_date, to_date), as_dict=True)[0]

        total = kpis.total_orders or 0
        confirmed = kpis.confirmed or 0
        cancelled = kpis.cancelled or 0
        pending = kpis.pending or 0

        # Per-agent performance
        agents = frappe.db.sql("""
            SELECT
                COALESCE(owner, 'Unassigned') as agent,
                COUNT(name) as total_orders,
                SUM(CASE WHEN custom_sales_status = 'Confirmed' THEN 1 ELSE 0 END) as confirmed,
                SUM(CASE WHEN custom_sales_status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled,
                SUM(CASE WHEN custom_sales_status = 'Pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN custom_sales_status = 'No Response' THEN 1 ELSE 0 END) as no_response,
                COALESCE(AVG(grand_total), 0) as avg_order_value
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
            GROUP BY owner
            ORDER BY confirmed DESC
        """, (company, from_date, to_date), as_dict=True)

        agent_data = []
        for a in agents:
            a_total = a.total_orders or 0
            a_confirmed = a.confirmed or 0
            agent_data.append({
                "agent": a.agent,
                "total_orders": a_total,
                "confirmed": a_confirmed,
                "cancelled": a.cancelled or 0,
                "pending": a.pending or 0,
                "no_response": a.no_response or 0,
                "confirmation_rate": round(a_confirmed / a_total * 100, 1) if a_total > 0 else 0,
                "avg_order_value": float(a.avg_order_value or 0),
            })

        # Hourly confirmation activity
        hourly = frappe.db.sql("""
            SELECT
                HOUR(creation) as hour,
                COUNT(name) as orders,
                SUM(CASE WHEN custom_sales_status = 'Confirmed' THEN 1 ELSE 0 END) as confirmed,
                SUM(CASE WHEN custom_sales_status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
            GROUP BY HOUR(creation)
            ORDER BY hour ASC
        """, (company, from_date, to_date), as_dict=True)

        # Cancellation reasons
        reasons = frappe.db.sql("""
            SELECT
                COALESCE(custom_cancellation_reason, 'Unknown') as reason,
                COUNT(name) as count
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
                AND custom_sales_status = 'Cancelled'
            GROUP BY custom_cancellation_reason
            ORDER BY count DESC
            LIMIT 10
        """, (company, from_date, to_date), as_dict=True)

        return {
            "kpis": {
                "total_orders": total,
                "confirmed": confirmed,
                "cancelled": cancelled,
                "pending": pending,
                "draft": kpis.draft or 0,
                "no_response": kpis.no_response or 0,
                "confirmation_rate": round(confirmed / total * 100, 1) if total > 0 else 0,
                "cancellation_rate": round(cancelled / total * 100, 1) if total > 0 else 0,
            },
            "agents": agent_data,
            "hourly_activity": [
                {"hour": r.hour, "orders": r.orders, "confirmed": r.confirmed, "cancelled": r.cancelled}
                for r in hourly
            ],
            "cancellation_reasons": [
                {"reason": r.reason, "count": r.count}
                for r in reasons
            ],
            "period": dates,
            "company": company,
        }

    return get_cached(cache_key, compute)
