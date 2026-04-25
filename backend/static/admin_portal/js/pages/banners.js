window.AdminPortalPages["banners"] = {
  render: async function (root, token) {
    root.innerHTML = `
      <div class="zy-card">
        <div class="zy-card-body">
          <div class="zy-search-bar">
            <div class="zy-search-item">
              <label class="zy-search-label">关键词</label>
              <input type="search" id="banner_search" placeholder="标题、跳转值" class="zy-form-input zy-search-control-md" />
            </div>
            <div class="zy-search-item">
              <label class="zy-search-label">启用状态</label>
              <select id="banner_status_filter" class="zy-select zy-search-control-sm">
                <option value="">全部状态</option>
                <option value="enabled">启用</option>
                <option value="disabled">停用</option>
              </select>
            </div>
            <div class="zy-search-actions">
              <button id="banner_reset_btn" class="zy-btn zy-btn-reset zy-btn-sm">重置</button>
              <button id="banner_reload_btn" class="zy-btn zy-btn-query zy-btn-sm">查询</button>
            </div>
          </div>
          <div class="zy-list-actions-row">
            <button id="banner_create_btn" type="button" class="zy-btn zy-btn-primary zy-btn-sm">新增</button>
          </div>
          <table class="zy-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>封面</th>
                <th>标题</th>
                <th>跳转类型</th>
                <th>跳转值</th>
                <th>排序</th>
                <th>状态</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody id="banner_tbody"></tbody>
          </table>
          <div id="banner_pagination" class="zy-pagination"></div>
        </div>
      </div>
      <div id="banner_drawer_overlay" class="zy-drawer-overlay">
        <div class="zy-drawer">
          <div class="zy-drawer-header">
            <h3 class="zy-drawer-title" id="banner_drawer_title">新增轮播图</h3>
            <button class="zy-drawer-close" id="banner_drawer_close">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-5 h-5">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
          <div class="zy-drawer-body">
            <form id="banner_form">
              <div class="zy-form-group">
                <label class="zy-form-label">标题</label>
                <input type="text" name="title" class="zy-form-input" placeholder="请输入标题（可选）" />
              </div>
              <div class="zy-form-group">
                <label class="zy-form-label">图片 <span class="text-red-500">*</span></label>
                <div class="zy-upload-area">
                  <input type="file" name="image" id="banner_image_input" accept="image/*" style="display:none" />
                  <div id="banner_image_preview" class="zy-upload-preview">
                    <div class="zy-upload-placeholder" id="banner_upload_placeholder">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-8 h-8 text-gray-400">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                        <circle cx="8.5" cy="8.5" r="1.5"></circle>
                        <polyline points="21 15 16 10 5 21"></polyline>
                      </svg>
                      <span class="text-gray-500 text-sm mt-2">点击上传图片</span>
                    </div>
                    <img id="banner_preview_img" src="" style="display:none;max-width:100%;max-height:200px;border-radius:4px;" />
                  </div>
                  <button type="button" id="banner_upload_btn" class="zy-btn zy-btn-sm zy-btn-secondary mt-2">选择图片</button>
                </div>
              </div>
              <div class="zy-form-group">
                <label class="zy-form-label">跳转类型</label>
                <select name="link_type" class="zy-select">
                  <option value="none">无跳转</option>
                  <option value="category">分类</option>
                  <option value="listing">服务详情</option>
                  <option value="url">网页链接</option>
                </select>
              </div>
              <div class="zy-form-group">
                <label class="zy-form-label">跳转值</label>
                <input type="text" name="link_value" class="zy-form-input" placeholder="分类ID/服务ID/URL" />
              </div>
              <div class="zy-form-group">
                <label class="zy-form-label">排序</label>
                <input type="number" name="sort_order" class="zy-form-input" value="0" placeholder="数字越小越靠前" />
              </div>
              <div class="zy-form-group">
                <label class="zy-form-label">状态</label>
                <select name="status" class="zy-select">
                  <option value="enabled">启用</option>
                  <option value="disabled">停用</option>
                </select>
              </div>
            </form>
          </div>
          <div class="zy-drawer-footer">
            <button type="button" class="zy-btn zy-btn-secondary" id="banner_cancel_btn">取消</button>
            <button type="button" class="zy-btn zy-btn-primary" id="banner_submit_btn">确定</button>
          </div>
        </div>
      </div>
    `;

    function statusBadge(v) {
      const map = {
        enabled: '<span class="zy-badge zy-badge-success">启用</span>',
        disabled: '<span class="zy-badge zy-badge-danger">停用</span>'
      };
      return map[v] || v || "-";
    }

    function linkTypeBadge(v) {
      const map = {
        none: '<span class="zy-badge">无跳转</span>',
        category: '<span class="zy-badge zy-badge-info">分类</span>',
        listing: '<span class="zy-badge zy-badge-info">服务详情</span>',
        url: '<span class="zy-badge zy-badge-info">网页链接</span>'
      };
      return map[v] || v || "-";
    }

    let lastItems = [];
    let editingId = null;
    let currentPage = 1;
    let pageSize = 10;
    let totalPages = 0;
    let currentImageUrl = null;

    const drawerOverlay = root.querySelector("#banner_drawer_overlay");
    const drawerTitle = root.querySelector("#banner_drawer_title");
    const imageInput = root.querySelector("#banner_image_input");
    const previewImg = root.querySelector("#banner_preview_img");
    const placeholder = root.querySelector("#banner_upload_placeholder");

    function openDrawer(isEdit, data) {
      if (isEdit && data) {
        editingId = data.id;
        currentImageUrl = data.image_url || null;
        drawerTitle.textContent = "编辑轮播图";
        const form = root.querySelector("#banner_form");
        form.title.value = data.title || "";
        form.link_type.value = data.link_type || "none";
        form.link_value.value = data.link_value || "";
        form.sort_order.value = data.sort_order || 0;
        form.status.value = data.status || "enabled";
        
        if (data.image_url) {
          previewImg.src = data.image_url;
          previewImg.style.display = "block";
          placeholder.style.display = "none";
        } else {
          previewImg.style.display = "none";
          placeholder.style.display = "flex";
        }
      } else {
        editingId = null;
        currentImageUrl = null;
        drawerTitle.textContent = "新增轮播图";
        const form = root.querySelector("#banner_form");
        form.reset();
        form.sort_order.value = 0;
        form.status.value = "enabled";
        previewImg.style.display = "none";
        placeholder.style.display = "flex";
        imageInput.value = "";
      }
      drawerOverlay.classList.add("active");
    }

    function closeDrawer() {
      drawerOverlay.classList.remove("active");
      editingId = null;
      currentImageUrl = null;
    }

    root.querySelector("#banner_drawer_close").addEventListener("click", closeDrawer);
    root.querySelector("#banner_cancel_btn").addEventListener("click", closeDrawer);
    drawerOverlay.addEventListener("click", (e) => {
      if (e.target === drawerOverlay) closeDrawer();
    });

    root.querySelector("#banner_upload_btn").addEventListener("click", () => {
      imageInput.click();
    });

    root.querySelector("#banner_image_preview").addEventListener("click", () => {
      imageInput.click();
    });

    imageInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (ev) => {
          previewImg.src = ev.target.result;
          previewImg.style.display = "block";
          placeholder.style.display = "none";
        };
        reader.readAsDataURL(file);
      }
    });

    function renderPagination(total, page, totalPages, pageSize) {
      window.renderAdminPagination({
        root,
        containerSelector: "#banner_pagination",
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
      const search = root.querySelector("#banner_search").value.trim();
      const status = root.querySelector("#banner_status_filter").value;

      const params = new URLSearchParams();
      params.append("page", currentPage);
      params.append("page_size", pageSize);
      if (search) params.append("search", search);
      if (status) params.append("status", status);

      const data = await authFetch(`/api/admin/banners?${params.toString()}`, { method: "GET" });
      let items = data.items || [];
      totalPages = data.total_pages || 1;

      lastItems = items;
      const tbody = root.querySelector("#banner_tbody");

      if (items.length === 0) {
        tbody.innerHTML = adminTableEmptyRow(9);
        renderPagination(data.total || 0, currentPage, totalPages, pageSize);
        return;
      }

      tbody.innerHTML = items
        .map((x) => {
          const preview = x.image_url
            ? `<img src="${x.image_url}" style="width:60px;height:40px;object-fit:cover;border-radius:4px;" onerror="this.style.display='none'" />`
            : "-";
          return `
            <tr>
              <td>${x.id}</td>
              <td>${preview}</td>
              <td>${x.title || "-"}</td>
              <td>${linkTypeBadge(x.link_type)}</td>
              <td>${x.link_value || "-"}</td>
              <td>${x.sort_order}</td>
              <td>${statusBadge(x.status)}</td>
              <td>${x.created_at || ""}</td>
              <td>
                <div class="zy-actions">
                  <a class="zy-action-link" data-action="edit" data-id="${x.id}">编辑</a>
                  <a class="zy-action-link ${x.status === 'enabled' ? 'zy-action-link--danger' : 'zy-action-link--success'}" data-action="toggle" data-id="${x.id}">
                    ${x.status === 'enabled' ? '停用' : '启用'}
                  </a>
                  <a class="zy-action-link zy-action-link--danger" data-action="delete" data-id="${x.id}">删除</a>
                </div>
              </td>
            </tr>
          `;
        })
        .join("");

      renderPagination(data.total || 0, currentPage, totalPages, pageSize);
    }

    root.addEventListener("click", async (e) => {
      const btn = e.target.closest("[data-action]");
      if (!btn) return;
      const action = btn.getAttribute("data-action");
      const id = btn.getAttribute("data-id");
      if (!action || !id) return;

      if (action === "toggle") {
        const target = lastItems.find((t) => String(t.id) === String(id));
        const nextStatus = target?.status === "enabled" ? "disabled" : "enabled";
        await authFetch(`/api/admin/banners/${id}`, {
          method: "PATCH",
          body: JSON.stringify({ status: nextStatus }),
        });
        await loadList();
        return;
      }

      if (action === "edit") {
        const target = lastItems.find((t) => String(t.id) === String(id));
        if (!target) return;
        openDrawer(true, target);
        return;
      }

      if (action === "delete") {
        showConfirm({
          title: "确认删除",
          message: "确定要删除这条轮播图吗？",
          confirmText: "删除",
          cancelText: "取消",
          type: "warning",
          onConfirm: async () => {
            try {
              await authFetch(`/api/admin/banners/${id}`, { method: "DELETE" });
              showToast({ title: "操作成功", message: "轮播图已删除", type: "success" });
              await loadList();
            } catch (err) {
              showToast({ title: "操作失败", message: err.message || "删除失败", type: "error" });
            }
          },
        });
      }
    });

    const debouncedBannerSearch =
      typeof window.adminDebounce === "function"
        ? window.adminDebounce(() => {
            currentPage = 1;
            loadList();
          }, 300)
        : () => {
            currentPage = 1;
            loadList();
          };
    root.querySelector("#banner_search").addEventListener("input", debouncedBannerSearch);

    root.querySelector("#banner_reload_btn").addEventListener("click", () => {
      currentPage = 1;
      loadList();
    });
    root.querySelector("#banner_reset_btn").addEventListener("click", () => {
      root.querySelector("#banner_search").value = "";
      root.querySelector("#banner_status_filter").value = "";
      currentPage = 1;
      loadList();
    });
    root.querySelector("#banner_search").addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        currentPage = 1;
        loadList();
      }
    });
    root.querySelector("#banner_create_btn").addEventListener("click", () => {
      openDrawer(false);
    });

    root.querySelector("#banner_submit_btn").addEventListener("click", async () => {
      const form = root.querySelector("#banner_form");
      const imageFile = imageInput.files[0];

      if (!imageFile && !currentImageUrl) {
        alert("请上传图片");
        return;
      }

      if (editingId) {
        if (imageFile) {
          const formData = new FormData();
          formData.append("title", form.title.value.trim());
          formData.append("link_type", form.link_type.value);
          formData.append("link_value", form.link_value.value.trim());
          formData.append("sort_order", parseInt(form.sort_order.value) || 0);
          formData.append("status", form.status.value);
          formData.append("image", imageFile);
          
          await authFetch(`/api/admin/banners/${editingId}`, {
            method: "PATCH",
            body: formData,
          });
        } else {
          const payload = {
            title: form.title.value.trim(),
            link_type: form.link_type.value,
            link_value: form.link_value.value.trim(),
            sort_order: parseInt(form.sort_order.value) || 0,
            status: form.status.value,
          };
          
          await authFetch(`/api/admin/banners/${editingId}`, {
            method: "PATCH",
            body: JSON.stringify(payload),
          });
        }
      } else {
        const formData = new FormData();
        formData.append("title", form.title.value.trim());
        formData.append("link_type", form.link_type.value);
        formData.append("link_value", form.link_value.value.trim());
        formData.append("sort_order", parseInt(form.sort_order.value) || 0);
        formData.append("status", form.status.value);
        formData.append("image", imageFile);
        
        await authFetch("/api/admin/banners", {
          method: "POST",
          body: formData,
        });
      }

      closeDrawer();
      await loadList();
    });

    await loadList();
  },
};
