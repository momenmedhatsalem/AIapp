import frappe
from justyol_dashboard.services.kpi_service import get_period_dates, compute_operations_funnel
from justyol_dashboard.services.cache_service import get_cached


@frappe.whitelist()
def get_operations_dashboard(company="Justyol Morocco", period="today"):
    """Single API call returning all operations dashboard data."""
    dates = get_period_dates(period)
    cache_key = f"dashboard:operations:{company}:{dates['from']}:{dates['to']}"

    def compute():
        from_date = dates["from"]
        to_date = dates["to"] + " 23:59:59"

        # Pipeline counts
        pipeline = frappe.db.sql("""
            SELECT
                SUM(CASE WHEN custom_sales_status = 'Pending' THEN 1 ELSE 0 END) as pending_confirmation,
                SUM(CASE WHEN custom_sales_status = 'Confirmed' AND custom_logistics_status = 'Pending' THEN 1 ELSE 0 END) as pending_preparation,
                SUM(CASE WHEN custom_logistics_status = 'Ready to Ship' THEN 1 ELSE 0 END) as ready_to_ship,
                SUM(CASE WHEN custom_logistics_status = 'Shipped' THEN 1 ELSE 0 END) as shipped,
                SUM(CASE WHEN custom_track_shipment_status = 'Delivered' THEN 1 ELSE 0 END) as delivered,
                SUM(CASE WHEN custom_track_shipment_status = 'Return' THEN 1 ELSE 0 END) as returns
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
        """, (company, from_date, to_date), as_dict=True)[0]

        # Hourly order flow (for activity chart)
        hourly = frappe.db.sql("""
            SELECT
                HOUR(creation) as hour,
                COUNT(name) as orders,
                SUM(CASE WHEN custom_sales_status = 'Confirmed' THEN 1 ELSE 0 END) as confirmed
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
            GROUP BY HOUR(creation)
            ORDER BY hour ASC
        """, (company, from_date, to_date), as_dict=True)

        # Team workload (orders by assigned user)
        workload = frappe.db.sql("""
            SELECT
                COALESCE(owner, 'Unassigned') as agent,
                COUNT(name) as orders,
                SUM(CASE WHEN custom_sales_status = 'Confirmed' THEN 1 ELSE 0 END) as confirmed,
                SUM(CASE WHEN custom_sales_status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
            GROUP BY owner
            ORDER BY orders DESC
            LIMIT 20
        """, (company, from_date, to_date), as_dict=True)

        return {
            "pipeline": {
                "pending_confirmation": pipeline.pending_confirmation or 0,
                "pending_preparation": pipeline.pending_preparation or 0,
                "ready_to_ship": pipeline.ready_to_ship or 0,
                "shipped": pipeline.shipped or 0,
                "delivered": pipeline.delivered or 0,
                "returns": pipeline.returns or 0,
            },
            "hourly_activity": [
                {"hour": row.hour, "orders": row.orders, "confirmed": row.confirmed}
                for row in hourly
            ],
            "team_workload": [
                {
                    "agent": row.agent,
                    "orders": row.orders,
                    "confirmed": row.confirmed or 0,
                    "cancelled": row.cancelled or 0,
                    "rate": round((row.confirmed or 0) / row.orders * 100, 1) if row.orders > 0 else 0,
                }
                for row in workload
            ],
            "funnel": compute_operations_funnel(company, dates),
            "period": dates,
            "company": company,
        }

    return get_cached(cache_key, compute)
