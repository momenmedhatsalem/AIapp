<template>
  <div class="marketing-dashboard">
    <div class="period-bar">
      <div class="period-buttons">
        <button v-for="p in filters.periods" :key="p.value" class="period-btn" :class="{ active: filters.period.value === p.value }" @click="changePeriod(p.value)">{{ p.label }}</button>
      </div>
      <div class="period-info">
        <span v-if="data">{{ data.period?.from_date }} &mdash; {{ data.period?.to_date }}</span>
        <button class="refresh-btn" @click="refresh">&#8635; Refresh</button>
      </div>
    </div>

    <div v-if="loading && !data" class="loading-state"><div class="spinner"></div><p>Loading Marketing Analytics...</p></div>

    <template v-if="data">
      <!-- KPIs -->
      <section class="kpi-grid">
        <KPICard label="Total Orders" :value="kpis.total_orders" format="number" icon="&#128230;" icon-color="purple" />
        <KPICard label="Total GMV" :value="kpis.total_gmv" format="currency" :currency="currency" icon="&#128176;" icon-color="blue" />
        <KPICard label="Confirmation Rate" :value="kpis.confirmation_rate" format="percent" icon="&#9989;" icon-color="green" />
        <KPICard label="Delivery Rate" :value="kpis.delivery_rate" format="percent" icon="&#127919;" icon-color="teal" />
        <KPICard label="Effective Rate" :value="kpis.effective_rate" format="percent" icon="&#128202;" icon-color="cyan"
          :sub-value="'Order → Delivered'" sub-label="Full funnel" />
        <KPICard label="Revenue After RTO" :value="kpis.revenue_after_rto" format="currency" :currency="currency" icon="&#128178;" icon-color="orange" />
      </section>

      <!-- Full Funnel -->
      <section class="funnel-section">
        <div class="section-card">
          <h3>Full Conversion Funnel</h3>
          <div class="funnel-container">
            <div v-for="(stage, idx) in data.funnel_stages" :key="stage.stage" class="funnel-row">
              <span class="funnel-label">{{ stage.stage }}</span>
              <div class="funnel-bar-bg">
                <div class="funnel-bar" :style="{ width: funnelWidth(stage.count) + '%', background: stage.color }"></div>
              </div>
              <div class="funnel-metrics">
                <span class="funnel-count">{{ formatNumber(stage.count) }}</span>
                <span class="funnel-value">{{ formatCurrency(stage.value) }}</span>
              </div>
              <span v-if="idx > 0" class="funnel-drop" :class="dropRate(idx) > 30 ? 'red' : 'green'">{{ dropRate(idx) }}% drop</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Charts -->
      <section class="charts-grid">
        <ChartCard title="Daily Performance" :option="dailyChartOption" :height="320" :loading="loading" :has-data="(data.daily_trend || []).length > 0" />
        <ChartCard title="Source Breakdown" :option="sourceChartOption" :height="320" :loading="loading" :has-data="(data.source_breakdown || []).length > 0" />
      </section>

      <!-- Source Table -->
      <section v-if="data.source_breakdown && data.source_breakdown.length > 0" class="table-section">
        <div class="section-card">
          <h3>Channel Performance</h3>
          <div class="table-wrap">
            <table class="data-table">
              <thead><tr><th>Source</th><th class="num">Orders</th><th class="num">GMV</th><th class="num">Confirmed</th><th class="num">Delivered</th><th class="num">Returns</th><th class="num">Conf %</th></tr></thead>
              <tbody>
                <tr v-for="s in data.source_breakdown" :key="s.source">
                  <td class="primary">{{ s.source }}</td>
                  <td class="num">{{ s.orders }}</td>
                  <td class="num">{{ formatCurrency(s.gmv) }}</td>
                  <td class="num green">{{ s.confirmed }}</td>
                  <td class="num teal">{{ s.delivered }}</td>
                  <td class="num red">{{ s.returns }}</td>
                  <td class="num" :class="s.conf_rate >= 60 ? 'green' : s.conf_rate >= 40 ? 'orange' : 'red'">{{ s.conf_rate }}%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- Product Performance -->
      <section class="table-section">
        <div class="section-card">
          <h3>Product Performance (Full Funnel)</h3>
          <div class="table-wrap">
            <table class="data-table">
              <thead><tr><th>Product</th><th class="num">Orders</th><th class="num">Revenue</th><th class="num">Delivered</th><th class="num">Returns</th><th class="num">Success %</th></tr></thead>
              <tbody>
                <tr v-for="p in data.product_performance" :key="p.item_code">
                  <td class="primary">{{ p.item_name || p.item_code }}</td>
                  <td class="num">{{ p.orders }}</td>
                  <td class="num">{{ formatCurrency(p.revenue) }}</td>
                  <td class="num green">{{ p.delivered }}</td>
                  <td class="num red">{{ p.returns }}</td>
                  <td class="num" :class="p.success_rate >= 70 ? 'green' : p.success_rate >= 50 ? 'orange' : 'red'">{{ p.success_rate }}%</td>
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
  name: "MarketingDashboard",
  components: { KPICard, ChartCard },
  props: { company: { type: String, required: true } },
  setup(props) {
    const filters = useFilters();
    const { data, loading, refresh } = useDashboardData(
      "justyol_dashboard.api.marketing.get_marketing_dashboard",
      () => filters.getParams(props.company), {}
    );
    const currencyMap = { "Justyol Morocco": "MAD", "Justyol China": "USD", "Justyol Holding": "USD", "Maslak LTD": "TRY" };
    const currency = computed(() => currencyMap[props.company] || "MAD");
    const kpis = computed(() => data.value?.kpis || {});
    function changePeriod(p) { filters.setPeriod(p); refresh(); }
    function formatCurrency(v) { if (!v && v !== 0) return "--"; return Number(v).toLocaleString("en-US", { maximumFractionDigits: 0 }) + " " + currency.value; }
    function formatNumber(n) { if (!n && n !== 0) return "0"; return Number(n).toLocaleString(); }

    const maxFunnel = computed(() => {
      if (!data.value?.funnel_stages?.length) return 1;
      return Math.max(data.value.funnel_stages[0].count, 1);
    });
    function funnelWidth(count) { return (count / maxFunnel.value) * 100; }
    function dropRate(idx) {
      const stages = data.value?.funnel_stages;
      if (!stages || idx === 0) return 0;
      const prev = stages[idx - 1].count || 1;
      const curr = stages[idx].count || 0;
      return Math.round((1 - curr / prev) * 100);
    }

    const dailyChartOption = computed(() => {
      const t = data.value?.daily_trend || [];
      return {
        tooltip: { trigger: "axis" }, legend: { top: 0 },
        grid: { left: 50, right: 20, top: 30, bottom: 40 },
        xAxis: { type: "category", data: t.map(d => d.date) },
        yAxis: [{ type: "value", name: "Orders" }, { type: "value", name: "GMV" }],
        series: [
          { name: "Orders", type: "bar", data: t.map(d => d.orders), itemStyle: { color: "#6366f1", borderRadius: [4,4,0,0] }, barMaxWidth: 14 },
          { name: "Confirmed", type: "bar", data: t.map(d => d.confirmed), itemStyle: { color: "#22c55e", borderRadius: [4,4,0,0] }, barMaxWidth: 14 },
          { name: "GMV", type: "line", yAxisIndex: 1, data: t.map(d => d.gmv), smooth: true, lineStyle: { color: "#f97316" }, itemStyle: { color: "#f97316" } },
        ],
      };
    });

    const sourceChartOption = computed(() => {
      const s = data.value?.source_breakdown || [];
      const colors = ["#6366f1", "#3b82f6", "#22c55e", "#f97316", "#a855f7", "#06b6d4", "#ec4899"];
      return {
        tooltip: { trigger: "item" },
        legend: { bottom: 0 },
        series: [{ type: "pie", radius: ["35%", "65%"], center: ["50%", "42%"],
          data: s.map((r, i) => ({ name: r.source, value: r.orders, itemStyle: { color: colors[i % colors.length] } })),
          label: { show: true, formatter: "{b}: {c}" },
        }],
      };
    });

    return { filters, data, loading, refresh, currency, kpis, changePeriod, formatCurrency, formatNumber, funnelWidth, dropRate, dailyChartOption, sourceChartOption };
  },
};
</script>

