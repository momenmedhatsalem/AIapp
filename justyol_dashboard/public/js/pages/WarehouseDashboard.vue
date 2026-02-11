<template>
  <div class="warehouse-dashboard">
    <div class="period-bar">
      <div class="period-buttons">
        <button v-for="p in filters.periods" :key="p.value" class="period-btn" :class="{ active: filters.period.value === p.value }" @click="changePeriod(p.value)">{{ p.label }}</button>
      </div>
      <div class="period-info">
        <span v-if="data">{{ data.period?.from_date }} &mdash; {{ data.period?.to_date }}</span>
        <button class="refresh-btn" @click="refresh">&#8635; Refresh</button>
      </div>
    </div>

    <div v-if="loading && !data" class="loading-state"><div class="spinner"></div><p>Loading Warehouse Data...</p></div>

    <template v-if="data">
      <!-- KPIs -->
      <section class="kpi-grid">
        <KPICard label="Pending Preparation" :value="kpis.pending_preparation" format="number" icon="&#9203;" icon-color="orange" />
        <KPICard label="Ready to Ship" :value="kpis.ready_to_ship" format="number" icon="&#9989;" icon-color="green" />
        <KPICard label="Shipped" :value="kpis.shipped" format="number" icon="&#128666;" icon-color="blue" />
        <KPICard label="Preparation Rate" :value="kpis.preparation_rate" format="percent" icon="&#128202;" icon-color="teal" />
        <KPICard label="Delivery Notes" :value="kpis.delivery_notes" format="number" icon="&#128196;" icon-color="purple" />
        <KPICard label="DN Value" :value="kpis.dn_value" format="currency" :currency="currency" icon="&#128176;" icon-color="cyan" />
      </section>

      <!-- Preparation Pipeline -->
      <section class="pipeline-section">
        <div class="section-card">
          <h3>Preparation Pipeline</h3>
          <div class="pipeline-visual">
            <div class="pipe-stage orange">
              <span class="pipe-count">{{ kpis.pending_preparation }}</span>
              <span class="pipe-label">Pending</span>
            </div>
            <div class="pipe-arrow">&#8594;</div>
            <div class="pipe-stage green">
              <span class="pipe-count">{{ kpis.ready_to_ship }}</span>
              <span class="pipe-label">Ready</span>
            </div>
            <div class="pipe-arrow">&#8594;</div>
            <div class="pipe-stage blue">
              <span class="pipe-count">{{ kpis.shipped }}</span>
              <span class="pipe-label">Shipped</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Charts -->
      <section class="charts-grid">
        <ChartCard title="Hourly Preparation Activity" :option="hourlyChartOption" :height="300" :loading="loading" :has-data="(data.hourly_prep || []).length > 0" />
        <ChartCard title="Stock Movements" :option="movementsChartOption" :height="300" :loading="loading" :has-data="(data.stock_movements || []).length > 0" />
      </section>

      <!-- Team Performance -->
      <section class="table-section">
        <div class="section-card">
          <h3>Team Performance</h3>
          <div class="table-wrap">
            <table class="data-table">
              <thead><tr><th>Agent</th><th class="num">Prepared</th><th class="num">Shipped</th><th>Progress</th></tr></thead>
              <tbody>
                <tr v-for="a in data.team_performance" :key="a.agent">
                  <td class="primary">{{ agentName(a.agent) }}</td>
                  <td class="num green">{{ a.prepared }}</td>
                  <td class="num blue">{{ a.shipped }}</td>
                  <td>
                    <div class="perf-bar-bg"><div class="perf-bar" :style="{ width: Math.min(100, (a.prepared / maxTeam) * 100) + '%' }"></div></div>
                  </td>
                </tr>
                <tr v-if="!data.team_performance?.length"><td colspan="4" class="empty">No data</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- Warehouse Stock -->
      <section class="table-section">
        <div class="section-card">
          <h3>Warehouse Stock Overview</h3>
          <div class="table-wrap">
            <table class="data-table">
              <thead><tr><th>Warehouse</th><th class="num">SKUs</th><th class="num">Total Qty</th><th class="num">Value</th><th class="num">Out of Stock</th><th class="num">Low Stock</th></tr></thead>
              <tbody>
                <tr v-for="w in data.warehouse_stock" :key="w.warehouse">
                  <td class="primary">{{ w.warehouse }}</td>
                  <td class="num">{{ w.sku_count }}</td>
                  <td class="num">{{ formatNumber(w.total_qty) }}</td>
                  <td class="num green">{{ formatCurrency(w.total_value) }}</td>
                  <td class="num" :class="w.out_of_stock > 0 ? 'red' : ''">{{ w.out_of_stock }}</td>
                  <td class="num" :class="w.low_stock > 0 ? 'orange' : ''">{{ w.low_stock }}</td>
                </tr>
                <tr v-if="!data.warehouse_stock?.length"><td colspan="6" class="empty">No warehouses</td></tr>
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
  name: "WarehouseDashboard",
  components: { KPICard, ChartCard },
  props: { company: { type: String, required: true } },
  setup(props) {
    const filters = useFilters();
    const { data, loading, refresh } = useDashboardData(
      "justyol_dashboard.api.warehouse.get_warehouse_dashboard",
      () => filters.getParams(props.company),
      { realtimeEvent: "sales_order_update" }
    );
    const currencyMap = { "Justyol Morocco": "MAD", "Justyol China": "USD", "Justyol Holding": "USD", "Maslak LTD": "TRY" };
    const currency = computed(() => currencyMap[props.company] || "MAD");
    const kpis = computed(() => data.value?.kpis || {});
    function changePeriod(p) { filters.setPeriod(p); refresh(); }
    function formatCurrency(v) { if (!v && v !== 0) return "--"; return Number(v).toLocaleString("en-US", { maximumFractionDigits: 0 }) + " " + currency.value; }
    function formatNumber(n) { if (!n && n !== 0) return "0"; return Number(n).toLocaleString(); }
    function agentName(email) { if (!email || email === "Unassigned") return "Unassigned"; return email.split("@")[0].replace(/[._-]/g, " ").replace(/\b\w/g, c => c.toUpperCase()); }

    const maxTeam = computed(() => {
      if (!data.value?.team_performance?.length) return 1;
      return Math.max(...data.value.team_performance.map(a => a.prepared), 1);
    });

    const hourlyChartOption = computed(() => {
      const h = data.value?.hourly_prep || [];
      const hours = Array.from({ length: 24 }, (_, i) => i);
      const maps = { orders: {}, prepared: {}, shipped: {} };
      h.forEach(r => { maps.orders[r.hour] = r.orders; maps.prepared[r.hour] = r.prepared; maps.shipped[r.hour] = r.shipped; });
      return {
        tooltip: { trigger: "axis" }, legend: { top: 0 },
        grid: { left: 50, right: 20, top: 30, bottom: 40 },
        xAxis: { type: "category", data: hours.map(h => h.toString().padStart(2, "0") + ":00") },
        yAxis: { type: "value" },
        series: [
          { name: "Confirmed", type: "bar", data: hours.map(h => maps.orders[h] || 0), itemStyle: { color: "#6366f1", borderRadius: [4,4,0,0] }, barMaxWidth: 14 },
          { name: "Prepared", type: "bar", data: hours.map(h => maps.prepared[h] || 0), itemStyle: { color: "#22c55e", borderRadius: [4,4,0,0] }, barMaxWidth: 14 },
          { name: "Shipped", type: "bar", data: hours.map(h => maps.shipped[h] || 0), itemStyle: { color: "#3b82f6", borderRadius: [4,4,0,0] }, barMaxWidth: 14 },
        ],
      };
    });

    const movementsChartOption = computed(() => {
      const m = data.value?.stock_movements || [];
      const colors = ["#6366f1", "#3b82f6", "#22c55e", "#f97316", "#a855f7", "#06b6d4"];
      return {
        tooltip: { trigger: "item" },
        legend: { bottom: 0 },
        series: [{ type: "pie", radius: ["40%", "70%"], center: ["50%", "42%"],
          data: m.map((r, i) => ({ name: r.type, value: r.count, itemStyle: { color: colors[i % colors.length] } })),
          label: { show: true, formatter: "{b}: {c}" },
        }],
      };
    });

    return { filters, data, loading, refresh, currency, kpis, changePeriod, formatCurrency, formatNumber, agentName, maxTeam, hourlyChartOption, movementsChartOption };
  },
};
</script>

