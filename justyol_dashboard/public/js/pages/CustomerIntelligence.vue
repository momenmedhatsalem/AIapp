<template>
  <div class="customer-dashboard">
    <div class="period-bar">
      <div class="period-buttons">
        <button v-for="p in filters.periods" :key="p.value" class="period-btn" :class="{ active: filters.period.value === p.value }" @click="changePeriod(p.value)">{{ p.label }}</button>
      </div>
      <div class="period-info">
        <span v-if="data">{{ data.period?.from_date }} &mdash; {{ data.period?.to_date }}</span>
        <button class="refresh-btn" @click="refresh">&#8635; Refresh</button>
      </div>
    </div>

    <div v-if="loading && !data" class="loading-state"><div class="spinner"></div><p>Loading Customer Intelligence...</p></div>

    <template v-if="data">
      <!-- KPIs -->
      <section class="kpi-grid">
        <KPICard label="Unique Customers" :value="kpis.unique_customers" format="number" icon="&#128101;" icon-color="purple" />
        <KPICard label="New Customers" :value="kpis.new_customers" format="number" icon="&#128100;" icon-color="blue" />
        <KPICard label="Repeat Customers" :value="kpis.repeat_customers" format="number" icon="&#128257;" icon-color="green" />
        <KPICard label="Repeat Rate" :value="kpis.repeat_rate" format="percent" icon="&#128200;" icon-color="teal" />
        <KPICard label="Avg Orders / Customer" :value="kpis.avg_orders_per_customer" format="number" icon="&#128202;" icon-color="cyan" />
        <KPICard label="Revenue / Customer" :value="kpis.revenue_per_customer" format="currency" :currency="currency" icon="&#128176;" icon-color="orange" />
      </section>

      <!-- Charts -->
      <section class="charts-grid">
        <ChartCard title="Customer Acquisition Trend" :option="acquisitionChartOption" :height="300" :loading="loading" :has-data="(data.acquisition_trend || []).length > 0" />
        <ChartCard title="Order Frequency Segments" :option="frequencyChartOption" :height="300" :loading="loading" :has-data="(data.frequency_distribution || []).length > 0" />
      </section>

      <!-- Top Customers -->
      <section class="table-section">
        <div class="section-card">
          <h3>Top Customers by Revenue</h3>
          <div class="table-wrap">
            <table class="data-table">
              <thead><tr><th>Customer</th><th class="num">Orders</th><th class="num">Total Spend</th><th class="num">AOV</th><th class="num">Delivered</th><th class="num">Returns</th><th class="num">Cancelled</th></tr></thead>
              <tbody>
                <tr v-for="c in data.top_customers" :key="c.customer">
                  <td class="primary">{{ c.customer_name || c.customer }}</td>
                  <td class="num">{{ c.orders }}</td>
                  <td class="num green">{{ formatCurrency(c.total_spend) }}</td>
                  <td class="num">{{ formatCurrency(c.avg_order) }}</td>
                  <td class="num teal">{{ c.delivered }}</td>
                  <td class="num red">{{ c.returns }}</td>
                  <td class="num orange">{{ c.cancelled }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- Risky Customers -->
      <section v-if="data.risky_customers && data.risky_customers.length > 0" class="table-section">
        <div class="section-card">
          <h3>&#9888; High-Risk Customers (RTO/Cancel)</h3>
          <div class="table-wrap">
            <table class="data-table">
              <thead><tr><th>Customer</th><th class="num">Orders</th><th class="num">Returns</th><th class="num">Cancelled</th><th class="num">Value</th><th class="num">Risk Score</th><th>Level</th></tr></thead>
              <tbody>
                <tr v-for="c in data.risky_customers" :key="c.customer">
                  <td class="primary">{{ c.customer_name || c.customer }}</td>
                  <td class="num">{{ c.total_orders }}</td>
                  <td class="num red">{{ c.returns }}</td>
                  <td class="num orange">{{ c.cancelled }}</td>
                  <td class="num">{{ formatCurrency(c.total_value) }}</td>
                  <td class="num" :class="c.risk_score > 60 ? 'red' : c.risk_score > 30 ? 'orange' : ''">{{ c.risk_score }}</td>
                  <td><span class="risk-badge" :class="c.risk_score > 60 ? 'high' : c.risk_score > 30 ? 'medium' : 'low'">{{ c.risk_score > 60 ? 'HIGH' : c.risk_score > 30 ? 'MED' : 'LOW' }}</span></td>
                </tr>
              </tbody>
            </table>
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
  name: "CustomerIntelligence",
  components: { KPICard, ChartCard },
  props: { company: { type: String, required: true } },
  setup(props) {
    const filters = useFilters();
    const { data, loading, refresh } = useDashboardData(
      "justyol_dashboard.api.customers.get_customer_dashboard",
      () => filters.getParams(props.company), {}
    );
    const currencyMap = { "Justyol Morocco": "MAD", "Justyol China": "USD", "Justyol Holding": "USD", "Maslak LTD": "TRY" };
    const currency = computed(() => currencyMap[props.company] || "MAD");
    const kpis = computed(() => data.value?.kpis || {});
    function changePeriod(p) { filters.setPeriod(p); refresh(); }
    function formatCurrency(v) { if (!v && v !== 0) return "--"; return Number(v).toLocaleString("en-US", { maximumFractionDigits: 0 }) + " " + currency.value; }

    const acquisitionChartOption = computed(() => {
      const t = data.value?.acquisition_trend || [];
      return {
        tooltip: { trigger: "axis" },
        grid: { left: 50, right: 20, top: 20, bottom: 40 },
        xAxis: { type: "category", data: t.map(d => d.date) },
        yAxis: { type: "value" },
        series: [{ name: "New Customers", type: "bar", data: t.map(d => d.new_customers), itemStyle: { color: "#6366f1", borderRadius: [4,4,0,0] }, barMaxWidth: 20 }],
      };
    });

    const frequencyChartOption = computed(() => {
      const f = data.value?.frequency_distribution || [];
      const colors = ["#3b82f6", "#22c55e", "#f97316", "#a855f7"];
      return {
        tooltip: { trigger: "item" },
        legend: { bottom: 0 },
        series: [{ type: "pie", radius: ["40%", "70%"], center: ["50%", "45%"],
          data: f.map((s, i) => ({ name: s.segment, value: s.customers, itemStyle: { color: colors[i % colors.length] } })),
          label: { show: true, formatter: "{b}: {c}" },
        }],
      };
    });

    return { filters, data, loading, refresh, currency, kpis, changePeriod, formatCurrency, acquisitionChartOption, frequencyChartOption };
  },
};
</script>

