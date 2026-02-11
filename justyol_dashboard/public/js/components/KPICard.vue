<template>
  <div class="kpi-card" :class="variant">
    <div class="kpi-header">
      <div class="kpi-icon" :class="iconColor">
        <slot name="icon">
          <span v-html="icon"></span>
        </slot>
      </div>
      <span v-if="trend !== null" class="kpi-trend" :class="trendClass">
        {{ trendDirection }} {{ Math.abs(trend).toFixed(1) }}%
      </span>
    </div>
    <div class="kpi-value">{{ formattedValue }}</div>
    <div class="kpi-label">{{ label }}</div>
    <div v-if="subValue" class="kpi-sub">
      {{ subLabel }}: <strong :class="subClass">{{ subValue }}</strong>
    </div>
  </div>
</template>

<script>
import { computed } from "vue";

export default {
  name: "KPICard",
  props: {
    value: { type: [Number, String], default: null },
    label: { type: String, required: true },
    icon: { type: String, default: "" },
    iconColor: { type: String, default: "blue" },
    variant: { type: String, default: "" },
    format: { type: String, default: "number" }, // number, currency, percent
    currency: { type: String, default: "MAD" },
    trend: { type: Number, default: null },
    trendInverse: { type: Boolean, default: false },
    subValue: { type: String, default: null },
    subLabel: { type: String, default: "vs Previous" },
    subClass: { type: String, default: "" },
  },

  setup(props) {
    const formattedValue = computed(() => {
      if (props.value === null || props.value === undefined) return "--";
      const num = Number(props.value);
      if (isNaN(num)) return props.value;

      if (props.format === "currency") {
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M ${props.currency}`;
        if (num >= 1000) return `${(num / 1000).toFixed(1)}K ${props.currency}`;
        return `${num.toLocaleString("en-US", { maximumFractionDigits: 0 })} ${props.currency}`;
      }
      if (props.format === "percent") {
        return `${num.toFixed(1)}%`;
      }
      return num.toLocaleString("en-US", { maximumFractionDigits: 0 });
    });

    const trendDirection = computed(() => (props.trend >= 0 ? "\u2191" : "\u2193"));

    const trendClass = computed(() => {
      if (props.trend === null) return "";
      const isPositive = props.trend >= 0;
      const isGood = props.trendInverse ? !isPositive : isPositive;
      return isGood ? "trend-up" : "trend-down";
    });

    return { formattedValue, trendDirection, trendClass };
  },
};
</script>

<style scoped>
.kpi-card {
  background: var(--bg-card);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--border);
  transition: all 0.2s ease;
}
.kpi-card:hover {
  border-color: var(--border-active);
  transform: translateY(-2px);
}

.kpi-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.kpi-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}
.kpi-icon.blue { background: rgba(59, 130, 246, 0.15); color: var(--blue); }
.kpi-icon.green { background: rgba(34, 197, 94, 0.15); color: var(--green); }
.kpi-icon.purple { background: rgba(168, 85, 247, 0.15); color: var(--purple); }
.kpi-icon.cyan { background: rgba(6, 182, 212, 0.15); color: var(--cyan); }
.kpi-icon.orange { background: rgba(249, 115, 22, 0.15); color: var(--orange); }
.kpi-icon.red { background: rgba(239, 68, 68, 0.15); color: var(--red); }
.kpi-icon.teal { background: rgba(20, 184, 166, 0.15); color: var(--teal); }

.kpi-trend {
  font-size: 12px;
  font-weight: 600;
}
.trend-up { color: var(--green); }
.trend-down { color: var(--red); }

.kpi-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
  line-height: 1.2;
}

.kpi-label {
  font-size: 12px;
  color: var(--text-dim);
  margin-bottom: 12px;
}

.kpi-sub {
  font-size: 11px;
  color: var(--text-dim);
}
.kpi-sub strong {
  color: var(--text-muted);
}

@media (max-width: 768px) {
  .kpi-card { padding: 16px; }
  .kpi-value { font-size: 22px; }
}
</style>
