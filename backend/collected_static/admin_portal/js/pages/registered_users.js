window.AdminPortalPages["registered_users"] = {
  render: async function (root, token) {
    let currentPage = 1;
    let pageSize = 10;
    let totalPages = 0;

    function formatDateTime(dateStr) {
      if (!dateStr) return "-";
      const date = new Date(dateStr);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      const seconds = String(date.getSeconds()).padStart(2, '0');
      return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    }

    root.innerHTML = `
      <div class="zy-card">
        <div class="zy-card-body">
          <div class="zy-search-bar">
            <div class="zy-search-item">
              <label class="zy-search-label">关键词</label>
              <input type="search" id="user_q_search" placeholder="用户名、姓名、手机号" class="zy-form-input zy-search-control-lg" />
            </div>
            <div class="zy-search-item">
              <label class="zy-search-label">手机号</label>
              <input type="text" id="phone_search" placeholder="精确按手机号" class="zy-form-input zy-search-control-md" />
            </div>
            <div class="zy-search-item">
              <label class="zy-search-label">注册时间</label>
              <input type="date" id="date_search" class="zy-form-input zy-search-control-md" />
            </div>
            <div class="zy-search-item">
              <label class="zy-search-label">用户状态</label>
              <select id="user_status_filter" class="zy-select zy-search-control-sm">
                <option value="">全部状态</option>
                <option value="active">启用</option>
                <option value="disabled">禁用</option>
              </select>
            </div>
            <div class="zy-search-actions">
              <button id="user_reset_btn" class="zy-btn zy-btn-reset zy-btn-sm">重置</button>
              <button id="user_reload_btn" class="zy-btn zy-btn-query zy-btn-sm">查询</button>
            </div>
          </div>
          <div class="zy-list-actions-row">
            <button id="user_add_btn" type="button" class="zy-btn zy-btn-primary zy-btn-sm">新增会员</button>
          </div>
          <table class="zy-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>用户名</th>
                <th>手机号</th>
                <th>注册时间</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody id="user_tbody"></tbody>
          </table>
          <div id="user_pagination" class="zy-pagination"></div>
        </div>
      </div>

      <!-- 右侧抽屉 -->
      <div id="user_drawer_overlay" class="zy-drawer-overlay">
        <div class="zy-drawer">
          <div class="zy-drawer-header">
            <h3 class="zy-drawer-title" id="user_drawer_title">用户详情</h3>
            <button class="zy-drawer-close" id="user_drawer_close">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-5 h-5">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
          <div class="zy-drawer-body" id="user_drawer_body"></div>
          <div class="zy-drawer-footer" id="user_drawer_footer"></div>
        </div>
      </div>
    `;

    const drawerOverlay = root.querySelector("#user_drawer_overlay");
    const drawerTitle = root.querySelector("#user_drawer_title");
    const drawerBody = root.querySelector("#user_drawer_body");
    const drawerFooter = root.querySelector("#user_drawer_footer");
    const drawerClose = root.querySelector("#user_drawer_close");

    function openDrawer(title, bodyHtml, footerHtml) {
      drawerTitle.textContent = title;
      drawerBody.innerHTML = bodyHtml;
      drawerFooter.innerHTML = footerHtml;
      drawerOverlay.classList.add("active");
    }

    function closeDrawer() {
      drawerOverlay.classList.remove("active");
    }

    drawerClose.addEventListener("click", closeDrawer);
    drawerOverlay.addEventListener("click", (e) => {
      if (e.target === drawerOverlay) closeDrawer();
    });

    function renderPagination(total, page, totalPages, pageSize) {
      window.renderAdminPagination({
        root,
        containerSelector: "#user_pagination",
        total,
        page,
        totalPages,
        pageSize,
        onPageChange: (nextPage) => {
          currentPage = nextPage;
          loadList();
        },
        onPageSizeChange: (nextPageSize) => {
          pageSize = nextPageSize;
          currentPage = 1;
          loadList();
        },
      });
    }


    const debouncedUserQ =
      typeof window.adminDebounce === "function"
        ? window.adminDebounce(() => {
            currentPage = 1;
            loadList();
          }, 300)
        : () => {
            currentPage = 1;
            loadList();
          };
    root.querySelector("#user_q_search").addEventListener("input", debouncedUserQ);

    async function loadList() {
      const q = root.querySelector("#user_q_search").value.trim();
      const phoneSearch = root.querySelector("#phone_search").value.trim();
      const dateSearch = root.querySelector("#date_search").value;
      const statusFilter = root.querySelector("#user_status_filter").value;

      const params = new URLSearchParams();
      params.append("page", currentPage);
      params.append("page_size", pageSize);
      if (q) params.append("q", q);
      if (phoneSearch) params.append("phone", phoneSearch);
      if (dateSearch) params.append("date", dateSearch);
      if (statusFilter) params.append("status", statusFilter);

      const data = await authFetch(`/api/admin/registered-users?${params.toString()}`, { method: "GET" });
      let items = data.items || [];
      totalPages = data.total_pages || 1;

      const tbody = root.querySelector("#user_tbody");

      if (items.length === 0) {
        tbody.innerHTML = adminTableEmptyRow(6);
        renderPagination(0, 1, 0, pageSize);
        return;
      }

      tbody.innerHTML = items
        .map((x) => {
          return `
            <tr>
              <td>${x.id}</td>
              <td>${x.username || ""}</td>
              <td>${x.phone || "-"}</td>
              <td>${formatDateTime(x.date_joined)}</td>
              <td>${x.is_active ? '<span class="zy-badge zy-badge-success">启用</span>' : '<span class="zy-badge zy-badge-danger">禁用</span>'}</td>
              <td>
                <div class="zy-actions">
                  <a class="zy-action-link" data-action="detail" data-id="${x.id}">详情</a>
                  <a class="zy-action-link ${x.is_active ? 'zy-action-link--danger' : 'zy-action-link--success'}" data-action="toggle" data-id="${x.id}" data-active="${x.is_active}">${x.is_active ? '禁用' : '启用'}</a>
                  <a class="zy-action-link text-orange-500" data-action="reset" data-id="${x.id}">重置密码</a>
                </div>
              </td>
            </tr>
          `;
        })
        .join("");

      renderPagination(data.total || 0, currentPage, totalPages, pageSize);
    }

    root.querySelector("#user_add_btn").addEventListener("click", () => {
      openDrawer(
        "新增会员",
        `
          <div style="font-size: 14px;">
            <div style="margin-bottom: 16px;">
              <label style="display: block; margin-bottom: 6px; color: #374151; font-weight: 500;">用户名（可选）</label>
              <input type="text" id="add_username" class="zy-form-input" style="width: 100%; padding: 8px 12px; border: 1px solid #e5e7eb; border-radius: 6px;" placeholder="留空则自动生成" />
            </div>
            <div style="margin-bottom: 16px;">
              <label style="display: block; margin-bottom: 6px; color: #374151; font-weight: 500;">手机号</label>
              <input type="tel" id="add_phone" class="zy-form-input" style="width: 100%; padding: 8px 12px; border: 1px solid #e5e7eb; border-radius: 6px;" placeholder="请输入手机号" />
            </div>
            <div style="margin-bottom: 16px;">
              <label style="display: block; margin-bottom: 6px; color: #374151; font-weight: 500;">密码</label>
              <input type="password" id="add_password" class="zy-form-input" style="width: 100%; padding: 8px 12px; border: 1px solid #e5e7eb; border-radius: 6px;" placeholder="请输入密码" />
            </div>
            <div style="margin-bottom: 16px;">
              <label style="display: block; margin-bottom: 6px; color: #374151; font-weight: 500;">确认密码</label>
              <input type="password" id="add_confirm_password" class="zy-form-input" style="width: 100%; padding: 8px 12px; border: 1px solid #e5e7eb; border-radius: 6px;" placeholder="请确认密码" />
            </div>
            <div style="margin-bottom: 16px;">
              <label style="display: block; margin-bottom: 6px; color: #374151; font-weight: 500;">会员状态</label>
              <select id="add_is_active" class="zy-select" style="width: 100%; padding: 8px 12px; border: 1px solid #e5e7eb; border-radius: 6px;">
                <option value="true">启用</option>
                <option value="false">禁用</option>
              </select>
            </div>
          </div>
        `,
        `<button class="zy-btn zy-btn-secondary zy-btn-sm" id="drawer_cancel">取消</button><button class="zy-btn zy-btn-primary zy-btn-sm" id="drawer_confirm">创建</button>`
      );
      root.querySelector("#drawer_cancel").addEventListener("click", closeDrawer);
      root.querySelector("#drawer_confirm").addEventListener("click", async () => {
        const username = root.querySelector("#add_username").value.trim();
        const phone = root.querySelector("#add_phone").value.trim();
        const password = root.querySelector("#add_password").value;
        const confirmPassword = root.querySelector("#add_confirm_password").value;
        const isActive = root.querySelector("#add_is_active").value === "true";

        if (!phone) {
          showToast({ title: "提示", message: "请输入手机号", type: "warning" });
          return;
        }
        if (!/^1[3-9]\d{9}$/.test(phone)) {
          showToast({ title: "提示", message: "手机号格式不正确", type: "warning" });
          return;
        }
        if (!password) {
          showToast({ title: "提示", message: "请输入密码", type: "warning" });
          return;
        }
        if (password.length < 6) {
          showToast({ title: "提示", message: "密码长度不能少于6位", type: "warning" });
          return;
        }
        if (password !== confirmPassword) {
          showToast({ title: "提示", message: "两次密码输入不一致", type: "warning" });
          return;
        }

        try {
          await authFetch("/api/admin/registered-users", {
            method: "POST",
            body: JSON.stringify({
              username,
              phone,
              password,
              is_active: isActive
            }),
          });
          showToast({ title: "操作成功", message: "新增会员成功", type: "success" });
          closeDrawer();
          await loadList();
        } catch (err) {
          showToast({ title: "操作失败", message: err.message, type: "error" });
        }
      });
    });

    root.addEventListener("click", async (e) => {
      const btn = e.target.closest("[data-action]");
      if (!btn) return;
      const action = btn.getAttribute("data-action");
      const id = btn.getAttribute("data-id");
      if (!action || !id) return;

      e.preventDefault();

      if (action === "detail") {
        const item = (await authFetch(`/api/admin/registered-users/${id}`, { method: "GET" }));
        openDrawer(
          "会员详情",
          `
            <div style="display: grid; grid-template-columns: 100px 1fr; gap: 16px; font-size: 14px;">
              <span style="color: #6b7280;">用户名</span>
              <span style="color: #1f2937;">${item.username || "-"}</span>
              <span style="color: #6b7280;">手机号</span>
              <span style="color: #1f2937;">${item.phone || "-"}</span>
              <span style="color: #6b7280;">状态</span>
              <span style="color: #1f2937;">${item.is_active ? '启用' : '禁用'}</span>
              <span style="color: #6b7280;">注册时间</span>
              <span style="color: #1f2937;">${formatDateTime(item.date_joined)}</span>
              <span style="color: #6b7280;">最后登录</span>
              <span style="color: #1f2937;">${formatDateTime(item.last_login)}</span>
            </div>
          `,
          `<button class="zy-btn zy-btn-secondary zy-btn-sm" id="drawer_close_btn">关闭</button>`
        );
        root.querySelector("#drawer_close_btn").addEventListener("click", closeDrawer);
        return;
      }

      if (action === "toggle") {
        const isActive = btn.getAttribute("data-active") === "true";
        openDrawer(
          isActive ? "禁用会员" : "启用会员",
          `<p style="color: #374151; line-height: 1.6;">确定要${isActive ? "禁用" : "启用"}该会员吗？</p>`,
          `<button class="zy-btn zy-btn-secondary zy-btn-sm" id="drawer_cancel">取消</button><button class="zy-btn zy-btn-primary zy-btn-sm" id="drawer_confirm">确定</button>`
        );
        root.querySelector("#drawer_cancel").addEventListener("click", closeDrawer);
        root.querySelector("#drawer_confirm").addEventListener("click", async () => {
          closeDrawer();
          try {
            await authFetch(`/api/admin/registered-users/${id}`, {
              method: "PATCH",
              body: JSON.stringify({ is_active: !isActive }),
            });
            showToast({ title: "操作成功", message: `会员已${isActive ? "禁用" : "启用"}`, type: "success" });
            await loadList();
          } catch (err) {
            showToast({ title: "操作失败", message: err.message, type: "error" });
          }
        });
        return;
      }

      if (action === "reset") {
        openDrawer(
          "重置密码",
          `<p style="color: #374151; margin-bottom: 16px;">确定要重置该会员密码吗？</p><p style="color: #6b7280; font-size: 13px;">重置后密码将设置为手机号后6位</p>`,
          `<button class="zy-btn zy-btn-secondary zy-btn-sm" id="drawer_cancel">取消</button><button class="zy-btn zy-btn-primary zy-btn-sm" id="drawer_confirm">重置</button>`
        );
        root.querySelector("#drawer_cancel").addEventListener("click", closeDrawer);
        root.querySelector("#drawer_confirm").addEventListener("click", async () => {
          closeDrawer();
          try {
            const result = await authFetch(`/api/admin/registered-users/${id}/reset-password`, { method: "POST" });
            showToast({ title: "操作成功", message: `会员密码重置成功，新密码: ${result.new_password}`, type: "success" });
            await loadList();
          } catch (err) {
            showToast({ title: "操作失败", message: err.message, type: "error" });
          }
        });
        return;
      }
    });

    root.querySelector("#user_reload_btn").addEventListener("click", () => {
      currentPage = 1;
      loadList();
    });
    root.querySelector("#user_reset_btn").addEventListener("click", () => {
      root.querySelector("#user_q_search").value = "";
      root.querySelector("#phone_search").value = "";
      root.querySelector("#date_search").value = "";
      root.querySelector("#user_status_filter").value = "";
      currentPage = 1;
      loadList();
    });
    root.querySelector("#user_q_search").addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        currentPage = 1;
        loadList();
      }
    });
    root.querySelector("#phone_search").addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        currentPage = 1;
        loadList();
      }
    });
    await loadList();
  },
};
