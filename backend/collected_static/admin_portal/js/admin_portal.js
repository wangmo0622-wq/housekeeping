/**
 * 管理后台壳层：布局、多标签、导航、分页组件、页面调度。
 *
 * 业务页面在 admin_portal/js/pages/*.js 中注册到 window.AdminPortalPages[pageKey]，
 * pageKey 与 Django 模板 base.html 中 {% if page_key == '...' %} 按需加载的脚本一致：
 *
 * | page_key          | 脚本文件                    |
 * |-------------------|-----------------------------|
 * | dashboard         | pages/dashboard.js          |
 * | categories        | pages/categories.js         |
 * | technicians       | pages/technicians.js        |
 * | listings          | pages/listings.js           |
 * | registered_users  | pages/registered_users.js   |
 * | admin_users       | pages/admin_users.js        |
 * | change_password   | pages/change_password.js    |
 * | profile           | pages/profile.js            |
 * | banners           | pages/banners.js            |
 * | hot_services      | pages/hot_services.js       |
 * | menus             | pages/menus.js              |
 */
window.AdminPortalPages = window.AdminPortalPages || {};
window.__ADMIN_MENU_ITEMS__ = [];

function requireTokenOrRedirect() {
  const token = getAdminToken();
  if (!token) {
    window.location.href = "/admin/login/";
    return false;
  }
  return true;
}

function initLogout() {
  const btn = document.getElementById("btn-logout");
  if (!btn) return;
  btn.addEventListener("click", () => {
    localStorage.removeItem("admin_access_token");
    window.location.href = "/admin/login/";
  });
}

function initUserDropdown() {
  const userBtn = document.getElementById("zy-user-btn");
  const userDropdown = document.querySelector(".zy-user-dropdown");
  
  if (!userBtn || !userDropdown) return;
  
  userBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    userDropdown.classList.toggle("active");
  });
  
  document.addEventListener("click", () => {
    userDropdown.classList.remove("active");
  });
}

async function loadCurrentUser() {
  try {
    const data = await authFetch("/api/admin/me", { method: "GET" });
    const nameEl = document.getElementById("current-user-name");
    const avatarPlaceholder = document.getElementById("user-avatar-placeholder");
    const avatarImg = document.getElementById("user-avatar-img");
    
    if (nameEl) {
      nameEl.textContent = data.first_name || data.username || "-";
    }
    if (avatarPlaceholder && avatarImg) {
      if (data.avatar_url && data.avatar_url.startsWith("http")) {
        avatarImg.src = data.avatar_url;
        avatarImg.classList.remove("hidden");
        avatarPlaceholder.classList.add("hidden");
      } else {
        avatarImg.classList.add("hidden");
        avatarPlaceholder.classList.remove("hidden");
        const initial = data.avatar_url || (data.first_name ? data.first_name.charAt(0).toUpperCase() : data.username.charAt(0).toUpperCase());
        avatarPlaceholder.textContent = initial;
      }
    }
  } catch (e) {
    console.error("加载用户信息失败", e);
    const avatarPlaceholder = document.getElementById("user-avatar-placeholder");
    const avatarImg = document.getElementById("user-avatar-img");
    if (avatarPlaceholder && avatarImg) {
      avatarImg.classList.add("hidden");
      avatarPlaceholder.classList.remove("hidden");
      avatarPlaceholder.textContent = "U";
    }
  }
}

