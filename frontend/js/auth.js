/**
 * Role-Based Access Control (RBAC) & Authentication Module
 * Manages persistent Citizen registration, login, session tokens,
 * and enforces strict single-administrator access control.
 */

import { Api } from "/static/js/api.js";
import { Toast } from "/static/js/toast.js";

const Auth = {
  SESSION_KEY: "civic_portal_active_user",

  getCurrentUser() {
    try {
      const stored = localStorage.getItem(this.SESSION_KEY);
      if (stored) {
        return JSON.parse(stored);
      }
    } catch (e) {
      console.error("[Auth] Error reading session:", e);
    }
    return null;
  },

  setCurrentUser(user) {
    if (user) {
      localStorage.setItem(this.SESSION_KEY, JSON.stringify(user));
    } else {
      localStorage.removeItem(this.SESSION_KEY);
    }
    this.applyRolePermissions(user);
    window.dispatchEvent(new CustomEvent("civic_auth_changed", { detail: user }));
  },

  getToken() {
    const u = this.getCurrentUser();
    return u ? u.token : null;
  },

  isCitizen() {
    const u = this.getCurrentUser();
    return u && u.role === "CITIZEN";
  },

  isAdmin() {
    const u = this.getCurrentUser();
    return u && u.role === "ADMIN";
  },

  async login(email, password) {
    const session = await Api.login(email, password);
    this.setCurrentUser(session);
    return session;
  },

  async register(name, email, password, phone = "") {
    const session = await Api.register(name, email, password, phone);
    this.setCurrentUser(session);
    return session;
  },

  async logout() {
    await Api.logout();
    this.setCurrentUser(null);
    // Switch to citizen report tab
    const tabCitizen = document.getElementById("tab-citizen-btn");
    if (tabCitizen) tabCitizen.click();
  },

  openAuthModal(tab = "login") {
    const modal = document.getElementById("auth-modal");
    if (modal) {
      modal.classList.remove("hidden");
      this.showAuthTab(tab);
    }
  },

  closeAuthModal() {
    const modal = document.getElementById("auth-modal");
    if (modal) modal.classList.add("hidden");
    const loginErr = document.getElementById("login-error-msg");
    if (loginErr) loginErr.classList.add("hidden");
    const regErr = document.getElementById("register-error-msg");
    if (regErr) regErr.classList.add("hidden");
  },

  showAuthTab(tab) {
    const tabLogin = document.getElementById("auth-tab-login");
    const tabReg = document.getElementById("auth-tab-register");
    const formLogin = document.getElementById("form-auth-login");
    const formReg = document.getElementById("form-auth-register");

    if (tab === "register") {
      if (tabReg) {
        tabReg.className = "flex-1 py-2.5 text-xs font-bold border-b-2 border-emerald-600 text-emerald-700 transition";
      }
      if (tabLogin) {
        tabLogin.className = "flex-1 py-2.5 text-xs font-bold border-b-2 border-transparent text-slate-500 hover:text-slate-700 transition";
      }
      if (formReg) formReg.classList.remove("hidden");
      if (formLogin) formLogin.classList.add("hidden");
    } else {
      if (tabLogin) {
        tabLogin.className = "flex-1 py-2.5 text-xs font-bold border-b-2 border-blue-600 text-blue-700 transition";
      }
      if (tabReg) {
        tabReg.className = "flex-1 py-2.5 text-xs font-bold border-b-2 border-transparent text-slate-500 hover:text-slate-700 transition";
      }
      if (formLogin) formLogin.classList.remove("hidden");
      if (formReg) formReg.classList.add("hidden");
    }
  },

  async handleLoginSubmit(event) {
    event.preventDefault();
    const email = document.getElementById("login-email")?.value.trim();
    const password = document.getElementById("login-password")?.value;
    const errEl = document.getElementById("login-error-msg");
    const submitBtn = document.getElementById("btn-login-submit");

    if (!email || !password) return;
    try {
      if (errEl) errEl.classList.add("hidden");
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = "Signing in...";
      }

      const session = await this.login(email, password);
      this.closeAuthModal();

      if (session.role === "ADMIN") {
        Toast.success(`Welcome Administrator! You have full access to Approvals & Operations.`);
        const tabApprovals = document.getElementById("tab-approvals-btn");
        if (tabApprovals) tabApprovals.click();
      } else {
        Toast.success(`Welcome back, ${session.name}!`);
        const tabMy = document.getElementById("tab-my-complaints-btn");
        if (tabMy) tabMy.click();
      }
    } catch (err) {
      if (errEl) {
        errEl.textContent = err.message;
        errEl.classList.remove("hidden");
      } else {
        Toast.error(err.message);
      }
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "Sign In to Portal";
      }
    }
  },

  async handleRegisterSubmit(event) {
    event.preventDefault();
    const name = document.getElementById("register-name")?.value.trim();
    const email = document.getElementById("register-email")?.value.trim();
    const phone = document.getElementById("register-phone")?.value.trim();
    const password = document.getElementById("register-password")?.value;
    const errEl = document.getElementById("register-error-msg");
    const submitBtn = document.getElementById("btn-register-submit");

    if (!name || !email || !password) return;
    try {
      if (errEl) errEl.classList.add("hidden");
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = "Creating account...";
      }

      const session = await this.register(name, email, password, phone);
      this.closeAuthModal();
      Toast.success(`Registration Successful! Welcome to the Civic Complaint Portal, ${session.name}.`);
      
      const tabMy = document.getElementById("tab-my-complaints-btn");
      if (tabMy) tabMy.click();
    } catch (err) {
      if (errEl) {
        errEl.textContent = err.message;
        errEl.classList.remove("hidden");
      } else {
        Toast.error(err.message);
      }
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "Complete Registration & Sign In";
      }
    }
  },

  applyRolePermissions(user = null) {
    const activeUser = user || this.getCurrentUser();
    const authLoggedOut = document.getElementById("auth-logged-out");
    const authLoggedIn = document.getElementById("auth-logged-in");
    const nameEl = document.getElementById("auth-user-name");
    const roleBadge = document.getElementById("auth-role-badge");

    // Admin Tabs
    const tabAdmin = document.getElementById("tab-admin-btn");
    const tabApprovals = document.getElementById("tab-approvals-btn");
    const tabAnalytics = document.getElementById("tab-analytics-btn");
    const tabAdminMobile = document.getElementById("tab-admin-mobile");
    const tabApprovalsMobile = document.getElementById("tab-approvals-mobile");
    const tabAnalyticsMobile = document.getElementById("tab-analytics-mobile");

    // Citizen Tabs
    const tabCitizen = document.getElementById("tab-citizen-btn");
    const tabMyComplaints = document.getElementById("tab-my-complaints-btn");

    if (!activeUser) {
      // Guest / Not Logged In
      if (authLoggedOut) authLoggedOut.classList.remove("hidden");
      if (authLoggedIn) authLoggedIn.classList.add("hidden");

      if (tabAdmin) tabAdmin.classList.add("hidden");
      if (tabApprovals) tabApprovals.classList.add("hidden");
      if (tabAnalytics) tabAnalytics.classList.add("hidden");
      if (tabAdminMobile) tabAdminMobile.classList.add("hidden");
      if (tabApprovalsMobile) tabApprovalsMobile.classList.add("hidden");
      if (tabAnalyticsMobile) tabAnalyticsMobile.classList.add("hidden");
      if (tabCitizen) tabCitizen.classList.remove("hidden");
      if (tabMyComplaints) tabMyComplaints.classList.remove("hidden");
      return;
    }

    // Logged In
    if (authLoggedOut) authLoggedOut.classList.add("hidden");
    if (authLoggedIn) authLoggedIn.classList.remove("hidden");
    if (nameEl) nameEl.textContent = activeUser.name;

    const isAdm = activeUser.role === "ADMIN";

    if (roleBadge) {
      if (isAdm) {
        roleBadge.textContent = "MUNICIPAL ADMIN";
        roleBadge.className = "px-2 py-0.5 rounded-full text-[9px] font-bold bg-purple-100 text-purple-800 border border-purple-300";
      } else {
        roleBadge.textContent = "VERIFIED CITIZEN";
        roleBadge.className = "px-2 py-0.5 rounded-full text-[9px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300";
      }
    }

    if (isAdm) {
      // Admin sees Approvals, Operations, Analytics, and Citizen Report
      if (tabApprovals) tabApprovals.classList.remove("hidden");
      if (tabAdmin) tabAdmin.classList.remove("hidden");
      if (tabAnalytics) tabAnalytics.classList.remove("hidden");
      if (tabApprovalsMobile) tabApprovalsMobile.classList.remove("hidden");
      if (tabAdminMobile) tabAdminMobile.classList.remove("hidden");
      if (tabAnalyticsMobile) tabAnalyticsMobile.classList.remove("hidden");
      if (tabCitizen) tabCitizen.classList.remove("hidden");
      if (tabMyComplaints) tabMyComplaints.classList.add("hidden");

      if (window.ApprovalsManager && typeof window.ApprovalsManager.loadApprovals === "function") {
        window.ApprovalsManager.loadApprovals();
      }
    } else {
      // Citizen ONLY sees Report, Track, and My Complaints
      if (tabApprovals) tabApprovals.classList.add("hidden");
      if (tabAdmin) tabAdmin.classList.add("hidden");
      if (tabAnalytics) tabAnalytics.classList.add("hidden");
      if (tabApprovalsMobile) tabApprovalsMobile.classList.add("hidden");
      if (tabAdminMobile) tabAdminMobile.classList.add("hidden");
      if (tabAnalyticsMobile) tabAnalyticsMobile.classList.add("hidden");
      if (tabCitizen) tabCitizen.classList.remove("hidden");
      if (tabMyComplaints) tabMyComplaints.classList.remove("hidden");

      // Auto-switch to citizen view if on an admin page
      const currentActive = document.querySelector(".nav-tab.bg-white");
      if (currentActive && (currentActive.dataset.target === "view-admin" || currentActive.dataset.target === "view-analytics" || currentActive.dataset.target === "view-approvals")) {
        if (tabMyComplaints) tabMyComplaints.click();
        else if (tabCitizen) tabCitizen.click();
      }
    }

    // Prefill citizen form inputs
    const citizenEmailInput = document.getElementById("input-citizen-email");
    const citizenNameInput = document.getElementById("input-citizen-name");
    const citizenPhoneInput = document.getElementById("input-citizen-phone");
    if (citizenEmailInput && !isAdm) citizenEmailInput.value = activeUser.email;
    if (citizenNameInput && !isAdm) citizenNameInput.value = activeUser.name;
    if (citizenPhoneInput && !isAdm && activeUser.phone) citizenPhoneInput.value = activeUser.phone;
  },

  init() {
    const user = this.getCurrentUser();
    this.applyRolePermissions(user);
  }
};

window.Auth = Auth;
export { Auth };
