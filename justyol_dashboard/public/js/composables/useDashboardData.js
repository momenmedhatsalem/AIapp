import { ref, watch, onMounted, onBeforeUnmount } from "vue";

/**
 * Composable for fetching dashboard data with caching, loading states,
 * and real-time updates.
 *
 * @param {string} apiMethod - Frappe whitelisted method path
 * @param {Object} params - Reactive params object
 * @param {Object} options - { autoRefresh: bool, refreshInterval: number, realtimeEvent: string }
 */
export function useDashboardData(apiMethod, params = {}, options = {}) {
  const data = ref(null);
  const loading = ref(true);
  const error = ref(null);
  const lastUpdated = ref(null);

  const { autoRefresh = false, refreshInterval = 300000, realtimeEvent = null } = options;

  let refreshTimer = null;

  async function fetchData() {
    loading.value = true;
    error.value = null;

    try {
      const result = await frappe.call({
        method: apiMethod,
        args: typeof params === "function" ? params() : params,
        freeze: false,
      });

      data.value = result.message;
      lastUpdated.value = new Date();
    } catch (err) {
      error.value = err.message || "Failed to load data";
      console.error(`Dashboard data error (${apiMethod}):`, err);
    } finally {
      loading.value = false;
    }
  }

  async function refresh() {
    await fetchData();
  }

  // Watch for param changes and refetch
  if (typeof params === "object" && params !== null) {
    watch(
      () => JSON.stringify(typeof params === "function" ? params() : params),
      () => fetchData(),
      { deep: true }
    );
  }

  // Auto refresh
  if (autoRefresh) {
    refreshTimer = setInterval(fetchData, refreshInterval);
  }

  // Real-time updates
  function onRealtimeUpdate(event) {
    const detail = event.detail;
    if (realtimeEvent && detail.type === realtimeEvent) {
      fetchData();
    }
  }

  onMounted(() => {
    fetchData();
    if (realtimeEvent) {
      window.addEventListener("dashboard-update", onRealtimeUpdate);
    }
  });

  onBeforeUnmount(() => {
    if (refreshTimer) clearInterval(refreshTimer);
    if (realtimeEvent) {
      window.removeEventListener("dashboard-update", onRealtimeUpdate);
    }
  });

  return { data, loading, error, lastUpdated, refresh };
}


/**
 * Composable for managing date/period filters.
 */
export function useFilters() {
  const period = ref("today");
  const fromDate = ref(null);
  const toDate = ref(null);
  const customRange = ref(false);

  const periods = [
    { value: "today", label: "Today" },
    { value: "yesterday", label: "Yesterday" },
    { value: "week", label: "This Week" },
    { value: "month", label: "This Month" },
    { value: "last_month", label: "Last Month" },
    { value: "quarter", label: "This Quarter" },
    { value: "year", label: "This Year" },
  ];

  function setPeriod(p) {
    period.value = p;
    customRange.value = false;
  }

  function setDateRange(from, to) {
    fromDate.value = from;
    toDate.value = to;
    customRange.value = true;
  }

  function getParams(company) {
    if (customRange.value && fromDate.value && toDate.value) {
      return { company, from_date: fromDate.value, to_date: toDate.value };
    }
    return { company, period: period.value };
  }

  return { period, fromDate, toDate, customRange, periods, setPeriod, setDateRange, getParams };
}
