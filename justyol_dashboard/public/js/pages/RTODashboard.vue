<template>
  <div class="rto-dashboard">
    <div class="period-bar">
      <div class="period-buttons">
        <button v-for="p in filters.periods" :key="p.value" class="period-btn" :class="{ active: filters.period.value === p.value }" @click="changePeriod(p.value)">{{ p.label }}</button>
      </div>
      <div class="period-info">
        <span v-if="data">{{ data.period?.from_date }} &mdash; {{ data.period?.to_date }}</span>
        <button class="refresh-btn" @click="refresh">&#8635; Refresh</button>
      </div>
    </div>

    <div v-if="loading && !data" class="loading-state"><div class="spinner"></div><p>Loading RTO Analytics...</p></div>

    <template v-if="data">
      <!-- KPIs -->
      <section class="kpi-grid">
        <KPICard label="Total Shipped" :value="kpis.total_shipped" format="number" icon="&#128666;" icon-color="blue" />
        <KPICard label="Delivered" :value="kpis.delivered" format="number" icon="&#127919;" icon-color="green" />
        <KPICard label="Returns (RTO)" :value="kpis.returns" format="number" icon="&#128260;" icon-color="red" />
        <KPICard label="RTO Rate" :value="kpis.rto_rate" format="percent" icon="&#128200;" icon-color="orange"
          :trend="kpis.prev_rto_rate ? ((kpis.rto_rate - kpis.prev_rto_rate) / kpis.prev_rto_rate) * 100 : null"
          :trend-inverse="true" />
        <KPICard label="Return Value Lost" :value="kpis.return_value" format="currency" :currency="currency" icon="&#128176;" icon-color="red" />
        <KPICard label="Revenue After RTO" :value="kpis.revenue_after_rto" format="currency" :currency="currency" icon="&#128178;" icon-color="teal" />
      </section>

      <!-- RTO Cost Impact -->
      <section class="impact-section">
        <div class="section-card">
          <h3>RTO Financial Impact</h3>
          <div class="impact-grid">
            <div class="impact-item">
              <span class="impact-label">Delivered Value</span>
              <span class="impact-value green">{{ formatCurrency(kpis.delivered_value) }}</span>
            </div>
            <div class="impact-item">
              <span class="impact-label">Return Value</span>
              <span class="impact-value red">{{ formatCurrency(kpis.return_value) }}</span>
            </div>
            <div class="impact-item">
              <span class="impact-label">Est. Total RTO Cost</span>
              <span class="impact-value red">{{ formatCurrency(kpis.total_rto_cost) }}</span>
            </div>
            <div class="impact-item">
              <span class="impact-label">Delivery Rate</span>
              <span class="impact-value blue">{{ kpis.delivery_rate }}%</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Charts -->
      <section class="charts-grid">
        <ChartCard title="RTO Trend" :option="trendChartOption" :height="300" :loading="loading" :has-data="(data.rto_trend || []).length > 0" />
        <ChartCard title="Return Reasons" :option="reasonsChartOption" :height="300" :loading="loading" :has-data="(data.rto_reasons || []).length > 0" />
      </section>

      <!-- High-RTO Products -->
      <section class="tables-grid">
        <div class="section-card">
          <h3>High-RTO Products</h3>
          <div class="table-wrap">
            <table class="data-table">
              <thead><tr><th>Product</th><th class="num">Returns</th><th class="num">Qty</th><th class="num">Value Lost</th></tr></thead>
              <tbody>
                <tr v-for="p in data.rto_products" :key="p.item_code">
                  <td class="primary">{{ p.item_name || p.item_code }}</td>
                  <td class="num red">{{ p.return_orders }}</td>
                  <td class="num">{{ p.return_qty }}</td>
                  <td class="num red">{{ formatCurrency(p.return_value) }}</td>
                </tr>
                <tr v-if="!data.rto_products?.length"><td colspan="4" class="empty">No return data</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- High-RTO Zones -->
        <div class="section-card">
          <h3>High-RTO Zones</h3>
          <div class="table-wrap">
            <table class="data-table">
              <thead><tr><th>Zone / City</th><th class="num">Orders</th><th class="num">Returns</th><th class="num">RTO %</th><th>Risk</th></tr></thead>
              <tbody>
                <tr v-for="z in data.rto_zones" :key="z.zone">
                  <td class="primary">{{ z.zone }}</td>
                  <td class="num">{{ z.total_orders }}</td>
                  <td class="num red">{{ z.returns }}</td>
                  <td class="num" :class="z.rto_rate > 30 ? 'red' : z.rto_rate > 15 ? 'orange' : 'green'">{{ z.rto_rate }}%</td>
                  <td><span class="risk-badge" :class="z.rto_rate > 30 ? 'high' : z.rto_rate > 15 ? 'medium' : 'low'">{{ z.rto_rate > 30 ? 'HIGH' : z.rto_rate > 15 ? 'MED' : 'LOW' }}</span></td>
                </tr>
                <tr v-if="!data.rto_zones?.length"><td colspan="5" class="empty">No zone data</td></tr>
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
  name: "RTODashboard",
  components: { KPICard, ChartCard },
  props: { company: { type: String, required: true } },
  setup(props) {
    const filters = useFilters();
    const { data, loading, refresh } = useDashboardData(
      "justyol_dashboard.api.rto.get_rto_dashboard",
      () => filters.getParams(props.company),
      { realtimeEvent: "sales_order_update" }
    );
    const currencyMap = { "Justyol Morocco": "MAD", "Justyol China": "USD", "Justyol Holding": "USD", "Maslak LTD": "TRY" };
    const currency = computed(() => currencyMap[props.company] || "MAD");
    const kpis = computed(() => data.value?.kpis || {});

    function changePeriod(p) { filters.setPeriod(p); refresh(); }
    function formatCurrency(v) {
      if (!v && v !== 0) return "--";
      return Number(v).toLocaleString("en-US", { maximumFractionDigits: 0 }) + " " + currency.value;
    }

    const trendChartOption = computed(() => {
      const t = data.value?.rto_trend || [];
      return {
        tooltip: { trigger: "axis" },
        legend: { top: 0 },
        grid: { left: 50, right: 30, top: 30, bottom: 40 },
        xAxis: { type: "category", data: t.map(d => d.date) },
        yAxis: [{ type: "value", name: "Orders" }, { type: "value", name: "RTO %", max: 100 }],
        series: [
          { name: "Delivered", type: "bar", data: t.map(d => d.delivered), itemStyle: { color: "#22c55e", borderRadius: [4,4,0,0] }, barMaxWidth: 16 },
          { name: "Returns", type: "bar", data: t.map(d => d.returns), itemStyle: { color: "#ef4444", borderRadius: [4,4,0,0] }, barMaxWidth: 16 },
          { name: "RTO Rate", type: "line", yAxisIndex: 1, data: t.map(d => d.rto_rate), smooth: true, lineStyle: { color: "#f97316" }, itemStyle: { color: "#f97316" } },
        ],
      };
    });

    const reasonsChartOption = computed(() => {
      const r = data.value?.rto_reasons || [];
      return {
        tooltip: { trigger: "axis" },
        grid: { left: 140, right: 40, top: 10, bottom: 10 },
        xAxis: { type: "value" },
        yAxis: { type: "category", data: r.map(x => x.reason).reverse() },
        series: [{ type: "bar", data: r.map(x => x.count).reverse(), itemStyle: { color: "#ef4444", borderRadius: [0,4,4,0] }, barMaxWidth: 20 }],
      };
    });

    return { filters, data, loading, refresh, currency, kpis, changePeriod, formatCurrency, trendChartOption, reasonsChartOption };
  },
};
</script>

