<template>
  <div class="operations-dashboard">
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
        <span v-if="data">{{ data.period?.from_date }} &mdash; {{ data.period?.to_date }}</span>
        <button class="refresh-btn" @click="refresh">&#8635; Refresh</button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading && !data" class="loading-state">
      <div class="spinner"></div>
      <p>Loading Operations Data...</p>
    </div>

    <template v-if="data">
      <!-- Pipeline Cards -->
      <section class="pipeline-grid">
        <div
          v-for="step in pipelineSteps"
          :key="step.key"
          class="pipeline-card"
          :class="step.variant"
        >
          <div class="pipeline-icon" v-html="step.icon"></div>
          <div class="pipeline-value">{{ formatNumber(data.pipeline[step.key]) }}</div>
          <div class="pipeline-label">{{ step.label }}</div>
          <div class="pipeline-bar-bg">
            <div
              class="pipeline-bar"
              :style="{ width: pipelinePercent(data.pipeline[step.key]) + '%' }"
            ></div>
          </div>
        </div>
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

      <!-- Charts Row -->
      <section class="charts-grid">
        <ChartCard
          title="Hourly Order Flow"
          :option="hourlyChartOption"
          :height="300"
          :loading="loading"
          :has-data="(data.hourly_activity || []).length > 0"
        />
        <ChartCard
          title="Pipeline Distribution"
          :option="pipelineChartOption"
          :height="300"
          :loading="loading"
          :has-data="hasPipelineData"
        />
      </section>

      <!-- Team Workload -->
      <section class="workload-section">
        <div class="section-card">
          <h3>Team Workload</h3>
          <div class="workload-table-wrap">
            <table class="workload-table">
              <thead>
                <tr>
                  <th>Agent</th>
                  <th class="num">Orders</th>
                  <th class="num">Confirmed</th>
                  <th class="num">Cancelled</th>
                  <th class="num">Rate</th>
                  <th>Performance</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="agent in data.team_workload" :key="agent.agent">
                  <td class="agent-name">{{ agentShortName(agent.agent) }}</td>
                  <td class="num">{{ formatNumber(agent.orders) }}</td>
                  <td class="num green">{{ formatNumber(agent.confirmed) }}</td>
                  <td class="num red">{{ formatNumber(agent.cancelled) }}</td>
                  <td class="num" :class="rateClass(agent.rate)">{{ agent.rate }}%</td>
                  <td>
                    <div class="perf-bar-bg">
                      <div
                        class="perf-bar"
                        :class="rateClass(agent.rate)"
                        :style="{ width: agent.rate + '%' }"
                      ></div>
                    </div>
                  </td>
                </tr>
                <tr v-if="!data.team_workload || data.team_workload.length === 0">
                  <td colspan="6" class="empty-row">No data for this period</td>
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
import ChartCard from "../components/ChartCard.vue";
import { useDashboardData, useFilters } from "../composables/useDashboardData.js";

const COLORS = {
  blue: "#3b82f6",
  green: "#22c55e",
  yellow: "#eab308",
  orange: "#f97316",
  red: "#ef4444",
  purple: "#a855f7",
  cyan: "#06b6d4",
  teal: "#14b8a6",
  indigo: "#6366f1",
};