<style scoped>
.warehouse-dashboard { max-width: 1400px; margin: 0 auto; }
.period-bar { display: flex; justify-content: space-between; align-items: center; background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 12px 20px; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.period-buttons { display: flex; gap: 8px; flex-wrap: wrap; }
.period-btn { background: var(--bg-primary); border: 1px solid var(--border); color: var(--text-muted); padding: 8px 16px; border-radius: 8px; font-size: 12px; cursor: pointer; transition: all 0.2s; font-family: inherit; }
.period-btn:hover { border-color: var(--accent); color: var(--text-secondary); }
.period-btn.active { background: var(--accent); border-color: var(--accent); color: white; }
.period-info { display: flex; align-items: center; gap: 12px; font-size: 12px; color: var(--text-muted); }
.refresh-btn { background: var(--accent); border: none; color: white; padding: 8px 14px; border-radius: 6px; cursor: pointer; font-size: 12px; font-family: inherit; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 16px; margin-bottom: 24px; }
.pipeline-section { margin-bottom: 24px; }
.section-card { background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid var(--border); }
.section-card h3 { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 16px; }
.pipeline-visual { display: flex; align-items: center; justify-content: center; gap: 20px; padding: 20px 0; }
.pipe-stage { text-align: center; padding: 20px 30px; border-radius: 12px; background: var(--bg-primary); border: 2px solid var(--border); min-width: 120px; }
.pipe-stage.orange { border-color: rgba(249,115,22,0.4); }
.pipe-stage.green { border-color: rgba(34,197,94,0.4); }
.pipe-stage.blue { border-color: rgba(59,130,246,0.4); }
.pipe-count { display: block; font-size: 32px; font-weight: 700; }
.pipe-stage.orange .pipe-count { color: #f97316; }
.pipe-stage.green .pipe-count { color: #22c55e; }
.pipe-stage.blue .pipe-count { color: #3b82f6; }
.pipe-label { display: block; font-size: 12px; color: var(--text-dim); text-transform: uppercase; margin-top: 4px; }
.pipe-arrow { font-size: 28px; color: var(--text-dim); }
.charts-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 16px; margin-bottom: 24px; }
.table-section { margin-bottom: 24px; }
.table-wrap { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border); color: var(--text-dim); font-size: 11px; font-weight: 600; text-transform: uppercase; }
.data-table td { padding: 10px 12px; border-bottom: 1px solid rgba(51,65,85,0.2); color: var(--text-secondary); }
.data-table th.num, .data-table td.num { text-align: right; }
.data-table td.primary { font-weight: 500; color: var(--text-primary); }
.data-table td.green { color: #22c55e; } .data-table td.blue { color: #3b82f6; } .data-table td.red { color: #ef4444; } .data-table td.orange { color: #f97316; }
.data-table td.empty { text-align: center; color: var(--text-dim); padding: 24px; }
.perf-bar-bg { height: 6px; background: var(--bg-primary); border-radius: 3px; overflow: hidden; min-width: 100px; }
.perf-bar { height: 100%; background: #22c55e; border-radius: 3px; transition: width 0.4s ease; }
.loading-state { display: flex; flex-direction: column; align-items: center; padding: 80px; color: var(--text-muted); gap: 16px; }
.spinner { width: 40px; height: 40px; border: 3px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 768px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } .charts-grid { grid-template-columns: 1fr; } .pipeline-visual { flex-direction: column; } .pipe-arrow { transform: rotate(90deg); } }
</style>
