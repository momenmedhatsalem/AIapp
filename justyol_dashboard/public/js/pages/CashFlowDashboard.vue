<template>
  <div class="cashflow-dashboard">
    <div class="period-bar">
      <div class="period-buttons">
        <button v-for="p in filters.periods" :key="p.value" class="period-btn" :class="{ active: filters.period.value === p.value }" @click="changePeriod(p.value)">{{ p.label }}</button>
      </div>
      <div class="period-info">
        <span v-if="data">{{ data.period?.from_date }} &mdash; {{ data.period?.to_date }}</span>
        <button class="refresh-btn" @click="refresh">&#8635; Refresh</button>
      </div>
    </div>

    <div v-if="loading && !data" class="loading-state"><div class="spinner"></div><p>Loading Cash Flow...</p></div>

    <template v-if="data">
      <!-- KPIs -->
      <section class="kpi-grid">
        <KPICard label="Total GMV" :value="kpis.total_gmv" format="currency" :currency="currency" icon="&#128176;" icon-color="purple" />
        <KPICard label="Delivered GMV" :value="kpis.delivered_gmv" format="currency" :currency="currency" icon="&#127919;" icon-color="green" />
        <KPICard label="Cash Received" :value="kpis.cash_received" format="currency" :currency="currency" icon="&#128178;" icon-color="teal" />
        <KPICard label="Cash Gap" :value="kpis.cash_gap" format="currency" :currency="currency" icon="&#8987;" icon-color="orange" />
        <KPICard label="Collection Rate" :value="kpis.collection_rate" format="percent" icon="&#128202;" icon-color="blue" />
        <KPICard label="Returns Cost" :value="kpis.return_cost" format="currency" :currency="currency" icon="&#128260;" icon-color="red" />
      </section>

      <!-- Cash Flow Summary -->
      <section class="flow-section">
        <div class="section-card">
          <h3>Cash Flow Summary</h3>
          <div class="flow-grid">
            <div class="flow-item in"><span class="flow-icon">&#8599;</span><span class="flow-label">Cash In</span><span class="flow-value">{{ formatCurrency(kpis.cash_received) }}</span><span class="flow-count">{{ kpis.receive_count }} payments</span></div>
            <div class="flow-item out"><span class="flow-icon">&#8600;</span><span class="flow-label">Cash Out</span><span class="flow-value">{{ formatCurrency(kpis.cash_paid) }}</span><span class="flow-count">{{ kpis.pay_count }} payments</span></div>
            <div class="flow-item net" :class="kpis.net_cash >= 0 ? 'positive' : 'negative'"><span class="flow-icon">&#128178;</span><span class="flow-label">Net Cash</span><span class="flow-value">{{ formatCurrency(kpis.net_cash) }}</span></div>
          </div>
        </div>
      </section>

      <!-- COD Pipeline -->
      <section class="pipeline-section">
        <div class="section-card">
          <h3>COD Collection Pipeline</h3>
          <div class="pipeline-rows">
            <div v-for="stage in data.collection_pipeline" :key="stage.stage" class="pipeline-row">
              <span class="pipeline-label">{{ stage.stage }}</span>
              <div class="pipeline-bar-bg">
                <div class="pipeline-bar" :style="{ width: pipelineWidth(stage.value) + '%', background: stageColor(stage.stage) }"></div>
              </div>
              <span class="pipeline-orders">{{ stage.orders }} orders</span>
              <span class="pipeline-value">{{ formatCurrency(stage.value) }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Charts -->
      <section class="charts-grid">
        <ChartCard title="Daily Cash Flow" :option="flowChartOption" :height="300" :loading="loading" :has-data="(data.daily_flow || []).length > 0" />
        <ChartCard title="GMV: Delivered vs Returns" :option="gmvChartOption" :height="300" :loading="loading" :has-data="(data.gmv_trend || []).length > 0" />
      </section>

      <!-- Aging Analysis -->
      <section v-if="data.aging && data.aging.length > 0" class="aging-section">
        <div class="section-card">
          <h3>Receivables Aging</h3>
          <div class="aging-grid">
            <div v-for="bucket in data.aging" :key="bucket.bucket" class="aging-item" :class="agingClass(bucket.bucket)">
              <span class="aging-bucket">{{ bucket.bucket }}</span>
              <span class="aging-count">{{ bucket.count }} invoices</span>
              <span class="aging-amount">{{ formatCurrency(bucket.amount) }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- In-Transit Value -->
      <section class="transit-section">
        <div class="section-card">
          <h3>Value In Transit</h3>
          <div class="transit-grid">
            <div class="transit-item"><span class="transit-label">In Transit</span><span class="transit-value blue">{{ formatCurrency(kpis.in_transit_value) }}</span></div>
            <div class="transit-item"><span class="transit-label">Out for Delivery</span><span class="transit-value cyan">{{ formatCurrency(kpis.out_for_delivery_value) }}</span></div>
            <div class="transit-item"><span class="transit-label">Cancelled Value</span><span class="transit-value red">{{ formatCurrency(kpis.cancelled_value) }}</span></div>
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
  name: "CashFlowDashboard",
  components: { KPICard, ChartCard },
  props: { company: { type: String, required: true } },
  setup(props) {
    const filters = useFilters();
    const { data, loading, refresh } = useDashboardData(
      "justyol_dashboard.api.cashflow.get_cashflow_dashboard",
      () => filters.getParams(props.company), {}
    );
    const currencyMap = { "Justyol Morocco": "MAD", "Justyol China": "USD", "Justyol Holding": "USD", "Maslak LTD": "TRY" };
    const currency = computed(() => currencyMap[props.company] || "MAD");
    const kpis = computed(() => data.value?.kpis || {});
    function changePeriod(p) { filters.setPeriod(p); refresh(); }
    function formatCurrency(v) { if (!v && v !== 0) return "--"; return Number(v).toLocaleString("en-US", { maximumFractionDigits: 0 }) + " " + currency.value; }

    const maxPipelineValue = computed(() => {
      if (!data.value?.collection_pipeline) return 1;
      return Math.max(...data.value.collection_pipeline.map(s => s.value), 1);
    });
    function pipelineWidth(v) { return (v / maxPipelineValue.value) * 100; }
    function stageColor(stage) {
      const m = { Delivered: "#22c55e", "In Transit": "#3b82f6", "Out for Delivery": "#f97316", Return: "#ef4444", Pending: "#eab308" };
      return m[stage] || "#6366f1";
    }
    function agingClass(b) { return b.includes("30+") ? "danger" : b.includes("16") ? "warn" : "ok"; }

    const flowChartOption = computed(() => {
      const f = data.value?.daily_flow || [];
      return {
        tooltip: { trigger: "axis" }, legend: { top: 0 },
        grid: { left: 60, right: 20, top: 30, bottom: 40 },
        xAxis: { type: "category", data: f.map(d => d.date) },
        yAxis: { type: "value" },
        series: [
          { name: "Cash In", type: "bar", data: f.map(d => d.cash_in), itemStyle: { color: "#22c55e", borderRadius: [4,4,0,0] }, barMaxWidth: 16 },
          { name: "Cash Out", type: "bar", data: f.map(d => d.cash_out), itemStyle: { color: "#ef4444", borderRadius: [4,4,0,0] }, barMaxWidth: 16 },
        ],
      };
    });

    const gmvChartOption = computed(() => {
      const g = data.value?.gmv_trend || [];
      return {
        tooltip: { trigger: "axis" }, legend: { top: 0 },
        grid: { left: 60, right: 20, top: 30, bottom: 40 },
        xAxis: { type: "category", data: g.map(d => d.date) },
        yAxis: { type: "value" },
        series: [
          { name: "Delivered", type: "line", data: g.map(d => d.delivered), smooth: true, lineStyle: { color: "#22c55e" }, itemStyle: { color: "#22c55e" }, areaStyle: { color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: "rgba(34,197,94,0.3)" }, { offset: 1, color: "rgba(34,197,94,0)" }] } } },
          { name: "Returns", type: "line", data: g.map(d => d.returned), smooth: true, lineStyle: { color: "#ef4444" }, itemStyle: { color: "#ef4444" } },
        ],
      };
    });

    return { filters, data, loading, refresh, currency, kpis, changePeriod, formatCurrency, pipelineWidth, stageColor, agingClass, flowChartOption, gmvChartOption };
  },
};
</script>

