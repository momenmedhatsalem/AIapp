<template>
  <div class="chart-card" :class="{ 'full-width': fullWidth }">
    <div class="chart-header">
      <h3>{{ title }}</h3>
      <slot name="actions"></slot>
    </div>
    <div class="chart-body" :style="{ height: height + 'px' }">
      <div v-if="loading" class="chart-loading">
        <div class="spinner"></div>
      </div>
      <div v-else-if="!hasData" class="chart-empty">No data available</div>
      <div v-else ref="chartContainer" class="chart-container"></div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from "vue";

// Lazy-load eCharts
let echartsPromise = null;
function loadECharts() {
  if (echartsPromise) return echartsPromise;
  echartsPromise = new Promise((resolve, reject) => {
    if (window.echarts) {
      resolve(window.echarts);
      return;
    }
    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js";
    script.onload = () => resolve(window.echarts);
    script.onerror = reject;
    document.head.appendChild(script);
  });
  return echartsPromise;
}

export default {
  name: "ChartCard",
  props: {
    title: { type: String, required: true },
    option: { type: Object, default: null },
    height: { type: Number, default: 300 },
    fullWidth: { type: Boolean, default: false },
    loading: { type: Boolean, default: false },
    hasData: { type: Boolean, default: true },
  },

  setup(props) {
    const chartContainer = ref(null);
    let chartInstance = null;
    let resizeObserver = null;

    const darkTheme = {
      backgroundColor: "transparent",
      textStyle: { color: "#94a3b8" },
      legend: { textStyle: { color: "#94a3b8" } },
      categoryAxis: {
        axisLine: { lineStyle: { color: "#334155" } },
        axisTick: { lineStyle: { color: "#334155" } },
        axisLabel: { color: "#94a3b8" },
        splitLine: { lineStyle: { color: "#1e293b" } },
      },
      valueAxis: {
        axisLine: { lineStyle: { color: "#334155" } },
        axisTick: { lineStyle: { color: "#334155" } },
        axisLabel: { color: "#94a3b8" },
        splitLine: { lineStyle: { color: "#1e293b" } },
      },
    };

    async function initChart() {
      if (!chartContainer.value || !props.option) return;

      const echarts = await loadECharts();

      if (chartInstance) {
        chartInstance.dispose();
      }

      chartInstance = echarts.init(chartContainer.value, darkTheme);
      chartInstance.setOption(props.option);
    }

    watch(
      () => props.option,
      async () => {
        await nextTick();
        if (chartInstance && props.option) {
          chartInstance.setOption(props.option, { notMerge: true });
        } else {
          initChart();
        }
      },
      { deep: true }
    );

    onMounted(async () => {
      await nextTick();
      await initChart();

      // Auto-resize
      resizeObserver = new ResizeObserver(() => {
        if (chartInstance) chartInstance.resize();
      });
      if (chartContainer.value) {
        resizeObserver.observe(chartContainer.value);
      }
    });

    onBeforeUnmount(() => {
      if (chartInstance) chartInstance.dispose();
      if (resizeObserver) resizeObserver.disconnect();
    });

    return { chartContainer };
  },
};
</script>

<style scoped>
.chart-card {
  background: var(--bg-card);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--border);
}
.chart-card.full-width {
  grid-column: 1 / -1;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.chart-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.chart-body {
  position: relative;
}

.chart-container {
  width: 100%;
  height: 100%;
}

.chart-loading,
.chart-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-dim);
  font-size: 13px;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .chart-card { padding: 16px; }
}
</style>
