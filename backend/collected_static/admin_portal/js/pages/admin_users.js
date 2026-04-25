window.AdminPortalPages["admin_users"] = {
  render: async function (root, token) {
    root.innerHTML = `
      <div class="zy-card">
        <div class="zy-card-body">
          <div class="zy-search-bar">
            <div class="zy-search-item">
              <label class="zy-search-label">关键词</label>
              <input type="search" id="admin_search" placeholder="用户名、姓名、邮箱" class="zy-form-input zy-search-control-lg" />
            </div>
            <div class="zy-search-item">
              <label class="zy-search-label">账号状态</label>
              <select id="admin_status_filter" class="zy-select zy-search-control-sm">
                <option value="">全部状态</option>
                <option value="active">启用</option>
                <option value="inactive">禁用</option>
              </select>
            </div>
            <div class="zy-search-actions">
              <button id="admin_reset_btn" class="zy-btn zy-btn-reset zy-btn-sm">重置</button>
              <button id="admin_reload_btn" class="zy-btn zy-btn-query zy-btn-sm">查询</button>
            </div>
          </div>
          <div class="zy-list-actions-row">
            <button id="admin_add_btn" type="button" class="zy-btn zy-btn-primary zy-btn-sm">新增管理员</button>
          </div>
          <table class="zy-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>用户名</th>
                <th>姓名</th>
                <th>邮箱</th>
                <th>超级管理员</th>
                <th>状态</th>
                <th>注册时间</th>
                <th>最后登录</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody id="admin_tbody"></tbody>
          </table>
          <div id="admin_pagination" class="zy-pagination"></div>
        </div>
      </div>

      <!-- 右侧抽屉 -->
      <div id="admin_drawer_overlay" class="zy-drawer-overlay">
        <div class="zy-drawer">
          <div class="zy-drawer-header">
            <h3 class="zy-drawer-title" id="drawer_title">新增</h3>
            <button class="zy-drawer-close" id="drawer_close">&times;</button>
          </div>
          <div class="zy-drawer-body">
            <form id="admin_form">
              <div class="zy-form-group">
                <label class="zy-form-label">用户名 *</label>
                <input type="text" name="username" class="zy-form-input" required />
              </div>
              <div class="zy-form-group" id="password_field">
                <label class="zy-form-label">密码 *</label>
                <input type="password" name="password" class="zy-form-input" />
              </div>
              <div class="zy-form-group">
                <label class="zy-form-label">姓名</label>
                <input type="text" name="first_name" class="zy-form-input" />
              </div>
              <div class="zy-form-group">
                <label class="zy-form-label">邮箱</label>
                <input type="email" name="email" class="zy-form-input" />
              </div>
              <div class="zy-form-group">
                <label class="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" name="is_superuser" class="w-4 h-4" />
                  <span class="text-sm">超级管理员</span>
                </label>
              </div>
              <div class="zy-form-group hidden" id="is_active_field">
                <label class="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" name="is_active" class="w-4 h-4" checked />
                  <span class="text-sm">启用</span>
                </label>
              </div>
              <input type="hidden" name="edit_id" value="" />
            </form>
          </div>
          <div class="zy-drawer-footer">
            <button id="drawer_cancel" class="zy-btn zy-btn-secondary zy-btn-sm">取消</button>
            <button id="drawer_submit" class="zy-btn zy-btn-primary zy-btn-sm">保存</button>
          </div>
        </div>
      </div>
    `;

    let editingId = null;
    let lastItems = [];
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

    function renderPagination(total, page, totalPages, pageSize) {
      window.renderAdminPagination({
        root,
        containerSelector: "#admin_pagination",
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

    async function loadList() {
      try {
        const search = root.querySelector("#admin_search").value.trim();
        const statusFilter = root.querySelector("#admin_status_filter").value;

        const params = new URLSearchParams();
        params.append("page", currentPage);
        params.append("page_size", pageSize);
        if (search) params.append("search", search);
        if (statusFilter) params.append("status", statusFilter);

        const data = await authFetch(`/api/admin/admin-users?${params.toString()}`, { method: "GET" });
        let items = data.items || [];
        totalPages = data.total_pages || 1;

        lastItems = items;
        const tbody = root.querySelector("#admin_tbody");

        if (items.length === 0) {
          tbody.innerHTML = adminTableEmptyRow(9);
          renderPagination(data.total || 0, currentPage, totalPages, pageSize);
          return;
        }

        tbody.innerHTML = items
          .map((x) => {
            return `
              <tr>
                <td>${x.id}</td>
                <td>${x.username || ""}</td>
                <td>${x.first_name || "-"}</td>
                <td>${x.email || "-"}</td>
                <td>${x.is_superuser ? '<span class="zy-badge zy-badge-primary">是</span>' : '<span class="zy-badge zy-badge-info">否</span>'}</td>
                <td>${x.is_active ? '<span class="zy-badge zy-badge-success">启用</span>' : '<span class="zy-badge zy-badge-danger">禁用</span>'}</td>
                <td>${formatDateTime(x.date_joined)}</td>
                <td>${formatDateTime(x.last_login)}</td>
                <td>
                  <div class="zy-actions">
                    <a class="zy-action-link" data-action="edit" data-id="${x.id}" data-username="${x.username}" data-first_name="${x.first_name || ''}" data-email="${x.email || ''}" data-is_superuser="${x.is_superuser}" data-is_active="${x.is_active}">编辑</a>
                    <a class="zy-action-link zy-action-link--danger" data-action="delete" data-id="${x.id}">删除</a>
                  </div>
                </td>
              </tr>
            `;
          })
          .join("");

        renderPagination(data.total || 0, currentPage, totalPages, pageSize);
      } catch (e) {
        const tbody = root.querySelector("#admin_tbody");
        tbody.innerHTML = adminTableErrorRow(9, `加载失败：${e.message || ""}`);
      }
    }

    function openDrawer(isEdit = false, data = {}) {
      editingId = isEdit ? data.id : null;
      root.querySelector("#drawer_title").textContent = isEdit ? "编辑用户" : "新增用户";
      const pw = root.querySelector("#password_field");
      const act = root.querySelector("#is_active_field");
      if (pw) {
        if (isEdit) pw.classList.add("hidden");
        else pw.classList.remove("hidden");
      }
      if (act) {
        if (isEdit) act.classList.remove("hidden");
        else act.classList.add("hidden");
      }
      
      const form = root.querySelector("#admin_form");
      form.reset();
      
      if (isEdit) {
        form.querySelector('[name="username"]').value = data.username || "";
        form.querySelector('[name="first_name"]').value = data.first_name || "";
        form.querySelector('[name="email"]').value = data.email || "";
        form.querySelector('[name="is_superuser"]').checked = data.is_superuser === "true" || data.is_superuser === true;
        form.querySelector('[name="is_active"]').checked = data.is_active === "true" || data.is_active === true;
      }
      
      root.querySelector("#admin_drawer_overlay").classList.add("active");
    }

    function closeDrawer() {
      root.querySelector("#admin_drawer_overlay").classList.remove("active");
    }

    root.querySelector("#admin_add_btn").addEventListener("click", () => openDrawer(false));

    root.querySelector("#drawer_close").addEventListener("click", closeDrawer);
    root.querySelector("#drawer_cancel").addEventListener("click", closeDrawer);

    root.querySelector("#admin_drawer_overlay").addEventListener("click", (e) => {
      if (e.target === root.querySelector("#admin_drawer_overlay")) {
        closeDrawer();
      }
    });

    root.querySelector("#drawer_submit").addEventListener("click", async () => {
      const form = root.querySelector("#admin_form");
      const formData = new FormData(form);
      const payload = {
        username: formData.get("username"),
        first_name: formData.get("first_name"),
        email: formData.get("email"),
        is_superuser: formData.get("is_superuser") === "on",
      };

      try {
        if (editingId) {
          payload.is_active = formData.get("is_active") === "on";
          await authFetch(`/api/admin/admin-users/${editingId}`, {
            method: "PATCH",
            body: JSON.stringify(payload),
          });
        } else {
          payload.password = formData.get("password");
          await authFetch("/api/admin/admin-users", {
            method: "POST",
            body: JSON.stringify(payload),
          });
        }
        closeDrawer();
        await loadList();
      } catch (e) {
        showError("保存失败：" + e.message);
      }
    });

    root.addEventListener("click", async (e) => {
      const btn = e.target.closest("[data-action]");
      if (!btn) return;
      const action = btn.getAttribute("data-action");
      const id = btn.getAttribute("data-id");
      if (!action || !id) return;

      if (action === "edit") {
        openDrawer(true, {
          id: id,
          username: btn.getAttribute("data-username"),
          first_name: btn.getAttribute("data-first_name"),
          email: btn.getAttribute("data-email"),
          is_superuser: btn.getAttribute("data-is_superuser"),
          is_active: btn.getAttribute("data-is_active"),
        });
      } else if (action === "delete") {
        // 保存 loadList 函数的引用
        const refreshList = loadList;
        
        showConfirm({
          title: "确认删除",
          message: "确定要删除该管理员吗？删除后不可恢复。",
          confirmText: "删除",
          cancelText: "取消",
          type: "warning",
          onConfirm: async () => {
            try {
              await authFetch(`/api/admin/admin-users/${id}`, { method: "DELETE" });
              await refreshList();
            } catch (e) {
              showError("删除失败：" + e.message);
            }
          }
        });
      }
    });

    const debouncedAdminSearch =
      typeof window.adminDebounce === "function"
        ? window.adminDebounce(() => {
            currentPage = 1;
            loadList();
          }, 300)
        : () => {
            currentPage = 1;
            loadList();
          };
    root.querySelector("#admin_search").addEventListener("input", debouncedAdminSearch);

    root.querySelector("#admin_reload_btn").addEventListener("click", () => {
      currentPage = 1;
      loadList();
    });
    root.querySelector("#admin_reset_btn").addEventListener("click", () => {
      root.querySelector("#admin_search").value = "";
      root.querySelector("#admin_status_filter").value = "";
      currentPage = 1;
      loadList();
    });
    root.querySelector("#admin_search").addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        currentPage = 1;
        loadList();
      }
    });
    await loadList();
  },
};
