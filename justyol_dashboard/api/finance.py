import frappe
from justyol_dashboard.services.kpi_service import get_period_dates
from justyol_dashboard.services.cache_service import get_cached


@frappe.whitelist()
def get_finance_dashboard(company="Justyol Morocco", period="month"):
    """Single API call returning all finance dashboard data."""
    dates = get_period_dates(period)
    cache_key = f"dashboard:finance:{company}:{dates['from']}:{dates['to']}"

    def compute():
        from_date = dates["from"]
        to_date = dates["to"] + " 23:59:59"

        # Revenue & COGS from Sales Invoices
        invoice_kpis = frappe.db.sql("""
            SELECT
                COALESCE(SUM(grand_total), 0) as total_revenue,
                COALESCE(SUM(net_total), 0) as net_revenue,
                COALESCE(SUM(total_taxes_and_charges), 0) as total_tax,
                COUNT(name) as invoice_count,
                COALESCE(AVG(grand_total), 0) as avg_invoice
            FROM `tabSales Invoice`
            WHERE company = %s
                AND posting_date >= %s
                AND posting_date <= %s
                AND docstatus = 1
        """, (company, from_date, dates["to"]), as_dict=True)[0]

        # Purchase totals
        purchase_kpis = frappe.db.sql("""
            SELECT
                COALESCE(SUM(grand_total), 0) as total_purchases,
                COUNT(name) as po_count
            FROM `tabPurchase Invoice`
            WHERE company = %s
                AND posting_date >= %s
                AND posting_date <= %s
                AND docstatus = 1
        """, (company, from_date, dates["to"]), as_dict=True)[0]

        # Accounts Receivable (outstanding)
        receivable = frappe.db.sql("""
            SELECT
                COALESCE(SUM(outstanding_amount), 0) as total_ar
            FROM `tabSales Invoice`
            WHERE company = %s
                AND outstanding_amount > 0
                AND docstatus = 1
        """, (company,), as_dict=True)[0]

        # Accounts Payable (outstanding)
        payable = frappe.db.sql("""
            SELECT
                COALESCE(SUM(outstanding_amount), 0) as total_ap
            FROM `tabPurchase Invoice`
            WHERE company = %s
                AND outstanding_amount > 0
                AND docstatus = 1
        """, (company,), as_dict=True)[0]

        # Revenue trend by date
        revenue_trend = frappe.db.sql("""
            SELECT
                posting_date as date,
                SUM(grand_total) as revenue,
                COUNT(name) as invoices
            FROM `tabSales Invoice`
            WHERE company = %s
                AND posting_date >= %s
                AND posting_date <= %s
                AND docstatus = 1
            GROUP BY posting_date
            ORDER BY posting_date ASC
        """, (company, from_date, dates["to"]), as_dict=True)

        # Payment entries for cash flow
        payments_in = frappe.db.sql("""
            SELECT
                COALESCE(SUM(paid_amount), 0) as total
            FROM `tabPayment Entry`
            WHERE company = %s
                AND posting_date >= %s
                AND posting_date <= %s
                AND payment_type = 'Receive'
                AND docstatus = 1
        """, (company, from_date, dates["to"]), as_dict=True)[0]

        payments_out = frappe.db.sql("""
            SELECT
                COALESCE(SUM(paid_amount), 0) as total
            FROM `tabPayment Entry`
            WHERE company = %s
                AND posting_date >= %s
                AND posting_date <= %s
                AND payment_type = 'Pay'
                AND docstatus = 1
        """, (company, from_date, dates["to"]), as_dict=True)[0]

        # GMV from Sales Orders (for COD tracking)
        cod_data = frappe.db.sql("""
            SELECT
                COALESCE(SUM(grand_total), 0) as total_gmv,
                COALESCE(SUM(CASE WHEN custom_track_shipment_status = 'Delivered' THEN grand_total ELSE 0 END), 0) as delivered_gmv,
                COALESCE(SUM(CASE WHEN custom_track_shipment_status = 'Return' THEN grand_total ELSE 0 END), 0) as return_cost
            FROM `tabSales Order`
            WHERE company = %s
                AND transaction_date >= %s
                AND transaction_date <= %s
        """, (company, from_date, dates["to"]), as_dict=True)[0]

        gross_profit = float(invoice_kpis.total_revenue or 0) - float(purchase_kpis.total_purchases or 0)
        margin = round(gross_profit / float(invoice_kpis.total_revenue) * 100, 1) if invoice_kpis.total_revenue else 0

        return {
            "kpis": {
                "total_revenue": float(invoice_kpis.total_revenue or 0),
                "net_revenue": float(invoice_kpis.net_revenue or 0),
                "total_purchases": float(purchase_kpis.total_purchases or 0),
                "gross_profit": gross_profit,
                "gross_margin": margin,
                "total_tax": float(invoice_kpis.total_tax or 0),
                "invoice_count": invoice_kpis.invoice_count or 0,
                "po_count": purchase_kpis.po_count or 0,
                "avg_invoice": float(invoice_kpis.avg_invoice or 0),
                "accounts_receivable": float(receivable.total_ar or 0),
                "accounts_payable": float(payable.total_ap or 0),
                "cash_in": float(payments_in.total or 0),
                "cash_out": float(payments_out.total or 0),
                "net_cash_flow": float(payments_in.total or 0) - float(payments_out.total or 0),
                "cod_gmv": float(cod_data.total_gmv or 0),
                "delivered_gmv": float(cod_data.delivered_gmv or 0),
                "return_cost": float(cod_data.return_cost or 0),
            },
            "revenue_trend": [
                {"date": str(r.date), "revenue": float(r.revenue), "invoices": r.invoices}
                for r in revenue_trend
            ],
            "period": dates,
            "company": company,
        }

    return get_cached(cache_key, compute)
