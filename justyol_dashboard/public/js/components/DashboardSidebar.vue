<template>
  <aside class="sidebar" :class="{ open }">
    <div class="sidebar-header">
      <div class="logo">
        <div class="logo-icon">J</div>
        <span class="logo-text">Justyol</span>
      </div>
      <button class="sidebar-close" @click="$emit('toggle')">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
    </div>

    <nav class="sidebar-nav">
      <div class="nav-section">
        <div class="nav-section-title">Main</div>
        <a
          v-for="item in mainNav"
          :key="item.path"
          class="nav-link"
          :class="{ active: activeRoute === item.path }"
          @click.prevent="$emit('navigate', item.path)"
        >
          <span class="nav-icon" v-html="item.icon"></span>
          <span class="nav-label">{{ item.label }}</span>
        </a>
      </div>

      <div class="nav-section">
        <div class="nav-section-title">Operations</div>
        <a
          v-for="item in opsNav"
          :key="item.path"
          class="nav-link"
          :class="{ active: activeRoute === item.path, disabled: item.disabled }"
          @click.prevent="!item.disabled && $emit('navigate', item.path)"
        >
          <span class="nav-icon" v-html="item.icon"></span>
          <span class="nav-label">{{ item.label }}</span>
          <span v-if="item.disabled" class="coming-soon">Soon</span>
        </a>
      </div>

      <div class="nav-section">
        <div class="nav-section-title">Intelligence</div>
        <a
          v-for="item in intelNav"
          :key="item.path"
          class="nav-link"
          :class="{ active: activeRoute === item.path, disabled: item.disabled }"
          @click.prevent="!item.disabled && $emit('navigate', item.path)"
        >
          <span class="nav-icon" v-html="item.icon"></span>
          <span class="nav-label">{{ item.label }}</span>
          <span v-if="item.disabled" class="coming-soon">Soon</span>
        </a>
      </div>
    </nav>

    <div class="sidebar-footer">
      <a href="/app" class="nav-link">
        <span class="nav-icon">&#9881;</span>
        <span class="nav-label">Back to ERPNext</span>
      </a>
    </div>
  </aside>

  <!-- Overlay for mobile -->
  <div v-if="open" class="sidebar-overlay" @click="$emit('toggle')"></div>
</template>

<script>
export default {
  name: "DashboardSidebar",
  props: {
    open: { type: Boolean, default: true },
    activeRoute: { type: String, default: "/" },
  },
  emits: ["toggle", "navigate"],

  setup() {
    const mainNav = [
      { path: "/", label: "Growth Hub", icon: "&#127968;" },
      { path: "/executive", label: "Executive", icon: "&#128202;" },
      { path: "/sales", label: "Sales Intelligence", icon: "&#128176;" },
      { path: "/finance", label: "Finance Control", icon: "&#128200;" },
    ];

    const opsNav = [
      { path: "/operations", label: "Operations", icon: "&#9881;" },
      { path: "/confirmation", label: "Confirmation", icon: "&#128172;" },
      { path: "/logistics", label: "Logistics", icon: "&#128666;" },
      { path: "/inventory", label: "Inventory", icon: "&#128230;" },
      { path: "/warehouse", label: "Warehouse", icon: "&#127981;" },
    ];

    const intelNav = [
      { path: "/rto", label: "RTO & Returns", icon: "&#128260;" },
      { path: "/cashflow", label: "COD Cash Flow", icon: "&#128178;" },
      { path: "/customers", label: "Customer Intel", icon: "&#128101;" },
      { path: "/marketing", label: "Marketing", icon: "&#128226;" },
      { path: "/alerts", label: "Alerts Center", icon: "&#128276;" },
    ];

    return { mainNav, opsNav, intelNav };
  },
};
</script>

<style scoped>
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: var(--sidebar-width);
  height: 100vh;
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(20px);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  z-index: 100;
  overflow-y: auto;
  transition: transform 0.3s ease;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid var(--border);
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, var(--accent), #8b5cf6);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 18px;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.sidebar-close {
  display: none;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 8px;
}

.sidebar-nav {
  flex: 1;
  padding: 12px 0;
  overflow-y: auto;
}

.nav-section {
  margin-bottom: 8px;
}

.nav-section-title {
  padding: 8px 20px;
  font-size: 10px;
  font-weight: 600;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 20px;
  color: var(--text-muted);
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.15s ease;
  cursor: pointer;
  border-left: 3px solid transparent;
}

.nav-link:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}

.nav-link.active {
  color: var(--accent-light);
  background: var(--bg-hover);
  border-left-color: var(--accent);
}

.nav-link.disabled {
  opacity: 0.4;
  cursor: default;
}
.nav-link.disabled:hover {
  background: none;
  color: var(--text-muted);
}

.nav-icon {
  font-size: 18px;
  width: 24px;
  text-align: center;
}

.coming-soon {
  margin-left: auto;
  font-size: 9px;
  padding: 2px 6px;
  border-radius: 3px;
  background: rgba(99, 102, 241, 0.15);
  color: var(--accent-light);
}

.sidebar-footer {
  padding: 12px 0;
  border-top: 1px solid var(--border);
}

.sidebar-overlay {
  display: none;
}

@media (max-width: 1024px) {
  .sidebar {
    transform: translateX(-100%);
  }
  .sidebar.open {
    transform: translateX(0);
  }
  .sidebar-close {
    display: block;
  }
  .sidebar-overlay {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 99;
  }
}
</style>
