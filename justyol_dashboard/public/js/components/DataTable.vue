<template>
  <div class="data-table-card">
    <div class="table-header">
      <h3>{{ title }}</h3>
      <span v-if="badge" class="badge" :class="badgeColor">{{ badge }}</span>
    </div>
    <div class="table-container">
      <table v-if="!loading && rows.length > 0">
        <thead>
          <tr>
            <th v-if="showIndex">#</th>
            <th v-for="col in columns" :key="col.key" :class="col.align || ''">
              {{ col.label }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in rows" :key="index">
            <td v-if="showIndex">{{ index + 1 }}</td>
            <td v-for="col in columns" :key="col.key" :class="col.align || ''">
              <template v-if="col.format === 'currency'">
                {{ formatCurrency(row[col.key]) }}
              </template>
              <template v-else-if="col.format === 'number'">
                {{ formatNumber(row[col.key]) }}
              </template>
              <template v-else-if="col.format === 'percent'">
                {{ formatPercent(row[col.key]) }}
              </template>
              <template v-else-if="col.format === 'badge'">
                <span class="status-badge" :class="col.badgeColor || 'green'">
                  {{ row[col.key] }}
                </span>
              </template>
              <template v-else>
                {{ row[col.key] || '--' }}
              </template>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else-if="loading" class="table-loading">Loading...</div>
      <div v-else class="table-empty">No data available</div>
    </div>
  </div>
</template>

<script>
export default {
  name: "DataTable",
  props: {
    title: { type: String, required: true },
    columns: { type: Array, required: true },
    rows: { type: Array, default: () => [] },
    loading: { type: Boolean, default: false },
    showIndex: { type: Boolean, default: true },
    badge: { type: String, default: null },
    badgeColor: { type: String, default: "green" },
    currency: { type: String, default: "MAD" },
  },

  setup(props) {
    function formatNumber(val) {
      if (val === null || val === undefined) return "--";
      return Number(val).toLocaleString("en-US", { maximumFractionDigits: 0 });
    }

    function formatCurrency(val) {
      if (val === null || val === undefined) return "--";
      const num = Number(val);
      if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
      if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
      return `${num.toLocaleString("en-US", { maximumFractionDigits: 0 })} ${props.currency}`;
    }

    function formatPercent(val) {
      if (val === null || val === undefined) return "--";
      return `${Number(val).toFixed(1)}%`;
    }

    return { formatNumber, formatCurrency, formatPercent };
  },
};
</script>

<style scoped>
.data-table-card {
  background: var(--bg-card);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--border);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.table-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.badge {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
}
.badge.green { background: rgba(34, 197, 94, 0.15); color: var(--green); }
.badge.purple { background: rgba(168, 85, 247, 0.15); color: var(--purple); }
.badge.blue { background: rgba(59, 130, 246, 0.15); color: var(--blue); }

.table-container {
  overflow-x: auto;
  max-height: 400px;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

thead {
  position: sticky;
  top: 0;
  background: rgba(30, 41, 59, 0.95);
  z-index: 1;
}

th {
  text-align: left;
  padding: 10px 12px;
  color: var(--text-dim);
  font-weight: 600;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid #334155;
}

td {
  padding: 10px 12px;
  color: var(--text-secondary);
  border-bottom: 1px solid #1e293b;
}

tbody tr:hover {
  background: var(--bg-hover);
}

.right { text-align: right; }

.status-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
}
.status-badge.green { background: rgba(34, 197, 94, 0.15); color: var(--green); }

.table-loading,
.table-empty {
  text-align: center;
  padding: 32px;
  color: var(--text-dim);
  font-size: 13px;
}
</style>
