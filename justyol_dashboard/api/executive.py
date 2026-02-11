import frappe
from justyol_dashboard.services.kpi_service import (
    get_period_dates,
    get_previous_period_dates,
    compute_sales_kpis,
    compute_revenue_trend,
    compute_status_distribution,
    compute_logistics_pipeline,
    compute_top_products,
    compute_top_suppliers,
    compute_operations_funnel,
)
from justyol_dashboard.services.cache_service import get_cached


@frappe.whitelist()
def get_executive_dashboard(company="Justyol Morocco", period="today"):
    """Single API call returning all executive dashboard data.

    This replaces 10-20 individual frappe.call() requests with one efficient call.
    Results are cached in Redis for 2 minutes.
    """
    dates = get_period_dates(period)
    prev_dates = get_previous_period_dates(dates, period)

    cache_key = f"dashboard:executive:{company}:{dates['from']}:{dates['to']}"

    def compute():
        kpis = compute_sales_kpis(company, dates)
        prev_kpis = compute_sales_kpis(company, prev_dates)

        return {
            "kpis": kpis,
            "previous_kpis": prev_kpis,
            "revenue_trend": compute_revenue_trend(company, dates),
            "status_distribution": compute_status_distribution(company, dates),
            "logistics_pipeline": compute_logistics_pipeline(company, dates),
            "top_products": compute_top_products(company, dates, limit=5),
            "top_suppliers": compute_top_suppliers(company, dates, limit=5),
            "funnel": compute_operations_funnel(company, dates),
            "period": {
                "label": period,
                "from_date": dates["from"],
                "to_date": dates["to"],
                "prev_from_date": prev_dates["from"],
                "prev_to_date": prev_dates["to"],
            },
            "company": company,
        }

    return get_cached(cache_key, compute)
