import frappe
from justyol_dashboard.services.kpi_service import get_period_dates
from justyol_dashboard.services.cache_service import get_cached


@frappe.whitelist()
def get_customer_dashboard(company="Justyol Morocco", period="month"):
    """Single API call returning all customer intelligence data."""
    dates = get_period_dates(period)
    cache_key = f"dashboard:customers:{company}:{dates['from']}:{dates['to']}"

    def compute():
        from_date = dates["from"]
        to_date = dates["to"] + " 23:59:59"

        # Customer overview
        customer_kpis = frappe.db.sql("""
            SELECT
                COUNT(DISTINCT customer) as unique_customers,
                COUNT(name) as total_orders,
                COALESCE(SUM(grand_total), 0) as total_revenue,
                COALESCE(AVG(grand_total), 0) as avg_order_value
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
        """, (company, from_date, to_date), as_dict=True)[0]

        # New vs repeat customers
        repeat_data = frappe.db.sql("""
            SELECT
                customer,
                COUNT(name) as order_count,
                COALESCE(SUM(grand_total), 0) as total_spend,
                MIN(creation) as first_order
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
            GROUP BY customer
        """, (company, from_date, to_date), as_dict=True)

        # Check which customers had prior orders
        new_customers = 0
        repeat_customers = 0
        for c in repeat_data:
            prior = frappe.db.count("Sales Order", {
                "company": company,
                "customer": c.customer,
                "creation": ["<", from_date],
            })
            if prior > 0:
                repeat_customers += 1
            else:
                new_customers += 1

        repeat_pct = round(repeat_customers / max(len(repeat_data), 1) * 100, 1)

        # Top customers by spend
        top_customers = frappe.db.sql("""
            SELECT
                customer,
                customer_name,
                COUNT(name) as orders,
                COALESCE(SUM(grand_total), 0) as total_spend,
                COALESCE(AVG(grand_total), 0) as avg_order,
                SUM(CASE WHEN custom_track_shipment_status = 'Delivered' THEN 1 ELSE 0 END) as delivered,
                SUM(CASE WHEN custom_track_shipment_status = 'Return' THEN 1 ELSE 0 END) as returns,
                SUM(CASE WHEN custom_sales_status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
            GROUP BY customer, customer_name
            ORDER BY total_spend DESC
            LIMIT 20
        """, (company, from_date, to_date), as_dict=True)

        # Customer segments by order frequency
        frequency_dist = frappe.db.sql("""
            SELECT
                CASE
                    WHEN cnt = 1 THEN '1 Order'
                    WHEN cnt BETWEEN 2 AND 3 THEN '2-3 Orders'
                    WHEN cnt BETWEEN 4 AND 5 THEN '4-5 Orders'
                    ELSE '6+ Orders'
                END as segment,
                COUNT(*) as customers,
                SUM(spend) as total_spend
            FROM (
                SELECT
                    customer,
                    COUNT(name) as cnt,
                    SUM(grand_total) as spend
                FROM `tabSales Order`
                WHERE company = %s
                    AND creation >= %s
                    AND creation <= %s
                GROUP BY customer
            ) t
            GROUP BY segment
            ORDER BY FIELD(segment, '1 Order', '2-3 Orders', '4-5 Orders', '6+ Orders')
        """, (company, from_date, to_date), as_dict=True)

        # Risk scoring — high RTO customers
        risky_customers = frappe.db.sql("""
            SELECT
                customer,
                customer_name,
                COUNT(name) as total_orders,
                SUM(CASE WHEN custom_track_shipment_status = 'Return' THEN 1 ELSE 0 END) as returns,
                SUM(CASE WHEN custom_sales_status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled,
                COALESCE(SUM(grand_total), 0) as total_value
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
            GROUP BY customer, customer_name
            HAVING returns > 0 OR cancelled > 1
            ORDER BY returns DESC, cancelled DESC
            LIMIT 20
        """, (company, from_date, to_date), as_dict=True)

        # Customer acquisition trend (new customers per day)
        acquisition_trend = frappe.db.sql("""
            SELECT
                DATE(first_order) as date,
                COUNT(*) as new_customers
            FROM (
                SELECT customer, MIN(creation) as first_order
                FROM `tabSales Order`
                WHERE company = %s
                GROUP BY customer
                HAVING MIN(creation) >= %s AND MIN(creation) <= %s
            ) t
            GROUP BY DATE(first_order)
            ORDER BY date ASC
        """, (company, from_date, to_date), as_dict=True)

        return {
            "kpis": {
                "unique_customers": customer_kpis.unique_customers or 0,
                "total_orders": customer_kpis.total_orders or 0,
                "total_revenue": float(customer_kpis.total_revenue or 0),
                "avg_order_value": float(customer_kpis.avg_order_value or 0),
                "new_customers": new_customers,
                "repeat_customers": repeat_customers,
                "repeat_rate": repeat_pct,
                "avg_orders_per_customer": round((customer_kpis.total_orders or 0) / max(customer_kpis.unique_customers or 1, 1), 1),
                "revenue_per_customer": round(float(customer_kpis.total_revenue or 0) / max(customer_kpis.unique_customers or 1, 1), 2),
            },
            "top_customers": [
                {
                    "customer": r.customer,
                    "customer_name": r.customer_name,
                    "orders": r.orders,
                    "total_spend": float(r.total_spend or 0),
                    "avg_order": float(r.avg_order or 0),
                    "delivered": r.delivered or 0,
                    "returns": r.returns or 0,
                    "cancelled": r.cancelled or 0,
                }
                for r in top_customers
            ],
            "frequency_distribution": [
                {"segment": r.segment, "customers": r.customers, "total_spend": float(r.total_spend or 0)}
                for r in frequency_dist
            ],
            "risky_customers": [
                {
                    "customer": r.customer,
                    "customer_name": r.customer_name,
                    "total_orders": r.total_orders,
                    "returns": r.returns or 0,
                    "cancelled": r.cancelled or 0,
                    "total_value": float(r.total_value or 0),
                    "risk_score": min(100, round(((r.returns or 0) * 30 + (r.cancelled or 0) * 15) / max(r.total_orders, 1) * 100)),
                }
                for r in risky_customers
            ],
            "acquisition_trend": [
                {"date": str(r.date), "new_customers": r.new_customers}
                for r in acquisition_trend
            ],
            "period": dates,
            "company": company,
        }

    return get_cached(cache_key, compute)