const pageConfig = {
  dashboard: {
    title: '系统首页',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><rect x="3" y="3" width="18" height="18" rx="2" ry="2" /><line x1="3" y1="9" x2="21" y2="9" /><line x1="9" y1="21" x2="9" y2="9" /></svg>',
    url: '/admin/dashboard/'
  },
  categories: {
    title: '分类管理',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><rect x="3" y="3" width="18" height="18" rx="2" ry="2" /><line x1="3" y1="9" x2="21" y2="9" /><line x1="9" y1="21" x2="9" y2="9" /></svg>',
    url: '/admin/categories/'
  },
  listings: {
    title: '服务管理',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /><polyline points="10 9 9 9 8 9" /></svg>',
    url: '/admin/listings/'
  },
  technicians: {
    title: '技师认证',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /></svg>',
    url: '/admin/technicians/'
  },
  organizations: {
    title: '机构管理',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="M3 21h18"/><path d="M5 21V7l7-4 7 4v14"/><path d="M9 9h.01"/><path d="M15 9h.01"/><path d="M9 13h.01"/><path d="M15 13h.01"/></svg>',
    url: '/admin/organizations/'
  },
  registered_users: {
    title: '会员列表',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></svg>',
    url: '/admin/registered-users/'
  },
  admin_users: {
    title: '管理用户',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></svg>',
    url: '/admin/admin-users/'
  },
  menus: {
    title: '菜单管理',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="M4 6h16"/><path d="M4 12h16"/><path d="M4 18h16"/></svg>',
    url: '/admin/menus/'
  },
  banners: {
    title: '轮播管理',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><rect x="3" y="3" width="18" height="18" rx="2" ry="2" /><circle cx="8.5" cy="8.5" r="1.5" /><polyline points="21 15 16 10 5 21" /></svg>',
    url: '/admin/banners/'
  },
  hot_services: {
    title: '热门服务',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z" /></svg>',
    url: '/admin/hot-services/'
  },
  legal_docs: {
    title: '协议政策管理',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /></svg>',
    url: '/admin/legal-docs/'
  },
  legal_terms: {
    title: '服务协议',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /></svg>',
    url: '/admin/legal-terms/'
  },
  legal_privacy: {
    title: '隐私政策',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /></svg>',
    url: '/admin/legal-privacy/'
  },
  llm_providers: {
    title: '大模型管理',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l8 4v6c0 5-3.5 9-8 10-4.5-1-8-5-8-10V6z"></path><path d="M9 12l2 2 4-4"></path></svg>',
    url: '/admin/llm-providers/'
  },
  change_password: {
    title: '修改密码',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>',
    url: '/admin/change-password/'
  },
  profile: {
    title: '个人资料',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>',
    url: '/admin/profile/'
  }
};

function getTabs() {
  const raw = localStorage.getItem("admin_tabs");
  if (!raw) return [];
  let tabs;
  try {
    tabs = JSON.parse(raw);
  } catch {
    return [];
  }
  if (!Array.isArray(tabs)) return [];
  const valid = tabs.filter((t) => t && t.key && pageConfig[t.key]);
  if (valid.length !== tabs.length) {
    saveTabs(valid);
  }
  return valid;
}

function saveTabs(tabs) {
  localStorage.setItem('admin_tabs', JSON.stringify(tabs));
}

function addTab(pageKey) {
  const config = pageConfig[pageKey];
  if (!config) return;
  
  let tabs = getTabs();
  
  // 检查标签页是否已存在
  const existingTab = tabs.find(tab => tab.key === pageKey);
  if (existingTab) {
    // 如果存在，激活该标签页
    activateTab(pageKey);
    return;
  }
  
  // 添加新标签页
  tabs.push({
    key: pageKey,
    title: config.title,
    url: config.url
  });
  
  saveTabs(tabs);
  renderTabs();
  activateTab(pageKey);
}

function removeTab(pageKey) {
  // 首页标签不能被删除
  if (pageKey === 'dashboard') {
    return;
  }
  
  let tabs = getTabs();
  tabs = tabs.filter(tab => tab.key !== pageKey);
  saveTabs(tabs);
  renderTabs();
  
  // 如果删除的是当前标签页，激活第一个标签页
  if (pageKey === window.__ADMIN_PAGE_KEY__) {
    if (tabs.length > 0) {
      window.location.href = tabs[0].url;
    } else {
      window.location.href = pageConfig.dashboard?.url || "/admin/dashboard/";
    }
  }
}

function activateTab(pageKey) {
  document.querySelectorAll('.zy-tab').forEach(tab => {
    if (tab.getAttribute('data-page') === pageKey) {
      tab.classList.add('active');
    } else {
      tab.classList.remove('active');
    }
  });
}

