<template>
  <div class="confirmation-dashboard">
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
      <p>Loading Confirmation Data...</p>
    </div>

    <template v-if="data">
      <!-- KPIs -->
      <section class="kpi-grid">
        <KPICard label="Total Orders" :value="kpis.total_orders" format="number" icon="&#128230;" icon-color="purple" />
        <KPICard label="Confirmed" :value="kpis.confirmed" format="number" icon="&#9989;" icon-color="green" />
        <KPICard label="Cancelled" :value="kpis.cancelled" format="number" icon="&#10060;" icon-color="red" />
        <KPICard label="Pending" :value="kpis.pending" format="number" icon="&#9203;" icon-color="yellow" />
        <KPICard label="Confirmation Rate" :value="kpis.confirmation_rate" format="percent" icon="&#128202;" icon-color="blue" />
        <KPICard label="No Response" :value="kpis.no_response" format="number" icon="&#128263;" icon-color="orange" />
      </section>

      <!-- Rate Bars -->
      <section class="rate-section">
        <div class="section-card">
          <h3>Confirmation vs Cancellation</h3>
          <div class="rate-bars">
            <div class="rate-row">
              <span class="rate-label">Confirmed</span>
              <div class="rate-bar-bg">
                <div class="rate-bar green" :style="{ width: kpis.confirmation_rate + '%' }"></div>
              </div>
              <span class="rate-value green">{{ kpis.confirmation_rate }}%</span>
            </div>
            <div class="rate-row">
              <span class="rate-label">Cancelled</span>
              <div class="rate-bar-bg">
                <div class="rate-bar red" :style="{ width: kpis.cancellation_rate + '%' }"></div>
              </div>
              <span class="rate-value red">{{ kpis.cancellation_rate }}%</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Charts -->
      <section class="charts-grid">
        <ChartCard
          title="Hourly Confirmation Activity"
          :option="hourlyChartOption"
          :height="300"
          :loading="loading"
          :has-data="(data.hourly_activity || []).length > 0"
        />
        <ChartCard
          title="Cancellation Reasons"
          :option="reasonsChartOption"
          :height="300"
          :loading="loading"
          :has-data="(data.cancellation_reasons || []).length > 0"
        />
      </section>

      <!-- Agent Performance Table -->
      <section class="agents-section">
        <div class="section-card">
          <h3>Agent Performance</h3>
          <div class="table-wrap">
            <table class="agent-table">
              <thead>
                <tr>
                  <th>Agent</th>
                  <th class="num">Total</th>
                  <th class="num">Confirmed</th>
                  <th class="num">Cancelled</th>
                  <th class="num">Pending</th>
                  <th class="num">No Resp</th>
                  <th class="num">Rate</th>
                  <th>Performance</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="agent in data.agents" :key="agent.agent">
                  <td class="agent-name">{{ agentName(agent.agent) }}</td>
                  <td class="num">{{ agent.total_orders }}</td>
                  <td class="num green">{{ agent.confirmed }}</td>
                  <td class="num red">{{ agent.cancelled }}</td>
                  <td class="num yellow">{{ agent.pending }}</td>
                  <td class="num">{{ agent.no_response }}</td>
                  <td class="num" :class="rateClass(agent.confirmation_rate)">{{ agent.confirmation_rate }}%</td>
                  <td>
                    <div class="perf-bar-bg">
                      <div class="perf-bar" :class="rateClass(agent.confirmation_rate)" :style="{ width: agent.confirmation_rate + '%' }"></div>
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

const COLORS = { blue: "#3b82f6", green: "#22c55e", red: "#ef4444", orange: "#f97316", indigo: "#6366f1" };

