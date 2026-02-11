<template>
  <div class="finance-dashboard">
    <!-- Period Selector -->
    <div class="period-bar">
      <div class="period-buttons">
        <button
          v-for="p in filters.periods"
          :key="p.value"
          class="period-btn"
          :class="{ active: filters.period.value === p.value }"
          @click="changePeriod(p.value)"
        >{{ p.label }}</button>
      </div>
      <div class="period-info">
        <span v-if="data">{{ data.period?.from_date }} &mdash; {{ data.period?.to_date }}</span>
        <button class="refresh-btn" @click="refresh">&#8635; Refresh</button>
      </div>
    </div>

    <div v-if="loading && !data" class="loading-state">
      <div class="spinner"></div>
      <p>Loading Finance Data...</p>
    </div>

    <template v-if="data">
      <!-- Primary Financial KPIs -->
      <section class="kpi-grid">
        <KPICard label="Total Revenue" :value="kpis.total_revenue" format="currency" :currency="currency" icon="&#128176;" icon-color="green" />
        <KPICard label="Total Purchases" :value="kpis.total_purchases" format="currency" :currency="currency" icon="&#128722;" icon-color="red" />
        <KPICard label="Gross Profit" :value="kpis.gross_profit" format="currency" :currency="currency" icon="&#128200;" icon-color="teal" />
        <KPICard label="Gross Margin" :value="kpis.gross_margin" format="percent" icon="&#128202;" icon-color="purple" />
      </section>

      <!-- Cash Flow + AR/AP -->
      <section class="kpi-grid secondary">
        <KPICard label="Cash In (Received)" :value="kpis.cash_in" format="currency" :currency="currency" icon="&#8599;" icon-color="green" />
        <KPICard label="Cash Out (Paid)" :value="kpis.cash_out" format="currency" :currency="currency" icon="&#8600;" icon-color="red" />
        <KPICard label="Net Cash Flow" :value="kpis.net_cash_flow" format="currency" :currency="currency" icon="&#128178;" icon-color="blue" />
        <KPICard label="Accounts Receivable" :value="kpis.accounts_receivable" format="currency" :currency="currency" icon="&#128203;" icon-color="orange" />
        <KPICard label="Accounts Payable" :value="kpis.accounts_payable" format="currency" :currency="currency" icon="&#128196;" icon-color="yellow" />
      </section>

      <!-- COD Metrics -->
      <section class="cod-section">
        <div class="section-card">
          <h3>COD Tracking</h3>
          <div class="cod-grid">
            <div class="cod-metric">
              <span class="cod-label">Total GMV (Orders)</span>
              <span class="cod-value">{{ formatCurrency(kpis.cod_gmv) }}</span>
            </div>
            <div class="cod-metric">
              <span class="cod-label">Delivered GMV</span>
              <span class="cod-value green">{{ formatCurrency(kpis.delivered_gmv) }}</span>
            </div>
            <div class="cod-metric">
              <span class="cod-label">Return Cost</span>
              <span class="cod-value red">{{ formatCurrency(kpis.return_cost) }}</span>
            </div>
            <div class="cod-metric">
              <span class="cod-label">Collection Rate</span>
              <span class="cod-value blue">{{ collectionRate }}%</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Revenue Chart -->
      <section class="chart-section">
        <ChartCard
          title="Revenue Trend"
          :option="revenueChartOption"
          :height="320"
          :full-width="true"
          :loading="loading"
          :has-data="(data.revenue_trend || []).length > 0"
        />
      </section>

      <!-- Summary Cards -->
      <section class="summary-grid">
        <div class="section-card">
          <h3>Invoicing</h3>
          <div class="stat-row"><span>Sales Invoices</span><span class="stat-val">{{ kpis.invoice_count }}</span></div>
          <div class="stat-row"><span>Purchase Orders</span><span class="stat-val">{{ kpis.po_count }}</span></div>
          <div class="stat-row"><span>Avg Invoice Value</span><span class="stat-val">{{ formatCurrency(kpis.avg_invoice) }}</span></div>
          <div class="stat-row"><span>Total Tax</span><span class="stat-val">{{ formatCurrency(kpis.total_tax) }}</span></div>
        </div>
        <div class="section-card">
          <h3>Quick Actions</h3>
          <div class="quick-actions">
            <a href="/app/sales-invoice" class="action-btn">View Sales Invoices</a>
            <a href="/app/purchase-invoice" class="action-btn">View Purchase Invoices</a>
            <a href="/app/payment-entry" class="action-btn">View Payments</a>
            <a href="/app/query-report/Profit and Loss Statement" class="action-btn">P&L Report</a>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script>
import { computed } from "vue";
import KPICard from "../components/KPICard.vue";
import ChartCard from "../components/ChartCard.vue";
import { useDashboardData, useFilters } from "../composables/useDashboardData.js";