<style scoped>
.rto-dashboard { max-width: 1400px; margin: 0 auto; }
.period-bar { display: flex; justify-content: space-between; align-items: center; background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 12px 20px; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.period-buttons { display: flex; gap: 8px; flex-wrap: wrap; }
.period-btn { background: var(--bg-primary); border: 1px solid var(--border); color: var(--text-muted); padding: 8px 16px; border-radius: 8px; font-size: 12px; cursor: pointer; transition: all 0.2s; font-family: inherit; }
.period-btn:hover { border-color: var(--accent); color: var(--text-secondary); }
.period-btn.active { background: var(--accent); border-color: var(--accent); color: white; }
.period-info { display: flex; align-items: center; gap: 12px; font-size: 12px; color: var(--text-muted); }
.refresh-btn { background: var(--accent); border: none; color: white; padding: 8px 14px; border-radius: 6px; cursor: pointer; font-size: 12px; font-family: inherit; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }
.impact-section { margin-bottom: 24px; }
.section-card { background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid var(--border); }
.section-card h3 { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 16px; }
.impact-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; }
.impact-item { text-align: center; }
.impact-label { display: block; font-size: 11px; color: var(--text-dim); text-transform: uppercase; margin-bottom: 6px; }
.impact-value { font-size: 22px; font-weight: 700; color: var(--text-primary); }
.impact-value.green { color: #22c55e; } .impact-value.red { color: #ef4444; } .impact-value.blue { color: #3b82f6; }
.charts-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 16px; margin-bottom: 24px; }
.tables-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 16px; margin-bottom: 24px; }
.table-wrap { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border); color: var(--text-dim); font-size: 11px; font-weight: 600; text-transform: uppercase; }
.data-table td { padding: 10px 12px; border-bottom: 1px solid rgba(51,65,85,0.2); color: var(--text-secondary); }
.data-table th.num, .data-table td.num { text-align: right; }
.data-table td.primary { font-weight: 500; color: var(--text-primary); }
.data-table td.red { color: #ef4444; } .data-table td.orange { color: #f97316; } .data-table td.green { color: #22c55e; }
.data-table td.empty { text-align: center; color: var(--text-dim); padding: 24px; }
.risk-badge { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; }
.risk-badge.high { background: rgba(239,68,68,0.15); color: #ef4444; }
.risk-badge.medium { background: rgba(249,115,22,0.15); color: #f97316; }
.risk-badge.low { background: rgba(34,197,94,0.15); color: #22c55e; }
.loading-state { display: flex; flex-direction: column; align-items: center; padding: 80px; color: var(--text-muted); gap: 16px; }
.spinner { width: 40px; height: 40px; border: 3px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 768px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } .charts-grid, .tables-grid { grid-template-columns: 1fr; } }
</style>
