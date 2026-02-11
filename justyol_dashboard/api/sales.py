import frappe
from justyol_dashboard.services.kpi_service import (
    get_period_dates,
    get_previous_period_dates,
    compute_sales_kpis,
    compute_revenue_trend,
    compute_status_distribution,
    compute_logistics_pipeline,
    compute_shipment_tracking,
    compute_cancellation_reasons,
    compute_top_products,
    compute_top_suppliers,
    compute_customer_insights,
    compute_operations_funnel,
)
from justyol_dashboard.services.cache_service import get_cached


@frappe.whitelist()
def get_sales_dashboard(company="Justyol Morocco", from_date=None, to_date=None, period="today"):
    """Single API call returning all sales dashboard data.

    Supports both preset periods and custom date ranges.
    """
    if from_date and to_date:
        dates = {"from": from_date, "to": to_date}
    else:
        dates = get_period_dates(period)

    prev_dates = get_previous_period_dates(dates, period)
    cache_key = f"dashboard:sales:{company}:{dates['from']}:{dates['to']}"

    def compute():
        kpis = compute_sales_kpis(company, dates)
        prev_kpis = compute_sales_kpis(company, prev_dates)

        return {
            "kpis": kpis,
            "previous_kpis": prev_kpis,
            "revenue_trend": compute_revenue_trend(company, dates),
            "status_distribution": compute_status_distribution(company, dates),
            "logistics_pipeline": compute_logistics_pipeline(company, dates),
            "shipment_tracking": compute_shipment_tracking(company, dates),
            "cancellation_reasons": compute_cancellation_reasons(company, dates),
            "top_products": compute_top_products(company, dates, limit=10),
            "top_suppliers": compute_top_suppliers(company, dates, limit=10),
            "customer_insights": compute_customer_insights(company, dates),
            "funnel": compute_operations_funnel(company, dates),
            "period": {
                "label": period,
                "from_date": dates["from"],
                "to_date": dates["to"],
            },
            "company": company,
        }

    return get_cached(cache_key, compute)


@frappe.whitelist()
def get_recent_orders(company="Justyol Morocco", limit=20):
    """Get latest orders for live feed."""
    orders = frappe.db.sql("""
        SELECT
            name, customer, grand_total, custom_sales_status,
            custom_logistics_status, custom_track_shipment_status,
            creation
        FROM `tabSales Order`
        WHERE company = %s
        ORDER BY creation DESC
        LIMIT %s
    """, (company, limit), as_dict=True)

    return [{
        "name": o.name,
        "customer": o.customer,
        "total": float(o.grand_total or 0),
        "sales_status": o.custom_sales_status,
        "logistics_status": o.custom_logistics_status,
        "shipment_status": o.custom_track_shipment_status,
        "created": str(o.creation),
    } for o in orders]