export default {
  name: "OperationsDashboard",
  components: { ChartCard },
  props: {
    company: { type: String, required: true },
  },

  setup(props) {
    const filters = useFilters();

    const { data, loading, refresh } = useDashboardData(
      "justyol_dashboard.api.operations.get_operations_dashboard",
      () => filters.getParams(props.company),
      { realtimeEvent: "sales_order_update" }
    );

    function changePeriod(period) {
      filters.setPeriod(period);
      refresh();
    }

    const pipelineSteps = [
      { key: "pending_confirmation", label: "Pending Confirm", icon: "&#128172;", variant: "orange" },
      { key: "pending_preparation", label: "Pending Prep", icon: "&#128230;", variant: "yellow" },
      { key: "ready_to_ship", label: "Ready to Ship", icon: "&#9989;", variant: "green" },
      { key: "shipped", label: "Shipped", icon: "&#128666;", variant: "blue" },
      { key: "delivered", label: "Delivered", icon: "&#127919;", variant: "teal" },
      { key: "returns", label: "Returns", icon: "&#128260;", variant: "red" },
    ];

    const totalPipeline = computed(() => {
      if (!data.value?.pipeline) return 1;
      const p = data.value.pipeline;
      return Math.max(Object.values(p).reduce((a, b) => a + (b || 0), 0), 1);
    });

    function pipelinePercent(val) {
      return ((val || 0) / totalPipeline.value) * 100;
    }

    const maxFunnel = computed(() => {
      if (!data.value?.funnel) return 1;
      return Math.max(...data.value.funnel.map((s) => s.count), 1);
    });

    function funnelWidth(count) {
      return (count / maxFunnel.value) * 100;
    }

    function formatNumber(n) {
      if (!n && n !== 0) return "0";
      return Number(n).toLocaleString("en-US", { maximumFractionDigits: 0 });
    }

    function agentShortName(email) {
      if (!email || email === "Unassigned") return "Unassigned";
      // Extract name from email: ahmed@justyol.com -> Ahmed
      const name = email.split("@")[0];
      return name.charAt(0).toUpperCase() + name.slice(1).replace(/[._-]/g, " ");
    }

    function rateClass(rate) {
      if (rate >= 60) return "green";
      if (rate >= 40) return "yellow";
      return "red";
    }

    const hasPipelineData = computed(() => {
      if (!data.value?.pipeline) return false;
      return Object.values(data.value.pipeline).some((v) => v > 0);
    });

    // Hourly activity chart
    const hourlyChartOption = computed(() => {
      const activity = data.value?.hourly_activity || [];
      // Fill in all 24 hours
      const hours = Array.from({ length: 24 }, (_, i) => i);
      const orderMap = {};
      const confirmMap = {};
      activity.forEach((row) => {
        orderMap[row.hour] = row.orders;
        confirmMap[row.hour] = row.confirmed;
      });

      return {
        tooltip: { trigger: "axis" },
        grid: { left: 50, right: 20, top: 30, bottom: 40 },
        xAxis: {
          type: "category",
          data: hours.map((h) => h.toString().padStart(2, "0") + ":00"),
        },
        yAxis: { type: "value" },
        series: [
          {
            name: "Orders",
            type: "bar",
            data: hours.map((h) => orderMap[h] || 0),
            itemStyle: { color: COLORS.indigo, borderRadius: [4, 4, 0, 0] },
            barMaxWidth: 20,
          },
          {
            name: "Confirmed",
            type: "bar",
            data: hours.map((h) => confirmMap[h] || 0),
            itemStyle: { color: COLORS.green, borderRadius: [4, 4, 0, 0] },
            barMaxWidth: 20,
          },
        ],
      };
    });

    // Pipeline distribution pie
    const pipelineChartOption = computed(() => {
      if (!data.value?.pipeline) return {};
      const p = data.value.pipeline;
      const colorMap = {
        pending_confirmation: COLORS.orange,
        pending_preparation: COLORS.yellow,
        ready_to_ship: COLORS.green,
        shipped: COLORS.blue,
        delivered: COLORS.teal,
        returns: COLORS.red,
      };
      const labelMap = {
        pending_confirmation: "Pending Confirm",
        pending_preparation: "Pending Prep",
        ready_to_ship: "Ready to Ship",
        shipped: "Shipped",
        delivered: "Delivered",
        returns: "Returns",
      };
      return {
        tooltip: { trigger: "item" },
        legend: { orient: "vertical", right: 10, top: "center" },
        series: [{
          type: "pie",
          radius: ["40%", "70%"],
          center: ["35%", "50%"],
          data: Object.entries(p).map(([key, val]) => ({
            name: labelMap[key] || key,
            value: val || 0,
            itemStyle: { color: colorMap[key] || COLORS.blue },
          })),
          label: { show: false },
          emphasis: { label: { show: true, fontSize: 14 } },
        }],
      };
    });

    return {
      filters, data, loading, refresh,
      changePeriod, pipelineSteps, pipelinePercent,
      funnelWidth, formatNumber, agentShortName, rateClass,
      hasPipelineData, hourlyChartOption, pipelineChartOption,
      maxFunnel,
    };
  },
};
</script>

