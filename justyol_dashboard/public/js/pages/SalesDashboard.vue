<template>
  <div class="sales-dashboard">
    <!-- Date Filter Bar -->
    <div class="filter-bar">
      <div class="filter-left">
        <div class="date-inputs">
          <div class="date-group">
            <label>From</label>
            <input type="date" v-model="fromDate" class="date-input" />
          </div>
          <div class="date-group">
            <label>To</label>
            <input type="date" v-model="toDate" class="date-input" />
          </div>
          <button class="apply-btn" @click="applyCustomDates">Apply</button>
        </div>
        <div class="preset-buttons">
          <button
            v-for="p in filters.periods"
            :key="p.value"
            class="preset-btn"
            :class="{ active: !customMode && filters.period.value === p.value }"
            @click="applyPreset(p.value)"
          >
            {{ p.label }}
          </button>
        </div>
      </div>
      <div class="filter-right">
        <span class="filter-label">{{ filterLabel }}</span>
        <button class="refresh-btn" @click="refresh">&#8635;</button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading && !data" class="loading-state">
      <div class="spinner"></div>
      <p>Loading Sales Dashboard...</p>
    </div>

    <template v-if="data">
      <!-- KPI Cards -->
      <section class="kpi-grid-7">
        <KPICard label="GMV" :value="kpis.gmv" format="currency" :currency="currency" icon-color="blue" icon="&#128176;" />
        <KPICard label="Total Orders" :value="kpis.total_orders" format="number" icon-color="purple" icon="&#128230;" />
        <KPICard label="Confirmed" :value="kpis.confirmed" format="number" icon-color="green" icon="&#9989;" />
        <KPICard label="Shipped" :value="kpis.shipped" format="number" icon-color="cyan" icon="&#128666;" />
        <KPICard label="Delivered" :value="kpis.delivered" format="number" icon-color="teal" icon="&#127919;" />
        <KPICard label="Cancelled" :value="kpis.cancelled" format="number" icon-color="orange" icon="&#10060;" />
        <KPICard label="Returns" :value="kpis.returns" format="number" icon-color="red" icon="&#128260;" />
      </section>

      <!-- Rate Bars -->
      <section class="rate-grid">
        <div class="rate-card">
          <div class="rate-info">
            <span class="rate-label">Confirmation Rate</span>
            <span class="rate-value green">{{ kpis.confirmation_rate }}%</span>
          </div>
          <div class="rate-bar-bg"><div class="rate-bar green" :style="{ width: kpis.confirmation_rate + '%' }"></div></div>
        </div>
        <div class="rate-card">
          <div class="rate-info">
            <span class="rate-label">Cancellation Rate</span>
            <span class="rate-value red">{{ kpis.cancellation_rate }}%</span>
          </div>
          <div class="rate-bar-bg"><div class="rate-bar red" :style="{ width: kpis.cancellation_rate + '%' }"></div></div>
        </div>
        <div class="rate-card">
          <div class="rate-info">
            <span class="rate-label">Delivery Rate</span>
            <span class="rate-value blue">{{ kpis.delivery_rate }}%</span>
          </div>
          <div class="rate-bar-bg"><div class="rate-bar blue" :style="{ width: kpis.delivery_rate + '%' }"></div></div>
        </div>
      </section>

      <!-- Customer Insights -->
      <section class="insights-section" v-if="data.customer_insights">
        <div class="section-card">
          <h3>Customer Insights</h3>
          <div class="insights-grid">
            <div class="insight-item">
              <span class="insight-value">{{ formatNumber(data.customer_insights.unique_customers) }}</span>
              <span class="insight-label">Unique Customers</span>
            </div>
            <div class="insight-item">
              <span class="insight-value green">{{ formatNumber(data.customer_insights.new_customers) }}</span>
              <span class="insight-label">New Customers</span>
            </div>
            <div class="insight-item">
              <span class="insight-value purple">{{ formatNumber(data.customer_insights.repeat_customers) }}</span>
              <span class="insight-label">Repeat Customers</span>
            </div>
            <div class="insight-item">
              <span class="insight-value cyan">{{ data.customer_insights.avg_order_frequency }}</span>
              <span class="insight-label">Avg Orders/Customer</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Summary -->
      <section class="summary-section">
        <div class="section-card">
          <h3>Performance Summary</h3>
          <div class="summary-grid">
            <div class="summary-item">
              <span class="summary-label">Total GMV</span>
              <span class="summary-value">{{ formatCurrency(kpis.gmv) }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">Total Orders</span>
              <span class="summary-value">{{ formatNumber(kpis.total_orders) }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">Avg Order Value</span>
              <span class="summary-value">{{ formatCurrency(kpis.aov) }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">Total Shipped</span>
              <span class="summary-value">{{ formatNumber(kpis.shipped) }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Charts -->
      <section class="charts-section">
        <ChartCard title="Daily GMV Trend" :option="gmvChartOption" :height="320" :full-width="true" :has-data="(data.revenue_trend || []).length > 0" />
      </section>

      <section class="charts-grid">
        <ChartCard title="Sales Status" :option="statusChartOption" :height="280" :has-data="(data.status_distribution || []).length > 0" />
        <ChartCard title="Cancellation Reasons" :option="cancelChartOption" :height="280" :has-data="(data.cancellation_reasons || []).length > 0" />
      </section>

      <!-- Products & Suppliers Tables -->
      <section class="tables-grid">
        <DataTable title="Winner Products" badge="Delivered" badge-color="green" :columns="productColumns" :rows="data.top_products || []" :currency="currency" />
        <DataTable title="Top Suppliers" badge="By Revenue" badge-color="purple" :columns="supplierColumns" :rows="data.top_suppliers || []" :currency="currency" />
      </section>
    </template>
  </div>
</template>

<script>
import { ref, computed } from "vue";
import KPICard from "../components/KPICard.vue";
import ChartCard from "../components/ChartCard.vue";
import DataTable from "../components/DataTable.vue";
import { useDashboardData, useFilters } from "../composables/useDashboardData.js";

const COLORS = ["#3b82f6", "#22c55e", "#a855f7", "#f97316", "#06b6d4", "#ec4899", "#14b8a6", "#eab308", "#ef4444"];

export default {
  name: "SalesDashboard",
  components: { KPICard, ChartCard, DataTable },
  props: { company: { type: String, required: true } },

  setup(props) {
    const filters = useFilters();
    const fromDate = ref("");
    const toDate = ref("");
    const customMode = ref(false);

    const apiParams = computed(() => {
      if (customMode.value && fromDate.value && toDate.value) {
        return { company: props.company, from_date: fromDate.value, to_date: toDate.value };
      }
      return { company: props.company, period: filters.period.value };
    });

    const { data, loading, refresh } = useDashboardData(
      "justyol_dashboard.api.sales.get_sales_dashboard",
      () => apiParams.value,
      { realtimeEvent: "sales_order_update" }
    );

    const currency = computed(() => {
      const map = { "Justyol Morocco": "MAD", "Justyol China": "USD", "Justyol Holding": "USD", "Maslak LTD": "TRY" };
      return map[props.company] || "MAD";
    });

    const kpis = computed(() => data.value?.kpis || {});

    const filterLabel = computed(() => {
      if (customMode.value) return `${fromDate.value} - ${toDate.value}`;
      return filters.periods.find(p => p.value === filters.period.value)?.label || "Today";
    });

    function applyPreset(period) {
      customMode.value = false;
      filters.setPeriod(period);
      refresh();
    }

    function applyCustomDates() {
      if (fromDate.value && toDate.value) {
        customMode.value = true;
        refresh();
      }
    }

    function formatNumber(n) {
      if (!n && n !== 0) return "--";
      return Number(n).toLocaleString("en-US", { maximumFractionDigits: 0 });
    }
    function formatCurrency(n) {
      if (!n && n !== 0) return "--";
      return formatNumber(n) + " " + currency.value;
    }

    const gmvChartOption = computed(() => {
      const trend = data.value?.revenue_trend || [];
      return {
        tooltip: { trigger: "axis" },
        grid: { left: 60, right: 20, top: 20, bottom: 40 },
        xAxis: { type: "category", data: trend.map(d => d.date) },
        yAxis: { type: "value" },
        series: [{
          type: "line", data: trend.map(d => d.gmv), smooth: true,
          lineStyle: { color: "#6366f1" }, itemStyle: { color: "#6366f1" },
          areaStyle: { color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: "rgba(99,102,241,0.3)" }, { offset: 1, color: "rgba(99,102,241,0)" }] } },
        }],
      };
    });

    const statusChartOption = computed(() => {
      const dist = data.value?.status_distribution || [];
      return {
        tooltip: { trigger: "item" },
        legend: { orient: "vertical", right: 10, top: "center" },
        series: [{ type: "pie", radius: ["45%", "70%"], center: ["35%", "50%"], data: dist.map((d, i) => ({ name: d.status, value: d.count, itemStyle: { color: COLORS[i % COLORS.length] } })), label: { show: false } }],
      };
    });

    const cancelChartOption = computed(() => {
      const reasons = data.value?.cancellation_reasons || [];
      return {
        tooltip: { trigger: "axis" },
        grid: { left: 120, right: 20, top: 10, bottom: 20 },
        xAxis: { type: "value" },
        yAxis: { type: "category", data: reasons.map(d => d.reason?.substring(0, 18) || "Unknown") },
        series: [{ type: "bar", data: reasons.map(d => d.count), itemStyle: { color: "#ef4444", borderRadius: [0, 4, 4, 0] }, barMaxWidth: 20 }],
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
    ];

    return {
      filters, data, loading, refresh, currency, kpis, filterLabel,
      fromDate, toDate, customMode, applyPreset, applyCustomDates,
      formatNumber, formatCurrency,
      gmvChartOption, statusChartOption, cancelChartOption,
      productColumns, supplierColumns,
    };
  },
};
</script>

<style scoped>
.sales-dashboard { max-width: 1400px; margin: 0 auto; }

.filter-bar {
  display: flex; justify-content: space-between; align-items: center;
  background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px;
  padding: 12px 20px; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;
}
.filter-left { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.date-inputs { display: flex; align-items: flex-end; gap: 8px; }
.date-group { display: flex; flex-direction: column; gap: 2px; }
.date-group label { font-size: 9px; color: var(--text-dim); text-transform: uppercase; }
.date-input {
  background: var(--bg-primary); border: 1px solid var(--border); border-radius: 6px;
  padding: 8px 12px; color: var(--text-secondary); font-size: 12px; outline: none;
}
.date-input:focus { border-color: var(--accent); }
.apply-btn {
  background: var(--green); border: none; color: white; padding: 8px 16px;
  border-radius: 6px; cursor: pointer; font-size: 12px; font-family: inherit;
}
.preset-buttons { display: flex; gap: 6px; flex-wrap: wrap; }
.preset-btn {
  background: var(--bg-primary); border: 1px solid var(--border); color: var(--text-muted);
  padding: 6px 12px; border-radius: 6px; font-size: 11px; cursor: pointer; font-family: inherit;
}
.preset-btn:hover { border-color: var(--accent); }
.preset-btn.active { background: var(--accent); border-color: var(--accent); color: white; }
.filter-right { display: flex; align-items: center; gap: 12px; }
.filter-label { font-size: 12px; color: var(--text-muted); }
.refresh-btn {
  background: var(--accent); border: none; color: white; width: 36px; height: 36px;
  border-radius: 8px; cursor: pointer; font-size: 16px;
}

.kpi-grid-7 {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 12px; margin-bottom: 18px;
}

.rate-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 12px; margin-bottom: 20px;
}
.rate-card {
  background: var(--bg-card); border-radius: 10px; padding: 16px; border: 1px solid var(--border);
}
.rate-info { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.rate-label { font-size: 13px; color: var(--text-muted); }
.rate-value { font-size: 20px; font-weight: 700; }
.rate-value.green { color: var(--green); }
.rate-value.red { color: var(--red); }
.rate-value.blue { color: var(--blue); }
.rate-bar-bg { background: var(--bg-primary); border-radius: 4px; height: 6px; overflow: hidden; }
.rate-bar { height: 100%; border-radius: 4px; transition: width 0.5s; }
.rate-bar.green { background: linear-gradient(90deg, #22c55e, #16a34a); }
.rate-bar.red { background: linear-gradient(90deg, #ef4444, #dc2626); }
.rate-bar.blue { background: linear-gradient(90deg, #3b82f6, #2563eb); }

.insights-section, .summary-section { margin-bottom: 20px; }
.section-card {
  background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid var(--border);
}
.section-card h3 { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 16px; }
.insights-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px;
}
.insight-item {
  background: var(--bg-primary); border-radius: 10px; padding: 16px; text-align: center;
}
.insight-value { display: block; font-size: 24px; font-weight: 700; color: var(--text-primary); }
.insight-value.green { color: var(--green); }
.insight-value.purple { color: var(--purple); }
.insight-value.cyan { color: var(--cyan); }
.insight-label { font-size: 11px; color: var(--text-dim); margin-top: 4px; display: block; }
.summary-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px;
}
.summary-item { background: var(--bg-primary); border-radius: 8px; padding: 14px; text-align: center; }
.summary-label { display: block; font-size: 10px; color: var(--text-dim); text-transform: uppercase; margin-bottom: 6px; }
.summary-value { font-size: 16px; font-weight: 700; color: var(--accent); }

.charts-section { margin-bottom: 20px; }
.charts-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 16px; margin-bottom: 20px;
}
.tables-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 16px; margin-bottom: 24px;
}

.loading-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 80px; color: var(--text-muted); gap: 16px;
}
.spinner {
  width: 40px; height: 40px; border: 3px solid var(--border);
  border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 768px) {
  .kpi-grid-7 { grid-template-columns: repeat(2, 1fr); }
  .charts-grid, .tables-grid { grid-template-columns: 1fr; }
  .preset-buttons { display: none; }
  .insights-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
