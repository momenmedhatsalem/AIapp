import frappe
from justyol_dashboard.services.kpi_service import get_period_dates
from justyol_dashboard.services.cache_service import get_cached


@frappe.whitelist()
def get_warehouse_dashboard(company="Justyol Morocco", period="today"):
    """Single API call returning warehouse operations data."""
    dates = get_period_dates(period)
    cache_key = f"dashboard:warehouse:{company}:{dates['from']}:{dates['to']}"

    def compute():
        from_date = dates["from"]
        to_date = dates["to"] + " 23:59:59"

        # Preparation pipeline
        prep_kpis = frappe.db.sql("""
            SELECT
                SUM(CASE WHEN custom_sales_status = 'Confirmed' AND custom_logistics_status = 'Pending' THEN 1 ELSE 0 END) as pending_preparation,
                SUM(CASE WHEN custom_logistics_status = 'Ready to Ship' THEN 1 ELSE 0 END) as ready_to_ship,
                SUM(CASE WHEN custom_logistics_status = 'Shipped' THEN 1 ELSE 0 END) as shipped,
                SUM(CASE WHEN custom_sales_status = 'Confirmed' THEN 1 ELSE 0 END) as total_confirmed,
                COUNT(name) as total_orders
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
        """, (company, from_date, to_date), as_dict=True)[0]

        # Hourly preparation activity
        hourly_prep = frappe.db.sql("""
            SELECT
                HOUR(creation) as hour,
                COUNT(name) as orders,
                SUM(CASE WHEN custom_logistics_status = 'Ready to Ship' THEN 1 ELSE 0 END) as prepared,
                SUM(CASE WHEN custom_logistics_status = 'Shipped' THEN 1 ELSE 0 END) as shipped
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
                AND custom_sales_status = 'Confirmed'
            GROUP BY HOUR(creation)
            ORDER BY hour ASC
        """, (company, from_date, to_date), as_dict=True)

        # Picker/packer performance (by owner who moved to Ready to Ship)
        team_perf = frappe.db.sql("""
            SELECT
                COALESCE(modified_by, owner) as agent,
                COUNT(name) as prepared,
                SUM(CASE WHEN custom_logistics_status = 'Shipped' THEN 1 ELSE 0 END) as shipped
            FROM `tabSales Order`
            WHERE company = %s
                AND creation >= %s
                AND creation <= %s
                AND custom_logistics_status IN ('Ready to Ship', 'Shipped')
            GROUP BY COALESCE(modified_by, owner)
            ORDER BY prepared DESC
            LIMIT 20
        """, (company, from_date, to_date), as_dict=True)

        # Warehouse stock health
        warehouse_stock = frappe.db.sql("""
            SELECT
                warehouse,
                COUNT(DISTINCT item_code) as sku_count,
                COALESCE(SUM(actual_qty), 0) as total_qty,
                COALESCE(SUM(stock_value), 0) as total_value,
                SUM(CASE WHEN actual_qty <= 0 THEN 1 ELSE 0 END) as out_of_stock,
                SUM(CASE WHEN actual_qty > 0 AND actual_qty <= 5 THEN 1 ELSE 0 END) as low_stock
            FROM `tabBin`
            WHERE warehouse IN (
                SELECT name FROM `tabWarehouse`
                WHERE company = %s AND is_group = 0
            )
            GROUP BY warehouse
            ORDER BY total_value DESC
        """, (company,), as_dict=True)

        # Delivery Note stats (actual shipments)
        dn_stats = frappe.db.sql("""
            SELECT
                COUNT(name) as total_dn,
                COALESCE(SUM(total), 0) as total_value,
                COUNT(CASE WHEN docstatus = 0 THEN 1 END) as draft_dn,
                COUNT(CASE WHEN docstatus = 1 THEN 1 END) as submitted_dn
            FROM `tabDelivery Note`
            WHERE company = %s
                AND posting_date >= %s
                AND posting_date <= %s
        """, (company, from_date, dates["to"]), as_dict=True)[0]

        # Stock Entry movements
        stock_movements = frappe.db.sql("""
            SELECT
                stock_entry_type as type,
                COUNT(name) as count,
                COALESCE(SUM(total_amount), 0) as value
            FROM `tabStock Entry`
            WHERE company = %s
                AND posting_date >= %s
                AND posting_date <= %s
                AND docstatus = 1
            GROUP BY stock_entry_type
            ORDER BY count DESC
        """, (company, from_date, dates["to"]), as_dict=True)

        pending = prep_kpis.pending_preparation or 0
        ready = prep_kpis.ready_to_ship or 0
        shipped = prep_kpis.shipped or 0
        total_confirmed = prep_kpis.total_confirmed or 0
        prep_rate = round((ready + shipped) / total_confirmed * 100, 1) if total_confirmed > 0 else 0

        return {
            "kpis": {
                "pending_preparation": pending,
                "ready_to_ship": ready,
                "shipped": shipped,
                "total_confirmed": total_confirmed,
                "total_orders": prep_kpis.total_orders or 0,
                "preparation_rate": prep_rate,
                "delivery_notes": dn_stats.total_dn or 0,
                "dn_value": float(dn_stats.total_value or 0),
            },
            "hourly_prep": [
                {"hour": r.hour, "orders": r.orders, "prepared": r.prepared or 0, "shipped": r.shipped or 0}
                for r in hourly_prep
            ],
            "team_performance": [
                {
                    "agent": r.agent,
                    "prepared": r.prepared,
                    "shipped": r.shipped or 0,
                }
                for r in team_perf
            ],
            "warehouse_stock": [
                {
                    "warehouse": r.warehouse,
                    "sku_count": r.sku_count,
                    "total_qty": float(r.total_qty),
                    "total_value": float(r.total_value),
                    "out_of_stock": r.out_of_stock or 0,
                    "low_stock": r.low_stock or 0,
                }
                for r in warehouse_stock
            ],
            "stock_movements": [
                {"type": r.type, "count": r.count, "value": float(r.value)}
                for r in stock_movements
            ],
            "period": dates,
            "company": company,
        }

    return get_cached(cache_key, compute)