<style scoped>
.customer-dashboard { max-width: 1400px; margin: 0 auto; }
.period-bar { display: flex; justify-content: space-between; align-items: center; background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 12px 20px; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.period-buttons { display: flex; gap: 8px; flex-wrap: wrap; }
.period-btn { background: var(--bg-primary); border: 1px solid var(--border); color: var(--text-muted); padding: 8px 16px; border-radius: 8px; font-size: 12px; cursor: pointer; transition: all 0.2s; font-family: inherit; }
.period-btn:hover { border-color: var(--accent); color: var(--text-secondary); }
.period-btn.active { background: var(--accent); border-color: var(--accent); color: white; }
.period-info { display: flex; align-items: center; gap: 12px; font-size: 12px; color: var(--text-muted); }
.refresh-btn { background: var(--accent); border: none; color: white; padding: 8px 14px; border-radius: 6px; cursor: pointer; font-size: 12px; font-family: inherit; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }
.charts-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 16px; margin-bottom: 24px; }
.table-section { margin-bottom: 24px; }
.section-card { background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid var(--border); }
.section-card h3 { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 16px; }
.table-wrap { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border); color: var(--text-dim); font-size: 11px; font-weight: 600; text-transform: uppercase; }
.data-table td { padding: 10px 12px; border-bottom: 1px solid rgba(51,65,85,0.2); color: var(--text-secondary); }
.data-table th.num, .data-table td.num { text-align: right; }
.data-table td.primary { font-weight: 500; color: var(--text-primary); }
.data-table td.green { color: #22c55e; } .data-table td.red { color: #ef4444; } .data-table td.orange { color: #f97316; } .data-table td.teal { color: #14b8a6; }
.risk-badge { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; }
.risk-badge.high { background: rgba(239,68,68,0.15); color: #ef4444; }
.risk-badge.medium { background: rgba(249,115,22,0.15); color: #f97316; }
.risk-badge.low { background: rgba(34,197,94,0.15); color: #22c55e; }
.loading-state { display: flex; flex-direction: column; align-items: center; padding: 80px; color: var(--text-muted); gap: 16px; }
.spinner { width: 40px; height: 40px; border: 3px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 768px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } .charts-grid { grid-template-columns: 1fr; } }
</style>
