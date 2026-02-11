<template>
  <div id="justyol-dashboard" :class="{ 'sidebar-open': sidebarOpen }">
    <!-- Sidebar Navigation -->
    <DashboardSidebar
      :open="sidebarOpen"
      :active-route="currentRoute"
      @toggle="sidebarOpen = !sidebarOpen"
      @navigate="navigateTo"
    />

    <!-- Main Content -->
    <main class="dashboard-main">
      <!-- Top Bar -->
      <TopBar
        :company="selectedCompany"
        :companies="companies"
        @company-change="setCompany"
        @toggle-sidebar="sidebarOpen = !sidebarOpen"
      />

      <!-- Dashboard Content -->
      <div class="dashboard-content">
        <router-view
          :company="selectedCompany"
          :key="selectedCompany"
        />
      </div>
    </main>

    <!-- Mobile Navigation -->
    <MobileNav :active-route="currentRoute" @navigate="navigateTo" />
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import { useRouter, useRoute } from "vue-router";
import DashboardSidebar from "./components/DashboardSidebar.vue";
import TopBar from "./components/TopBar.vue";
import MobileNav from "./components/MobileNav.vue";

export default {
  name: "JustyolDashboard",
  components: { DashboardSidebar, TopBar, MobileNav },

  setup() {
    const router = useRouter();
    const route = useRoute();

    const sidebarOpen = ref(window.innerWidth > 1024);
    const selectedCompany = ref(
      localStorage.getItem("justyol_company") || "Justyol Morocco"
    );
    const companies = ref([
      { value: "Justyol Morocco", label: "Justyol Morocco", currency: "MAD" },
      { value: "Justyol China", label: "Justyol China", currency: "USD" },
      { value: "Justyol Holding", label: "Justyol Holding", currency: "USD" },
      { value: "Maslak LTD", label: "Maslak LTD", currency: "TRY" },
    ]);

    const currentRoute = computed(() => route.path);

    function setCompany(company) {
      selectedCompany.value = company;
      localStorage.setItem("justyol_company", company);
    }

    function navigateTo(path) {
      router.push(path);
      if (window.innerWidth < 1024) {
        sidebarOpen.value = false;
      }
    }

    // Handle realtime updates
    function onDashboardUpdate(event) {
      const data = event.detail;
      if (data.company && data.company !== selectedCompany.value) return;
      // Components handle their own updates via the event
    }

    onMounted(() => {
      window.addEventListener("dashboard-update", onDashboardUpdate);
      // Responsive sidebar
      window.addEventListener("resize", () => {
        sidebarOpen.value = window.innerWidth > 1024;
      });
    });

    onBeforeUnmount(() => {
      window.removeEventListener("dashboard-update", onDashboardUpdate);
    });

    return {
      sidebarOpen,
      selectedCompany,
      companies,
      currentRoute,
      setCompany,
      navigateTo,
    };
  },
};
</script>

<style>
@import url("https://fonts.googleapis.com/css2?family=Alexandria:wght@300;400;500;600;700&display=swap");

:root {
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --bg-card: rgba(30, 41, 59, 0.7);
  --bg-hover: rgba(99, 102, 241, 0.1);
  --border: rgba(51, 65, 85, 0.5);
  --border-active: rgba(99, 102, 241, 0.4);
  --text-primary: #f1f5f9;
  --text-secondary: #e2e8f0;
  --text-muted: #94a3b8;
  --text-dim: #64748b;
  --accent: #6366f1;
  --accent-light: #818cf8;
  --blue: #3b82f6;
  --green: #22c55e;
  --yellow: #eab308;
  --orange: #f97316;
  --red: #ef4444;
  --purple: #a855f7;
  --cyan: #06b6d4;
  --teal: #14b8a6;
  --sidebar-width: 260px;
  --topbar-height: 64px;
  --mobile-nav-height: 64px;
  --safe-bottom: env(safe-area-inset-bottom, 0px);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#justyol-dashboard {
  font-family: "Alexandria", "Inter", -apple-system, sans-serif;
  background: linear-gradient(135deg, var(--bg-primary) 0%, #1e1b4b 100%);
  color: var(--text-secondary);
  min-height: 100vh;
  display: flex;
}

.dashboard-main {
  flex: 1;
  margin-left: var(--sidebar-width);
  min-height: 100vh;
  transition: margin-left 0.3s ease;
}

.dashboard-content {
  padding: 24px;
  padding-top: calc(var(--topbar-height) + 24px);
}

/* Responsive */
@media (max-width: 1024px) {
  .dashboard-main {
    margin-left: 0;
  }

  .dashboard-content {
    padding: 16px;
    padding-top: calc(var(--topbar-height) + 16px);
    padding-bottom: calc(var(--mobile-nav-height) + var(--safe-bottom) + 16px);
  }
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: var(--bg-primary);
}
::-webkit-scrollbar-thumb {
  background: #334155;
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: #475569;
}
</style>