function renderTabs() {
  const tabsContainer = document.getElementById('zy-tabs');
  if (!tabsContainer) return;
  
  const tabs = getTabs();
  tabsContainer.innerHTML = '';
  
  tabs.forEach(tab => {
    const config = pageConfig[tab.key];
    if (!config) return;
    
    const tabElement = document.createElement('a');
    tabElement.className = `zy-tab ${tab.key === window.__ADMIN_PAGE_KEY__ ? 'active' : ''}`;
    tabElement.href = tab.url;
    tabElement.setAttribute('data-page', tab.key);
    
    // 首页标签不能关闭
    if (tab.key === 'dashboard') {
      tabElement.innerHTML = `
        ${config.icon}
        ${config.title}
      `;
    } else {
      tabElement.innerHTML = `
        ${config.icon}
        ${config.title}
        <button class="zy-tab-close" data-page="${tab.key}">&times;</button>
      `;
    }
    tabsContainer.appendChild(tabElement);
  });
  
}

let __adminTabCloseDelegated = false;

/** 标签关闭：仅绑定一次 document 委托，避免 renderTabs 重复注册监听器 */
function ensureTabCloseDelegation() {
  if (__adminTabCloseDelegated) return;
  __adminTabCloseDelegated = true;
  document.addEventListener("click", (e) => {
    const closeBtn = e.target.closest(".zy-tab-close");
    if (!closeBtn) return;
    e.preventDefault();
    e.stopPropagation();
    const pageKey = closeBtn.getAttribute("data-page");
    if (pageKey) removeTab(pageKey);
  });
}

function renderMenuTree(items) {
  const nav = document.querySelector('.zy-nav');
  if (!nav || !Array.isArray(items) || items.length === 0) return;

  const escapeHtml = (s) =>
    String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");

  const normalizeIconKey = (raw) => {
    let s = String(raw || "").trim();
    if (!s) return "";
    if (s.includes("<svg")) return s;
    s = s.replace(/\\/g, "/");
    if (s.includes("/")) s = s.split("/").pop() || "";
    s = s.replace(/\.svg$/i, "");
    return s.trim();
  };

  const renderIcon = (raw, className = "zy-nav-item-icon") => {
    const iconKey = normalizeIconKey(raw);
    if (!iconKey) return "";
    if (iconKey.includes("<svg")) {
      return `<span class="${className}">${iconKey}</span>`;
    }
    return `<img src="/static/admin_portal/icons/svg/${escapeHtml(iconKey)}.svg" alt="" class="${className}" onerror="this.style.display='none'" />`;
  };

  const renderLink = (m) => {
    const key = escapeHtml(m.key);
    const path = escapeHtml(m.path || "#");
    const name = escapeHtml(m.name);
    const iconHtml = renderIcon(m.icon, "zy-nav-item-icon");
    return `<a class="zy-nav-item" data-page="${key}" href="${path}">${iconHtml}<span>${name}</span></a>`;
  };

  const html = items
    .map((item) => {
      if (item.is_section) {
        const children = Array.isArray(item.children) ? item.children : [];
        const showAsPlain = children.length === 0 && item.path && item.key;
        if (showAsPlain) {
          return `<div class="zy-nav-section">${renderLink(item)}</div>`;
        }
        const sectionIcon = renderIcon(item.icon, "zy-nav-item-icon");
        return `
          <div class="zy-nav-section">
            <div class="zy-nav-section-title zy-nav-section-toggle">
              ${sectionIcon}
              ${escapeHtml(item.name)}
              <span class="zy-nav-arrow">‹</span>
            </div>
            <div class="zy-nav-section-content expanded">
              ${children.map(renderLink).join("")}
            </div>
          </div>
        `;
      }
      return `<div class="zy-nav-section">${renderLink(item)}</div>`;
    })
    .join("");

  if (html.trim()) {
    nav.innerHTML = html;
  }
}

function syncActiveNavItem() {
  const currentPageKey = window.__ADMIN_PAGE_KEY__;
  document.querySelectorAll('.zy-nav-item').forEach((item) => {
    const isActive = item.getAttribute('data-page') === currentPageKey;
    item.classList.toggle('active', isActive);
  });
}

