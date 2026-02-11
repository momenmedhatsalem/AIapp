import frappe
from justyol_dashboard.services.cache_service import get_cached


@frappe.whitelist()
def get_alerts_dashboard(company="Justyol Morocco"):
    """Single API call returning all active alerts and anomalies."""
    cache_key = f"dashboard:alerts:{company}"

    def compute():
        alerts = []

        # 1. Low stock alerts
        low_stock = frappe.db.sql("""
            SELECT
                b.item_code,
                i.item_name,
                b.actual_qty,
                b.warehouse
            FROM `tabBin` b
            LEFT JOIN `tabItem` i ON i.name = b.item_code
            WHERE b.warehouse IN (
                SELECT name FROM `tabWarehouse`
                WHERE company = %s AND is_group = 0
            )
            AND b.actual_qty > 0 AND b.actual_qty <= 3
            ORDER BY b.actual_qty ASC
            LIMIT 20
        """, (company,), as_dict=True)

        for item in low_stock:
            alerts.append({
                "type": "warning",
                "category": "Inventory",
                "title": f"Low Stock: {item.item_name or item.item_code}",
                "detail": f"Only {int(item.actual_qty)} units left in {item.warehouse}",
                "priority": "high" if item.actual_qty <= 1 else "medium",
                "link": f"/app/item/{item.item_code}",
            })

        # 2. Out of stock alerts
        out_of_stock = frappe.db.sql("""
            SELECT
                b.item_code,
                i.item_name,
                b.warehouse
            FROM `tabBin` b
            LEFT JOIN `tabItem` i ON i.name = b.item_code
            WHERE b.warehouse IN (
                SELECT name FROM `tabWarehouse`
                WHERE company = %s AND is_group = 0
            )
            AND b.actual_qty <= 0
            LIMIT 20
        """, (company,), as_dict=True)

        for item in out_of_stock:
            alerts.append({
                "type": "danger",
                "category": "Inventory",
                "title": f"Out of Stock: {item.item_name or item.item_code}",
                "detail": f"Zero stock in {item.warehouse}",
                "priority": "critical",
                "link": f"/app/item/{item.item_code}",
            })

        # 3. High pending orders (unconfirmed > 24h)
        old_pending = frappe.db.sql("""
            SELECT COUNT(name) as count
            FROM `tabSales Order`
            WHERE company = %s
                AND custom_sales_status = 'Pending'
                AND creation < DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """, (company,), as_dict=True)[0]

        if old_pending.count > 0:
            alerts.append({
                "type": "warning",
                "category": "Operations",
                "title": f"{old_pending.count} orders pending > 24 hours",
                "detail": "Orders awaiting confirmation for more than 24 hours",
                "priority": "high",
                "link": "/app/sales-order?custom_sales_status=Pending",
            })

        # 4. Ready to ship but not shipped (>48h)
        stuck_shipments = frappe.db.sql("""
            SELECT COUNT(name) as count
            FROM `tabSales Order`
            WHERE company = %s
                AND custom_logistics_status = 'Ready to Ship'
                AND creation < DATE_SUB(NOW(), INTERVAL 48 HOUR)
        """, (company,), as_dict=True)[0]

        if stuck_shipments.count > 0:
            alerts.append({
                "type": "warning",
                "category": "Logistics",
                "title": f"{stuck_shipments.count} orders ready but not shipped > 48h",
                "detail": "Prepared orders stuck in warehouse",
                "priority": "high",
                "link": "/app/sales-order?custom_logistics_status=Ready to Ship",
            })

        # 5. High RTO rate today
        today_rto = frappe.db.sql("""
            SELECT
                SUM(CASE WHEN custom_track_shipment_status = 'Return' THEN 1 ELSE 0 END) as returns,
                SUM(CASE WHEN custom_track_shipment_status IN ('Delivered', 'Return') THEN 1 ELSE 0 END) as total
            FROM `tabSales Order`
            WHERE company = %s
                AND DATE(creation) = CURDATE()
        """, (company,), as_dict=True)[0]

        if today_rto.total and today_rto.total > 5:
            rto_rate = round((today_rto.returns or 0) / today_rto.total * 100, 1)
            if rto_rate > 25:
                alerts.append({
                    "type": "danger",
                    "category": "Returns",
                    "title": f"High RTO Rate Today: {rto_rate}%",
                    "detail": f"{today_rto.returns} returns out of {today_rto.total} completed orders",
                    "priority": "critical",
                    "link": "/app/sales-order?custom_track_shipment_status=Return",
                })

        # 6. Outstanding invoices > 30 days
        old_invoices = frappe.db.sql("""
            SELECT
                COUNT(name) as count,
                COALESCE(SUM(outstanding_amount), 0) as amount
            FROM `tabSales Invoice`
            WHERE company = %s
                AND outstanding_amount > 0
                AND docstatus = 1
                AND DATEDIFF(CURDATE(), posting_date) > 30
        """, (company,), as_dict=True)[0]

        if old_invoices.count > 0:
            alerts.append({
                "type": "warning",
                "category": "Finance",
                "title": f"{old_invoices.count} invoices overdue > 30 days",
                "detail": f"Outstanding amount: {float(old_invoices.amount):,.0f}",
                "priority": "medium",
                "link": "/app/sales-invoice?outstanding_amount=[\">\",0]",
            })

        # 7. Low confirmation rate today
        today_conf = frappe.db.sql("""
            SELECT
                COUNT(name) as total,
                SUM(CASE WHEN custom_sales_status = 'Confirmed' THEN 1 ELSE 0 END) as confirmed
            FROM `tabSales Order`
            WHERE company = %s
                AND DATE(creation) = CURDATE()
        """, (company,), as_dict=True)[0]

        if today_conf.total and today_conf.total > 10:
            conf_rate = round((today_conf.confirmed or 0) / today_conf.total * 100, 1)
            if conf_rate < 40:
                alerts.append({
                    "type": "warning",
                    "category": "Confirmation",
                    "title": f"Low Confirmation Rate Today: {conf_rate}%",
                    "detail": f"Only {today_conf.confirmed} of {today_conf.total} orders confirmed",
                    "priority": "high",
                    "link": "#/confirmation",
                })

        # Summary counts
        critical_count = sum(1 for a in alerts if a["priority"] == "critical")
        high_count = sum(1 for a in alerts if a["priority"] == "high")
        medium_count = sum(1 for a in alerts if a["priority"] == "medium")

        return {
            "alerts": sorted(alerts, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x["priority"], 4)),
            "summary": {
                "total": len(alerts),
                "critical": critical_count,
                "high": high_count,
                "medium": medium_count,
            },
            "company": company,
        }

    return get_cached(cache_key, compute, ttl=60)
