import frappe
from justyol_dashboard.services.kpi_service import get_period_dates, get_previous_period_dates
from justyol_dashboard.services.cache_service import get_cached


@frappe.whitelist()
def get_rto_dashboard(company="Justyol Morocco", period="month"):
    """Single API call returning all RTO & Returns analytics data."""
    dates = get_period_dates(period)
    cache_key = f"dashboard:rto:{company}:{dates['from']}:{dates['to']}"

    def compute():
        from_date = dates["from"]
        to_date = dates["to"] + " 23:59:59"
        prev_dates = get_previous_period_dates(dates, period)

        # Core RTO metrics
        rto_kpis = frappe.db.sql("""
            SELECT
                COUNT(name) as total_orders,
                SUM(CASE WHEN custom_sales_status = 'Confirmed' THEN 1 ELSE 0 END) as confirmed,
                SUM(CASE WHEN custom_logistics_status = 'Shipped' THEN 1 ELSE 0 END) as total_shipped,
                SUM(CASE WHEN custom_track_shipment_status = 'Delivered' THEN 1 ELSE 0 END) as delivered,
                SUM(CASE WHEN custom_track_shipment_status = 'Return' THEN 1 ELSE 0 END) as returns,
                COALESCE(SUM(CASE WHEN custom_track_shipment_status = 'Return' THEN grand_total ELSE 0 END), 0) as return_value,
                COALESCE(SUM(CASE WHEN custom_track_shipment_status = 'Delivered' THEN grand_total ELSE 0 END), 0) as delivered_value,
                COALESCE(SUM(CASE WHEN custom_logistics_status = 'Shipped' THEN grand_total ELSE 0 END), 0) as shipped_value,
                SUM(CASE WHEN custom_sales_status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
        """, (company, from_date, to_date), as_dict=True)[0]

        # Previous period for comparison
        prev_kpis = frappe.db.sql("""
            SELECT
                SUM(CASE WHEN custom_track_shipment_status = 'Return' THEN 1 ELSE 0 END) as returns,
                SUM(CASE WHEN custom_logistics_status = 'Shipped' THEN 1 ELSE 0 END) as total_shipped
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
        """, (company, prev_dates["from"], prev_dates["to"] + " 23:59:59"), as_dict=True)[0]

        total_shipped = (rto_kpis.total_shipped or 0) + (rto_kpis.delivered or 0) + (rto_kpis.returns or 0)
        rto_rate = round((rto_kpis.returns or 0) / total_shipped * 100, 1) if total_shipped > 0 else 0
        prev_shipped = (prev_kpis.total_shipped or 0)
        prev_rto_rate = round((prev_kpis.returns or 0) / prev_shipped * 100, 1) if prev_shipped > 0 else 0

        # Estimated RTO cost (shipping cost per return — rough estimate)
        avg_order_value = float(rto_kpis.shipped_value or 0) / total_shipped if total_shipped > 0 else 0
        estimated_shipping_cost = avg_order_value * 0.08  # ~8% of AOV as shipping estimate
        total_rto_cost = float(rto_kpis.return_value or 0) + (estimated_shipping_cost * (rto_kpis.returns or 0))

        # RTO by cancellation reason (for returned orders)
        rto_reasons = frappe.db.sql("""
            SELECT
                COALESCE(custom_cancellation_reason, 'No Reason Given') as reason,
                COUNT(name) as count,
                COALESCE(SUM(grand_total), 0) as value
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
                AND custom_track_shipment_status = 'Return'
            GROUP BY custom_cancellation_reason
            ORDER BY count DESC
            LIMIT 10
        """, (company, from_date, to_date), as_dict=True)

        # RTO trend over time
        rto_trend = frappe.db.sql("""
            SELECT
                DATE(creation) as date,
                SUM(CASE WHEN custom_track_shipment_status = 'Delivered' THEN 1 ELSE 0 END) as delivered,
                SUM(CASE WHEN custom_track_shipment_status = 'Return' THEN 1 ELSE 0 END) as returns,
                SUM(CASE WHEN custom_logistics_status = 'Shipped' THEN 1 ELSE 0 END) as shipped
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
            GROUP BY DATE(creation)
            ORDER BY date ASC
        """, (company, from_date, to_date), as_dict=True)

        # RTO by product (which products get returned most)
        rto_products = frappe.db.sql("""
            SELECT
                soi.item_code,
                soi.item_name,
                COUNT(DISTINCT so.name) as return_orders,
                SUM(soi.qty) as return_qty,
                COALESCE(SUM(soi.amount), 0) as return_value
            FROM `tabSales Order Item` soi
            INNER JOIN `tabSales Order` so ON so.name = soi.parent
            WHERE so.company = %s
                AND so.creation >= %s
                AND so.creation <= %s
                AND so.custom_track_shipment_status = 'Return'
            GROUP BY soi.item_code, soi.item_name
            ORDER BY return_orders DESC
            LIMIT 15
        """, (company, from_date, to_date), as_dict=True)

        # RTO by city/zone
        rto_zones = frappe.db.sql("""
            SELECT
                COALESCE(shipping_address_name, customer_address, 'Unknown') as zone,
                COUNT(name) as total_orders,
                SUM(CASE WHEN custom_track_shipment_status = 'Delivered' THEN 1 ELSE 0 END) as delivered,
                SUM(CASE WHEN custom_track_shipment_status = 'Return' THEN 1 ELSE 0 END) as returns
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
                AND custom_logistics_status IN ('Shipped')
            GROUP BY COALESCE(shipping_address_name, customer_address, 'Unknown')
            HAVING returns > 0
            ORDER BY returns DESC
            LIMIT 15
        """, (company, from_date, to_date), as_dict=True)

        return {
            "kpis": {
                "total_orders": rto_kpis.total_orders or 0,
                "confirmed": rto_kpis.confirmed or 0,
                "total_shipped": total_shipped,
                "delivered": rto_kpis.delivered or 0,
                "returns": rto_kpis.returns or 0,
                "cancelled": rto_kpis.cancelled or 0,
                "rto_rate": rto_rate,
                "prev_rto_rate": prev_rto_rate,
                "delivery_rate": round((rto_kpis.delivered or 0) / total_shipped * 100, 1) if total_shipped > 0 else 0,
                "return_value": float(rto_kpis.return_value or 0),
                "delivered_value": float(rto_kpis.delivered_value or 0),
                "total_rto_cost": round(total_rto_cost, 2),
                "revenue_after_rto": float(rto_kpis.delivered_value or 0),
            },
            "rto_reasons": [
                {"reason": r.reason, "count": r.count, "value": float(r.value)}
                for r in rto_reasons
            ],
            "rto_trend": [
                {
                    "date": str(r.date),
                    "delivered": r.delivered or 0,
                    "returns": r.returns or 0,
                    "shipped": r.shipped or 0,
                    "rto_rate": round((r.returns or 0) / max((r.shipped or 0) + (r.delivered or 0) + (r.returns or 0), 1) * 100, 1),
                }
                for r in rto_trend
            ],
            "rto_products": [
                {
                    "item_code": r.item_code,
                    "item_name": r.item_name,
                    "return_orders": r.return_orders,
                    "return_qty": r.return_qty or 0,
                    "return_value": float(r.return_value or 0),
                }
                for r in rto_products
            ],
            "rto_zones": [
                {
                    "zone": r.zone,
                    "total_orders": r.total_orders,
                    "delivered": r.delivered or 0,
                    "returns": r.returns or 0,
                    "rto_rate": round((r.returns or 0) / max(r.total_orders, 1) * 100, 1),
                }
                for r in rto_zones
            ],
            "period": dates,
            "company": company,
        }

    return get_cached(cache_key, compute)
