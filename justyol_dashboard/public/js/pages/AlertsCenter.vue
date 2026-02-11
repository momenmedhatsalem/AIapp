<template>
  <div class="alerts-dashboard">
    <div class="page-header">
      <h2>Alerts Center</h2>
      <button class="refresh-btn" @click="refresh">&#8635; Refresh</button>
    </div>

    <div v-if="loading && !data" class="loading-state"><div class="spinner"></div><p>Scanning for alerts...</p></div>

    <template v-if="data">
      <!-- Summary -->
      <section class="summary-bar">
        <div class="summary-item total">
          <span class="summary-count">{{ data.summary.total }}</span>
          <span class="summary-label">Total Alerts</span>
        </div>
        <div class="summary-item critical">
          <span class="summary-count">{{ data.summary.critical }}</span>
          <span class="summary-label">Critical</span>
        </div>
        <div class="summary-item high">
          <span class="summary-count">{{ data.summary.high }}</span>
          <span class="summary-label">High</span>
        </div>
        <div class="summary-item medium">
          <span class="summary-count">{{ data.summary.medium }}</span>
          <span class="summary-label">Medium</span>
        </div>
      </section>

      <!-- No alerts state -->
      <div v-if="data.alerts.length === 0" class="no-alerts">
        <div class="no-alerts-icon">&#9989;</div>
        <h3>All Clear</h3>
        <p>No active alerts for {{ company }}. Everything is running smoothly.</p>
      </div>

      <!-- Alert Cards -->
      <section class="alerts-list">
        <div
          v-for="(alert, idx) in data.alerts"
          :key="idx"
          class="alert-card"
          :class="alert.type"
        >
          <div class="alert-priority" :class="alert.priority">{{ alert.priority.toUpperCase() }}</div>
          <div class="alert-body">
            <div class="alert-category">{{ alert.category }}</div>
            <h4 class="alert-title">{{ alert.title }}</h4>
            <p class="alert-detail">{{ alert.detail }}</p>
          </div>
          <a v-if="alert.link" :href="alert.link" class="alert-action" :target="alert.link.startsWith('#') ? '' : '_self'">
            View &#8594;
          </a>
        </div>
      </section>
    </template>
  </div>
</template>

<script>
import { useDashboardData } from "../composables/useDashboardData.js";

export default {
  name: "AlertsCenter",
  props: { company: { type: String, required: true } },
  setup(props) {
    const { data, loading, refresh } = useDashboardData(
      "justyol_dashboard.api.alerts.get_alerts_dashboard",
      () => ({ company: props.company }),
      { autoRefresh: true, refreshInterval: 60000 }
    );
    return { data, loading, refresh };
  },
};
</script>

<style scoped>
.alerts-dashboard { max-width: 1000px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-header h2 { font-size: 20px; font-weight: 600; color: var(--text-primary); }
.refresh-btn { background: var(--accent); border: none; color: white; padding: 8px 14px; border-radius: 6px; cursor: pointer; font-size: 12px; font-family: inherit; }

.summary-bar { display: flex; gap: 14px; margin-bottom: 24px; }
.summary-item { flex: 1; text-align: center; background: var(--bg-card); border-radius: 12px; padding: 16px; border: 1px solid var(--border); }
.summary-count { display: block; font-size: 28px; font-weight: 700; }
.summary-label { display: block; font-size: 11px; color: var(--text-dim); text-transform: uppercase; margin-top: 4px; }
.summary-item.total .summary-count { color: var(--text-primary); }
.summary-item.critical .summary-count { color: #ef4444; }
.summary-item.critical { border-color: rgba(239,68,68,0.3); }
.summary-item.high .summary-count { color: #f97316; }
.summary-item.high { border-color: rgba(249,115,22,0.3); }
.summary-item.medium .summary-count { color: #eab308; }

.no-alerts { text-align: center; padding: 80px 40px; background: var(--bg-card); border-radius: 12px; border: 1px solid var(--border); }
.no-alerts-icon { font-size: 48px; margin-bottom: 16px; }
.no-alerts h3 { font-size: 18px; color: var(--text-primary); margin-bottom: 8px; }
.no-alerts p { font-size: 14px; color: var(--text-muted); }

.alerts-list { display: flex; flex-direction: column; gap: 12px; }
.alert-card { display: flex; align-items: flex-start; gap: 16px; background: var(--bg-card); border-radius: 12px; padding: 18px 20px; border: 1px solid var(--border); transition: all 0.2s; }
.alert-card:hover { border-color: var(--border-active); }
.alert-card.danger { border-left: 4px solid #ef4444; }
.alert-card.warning { border-left: 4px solid #f97316; }
.alert-card.info { border-left: 4px solid #3b82f6; }

.alert-priority { padding: 4px 10px; border-radius: 4px; font-size: 10px; font-weight: 700; text-transform: uppercase; white-space: nowrap; }
.alert-priority.critical { background: rgba(239,68,68,0.15); color: #ef4444; }
.alert-priority.high { background: rgba(249,115,22,0.15); color: #f97316; }
.alert-priority.medium { background: rgba(234,179,8,0.15); color: #eab308; }
.alert-priority.low { background: rgba(59,130,246,0.15); color: #3b82f6; }

.alert-body { flex: 1; }
.alert-category { font-size: 10px; font-weight: 600; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
.alert-title { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }
.alert-detail { font-size: 12px; color: var(--text-muted); line-height: 1.5; }

.alert-action { display: flex; align-items: center; padding: 8px 14px; background: var(--bg-primary); border: 1px solid var(--border); border-radius: 6px; color: var(--accent-light); text-decoration: none; font-size: 12px; font-weight: 500; white-space: nowrap; transition: all 0.2s; }
.alert-action:hover { border-color: var(--accent); background: var(--bg-hover); }

.loading-state { display: flex; flex-direction: column; align-items: center; padding: 80px; color: var(--text-muted); gap: 16px; }
.spinner { width: 40px; height: 40px; border: 3px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 768px) { .summary-bar { flex-wrap: wrap; } .summary-item { min-width: calc(50% - 8px); } .alert-card { flex-direction: column; } }
</style>
