<template>
  <div class="executive-dashboard">
    <!-- Period Selector -->
    <div class="period-bar">
      <div class="period-buttons">
        <button
          v-for="p in filters.periods"
          :key="p.value"
          class="period-btn"
          :class="{ active: filters.period.value === p.value }"
          @click="changePeriod(p.value)"
        >
          {{ p.label }}
        </button>
      </div>
      <div class="period-info">
        <span v-if="data">{{ data.period?.from_date }} to {{ data.period?.to_date }}</span>
        <button class="refresh-btn" @click="refresh">&#8635; Refresh</button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading && !data" class="loading-state">
      <div class="spinner"></div>
      <p>Loading Executive Dashboard...</p>
    </div>

    <template v-if="data">
      <!-- Primary KPIs -->
      <section class="kpi-grid">
        <KPICard
          label="Gross Merchandise Value"
          :value="kpis.gmv"
          format="currency"
          :currency="currency"
          icon-color="blue"
          icon="&#128176;"
          :trend="computeTrend('gmv')"
          :sub-value="formatShort(prevKpis.gmv)"
          sub-label="vs Previous"
        />
        <KPICard
          label="Total Orders"
          :value="kpis.total_orders"
          format="number"
          icon-color="purple"
          icon="&#128230;"
          :trend="computeTrend('total_orders')"
          :sub-value="String(prevKpis.total_orders || 0)"
          sub-label="vs Previous"
        />
        <KPICard
          label="Confirmed Orders"
          :value="kpis.confirmed"
          format="number"
          icon-color="green"
          icon="&#9989;"
          :trend="computeTrend('confirmed')"
          :sub-value="kpis.confirmation_rate + '%'"
          sub-label="Rate"
          sub-class="green"
        />
        <KPICard
          label="Delivered Orders"
          :value="kpis.delivered"
          format="number"
          icon-color="cyan"
          icon="&#127919;"
          :trend="computeTrend('delivered')"
          :sub-value="kpis.delivery_rate + '%'"
          sub-label="Delivery Rate"
          sub-class="blue"
        />
        <KPICard
          label="Average Order Value"
          :value="kpis.aov"
          format="currency"
          :currency="currency"
          icon-color="orange"
          icon="&#128722;"
          :trend="computeTrend('aov')"
          :sub-value="formatShort(prevKpis.aov)"
          sub-label="vs Previous"
        />
        <KPICard
          label="Cancelled Orders"
          :value="kpis.cancelled"
          format="number"
          icon-color="red"
          icon="&#10060;"
          :trend="computeTrend('cancelled')"
          :trend-inverse="true"
          :sub-value="kpis.cancellation_rate + '%'"
          sub-label="Cancel Rate"
          sub-class="red"
        />
      </section>

      <!-- Revenue Trend Chart -->
      <section class="charts-section">
        <ChartCard
          title="Revenue Trend"
          :option="revenueChartOption"
          :height="320"
          :full-width="true"
          :loading="loading"
          :has-data="(data?.revenue_trend || []).length > 0"
        />
      </section>

      <!-- Status + Logistics Charts -->
      <section class="charts-grid">
        <ChartCard
          title="Order Status Distribution"
          :option="statusChartOption"
          :height="280"
          :loading="loading"
          :has-data="(data?.status_distribution || []).length > 0"
        />
        <ChartCard
          title="Logistics Pipeline"
          :option="logisticsChartOption"
          :height="280"
          :loading="loading"
          :has-data="(data?.logistics_pipeline || []).length > 0"
        />
      </section>

      <!-- Operations Funnel -->
      <section class="funnel-section">
        <div class="section-card">
          <h3>Operations Funnel</h3>
          <div class="funnel-container">
            <div v-for="stage in data.funnel" :key="stage.stage" class="funnel-row">
              <span class="funnel-label">{{ stage.stage }}</span>
              <div class="funnel-bar-bg">
                <div
                  class="funnel-bar"
                  :style="{ width: funnelWidth(stage.count) + '%', background: stage.color }"
                ></div>
              </div>
              <span class="funnel-count">{{ formatNumber(stage.count) }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Top Performers -->
      <section class="tables-grid">
        <DataTable
          title="Top Products"
          badge="By Revenue"
          badge-color="green"
          :columns="productColumns"
          :rows="data.top_products || []"
          :loading="loading"
          :currency="currency"
        />
        <DataTable
          title="Top Suppliers"
          badge="By Revenue"
          badge-color="purple"
          :columns="supplierColumns"
          :rows="data.top_suppliers || []"
          :loading="loading"
          :currency="currency"
        />
      </section>
    </template>
  </div>
</template>

<script>
import { ref, computed, watch } from "vue";
import KPICard from "../components/KPICard.vue";
import ChartCard from "../components/ChartCard.vue";
import DataTable from "../components/DataTable.vue";
import { useDashboardData, useFilters } from "../composables/useDashboardData.js";

const COLORS = {
  primary: "#6366f1",
  blue: "#3b82f6",
  cyan: "#06b6d4",
  green: "#22c55e",
  yellow: "#eab308",
  orange: "#f97316",
  red: "#ef4444",
  purple: "#a855f7",
  teal: "#14b8a6",
  pink: "#ec4899",
};

const CHART_COLORS = [COLORS.blue, COLORS.green, COLORS.purple, COLORS.orange, COLORS.cyan, COLORS.pink, COLORS.teal, COLORS.yellow, COLORS.red];

export default {
  name: "ExecutiveDashboard",
  components: { KPICard, ChartCard, DataTable },
  props: {
    company: { type: String, required: true },
  },

  setup(props) {
    const filters = useFilters();

    const apiParams = computed(() => filters.getParams(props.company));

    const { data, loading, lastUpdated, refresh } = useDashboardData(
      "justyol_dashboard.api.executive.get_executive_dashboard",
      () => apiParams.value,
      { realtimeEvent: "sales_order_update" }
    );

    const currency = computed(() => {
      const map = { "Justyol Morocco": "MAD", "Justyol China": "USD", "Justyol Holding": "USD", "Maslak LTD": "TRY" };
      return map[props.company] || "MAD";
    });

    const kpis = computed(() => data.value?.kpis || {});
    const prevKpis = computed(() => data.value?.previous_kpis || {});

    function changePeriod(period) {
      filters.setPeriod(period);
      refresh();
    }

    function computeTrend(key) {
      const curr = kpis.value[key];
      const prev = prevKpis.value[key];
      if (!curr || !prev) return null;
      return ((curr - prev) / prev) * 100;
    }

    function formatNumber(n) {
      if (!n && n !== 0) return "--";
      return Number(n).toLocaleString("en-US", { maximumFractionDigits: 0 });
    }

    function formatShort(n) {
      if (!n && n !== 0) return "--";
      if (n >= 1000000) return (n / 1000000).toFixed(1) + "M";
      if (n >= 1000) return (n / 1000).toFixed(1) + "K";
      return formatNumber(n);
    }

    // Max funnel value for bar scaling
    const maxFunnel = computed(() => {
      if (!data.value?.funnel) return 1;
      return Math.max(...data.value.funnel.map((s) => s.count), 1);
    });
    function funnelWidth(count) {
      return (count / maxFunnel.value) * 100;
    }

    // Revenue Chart Option (eCharts)
    const revenueChartOption = computed(() => {
      const trend = data.value?.revenue_trend || [];
      return {
        tooltip: { trigger: "axis" },
        grid: { left: 60, right: 40, top: 40, bottom: 40 },
        xAxis: { type: "category", data: trend.map((d) => d.date) },
        yAxis: [
          { type: "value", name: "GMV", position: "left" },
          { type: "value", name: "Orders", position: "right" },
        ],
        series: [
          {
            name: "GMV",
            type: "line",
            data: trend.map((d) => d.gmv),
            smooth: true,
            yAxisIndex: 0,
            lineStyle: { color: COLORS.primary },
            itemStyle: { color: COLORS.primary },
            areaStyle: { color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: "rgba(99,102,241,0.3)" }, { offset: 1, color: "rgba(99,102,241,0)" }] } },
          },
          {
            name: "Orders",
            type: "bar",
            data: trend.map((d) => d.orders),
            yAxisIndex: 1,
            itemStyle: { color: COLORS.cyan, borderRadius: [4, 4, 0, 0] },
            barMaxWidth: 30,
          },
        ],
      };
    });

    // Status Distribution (Donut)
    const statusChartOption = computed(() => {
      const dist = data.value?.status_distribution || [];
      return {
        tooltip: { trigger: "item" },
        legend: { orient: "vertical", right: 10, top: "center" },
        series: [{
          type: "pie",
          radius: ["45%", "70%"],
          center: ["35%", "50%"],
          data: dist.map((d, i) => ({ name: d.status, value: d.count, itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] } })),
          label: { show: false },
          emphasis: { label: { show: true, fontSize: 14 } },
        }],
      };
    });

    // Logistics Pipeline (Bar)
    const logisticsChartOption = computed(() => {
      const pipe = data.value?.logistics_pipeline || [];
      return {
        tooltip: { trigger: "axis" },
        grid: { left: 60, right: 20, top: 20, bottom: 40 },
        xAxis: { type: "category", data: pipe.map((d) => d.status) },
        yAxis: { type: "value" },
        series: [{
          type: "bar",
          data: pipe.map((d, i) => ({ value: d.count, itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length], borderRadius: [6, 6, 0, 0] } })),
          barMaxWidth: 40,
        }],
      };
    });

    const productColumns = [
      { key: "item_name", label: "Product" },
      { key: "qty", label: "Qty", format: "number", align: "right" },
      { key: "revenue", label: "Revenue", format: "currency", align: "right" },
    ];

    const supplierColumns = [
      { key: "supplier", label: "Supplier" },
      { key: "qty", label: "Items", format: "number", align: "right" },
      { key: "revenue", label: "Revenue", format: "currency", align: "right" },
      { key: "orders", label: "Orders", format: "number", align: "right" },
    ];

    return {
      filters, data, loading, lastUpdated, refresh,
      currency, kpis, prevKpis,
      changePeriod, computeTrend, formatNumber, formatShort,
      funnelWidth, revenueChartOption, statusChartOption, logisticsChartOption,
      productColumns, supplierColumns,
    };
  },
};
</script>

