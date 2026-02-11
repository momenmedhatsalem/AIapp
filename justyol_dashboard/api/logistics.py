import frappe
from justyol_dashboard.services.kpi_service import get_period_dates
from justyol_dashboard.services.cache_service import get_cached


@frappe.whitelist()
def get_logistics_dashboard(company="Justyol Morocco", period="month"):
    """Single API call returning all logistics & shipping data."""
    dates = get_period_dates(period)
    cache_key = f"dashboard:logistics:{company}:{dates['from']}:{dates['to']}"

    def compute():
        from_date = dates["from"]
        to_date = dates["to"] + " 23:59:59"

        # Shipment status breakdown
        shipment_kpis = frappe.db.sql("""
            SELECT
                COUNT(name) as total,
                SUM(CASE WHEN custom_logistics_status = 'Shipped' THEN 1 ELSE 0 END) as shipped,
                SUM(CASE WHEN custom_logistics_status = 'Ready to Ship' THEN 1 ELSE 0 END) as ready,
                SUM(CASE WHEN custom_logistics_status = 'Pending' THEN 1 ELSE 0 END) as pending_logistics,
                SUM(CASE WHEN custom_track_shipment_status = 'Delivered' THEN 1 ELSE 0 END) as delivered,
                SUM(CASE WHEN custom_track_shipment_status = 'In Transit' THEN 1 ELSE 0 END) as in_transit,
                SUM(CASE WHEN custom_track_shipment_status = 'Return' THEN 1 ELSE 0 END) as returns,
                SUM(CASE WHEN custom_track_shipment_status = 'Out for Delivery' THEN 1 ELSE 0 END) as out_for_delivery,
                COALESCE(SUM(CASE WHEN custom_track_shipment_status = 'Delivered' THEN grand_total ELSE 0 END), 0) as delivered_value,
                COALESCE(SUM(CASE WHEN custom_track_shipment_status = 'Return' THEN grand_total ELSE 0 END), 0) as return_value
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
        """, (company, from_date, to_date), as_dict=True)[0]

        total_shipped = (shipment_kpis.shipped or 0) + (shipment_kpis.delivered or 0) + (shipment_kpis.returns or 0)
        delivery_rate = round((shipment_kpis.delivered or 0) / total_shipped * 100, 1) if total_shipped > 0 else 0
        rto_rate = round((shipment_kpis.returns or 0) / total_shipped * 100, 1) if total_shipped > 0 else 0

        # Tracking status distribution for chart
        tracking_dist = frappe.db.sql("""
            SELECT
                COALESCE(custom_track_shipment_status, 'Unknown') as status,
                COUNT(name) as count
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
                AND custom_logistics_status IN ('Shipped', 'Ready to Ship')
            GROUP BY custom_track_shipment_status
            ORDER BY count DESC
        """, (company, from_date, to_date), as_dict=True)

        # Daily shipment trend
        shipment_trend = frappe.db.sql("""
            SELECT
                DATE(creation) as date,
                SUM(CASE WHEN custom_logistics_status = 'Shipped' THEN 1 ELSE 0 END) as shipped,
                SUM(CASE WHEN custom_track_shipment_status = 'Delivered' THEN 1 ELSE 0 END) as delivered,
                SUM(CASE WHEN custom_track_shipment_status = 'Return' THEN 1 ELSE 0 END) as returns
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
            GROUP BY DATE(creation)
            ORDER BY date ASC
        """, (company, from_date, to_date), as_dict=True)

        # Top cities by order volume
        top_cities = frappe.db.sql("""
            SELECT
                COALESCE(shipping_address_name, customer_address, 'Unknown') as city,
                COUNT(name) as orders,
                SUM(CASE WHEN custom_track_shipment_status = 'Delivered' THEN 1 ELSE 0 END) as delivered,
                SUM(CASE WHEN custom_track_shipment_status = 'Return' THEN 1 ELSE 0 END) as returns
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
            GROUP BY COALESCE(shipping_address_name, customer_address, 'Unknown')
            ORDER BY orders DESC
            LIMIT 15
        """, (company, from_date, to_date), as_dict=True)

        return {
            "kpis": {
                "total": shipment_kpis.total or 0,
                "shipped": shipment_kpis.shipped or 0,
                "ready": shipment_kpis.ready or 0,
                "pending_logistics": shipment_kpis.pending_logistics or 0,
                "delivered": shipment_kpis.delivered or 0,
                "in_transit": shipment_kpis.in_transit or 0,
                "out_for_delivery": shipment_kpis.out_for_delivery or 0,
                "returns": shipment_kpis.returns or 0,
                "delivery_rate": delivery_rate,
                "rto_rate": rto_rate,
                "delivered_value": float(shipment_kpis.delivered_value or 0),
                "return_value": float(shipment_kpis.return_value or 0),
            },
            "tracking_distribution": [
                {"status": r.status, "count": r.count}
                for r in tracking_dist
            ],
            "shipment_trend": [
                {"date": str(r.date), "shipped": r.shipped, "delivered": r.delivered, "returns": r.returns}
                for r in shipment_trend
            ],
            "top_cities": [
                {
                    "city": r.city,
                    "orders": r.orders,
                    "delivered": r.delivered or 0,
                    "returns": r.returns or 0,
                    "delivery_rate": round((r.delivered or 0) / r.orders * 100, 1) if r.orders > 0 else 0,
                }
                for r in top_cities
            ],
            "period": dates,
            "company": company,
        }

    return get_cached(cache_key, compute)
