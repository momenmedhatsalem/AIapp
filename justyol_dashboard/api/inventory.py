import frappe
from justyol_dashboard.services.cache_service import get_cached


@frappe.whitelist()
def get_inventory_dashboard(company="Justyol Morocco"):
    """Single API call returning all inventory intelligence data."""
    cache_key = f"dashboard:inventory:{company}"

    def compute():
        # Stock summary across warehouses
        stock_summary = frappe.db.sql("""
            SELECT
                COUNT(DISTINCT item_code) as total_items,
                COALESCE(SUM(actual_qty), 0) as total_stock,
                COALESCE(SUM(stock_value), 0) as total_value,
                SUM(CASE WHEN actual_qty <= 0 THEN 1 ELSE 0 END) as out_of_stock,
                SUM(CASE WHEN actual_qty > 0 AND actual_qty <= 5 THEN 1 ELSE 0 END) as low_stock
            FROM `tabBin`
            WHERE warehouse IN (
                SELECT name FROM `tabWarehouse`
                WHERE company = %s AND is_group = 0
            )
        """, (company,), as_dict=True)[0]

        # Top items by stock value
        top_items = frappe.db.sql("""
            SELECT
                b.item_code,
                i.item_name,
                b.actual_qty as qty,
                b.stock_value as value,
                b.warehouse
            FROM `tabBin` b
            LEFT JOIN `tabItem` i ON i.name = b.item_code
            WHERE b.warehouse IN (
                SELECT name FROM `tabWarehouse`
                WHERE company = %s AND is_group = 0
            )
            AND b.actual_qty > 0
            ORDER BY b.stock_value DESC
            LIMIT 20
        """, (company,), as_dict=True)

        # Low / out of stock items
        restock_alerts = frappe.db.sql("""
            SELECT
                b.item_code,
                i.item_name,
                b.actual_qty as qty,
                b.warehouse
            FROM `tabBin` b
            LEFT JOIN `tabItem` i ON i.name = b.item_code
            WHERE b.warehouse IN (
                SELECT name FROM `tabWarehouse`
                WHERE company = %s AND is_group = 0
            )
            AND b.actual_qty <= 5
            ORDER BY b.actual_qty ASC
            LIMIT 30
        """, (company,), as_dict=True)

        # Warehouse-wise stock distribution
        warehouse_dist = frappe.db.sql("""
            SELECT
                b.warehouse,
                COUNT(DISTINCT b.item_code) as items,
                COALESCE(SUM(b.actual_qty), 0) as total_qty,
                COALESCE(SUM(b.stock_value), 0) as total_value
            FROM `tabBin` b
            WHERE b.warehouse IN (
                SELECT name FROM `tabWarehouse`
                WHERE company = %s AND is_group = 0
            )
            AND b.actual_qty > 0
            GROUP BY b.warehouse
            ORDER BY total_value DESC
        """, (company,), as_dict=True)

        # Recent Purchase Orders
        recent_pos = frappe.db.sql("""
            SELECT
                name, supplier, grand_total, status,
                transaction_date, per_received
            FROM `tabPurchase Order`
            WHERE company = %s
                AND docstatus = 1
            ORDER BY creation DESC
            LIMIT 10
        """, (company,), as_dict=True)

        return {
            "kpis": {
                "total_items": stock_summary.total_items or 0,
                "total_stock": float(stock_summary.total_stock or 0),
                "total_value": float(stock_summary.total_value or 0),
                "out_of_stock": stock_summary.out_of_stock or 0,
                "low_stock": stock_summary.low_stock or 0,
            },
            "top_items": [
                {
                    "item_code": r.item_code,
                    "item_name": r.item_name,
                    "qty": float(r.qty),
                    "value": float(r.value),
                    "warehouse": r.warehouse,
                }
                for r in top_items
            ],
            "restock_alerts": [
                {
                    "item_code": r.item_code,
                    "item_name": r.item_name,
                    "qty": float(r.qty),
                    "warehouse": r.warehouse,
                }
                for r in restock_alerts
            ],
            "warehouse_distribution": [
                {
                    "warehouse": r.warehouse,
                    "items": r.items,
                    "total_qty": float(r.total_qty),
                    "total_value": float(r.total_value),
                }
                for r in warehouse_dist
            ],
            "recent_purchase_orders": [
                {
                    "name": r.name,
                    "supplier": r.supplier,
                    "grand_total": float(r.grand_total),
                    "status": r.status,
                    "date": str(r.transaction_date),
                    "received_pct": float(r.per_received or 0),
                }
                for r in recent_pos
            ],
            "company": company,
        }

    return get_cached(cache_key, compute, ttl=180)
