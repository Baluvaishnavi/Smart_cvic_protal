/**
 * In-App Toast Notification Utility:
 * Sleek, modern, accessible notification banners that auto-dismiss.
 */

export const Toast = {
  container: null,

  init() {
    if (!this.container) {
      let el = document.getElementById("toast-container");
      if (!el) {
        el = document.createElement("div");
        el.id = "toast-container";
        el.className = "fixed bottom-5 right-5 z-50 flex flex-col gap-2 pointer-events-none max-w-sm w-full";
        document.body.appendChild(el);
      }
      this.container = el;
    }
  },

  show(message, type = "info", duration = 4000) {
    this.init();

    const toast = document.createElement("div");
    toast.className = `pointer-events-auto flex items-start gap-3 p-3.5 rounded-xl shadow-xl border text-xs font-semibold transform transition-all duration-300 translate-y-4 opacity-0`;

    let icon = "ℹ️";
    let colorClasses = "bg-white text-slate-800 border-slate-200";

    if (type === "success") {
      icon = "✓";
      colorClasses = "bg-emerald-50 text-emerald-950 border-emerald-300 ring-1 ring-emerald-400/20";
    } else if (type === "error") {
      icon = "✕";
      colorClasses = "bg-rose-50 text-rose-950 border-rose-300 ring-1 ring-rose-400/20";
    } else if (type === "warning") {
      icon = "⚠️";
      colorClasses = "bg-amber-50 text-amber-950 border-amber-300 ring-1 ring-amber-400/20";
    }

    toast.className += ` ${colorClasses}`;
    toast.innerHTML = `
      <div class="w-5 h-5 rounded-full flex items-center justify-center font-bold text-xs shrink-0 ${
        type === 'success' ? 'bg-emerald-600 text-white' :
        type === 'error' ? 'bg-rose-600 text-white' :
        type === 'warning' ? 'bg-amber-600 text-white' : 'bg-blue-600 text-white'
      }">${icon}</div>
      <div class="flex-1 pr-2 leading-relaxed">${message}</div>
      <button class="text-slate-400 hover:text-slate-600 text-sm font-bold leading-none p-1">&times;</button>
    `;

    const closeBtn = toast.querySelector("button");
    closeBtn.addEventListener("click", () => this.dismiss(toast));

    this.container.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
      toast.classList.remove("translate-y-4", "opacity-0");
      toast.classList.add("translate-y-0", "opacity-100");
    });

    // Auto dismiss
    const timer = setTimeout(() => {
      this.dismiss(toast);
    }, duration);

    toast.dataset.timer = timer;
  },

  dismiss(toast) {
    if (toast.dataset.timer) clearTimeout(Number(toast.dataset.timer));
    toast.classList.add("opacity-0", "translate-y-2");
    setTimeout(() => {
      if (toast.parentElement) toast.parentElement.removeChild(toast);
    }, 300);
  },

  success(msg, duration) {
    this.show(msg, "success", duration);
  },

  error(msg, duration) {
    this.show(msg, "error", duration);
  },

  info(msg, duration) {
    this.show(msg, "info", duration);
  },

  warning(msg, duration) {
    this.show(msg, "warning", duration);
  },
};

window.Toast = Toast;