<style scoped>
.cashflow-dashboard { max-width: 1400px; margin: 0 auto; }
.period-bar { display: flex; justify-content: space-between; align-items: center; background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 12px 20px; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.period-buttons { display: flex; gap: 8px; flex-wrap: wrap; }
.period-btn { background: var(--bg-primary); border: 1px solid var(--border); color: var(--text-muted); padding: 8px 16px; border-radius: 8px; font-size: 12px; cursor: pointer; transition: all 0.2s; font-family: inherit; }
.period-btn:hover { border-color: var(--accent); color: var(--text-secondary); }
.period-btn.active { background: var(--accent); border-color: var(--accent); color: white; }
.period-info { display: flex; align-items: center; gap: 12px; font-size: 12px; color: var(--text-muted); }
.refresh-btn { background: var(--accent); border: none; color: white; padding: 8px 14px; border-radius: 6px; cursor: pointer; font-size: 12px; font-family: inherit; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }
.flow-section, .pipeline-section, .aging-section, .transit-section { margin-bottom: 24px; }
.section-card { background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid var(--border); }
.section-card h3 { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 16px; }
.flow-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.flow-item { text-align: center; padding: 16px; border-radius: 10px; background: var(--bg-primary); }
.flow-icon { font-size: 24px; display: block; margin-bottom: 8px; }
.flow-label { display: block; font-size: 11px; color: var(--text-dim); text-transform: uppercase; margin-bottom: 6px; }
.flow-value { display: block; font-size: 20px; font-weight: 700; }
.flow-item.in .flow-value { color: #22c55e; } .flow-item.out .flow-value { color: #ef4444; }
.flow-item.positive .flow-value { color: #22c55e; } .flow-item.negative .flow-value { color: #ef4444; }
.flow-count { display: block; font-size: 11px; color: var(--text-dim); margin-top: 4px; }
.pipeline-rows { display: flex; flex-direction: column; gap: 10px; }
.pipeline-row { display: grid; grid-template-columns: 120px 1fr 90px 120px; align-items: center; gap: 12px; }
.pipeline-label { font-size: 12px; color: var(--text-muted); font-weight: 500; }
.pipeline-bar-bg { height: 24px; background: var(--bg-primary); border-radius: 4px; overflow: hidden; }
.pipeline-bar { height: 100%; border-radius: 4px; transition: width 0.5s ease; }
.pipeline-orders { font-size: 12px; color: var(--text-dim); text-align: right; }
.pipeline-value { font-size: 13px; font-weight: 600; color: var(--text-primary); text-align: right; }
.charts-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 16px; margin-bottom: 24px; }
.aging-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 14px; }
.aging-item { text-align: center; padding: 14px; border-radius: 10px; background: var(--bg-primary); border: 1px solid var(--border); }
.aging-item.danger { border-color: rgba(239,68,68,0.3); }
.aging-item.warn { border-color: rgba(249,115,22,0.3); }
.aging-bucket { display: block; font-size: 13px; font-weight: 600; color: var(--text-primary); margin-bottom: 6px; }
.aging-count { display: block; font-size: 11px; color: var(--text-dim); margin-bottom: 4px; }
.aging-amount { display: block; font-size: 16px; font-weight: 700; color: var(--text-primary); }
.aging-item.danger .aging-amount { color: #ef4444; }
.aging-item.warn .aging-amount { color: #f97316; }
.transit-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.transit-item { text-align: center; }
.transit-label { display: block; font-size: 11px; color: var(--text-dim); text-transform: uppercase; margin-bottom: 6px; }
.transit-value { font-size: 22px; font-weight: 700; }
.transit-value.blue { color: #3b82f6; } .transit-value.cyan { color: #06b6d4; } .transit-value.red { color: #ef4444; }
.loading-state { display: flex; flex-direction: column; align-items: center; padding: 80px; color: var(--text-muted); gap: 16px; }
.spinner { width: 40px; height: 40px; border: 3px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 768px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } .charts-grid { grid-template-columns: 1fr; } .flow-grid, .transit-grid { grid-template-columns: 1fr; } .pipeline-row { grid-template-columns: 80px 1fr 70px 90px; } }
</style>
