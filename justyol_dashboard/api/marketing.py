import frappe
from justyol_dashboard.services.kpi_service import get_period_dates
from justyol_dashboard.services.cache_service import get_cached


@frappe.whitelist()
def get_marketing_dashboard(company="Justyol Morocco", period="month"):
    """Single API call returning marketing & media analytics data."""
    dates = get_period_dates(period)
    cache_key = f"dashboard:marketing:{company}:{dates['from']}:{dates['to']}"

    def compute():
        from_date = dates["from"]
        to_date = dates["to"] + " 23:59:59"

        # Full funnel metrics
        funnel = frappe.db.sql("""
            SELECT
                COUNT(name) as total_orders,
                COALESCE(SUM(grand_total), 0) as total_gmv,
                SUM(CASE WHEN custom_sales_status = 'Confirmed' THEN 1 ELSE 0 END) as confirmed,
                COALESCE(SUM(CASE WHEN custom_sales_status = 'Confirmed' THEN grand_total ELSE 0 END), 0) as confirmed_gmv,
                SUM(CASE WHEN custom_track_shipment_status = 'Delivered' THEN 1 ELSE 0 END) as delivered,
                COALESCE(SUM(CASE WHEN custom_track_shipment_status = 'Delivered' THEN grand_total ELSE 0 END), 0) as delivered_gmv,
                SUM(CASE WHEN custom_track_shipment_status = 'Return' THEN 1 ELSE 0 END) as returns,
                SUM(CASE WHEN custom_sales_status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled,
                COUNT(DISTINCT customer) as unique_customers
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
        """, (company, from_date, to_date), as_dict=True)[0]

        total = funnel.total_orders or 0
        confirmed = funnel.confirmed or 0
        delivered = funnel.delivered or 0

        # Source/channel breakdown (using source field if available)
        source_breakdown = frappe.db.sql("""
            SELECT
                COALESCE(source, 'Direct / Unknown') as source,
                COUNT(name) as orders,
                COALESCE(SUM(grand_total), 0) as gmv,
                SUM(CASE WHEN custom_sales_status = 'Confirmed' THEN 1 ELSE 0 END) as confirmed,
                SUM(CASE WHEN custom_track_shipment_status = 'Delivered' THEN 1 ELSE 0 END) as delivered,
                SUM(CASE WHEN custom_track_shipment_status = 'Return' THEN 1 ELSE 0 END) as returns,
                COUNT(DISTINCT customer) as customers
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
            GROUP BY COALESCE(source, 'Direct / Unknown')
            ORDER BY orders DESC
        """, (company, from_date, to_date), as_dict=True)

        # Daily orders trend for acquisition rate
        daily_orders = frappe.db.sql("""
            SELECT
                DATE(creation) as date,
                COUNT(name) as orders,
                COALESCE(SUM(grand_total), 0) as gmv,
                SUM(CASE WHEN custom_sales_status = 'Confirmed' THEN 1 ELSE 0 END) as confirmed,
                SUM(CASE WHEN custom_track_shipment_status = 'Delivered' THEN 1 ELSE 0 END) as delivered
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
            GROUP BY DATE(creation)
            ORDER BY date ASC
        """, (company, from_date, to_date), as_dict=True)

        # Top performing products (by delivery success)
        product_perf = frappe.db.sql("""
            SELECT
                soi.item_code,
                soi.item_name,
                COUNT(DISTINCT so.name) as orders,
                SUM(soi.qty) as qty,
                COALESCE(SUM(soi.amount), 0) as revenue,
                SUM(CASE WHEN so.custom_track_shipment_status = 'Delivered' THEN 1 ELSE 0 END) as delivered,
                SUM(CASE WHEN so.custom_track_shipment_status = 'Return' THEN 1 ELSE 0 END) as returns
            FROM `tabSales Order Item` soi
            INNER JOIN `tabSales Order` so ON so.name = soi.parent
            WHERE so.company = %s
                AND so.creation >= %s
                AND so.creation <= %s
            GROUP BY soi.item_code, soi.item_name
            ORDER BY revenue DESC
            LIMIT 15
        """, (company, from_date, to_date), as_dict=True)

        confirmed_rate = round(confirmed / total * 100, 1) if total > 0 else 0
        delivered_rate = round(delivered / confirmed * 100, 1) if confirmed > 0 else 0
        revenue_after_rto = float(funnel.delivered_gmv or 0)

        return {
            "kpis": {
                "total_orders": total,
                "total_gmv": float(funnel.total_gmv or 0),
                "confirmed": confirmed,
                "confirmed_gmv": float(funnel.confirmed_gmv or 0),
                "delivered": delivered,
                "delivered_gmv": float(funnel.delivered_gmv or 0),
                "returns": funnel.returns or 0,
                "cancelled": funnel.cancelled or 0,
                "unique_customers": funnel.unique_customers or 0,
                "confirmation_rate": confirmed_rate,
                "delivery_rate": delivered_rate,
                "revenue_after_rto": revenue_after_rto,
                "effective_rate": round(delivered / total * 100, 1) if total > 0 else 0,
            },
            "funnel_stages": [
                {"stage": "Orders Created", "count": total, "value": float(funnel.total_gmv or 0), "color": "#6366f1"},
                {"stage": "Confirmed", "count": confirmed, "value": float(funnel.confirmed_gmv or 0), "color": "#3b82f6"},
                {"stage": "Shipped", "count": confirmed, "value": float(funnel.confirmed_gmv or 0), "color": "#06b6d4"},
                {"stage": "Delivered", "count": delivered, "value": float(funnel.delivered_gmv or 0), "color": "#22c55e"},
                {"stage": "Cash Collected", "count": delivered, "value": revenue_after_rto, "color": "#14b8a6"},
            ],
            "source_breakdown": [
                {
                    "source": r.source,
                    "orders": r.orders,
                    "gmv": float(r.gmv or 0),
                    "confirmed": r.confirmed or 0,
                    "delivered": r.delivered or 0,
                    "returns": r.returns or 0,
                    "customers": r.customers,
                    "conf_rate": round((r.confirmed or 0) / max(r.orders, 1) * 100, 1),
                }
                for r in source_breakdown
            ],
            "daily_trend": [
                {"date": str(r.date), "orders": r.orders, "gmv": float(r.gmv), "confirmed": r.confirmed, "delivered": r.delivered}
                for r in daily_orders
            ],
            "product_performance": [
                {
                    "item_code": r.item_code,
                    "item_name": r.item_name,
                    "orders": r.orders,
                    "qty": r.qty or 0,
                    "revenue": float(r.revenue or 0),
                    "delivered": r.delivered or 0,
                    "returns": r.returns or 0,
                    "success_rate": round((r.delivered or 0) / max(r.orders, 1) * 100, 1),
                }
                for r in product_perf
            ],
            "period": dates,
            "company": company,
        }

    return get_cached(cache_key, compute)
