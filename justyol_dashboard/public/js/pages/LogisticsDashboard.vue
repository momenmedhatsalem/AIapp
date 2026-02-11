<template>
  <div class="logistics-dashboard">
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
      <p>Loading Logistics Data...</p>
    </div>

    <template v-if="data">
      <!-- KPIs -->
      <section class="kpi-grid">
        <KPICard label="Total Shipments" :value="kpis.total" format="number" icon="&#128666;" icon-color="purple" />
        <KPICard label="Shipped" :value="kpis.shipped" format="number" icon="&#128230;" icon-color="blue" />
        <KPICard label="In Transit" :value="kpis.in_transit" format="number" icon="&#128667;" icon-color="cyan" />
        <KPICard label="Delivered" :value="kpis.delivered" format="number" icon="&#127919;" icon-color="green" />
        <KPICard label="Returns (RTO)" :value="kpis.returns" format="number" icon="&#128260;" icon-color="red" />
        <KPICard label="Delivery Rate" :value="kpis.delivery_rate" format="percent" icon="&#128202;" icon-color="teal" />
      </section>

      <!-- RTO + Value Cards -->
      <section class="metrics-row">
        <div class="metric-card green">
          <span class="metric-label">Delivered Value</span>
          <span class="metric-value">{{ formatShort(kpis.delivered_value) }}</span>
        </div>
        <div class="metric-card red">
          <span class="metric-label">Return Cost (Lost)</span>
          <span class="metric-value">{{ formatShort(kpis.return_value) }}</span>
        </div>
        <div class="metric-card orange">
          <span class="metric-label">RTO Rate</span>
          <span class="metric-value">{{ kpis.rto_rate }}%</span>
        </div>
        <div class="metric-card blue">
          <span class="metric-label">Ready to Ship</span>
          <span class="metric-value">{{ kpis.ready }}</span>
        </div>
        <div class="metric-card yellow">
          <span class="metric-label">Out for Delivery</span>
          <span class="metric-value">{{ kpis.out_for_delivery }}</span>
        </div>
      </section>

      <!-- Charts -->
      <section class="charts-grid">
        <ChartCard
          title="Shipment Trend"
          :option="trendChartOption"
          :height="300"
          :loading="loading"
          :has-data="(data.shipment_trend || []).length > 0"
        />
        <ChartCard
          title="Tracking Status"
          :option="trackingChartOption"
          :height="300"
          :loading="loading"
          :has-data="(data.tracking_distribution || []).length > 0"
        />
      </section>

      <!-- Top Cities -->
      <section class="cities-section">
        <div class="section-card">
          <h3>Top Cities by Orders</h3>
          <div class="table-wrap">
            <table class="city-table">
              <thead>
                <tr>
                  <th>City / Address</th>
                  <th class="num">Orders</th>
                  <th class="num">Delivered</th>
                  <th class="num">Returns</th>
                  <th class="num">Delivery %</th>
                  <th>Performance</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="city in data.top_cities" :key="city.city">
                  <td class="city-name">{{ city.city }}</td>
                  <td class="num">{{ city.orders }}</td>
                  <td class="num green">{{ city.delivered }}</td>
                  <td class="num red">{{ city.returns }}</td>
                  <td class="num" :class="deliveryRateClass(city.delivery_rate)">{{ city.delivery_rate }}%</td>
                  <td>
                    <div class="perf-bar-bg">
                      <div class="perf-bar" :class="deliveryRateClass(city.delivery_rate)" :style="{ width: city.delivery_rate + '%' }"></div>
                    </div>
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
import { useDashboardData, useFilters } from "../composables/useDashboardData.js";

const COLORS = {
  blue: "#3b82f6", green: "#22c55e", red: "#ef4444",
  orange: "#f97316", cyan: "#06b6d4", teal: "#14b8a6",
  indigo: "#6366f1", yellow: "#eab308",
};

