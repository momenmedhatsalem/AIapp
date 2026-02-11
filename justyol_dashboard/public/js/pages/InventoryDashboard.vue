<template>
  <div class="inventory-dashboard">
    <div class="page-header">
      <h2>Inventory Intelligence</h2>
      <button class="refresh-btn" @click="refresh">&#8635; Refresh</button>
    </div>

    <div v-if="loading && !data" class="loading-state">
      <div class="spinner"></div>
      <p>Loading Inventory Data...</p>
    </div>

    <template v-if="data">
      <!-- KPIs -->
      <section class="kpi-grid">
        <KPICard label="Total SKUs" :value="kpis.total_items" format="number" icon="&#128230;" icon-color="purple" />
        <KPICard label="Total Stock Qty" :value="kpis.total_stock" format="number" icon="&#128202;" icon-color="blue" />
        <KPICard label="Stock Value" :value="kpis.total_value" format="currency" :currency="currency" icon="&#128176;" icon-color="green" />
        <KPICard label="Out of Stock" :value="kpis.out_of_stock" format="number" icon="&#128308;" icon-color="red" />
        <KPICard label="Low Stock (≤5)" :value="kpis.low_stock" format="number" icon="&#9888;" icon-color="orange" />
      </section>

      <!-- Stock Health Bar -->
      <section class="health-section">
        <div class="section-card">
          <h3>Stock Health</h3>
          <div class="health-bar-container">
            <div class="health-bar">
              <div class="health-segment green" :style="{ width: healthPct.healthy + '%' }" :title="'Healthy: ' + healthPct.healthy + '%'"></div>
              <div class="health-segment orange" :style="{ width: healthPct.low + '%' }" :title="'Low: ' + healthPct.low + '%'"></div>
              <div class="health-segment red" :style="{ width: healthPct.out + '%' }" :title="'Out: ' + healthPct.out + '%'"></div>
            </div>
            <div class="health-legend">
              <span class="legend-item"><span class="dot green"></span> Healthy ({{ healthPct.healthy }}%)</span>
              <span class="legend-item"><span class="dot orange"></span> Low Stock ({{ healthPct.low }}%)</span>
              <span class="legend-item"><span class="dot red"></span> Out of Stock ({{ healthPct.out }}%)</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Charts -->
      <section class="charts-grid">
        <ChartCard
          title="Warehouse Distribution"
          :option="warehouseChartOption"
          :height="300"
          :loading="loading"
          :has-data="(data.warehouse_distribution || []).length > 0"
        />
        <ChartCard
          title="Top Items by Value"
          :option="topItemsChartOption"
          :height="300"
          :loading="loading"
          :has-data="(data.top_items || []).length > 0"
        />
      </section>

      <!-- Restock Alerts -->
      <section v-if="data.restock_alerts && data.restock_alerts.length > 0" class="alerts-section">
        <div class="section-card">
          <h3>&#9888; Restock Alerts</h3>
          <div class="table-wrap">
            <table class="alert-table">
              <thead>
                <tr>
                  <th>Item Code</th>
                  <th>Item Name</th>
                  <th class="num">Qty Left</th>
                  <th>Warehouse</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in data.restock_alerts" :key="item.item_code + item.warehouse">
                  <td class="item-code">{{ item.item_code }}</td>
                  <td>{{ item.item_name }}</td>
                  <td class="num" :class="item.qty <= 0 ? 'red' : 'orange'">{{ item.qty }}</td>
                  <td>{{ item.warehouse }}</td>
                  <td><span class="status-badge" :class="item.qty <= 0 ? 'out' : 'low'">{{ item.qty <= 0 ? 'OUT' : 'LOW' }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- Recent POs -->
      <section v-if="data.recent_purchase_orders && data.recent_purchase_orders.length > 0" class="po-section">
        <div class="section-card">
          <h3>Recent Purchase Orders</h3>
          <div class="table-wrap">
            <table class="po-table">
              <thead>
                <tr>
                  <th>PO</th>
                  <th>Supplier</th>
                  <th class="num">Amount</th>
                  <th>Status</th>
                  <th>Date</th>
                  <th class="num">Received %</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="po in data.recent_purchase_orders" :key="po.name">
                  <td><a :href="'/app/purchase-order/' + po.name" class="po-link">{{ po.name }}</a></td>
                  <td>{{ po.supplier }}</td>
                  <td class="num">{{ formatCurrency(po.grand_total) }}</td>
                  <td><span class="status-badge" :class="poStatusClass(po.status)">{{ po.status }}</span></td>
                  <td>{{ po.date }}</td>
                  <td class="num">
                    <div class="recv-bar-bg">
                      <div class="recv-bar" :style="{ width: po.received_pct + '%' }"></div>
                    </div>
                    <span class="recv-pct">{{ po.received_pct.toFixed(0) }}%</span>
                  </td>
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
import { useDashboardData } from "../composables/useDashboardData.js";

const COLORS = ["#6366f1", "#3b82f6", "#22c55e", "#14b8a6", "#06b6d4", "#f97316", "#eab308", "#a855f7", "#ec4899"];

export default {
  name: "InventoryDashboard",
  components: { KPICard, ChartCard },
  props: { company: { type: String, required: true } },

  setup(props) {
    const { data, loading, refresh } = useDashboardData(
      "justyol_dashboard.api.inventory.get_inventory_dashboard",
      () => ({ company: props.company }),
      { autoRefresh: true, refreshInterval: 180000 }
    );

    const currencyMap = { "Justyol Morocco": "MAD", "Justyol China": "USD", "Justyol Holding": "USD", "Maslak LTD": "TRY" };
    const currency = computed(() => currencyMap[props.company] || "MAD");
    const kpis = computed(() => data.value?.kpis || {});

    const healthPct = computed(() => {
      const total = kpis.value.total_items || 1;
      const out = kpis.value.out_of_stock || 0;
      const low = kpis.value.low_stock || 0;
      const healthy = total - out - low;
      return {
        healthy: Math.round((healthy / total) * 100),
        low: Math.round((low / total) * 100),
        out: Math.round((out / total) * 100),
      };
    });

    function formatCurrency(val) {
      if (!val && val !== 0) return "--";
      return Number(val).toLocaleString("en-US", { maximumFractionDigits: 0 }) + " " + currency.value;
    }

    function poStatusClass(status) {
      const map = { Completed: "green", "To Receive and Bill": "blue", "To Bill": "orange", "To Receive": "yellow", Draft: "gray" };
      return map[status] || "gray";
    }

    const warehouseChartOption = computed(() => {
      const wh = data.value?.warehouse_distribution || [];
      return {
        tooltip: { trigger: "item" },
        legend: { orient: "vertical", right: 10, top: "center" },
        series: [{
          type: "pie",
          radius: ["40%", "70%"],
          center: ["35%", "50%"],
          data: wh.map((w, i) => ({
            name: w.warehouse.split(" - ")[0],
            value: w.total_value,
            itemStyle: { color: COLORS[i % COLORS.length] },
          })),
          label: { show: false },
          emphasis: { label: { show: true, fontSize: 13 } },
        }],
      };
    });

    const topItemsChartOption = computed(() => {
      const items = (data.value?.top_items || []).slice(0, 10);
      return {
        tooltip: { trigger: "axis" },
        grid: { left: 120, right: 40, top: 20, bottom: 20 },
        xAxis: { type: "value" },
        yAxis: { type: "category", data: items.map((i) => i.item_name || i.item_code).reverse() },
        series: [{
          type: "bar",
          data: items.map((i) => i.value).reverse(),
          itemStyle: { color: "#6366f1", borderRadius: [0, 4, 4, 0] },
          barMaxWidth: 20,
        }],
      };
    });

    return {
      data, loading, refresh, currency, kpis,
      healthPct, formatCurrency, poStatusClass,
      warehouseChartOption, topItemsChartOption,
    };
  },
};
</script>

<style scoped>
.inventory-dashboard { max-width: 1400px; margin: 0 auto; }

.page-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 20px;
}
.page-header h2 { font-size: 20px; font-weight: 600; color: var(--text-primary); }
.refresh-btn {
  background: var(--accent); border: none; color: white;
  padding: 8px 14px; border-radius: 6px; cursor: pointer; font-size: 12px; font-family: inherit;
}

