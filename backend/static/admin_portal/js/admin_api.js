/**
 * 管理后台 HTTP 与通用 UI：JWT authFetch、对话框、Toast。
 * 依赖：由 base.html 先于 admin_portal.js 加载。
 */
function getAdminToken() {
  return localStorage.getItem("admin_access_token") || "";
}

function shortToken(token) {
  if (!token) return "-";
  return token.slice(0, 8) + "...";
}

async function authFetch(path, options = {}) {
  const token = getAdminToken();
  const isFormData = options.body instanceof FormData;
  const headers = Object.assign(
    isFormData ? {} : { "Content-Type": "application/json" },
    options.headers || {}
  );
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const resp = await fetch(path, Object.assign({}, options, { headers }));
  
  // 处理 401 未授权错误，自动跳转到登录页
  if (resp.status === 401) {
    localStorage.removeItem("admin_access_token");
    window.location.href = "/admin/login/";
    throw new Error("登录已过期，请重新登录");
  }
  
  const text = await resp.text();
  let data = {};
  try {
    data = text ? JSON.parse(text) : {};
  } catch (_e) {
    data = { detail: text };
  }

  if (!resp.ok) {
    const detail = data.detail || data.message || `请求失败：HTTP ${resp.status}`;
    throw new Error(detail);
  }
  return data;
}

function el(id) {
  return document.getElementById(id);
}

function adminEscapeHtml(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/**
 * 表格无数据时统一单元格
 * @param {number} colspan
 * @param {string} [text=暂无数据]
 */
function adminTableEmptyRow(colspan, text) {
  const t = text != null && text !== "" ? text : "暂无数据";
  return `<tr><td colspan="${colspan}" class="zy-table-empty">${adminEscapeHtml(t)}</td></tr>`;
}

/** 加载失败等错误行 */
function adminTableErrorRow(colspan, text) {
  const t = text != null && text !== "" ? text : "加载失败";
  return `<tr><td colspan="${colspan}" class="zy-table-empty zy-table-empty--error">${adminEscapeHtml(t)}</td></tr>`;
}

/**
 * 弹窗/抽屉内只读键值对 HTML
 * @param {{ label: string, value: string }[]} lines
 */
function adminDetailLinesHtml(lines) {
  if (!lines || !lines.length) {
    return `<div class="zy-detail-block text-gray-500">无详细数据</div>`;
  }
  const body = lines
    .map(
      (l) =>
        `<div class="zy-detail-line"><span class="zy-detail-k">${adminEscapeHtml(l.label)}</span><span class="zy-detail-v">${adminEscapeHtml(l.value)}</span></div>`
    )
    .join("");
  return `<div class="zy-detail-block">${body}</div>`;
}

// 自定义弹窗函数
function showDialog(options) {
  const { title, message, type = 'info', confirmText = '确定', cancelText = '取消', showCancel = false, onConfirm, onCancel } = options;
  
  // 创建弹窗元素
  const overlay = document.createElement('div');
  overlay.className = 'zy-dialog-overlay';
  
  const iconMap = {
    warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
    info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>',
    success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>',
    error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>'
  };
  
  overlay.innerHTML = `
    <div class="zy-dialog">
      <div class="zy-dialog-header">
        <div class="zy-dialog-icon ${type}">
          ${iconMap[type] || iconMap.info}
        </div>
        <h3 class="zy-dialog-title">${title}</h3>
      </div>
      <div class="zy-dialog-body">${message}</div>
      <div class="zy-dialog-footer">
        ${showCancel ? `<button class="zy-btn zy-btn-secondary zy-btn-sm zy-dialog-cancel" type="button">${cancelText}</button>` : ''}
        <button class="zy-btn zy-btn-primary zy-btn-sm zy-dialog-confirm" type="button">${confirmText}</button>
      </div>
    </div>
  `;
  
  document.body.appendChild(overlay);
  
  // 显示弹窗
  requestAnimationFrame(() => {
    overlay.classList.add('active');
  });
  
  // 绑定事件
  const confirmBtn = overlay.querySelector('.zy-dialog-confirm');
  const cancelBtn = overlay.querySelector('.zy-dialog-cancel');
  
  function close() {
    overlay.classList.remove('active');
    setTimeout(() => {
      if (overlay.parentNode) {
        document.body.removeChild(overlay);
      }
    }, 200);
  }
  
  confirmBtn.addEventListener('click', async () => {
    close();
    if (onConfirm) await onConfirm();
  });
  
  if (cancelBtn) {
    cancelBtn.addEventListener('click', () => {
      close();
      if (onCancel) onCancel();
    });
  }
  
  // 点击遮罩关闭
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) {
      close();
      if (onCancel) onCancel();
    }
  });
}