async function refreshAdminMenus() {
  try {
    const data = await authFetch('/api/admin/menus', { method: 'GET' });
    const items = (data && data.items) || [];
    window.__ADMIN_MENU_ITEMS__ = items;
    renderMenuTree(items);
    syncActiveNavItem();
  } catch (e) {
    console.warn('加载动态菜单失败，使用静态菜单', e);
    window.__ADMIN_MENU_ITEMS__ = [];
    syncActiveNavItem();
  }
}

window.refreshAdminMenus = refreshAdminMenus;

async function initNavigation() {
  await refreshAdminMenus();
  syncActiveNavItem();

  document.addEventListener('click', (e) => {
    const navItem = e.target.closest('.zy-nav-item');
    if (!navItem) return;
    
    // mobile: 导航点击后收起侧边栏抽屉
    if (window.matchMedia && window.matchMedia('(max-width: 768px)').matches) {
      document.body.classList.remove('zy-mobile-sidebar-open');
    }
  });
  
  // 初始化导航菜单收缩功能
  initNavToggle();
}

function initMobileSidebar() {
  const btn = document.getElementById('zy-mobile-menu-btn');
  const overlay = document.getElementById('zy-mobile-sidebar-overlay');
  if (!btn || !overlay) return;

  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    document.body.classList.toggle('zy-mobile-sidebar-open');
  });

  overlay.addEventListener('click', () => {
    document.body.classList.remove('zy-mobile-sidebar-open');
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.body.classList.remove('zy-mobile-sidebar-open');
    }
  });
}

function initNavToggle() {
  const currentPageKey = window.__ADMIN_PAGE_KEY__;
  
  const contents = document.querySelectorAll('.zy-nav-section-content');
  const titles = document.querySelectorAll('.zy-nav-section-title');
  
  contents.forEach(el => el.style.transition = 'none');
  titles.forEach(el => el.style.transition = 'none');
  
  document.querySelectorAll('.zy-nav-section').forEach(section => {
    const content = section.querySelector('.zy-nav-section-content');
    const title = section.querySelector('.zy-nav-section-title');
    const activeItem = section.querySelector(`.zy-nav-item[data-page="${currentPageKey}"]`);
    
    if (content && title && activeItem) {
      content.classList.add('expanded');
      title.classList.add('expanded');
    }
  });
  
  requestAnimationFrame(() => {
    contents.forEach(el => el.style.transition = '');
    titles.forEach(el => el.style.transition = '');
  });
  
  document.addEventListener('click', (e) => {
    const toggle = e.target.closest('.zy-nav-section-toggle');
    if (!toggle) return;
    
    e.preventDefault();
    e.stopPropagation();
    
    const section = toggle.closest('.zy-nav-section');
    const content = section.querySelector('.zy-nav-section-content');
    if (!content) return;
    
    const isExpanded = content.classList.contains('expanded');
    
    document.querySelectorAll('.zy-nav-section-content.expanded').forEach(item => {
      if (item !== content) {
        item.classList.remove('expanded');
        const itemTitle = item.closest('.zy-nav-section').querySelector('.zy-nav-section-title');
        if (itemTitle) {
          itemTitle.classList.remove('expanded');
        }
      }
    });
    
    if (isExpanded) {
      content.classList.remove('expanded');
      toggle.classList.remove('expanded');
    } else {
      content.classList.add('expanded');
      toggle.classList.add('expanded');
    }
  });
}