.kpi-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 16px; margin-bottom: 24px;
}

.health-section { margin-bottom: 24px; }
.section-card {
  background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid var(--border);
}
.section-card h3 { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 16px; }
.health-bar { display: flex; height: 20px; border-radius: 10px; overflow: hidden; background: var(--bg-primary); }
.health-segment { transition: width 0.5s ease; }
.health-segment.green { background: #22c55e; }
.health-segment.orange { background: #f97316; }
.health-segment.red { background: #ef4444; }
.health-legend { display: flex; gap: 20px; margin-top: 12px; font-size: 12px; color: var(--text-muted); }
.legend-item { display: flex; align-items: center; gap: 6px; }
.dot { width: 10px; height: 10px; border-radius: 50%; }
.dot.green { background: #22c55e; }
.dot.orange { background: #f97316; }
.dot.red { background: #ef4444; }

.charts-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 16px; margin-bottom: 24px;
}

.alerts-section, .po-section { margin-bottom: 24px; }
.table-wrap { overflow-x: auto; }

.alert-table, .po-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.alert-table th, .po-table th {
  text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border);
  color: var(--text-dim); font-size: 11px; font-weight: 600; text-transform: uppercase;
}
.alert-table td, .po-table td {
  padding: 10px 12px; border-bottom: 1px solid rgba(51, 65, 85, 0.2); color: var(--text-secondary);
}
.alert-table th.num, .alert-table td.num,
.po-table th.num, .po-table td.num { text-align: right; }
.item-code { font-weight: 500; color: var(--text-primary); font-family: monospace; font-size: 12px; }
.alert-table td.red { color: #ef4444; font-weight: 700; }
.alert-table td.orange { color: #f97316; font-weight: 700; }

.status-badge {
  display: inline-block; padding: 3px 10px; border-radius: 6px;
  font-size: 11px; font-weight: 600; text-transform: uppercase;
}
.status-badge.out { background: rgba(239, 68, 68, 0.15); color: #ef4444; }
.status-badge.low { background: rgba(249, 115, 22, 0.15); color: #f97316; }
.status-badge.green { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
.status-badge.blue { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }
.status-badge.orange { background: rgba(249, 115, 22, 0.15); color: #f97316; }
.status-badge.yellow { background: rgba(234, 179, 8, 0.15); color: #eab308; }
.status-badge.gray { background: rgba(100, 116, 139, 0.15); color: #64748b; }

.po-link { color: var(--accent); text-decoration: none; font-weight: 500; }
.po-link:hover { text-decoration: underline; }

.recv-bar-bg { height: 6px; background: var(--bg-primary); border-radius: 3px; overflow: hidden; display: inline-block; width: 60px; vertical-align: middle; margin-right: 8px; }
.recv-bar { height: 100%; background: #22c55e; border-radius: 3px; }
.recv-pct { font-size: 12px; color: var(--text-muted); }

.loading-state { display: flex; flex-direction: column; align-items: center; padding: 80px; color: var(--text-muted); gap: 16px; }
.spinner { width: 40px; height: 40px; border: 3px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 768px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .charts-grid { grid-template-columns: 1fr; }
}
</style>
