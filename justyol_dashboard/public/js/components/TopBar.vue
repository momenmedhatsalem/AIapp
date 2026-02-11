<template>
  <header class="topbar">
    <div class="topbar-left">
      <button class="menu-toggle" @click="$emit('toggle-sidebar')">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
      </button>
    </div>

    <div class="topbar-center">
      <div class="company-selector">
        <label>Company</label>
        <select :value="company" @change="$emit('company-change', $event.target.value)">
          <option v-for="c in companies" :key="c.value" :value="c.value">
            {{ c.label }} ({{ c.currency }})
          </option>
        </select>
      </div>
    </div>

    <div class="topbar-right">
      <span class="datetime">{{ datetime }}</span>
      <div class="user-info" v-if="user">
        <span class="user-name">{{ user }}</span>
        <div class="user-avatar">{{ initials }}</div>
      </div>
    </div>
  </header>
</template>

<script>
import { ref, computed, onMounted } from "vue";

export default {
  name: "TopBar",
  props: {
    company: { type: String, required: true },
    companies: { type: Array, required: true },
  },
  emits: ["company-change", "toggle-sidebar"],

  setup() {
    const datetime = ref("");
    const user = ref("");

    const initials = computed(() => {
      if (!user.value) return "?";
      return user.value
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .substring(0, 2);
    });

    function updateDateTime() {
      datetime.value = new Date().toLocaleDateString("en-US", {
        weekday: "short",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    }

    onMounted(() => {
      user.value = frappe.session?.user_fullname || frappe.session?.user || "";
      updateDateTime();
      setInterval(updateDateTime, 60000);
    });

    return { datetime, user, initials };
  },
};
</script>

<style scoped>
.topbar {
  position: fixed;
  top: 0;
  left: var(--sidebar-width);
  right: 0;
  height: var(--topbar-height);
  background: rgba(15, 23, 42, 0.9);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  z-index: 90;
  transition: left 0.3s ease;
}

.topbar-left {
  display: flex;
  align-items: center;
}

.menu-toggle {
  display: none;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
}
.menu-toggle:hover {
  background: var(--bg-hover);
}

.company-selector {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.company-selector label {
  font-size: 9px;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.company-selector select {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 16px;
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  outline: none;
  min-width: 200px;
  font-family: inherit;
}
.company-selector select:focus {
  border-color: var(--accent);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.datetime {
  font-size: 12px;
  color: var(--text-muted);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-name {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.user-avatar {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, var(--accent), #a855f7);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  color: white;
}

@media (max-width: 1024px) {
  .topbar {
    left: 0;
  }
  .menu-toggle {
    display: block;
  }
  .datetime, .user-name {
    display: none;
  }
  .company-selector select {
    min-width: 160px;
  }
}
</style>
