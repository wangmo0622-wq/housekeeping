/**
 * 分类管理：左侧一级分类列表 + 右侧二级分类表格（常见后台主从布局）
 */
window.AdminPortalPages["categories"] = {
  render: async function (root, token) {
    root.innerHTML = `
      <div class="zy-card">
        <div class="zy-card-body">
          <div class="cat-admin-filter-inline">
            <div class="zy-search-item">
              <label class="zy-search-label">筛选一级</label>
              <input type="search" id="cat_sidebar_filter" class="zy-form-input zy-search-control-md" placeholder="输入名称过滤…" />
            </div>
          </div>
          <div class="zy-list-actions-row">
            <button id="cat_create_root_btn" type="button" class="zy-btn zy-btn-primary zy-btn-sm">新增一级分类</button>
          </div>

          <div class="cat-admin-layout">
            <aside class="cat-admin-sidebar" aria-label="一级分类">
              <div class="cat-admin-sidebar-head">
                <span class="text-xs text-gray-500">点击左侧选择一级分类，右侧管理其子类</span>
              </div>
              <div id="cat_sidebar_list" class="cat-admin-sidebar-list"></div>
            </aside>
            <main class="cat-admin-main" id="cat_main_panel">
              <div id="cat_main_inner" class="cat-admin-main-empty">加载中…</div>
            </main>
          </div>
        </div>
      </div>

      <div id="cat_drawer_overlay" class="zy-drawer-overlay">
        <div class="zy-drawer">
          <div class="zy-drawer-header">
            <h3 class="zy-drawer-title" id="cat_drawer_title">新增分类</h3>
            <button class="zy-drawer-close" id="cat_drawer_close" type="button">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-5 h-5">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>

          <div class="zy-drawer-body">
            <form id="cat_form">
              <div class="zy-form-group">
                <label class="zy-form-label">分类名称 <span class="text-red-500">*</span></label>
                <input type="text" name="name" class="zy-form-input" placeholder="请输入分类名称" required />
              </div>

              <div class="zy-form-group">
                <label class="zy-form-label">父级分类</label>
                <select name="parent_id" class="zy-select" id="cat_parent_select">
                  <option value="">无（作为一级分类）</option>
                </select>
                <p class="text-xs text-gray-500 mt-1">最多两级：一级根 + 二级子类</p>
              </div>

              <div class="zy-form-group">
                <label class="zy-form-label">排序</label>
                <input type="number" name="sort_order" class="zy-form-input" value="0" min="0" />
                <p class="text-xs text-gray-500 mt-1">数字越小排序越靠前</p>
              </div>
            </form>
          </div>

          <div class="zy-drawer-footer">
            <button type="button" class="zy-btn zy-btn-secondary" id="cat_cancel_btn">取消</button>
            <button type="button" class="zy-btn zy-btn-primary" id="cat_submit_btn">确定</button>
          </div>
        </div>
      </div>
    `;

    const sidebarListEl = root.querySelector("#cat_sidebar_list");
    const mainInnerEl = root.querySelector("#cat_main_inner");
    const filterInput = root.querySelector("#cat_sidebar_filter");

    let categoryTree = [];
    let editingId = null;
    let editingIsRoot = true;
    let parentLocked = true;
    let selectedRootId = null;

    function statusLabel(st) {
      if (st === "disabled") return '<span class="zy-badge zy-badge-danger">停用</span>';
      return '<span class="zy-badge zy-badge-success">启用</span>';
    }

    function closeDrawer() {
      root.querySelector("#cat_drawer_overlay").classList.remove("active");
      editingId = null;
      editingIsRoot = true;
      parentLocked = true;
    }

    function openDrawer({ isEdit, mode, id, name, parent_id, sort_order }) {
      const title = root.querySelector("#cat_drawer_title");
      const form = root.querySelector("#cat_form");
      form.reset();

      root.querySelector('[name="name"]').value = name || "";
      root.querySelector('[name="sort_order"]').value = sort_order || 0;
      root.querySelector('[name="parent_id"]').value = parent_id ? String(parent_id) : "";

      editingId = isEdit ? id : null;
      editingIsRoot = mode === "root";

      const parentSelect = root.querySelector("#cat_parent_select");
      if (parentSelect) {
        parentLocked = mode !== "root";
        parentSelect.disabled = mode === "root";
      }

      if (!isEdit) {
        title.textContent = mode === "root" ? "新增一级分类" : "新增二级分类";
      } else {
        title.textContent = mode === "root" ? "编辑一级分类" : "编辑二级分类";
      }

      root.querySelector("#cat_drawer_overlay").classList.add("active");
    }

    function renderParentOptions() {
      const select = root.querySelector("#cat_parent_select");
      if (!select) return;

      select.innerHTML = '<option value="">无（作为一级分类）</option>';
      (categoryTree || []).forEach((r) => {
        const opt = document.createElement("option");
        opt.value = String(r.id);
        opt.textContent = `${r.name} (ID: ${r.id})`;
        select.appendChild(opt);
      });
    }

    function filteredRoots() {
      const q = (filterInput && filterInput.value) ? filterInput.value.trim().toLowerCase() : "";
      const roots = categoryTree || [];
      if (!q) return roots;
      return roots.filter((r) => (r.name || "").toLowerCase().includes(q));
    }

    function ensureSelection() {
      const roots = filteredRoots();
      if (!roots.length) {
        selectedRootId = null;
        return;
      }
      const still = roots.some((r) => String(r.id) === String(selectedRootId));
      if (!still) selectedRootId = roots[0].id;
    }

    function renderSidebar() {
      if (!sidebarListEl) return;
      const roots = filteredRoots();
      if (!roots.length) {
        sidebarListEl.innerHTML = `<div class="zy-empty-hint zy-empty-hint--tight">暂无匹配的一级分类</div>`;
        return;
      }
      sidebarListEl.innerHTML = roots
        .map((r) => {
          const active = String(r.id) === String(selectedRootId) ? " active" : "";
          const nChild = (r.children || []).length;
          return `
            <button type="button" class="cat-admin-sidebar-item${active}" data-root-id="${r.id}">
              <span class="cat-admin-sidebar-name">
                <span class="cat-admin-sidebar-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 7h7v10H3z"></path>
                    <path d="M14 7h7v4h-7z"></path>
                    <path d="M14 15h7v2h-7z"></path>
                  </svg>
                </span>
                <span>${r.name}</span>
              </span>
              <span class="cat-admin-sidebar-meta">ID ${r.id} · 排序 ${r.sort_order || 0} · ${nChild} 个子类 · ${statusLabel(r.status)}</span>
            </button>
          `;
        })
        .join("");
    }

    function renderMain() {
      ensureSelection();
      renderSidebar();

      if (!mainInnerEl) return;
      const rootNode = (categoryTree || []).find((r) => String(r.id) === String(selectedRootId));
      if (!rootNode) {
        mainInnerEl.className = "cat-admin-main-empty";
        const msg =
          (categoryTree || []).length === 0
            ? "暂无分类，请先新增一级分类"
            : "请从左侧选择一个一级分类";
        mainInnerEl.innerHTML = `<div class="zy-empty-hint zy-empty-hint--tight">${msg}</div>`;
        return;
      }

      const children = rootNode.children || [];
      const childRows = children.length
        ? children
            .map(
              (c) => `
            <tr>
              <td class="font-semibold">${c.name} <span class="text-xs text-gray-500">ID: ${c.id}</span></td>
              <td>${c.sort_order || 0}</td>
              <td>${statusLabel(c.status)}</td>
              <td>
                <div class="zy-actions">
                  <a class="zy-action-link" href="#" data-action="edit_child" data-id="${c.id}" data-parent-id="${rootNode.id}">编辑</a>
                  <a class="zy-action-link zy-action-link--danger" href="#" data-action="delete" data-id="${c.id}" data-name="${c.name.replace(/"/g, "&quot;")}">删除</a>
                </div>
              </td>
            </tr>
          `
            )
            .join("")
        : adminTableEmptyRow(4, "暂无二级分类，可点击「新增二级」添加");

      mainInnerEl.className = "";
      mainInnerEl.innerHTML = `
        <div class="cat-admin-main-toolbar">
          <div>
            <div class="cat-admin-main-title">${rootNode.name} <span class="text-sm font-normal text-gray-500">(一级 ID: ${rootNode.id})</span></div>
            <div class="text-xs text-gray-500 mt-1">排序 ${rootNode.sort_order || 0} · ${statusLabel(rootNode.status)}</div>
          </div>
          <div class="cat-admin-main-actions">
            <a class="zy-action-link" href="#" data-action="add_child" data-parent-id="${rootNode.id}">新增二级</a>
            <a class="zy-action-link" href="#" data-action="edit_root" data-id="${rootNode.id}">编辑一级</a>
            <a class="zy-action-link zy-action-link--danger" href="#" data-action="delete" data-id="${rootNode.id}" data-name="${(rootNode.name || "").replace(/"/g, "&quot;")}">删除一级</a>
          </div>
        </div>
        <div class="zy-table-scroll">
          <table class="zy-table">
            <thead>
              <tr>
                <th>二级分类</th>
                <th>排序</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>${childRows}</tbody>
          </table>
        </div>
      `;
    }

    async function loadTree() {
      const data = await authFetch("/api/admin/categories/tree", { method: "GET" });
      categoryTree = data.tree || [];
      renderParentOptions();
      ensureSelection();
      renderMain();
    }

    root.querySelector("#cat_drawer_close").addEventListener("click", closeDrawer);
    root.querySelector("#cat_cancel_btn").addEventListener("click", closeDrawer);
    root.querySelector("#cat_drawer_overlay").addEventListener("click", (e) => {
      if (e.target === root.querySelector("#cat_drawer_overlay")) closeDrawer();
    });

    root.querySelector("#cat_create_root_btn").addEventListener("click", () => {
      openDrawer({ isEdit: false, mode: "root", id: null, name: "", parent_id: null, sort_order: 0 });
    });

    const debouncedFilter =
      typeof window.adminDebounce === "function"
        ? window.adminDebounce(() => {
            renderMain();
          }, 200)
        : () => renderMain();

    if (filterInput) {
      filterInput.addEventListener("input", debouncedFilter);
    }

    sidebarListEl.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-root-id]");
      if (!btn) return;
      e.preventDefault();
      selectedRootId = btn.getAttribute("data-root-id");
      renderMain();
    });

    root.querySelector("#cat_submit_btn").addEventListener("click", async () => {
      const form = root.querySelector("#cat_form");
      const name = form.querySelector('[name="name"]').value.trim();
      const parentId = form.querySelector('[name="parent_id"]').value;
      const sortOrder = form.querySelector('[name="sort_order"]').value;

      if (!name) {
        showAlert("请输入分类名称", "提示", "warning");
        return;
      }

      const payload = {
        name,
        parent_id: parentId ? parseInt(parentId, 10) : null,
        sort_order: parseInt(sortOrder || "0", 10),
      };

      try {
        if (editingId) {
          await authFetch(`/api/admin/categories/${editingId}`, {
            method: "PATCH",
            body: JSON.stringify(payload),
          });
        } else {
          await authFetch("/api/admin/categories", {
            method: "POST",
            body: JSON.stringify(payload),
          });
        }
        closeDrawer();
        await loadTree();
        showToast({ title: "操作成功", message: "分类保存成功", type: "success" });
      } catch (e) {
        showError("保存失败：" + (e.message || String(e)));
      }
    });

    mainInnerEl.addEventListener("click", async (e) => {
      const btn = e.target.closest("[data-action]");
      if (!btn) return;
      e.preventDefault();

      const action = btn.getAttribute("data-action");
      const id = btn.getAttribute("data-id");
      const name = btn.getAttribute("data-name");
      const parentId = btn.getAttribute("data-parent-id");

      if (action === "add_child") {
        openDrawer({
          isEdit: false,
          mode: "child",
          id: null,
          name: "",
          parent_id: parentId,
          sort_order: 0,
        });
        return;
      }

      if (action === "edit_root") {
        const r = categoryTree.find((x) => String(x.id) === String(id));
        openDrawer({
          isEdit: true,
          mode: "root",
          id,
          name: r?.name || "",
          parent_id: null,
          sort_order: r?.sort_order || 0,
        });
        return;
      }

      if (action === "edit_child") {
        const r = categoryTree.find((x) => String(x.id) === String(parentId));
        const c = (r?.children || []).find((ch) => String(ch.id) === String(id));
        openDrawer({
          isEdit: true,
          mode: "child",
          id,
          name: c?.name || "",
          parent_id: parentId,
          sort_order: c?.sort_order || 0,
        });
        return;
      }

      if (action === "delete") {
        showConfirm({
          title: "确认删除",
          message: `确定要删除分类 "${name}" 吗？<br><span class="text-red-500 text-sm">注意：如果该分类下有子分类、服务类型或服务发布，将无法删除。</span>`,
          confirmText: "删除",
          cancelText: "取消",
          type: "warning",
          onConfirm: async () => {
            try {
              await authFetch(`/api/admin/categories/${id}`, { method: "DELETE" });
              showToast({ title: "操作成功", message: "分类已删除", type: "success" });
              if (String(selectedRootId) === String(id)) selectedRootId = null;
              await loadTree();
            } catch (e2) {
              showError(e2.message || "删除失败");
            }
          },
        });
      }
    });

    await loadTree();
  },
};