function renderAdminPagination(options) {
  const {
    root,
    containerSelector,
    total,
    page,
    totalPages,
    pageSize,
    onPageChange,
    onPageSizeChange,
  } = options;

  if (!root || !containerSelector) return;
  const pagination = root.querySelector(containerSelector);
  if (!pagination) return;

  if (!total || total <= 0 || !totalPages || totalPages <= 0) {
    pagination.innerHTML = "";
    return;
  }

  const safePage = Math.max(1, Math.min(page, totalPages));
  const start = (safePage - 1) * pageSize + 1;
  const end = Math.min(safePage * pageSize, total);

  let pageButtons = "";
  const maxButtons = 5;
  let startPage = Math.max(1, safePage - Math.floor(maxButtons / 2));
  let endPage = Math.min(totalPages, startPage + maxButtons - 1);
  startPage = Math.max(1, endPage - maxButtons + 1);

  if (startPage > 1) {
    pageButtons += '<button class="zy-page-btn" data-page="1">1</button>';
    if (startPage > 2) {
      pageButtons += '<span class="zy-page-ellipsis">...</span>';
    }
  }

  for (let i = startPage; i <= endPage; i += 1) {
    pageButtons += `<button class="zy-page-btn ${i === safePage ? "active" : ""}" data-page="${i}">${i}</button>`;
  }

  if (endPage < totalPages) {
    if (endPage < totalPages - 1) {
      pageButtons += '<span class="zy-page-ellipsis">...</span>';
    }
    pageButtons += `<button class="zy-page-btn" data-page="${totalPages}">${totalPages}</button>`;
  }

  pagination.innerHTML = `
    <div class="zy-pagination-info">
      显示 ${start}-${end} 共 ${total} 条
    </div>
    <div class="zy-pagination-controls">
      <select class="zy-select zy-page-size-select" data-role="page-size">
        <option value="10" ${pageSize === 10 ? "selected" : ""}>10条/页</option>
        <option value="20" ${pageSize === 20 ? "selected" : ""}>20条/页</option>
        <option value="50" ${pageSize === 50 ? "selected" : ""}>50条/页</option>
        <option value="100" ${pageSize === 100 ? "selected" : ""}>100条/页</option>
      </select>
      <button class="zy-page-btn" data-page="${safePage > 1 ? safePage - 1 : 1}" ${safePage === 1 ? "disabled" : ""}>上一页</button>
      ${pageButtons}
      <button class="zy-page-btn" data-page="${safePage < totalPages ? safePage + 1 : totalPages}" ${safePage === totalPages ? "disabled" : ""}>下一页</button>
      <div class="zy-jump-to-page">
        跳至 <input type="number" class="zy-form-input zy-jump-input" data-role="jump-page" min="1" max="${totalPages}" value="${safePage}" /> 页
      </div>
    </div>
  `;

  pagination.querySelectorAll(".zy-page-btn[data-page]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const nextPage = parseInt(btn.dataset.page || "", 10);
      if (Number.isNaN(nextPage) || nextPage < 1 || nextPage > totalPages || nextPage === safePage) {
        return;
      }
      if (typeof onPageChange === "function") {
        onPageChange(nextPage);
      }
    });
  });

  const pageSizeSelect = pagination.querySelector('[data-role="page-size"]');
  if (pageSizeSelect) {
    pageSizeSelect.addEventListener("change", (e) => {
      const nextSize = parseInt(e.target.value, 10);
      if (Number.isNaN(nextSize) || nextSize <= 0) return;
      if (typeof onPageSizeChange === "function") {
        onPageSizeChange(nextSize);
      }
    });
  }

  const jumpInput = pagination.querySelector('[data-role="jump-page"]');
  if (jumpInput) {
    jumpInput.addEventListener("keypress", (e) => {
      if (e.key !== "Enter") return;
      const nextPage = parseInt(jumpInput.value, 10);
      if (Number.isNaN(nextPage) || nextPage < 1 || nextPage > totalPages || nextPage === safePage) {
        return;
      }
      if (typeof onPageChange === "function") {
        onPageChange(nextPage);
      }
    });
  }
}

window.renderAdminPagination = renderAdminPagination;

function initHeaderToolbar() {
  const fsBtn = document.getElementById("zy-btn-fullscreen");
  if (fsBtn) {
    fsBtn.addEventListener("click", async () => {
      try {
        if (!document.fullscreenElement) {
          await document.documentElement.requestFullscreen();
          fsBtn.setAttribute("title", "退出全屏");
        } else {
          await document.exitFullscreen();
          fsBtn.setAttribute("title", "全屏");
        }
      } catch (_e) {
        if (typeof showToast === "function") {
          showToast("当前环境不支持全屏", "warning");
        }
      }
    });
    document.addEventListener("fullscreenchange", () => {
      const inFs = !!document.fullscreenElement;
      fsBtn.setAttribute("title", inFs ? "退出全屏" : "全屏");
    });
  }

  const themeBtn = document.getElementById("zy-btn-theme");
  if (themeBtn) {
    const storageKey = "admin_theme";
    const syncThemeTitle = () => {
      const mode = document.documentElement.getAttribute("data-theme") || "light";
      themeBtn.setAttribute("title", mode === "dark" ? "切换为浅色" : "切换为深色");
    };
    const apply = (mode) => {
      document.documentElement.setAttribute("data-theme", mode);
      try {
        localStorage.setItem(storageKey, mode);
      } catch (_e) {}
      syncThemeTitle();
    };
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved === "dark" || saved === "light") apply(saved);
      else syncThemeTitle();
    } catch (_e) {
      syncThemeTitle();
    }
    themeBtn.addEventListener("click", () => {
      const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      apply(next);
    });
  }
}

