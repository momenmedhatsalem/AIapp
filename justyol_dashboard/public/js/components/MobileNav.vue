<template>
  <nav class="mobile-nav">
    <a
      v-for="item in navItems"
      :key="item.path"
      class="mobile-nav-item"
      :class="{ active: activeRoute === item.path }"
      @click.prevent="$emit('navigate', item.path)"
    >
      <span class="mobile-nav-icon" v-html="item.icon"></span>
      <small>{{ item.label }}</small>
    </a>
  </nav>
</template>

<script>
export default {
  name: "MobileNav",
  props: {
    activeRoute: { type: String, default: "/" },
  },
  emits: ["navigate"],

  setup() {
    const navItems = [
      { path: "/", label: "Hub", icon: "&#127968;" },
      { path: "/executive", label: "Executive", icon: "&#128202;" },
      { path: "/sales", label: "Sales", icon: "&#128176;" },
      { path: "/operations", label: "Ops", icon: "&#9881;" },
      { path: "/inventory", label: "Inventory", icon: "&#128230;" },
    ];
    return { navItems };
  },
};
</script>

<style scoped>
.mobile-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(180deg, #1e293b, #0f172a);
  display: none;
  justify-content: space-around;
  padding: 8px 0;
  padding-bottom: calc(8px + var(--safe-bottom));
  border-top: 1px solid var(--border);
  z-index: 100;
  backdrop-filter: blur(20px);
}

.mobile-nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  text-decoration: none;
  color: var(--text-muted);
  font-size: 10px;
  padding: 6px 12px;
  border-radius: 8px;
  transition: all 0.2s;
  min-width: 56px;
}

.mobile-nav-item.active {
  color: var(--accent-light);
  background: var(--bg-hover);
}

.mobile-nav-icon {
  font-size: 20px;
}

@media (max-width: 1024px) {
  .mobile-nav {
    display: flex;
  }
}
</style>
