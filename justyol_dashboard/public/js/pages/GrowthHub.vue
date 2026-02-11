<template>
  <div class="growth-hub">
    <!-- Quick Stats Bar -->
    <section class="quick-stats">
      <KPICard
        v-for="stat in quickStats"
        :key="stat.label"
        :value="stat.value"
        :label="stat.label"
        :icon="stat.icon"
        :icon-color="stat.color"
        :format="stat.format"
        :currency="currency"
        class="quick-stat"
      />
    </section>

    <!-- Dashboard Cards Grid -->
    <section class="dashboard-grid">
      <router-link
        v-for="card in dashboardCards"
        :key="card.path"
        :to="card.path"
        class="dashboard-card"
        :class="card.variant"
      >
        <div class="card-icon-wrap" :class="card.variant">
          <span class="card-icon" v-html="card.icon"></span>
        </div>
        <div class="card-content">
          <h3>{{ card.title }}</h3>
          <p>{{ card.description }}</p>
        </div>
        <div class="card-metrics">
          <div v-for="m in card.metrics" :key="m.label" class="card-metric">
            <span class="card-metric-value">{{ m.value }}</span>
            <span class="card-metric-label">{{ m.label }}</span>
          </div>
        </div>
        <div class="card-arrow">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </div>
      </router-link>
    </section>

    <!-- Quick Links -->
    <section class="quick-links">
      <h2>Quick Access</h2>
      <div class="links-grid">
        <a
          v-for="link in quickLinks"
          :key="link.href"
          :href="link.href"
          class="quick-link"
          :target="link.external ? '_blank' : ''"
        >
          <span v-html="link.icon"></span>
          {{ link.label }}
        </a>
      </div>
    </section>

    <!-- Last Updated -->
    <div class="hub-footer">
      <span v-if="lastUpdated">
        Last updated: {{ lastUpdated.toLocaleTimeString() }}
      </span>
      <button class="refresh-btn" @click="refresh">&#8635; Refresh</button>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from "vue";
import KPICard from "../components/KPICard.vue";
import { useDashboardData } from "../composables/useDashboardData.js";

export default {
  name: "GrowthHub",
  components: { KPICard },
  props: {
    company: { type: String, required: true },
  },

  setup(props) {
    const { data, loading, lastUpdated, refresh } = useDashboardData(
      "justyol_dashboard.api.executive.get_executive_dashboard",
      () => ({ company: props.company, period: "today" }),
      { autoRefresh: true, refreshInterval: 120000, realtimeEvent: "sales_order_update" }
    );

    const currency = computed(() => {
      const map = {
        "Justyol Morocco": "MAD",
        "Justyol China": "USD",
        "Justyol Holding": "USD",
        "Maslak LTD": "TRY",
      };
      return map[props.company] || "MAD";
    });

    const kpis = computed(() => data.value?.kpis || {});

    const quickStats = computed(() => [
      { label: "Today Revenue", value: kpis.value.gmv, icon: "&#128176;", color: "blue", format: "currency" },
      { label: "Total Orders", value: kpis.value.total_orders, icon: "&#128230;", color: "purple", format: "number" },
      { label: "Confirmed", value: kpis.value.confirmed, icon: "&#9989;", color: "green", format: "number" },
      { label: "Shipped", value: kpis.value.shipped, icon: "&#128666;", color: "cyan", format: "number" },
      { label: "Delivered", value: kpis.value.delivered, icon: "&#127919;", color: "teal", format: "number" },
    ]);

    function fmt(n) {
      if (!n && n !== 0) return "--";
      if (n >= 1000000) return (n / 1000000).toFixed(1) + "M";
      if (n >= 1000) return (n / 1000).toFixed(1) + "K";
      return n.toLocaleString();
    }

    const dashboardCards = computed(() => [
      {
        path: "/executive",
        title: "Executive Dashboard",
        description: "High-level KPIs, trends, and strategic overview",
        icon: "&#128202;",
        variant: "executive",
        metrics: [
          { label: "GMV MTD", value: fmt(data.value?.kpis?.gmv) },
          { label: "Confirm Rate", value: (data.value?.kpis?.confirmation_rate || 0).toFixed(1) + "%" },
        ],
      },
      {
        path: "/sales",
        title: "Sales Intelligence",
        description: "Sales analytics, customer insights, and performance",
        icon: "&#128176;",
        variant: "sales",
        metrics: [
          { label: "Orders", value: fmt(data.value?.kpis?.total_orders) },
          { label: "AOV", value: fmt(data.value?.kpis?.aov) },
        ],
      },
      {
        path: "/finance",
        title: "Finance Control",
        description: "P&L, cash flow, AR/AP, and financial health",
        icon: "&#128200;",
        variant: "finance",
        metrics: [
          { label: "Revenue", value: fmt(data.value?.kpis?.gmv) },
          { label: "Cancelled", value: fmt(data.value?.kpis?.cancelled) },
        ],
      },
      {
        path: "/rto",
        title: "RTO & Returns",
        description: "Return analytics, cost impact, zone & product RTO",
        icon: "&#128260;",
        variant: "rto",
        metrics: [
          { label: "Returns", value: fmt(data.value?.kpis?.returns) },
          { label: "Return Rate", value: (data.value?.kpis?.return_rate || 0).toFixed(1) + "%" },
        ],
      },
      {
        path: "/cashflow",
        title: "COD Cash Flow",
        description: "COD collection, remittance tracking, aging analysis",
        icon: "&#128178;",
        variant: "cashflow",
        metrics: [
          { label: "Delivered", value: fmt(data.value?.kpis?.delivered) },
          { label: "GMV", value: fmt(data.value?.kpis?.gmv) },
        ],
      },
      {
        path: "/inventory",
        title: "Inventory Intelligence",
        description: "Stock health, restock alerts, and procurement",
        icon: "&#128230;",
        variant: "inventory",
        metrics: [
          { label: "Shipped", value: fmt(data.value?.kpis?.shipped) },
          { label: "Returns", value: fmt(data.value?.kpis?.returns) },
        ],
      },
      {
        path: "/operations",
        title: "Operations Center",
        description: "Pipeline, team workload, and real-time activity",
        icon: "&#9881;",
        variant: "operations",
        metrics: [
          { label: "Pending", value: fmt(data.value?.kpis?.pending) },
          { label: "Ready", value: fmt(data.value?.kpis?.ready_to_ship) },
        ],
      },
    ]);

    const quickLinks = [
      { label: "Preparation", icon: "&#9989;", href: "/preparation-dashboard" },
      { label: "Confirmation", icon: "&#128172;", href: "/confirmation-dashboard" },
      { label: "Shipping", icon: "&#128666;", href: "/shipping-status-dashboard" },
      { label: "Sales Analytics", icon: "&#128200;", href: "/app/query-report/Sales%20Analytics", external: true },
      { label: "Stock Balance", icon: "&#128230;", href: "/app/query-report/Stock%20Balance", external: true },
      { label: "P&L Statement", icon: "&#128176;", href: "/app/query-report/Profit%20and%20Loss%20Statement", external: true },
    ];

    return {
      data, loading, lastUpdated, refresh,
      currency, quickStats, dashboardCards, quickLinks,
    };
  },
};
</script>