function renderBreadcrumb() {
  const el = document.getElementById("zy-header-breadcrumb");
  if (!el) return;
  const currentPageKey = window.__ADMIN_PAGE_KEY__;
  const items = window.__ADMIN_MENU_ITEMS__ || [];

  const walk = (nodes, parent = null) => {
    for (const n of nodes || []) {
      if (n && n.key === currentPageKey) return { node: n, parent };
      const found = walk(n.children || [], n);
      if (found) return found;
    }
    return null;
  };

  const found = walk(items);
  const currentTitle = found?.node?.name || pageConfig[currentPageKey]?.title || "当前页面";
  const parentTitle = found?.parent?.name || "";

  const crumb = parentTitle
    ? `<span class="zy-header-breadcrumb-item">${parentTitle}</span><span class="zy-header-breadcrumb-sep">/</span><span class="zy-header-breadcrumb-item active">${currentTitle}</span>`
    : `<span class="zy-header-breadcrumb-item active">${currentTitle}</span>`;

  el.innerHTML = `
    <span class="zy-header-breadcrumb-icon" aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="4" y1="6" x2="20" y2="6"></line>
        <line x1="4" y1="12" x2="20" y2="12"></line>
        <line x1="4" y1="18" x2="20" y2="18"></line>
      </svg>
    </span>
    ${crumb}
  `;
}

async function initPage() {
  // 默认收起移动端侧边栏抽屉
  document.body.classList.remove('zy-mobile-sidebar-open');

  initLogout();
  initUserDropdown();
  await initNavigation();
  initMobileSidebar();
  ensureTabCloseDelegation();
  initHeaderToolbar();
  renderBreadcrumb();
  await loadCurrentUser();
  addTab(window.__ADMIN_PAGE_KEY__ || "dashboard");
  renderTabs();
  activateTab(window.__ADMIN_PAGE_KEY__ || "dashboard");

  const root = document.getElementById("admin-page-root");
  if (!root) return;
  root.classList.add("zy-page");
  const pageKey = root.getAttribute("data-page-key") || window.__ADMIN_PAGE_KEY__;

  if (!requireTokenOrRedirect()) return;

  const token = getAdminToken();
  const page = window.AdminPortalPages[pageKey];
  if (!page || typeof page.render !== "function") {
    root.innerHTML = `<div class="zy-alert zy-alert-warning">页面未实现：${pageKey}</div>`;
    return;
  }

  root.innerHTML =
    '<div class="zy-page-loading" role="status" aria-live="polite"><span class="zy-page-loading-dot"></span><span class="zy-page-loading-dot"></span><span class="zy-page-loading-dot"></span><span class="zy-page-loading-text">加载中</span></div>';
  try {
    await page.render(root, token);
  } catch (e) {
    console.error(e);
    root.innerHTML = `<div class="zy-alert zy-alert-error">页面加载失败：${(e && e.message) || "未知错误"}</div>`;
    return;
  }
  ensureTableHorizontalScroll(root);
}

function ensureTableHorizontalScroll(container) {
  if (!container) return;
  container.querySelectorAll(".zy-table").forEach((table) => {
    if (table.parentElement && table.parentElement.classList.contains("zy-table-scroll")) {
      return;
    }
    const wrapper = document.createElement("div");
    wrapper.className = "zy-table-scroll";
    table.parentNode.insertBefore(wrapper, table);
    wrapper.appendChild(table);
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  await initPage();
});