export default {
  name: "FinanceDashboard",
  components: { KPICard, ChartCard },
  props: {
    company: { type: String, required: true },
  },

  setup(props) {
    const filters = useFilters();

    const { data, loading, refresh } = useDashboardData(
      "justyol_dashboard.api.finance.get_finance_dashboard",
      () => filters.getParams(props.company),
      {}
    );

    const currencyMap = { "Justyol Morocco": "MAD", "Justyol China": "USD", "Justyol Holding": "USD", "Maslak LTD": "TRY" };
    const currency = computed(() => currencyMap[props.company] || "MAD");
    const kpis = computed(() => data.value?.kpis || {});

    function changePeriod(period) {
      filters.setPeriod(period);
      refresh();
    }

    function formatCurrency(val) {
      if (!val && val !== 0) return "--";
      return Number(val).toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + " " + currency.value;
    }

    const collectionRate = computed(() => {
      const gmv = kpis.value.cod_gmv;
      const delivered = kpis.value.delivered_gmv;
      if (!gmv) return 0;
      return ((delivered / gmv) * 100).toFixed(1);
    });

    const revenueChartOption = computed(() => {
      const trend = data.value?.revenue_trend || [];
      return {
        tooltip: { trigger: "axis" },
        grid: { left: 60, right: 40, top: 40, bottom: 40 },
        xAxis: { type: "category", data: trend.map((d) => d.date) },
        yAxis: { type: "value", name: currency.value },
        series: [
          {
            name: "Revenue",
            type: "line",
            data: trend.map((d) => d.revenue),
            smooth: true,
            lineStyle: { color: "#22c55e" },
            itemStyle: { color: "#22c55e" },
            areaStyle: {
              color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1,
                colorStops: [{ offset: 0, color: "rgba(34,197,94,0.3)" }, { offset: 1, color: "rgba(34,197,94,0)" }]
              },
            },
          },
          {
            name: "Invoices",
            type: "bar",
            data: trend.map((d) => d.invoices),
            yAxisIndex: 0,
            itemStyle: { color: "#6366f1", borderRadius: [4, 4, 0, 0] },
            barMaxWidth: 20,
          },
        ],
      };
    });

    return {
      filters, data, loading, refresh,
      currency, kpis, changePeriod,
      formatCurrency, collectionRate, revenueChartOption,
    };
  },
};
</script>

<style scoped>
.finance-dashboard { max-width: 1400px; margin: 0 auto; }

.period-bar {
  display: flex; justify-content: space-between; align-items: center;
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: 12px; padding: 12px 20px; margin-bottom: 20px;
  flex-wrap: wrap; gap: 12px;
}
.period-buttons { display: flex; gap: 8px; flex-wrap: wrap; }
.period-btn {
  background: var(--bg-primary); border: 1px solid var(--border);
  color: var(--text-muted); padding: 8px 16px; border-radius: 8px;
  font-size: 12px; cursor: pointer; transition: all 0.2s; font-family: inherit;
}
.period-btn:hover { border-color: var(--accent); color: var(--text-secondary); }
.period-btn.active { background: var(--accent); border-color: var(--accent); color: white; }
.period-info { display: flex; align-items: center; gap: 12px; font-size: 12px; color: var(--text-muted); }
.refresh-btn {
  background: var(--accent); border: none; color: white;
  padding: 8px 14px; border-radius: 6px; cursor: pointer;
  font-size: 12px; font-family: inherit;
}

.kpi-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px; margin-bottom: 20px;
}
.kpi-grid.secondary { margin-bottom: 24px; }

.cod-section { margin-bottom: 24px; }
.section-card {
  background: var(--bg-card); border-radius: 12px; padding: 20px;
  border: 1px solid var(--border);
}
.section-card h3 {
  font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 16px;
}
.cod-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; }
.cod-metric { text-align: center; }
.cod-label { display: block; font-size: 11px; color: var(--text-dim); text-transform: uppercase; margin-bottom: 6px; }
.cod-value { font-size: 22px; font-weight: 700; color: var(--text-primary); }
.cod-value.green { color: #22c55e; }
.cod-value.red { color: #ef4444; }
.cod-value.blue { color: #3b82f6; }

.chart-section { margin-bottom: 24px; }

.summary-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px; margin-bottom: 24px;
}
.stat-row {
  display: flex; justify-content: space-between; padding: 10px 0;
  border-bottom: 1px solid rgba(51, 65, 85, 0.2); font-size: 13px; color: var(--text-muted);
}
.stat-val { font-weight: 600; color: var(--text-primary); }
.quick-actions { display: flex; flex-direction: column; gap: 10px; }
.action-btn {
  display: block; padding: 10px 16px; background: rgba(99, 102, 241, 0.1);
  border: 1px solid var(--border); border-radius: 8px;
  color: var(--text-secondary); text-decoration: none; font-size: 13px;
  transition: all 0.2s;
}
.action-btn:hover { border-color: var(--accent); color: var(--text-primary); }

.loading-state {
  display: flex; flex-direction: column; align-items: center;
  padding: 80px; color: var(--text-muted); gap: 16px;
}
.spinner {
  width: 40px; height: 40px; border: 3px solid var(--border);
  border-top-color: var(--accent); border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 768px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .cod-grid { grid-template-columns: repeat(2, 1fr); }
  .summary-grid { grid-template-columns: 1fr; }
}
</style>
