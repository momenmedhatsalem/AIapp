import frappe
from justyol_dashboard.services.kpi_service import get_period_dates
from justyol_dashboard.services.cache_service import get_cached


@frappe.whitelist()
def get_cashflow_dashboard(company="Justyol Morocco", period="month"):
    """Single API call returning all COD cash flow data."""
    dates = get_period_dates(period)
    cache_key = f"dashboard:cashflow:{company}:{dates['from']}:{dates['to']}"

    def compute():
        from_date = dates["from"]
        to_date = dates["to"] + " 23:59:59"

        # COD expected vs collected
        cod_kpis = frappe.db.sql("""
            SELECT
                COUNT(name) as total_orders,
                COALESCE(SUM(grand_total), 0) as total_gmv,
                COALESCE(SUM(CASE WHEN custom_sales_status = 'Confirmed' THEN grand_total ELSE 0 END), 0) as confirmed_gmv,
                COALESCE(SUM(CASE WHEN custom_track_shipment_status = 'Delivered' THEN grand_total ELSE 0 END), 0) as delivered_gmv,
                COALESCE(SUM(CASE WHEN custom_track_shipment_status = 'Return' THEN grand_total ELSE 0 END), 0) as return_cost,
                COALESCE(SUM(CASE WHEN custom_track_shipment_status = 'In Transit' THEN grand_total ELSE 0 END), 0) as in_transit_value,
                COALESCE(SUM(CASE WHEN custom_track_shipment_status = 'Out for Delivery' THEN grand_total ELSE 0 END), 0) as out_for_delivery_value,
                COALESCE(SUM(CASE WHEN custom_sales_status = 'Cancelled' THEN grand_total ELSE 0 END), 0) as cancelled_value
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
        """, (company, from_date, to_date), as_dict=True)[0]

        # Payment entries (actual cash received)
        payments = frappe.db.sql("""
            SELECT
                COALESCE(SUM(CASE WHEN payment_type = 'Receive' THEN paid_amount ELSE 0 END), 0) as cash_received,
                COALESCE(SUM(CASE WHEN payment_type = 'Pay' THEN paid_amount ELSE 0 END), 0) as cash_paid,
                COUNT(CASE WHEN payment_type = 'Receive' THEN 1 END) as receive_count,
                COUNT(CASE WHEN payment_type = 'Pay' THEN 1 END) as pay_count
            FROM `tabPayment Entry`
            WHERE company = %s
                AND posting_date >= %s
                AND posting_date <= %s
                AND docstatus = 1
        """, (company, from_date, dates["to"]), as_dict=True)[0]

        # Daily cash flow trend
        daily_flow = frappe.db.sql("""
            SELECT
                posting_date as date,
                SUM(CASE WHEN payment_type = 'Receive' THEN paid_amount ELSE 0 END) as cash_in,
                SUM(CASE WHEN payment_type = 'Pay' THEN paid_amount ELSE 0 END) as cash_out
            FROM `tabPayment Entry`
            WHERE company = %s
                AND posting_date >= %s
                AND posting_date <= %s
                AND docstatus = 1
            GROUP BY posting_date
            ORDER BY posting_date ASC
        """, (company, from_date, dates["to"]), as_dict=True)

        # COD collection pipeline (orders by shipment status with values)
        collection_pipeline = frappe.db.sql("""
            SELECT
                COALESCE(custom_track_shipment_status, 'Pending') as stage,
                COUNT(name) as orders,
                COALESCE(SUM(grand_total), 0) as value
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
                AND custom_sales_status = 'Confirmed'
            GROUP BY custom_track_shipment_status
            ORDER BY value DESC
        """, (company, from_date, to_date), as_dict=True)

        # Aging analysis — outstanding Sales Invoices
        aging = frappe.db.sql("""
            SELECT
                CASE
                    WHEN DATEDIFF(CURDATE(), posting_date) <= 7 THEN '0-7 days'
                    WHEN DATEDIFF(CURDATE(), posting_date) <= 15 THEN '8-15 days'
                    WHEN DATEDIFF(CURDATE(), posting_date) <= 30 THEN '16-30 days'
                    ELSE '30+ days'
                END as bucket,
                COUNT(name) as count,
                COALESCE(SUM(outstanding_amount), 0) as amount
            FROM `tabSales Invoice`
            WHERE company = %s
                AND outstanding_amount > 0
                AND docstatus = 1
            GROUP BY bucket
            ORDER BY FIELD(bucket, '0-7 days', '8-15 days', '16-30 days', '30+ days')
        """, (company,), as_dict=True)

        # Daily GMV trend from orders
        gmv_trend = frappe.db.sql("""
            SELECT
                DATE(creation) as date,
                COALESCE(SUM(CASE WHEN custom_track_shipment_status = 'Delivered' THEN grand_total ELSE 0 END), 0) as delivered,
                COALESCE(SUM(CASE WHEN custom_track_shipment_status = 'Return' THEN grand_total ELSE 0 END), 0) as returned
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
            GROUP BY DATE(creation)
            ORDER BY date ASC
        """, (company, from_date, to_date), as_dict=True)

        delivered_gmv = float(cod_kpis.delivered_gmv or 0)
        total_gmv = float(cod_kpis.total_gmv or 0)
        cash_received = float(payments.cash_received or 0)
        collection_rate = round(delivered_gmv / total_gmv * 100, 1) if total_gmv > 0 else 0
        cash_gap = delivered_gmv - cash_received

        return {
            "kpis": {
                "total_gmv": total_gmv,
                "confirmed_gmv": float(cod_kpis.confirmed_gmv or 0),
                "delivered_gmv": delivered_gmv,
                "return_cost": float(cod_kpis.return_cost or 0),
                "in_transit_value": float(cod_kpis.in_transit_value or 0),
                "out_for_delivery_value": float(cod_kpis.out_for_delivery_value or 0),
                "cancelled_value": float(cod_kpis.cancelled_value or 0),
                "cash_received": cash_received,
                "cash_paid": float(payments.cash_paid or 0),
                "net_cash": cash_received - float(payments.cash_paid or 0),
                "collection_rate": collection_rate,
                "cash_gap": cash_gap,
                "receive_count": payments.receive_count or 0,
                "pay_count": payments.pay_count or 0,
            },
            "daily_flow": [
                {"date": str(r.date), "cash_in": float(r.cash_in), "cash_out": float(r.cash_out)}
                for r in daily_flow
            ],
            "collection_pipeline": [
                {"stage": r.stage, "orders": r.orders, "value": float(r.value)}
                for r in collection_pipeline
            ],
            "aging": [
                {"bucket": r.bucket, "count": r.count, "amount": float(r.amount)}
                for r in aging
            ],
            "gmv_trend": [
                {"date": str(r.date), "delivered": float(r.delivered), "returned": float(r.returned)}
                for r in gmv_trend
            ],
            "period": dates,
            "company": company,
        }

    return get_cached(cache_key, compute)
