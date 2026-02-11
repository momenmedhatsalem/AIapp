import { createRouter, createWebHashHistory } from "vue-router";

// Lazy-loaded page components
const GrowthHub = () => import("./pages/GrowthHub.vue");
const ExecutiveDashboard = () => import("./pages/ExecutiveDashboard.vue");
const SalesDashboard = () => import("./pages/SalesDashboard.vue");
const OperationsDashboard = () => import("./pages/OperationsDashboard.vue");
const ConfirmationDashboard = () => import("./pages/ConfirmationDashboard.vue");
const FinanceDashboard = () => import("./pages/FinanceDashboard.vue");
const LogisticsDashboard = () => import("./pages/LogisticsDashboard.vue");
const InventoryDashboard = () => import("./pages/InventoryDashboard.vue");
const RTODashboard = () => import("./pages/RTODashboard.vue");
const CashFlowDashboard = () => import("./pages/CashFlowDashboard.vue");
const CustomerIntelligence = () => import("./pages/CustomerIntelligence.vue");
const MarketingDashboard = () => import("./pages/MarketingDashboard.vue");
const WarehouseDashboard = () => import("./pages/WarehouseDashboard.vue");
const AlertsCenter = () => import("./pages/AlertsCenter.vue");

const routes = [
  { path: "/", name: "growth-hub", component: GrowthHub, meta: { title: "Growth Hub" } },
  { path: "/executive", name: "executive", component: ExecutiveDashboard, meta: { title: "Executive Dashboard" } },
  { path: "/sales", name: "sales", component: SalesDashboard, meta: { title: "Sales Intelligence" } },
  { path: "/operations", name: "operations", component: OperationsDashboard, meta: { title: "Operations Center" } },
  { path: "/confirmation", name: "confirmation", component: ConfirmationDashboard, meta: { title: "Confirmation Center" } },
  { path: "/finance", name: "finance", component: FinanceDashboard, meta: { title: "Finance Control" } },
  { path: "/logistics", name: "logistics", component: LogisticsDashboard, meta: { title: "Logistics & Shipping" } },
  { path: "/inventory", name: "inventory", component: InventoryDashboard, meta: { title: "Inventory Intelligence" } },
  { path: "/rto", name: "rto", component: RTODashboard, meta: { title: "RTO & Returns" } },
  { path: "/cashflow", name: "cashflow", component: CashFlowDashboard, meta: { title: "COD Cash Flow" } },
  { path: "/customers", name: "customers", component: CustomerIntelligence, meta: { title: "Customer Intelligence" } },
  { path: "/marketing", name: "marketing", component: MarketingDashboard, meta: { title: "Marketing & Media" } },
  { path: "/warehouse", name: "warehouse", component: WarehouseDashboard, meta: { title: "Warehouse Operations" } },
  { path: "/alerts", name: "alerts", component: AlertsCenter, meta: { title: "Alerts Center" } },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

router.beforeEach((to) => {
  document.title = `${to.meta.title || "Dashboard"} | Justyol`;
});

export default router;
