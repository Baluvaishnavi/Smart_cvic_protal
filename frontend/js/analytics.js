/**
 * Executive Analytics & SLA Command Center module.
 * Renders Chart.js charts for category distribution, aging buckets,
 * department compliance, and triggers Leaflet hotspot map markers.
 */

import { Api } from "./api.js";
import { Toast } from "./toast.js";

export const AnalyticsPortal = {
  charts: {},

  init() {
    this.bindEvents();
    this.refreshAnalytics();
  },

  bindEvents() {
    const btnRefresh = document.getElementById("btn-analytics-refresh");
    if (btnRefresh) {
      btnRefresh.addEventListener("click", () => {
        this.refreshAnalytics();
        Toast.info("Analytics metrics refreshed.");
      });
    }

    const btnSeed = document.getElementById("btn-reseed-data");
    if (btnSeed) {
      btnSeed.addEventListener("click", () => this.handleReseed());
    }
  },

  async handleReseed() {
    if (!confirm("Reset database with standard realistic Civic Service Requests?")) return;
    try {
      const res = await Api.seedDatabase(true);
      Toast.success(res.message);
      this.refreshAnalytics();
      if (window.AdminPortal) window.AdminPortal.loadQueues();
      if (window.ApprovalsManager) window.ApprovalsManager.loadApprovals();
    } catch (err) {
      Toast.error("Reseed failed: " + err.message);
    }
  },

  async refreshAnalytics() {
    try {
      const data = await Api.getDashboardMetrics();
      const hotspots = await Api.getHotspots();

      this.updateKPICards(data.summary);
      this.renderCategoryChart(data.category_distribution);
      this.renderAgingChart(data.aging_breakdown);
      this.renderDepartmentSLAChart(data.department_sla);
      this.renderStatusChart(data.status_distribution);
      this.renderHighPriorityLocations(hotspots);
    } catch (err) {
      console.error("Failed to load analytics:", err);
    }
  },

  updateKPICards(summary) {
    if (!summary) return;

    document.getElementById("kpi-total").textContent = summary.total;
    document.getElementById("kpi-unresolved").textContent = summary.unresolved;
    document.getElementById("kpi-aging").textContent = summary.aging_count;
    document.getElementById("kpi-sla-breached").textContent = summary.sla_breached;
    document.getElementById("kpi-sla-compliance").textContent = `${summary.sla_compliance_rate}%`;
    document.getElementById("kpi-mttr").textContent = `${summary.avg_resolution_hours}h`;

    // Highlight breach card if breaches exist
    const breachedCard = document.getElementById("kpi-breached-card");
    if (breachedCard) {
      if (summary.sla_breached > 0) {
        breachedCard.classList.add("border-red-300", "bg-red-50/50");
      } else {
        breachedCard.classList.remove("border-red-300", "bg-red-50/50");
      }
    }
  },

  renderCategoryChart(catData) {
    const canvas = document.getElementById("chart-categories");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (this.charts.categories) this.charts.categories.destroy();

    const labels = Object.keys(catData || {});
    const values = Object.values(catData || {});

    const colors = [
      "#3b82f6", "#f59e0b", "#ef4444", "#10b981", "#8b5cf6",
      "#ec4899", "#14b8a6", "#64748b", "#06b6d4"
    ];

    this.charts.categories = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: colors.slice(0, labels.length),
          borderWidth: 2,
          borderColor: "#ffffff",
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "right", labels: { font: { size: 11, family: "'Inter', sans-serif" } } }
        }
      }
    });
  },

  renderAgingChart(agingData) {
    const canvas = document.getElementById("chart-aging");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (this.charts.aging) this.charts.aging.destroy();

    const labels = ["0-24 hrs (Fresh)", "24-48 hrs", "48-72 hrs", ">72 hrs (Aging)"];
    const values = [
      agingData?.["0_24h"] || 0,
      agingData?.["24_48h"] || 0,
      agingData?.["48_72h"] || 0,
      agingData?.["over_72h"] || 0,
    ];

    this.charts.aging = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [{
          label: "Active Complaints",
          data: values,
          backgroundColor: ["#10b981", "#f59e0b", "#f97316", "#ef4444"],
          borderRadius: 6,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, grid: { color: "#f1f5f9" } },
          x: { grid: { display: false } }
        }
      }
    });
  },

  renderDepartmentSLAChart(deptData) {
    const canvas = document.getElementById("chart-department-sla");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (this.charts.deptSla) this.charts.deptSla.destroy();

    const depts = Object.keys(deptData || {});
    const rates = depts.map((d) => deptData[d]?.compliance_rate || 0);
    // Shorten department labels for legibility
    const shortLabels = depts.map((d) => d.split("(")[0].trim().replace("Department of ", ""));

    this.charts.deptSla = new Chart(ctx, {
      type: "bar",
      data: {
        labels: shortLabels,
        datasets: [{
          label: "SLA Compliance Rate (%)",
          data: rates,
          backgroundColor: rates.map((r) => r >= 85 ? "#10b981" : r >= 70 ? "#f59e0b" : "#ef4444"),
          borderRadius: 6,
        }]
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { min: 0, max: 100, grid: { color: "#f1f5f9" } },
          y: { grid: { display: false } }
        }
      }
    });
  },

  renderStatusChart(statusData) {
    const canvas = document.getElementById("chart-status");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (this.charts.status) this.charts.status.destroy();

    const labels = ["New", "Assigned", "In Progress", "Resolved"];
    const values = [
      statusData?.NEW || 0,
      statusData?.ASSIGNED || 0,
      statusData?.IN_PROGRESS || 0,
      statusData?.RESOLVED || 0,
    ];

    this.charts.status = new Chart(ctx, {
      type: "pie",
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: ["#94a3b8", "#3b82f6", "#8b5cf6", "#10b981"],
          borderWidth: 2,
          borderColor: "#ffffff",
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom", labels: { font: { size: 11, family: "'Inter', sans-serif" } } }
        }
      }
    });
  },

  renderHighPriorityLocations(hotspots) {
    const tbody = document.getElementById("analytics-hotspots-tbody");
    if (!tbody) return;

    if (!hotspots || hotspots.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="py-6 text-center text-xs text-slate-400">No high-density problem clusters identified.</td></tr>`;
      return;
    }

    tbody.innerHTML = hotspots.map((h) => {
      let tierColor = "bg-slate-100 text-slate-700 border-slate-200";
      if (h.highest_priority === "CRITICAL") tierColor = "bg-red-100 text-red-800 border-red-300";
      else if (h.highest_priority === "HIGH") tierColor = "bg-amber-100 text-amber-800 border-amber-300";
      else if (h.highest_priority === "MEDIUM") tierColor = "bg-blue-100 text-blue-800 border-blue-300";

      return `
        <tr class="border-b border-slate-100 hover:bg-slate-50 text-xs">
          <td class="py-3 px-3">
            <span class="font-bold text-slate-900">${h.location_address || "District Sector"}</span>
            <span class="block text-[11px] text-slate-500 font-medium">${h.borough || "Central Ward"}</span>
          </td>
          <td class="py-3 px-3">
            <span class="px-2 py-0.5 rounded-full font-bold text-[11px] bg-slate-100 text-slate-800">
              ${h.count} complaints
            </span>
          </td>
          <td class="py-3 px-3">
            <span class="px-2 py-0.5 rounded-md font-bold text-[10px] border ${tierColor}">
              ${h.highest_priority} (${h.max_priority_score})
            </span>
          </td>
          <td class="py-3 px-3">
            <div class="flex flex-wrap gap-1">
              ${(h.categories || []).map((cat) => `<span class="px-1.5 py-0.5 rounded text-[10px] bg-blue-50 text-blue-700 border border-blue-200">${cat}</span>`).join("")}
            </div>
          </td>
          <td class="py-3 px-3 text-right">
            <span class="text-[11px] font-semibold text-slate-500">Active Hotspot</span>
          </td>
        </tr>
      `;
    }).join("");
  },
};