export default {
  name: "ConfirmationDashboard",
  components: { KPICard, ChartCard },
  props: { company: { type: String, required: true } },

  setup(props) {
    const filters = useFilters();

    const { data, loading, refresh } = useDashboardData(
      "justyol_dashboard.api.confirmation.get_confirmation_dashboard",
      () => filters.getParams(props.company),
      { realtimeEvent: "sales_order_update" }
    );

    const kpis = computed(() => data.value?.kpis || {});

    function changePeriod(period) {
      filters.setPeriod(period);
      refresh();
    }

    function agentName(email) {
      if (!email || email === "Unassigned") return "Unassigned";
      return email.split("@")[0].replace(/[._-]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
    }

    function rateClass(rate) {
      if (rate >= 60) return "green";
      if (rate >= 40) return "yellow";
      return "red";
    }

    const hourlyChartOption = computed(() => {
      const activity = data.value?.hourly_activity || [];
      const hours = Array.from({ length: 24 }, (_, i) => i);
      const maps = { orders: {}, confirmed: {}, cancelled: {} };
      activity.forEach((r) => {
        maps.orders[r.hour] = r.orders;
        maps.confirmed[r.hour] = r.confirmed;
        maps.cancelled[r.hour] = r.cancelled;
      });
      return {
        tooltip: { trigger: "axis" },
        legend: { top: 0 },
        grid: { left: 50, right: 20, top: 30, bottom: 40 },
        xAxis: { type: "category", data: hours.map((h) => h.toString().padStart(2, "0") + ":00") },
        yAxis: { type: "value" },
        series: [
          { name: "Orders", type: "bar", data: hours.map((h) => maps.orders[h] || 0), itemStyle: { color: COLORS.indigo, borderRadius: [4, 4, 0, 0] }, barMaxWidth: 16 },
          { name: "Confirmed", type: "bar", data: hours.map((h) => maps.confirmed[h] || 0), itemStyle: { color: COLORS.green, borderRadius: [4, 4, 0, 0] }, barMaxWidth: 16 },
          { name: "Cancelled", type: "bar", data: hours.map((h) => maps.cancelled[h] || 0), itemStyle: { color: COLORS.red, borderRadius: [4, 4, 0, 0] }, barMaxWidth: 16 },
        ],
      };
    });

    const reasonsChartOption = computed(() => {
      const reasons = data.value?.cancellation_reasons || [];
      return {
        tooltip: { trigger: "axis" },
        grid: { left: 150, right: 40, top: 20, bottom: 20 },
        xAxis: { type: "value" },
        yAxis: { type: "category", data: reasons.map((r) => r.reason).reverse() },
        series: [{
          type: "bar",
          data: reasons.map((r) => r.count).reverse(),
          itemStyle: { color: COLORS.red, borderRadius: [0, 4, 4, 0] },
          barMaxWidth: 24,
        }],
      };
    });

    return {
      filters, data, loading, refresh,
      kpis, changePeriod, agentName, rateClass,
      hourlyChartOption, reasonsChartOption,
    };
  },
};
</script>

<style scoped>
.confirmation-dashboard { max-width: 1400px; margin: 0 auto; }

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

.rate-section { margin-bottom: 24px; }
.section-card {
  background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid var(--border);
}
.section-card h3 { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 16px; }
.rate-bars { display: flex; flex-direction: column; gap: 14px; }
.rate-row { display: grid; grid-template-columns: 100px 1fr 70px; align-items: center; gap: 14px; }
.rate-label { font-size: 13px; color: var(--text-muted); font-weight: 500; }
.rate-bar-bg { height: 24px; background: var(--bg-primary); border-radius: 6px; overflow: hidden; }
.rate-bar { height: 100%; border-radius: 6px; transition: width 0.5s ease; }
.rate-bar.green { background: #22c55e; }
.rate-bar.red { background: #ef4444; }
.rate-value { font-size: 16px; font-weight: 700; text-align: right; }
.rate-value.green { color: #22c55e; }
.rate-value.red { color: #ef4444; }

.charts-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 16px; margin-bottom: 24px;
}

.agents-section { margin-bottom: 24px; }
.table-wrap { overflow-x: auto; }
.agent-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.agent-table th {
  text-align: left; padding: 10px 12px;
  border-bottom: 1px solid var(--border); color: var(--text-dim);
  font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;
}
.agent-table td {
  padding: 10px 12px; border-bottom: 1px solid rgba(51, 65, 85, 0.2); color: var(--text-secondary);
}
.agent-table th.num, .agent-table td.num { text-align: right; }
.agent-name { font-weight: 500; color: var(--text-primary); }
.agent-table td.green { color: #22c55e; }
.agent-table td.red { color: #ef4444; }
.agent-table td.yellow { color: #eab308; }

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
  .charts-grid { grid-template-columns: 1fr; }
}
</style>
