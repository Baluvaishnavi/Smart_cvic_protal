/**
 * Municipal Approvals Management Module:
 * Review, verify, dispatch, and bulk-approve citizen-submitted service requests.
 */

import { Api } from "./api.js";
import { Toast } from "./toast.js";

export const ApprovalsManager = {
  activeStatusTab: "PENDING_REVIEW",
  complaints: [],
  selectedIds: new Set(),
  activeDecisionTicketId: null,

  init() {
    this.bindEvents();
  },

  bindEvents() {
    // Status Filter Tabs in Approvals View
    document.querySelectorAll(".approval-status-tab").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".approval-status-tab").forEach((b) => {
          b.classList.remove("bg-blue-600", "text-white", "shadow-sm");
          b.classList.add("bg-white", "text-slate-600");
        });
        btn.classList.add("bg-blue-600", "text-white", "shadow-sm");
        btn.classList.remove("bg-white", "text-slate-600");
        this.activeStatusTab = btn.dataset.status;
        this.selectedIds.clear();
        this.updateBatchButton();
        this.renderQueue();
      });
    });

    // Search and Filters
    const searchInput = document.getElementById("approval-search-input");
    if (searchInput) {
      searchInput.addEventListener("input", () => this.renderQueue());
    }

    const zoneFilter = document.getElementById("approval-filter-zone");
    if (zoneFilter) {
      zoneFilter.addEventListener("change", () => this.renderQueue());
    }

    const catFilter = document.getElementById("approval-filter-category");
    if (catFilter) {
      catFilter.addEventListener("change", () => this.renderQueue());
    }

    // Refresh Button
    const btnRefresh = document.getElementById("btn-refresh-approvals");
    if (btnRefresh) {
      btnRefresh.addEventListener("click", () => {
        this.loadApprovals();
        Toast.info("Approvals queue refreshed.");
      });
    }

    // Batch Select All
    const chkSelectAll = document.getElementById("approval-select-all");
    if (chkSelectAll) {
      chkSelectAll.addEventListener("change", (e) => {
        const isChecked = e.target.checked;
        const visibleIds = this.getFilteredComplaints().map((c) => c.id);
        if (isChecked) {
          visibleIds.forEach((id) => this.selectedIds.add(id));
        } else {
          this.selectedIds.clear();
        }
        document.querySelectorAll(".approval-item-checkbox").forEach((cb) => {
          cb.checked = isChecked;
        });
        this.updateBatchButton();
      });
    }

    // Batch Approve Button
    const btnBatchApprove = document.getElementById("btn-batch-approve");
    if (btnBatchApprove) {
      btnBatchApprove.addEventListener("click", () => this.handleBatchApprove());
    }

    // Preset Remarks Pills in Approval Modal
    document.querySelectorAll(".preset-remark-pill").forEach((pill) => {
      pill.addEventListener("click", () => {
        const textarea = document.getElementById("approval-decision-notes");
        if (textarea) {
          textarea.value = pill.dataset.remark || pill.textContent.trim();
        }
      });
    });

    // Approval Decision Radio Toggle
    const radioApprove = document.getElementById("radio-action-approve");
    const radioReject = document.getElementById("radio-action-reject");
    if (radioApprove && radioReject) {
      radioApprove.addEventListener("change", () => this.syncModalActionState("APPROVED"));
      radioReject.addEventListener("change", () => this.syncModalActionState("REJECTED"));
    }

    // Approval Decision Modal Form Submission
    const decisionForm = document.getElementById("approval-decision-form");
    if (decisionForm) {
      decisionForm.addEventListener("submit", (e) => {
        e.preventDefault();
        this.submitDecisionModal();
      });
    }
  },

  syncModalActionState(action) {
    const deptContainer = document.getElementById("approval-dept-container");
    const submitBtn = document.getElementById("btn-confirm-approval-decision");
    const pillsApprove = document.getElementById("preset-pills-approve");
    const pillsReject = document.getElementById("preset-pills-reject");
    const notesInput = document.getElementById("approval-decision-notes");

    if (action === "APPROVED") {
      if (deptContainer) deptContainer.classList.remove("hidden");
      if (pillsApprove) pillsApprove.classList.remove("hidden");
      if (pillsReject) pillsReject.classList.add("hidden");
      if (submitBtn) {
        submitBtn.className = "px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs transition flex items-center gap-1.5 shadow-sm";
        submitBtn.innerHTML = `<span>✓</span> <span>Approve & Dispatch</span>`;
      }
      if (notesInput && !notesInput.value) {
        notesInput.value = "Civic complaint verified. Dispatched to field crew.";
      }
    } else {
      if (deptContainer) deptContainer.classList.add("hidden");
      if (pillsApprove) pillsApprove.classList.add("hidden");
      if (pillsReject) pillsReject.classList.remove("hidden");
      if (submitBtn) {
        submitBtn.className = "px-4 py-2.5 bg-rose-600 hover:bg-rose-700 text-white font-bold rounded-xl text-xs transition flex items-center gap-1.5 shadow-sm";
        submitBtn.innerHTML = `<span>✕</span> <span>Reject & Close</span>`;
      }
      if (notesInput && (!notesInput.value || notesInput.value.includes("verified"))) {
        notesInput.value = "Duplicate of existing report or outside municipal jurisdiction.";
      }
    }
  },

  async loadApprovals() {
    try {
      const data = await Api.getComplaints({ limit: 300 });
      this.complaints = data || [];
      this.updateKPIs();
      this.renderQueue();
    } catch (e) {
      console.error("[Approvals] Failed to load complaints:", e);
      Toast.error("Failed to load approvals queue: " + e.message);
    }
  },

  updateKPIs() {
    const pending = this.complaints.filter((c) => c.approval_status === "PENDING_REVIEW").length;
    const approved = this.complaints.filter((c) => c.approval_status === "APPROVED").length;
    const rejected = this.complaints.filter((c) => c.approval_status === "REJECTED").length;

    const elPending = document.getElementById("kpi-approval-pending");
    const elApproved = document.getElementById("kpi-approval-approved");
    const elRejected = document.getElementById("kpi-approval-rejected");
    const elBadge = document.getElementById("nav-badge-approvals");

    if (elPending) elPending.textContent = pending;
    if (elApproved) elApproved.textContent = approved;
    if (elRejected) elRejected.textContent = rejected;

    if (elBadge) {
      if (pending > 0) {
        elBadge.textContent = pending;
        elBadge.classList.remove("hidden");
      } else {
        elBadge.classList.add("hidden");
      }
    }

    const tabPendingCount = document.getElementById("tab-count-pending");
    if (tabPendingCount) tabPendingCount.textContent = pending;
  },

  getFilteredComplaints() {
    let list = [...this.complaints];

    // Status Tab Filter
    if (this.activeStatusTab !== "ALL") {
      list = list.filter((c) => c.approval_status === this.activeStatusTab);
    }

    // Search
    const searchVal = document.getElementById("approval-search-input")?.value.trim().toLowerCase();
    if (searchVal) {
      list = list.filter(
        (c) =>
          c.id.toLowerCase().includes(searchVal) ||
          c.title.toLowerCase().includes(searchVal) ||
          (c.category && c.category.toLowerCase().includes(searchVal)) ||
          (c.location_address && c.location_address.toLowerCase().includes(searchVal)) ||
          (c.citizen_name && c.citizen_name.toLowerCase().includes(searchVal))
      );
    }

    // Zone
    const zoneVal = document.getElementById("approval-filter-zone")?.value;
    if (zoneVal && zoneVal !== "ALL") {
      list = list.filter((c) => (c.borough || c.zone) === zoneVal);
    }

    // Category
    const catVal = document.getElementById("approval-filter-category")?.value;
    if (catVal && catVal !== "ALL") {
      if (catVal === "OTHER") {
        const standardCats = ["Streetlight", "Pothole", "Water Supply", "Garbage & Sanitation", "Traffic Signal", "Broken Sidewalk", "Trees & Parks", "Noise & Disturbance"];
        list = list.filter((c) => !standardCats.includes(c.category));
      } else {
        list = list.filter((c) => c.category === catVal);
      }
    }

    return list;
  },

  renderQueue() {
    const container = document.getElementById("approval-cards-container");
    if (!container) return;

    const items = this.getFilteredComplaints();

    if (items.length === 0) {
      container.innerHTML = `
        <div class="p-12 text-center bg-white rounded-2xl border border-slate-200 shadow-sm col-span-full">
          <div class="w-12 h-12 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center text-xl mx-auto mb-3">✓</div>
          <h4 class="text-sm font-bold text-slate-800">No requests in this view</h4>
          <p class="text-xs text-slate-500 mt-1 max-w-sm mx-auto">All citizen complaints under "${this.activeStatusTab}" have been handled or no items match your search filters.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = items
      .map((item) => {
        const isChecked = this.selectedIds.has(item.id);
        const isPending = item.approval_status === "PENDING_REVIEW";
        const isApproved = item.approval_status === "APPROVED";
        const isRejected = item.approval_status === "REJECTED";

        let statusBadge = `<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">🟡 PENDING REVIEW</span>`;
        if (isApproved) {
          statusBadge = `<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">🟢 APPROVED & DISPATCHED</span>`;
        } else if (isRejected) {
          statusBadge = `<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-300">🔴 REJECTED / CLOSED</span>`;
        }

        let priorityColor = "bg-slate-100 text-slate-700 border-slate-200";
        if (item.priority === "CRITICAL") priorityColor = "bg-red-100 text-red-800 border-red-300";
        else if (item.priority === "HIGH") priorityColor = "bg-amber-100 text-amber-800 border-amber-300";
        else if (item.priority === "MEDIUM") priorityColor = "bg-blue-100 text-blue-800 border-blue-300";

        return `
          <div class="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm hover:border-blue-300 transition flex flex-col justify-between gap-4">
            
            <!-- Card Header -->
            <div>
              <div class="flex items-start justify-between gap-2 mb-2">
                <div class="flex items-center gap-2">
                  ${
                    isPending
                      ? `<input type="checkbox" class="approval-item-checkbox rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-4 w-4" data-id="${item.id}" ${isChecked ? "checked" : ""} />`
                      : ""
                  }
                  <span class="font-mono font-bold text-xs text-blue-700">${item.id}</span>
                </div>
                <div class="flex items-center gap-1.5">
                  <span class="px-2 py-0.5 rounded-md text-[10px] font-bold border ${priorityColor}">
                    ${item.priority || "NORMAL"} (${item.priority_score || 0})
                  </span>
                  ${statusBadge}
                </div>
              </div>

              <!-- Issue Title -->
              <h4 class="font-bold text-slate-900 text-sm leading-snug mb-1.5">${item.title}</h4>

              <!-- Location & Category -->
              <div class="flex flex-wrap items-center gap-2 text-xs text-slate-500 mb-3">
                <span class="inline-flex items-center gap-1 font-medium bg-slate-100 px-2 py-0.5 rounded-md text-slate-700">
                  <span>📍</span> <span>${item.borough || item.zone || "Central Ward"}</span>
                </span>
                <span class="text-slate-400">&bull;</span>
                <span class="text-slate-600 truncate max-w-[200px]" title="${item.location_address}">${item.location_address || "Unspecified"}</span>
                <span class="text-slate-400">&bull;</span>
                <span class="font-semibold text-slate-700">${item.category}</span>
              </div>

              <!-- Citizen Details Box -->
              <div class="p-2.5 rounded-xl bg-slate-50 border border-slate-200 text-[11px] space-y-1 mb-3">
                <div class="flex justify-between">
                  <span class="text-slate-500">Citizen:</span>
                  <span class="font-bold text-slate-800">${item.citizen_name || "Civic Resident"}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-slate-500">Email:</span>
                  <span class="font-medium text-slate-700 font-mono">${item.citizen_email || "--"}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-slate-500">Assigned Dept:</span>
                  <span class="font-semibold text-blue-800">${item.assigned_department || "Municipal Operations"}</span>
                </div>
                ${
                  item.admin_review_notes
                    ? `<div class="pt-1 mt-1 border-t border-slate-200 text-slate-600 italic">
                        <strong>Remarks:</strong> ${item.admin_review_notes} (${item.reviewed_by || "Admin"})
                       </div>`
                    : ""
                }
              </div>
            </div>

            <!-- Card Actions -->
            <div class="pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
              <span class="text-[10px] text-slate-400">
                ${new Date(item.created_at).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
              </span>

              <div class="flex items-center gap-1.5">
                ${
                  isPending
                    ? `
                    <button class="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs transition shadow-sm flex items-center gap-1"
                      onclick="window.ApprovalsManager.openDecisionModal('${item.id}', 'APPROVED')">
                      <span>✓</span> <span>Approve</span>
                    </button>
                    <button class="px-2.5 py-1.5 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-bold text-xs transition"
                      onclick="window.ApprovalsManager.openDecisionModal('${item.id}', 'REJECTED')">
                      <span>✕</span>
                    </button>
                  `
                    : `
                    <button class="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition"
                      onclick="window.ApprovalsManager.openDecisionModal('${item.id}', '${item.approval_status}')">
                      Update Decision
                    </button>
                  `
                }
              </div>
            </div>

          </div>
        `;
      })
      .join("");

    // Bind item checkboxes
    container.querySelectorAll(".approval-item-checkbox").forEach((cb) => {
      cb.addEventListener("change", (e) => {
        const id = e.target.dataset.id;
        if (e.target.checked) {
          this.selectedIds.add(id);
        } else {
          this.selectedIds.delete(id);
        }
        this.updateBatchButton();
      });
    });
  },

  updateBatchButton() {
    const btn = document.getElementById("btn-batch-approve");
    const countSpan = document.getElementById("batch-selected-count");
    if (btn && countSpan) {
      countSpan.textContent = this.selectedIds.size;
      if (this.selectedIds.size > 0) {
        btn.classList.remove("opacity-50", "pointer-events-none");
      } else {
        btn.classList.add("opacity-50", "pointer-events-none");
      }
    }
  },

  async handleBatchApprove() {
    if (this.selectedIds.size === 0) return;

    const ids = Array.from(this.selectedIds);
    const user = window.Auth ? window.Auth.getCurrentUser() : null;
    const reviewer = user ? user.name : "Municipal Operations Administrator";

    try {
      await Api.batchUpdateApproval(
        ids,
        "APPROVED",
        "Approved in bulk municipal operations review.",
        null,
        reviewer
      );
      Toast.success(`Successfully approved and dispatched ${ids.length} service requests.`);
      this.selectedIds.clear();
      this.updateBatchButton();
      await this.loadApprovals();
      if (window.AdminPortal) window.AdminPortal.loadQueues();
    } catch (err) {
      Toast.error("Batch approval failed: " + err.message);
    }
  },

  openDecisionModal(complaintId, actionType = "APPROVED") {
    const complaint = this.complaints.find((c) => c.id === complaintId);
    if (!complaint) return;

    this.activeDecisionTicketId = complaintId;

    const modal = document.getElementById("approval-decision-modal");
    if (!modal) return;

    document.getElementById("modal-decision-ticket-id").textContent = complaint.id;
    document.getElementById("modal-decision-title").textContent = complaint.title;
    document.getElementById("modal-decision-cat").textContent = complaint.category;
    document.getElementById("modal-decision-loc").textContent = `${complaint.location_address || ""} (${complaint.borough || complaint.zone || "Central Ward"})`;
    document.getElementById("modal-decision-reporter").textContent = `${complaint.citizen_name || "Civic Resident"} &bull; ${complaint.citizen_email || ""}`;

    const deptSelect = document.getElementById("approval-decision-dept");
    if (deptSelect && complaint.assigned_department) {
      deptSelect.value = complaint.assigned_department;
    }

    // Set radio buttons
    const radioApprove = document.getElementById("radio-action-approve");
    const radioReject = document.getElementById("radio-action-reject");
    if (actionType === "REJECTED") {
      if (radioReject) radioReject.checked = true;
      this.syncModalActionState("REJECTED");
    } else {
      if (radioApprove) radioApprove.checked = true;
      this.syncModalActionState("APPROVED");
    }

    modal.classList.remove("hidden");
  },

  closeDecisionModal() {
    const modal = document.getElementById("approval-decision-modal");
    if (modal) modal.classList.add("hidden");
    this.activeDecisionTicketId = null;
  },

  async submitDecisionModal() {
    if (!this.activeDecisionTicketId) return;

    const id = this.activeDecisionTicketId;
    const isApprove = document.getElementById("radio-action-approve")?.checked;
    const approvalStatus = isApprove ? "APPROVED" : "REJECTED";
    const notes = document.getElementById("approval-decision-notes")?.value.trim() || "";
    const dept = isApprove ? document.getElementById("approval-decision-dept")?.value : null;

    const user = window.Auth ? window.Auth.getCurrentUser() : null;
    const reviewer = user ? user.name : "Municipal Operations Administrator";

    try {
      await Api.updateComplaintApproval(id, approvalStatus, notes, dept, reviewer);
      this.closeDecisionModal();
      Toast.success(`Complaint ${id} successfully marked as ${approvalStatus}.`);
      await this.loadApprovals();
      if (window.AdminPortal) window.AdminPortal.loadQueues();
    } catch (err) {
      Toast.error("Failed to update approval: " + err.message);
    }
  },
};

window.ApprovalsManager = ApprovalsManager;
