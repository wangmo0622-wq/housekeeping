window.AdminPortalPages["menus"] = {
  render: async function (root) {
    root.innerHTML = `
      <div class="zy-card">
        <div class="zy-card-body">
          <div class="zy-list-actions-row">
            <button id="menu_add_section_btn" class="zy-btn zy-btn-secondary zy-btn-sm">新增分组</button>
            <button id="menu_add_item_btn" class="zy-btn zy-btn-primary zy-btn-sm">新增菜单</button>
          </div>
          <table class="zy-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>名称</th>
                <th>图标</th>
                <th>Key</th>
                <th>路径</th>
                <th>父级</th>
                <th>排序</th>
                <th>显示</th>
                <th>启用</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody id="menu_tbody"></tbody>
          </table>
        </div>
      </div>

      <div id="menu_drawer_overlay" class="zy-drawer-overlay">
        <div class="zy-drawer">
          <div class="zy-drawer-header">
            <h3 class="zy-drawer-title" id="menu_drawer_title">新增菜单</h3>
            <button class="zy-drawer-close" id="menu_drawer_close">&times;</button>
          </div>
          <div class="zy-drawer-body">
            <form id="menu_form">
              <div class="zy-form-group">
                <label class="zy-form-label">名称 *</label>
                <input type="text" name="name" class="zy-form-input" required />
              </div>
              <div class="zy-form-group">
                <label class="zy-form-label">父级菜单</label>
                <select name="parent_id" class="zy-select" id="menu_parent_select">
                  <option value="">无（顶级）</option>
                </select>
              </div>
              <div class="zy-form-group">
                <label class="zy-form-label">页面Key</label>
                <input type="text" name="key" class="zy-form-input" placeholder="如: menus" />
              </div>
              <div class="zy-form-group">
                <label class="zy-form-label">路径</label>
                <input type="text" name="path" class="zy-form-input" placeholder="/admin/menus/" />
              </div>
              <div class="zy-form-group">
                <label class="zy-form-label">图标（来自图标库）</label>
                <input type="hidden" name="icon" id="menu_icon_value" />
                <div class="menu-icon-picker-trigger">
                  <input type="text" id="menu_icon_display" class="zy-form-input" placeholder="请选择图标" readonly />
                  <button type="button" id="menu_icon_open_btn" class="zy-btn zy-btn-secondary zy-btn-sm">选择图标</button>
                  <button type="button" id="menu_icon_clear_btn" class="zy-btn zy-btn-secondary zy-btn-sm">删除图标</button>
                </div>
                <div id="menu_icon_preview" class="text-xs text-gray-500 mt-1">未选择图标</div>
                <div id="menu_icon_panel" class="menu-icon-panel hidden">
                  <div class="menu-icon-panel-header">
                    <input type="search" id="menu_icon_search" class="zy-form-input" placeholder="请输入图标名称" />
                    <button type="button" id="menu_icon_panel_close" class="zy-btn zy-btn-secondary zy-btn-sm">关闭</button>
                  </div>
                  <div id="menu_icon_grid" class="menu-icon-grid"></div>
                </div>
              </div>
              <div class="zy-form-group">
                <label class="zy-form-label">排序</label>
                <input type="number" name="sort_order" class="zy-form-input" value="0" />
              </div>
              <div class="zy-form-group">
                <label class="flex items-center gap-2"><input type="checkbox" name="is_section" /> 分组菜单</label>
              </div>
              <div class="zy-form-group">
                <label class="flex items-center gap-2"><input type="checkbox" name="is_visible" checked /> 显示</label>
              </div>
              <div class="zy-form-group">
                <label class="flex items-center gap-2"><input type="checkbox" name="is_enabled" checked /> 启用</label>
              </div>
              <input type="hidden" name="edit_id" />
            </form>
          </div>
          <div class="zy-drawer-footer">
            <button id="menu_cancel_btn" class="zy-btn zy-btn-secondary zy-btn-sm">取消</button>
            <button id="menu_submit_btn" class="zy-btn zy-btn-primary zy-btn-sm">保存</button>
          </div>
        </div>
      </div>
    `;

    let flatMenus = [];
    let editingId = null;
    let iconKeys = [];

    function normalizeIconKey(raw) {
      let s = String(raw || "").trim();
      if (!s) return "";
      s = s.replace(/\\/g, "/");
      if (s.includes("/")) s = s.split("/").pop() || "";
      s = s.replace(/\.svg$/i, "");
      return s.trim();
    }

    function flatten(items, parentName = "—", acc = []) {
      (items || []).forEach((m) => {
        acc.push({
          id: m.id,
          name: m.name,
          key: m.key || "",
          icon: normalizeIconKey(m.icon || ""),
          path: m.path || "",
          parent_id: m.parent_id,
          parent_name: parentName,
          sort_order: m.sort_order || 0,
          is_visible: !!m.is_visible,
          is_enabled: !!m.is_enabled,
          is_section: !!m.is_section,
          children: m.children || [],
        });
        if (m.children && m.children.length) flatten(m.children, m.name, acc);
      });
      return acc;
    }

    async function loadMenus() {
      const data = await authFetch("/api/admin/menus?manage=1", { method: "GET" });
      flatMenus = flatten(data.items || []);
      renderTable();
      renderParentOptions();
      if (typeof window.refreshAdminMenus === "function") {
        await window.refreshAdminMenus();
      }
    }

    async function loadIconKeys() {
      try {
        const resp = await fetch("/static/admin_portal/icons/index.json");
        const data = await resp.json();
        iconKeys = Array.isArray(data.icons) ? data.icons : [];
      } catch (_e) {
        iconKeys = [];
      }
      const select = root.querySelector("#menu_icon_select");
      const grid = root.querySelector("#menu_icon_grid");
      if (!grid) return;
      const html = iconKeys
        .map(
          (k) => `
            <button type="button" class="menu-icon-item" data-icon-key="${k}" title="${k}">
              <img src="/static/admin_portal/icons/svg/${k}.svg" alt="" onerror="this.style.display='none'" />
              <span>${k}</span>
            </button>
          `
        )
        .join("");
      grid.innerHTML = html || '<div class="text-gray-500 text-sm">未加载到图标</div>';
    }

    function renderTable() {
      const tbody = root.querySelector("#menu_tbody");
      if (!flatMenus.length) {
        tbody.innerHTML = adminTableEmptyRow(10, "暂无菜单");
        return;
      }
      tbody.innerHTML = flatMenus
        .map((m) => {
          return `
            <tr>
              <td>${m.id}</td>
              <td>${m.name}${m.is_section ? ' <span class="zy-badge zy-badge-info">分组</span>' : ""}</td>
              <td>${m.icon ? `<img src="/static/admin_portal/icons/svg/${m.icon}.svg" alt="" style="width:16px;height:16px;vertical-align:middle;" title="${m.icon}" onerror="this.outerHTML='-'" />` : "-"}</td>
              <td>${m.key || "-"}</td>
              <td>${m.path || "-"}</td>
              <td>${m.parent_name || "—"}</td>
              <td>${m.sort_order}</td>
              <td>${m.is_visible ? '<span class="zy-badge zy-badge-success">是</span>' : '<span class="zy-badge zy-badge-danger">否</span>'}</td>
              <td>${m.is_enabled ? '<span class="zy-badge zy-badge-success">是</span>' : '<span class="zy-badge zy-badge-danger">否</span>'}</td>
              <td>
                <div class="zy-actions">
                  <a class="zy-action-link" data-action="edit" data-id="${m.id}">编辑</a>
                  <a class="zy-action-link zy-action-link--danger" data-action="delete" data-id="${m.id}">删除</a>
                </div>
              </td>
            </tr>
          `;
        })
        .join("");
    }

    function renderParentOptions() {
      const select = root.querySelector("#menu_parent_select");
      select.innerHTML = '<option value="">无（顶级）</option>';
      flatMenus
        .filter((m) => !!m.is_section)
        .forEach((m) => {
        const opt = document.createElement("option");
        opt.value = String(m.id);
        opt.textContent = `${m.name} (ID:${m.id})`;
        select.appendChild(opt);
      });
    }

    function openDrawer(mode, menu) {
      const form = root.querySelector("#menu_form");
      form.reset();
      editingId = menu ? menu.id : null;
      root.querySelector("#menu_drawer_title").textContent = editingId ? "编辑菜单" : "新增菜单";
      if (mode === "section") {
        form.querySelector('[name="is_section"]').checked = true;
      }
      if (menu) {
        form.querySelector('[name="name"]').value = menu.name || "";
        form.querySelector('[name="key"]').value = menu.key || "";
        form.querySelector('[name="path"]').value = menu.path || "";
        form.querySelector('[name="icon"]').value = normalizeIconKey(menu.icon || "");
        form.querySelector('[name="sort_order"]').value = menu.sort_order || 0;
        form.querySelector('[name="parent_id"]').value = menu.parent_id ? String(menu.parent_id) : "";
        form.querySelector('[name="is_section"]').checked = !!menu.is_section;
        form.querySelector('[name="is_visible"]').checked = !!menu.is_visible;
        form.querySelector('[name="is_enabled"]').checked = !!menu.is_enabled;
      }
      updateIconPreview();
      root.querySelector("#menu_drawer_overlay").classList.add("active");
    }

    function closeDrawer() {
      root.querySelector("#menu_drawer_overlay").classList.remove("active");
      editingId = null;
    }

    async function submitForm() {
      const form = root.querySelector("#menu_form");
      const fd = new FormData(form);
      const payload = {
        name: fd.get("name"),
        key: fd.get("key"),
        path: fd.get("path"),
        icon: normalizeIconKey(fd.get("icon")),
        parent_id: fd.get("parent_id") || null,
        sort_order: parseInt(fd.get("sort_order") || "0", 10),
        is_section: fd.get("is_section") === "on",
        is_visible: fd.get("is_visible") === "on",
        is_enabled: fd.get("is_enabled") === "on",
      };
      if (!payload.name) {
        showError("菜单名称必填");
        return;
      }
      if (editingId) {
        await authFetch(`/api/admin/menus/${editingId}`, { method: "PATCH", body: JSON.stringify(payload) });
      } else {
        await authFetch("/api/admin/menus", { method: "POST", body: JSON.stringify(payload) });
      }
      closeDrawer();
      await loadMenus();
    }

    function updateIconPreview() {
      const hiddenInput = root.querySelector("#menu_icon_value");
      const displayInput = root.querySelector("#menu_icon_display");
      const key = normalizeIconKey((hiddenInput && hiddenInput.value) || "");
      if (hiddenInput) hiddenInput.value = key;
      if (displayInput) displayInput.value = key;
      const preview = root.querySelector("#menu_icon_preview");
      if (!preview) return;
      if (!key) {
        preview.innerHTML = "未选择图标";
        return;
      }
      preview.innerHTML = `<img src="/static/admin_portal/icons/svg/${key}.svg" alt="" style="width:16px;height:16px;vertical-align:middle;margin-right:6px;" onerror="this.remove();this.parentElement.innerHTML='图标不存在：${key}'" />${key}`;
    }

    function openIconPanel() {
      root.querySelector("#menu_icon_panel").classList.remove("hidden");
      root.querySelector("#menu_icon_search").focus();
      filterIconGrid();
    }

    function closeIconPanel() {
      root.querySelector("#menu_icon_panel").classList.add("hidden");
    }

    function setIconValue(iconKey) {
      const key = normalizeIconKey(iconKey);
      root.querySelector("#menu_icon_value").value = key;
      updateIconPreview();
    }

    function filterIconGrid() {
      const q = (root.querySelector("#menu_icon_search").value || "").trim().toLowerCase();
      const items = root.querySelectorAll(".menu-icon-item");
      items.forEach((el) => {
        const key = (el.getAttribute("data-icon-key") || "").toLowerCase();
        el.style.display = !q || key.includes(q) ? "" : "none";
      });
    }

    root.querySelector("#menu_add_item_btn").addEventListener("click", () => openDrawer("item"));
    root.querySelector("#menu_add_section_btn").addEventListener("click", () => openDrawer("section"));
    root.querySelector("#menu_drawer_close").addEventListener("click", closeDrawer);
    root.querySelector("#menu_cancel_btn").addEventListener("click", closeDrawer);
    root.querySelector("#menu_submit_btn").addEventListener("click", submitForm);
    root.querySelector("#menu_icon_open_btn").addEventListener("click", openIconPanel);
    root.querySelector("#menu_icon_panel_close").addEventListener("click", closeIconPanel);
    root.querySelector("#menu_icon_clear_btn").addEventListener("click", () => {
      setIconValue("");
      closeIconPanel();
    });
    root.querySelector("#menu_icon_search").addEventListener("input", filterIconGrid);
    root.querySelector("#menu_drawer_overlay").addEventListener("click", (e) => {
      if (e.target === root.querySelector("#menu_drawer_overlay")) closeDrawer();
    });
    root.querySelector("#menu_icon_grid").addEventListener("click", (e) => {
      const btn = e.target.closest(".menu-icon-item");
      if (!btn) return;
      setIconValue(btn.getAttribute("data-icon-key"));
      closeIconPanel();
    });

    root.addEventListener("click", async (e) => {
      const btn = e.target.closest("[data-action]");
      if (!btn) return;
      const action = btn.getAttribute("data-action");
      const id = Number(btn.getAttribute("data-id"));
      const menu = flatMenus.find((x) => x.id === id);
      if (!menu) return;

      if (action === "edit") {
        openDrawer("item", menu);
        return;
      }
      if (action === "delete") {
        try {
          await authFetch(`/api/admin/menus/${id}`, { method: "DELETE" });
          await loadMenus();
          showToast("删除成功", "success");
        } catch (err) {
          showError(err.message || "删除失败");
        }
      }
    });

    await loadIconKeys();
    await loadMenus();
  },
};