<style scoped>
.operations-dashboard {
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
.period-buttons { display: flex; gap: 8px; flex-wrap: wrap; }
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
.period-info { display: flex; align-items: center; gap: 12px; font-size: 12px; color: var(--text-muted); }
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

/* Pipeline Cards */
.pipeline-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 14px;
  margin-bottom: 24px;
}
.pipeline-card {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--border);
  text-align: center;
  transition: all 0.2s;
}
.pipeline-card:hover {
  border-color: var(--border-active);
  transform: translateY(-2px);
}
.pipeline-icon { font-size: 28px; margin-bottom: 8px; }
.pipeline-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}
.pipeline-label {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 6px 0 12px;
}
.pipeline-bar-bg {
  height: 4px;
  background: var(--bg-primary);
  border-radius: 2px;
  overflow: hidden;
}
.pipeline-bar {
  height: 100%;
  border-radius: 2px;
  transition: width 0.5s ease;
}
.pipeline-card.orange .pipeline-bar { background: #f97316; }
.pipeline-card.yellow .pipeline-bar { background: #eab308; }
.pipeline-card.green .pipeline-bar { background: #22c55e; }
.pipeline-card.blue .pipeline-bar { background: #3b82f6; }
.pipeline-card.teal .pipeline-bar { background: #14b8a6; }
.pipeline-card.red .pipeline-bar { background: #ef4444; }

.pipeline-card.orange .pipeline-value { color: #f97316; }
.pipeline-card.yellow .pipeline-value { color: #eab308; }
.pipeline-card.green .pipeline-value { color: #22c55e; }
.pipeline-card.blue .pipeline-value { color: #3b82f6; }
.pipeline-card.teal .pipeline-value { color: #14b8a6; }
.pipeline-card.red .pipeline-value { color: #ef4444; }

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
  grid-template-columns: 110px 1fr 70px;
  align-items: center;
  gap: 14px;
}
.funnel-label { font-size: 12px; color: var(--text-muted); font-weight: 500; }
.funnel-bar-bg { background: var(--bg-primary); border-radius: 4px; height: 28px; overflow: hidden; }
.funnel-bar { height: 100%; border-radius: 4px; transition: width 0.5s ease; }
.funnel-count { font-size: 14px; font-weight: 700; text-align: right; color: var(--text-primary); }

/* Charts */
.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

/* Workload Table */
.workload-section { margin-bottom: 24px; }
.workload-table-wrap { overflow-x: auto; }
.workload-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.workload-table th {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
  color: var(--text-dim);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.workload-table td {
  padding: 10px 12px;
  border-bottom: 1px solid rgba(51, 65, 85, 0.2);
  color: var(--text-secondary);
}
.workload-table th.num, .workload-table td.num { text-align: right; }
.agent-name { font-weight: 500; color: var(--text-primary); }
.workload-table td.green { color: #22c55e; }
.workload-table td.red { color: #ef4444; }
.workload-table td.yellow { color: #eab308; }
.empty-row { text-align: center; color: var(--text-dim); padding: 24px !important; }

.perf-bar-bg {
  height: 6px;
  background: var(--bg-primary);
  border-radius: 3px;
  overflow: hidden;
  min-width: 80px;
}
.perf-bar {
  height: 100%;
  border-radius: 3px;
  transition: width 0.4s ease;
}
.perf-bar.green { background: #22c55e; }
.perf-bar.yellow { background: #eab308; }
.perf-bar.red { background: #ef4444; }

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
  .pipeline-grid { grid-template-columns: repeat(2, 1fr); }
  .charts-grid { grid-template-columns: 1fr; }
  .funnel-row { grid-template-columns: 80px 1fr 50px; }
}
</style>