export default {
  name: "LogisticsDashboard",
  components: { KPICard, ChartCard },
  props: { company: { type: String, required: true } },

  setup(props) {
    const filters = useFilters();

    const { data, loading, refresh } = useDashboardData(
      "justyol_dashboard.api.logistics.get_logistics_dashboard",
      () => filters.getParams(props.company),
      { realtimeEvent: "sales_order_update" }
    );

    const kpis = computed(() => data.value?.kpis || {});

    function changePeriod(period) {
      filters.setPeriod(period);
      refresh();
    }

    function formatShort(n) {
      if (!n && n !== 0) return "--";
      if (n >= 1000000) return (n / 1000000).toFixed(1) + "M";
      if (n >= 1000) return (n / 1000).toFixed(1) + "K";
      return Number(n).toLocaleString();
    }

    function deliveryRateClass(rate) {
      if (rate >= 70) return "green";
      if (rate >= 50) return "yellow";
      return "red";
    }

    const trendChartOption = computed(() => {
      const trend = data.value?.shipment_trend || [];
      return {
        tooltip: { trigger: "axis" },
        legend: { top: 0 },
        grid: { left: 50, right: 20, top: 30, bottom: 40 },
        xAxis: { type: "category", data: trend.map((d) => d.date) },
        yAxis: { type: "value" },
        series: [
          { name: "Shipped", type: "line", data: trend.map((d) => d.shipped), smooth: true, lineStyle: { color: COLORS.blue }, itemStyle: { color: COLORS.blue } },
          { name: "Delivered", type: "line", data: trend.map((d) => d.delivered), smooth: true, lineStyle: { color: COLORS.green }, itemStyle: { color: COLORS.green } },
          { name: "Returns", type: "line", data: trend.map((d) => d.returns), smooth: true, lineStyle: { color: COLORS.red }, itemStyle: { color: COLORS.red } },
        ],
      };
    });

    const trackingChartOption = computed(() => {
      const dist = data.value?.tracking_distribution || [];
      const colorMap = {
        "Delivered": COLORS.green, "In Transit": COLORS.blue, "Return": COLORS.red,
        "Out for Delivery": COLORS.orange, "Pending": COLORS.yellow,
      };
      return {
        tooltip: { trigger: "item" },
        legend: { orient: "vertical", right: 10, top: "center" },
        series: [{
          type: "pie",
          radius: ["40%", "70%"],
          center: ["35%", "50%"],
          data: dist.map((d) => ({
            name: d.status, value: d.count,
            itemStyle: { color: colorMap[d.status] || COLORS.indigo },
          })),
          label: { show: false },
          emphasis: { label: { show: true, fontSize: 14 } },
        }],
      };
    });

    return {
      filters, data, loading, refresh, kpis,
      changePeriod, formatShort, deliveryRateClass,
      trendChartOption, trackingChartOption,
    };
  },
};
</script>

<style scoped>
.logistics-dashboard { max-width: 1400px; margin: 0 auto; }

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
  padding: 8px 14px; border-radius: 6px; cursor: pointer; font-size: 12px; font-family: inherit;
}

.kpi-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 16px; margin-bottom: 20px;
}

.metrics-row {
  display: flex; gap: 14px; margin-bottom: 24px; overflow-x: auto;
  padding-bottom: 4px;
}
.metric-card {
  flex: 1; min-width: 140px;
  background: var(--bg-card); border-radius: 12px; padding: 16px;
  border: 1px solid var(--border); text-align: center;
}
.metric-label { display: block; font-size: 11px; color: var(--text-dim); text-transform: uppercase; margin-bottom: 8px; }
.metric-value { font-size: 22px; font-weight: 700; }
.metric-card.green .metric-value { color: #22c55e; }
.metric-card.red .metric-value { color: #ef4444; }
.metric-card.orange .metric-value { color: #f97316; }
.metric-card.blue .metric-value { color: #3b82f6; }
.metric-card.yellow .metric-value { color: #eab308; }

.charts-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 16px; margin-bottom: 24px;
}

.cities-section { margin-bottom: 24px; }
.section-card {
  background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid var(--border);
}
.section-card h3 { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 16px; }
.table-wrap { overflow-x: auto; }
.city-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.city-table th {
  text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border);
  color: var(--text-dim); font-size: 11px; font-weight: 600; text-transform: uppercase;
}
.city-table td { padding: 10px 12px; border-bottom: 1px solid rgba(51, 65, 85, 0.2); color: var(--text-secondary); }
.city-table th.num, .city-table td.num { text-align: right; }
.city-name { font-weight: 500; color: var(--text-primary); }
.city-table td.green { color: #22c55e; }
.city-table td.red { color: #ef4444; }
.city-table td.yellow { color: #eab308; }

.perf-bar-bg { height: 6px; background: var(--bg-primary); border-radius: 3px; overflow: hidden; min-width: 80px; }
.perf-bar { height: 100%; border-radius: 3px; transition: width 0.4s ease; }
.perf-bar.green { background: #22c55e; }
.perf-bar.yellow { background: #eab308; }
.perf-bar.red { background: #ef4444; }

.loading-state { display: flex; flex-direction: column; align-items: center; padding: 80px; color: var(--text-muted); gap: 16px; }
.spinner { width: 40px; height: 40px; border: 3px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 768px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .metrics-row { flex-direction: column; }
  .charts-grid { grid-template-columns: 1fr; }
}
</style>