<style scoped>
.marketing-dashboard { max-width: 1400px; margin: 0 auto; }
.period-bar { display: flex; justify-content: space-between; align-items: center; background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 12px 20px; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.period-buttons { display: flex; gap: 8px; flex-wrap: wrap; }
.period-btn { background: var(--bg-primary); border: 1px solid var(--border); color: var(--text-muted); padding: 8px 16px; border-radius: 8px; font-size: 12px; cursor: pointer; transition: all 0.2s; font-family: inherit; }
.period-btn:hover { border-color: var(--accent); color: var(--text-secondary); }
.period-btn.active { background: var(--accent); border-color: var(--accent); color: white; }
.period-info { display: flex; align-items: center; gap: 12px; font-size: 12px; color: var(--text-muted); }
.refresh-btn { background: var(--accent); border: none; color: white; padding: 8px 14px; border-radius: 6px; cursor: pointer; font-size: 12px; font-family: inherit; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }
.funnel-section { margin-bottom: 24px; }
.section-card { background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid var(--border); }
.section-card h3 { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 16px; }
.funnel-container { display: flex; flex-direction: column; gap: 10px; }
.funnel-row { display: grid; grid-template-columns: 120px 1fr 180px 80px; align-items: center; gap: 12px; }
.funnel-label { font-size: 12px; color: var(--text-muted); font-weight: 500; }
.funnel-bar-bg { height: 32px; background: var(--bg-primary); border-radius: 6px; overflow: hidden; }
.funnel-bar { height: 100%; border-radius: 6px; transition: width 0.5s ease; }
.funnel-metrics { display: flex; flex-direction: column; }
.funnel-count { font-size: 16px; font-weight: 700; color: var(--text-primary); }
.funnel-value { font-size: 11px; color: var(--text-dim); }
.funnel-drop { font-size: 11px; font-weight: 600; }
.funnel-drop.red { color: #ef4444; } .funnel-drop.green { color: #22c55e; }
.charts-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 16px; margin-bottom: 24px; }
.table-section { margin-bottom: 24px; }
.table-wrap { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border); color: var(--text-dim); font-size: 11px; font-weight: 600; text-transform: uppercase; }
.data-table td { padding: 10px 12px; border-bottom: 1px solid rgba(51,65,85,0.2); color: var(--text-secondary); }
.data-table th.num, .data-table td.num { text-align: right; }
.data-table td.primary { font-weight: 500; color: var(--text-primary); }
.data-table td.green { color: #22c55e; } .data-table td.red { color: #ef4444; } .data-table td.orange { color: #f97316; } .data-table td.teal { color: #14b8a6; }
.loading-state { display: flex; flex-direction: column; align-items: center; padding: 80px; color: var(--text-muted); gap: 16px; }
.spinner { width: 40px; height: 40px; border: 3px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 768px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } .charts-grid { grid-template-columns: 1fr; } .funnel-row { grid-template-columns: 90px 1fr 120px 60px; } }
</style>