// 确认弹窗
function showConfirm(options) {
  showDialog({ ...options, showCancel: true, type: options.type || 'warning' });
}

// 提示弹窗
function showAlert(message, title = '提示', type = 'info') {
  showDialog({ title, message, type, confirmText: '知道了' });
}

// 成功提示
function showSuccess(message, title = '成功') {
  showDialog({ title, message, type: 'success', confirmText: '知道了' });
}

// 错误提示
function showError(message, title = '错误') {
  showDialog({ title, message, type: 'error', confirmText: '知道了' });
}

/**
 * Toast：支持
 *   showToast("文字", "success", 3000)
 *   showToast({ title, message, type, duration })
 */
function showToast(messageOrOpts, type = 'success', duration = 3000) {
  let message = "";
  let toastType = type;
  let ms = duration;

  if (messageOrOpts && typeof messageOrOpts === "object" && !Array.isArray(messageOrOpts)) {
    const o = messageOrOpts;
    const title = o.title != null && String(o.title).trim() !== "" ? String(o.title) : "";
    const msg = o.message != null && String(o.message).trim() !== "" ? String(o.message) : "";
    if (title && msg) {
      message = title + "：" + msg;
    } else {
      message = title || msg;
    }
    if (o.type) {
      toastType = o.type;
    }
    if (o.duration != null) {
      ms = o.duration;
    }
  } else {
    message = String(messageOrOpts ?? "");
  }

  // 创建 toast 容器（如果不存在）
  let toastContainer = document.querySelector('.toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container';
    document.body.appendChild(toastContainer);
  }
  // 使用独立容器，避免被 daisyui 的 .toast/.toast-top/.toast-end 样式覆盖到页面底部
  toastContainer.style.setProperty("position", "fixed", "important");
  toastContainer.style.setProperty("top", "16px", "important");
  toastContainer.style.setProperty("right", "16px", "important");
  toastContainer.style.setProperty("left", "auto", "important");
  toastContainer.style.setProperty("bottom", "auto", "important");
  toastContainer.style.setProperty("z-index", "9999", "important");
  toastContainer.style.setProperty("display", "flex", "important");
  toastContainer.style.setProperty("flex-direction", "column", "important");
  toastContainer.style.setProperty("gap", "8px", "important");
  toastContainer.style.setProperty("pointer-events", "none", "important");
  
  // 主题色
  const typePalette = {
    success: { bg: "#f0fdf4", border: "#86efac", text: "#14532d", icon: "#166534" },
    error: { bg: "#fef2f2", border: "#fecaca", text: "#7f1d1d", icon: "#b91c1c" },
    warning: { bg: "#fffbeb", border: "#fde68a", text: "#78350f", icon: "#b45309" },
    info: { bg: "#eff6ff", border: "#bfdbfe", text: "#1e3a8a", icon: "#1d4ed8" },
  };

  const typeIcons = {
    success: '<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>',
    error: '<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>',
    warning: '<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>',
    info: '<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>'
  };
  
  // 创建 toast 元素
  const toast = document.createElement('div');
  const palette = typePalette[toastType] || typePalette.success;
  const ti = typeIcons[toastType] || typeIcons.success;
  toast.className = `transition-all duration-300 ease-in-out opacity-0 translate-x-full`;
  toast.style.pointerEvents = "auto";
  toast.style.minWidth = "240px";
  toast.style.maxWidth = "360px";
  toast.style.borderRadius = "10px";
  toast.style.border = `1px solid ${palette.border}`;
  toast.style.background = palette.bg;
  toast.style.color = palette.text;
  toast.style.boxShadow = "0 12px 28px rgba(2, 6, 23, 0.14)";
  toast.style.padding = "10px 12px";
  toast.style.fontSize = "13px";
  toast.style.lineHeight = "1.45";
  toast.style.display = "flex";
  toast.style.alignItems = "center";
  toast.style.gap = "8px";
  toast.innerHTML = `
    <span style="display:inline-flex;color:${palette.icon};">${ti}</span>
    <span>${adminEscapeHtml(message)}</span>
  `;
  
  toastContainer.appendChild(toast);
  
  // 动画进入
  requestAnimationFrame(() => {
    toast.classList.remove('opacity-0', 'translate-x-full');
  });
  
  // 自动消失
  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-x-full');
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 300);
  }, ms);
}

async function getDashboardData() {
  return authFetch('/api/admin/dashboard');
}

window.adminEscapeHtml = adminEscapeHtml;
window.adminTableEmptyRow = adminTableEmptyRow;
window.adminTableErrorRow = adminTableErrorRow;
window.adminDetailLinesHtml = adminDetailLinesHtml;
