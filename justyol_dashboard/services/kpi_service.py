import frappe
from frappe.utils import getdate, add_days, get_first_day, get_last_day, nowdate


def get_period_dates(period="today"):
    """Convert period name to from_date/to_date dict."""
    today = getdate(nowdate())

    if period == "today":
        return {"from": str(today), "to": str(today)}
    elif period == "yesterday":
        yesterday = add_days(today, -1)
        return {"from": str(yesterday), "to": str(yesterday)}
    elif period == "week":
        # Start of current week (Monday)
        week_start = add_days(today, -today.weekday())
        return {"from": str(week_start), "to": str(today)}
    elif period == "month":
        month_start = get_first_day(today)
        return {"from": str(month_start), "to": str(today)}
    elif period == "last_month":
        last_month_end = add_days(get_first_day(today), -1)
        last_month_start = get_first_day(last_month_end)
        return {"from": str(last_month_start), "to": str(last_month_end)}
    elif period == "quarter":
        quarter_month = ((today.month - 1) // 3) * 3 + 1
        quarter_start = today.replace(month=quarter_month, day=1)
        return {"from": str(quarter_start), "to": str(today)}
    elif period == "year":
        year_start = today.replace(month=1, day=1)
        return {"from": str(year_start), "to": str(today)}
    else:
        return {"from": str(today), "to": str(today)}


def get_previous_period_dates(dates, period="today"):
    """Get the equivalent previous period for comparison."""
    from_date = getdate(dates["from"])
    to_date = getdate(dates["to"])
    period_days = (to_date - from_date).days + 1

    prev_to = add_days(from_date, -1)
    prev_from = add_days(prev_to, -(period_days - 1))

    return {"from": str(prev_from), "to": str(prev_to)}


def compute_sales_kpis(company, dates):
    """Compute all sales KPIs in a single efficient query batch."""
    from_date = dates["from"]
    to_date = dates["to"] + " 23:59:59"

    # Single query for main metrics
    main = frappe.db.sql("""
        SELECT
            COUNT(name) as total_orders,
            COALESCE(SUM(grand_total), 0) as gmv,
            COALESCE(AVG(grand_total), 0) as aov,
            SUM(CASE WHEN custom_sales_status = 'Confirmed' THEN 1 ELSE 0 END) as confirmed,
            SUM(CASE WHEN custom_sales_status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled,
            SUM(CASE WHEN custom_sales_status = 'Pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN custom_sales_status = 'Draft' THEN 1 ELSE 0 END) as draft,
            SUM(CASE WHEN custom_logistics_status = 'Shipped' THEN 1 ELSE 0 END) as shipped,
            SUM(CASE WHEN custom_logistics_status = 'Ready to Ship' THEN 1 ELSE 0 END) as ready_to_ship,
            SUM(CASE WHEN custom_track_shipment_status = 'Delivered' THEN 1 ELSE 0 END) as delivered,
            SUM(CASE WHEN custom_track_shipment_status = 'Return' THEN 1 ELSE 0 END) as returns
        FROM `tabSales Order`
        WHERE company = %s
            AND creation >= %s
            AND creation <= %s
    """, (company, from_date, to_date), as_dict=True)[0]

    total = main.total_orders or 0
    confirmed = main.confirmed or 0
    delivered = main.delivered or 0

    return {
        "total_orders": total,
        "gmv": float(main.gmv or 0),
        "aov": float(main.aov or 0),
        "confirmed": confirmed,
        "cancelled": main.cancelled or 0,
        "pending": main.pending or 0,
        "draft": main.draft or 0,
        "shipped": main.shipped or 0,
        "ready_to_ship": main.ready_to_ship or 0,
        "delivered": delivered,
        "returns": main.returns or 0,
        "confirmation_rate": round((confirmed / total * 100), 1) if total > 0 else 0,
        "cancellation_rate": round(((main.cancelled or 0) / total * 100), 1) if total > 0 else 0,
        "delivery_rate": round((delivered / confirmed * 100), 1) if confirmed > 0 else 0,
        "return_rate": round(((main.returns or 0) / confirmed * 100), 1) if confirmed > 0 else 0,
    }


def compute_revenue_trend(company, dates):
    """Daily revenue trend data for charts."""
    from_date = dates["from"]
    to_date = dates["to"] + " 23:59:59"

    data = frappe.db.sql("""
        SELECT
            DATE(creation) as date,
            COALESCE(SUM(grand_total), 0) as gmv,
            COUNT(name) as orders,
            SUM(CASE WHEN custom_sales_status = 'Confirmed' THEN 1 ELSE 0 END) as confirmed
        FROM `tabSales Order`
        WHERE company = %s
            AND creation >= %s
            AND creation <= %s
        GROUP BY DATE(creation)
        ORDER BY DATE(creation) ASC
    """, (company, from_date, to_date), as_dict=True)

    return [
        {
            "date": str(row.date),
            "gmv": float(row.gmv),
            "orders": row.orders,
            "confirmed": row.confirmed,
        }
        for row in data
    ]


def compute_status_distribution(company, dates):
    """Sales status breakdown for pie/donut charts."""
    from_date = dates["from"]
    to_date = dates["to"] + " 23:59:59"

    data = frappe.db.sql("""
        SELECT
            COALESCE(custom_sales_status, 'Unknown') as status,
            COUNT(name) as count,
            COALESCE(SUM(grand_total), 0) as gmv
        FROM `tabSales Order`
        WHERE company = %s
            AND creation >= %s
            AND creation <= %s
        GROUP BY custom_sales_status
        ORDER BY count DESC
    """, (company, from_date, to_date), as_dict=True)

    return [
        {"status": row.status, "count": row.count, "gmv": float(row.gmv)}
        for row in data
    ]


def compute_logistics_pipeline(company, dates):
    """Logistics status breakdown."""
    from_date = dates["from"]
    to_date = dates["to"] + " 23:59:59"

    data = frappe.db.sql("""
        SELECT
            COALESCE(custom_logistics_status, 'Unknown') as status,
            COUNT(name) as count
        FROM `tabSales Order`
        WHERE company = %s
            AND creation >= %s
            AND creation <= %s
        GROUP BY custom_logistics_status
        ORDER BY count DESC
    """, (company, from_date, to_date), as_dict=True)

    return [{"status": row.status, "count": row.count} for row in data]


def compute_shipment_tracking(company, dates):
    """Shipment tracking status breakdown."""
    from_date = dates["from"]
    to_date = dates["to"] + " 23:59:59"

    data = frappe.db.sql("""
        SELECT
            COALESCE(custom_track_shipment_status, 'Pending') as status,
            COUNT(name) as count
        FROM `tabSales Order`
        WHERE company = %s
            AND creation >= %s
            AND creation <= %s
        GROUP BY custom_track_shipment_status
        ORDER BY count DESC
    """, (company, from_date, to_date), as_dict=True)

    return [{"status": row.status, "count": row.count} for row in data]


def compute_cancellation_reasons(company, dates, limit=10):
    """Top cancellation reasons."""
    from_date = dates["from"]
    to_date = dates["to"] + " 23:59:59"

    data = frappe.db.sql("""
        SELECT
            COALESCE(custom_cancellation_reason, 'Unknown') as reason,
            COUNT(name) as count
        FROM `tabSales Order`
        WHERE company = %s
            AND custom_sales_status = 'Cancelled'
            AND creation >= %s
            AND creation <= %s
        GROUP BY custom_cancellation_reason
        ORDER BY count DESC
        LIMIT %s
    """, (company, from_date, to_date, limit), as_dict=True)

    return [{"reason": row.reason, "count": row.count} for row in data]


def compute_top_products(company, dates, limit=10):
    """Top selling products by revenue (from delivered orders)."""
    from_date = dates["from"]
    to_date = dates["to"] + " 23:59:59"

    data = frappe.db.sql("""
        SELECT
            soi.item_code,
            soi.item_name,
            SUM(soi.qty) as qty,
            SUM(soi.amount) as revenue
        FROM `tabSales Order Item` soi
        INNER JOIN `tabSales Order` so ON so.name = soi.parent
        WHERE so.company = %s
            AND so.creation >= %s
            AND so.creation <= %s
            AND so.custom_track_shipment_status = 'Delivered'
        GROUP BY soi.item_code, soi.item_name
        ORDER BY revenue DESC
        LIMIT %s
    """, (company, from_date, to_date, limit), as_dict=True)

    return [
        {
            "item_code": row.item_code,
            "item_name": row.item_name,
            "qty": row.qty or 0,
            "revenue": float(row.revenue or 0),
        }
        for row in data
    ]


def compute_top_suppliers(company, dates, limit=10):
    """Top suppliers by revenue."""
    from_date = dates["from"]
    to_date = dates["to"] + " 23:59:59"

    data = frappe.db.sql("""
        SELECT
            COALESCE(soi.supplier, 'Unknown') as supplier,
            SUM(soi.qty) as qty,
            SUM(soi.amount) as revenue,
            COUNT(DISTINCT soi.parent) as orders
        FROM `tabSales Order Item` soi
        INNER JOIN `tabSales Order` so ON so.name = soi.parent
        WHERE so.company = %s
            AND so.creation >= %s
            AND so.creation <= %s
            AND so.custom_track_shipment_status = 'Delivered'
        GROUP BY soi.supplier
        ORDER BY revenue DESC
        LIMIT %s
    """, (company, from_date, to_date, limit), as_dict=True)

    return [
        {
            "supplier": row.supplier,
            "qty": row.qty or 0,
            "revenue": float(row.revenue or 0),
            "orders": row.orders or 0,
        }
        for row in data
    ]


def compute_customer_insights(company, dates):
    """Customer analytics: unique, new, repeat, frequency."""
    from_date = dates["from"]
    to_date = dates["to"] + " 23:59:59"

    data = frappe.db.sql("""
        SELECT
            customer,
            COUNT(name) as order_count
        FROM `tabSales Order`
        WHERE company = %s
            AND creation >= %s
            AND creation <= %s
        GROUP BY customer
    """, (company, from_date, to_date), as_dict=True)

    unique_customers = len(data)
    repeat_customers = sum(1 for c in data if c.order_count > 1)
    new_customers = unique_customers - repeat_customers
    total_orders = sum(c.order_count for c in data)
    avg_frequency = round(total_orders / unique_customers, 1) if unique_customers > 0 else 0

    return {
        "unique_customers": unique_customers,
        "new_customers": new_customers,
        "repeat_customers": repeat_customers,
        "avg_order_frequency": avg_frequency,
        "total_orders": total_orders,
    }


def compute_operations_funnel(company, dates):
    """Full operations funnel data."""
    from_date = dates["from"]
    to_date = dates["to"] + " 23:59:59"

    data = frappe.db.sql("""
        SELECT
            COUNT(name) as total,
            SUM(CASE WHEN custom_sales_status = 'Draft' THEN 1 ELSE 0 END) as draft,
            SUM(CASE WHEN custom_sales_status = 'Pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN custom_sales_status = 'Confirmed' THEN 1 ELSE 0 END) as confirmed,
            SUM(CASE WHEN custom_logistics_status = 'Ready to Ship' THEN 1 ELSE 0 END) as ready_to_ship,
            SUM(CASE WHEN custom_logistics_status = 'Shipped' THEN 1 ELSE 0 END) as shipped,
            SUM(CASE WHEN custom_track_shipment_status = 'Delivered' THEN 1 ELSE 0 END) as delivered,
            SUM(CASE WHEN custom_track_shipment_status = 'Return' THEN 1 ELSE 0 END) as returns,
            SUM(CASE WHEN custom_sales_status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled
        FROM `tabSales Order`
        WHERE company = %s
            AND creation >= %s
            AND creation <= %s
    """, (company, from_date, to_date), as_dict=True)[0]

    return [
        {"stage": "Draft", "count": data.draft or 0, "color": "#64748b"},
        {"stage": "Pending", "count": data.pending or 0, "color": "#a855f7"},
        {"stage": "Confirmed", "count": data.confirmed or 0, "color": "#3b82f6"},
        {"stage": "Ready to Ship", "count": data.ready_to_ship or 0, "color": "#06b6d4"},
        {"stage": "Shipped", "count": data.shipped or 0, "color": "#14b8a6"},
        {"stage": "Delivered", "count": data.delivered or 0, "color": "#22c55e"},
        {"stage": "Returns", "count": data.returns or 0, "color": "#f97316"},
        {"stage": "Cancelled", "count": data.cancelled or 0, "color": "#ef4444"},
    ]
