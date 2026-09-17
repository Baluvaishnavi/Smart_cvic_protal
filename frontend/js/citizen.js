/**
 * Citizen Portal functionality:
 * Issue submission, personalized 'My Complaints' tracking,
 * official municipal approval status indicators, and tracking drawer.
 */

import { Api } from "./api.js";
import { Toast } from "./toast.js";

export const CitizenPortal = {
  selectedCategory: "Streetlight",
  myComplaintsData: [],

  init() {
    this.bindEvents();
    this.loadNearbyIssues();
    this.loadMyComplaints();
  },

  bindEvents() {
    // Quick Category chips
    document.querySelectorAll(".cat-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        document.querySelectorAll(".cat-chip").forEach((c) => c.classList.remove("ring-2", "ring-blue-600", "bg-blue-50"));
        chip.classList.add("ring-2", "ring-blue-600", "bg-blue-50");
        this.selectedCategory = chip.dataset.category;
        const sel = document.getElementById("select-category");
        const customBox = document.getElementById("custom-category-box");
        const customInput = document.getElementById("input-custom-category");

        if (this.selectedCategory === "OTHER") {
          if (sel) sel.value = "OTHER";
          if (customBox) customBox.classList.remove("hidden");
          if (customInput) customInput.focus();
        } else {
          if (sel) sel.value = this.selectedCategory;
          if (customBox) customBox.classList.add("hidden");
        }
        this.loadNearbyIssues();
      });
    });

    // Select category dropdown change
    const selCat = document.getElementById("select-category");
    if (selCat) {
      selCat.addEventListener("change", (e) => {
        const val = e.target.value;
        this.selectedCategory = val;
        const customBox = document.getElementById("custom-category-box");
        const customInput = document.getElementById("input-custom-category");

        document.querySelectorAll(".cat-chip").forEach((c) => {
          if (c.dataset.category === val) {
            c.classList.add("ring-2", "ring-blue-600", "bg-blue-50");
          } else {
            c.classList.remove("ring-2", "ring-blue-600", "bg-blue-50");
          }
        });

        if (val === "OTHER") {
          if (customBox) customBox.classList.remove("hidden");
          if (customInput) customInput.focus();
        } else {
          if (customBox) customBox.classList.add("hidden");
        }
        this.loadNearbyIssues();
      });
    }

    // Custom Category Manual Input typing
    const customInput = document.getElementById("input-custom-category");
    if (customInput) {
      customInput.addEventListener("input", () => {
        this.selectedCategory = "OTHER";
        const sel = document.getElementById("select-category");
        if (sel) sel.value = "OTHER";
        document.querySelectorAll(".cat-chip").forEach((c) => {
          if (c.dataset.category === "OTHER") {
            c.classList.add("ring-2", "ring-blue-600", "bg-blue-50");
          } else {
            c.classList.remove("ring-2", "ring-blue-600", "bg-blue-50");
          }
        });
      });
    }

    // Smart Assistive Auto-Fill Button
    const btnAi = document.getElementById("btn-ai-autofill");
    if (btnAi) {
      btnAi.addEventListener("click", () => this.handleAiAnalysis());
    }

    // Submit Form
    const form = document.getElementById("complaint-form");
    if (form) {
      form.addEventListener("submit", (e) => {
        e.preventDefault();
        this.submitComplaint();
      });
    }

    // Track Button
    const btnTrack = document.getElementById("btn-track");
    if (btnTrack) {
      btnTrack.addEventListener("click", () => {
        const idInput = document.getElementById("track-id-input");
        if (idInput && idInput.value.trim()) {
          this.trackComplaint(idInput.value.trim());
        }
      });
    }

    // Add Comment on Tracked Issue
    const btnComment = document.getElementById("btn-add-comment");
    if (btnComment) {
      btnComment.addEventListener("click", () => this.submitComment());
    }

    // Filter My Complaints
    const myFilterStatus = document.getElementById("my-filter-status");
    if (myFilterStatus) {
      myFilterStatus.addEventListener("change", () => this.renderMyComplaintsList());
    }

    const mySearchInput = document.getElementById("my-search-input");
    if (mySearchInput) {
      mySearchInput.addEventListener("input", () => this.renderMyComplaintsList());
    }

    // Listen for auth change
    window.addEventListener("civic_auth_changed", () => {
      this.loadMyComplaints();
    });
  },

  async handleAiAnalysis() {
    const inputRaw = document.getElementById("input-raw-desc");
    const text = inputRaw ? inputRaw.value.trim() : "";
    if (!text || text.length < 5) {
      Toast.warning("Please enter a description of the civic problem first.");
      return;
    }

    const aiStatus = document.getElementById("ai-status-indicator");
    const aiBanner = document.getElementById("ai-result-banner");
    const aiBtn = document.getElementById("btn-ai-autofill");

    try {
      if (aiBtn) aiBtn.innerHTML = `<span>⏳ Analyzing text...</span>`;
      if (aiStatus) aiStatus.classList.remove("hidden");

      const result = await Api.analyzeWithAI(text);

      // Auto-fill form fields
      const inputTitle = document.getElementById("input-title");
      const selCat = document.getElementById("select-category");
      const inputAddr = document.getElementById("input-address");
      const selUrgency = document.getElementById("select-urgency");

      if (inputTitle) inputTitle.value = result.issue_summary;
      if (selCat) {
        selCat.value = result.category;
        this.selectedCategory = result.category;
        document.querySelectorAll(".cat-chip").forEach((c) => {
          if (c.dataset.category === result.category) {
            c.classList.add("ring-2", "ring-blue-600", "bg-blue-50");
          } else {
            c.classList.remove("ring-2", "ring-blue-600", "bg-blue-50");
          }
        });
      }

      if (inputAddr && result.extracted_location) {
        inputAddr.value = result.extracted_location;
      }
      if (selUrgency) {
        selUrgency.value = result.urgency;
      }

      // Display clean assistive banner
      if (aiBanner) {
        aiBanner.className = "p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs flex items-center justify-between";
        aiBanner.innerHTML = `
          <div class="flex items-center gap-2">
            <span class="w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-xs">✓</span>
            <div>
              <p class="font-semibold text-slate-800">Detected: <span class="text-blue-700 font-bold">${result.category}</span> &bull; Routed to: <span class="text-slate-600 font-medium">${result.suggested_department}</span></p>
              <p class="text-[11px] text-slate-500">${result.issue_summary}</p>
            </div>
          </div>
          <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
            ${Math.round(result.confidence * 100)}% Match
          </span>
        `;
        aiBanner.classList.remove("hidden");
      }

      this.loadNearbyIssues();
    } catch (err) {
      console.error("[Citizen] Analysis error:", err);
    } finally {
      if (aiBtn) aiBtn.innerHTML = `<span>⚡ Smart Category Suggestions</span>`;
      if (aiStatus) aiStatus.classList.add("hidden");
    }
  },

  async submitComplaint() {
    const btn = document.querySelector("#complaint-form button[type='submit']");
    const origText = btn ? btn.innerHTML : "";

    const user = window.Auth ? window.Auth.getCurrentUser() : { email: "citizen@civicportal.gov", name: "Civic Resident" };

    const customCatVal = document.getElementById("input-custom-category")?.value.trim();
    const selCatVal = document.getElementById("select-category")?.value;
    let finalCategory = this.selectedCategory;

    if (selCatVal === "OTHER" || this.selectedCategory === "OTHER" || (customCatVal && !document.getElementById("custom-category-box")?.classList.contains("hidden"))) {
      finalCategory = customCatVal || "General Civic Issue";
    } else if (selCatVal) {
      finalCategory = selCatVal;
    }

    const payload = {
      title: document.getElementById("input-title")?.value.trim() || "",
      description: document.getElementById("input-raw-desc")?.value.trim() || document.getElementById("input-title")?.value.trim() || "",
      raw_input: document.getElementById("input-raw-desc")?.value.trim() || "",
      category: finalCategory,
      location_address: document.getElementById("input-address")?.value.trim() || "Unspecified Location",
      borough: document.getElementById("select-borough")?.value || "Central Ward",
      priority: document.getElementById("select-urgency")?.value || "MEDIUM",
      citizen_email: user.email || "citizen@civicportal.gov",
      citizen_name: user.name || "Civic Resident",
      citizen_phone: document.getElementById("input-citizen-phone")?.value.trim() || null,
      approval_status: "PENDING_REVIEW"
    };

    try {
      if (btn) btn.innerHTML = `<span>⏳ Submitting to Municipal Authority...</span>`;
      const res = await Api.createComplaint(payload);

      // Show Confirmation Modal & Toast
      this.showSubmissionSuccess(res);
      Toast.success(`Service request registered: ${res.id}`);

      // Reset form
      document.getElementById("complaint-form").reset();
      const rawDesc = document.getElementById("input-raw-desc");
      if (rawDesc) rawDesc.value = "";
      const banner = document.getElementById("ai-result-banner");
      if (banner) banner.classList.add("hidden");
      const customBox = document.getElementById("custom-category-box");
      if (customBox) customBox.classList.add("hidden");
      const customInput = document.getElementById("input-custom-category");
      if (customInput) customInput.value = "";
      this.selectedCategory = "Streetlight";
      document.querySelectorAll(".cat-chip").forEach((c) => {
        if (c.dataset.category === "Streetlight") {
          c.classList.add("ring-2", "ring-blue-600", "bg-blue-50");
        } else {
          c.classList.remove("ring-2", "ring-blue-600", "bg-blue-50");
        }
      });

      // Refresh My Complaints
      this.loadMyComplaints();
    } catch (err) {
      Toast.error("Submission error: " + err.message);
    } finally {
      if (btn) btn.innerHTML = origText;
    }
  },

  showSubmissionSuccess(data) {
    const modal = document.getElementById("submission-success-modal");
    if (!modal) return;

    const elId = document.getElementById("modal-ticket-id");
    const elTitle = document.getElementById("modal-ticket-title");
    const elCat = document.getElementById("modal-ticket-cat");
    const elAddr = document.getElementById("modal-ticket-addr");
    const elSla = document.getElementById("modal-ticket-sla");

    if (elId) elId.textContent = data.id || "";
    if (elTitle) elTitle.textContent = data.title || data.description || "";
    if (elCat) elCat.textContent = data.category || "";
    if (elAddr) elAddr.textContent = `${data.location_address || ""} (${data.borough || data.zone || ""})`;
    if (elSla && data.sla_due_date) elSla.textContent = new Date(data.sla_due_date).toLocaleString();

    modal.classList.remove("hidden");
  },

  /**
   * Personalized Citizen Dashboard:
   * Fetches only complaints submitted by the active citizen.
   */
  async loadMyComplaints() {
    const container = document.getElementById("my-complaints-list");
    if (!container) return;

    const user = window.Auth && typeof window.Auth.getCurrentUser === "function" ? window.Auth.getCurrentUser() : null;
    if (!user) {
      container.innerHTML = `
        <div class="p-12 text-center bg-slate-50 rounded-2xl border border-slate-200">
          <span class="text-3xl block mb-2">🔒</span>
          <h4 class="text-sm font-bold text-slate-800 mb-1">Sign In Required for Personal Tracking</h4>
          <p class="text-xs text-slate-500 max-w-sm mx-auto mb-4">Please register or sign in to your citizen account to view complaints submitted by you and track their official municipal approval.</p>
          <button onclick="window.Auth.openAuthModal('login')" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-xs shadow-md transition">
            Sign In / Register
          </button>
        </div>
      `;
      return;
    }

    try {
      container.innerHTML = `<div class="p-8 text-center text-slate-400 text-xs">Loading your submitted requests...</div>`;
      const data = await Api.getMyComplaints(user.email);
      this.myComplaintsData = data || [];

      this.updateMyComplaintsKPIs();
      this.renderMyComplaintsList();
    } catch (err) {
      console.error("[Citizen] Error loading my complaints:", err);
      container.innerHTML = `
        <div class="p-6 text-center text-slate-500 text-xs">
          <p class="font-semibold text-slate-700">No complaints registered under ${user.email} yet.</p>
          <p class="mt-1">Submit your first civic issue above to track its live status and official municipal review.</p>
        </div>
      `;
    }
  },

  updateMyComplaintsKPIs() {
    const total = this.myComplaintsData.length;
    const pending = this.myComplaintsData.filter(c => c.approval_status === "PENDING_REVIEW").length;
    const approved = this.myComplaintsData.filter(c => c.approval_status === "APPROVED" && c.status !== "RESOLVED").length;
    const resolved = this.myComplaintsData.filter(c => c.status === "RESOLVED").length;

    const elTotal = document.getElementById("my-kpi-total");
    const elPending = document.getElementById("my-kpi-pending");
    const elApproved = document.getElementById("my-kpi-approved");
    const elResolved = document.getElementById("my-kpi-resolved");

    if (elTotal) elTotal.textContent = total;
    if (elPending) elPending.textContent = pending;
    if (elApproved) elApproved.textContent = approved;
    if (elResolved) elResolved.textContent = resolved;
  },

  renderMyComplaintsList() {
    const container = document.getElementById("my-complaints-list");
    if (!container) return;

    const filterStatus = document.getElementById("my-filter-status")?.value || "ALL";
    const searchQuery = (document.getElementById("my-search-input")?.value || "").toLowerCase().trim();

    let list = [...this.myComplaintsData];

    if (filterStatus !== "ALL") {
      if (filterStatus === "PENDING_REVIEW") {
        list = list.filter(c => c.approval_status === "PENDING_REVIEW");
      } else if (filterStatus === "APPROVED") {
        list = list.filter(c => c.approval_status === "APPROVED");
      } else if (filterStatus === "RESOLVED") {
        list = list.filter(c => c.status === "RESOLVED");
      }
    }

    if (searchQuery) {
      list = list.filter(c =>
        c.id.toLowerCase().includes(searchQuery) ||
        c.title.toLowerCase().includes(searchQuery) ||
        c.category.toLowerCase().includes(searchQuery) ||
        c.location_address.toLowerCase().includes(searchQuery)
      );
    }

    if (list.length === 0) {
      container.innerHTML = `
        <div class="p-8 text-center text-slate-400 text-xs">
          <p class="font-medium text-slate-600">No matching requests found.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = list.map((ticket) => {
      const approvalBadge = this.getApprovalBadgeHtml(ticket.approval_status, ticket.status);
      const categoryIcon = this.getCategoryIcon(ticket.category);

      return `
        <div class="p-4 rounded-xl border border-slate-200 bg-white hover:border-blue-300 hover:shadow-sm transition flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div class="flex items-start gap-3">
            <div class="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center text-xl shrink-0">
              ${categoryIcon}
            </div>
            <div>
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-xs font-mono font-bold text-blue-700">${ticket.id}</span>
                <span class="text-xs font-bold text-slate-900">${ticket.title}</span>
                ${approvalBadge}
              </div>
              <p class="text-xs text-slate-500 mt-1 flex items-center gap-1">
                <span>📍 ${ticket.location_address} (${ticket.borough})</span>
                &bull;
                <span>📅 ${new Date(ticket.created_at).toLocaleDateString()}</span>
                &bull;
                <span>SLA Target: ${new Date(ticket.sla_due_date).toLocaleDateString()}</span>
              </p>
            </div>
          </div>

          <div class="flex items-center gap-2 self-end sm:self-center shrink-0">
            <button class="px-3 py-1.5 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 text-xs font-semibold border border-blue-200 transition flex items-center gap-1"
              onclick="window.CitizenPortal.trackComplaint('${ticket.id}')">
              <span>🔍 Track Status & Details</span>
            </button>
          </div>
        </div>
      `;
    }).join("");
  },

  getApprovalBadgeHtml(approvalStatus, ticketStatus) {
    if (ticketStatus === "RESOLVED") {
      return `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">🏆 RESOLVED</span>`;
    }
    if (approvalStatus === "APPROVED") {
      return `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-300">✅ APPROVED & DISPATCHED</span>`;
    }
    if (approvalStatus === "REJECTED") {
      return `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-300">❌ CLOSED / REJECTED</span>`;
    }
    return `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">⏳ UNDER MUNICIPAL REVIEW</span>`;
  },

  getCategoryIcon(cat) {
    const icons = {
      Streetlight: "💡",
      Pothole: "🕳️",
      "Water Supply": "💧",
      "Garbage & Sanitation": "🗑️",
      "Traffic Signal": "🚦",
      "Broken Sidewalk": "🚶",
      "Trees & Parks": "🌳",
      "Noise & Disturbance": "📢",
    };
    return icons[cat] || "📋";
  },

  async trackComplaint(id) {
    const trackModal = document.getElementById("tracking-modal");
    const trackCard = document.getElementById("tracking-result-card");
    const errorBox = document.getElementById("tracking-error");
    if (errorBox) errorBox.classList.add("hidden");

    try {
      const data = await Api.getComplaint(id);
      this.renderTrackingDetails(data);
      if (trackModal) trackModal.classList.remove("hidden");
      if (trackCard) trackCard.classList.remove("hidden");
    } catch (err) {
      if (errorBox) {
        errorBox.textContent = `Could not locate complaint '${id}'. Please verify your ticket reference.`;
        errorBox.classList.remove("hidden");
      }
    }
  },

  renderTrackingDetails(data) {
    const elId = document.getElementById("track-detail-id");
    const elTitle = document.getElementById("track-detail-title");
    const elCat = document.getElementById("track-detail-cat");
    const elAddr = document.getElementById("track-detail-addr");
    const elCreated = document.getElementById("track-detail-created");
    const elSla = document.getElementById("track-detail-sla");
    const elDept = document.getElementById("track-detail-dept");

    if (elId) elId.textContent = data.id || "";
    if (elTitle) elTitle.textContent = data.title || "";
    if (elCat) elCat.textContent = data.category || "";
    if (elAddr) elAddr.textContent = `${data.location_address || ""} (${data.borough || data.zone || ""})`;
    if (elCreated && data.created_at) elCreated.textContent = new Date(data.created_at).toLocaleString();
    if (elSla && data.sla_due_date) elSla.textContent = new Date(data.sla_due_date).toLocaleString();
    if (elDept) elDept.textContent = data.assigned_department || "Municipal Operations Directorate";

    // Approval status callout
    const approvalBox = document.getElementById("track-approval-banner");
    if (approvalBox) {
      const isApproved = data.approval_status === "APPROVED";
      const isRejected = data.approval_status === "REJECTED";
      if (isApproved) {
        approvalBox.className = "p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-900";
        approvalBox.innerHTML = `<strong>Status:</strong> Approved by Operations (${data.reviewed_by || "Administrator"}). Dispatched for field rectification.`;
      } else if (isRejected) {
        approvalBox.className = "p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-900";
        approvalBox.innerHTML = `<strong>Status:</strong> Closed / Rejected. Remarks: ${data.admin_review_notes || "Duplicate or outside municipal purview."}`;
      } else {
        approvalBox.className = "p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900";
        approvalBox.innerHTML = `<strong>Status:</strong> Under Review. A municipal officer is currently evaluating this request.`;
      }
    }

    // Step Stepper: SUBMITTED -> REVIEWED -> ASSIGNED -> IN_PROGRESS -> RESOLVED
    const steps = ["NEW", "ASSIGNED", "IN_PROGRESS", "RESOLVED"];
    const currentIdx = steps.indexOf(data.status);

    steps.forEach((step, idx) => {
      const stepCircle = document.getElementById(`step-circle-${step.toLowerCase()}`);
      if (stepCircle) {
        if (idx <= currentIdx) {
          stepCircle.className = "w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-xs ring-4 ring-blue-100";
        } else {
          stepCircle.className = "w-8 h-8 rounded-full bg-slate-200 text-slate-500 flex items-center justify-center font-bold text-xs";
        }
      }
    });

    // Render Timeline entries
    const tlContainer = document.getElementById("tracking-timeline-list");
    if (tlContainer) {
      tlContainer.innerHTML = (data.timeline || []).map((t) => `
        <div class="relative pl-6 pb-4 border-l-2 border-blue-200 last:border-transparent">
          <div class="absolute -left-[7px] top-0 w-3 h-3 rounded-full bg-blue-600"></div>
          <p class="text-xs font-semibold text-slate-900">${t.to_status} &bull; <span class="text-slate-500 font-normal">${new Date(t.created_at).toLocaleString()}</span></p>
          <p class="text-xs text-slate-600 mt-0.5"><strong>${t.actor}:</strong> ${t.notes || "Status updated"}</p>
        </div>
      `).join("");
    }

    // Render Comments
    const commentsContainer = document.getElementById("tracking-comments-list");
    if (commentsContainer) {
      if (!data.comments || data.comments.length === 0) {
        commentsContainer.innerHTML = `<p class="text-xs text-slate-400 italic">No notes posted yet.</p>`;
      } else {
        commentsContainer.innerHTML = data.comments.map((c) => `
          <div class="p-2.5 rounded-lg text-xs mb-2 ${c.author_type === 'Official' ? 'bg-blue-50 border border-blue-200 text-blue-900' : 'bg-slate-50 border border-slate-200 text-slate-800'}">
            <div class="flex items-center justify-between font-medium mb-1">
              <span>${c.author} ${c.author_type === 'Official' ? '🏛️ (City Staff)' : '👤'}</span>
              <span class="text-[10px] text-slate-400">${new Date(c.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
            </div>
            <p>${c.comment}</p>
          </div>
        `).join("");
      }
    }
  },

  async loadNearbyIssues() {
    const container = document.getElementById("nearby-issues-list");
    if (!container) return;

    const selBorough = document.getElementById("select-borough")?.value || "Central Ward";
    try {
      const items = await Api.getNearbyComplaints(selBorough, this.selectedCategory);
      if (!items || items.length === 0) {
        container.innerHTML = `<p class="text-xs text-slate-400 italic py-2">No active reports in this neighborhood right now.</p>`;
        return;
      }
      container.innerHTML = items.map((i) => `
        <div class="p-2.5 rounded-xl border border-slate-200 bg-white hover:border-blue-300 transition text-xs flex items-center justify-between">
          <div>
            <p class="font-semibold text-slate-800">${i.title}</p>
            <p class="text-[11px] text-slate-500">${i.location_address} &bull; ${i.status}</p>
          </div>
          <button class="px-2.5 py-1 rounded bg-slate-100 hover:bg-blue-100 text-blue-700 text-[11px] font-bold transition"
            onclick="window.upvoteComplaint('${i.id}')">
            👍 Confirm (+1)
          </button>
        </div>
      `).join("");
    } catch (e) {
      console.error(e);
    }
  }
};

window.CitizenPortal = CitizenPortal;
