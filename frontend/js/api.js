/**
 * API client module for Civic Complaint Portal
 * Handles authenticated citizen submissions, single-admin workflows, and real-time operations.
 */

const API_BASE = window.location.origin;

function getAuthHeaders(customHeaders = {}) {
  const headers = { ...customHeaders };
  const user = window.Auth && typeof window.Auth.getCurrentUser === "function" ? window.Auth.getCurrentUser() : null;
  if (user && user.token) {
    headers["Authorization"] = `Bearer ${user.token}`;
  }
  return headers;
}

export const Api = {
  // Authentication Endpoints
  async register(name, email, password, phone = "") {
    const res = await fetch(`${API_BASE}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password, phone }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Registration failed. Please check your inputs.");
    }
    return res.json();
  },

  async login(email, password) {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Sign-in failed. Please verify credentials.");
    }
    return res.json();
  },

  async getMe() {
    const res = await fetch(`${API_BASE}/api/auth/me`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Failed to fetch current user profile");
    return res.json();
  },

  async logout() {
    try {
      await fetch(`${API_BASE}/api/auth/logout`, {
        method: "POST",
        headers: getAuthHeaders(),
      });
    } catch (e) {
      console.warn("[Api] Logout network call error:", e);
    }
  },

  async getCategories() {
    const res = await fetch(`${API_BASE}/api/config/categories`);
    if (!res.ok) throw new Error("Failed to fetch categories");
    return res.json();
  },

  async getComplaints(params = {}) {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== "" && val !== "ALL") {
        query.append(key, val);
      }
    });
    const res = await fetch(`${API_BASE}/api/complaints?${query.toString()}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Failed to fetch complaints");
    return res.json();
  },

  async getComplaint(id) {
    const res = await fetch(`${API_BASE}/api/complaints/${encodeURIComponent(id)}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(`Complaint ${id} not found`);
    return res.json();
  },

  async getMyComplaints(citizenEmail) {
    const cleanEmail = encodeURIComponent(citizenEmail || "");
    const res = await fetch(`${API_BASE}/api/complaints/my-complaints?citizen_email=${cleanEmail}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Failed to fetch citizen complaints");
    return res.json();
  },

  async updateComplaintApproval(id, approvalStatus, adminNotes = "", assignedDepartment = null, reviewedBy = "Municipal Operations Administrator") {
    const res = await fetch(`${API_BASE}/api/complaints/${encodeURIComponent(id)}/approval`, {
      method: "PATCH",
      headers: getAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        approval_status: approvalStatus,
        admin_review_notes: adminNotes,
        assigned_department: assignedDepartment,
        reviewed_by: reviewedBy,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to update complaint approval status");
    }
    return res.json();
  },

  async batchUpdateApproval(complaintIds, approvalStatus, adminNotes = "", assignedDepartment = null, reviewedBy = "Municipal Operations Administrator") {
    const res = await fetch(`${API_BASE}/api/complaints/batch-approval`, {
      method: "POST",
      headers: getAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        complaint_ids: complaintIds,
        approval_status: approvalStatus,
        admin_review_notes: adminNotes,
        assigned_department: assignedDepartment,
        reviewed_by: reviewedBy,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to batch update approvals");
    }
    return res.json();
  },

  async createComplaint(payload) {
    const res = await fetch(`${API_BASE}/api/complaints`, {
      method: "POST",
      headers: getAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to submit complaint");
    }
    return res.json();
  },

  async updateComplaintStatus(id, status, notes = "", actor = "Operations Staff", resolutionNotes = "") {
    const res = await fetch(`${API_BASE}/api/complaints/${encodeURIComponent(id)}/status`, {
      method: "PATCH",
      headers: getAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        status,
        notes,
        actor,
        resolution_notes: resolutionNotes,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to update status");
    }
    return res.json();
  },

  async assignComplaint(id, department, officer = "", notes = "", actor = "Dispatcher") {
    const res = await fetch(`${API_BASE}/api/complaints/${encodeURIComponent(id)}/assign`, {
      method: "POST",
      headers: getAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        department,
        officer,
        notes,
        actor,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to assign complaint");
    }
    return res.json();
  },

  async upvoteComplaint(id) {
    const res = await fetch(`${API_BASE}/api/complaints/${encodeURIComponent(id)}/upvote`, {
      method: "POST",
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Failed to upvote complaint");
    return res.json();
  },

  async addComment(id, author, comment, authorType = "Citizen") {
    const res = await fetch(`${API_BASE}/api/complaints/${encodeURIComponent(id)}/comments`, {
      method: "POST",
      headers: getAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        author,
        comment,
        author_type: authorType,
      }),
    });
    if (!res.ok) throw new Error("Failed to add comment");
    return res.json();
  },

  async getNearbyComplaints(borough = "", category = "") {
    const query = new URLSearchParams();
    if (borough) query.append("borough", borough);
    if (category) query.append("category", category);
    const res = await fetch(`${API_BASE}/api/complaints/nearby?${query.toString()}`);
    if (!res.ok) return [];
    return res.json();
  },

  async analyzeWithAI(text) {
    const res = await fetch(`${API_BASE}/api/ai/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "AI analysis failed");
    }
    return res.json();
  },

  async getDashboardMetrics() {
    const res = await fetch(`${API_BASE}/api/analytics/dashboard`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Failed to fetch analytics");
    return res.json();
  },

  async getHotspots() {
    const res = await fetch(`${API_BASE}/api/analytics/hotspots`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Failed to fetch hotspots");
    return res.json();
  },

  async seedDatabase(force = false) {
    const res = await fetch(`${API_BASE}/api/analytics/seed?force=${force}`, {
      method: "POST",
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Failed to seed database");
    return res.json();
  },

  async getModelStatus() {
    const res = await fetch(`${API_BASE}/api/ai/model-status`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Failed to fetch ML model status");
    return res.json();
  },

  async trainModel(datasetPath = null, testSize = 0.2, algorithm = "ensemble") {
    const res = await fetch(`${API_BASE}/api/ai/train`, {
      method: "POST",
      headers: getAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ dataset_path: datasetPath, test_size: testSize, algorithm: algorithm }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Model training failed");
    }
    return res.json();
  },
};