<style scoped>
.executive-dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

/* Period Bar */
.period-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px 20px;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}
.period-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.period-btn {
  background: var(--bg-primary);
  border: 1px solid var(--border);
  color: var(--text-muted);
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
}
.period-btn:hover { border-color: var(--accent); color: var(--text-secondary); }
.period-btn.active { background: var(--accent); border-color: var(--accent); color: white; }

.period-info {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: var(--text-muted);
}
.refresh-btn {
  background: var(--accent);
  border: none;
  color: white;
  padding: 8px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  font-family: inherit;
}
.refresh-btn:hover { background: #4f46e5; }

/* KPI Grid */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

/* Charts */
.charts-section { margin-bottom: 20px; }
.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

/* Funnel */
.funnel-section { margin-bottom: 24px; }
.section-card {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--border);
}
.section-card h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
}
.funnel-container { display: flex; flex-direction: column; gap: 10px; }
.funnel-row {
  display: grid;
  grid-template-columns: 100px 1fr 70px;
  align-items: center;
  gap: 14px;
}
.funnel-label { font-size: 12px; color: var(--text-muted); font-weight: 500; }
.funnel-bar-bg { background: var(--bg-primary); border-radius: 4px; height: 28px; overflow: hidden; }
.funnel-bar { height: 100%; border-radius: 4px; transition: width 0.5s ease; }
.funnel-count { font-size: 14px; font-weight: 700; text-align: right; color: var(--text-primary); }

/* Tables */
.tables-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

/* Loading */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px;
  color: var(--text-muted);
  gap: 16px;
}
.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 768px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .charts-grid, .tables-grid { grid-template-columns: 1fr; }
  .funnel-row { grid-template-columns: 70px 1fr 50px; }
  .period-buttons { width: 100%; }
}
</style>