<style scoped>
.growth-hub {
  max-width: 1400px;
  margin: 0 auto;
}

/* Quick Stats */
.quick-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  overflow-x: auto;
  padding-bottom: 4px;
  -webkit-overflow-scrolling: touch;
  scroll-snap-type: x mandatory;
}
.quick-stat {
  flex: 1;
  min-width: 160px;
  scroll-snap-align: start;
}

/* Dashboard Cards Grid */
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.dashboard-card {
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 24px;
  border: 1px solid var(--border);
  text-decoration: none;
  color: inherit;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}
.dashboard-card::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  border-radius: 16px 16px 0 0;
}
.dashboard-card.executive::before { background: linear-gradient(90deg, #6366f1, #8b5cf6); }
.dashboard-card.sales::before { background: linear-gradient(90deg, #3b82f6, #06b6d4); }
.dashboard-card.finance::before { background: linear-gradient(90deg, #22c55e, #14b8a6); }
.dashboard-card.inventory::before { background: linear-gradient(90deg, #f97316, #eab308); }
.dashboard-card.operations::before { background: linear-gradient(90deg, #a855f7, #ec4899); }
.dashboard-card.rto::before { background: linear-gradient(90deg, #ef4444, #f97316); }
.dashboard-card.cashflow::before { background: linear-gradient(90deg, #14b8a6, #06b6d4); }

.dashboard-card:hover {
  border-color: var(--border-active);
  transform: translateY(-4px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.card-icon-wrap {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}
.card-icon-wrap.executive { background: rgba(99, 102, 241, 0.1); }
.card-icon-wrap.sales { background: rgba(59, 130, 246, 0.1); }
.card-icon-wrap.finance { background: rgba(34, 197, 94, 0.1); }
.card-icon-wrap.inventory { background: rgba(249, 115, 22, 0.1); }
.card-icon-wrap.operations { background: rgba(168, 85, 247, 0.1); }
.card-icon-wrap.rto { background: rgba(239, 68, 68, 0.1); }
.card-icon-wrap.cashflow { background: rgba(20, 184, 166, 0.1); }
.card-icon { font-size: 28px; }

.card-content h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}
.card-content p {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.5;
  margin-bottom: 20px;
}

.card-metrics {
  display: flex;
  gap: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
  margin-top: auto;
}
.card-metric-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  display: block;
}
.card-metric-label {
  font-size: 11px;
  color: var(--text-dim);
  text-transform: uppercase;
}

.card-arrow {
  position: absolute;
  bottom: 24px;
  right: 24px;
  color: #475569;
  transition: all 0.2s;
}
.dashboard-card:hover .card-arrow {
  color: var(--accent);
  transform: translateX(4px);
}

/* Quick Links */
.quick-links {
  background: var(--bg-card);
  border-radius: 16px;
  padding: 24px;
  border: 1px solid var(--border);
  margin-bottom: 24px;
}
.quick-links h2 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 16px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.links-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.quick-link {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px 18px;
  color: var(--text-muted);
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
}
.quick-link:hover {
  background: var(--bg-hover);
  border-color: var(--border-active);
  color: var(--text-secondary);
}

/* Footer */
.hub-footer {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  padding: 24px;
  color: var(--text-dim);
  font-size: 12px;
}
.refresh-btn {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  color: var(--text-muted);
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}
.refresh-btn:hover {
  border-color: var(--accent);
  color: var(--text-primary);
}

@media (max-width: 768px) {
  .quick-stats { flex-direction: column; }
  .quick-stat { min-width: auto; }
  .dashboard-grid { grid-template-columns: 1fr; }
  .links-grid { flex-direction: column; }
}
</style>
