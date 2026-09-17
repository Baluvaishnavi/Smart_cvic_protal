/**
 * Municipal Operations Admin Portal:
 * Lifecycle Queue Management (New -> Assigned -> In Progress -> Resolved),
 * Rule-Based Prioritization Inspector, Assignment, and Approval / Rejection Actions.
 */

import { Api } from "./api.js";
import { Toast } from "./toast.js";

export const AdminPortal = {
  complaints: [],
  currentFilter: {
    status: "ALL",
    approval_status: "ALL",
    category: "ALL",
    borough: "ALL",
    priority: "ALL",
    is_aging: false,
    search: "",
  },
  activeTicketId: null,

  init() {
    this.bindEvents();
    this.loadQueues();
  },

  bindEvents() {
    // Filter Controls
    const searchInput = document.getElementById("admin-search-input");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        this.currentFilter.search = e.target.value;
        this.loadQueues();
      });
    }

    const selStatus = document.getElementById("admin-filter-status");
    if (selStatus) {
      selStatus.addEventListener("change", (e) => {
        this.currentFilter.status = e.target.value;
        this.loadQueues();
      });
    }

    const selApproval = document.getElementById("admin-filter-approval");
    if (selApproval) {
      selApproval.addEventListener("change", (e) => {
        this.currentFilter.approval_status = e.target.value;
        this.loadQueues();
      });
    }

    const selZone = document.getElementById("admin-filter-borough");
    if (selZone) {
      selZone.addEventListener("change", (e) => {
        this.currentFilter.borough = e.target.value;
        this.loadQueues();
      });
    }

    const selCategory = document.getElementById("admin-filter-category");
    if (selCategory) {
      selCategory.addEventListener("change", (e) => {
        this.currentFilter.category = e.target.value;
        this.loadQueues();
      });
    }

    const selPriority = document.getElementById("admin-filter-priority");
    if (selPriority) {
      selPriority.addEventListener("change", (e) => {
        this.currentFilter.priority = e.target.value;
        this.loadQueues();
      });
    }

    // Toggle Aging Checkbox
    const chkAging = document.getElementById("admin-filter-aging");
    if (chkAging) {
      chkAging.addEventListener("change", (e) => {
        this.currentFilter.is_aging = e.target.checked;
        this.loadQueues();
      });
    }

    // View Switcher: Kanban vs Table
    const btnKanban = document.getElementById("btn-view-kanban");
    const btnTable = document.getElementById("btn-view-table");
    if (btnKanban && btnTable) {
      btnKanban.addEventListener("click", () => {
        btnKanban.classList.add("bg-white", "shadow-sm", "text-blue-700");
        btnKanban.classList.remove("text-slate-600");
        btnTable.classList.remove("bg-white", "shadow-sm", "text-blue-700");
        btnTable.classList.add("text-slate-600");
        document.getElementById("kanban-container").classList.remove("hidden");
        document.getElementById("table-container").classList.add("hidden");
      });

      btnTable.addEventListener("click", () => {
        btnTable.classList.add("bg-white", "shadow-sm", "text-blue-700");
        btnTable.classList.remove("text-slate-600");
        btnKanban.classList.remove("bg-white", "shadow-sm", "text-blue-700");
        btnKanban.classList.add("text-slate-600");
        document.getElementById("table-container").classList.remove("hidden");
        document.getElementById("kanban-container").classList.add("hidden");
      });
    }

    // Modal Status Save Button
    const btnSaveStatus = document.getElementById("btn-save-status");
    if (btnSaveStatus) {
      btnSaveStatus.addEventListener("click", () => this.executeStatusUpdate());
    }

    // Modal Assign Save Button
    const btnSaveAssign = document.getElementById("btn-save-assign");
    if (btnSaveAssign) {
      btnSaveAssign.addEventListener("click", () => this.executeAssignment());
    }

    // Refresh Queues Button
    const btnRefresh = document.getElementById("btn-refresh-queues");
    if (btnRefresh) {
      btnRefresh.addEventListener("click", () => this.loadQueues());
    }
  },

  async loadQueues() {
    if (window.Auth && !window.Auth.isAdmin()) {
      const kanban = document.getElementById("kanban-container");
      if (kanban) {
        kanban.innerHTML = `
          <div class="col-span-full p-16 text-center bg-slate-50 rounded-2xl border border-slate-200">
            <span class="text-4xl block mb-2">🔒</span>
            <h3 class="text-base font-bold text-slate-900 mb-1">Municipal Administrator Sign-In Required</h3>
            <p class="text-xs text-slate-500 max-w-md mx-auto mb-4">The Operations Queue and Ticket Approval tools are restricted strictly to authorized municipal officials.</p>
            <button onclick="window.Auth.openAuthModal('login')" class="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-xs shadow-md transition">
              Sign In with Administrator Credentials
            </button>
          </div>
        `;
      }
      return;
    }
    const params = { ...this.currentFilter };
    try {
      this.complaints = await Api.getComplaints(params);
      this.renderKanban(this.complaints);
      this.renderTable(this.complaints);
    } catch (err) {
      console.error("[Admin] Error loading queues:", err);
    }
  },

  renderKanban(items) {
    const cols = {
      NEW: document.getElementById("kanban-col-new"),
      ASSIGNED: document.getElementById("kanban-col-assigned"),
      IN_PROGRESS: document.getElementById("kanban-col-inprogress"),
      RESOLVED: document.getElementById("kanban-col-resolved"),
    };

    const countBadges = {
      NEW: document.getElementById("badge-count-new"),
      ASSIGNED: document.getElementById("badge-count-assigned"),
      IN_PROGRESS: document.getElementById("badge-count-inprogress"),
      RESOLVED: document.getElementById("badge-count-resolved"),
    };

    Object.values(cols).forEach((col) => {
      if (col) col.innerHTML = "";
    });

    const counts = { NEW: 0, ASSIGNED: 0, IN_PROGRESS: 0, RESOLVED: 0 };

    items.forEach((item) => {
      const statusKey = item.status || "NEW";
      counts[statusKey] = (counts[statusKey] || 0) + 1;

      const colEl = cols[statusKey];
      if (!colEl) return;

      const card = document.createElement("div");
      card.className = "bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition mb-3 group";

      const approvalBadge = this.getApprovalBadgeHtml(item.approval_status);

      card.innerHTML = `
        <div class="flex items-start justify-between gap-2 mb-2">
          <span class="text-[10px] font-mono font-bold text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">${item.id}</span>
          <div class="flex items-center gap-1.5 flex-wrap justify-end">
            ${approvalBadge}
            <span class="cursor-pointer px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider badge-${item.priority.toLowerCase()} flex items-center gap-1"
              onclick="window.inspectPriority('${item.id}')" title="Click to view rule-based priority formula breakdown">
              ${item.priority} &bull; ${item.priority_score}
            </span>
          </div>
        </div>

        <h4 class="text-xs font-semibold text-slate-900 line-clamp-2 mb-1.5 group-hover:text-blue-600 transition">
          ${item.title}
        </h4>

        <div class="text-[11px] text-slate-500 mb-2 flex items-center gap-1">
          <span>📍 ${item.location_address || item.borough}</span>
        </div>

        <div class="flex items-center justify-between text-[11px] pt-2 border-t border-slate-100">
          <span class="${item.is_sla_breached ? 'badge-breached px-1.5 py-0.5 rounded font-bold' : 'text-slate-500'}">
            ⏱️ ${item.age_hours}h open ${item.is_sla_breached ? '(OVERDUE)' : ''}
          </span>
          <span class="text-slate-400 font-medium">${item.similar_complaint_count || 0} duplicates</span>
        </div>

        <div class="mt-3 flex items-center justify-between gap-2 pt-2 border-t border-slate-100">
          <button class="text-xs font-medium text-blue-600 hover:text-blue-800" onclick="window.viewTicketDetail('${item.id}')">
            Details
          </button>
          <div class="flex items-center gap-1">
            ${item.approval_status === 'PENDING_REVIEW' ? `
              <button class="bg-emerald-600 hover:bg-emerald-700 text-white px-2 py-1 rounded text-[10px] font-bold transition"
                onclick="window.approveTicket('${item.id}', 'APPROVED')" title="Approve and validate complaint">
                ✓ Approve
              </button>
              <button class="bg-rose-50 hover:bg-rose-100 text-rose-700 px-2 py-1 rounded text-[10px] font-bold border border-rose-200 transition"
                onclick="window.approveTicket('${item.id}', 'REJECTED')" title="Reject or close request">
                ✗ Reject
              </button>
            ` : ''}

            ${item.status === 'NEW' ? `
              <button class="bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-[11px] font-medium"
                onclick="window.openAssignModal('${item.id}')">
                Dispatch
              </button>
            ` : `
              <button class="bg-slate-100 hover:bg-slate-200 text-slate-700 px-2 py-1 rounded text-[11px] font-medium"
                onclick="window.openStatusModal('${item.id}', '${item.status}')">
                Update Status
              </button>
            `}
          </div>
        </div>
      `;

      colEl.appendChild(card);
    });

    // Update count labels
    Object.entries(counts).forEach(([statusKey, count]) => {
      if (countBadges[statusKey]) {
        countBadges[statusKey].textContent = count;
      }
    });
  },

  renderTable(items) {
    const tbody = document.getElementById("admin-table-tbody");
    if (!tbody) return;

    if (items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" class="text-center py-6 text-xs text-slate-400">No complaints matching filter criteria.</td></tr>`;
      return;
    }

    tbody.innerHTML = items.map((item) => {
      const approvalBadge = this.getApprovalBadgeHtml(item.approval_status);

      return `
        <tr class="hover:bg-slate-50 border-b border-slate-100 text-xs transition">
          <td class="py-3 px-3 font-mono font-medium text-blue-600 cursor-pointer" onclick="window.viewTicketDetail('${item.id}')">${item.id}</td>
          <td class="py-3 px-3 font-medium text-slate-900 max-w-[200px] truncate" title="${item.title}">${item.title}</td>
          <td class="py-3 px-3 text-slate-600">${item.category}</td>
          <td class="py-3 px-3 text-slate-600">${item.borough}</td>
          <td class="py-3 px-3">
            ${approvalBadge}
          </td>
          <td class="py-3 px-3">
            <span class="cursor-pointer px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider badge-${item.priority.toLowerCase()}"
              onclick="window.inspectPriority('${item.id}')">
              ${item.priority} (${item.priority_score})
            </span>
          </td>
          <td class="py-3 px-3">
            <span class="px-2 py-0.5 rounded text-[10px] font-semibold ${item.status === 'RESOLVED' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-700'}">
              ${item.status}
            </span>
          </td>
          <td class="py-3 px-3 ${item.is_sla_breached ? 'text-rose-600 font-bold' : 'text-slate-500'}">
            ${item.age_hours}h ${item.is_sla_breached ? '⚠️ BREACHED' : ''}
          </td>
          <td class="py-3 px-3 text-right">
            ${item.approval_status === 'PENDING_REVIEW' ? `
              <button class="text-emerald-700 hover:text-emerald-900 font-bold mr-2 text-[11px]" onclick="window.approveTicket('${item.id}', 'APPROVED')">Approve</button>
              <button class="text-rose-600 hover:text-rose-800 font-medium mr-2 text-[11px]" onclick="window.approveTicket('${item.id}', 'REJECTED')">Reject</button>
            ` : ''}
            <button class="text-blue-600 hover:text-blue-800 font-medium mr-2" onclick="window.openStatusModal('${item.id}', '${item.status}')">Status</button>
            <button class="text-slate-600 hover:text-slate-800" onclick="window.viewTicketDetail('${item.id}')">View</button>
          </td>
        </tr>
      `;
    }).join("");
  },

  getApprovalBadgeHtml(status) {
    if (status === "APPROVED") {
      return `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-300">APPROVED</span>`;
    }
    if (status === "REJECTED") {
      return `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-300">REJECTED</span>`;
    }
    return `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">PENDING REVIEW</span>`;
  },

  approveTicket(id, approvalStatus = "APPROVED") {
    if (window.ApprovalsManager && typeof window.ApprovalsManager.openDecisionModal === "function") {
      window.ApprovalsManager.openDecisionModal(id, approvalStatus);
    } else {
      console.warn("ApprovalsManager not yet initialized");
    }
  },

  async inspectPriority(id) {
    try {
      const complaint = await Api.getComplaint(id);
      const b = complaint.score_breakdown || {};

      const modal = document.getElementById("priority-breakdown-modal") || document.getElementById("priority-inspector-modal");
      if (!modal) return;

      const container = document.getElementById("priority-breakdown-content");
      if (container) {
        container.innerHTML = `
          <div class="p-3 bg-slate-50 rounded-xl border border-slate-200">
            <div class="flex justify-between items-center mb-1">
              <span class="font-mono font-bold text-blue-700">${complaint.id}</span>
              <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-blue-100 text-blue-800">${b.priority_tier || complaint.priority}</span>
            </div>
            <p class="font-bold text-slate-800">${complaint.title}</p>
          </div>

          <div class="grid grid-cols-2 gap-2 text-xs">
            <div class="p-2.5 rounded-lg border border-slate-200 bg-white">
              <span class="text-slate-500 block text-[11px]">Base Category Severity</span>
              <span class="font-bold text-slate-800 text-sm">${b.base_severity || 0} pts</span>
              <span class="text-[10px] text-slate-400 block">${complaint.category}</span>
            </div>
            <div class="p-2.5 rounded-lg border border-slate-200 bg-white">
              <span class="text-slate-500 block text-[11px]">Aging Penalty</span>
              <span class="font-bold text-slate-800 text-sm">+${b.age_penalty || 0} pts</span>
              <span class="text-[10px] text-slate-400 block">${b.age_hours || 0} hours open</span>
            </div>
            <div class="p-2.5 rounded-lg border border-slate-200 bg-white">
              <span class="text-slate-500 block text-[11px]">Similar / Duplicate Bonus</span>
              <span class="font-bold text-slate-800 text-sm">+${b.duplicate_bonus || 0} pts</span>
              <span class="text-[10px] text-slate-400 block">${b.duplicate_count || 0} duplicate reports</span>
            </div>
            <div class="p-2.5 rounded-lg border border-slate-200 bg-white">
              <span class="text-slate-500 block text-[11px]">Location Risk & SLA</span>
              <span class="font-bold text-slate-800 text-sm">+${(b.location_risk_bonus || 0) + (b.sla_breached ? (b.sla_penalty || 0) : 0)} pts</span>
              <span class="text-[10px] text-slate-400 block">${b.sla_breached ? 'SLA OVERDUE (+30 pts)' : 'Within SLA Target'}</span>
            </div>
          </div>

          <div class="p-3 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-900 flex justify-between items-center">
            <div>
              <span class="text-[11px] font-bold uppercase text-indigo-700 block">Total Calculated Score</span>
              <span class="text-xs text-indigo-600">${b.explanation || 'Rule-based weighted formula'}</span>
            </div>
            <span class="text-2xl font-black text-indigo-800">${b.total_score || complaint.priority_score}</span>
          </div>
        `;
      }

      modal.classList.remove("hidden");
    } catch (err) {
      Toast.error("Error inspecting priority: " + err.message);
    }
  },

  openAssignModal(id) {
    this.activeTicketId = id;
    const modal = document.getElementById("admin-assign-modal") || document.getElementById("assign-ticket-modal");
    if (!modal) return;
    const label = document.getElementById("assign-ticket-id-label") || document.getElementById("modal-assign-ticket-id");
    if (label) label.textContent = id;
    modal.classList.remove("hidden");
  },

  async executeAssignment() {
    if (!this.activeTicketId) return;
    const dept = document.getElementById("modal-assign-dept")?.value || document.getElementById("select-assign-dept")?.value;
    const officer = document.getElementById("modal-assign-officer")?.value || document.getElementById("input-assign-officer")?.value || "";
    const notes = document.getElementById("modal-assign-notes")?.value || document.getElementById("input-assign-notes")?.value || "";

    const user = window.Auth ? window.Auth.getCurrentUser() : { name: "Dispatch Administrator" };

    try {
      await Api.assignComplaint(this.activeTicketId, dept, officer, notes, user.name);
      const modal = document.getElementById("admin-assign-modal") || document.getElementById("assign-ticket-modal");
      if (modal) modal.classList.add("hidden");
      Toast.success(`Complaint ${this.activeTicketId} successfully assigned to ${dept}.`);
      this.loadQueues();
      if (window.ApprovalsManager) window.ApprovalsManager.loadApprovals();
    } catch (err) {
      Toast.error("Failed to assign ticket: " + err.message);
    }
  },

  openStatusModal(id, currentStatus) {
    this.activeTicketId = id;
    const modal = document.getElementById("admin-status-modal") || document.getElementById("update-status-modal");
    if (!modal) return;

    modal.dataset.ticketId = id;
    const label = document.getElementById("status-ticket-id-label") || document.getElementById("modal-status-ticket-id");
    if (label) label.textContent = id;
    const sel = document.getElementById("modal-status-select") || document.getElementById("select-new-status");
    if (sel) sel.value = currentStatus;

    modal.classList.remove("hidden");
  },

  async executeStatusUpdate() {
    const modal = document.getElementById("admin-status-modal") || document.getElementById("update-status-modal");
    const ticketId = this.activeTicketId || modal?.dataset?.ticketId || document.getElementById("status-ticket-id-label")?.textContent?.trim();
    if (!ticketId || ticketId === "--") {
      Toast.error("No active complaint selected to update.");
      return;
    }

    const newStatus = document.getElementById("modal-status-select")?.value || document.getElementById("select-new-status")?.value || "IN_PROGRESS";
    const notes = document.getElementById("modal-status-notes")?.value || document.getElementById("input-status-notes")?.value || "";
    const resNotes = document.getElementById("modal-resolution-notes")?.value || document.getElementById("input-resolution-notes")?.value || notes;

    const user = window.Auth ? window.Auth.getCurrentUser() : { name: "Operations Staff" };
    const btn = document.getElementById("btn-save-status");
    const origText = btn ? btn.innerHTML : "";

    try {
      if (btn) btn.innerHTML = `<span>⏳ Updating...</span>`;
      await Api.updateComplaintStatus(ticketId, newStatus, notes, user.name, resNotes);
      if (modal) modal.classList.add("hidden");
      Toast.success(`Complaint ${ticketId} transitioned to ${newStatus}.`);
      this.loadQueues();
      if (window.ApprovalsManager) window.ApprovalsManager.loadApprovals();
    } catch (err) {
      Toast.error("Failed to update status: " + err.message);
    } finally {
      if (btn) btn.innerHTML = origText;
    }
  }

};

window.AdminPortal = AdminPortal;
window.approveTicket = (id, status) => AdminPortal.approveTicket(id, status);
window.openAssignModal = (id) => AdminPortal.openAssignModal(id);
window.openStatusModal = (id, currentStatus) => AdminPortal.openStatusModal(id, currentStatus);
window.inspectPriority = (id) => AdminPortal.inspectPriority(id);
window.viewTicketDetail = (id) => {
  if (window.CitizenPortal && typeof window.CitizenPortal.trackComplaint === "function") {
    window.CitizenPortal.trackComplaint(id);
  }
};
