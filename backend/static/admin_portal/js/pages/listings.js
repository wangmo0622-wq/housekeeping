window.AdminPortalPages["listings"] = {
  render: async function (root, token) {
    /** 与后端 Listing.MAX_COVER_URLS 一致 */
    const LISTING_MAX_COVERS = 6;
    /** 分类树：一级为根，children 为二级（后端已限制最多两级） */
    let categoryTree = [];
    let currentPage = 1;
    let pageSize = 10;
    let totalPages = 0;

    root.innerHTML = `
      <div class="zy-card">
        <div class="zy-card-body">
          <div class="zy-search-toolbar">
            <div class="zy-search-toolbar-top">
              <div class="zy-search-keyword">
                <label class="zy-search-label">关键词</label>
                <input type="search" id="listing_q_search" placeholder="标题 / 描述 / 联系方式 / 区域 / 发布者姓名" class="zy-form-input w-full" />
              </div>
              <button type="button" id="listing_toggle_advanced" class="zy-btn zy-btn-secondary zy-btn-sm zy-search-advanced-toggle">高级筛选</button>
            </div>
            <div class="zy-search-advanced-panel is-collapsed" id="listing_advanced_panel">
              <div class="zy-search-bar zy-search-bar--cols-3">
            <div class="zy-search-item">
              <label class="zy-search-label">服务标题</label>
              <input type="text" id="listing_title_search" placeholder="精确按标题" class="zy-form-input zy-search-control-lg" />
            </div>
            <div class="zy-search-item">
              <label class="zy-search-label">一级分类</label>
              <select id="listing_primary_category_filter" class="zy-select zy-search-control-lg">
                <option value="">全部一级分类</option>
              </select>
            </div>
            <div class="zy-search-item">
              <label class="zy-search-label">二级分类</label>
              <select id="listing_secondary_category_filter" class="zy-select zy-search-control-lg">
                <option value="">全部二级分类</option>
              </select>
            </div>
            <div class="zy-search-item">
              <label class="zy-search-label">发布者</label>
              <input type="text" id="listing_publisher_search" placeholder="请输入" class="zy-form-input zy-search-control-md" />
            </div>
            <div class="zy-search-item">
              <label class="zy-search-label">发布时间</label>
              <input type="date" id="listing_date_search" class="zy-form-input zy-search-control-md" />
            </div>
            <div class="zy-search-item zy-search-item--twin">
              <div class="zy-search-twin-field">
                <label class="zy-search-label">审核状态</label>
                <select id="listing_status_filter" class="zy-select zy-search-control-sm">
                  <option value="">全部状态</option>
                  <option value="pending">待审核</option>
                  <option value="published">已发布</option>
                  <option value="rejected">已驳回</option>
                  <option value="disabled">已下架</option>
                </select>
              </div>
              <div class="zy-search-twin-field">
                <label class="zy-search-label">删除状态</label>
                <select id="listing_deleted_filter" class="zy-select zy-search-control-sm">
                  <option value="">全部</option>
                  <option value="0">未删除</option>
                  <option value="1">已删除</option>
                </select>
              </div>
            </div>
            <div class="zy-search-actions">
              <button id="listing_reload_btn" class="zy-btn zy-btn-reset zy-btn-sm">重置</button>
              <button id="listing_query_btn" class="zy-btn zy-btn-query zy-btn-sm">查询</button>
            </div>
              </div>
            </div>
          </div>
          <div class="zy-table-scroll">
            <table class="zy-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>服务标题</th>
                  <th>一级分类</th>
                  <th>二级分类</th>
                  <th>服务价格</th>
                  <th>服务区域</th>
                  <th>联系方式</th>
                  <th>发布者</th>
                  <th>发布时间</th>
                  <th>审核状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody id="listing_tbody"></tbody>
            </table>
          </div>
          <div id="listing_pagination" class="zy-pagination"></div>
        </div>
      </div>

      <!-- 右侧抽屉 -->
      <div id="listing_drawer_overlay" class="zy-drawer-overlay">
        <div class="zy-drawer">
          <div class="zy-drawer-header">
            <h3 class="zy-drawer-title" id="listing_drawer_title">详情</h3>
            <button class="zy-drawer-close" id="listing_drawer_close">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-5 h-5">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
          <div class="zy-drawer-body" id="listing_drawer_body"></div>
          <div class="zy-drawer-footer" id="listing_drawer_footer"></div>
        </div>
      </div>
    `;

    const drawerOverlay = root.querySelector("#listing_drawer_overlay");
    const drawerTitle = root.querySelector("#listing_drawer_title");
    const drawerBody = root.querySelector("#listing_drawer_body");
    const drawerFooter = root.querySelector("#listing_drawer_footer");
    const drawerClose = root.querySelector("#listing_drawer_close");

    function openDrawer(title, bodyHtml, footerHtml) {
      drawerTitle.textContent = title;
      drawerBody.innerHTML = bodyHtml;
      drawerFooter.innerHTML = footerHtml;
      drawerOverlay.classList.add("active");
    }

    function renderListingAuditHistory(audits) {
      if (!audits || audits.length === 0) {
        return '<p class="zy-empty-hint zy-empty-hint--tight">暂无审核记录</p>';
      }
      return audits.map(audit => {
        const statusMap = {
          pending: '<span class="zy-badge zy-badge-warning">待审核</span>',
          published: '<span class="zy-badge zy-badge-success">已发布</span>',
          rejected: '<span class="zy-badge zy-badge-danger">已驳回</span>',
          disabled: '<span class="zy-badge zy-badge-danger">已下架</span>'
        };
        return `
          <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
              <span style="font-weight: 500; color: #1f2937;">服务审核</span>
              ${statusMap[audit.status] || audit.status}
            </div>
            <div style="font-size: 13px; color: #6b7280;">
              ${audit.created_at ? '创建时间: ' + audit.created_at : ''}
            </div>
            ${audit.reviewed_at ? `
              <div style="font-size: 13px; color: #6b7280; margin-top: 4px;">
                审核时间: ${audit.reviewed_at}
              </div>
            ` : ''}
            ${audit.reviewed_by ? `
              <div style="font-size: 13px; color: #6b7280; margin-top: 4px;">
                审核人: ${audit.reviewed_by}
              </div>
            ` : ''}
            ${audit.audit_note ? `
              <div style="font-size: 13px; color: #374151; margin-top: 8px; padding: 8px; background: #f9fafb; border-radius: 4px;">
                审核备注: ${audit.audit_note}
              </div>
            ` : ''}
          </div>
        `;
      }).join("");
    }

    function closeDrawer() {
      drawerOverlay.classList.remove("active");
    }

    function escapeHtml(value) {
      return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
    }

    function escapeAttr(value) {
      return escapeHtml(value);
    }

    function buildCategoryOptions(tree, selectedId) {
      let html = "";
      for (const rootNode of tree || []) {
        const rs = String(rootNode.id) === String(selectedId) ? "selected" : "";
        html += `<option value="${rootNode.id}" ${rs}>${escapeHtml(rootNode.name)}</option>`;
        for (const c of rootNode.children || []) {
          const cs = String(c.id) === String(selectedId) ? "selected" : "";
          html += `<option value="${c.id}" ${cs}>${escapeHtml(rootNode.name)} / ${escapeHtml(c.name)}</option>`;
        }
      }
      return html;
    }

    // 图片预览功能
    let imgPreviewOverlay = null;
    let imgPreviewImg = null;
    function initImgPreview() {
      if (!imgPreviewOverlay) {
        imgPreviewOverlay = document.createElement("div");
        imgPreviewOverlay.id = "img_preview_overlay";
        imgPreviewOverlay.style.cssText = "position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.9);z-index:10000;display:none;align-items:center;justify-content:center;cursor:pointer;";
        imgPreviewImg = document.createElement("img");
        imgPreviewImg.style.cssText = "max-width:90%;max-height:90%;object-fit:contain;border-radius:8px;";
        imgPreviewOverlay.appendChild(imgPreviewImg);
        document.body.appendChild(imgPreviewOverlay);
        imgPreviewOverlay.addEventListener("click", () => {
          imgPreviewOverlay.style.display = "none";
        });
      }
    }
    window.showImgPreview = function(src) {
      initImgPreview();
      imgPreviewImg.src = src;
      imgPreviewOverlay.style.display = "flex";
    };

    drawerClose.addEventListener("click", closeDrawer);
    drawerOverlay.addEventListener("click", (e) => {
      if (e.target === drawerOverlay) closeDrawer();
    });

    function renderPrimaryOptions() {
      const select = root.querySelector("#listing_primary_category_filter");
      const current = select.value;
      select.innerHTML = '<option value="">全部一级分类</option>';
      (categoryTree || []).forEach((r) => {
        const option = document.createElement("option");
        option.value = String(r.id);
        option.textContent = r.name;
        select.appendChild(option);
      });
      if (current && [...select.options].some((o) => o.value === current)) select.value = current;
    }

    function renderSecondaryOptions(primaryId = "") {
      const select = root.querySelector("#listing_secondary_category_filter");
      const current = select.value;
      select.innerHTML = '<option value="">全部二级分类</option>';

      const pid = primaryId ? String(primaryId) : String(root.querySelector("#listing_primary_category_filter").value || "");
      const primaryNode = (categoryTree || []).find((r) => String(r.id) === pid);
      const children = (primaryNode && primaryNode.children) ? primaryNode.children : [];

      children.forEach((c) => {
        const option = document.createElement("option");
        option.value = String(c.id);
        option.textContent = c.name;
        select.appendChild(option);
      });

      if (current && [...select.options].some((o) => o.value === current)) {
        select.value = current;
      } else {
        select.value = "";
      }
    }

    async function loadCategories() {
      try {
        const data = await authFetch("/api/admin/categories/tree", { method: "GET" });
        categoryTree = data.tree || [];
        renderPrimaryOptions();
        renderSecondaryOptions();
      } catch (err) {
        console.error("加载分类失败:", err);
      }
    }

    function statusBadge(v) {
      const map = {
        draft: '<span class="zy-badge zy-badge-info">草稿</span>',
        pending: '<span class="zy-badge zy-badge-warning">待审核</span>',
        published: '<span class="zy-badge zy-badge-success">已发布</span>',
        rejected: '<span class="zy-badge zy-badge-danger">已驳回</span>',
        disabled: '<span class="zy-badge zy-badge-danger">已下架</span>'
      };
      return map[v] || v || "-";
    }

    function listingCoverUrls(item) {
      if (item.cover_urls && item.cover_urls.length) return item.cover_urls.slice(0, LISTING_MAX_COVERS);
      if (item.cover_url) return [item.cover_url];
      return [];
    }

    function listingCoversHtml(item) {
      const urls = listingCoverUrls(item);
      if (!urls.length) return "";
      const imgs = urls
        .map(
          (u) =>
            `<img class="listing-cover-thumb" src=${JSON.stringify(u)} alt="" style="width:120px;height:80px;object-fit:cover;border-radius:8px;cursor:pointer;border:1px solid #e5e7eb;" />`
        )
        .join("");
      return `<div style="margin-top: 16px;">
        <span style="color: #6b7280; display: block; margin-bottom: 8px;">封面图（最多 ${LISTING_MAX_COVERS} 张，与小程序一致）</span>
        <div style="display: flex; flex-wrap: wrap; gap: 8px;">${imgs}</div>
      </div>`;
    }

    function bindListingCoverThumbs(container) {
      if (!container) return;
      container.querySelectorAll(".listing-cover-thumb").forEach((img) => {
        img.addEventListener("click", () => window.showImgPreview(img.src));
      });
    }

    function renderPagination(total, page, totalPages, pageSize) {
      window.renderAdminPagination({
        root,
        containerSelector: "#listing_pagination",
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


    const advPanel = root.querySelector("#listing_advanced_panel");
    const advToggle = root.querySelector("#listing_toggle_advanced");
    if (advToggle && advPanel) {
      advToggle.addEventListener("click", () => {
        advPanel.classList.toggle("is-collapsed");
        advToggle.textContent = advPanel.classList.contains("is-collapsed") ? "高级筛选" : "收起筛选";
      });
    }

    const runListingSearch = () => {
      currentPage = 1;
      loadList();
    };
    const debouncedListingQ =
      typeof window.adminDebounce === "function"
        ? window.adminDebounce(runListingSearch, 320)
        : runListingSearch;

    root.querySelector("#listing_q_search").addEventListener("input", debouncedListingQ);

    async function loadList() {
      const qSearch = root.querySelector("#listing_q_search").value.trim();
      const titleSearch = root.querySelector("#listing_title_search").value.trim();
      const primaryCategoryId = root.querySelector("#listing_primary_category_filter").value;
      const secondaryCategoryId = root.querySelector("#listing_secondary_category_filter").value;
      const publisherSearch = root.querySelector("#listing_publisher_search").value.trim();
      const dateSearch = root.querySelector("#listing_date_search").value;
      const status = root.querySelector("#listing_status_filter").value;
      const deletedFilter = root.querySelector("#listing_deleted_filter").value;

      const params = new URLSearchParams();
      params.append("page", currentPage);
      params.append("page_size", pageSize);
      if (qSearch) params.append("q", qSearch);
      if (titleSearch) params.append("title", titleSearch);
      if (secondaryCategoryId) params.append("secondary_category_id", secondaryCategoryId);
      else if (primaryCategoryId) params.append("primary_category_id", primaryCategoryId);
      if (publisherSearch) params.append("publisher", publisherSearch);
      if (dateSearch) params.append("date", dateSearch);
      if (status) params.append("status", status);
      if (deletedFilter === "0") params.append("show_deleted", "false");
      else if (deletedFilter === "1") params.append("show_deleted", "true");

      const data = await authFetch(`/api/admin/listings?${params.toString()}`, { method: "GET" });
      const items = data.items || [];
      totalPages = data.total_pages || 1;
      const tbody = root.querySelector("#listing_tbody");

      if (items.length === 0) {
        tbody.innerHTML = adminTableEmptyRow(11);
        renderPagination(0, 1, 0, pageSize);
        return;
      }

      tbody.innerHTML = items
        .map((x) => {
          const isPending = x.status === "pending";
          return `
            <tr ${x.is_deleted ? 'style="opacity: 0.6;"' : ''}>
              <td>${x.id}</td>
              <td>${x.title || ""} ${x.is_deleted ? '<span style="color: #9ca3af; font-size: 12px; margin-left: 8px;">(已删除)</span>' : ''}</td>
              <td>${x.primary_category_name || "-"}</td>
              <td>${x.secondary_category_name || "-"}</td>
              <td>${x.service_price || "-"}</td>
              <td>${x.service_areas ? (x.service_areas.split(',').filter(a => a.trim()).length > 0 ? x.service_areas.split(',').filter(a => a.trim()).slice(0, 2).join('、') + (x.service_areas.split(',').filter(a => a.trim()).length > 2 ? '等' + x.service_areas.split(',').filter(a => a.trim()).length + '个区域' : '') : '-') : '-'}</td>
              <td>${x.contact_info || "-"}</td>
              <td>${x.real_name || ""}</td>
              <td>${x.created_at || ""}</td>
              <td>${statusBadge(x.status)}</td>
              <td>
                <div class="zy-actions">
                  ${!x.is_deleted && isPending ? '<a class="zy-action-link zy-action-link--primary" data-action="review" data-id="' + x.id + '">审核</a>' : ''}
                  <a class="zy-action-link" data-action="detail" data-id="${x.id}">详情</a>
                  ${!x.is_deleted ? '<a class="zy-action-link zy-action-link--primary" data-action="edit" data-id="' + x.id + '">编辑</a>' : ''}
                  ${!x.is_deleted ? '<a class="zy-action-link zy-action-link--danger" data-action="delete" data-id="' + x.id + '">删除</a>' : ''}
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

      e.preventDefault();

      if (action === "detail") {
        const item = await authFetch(`/api/admin/listings/${id}`, { method: "GET" });
        const servicePriceRow = item.service_price
          ? `<div style="display: grid; grid-template-columns: 100px 1fr; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f3f4f6;">
              <span style="color: #6b7280;">服务价格</span>
              <span style="color: #1f2937;">${item.service_price}</span>
            </div>`
          : "";
        openDrawer(
          "服务详情",
          `
            <div style="font-size: 14px;">
              <h4 style="color: #1f2937; font-weight: 500; margin-bottom: 16px;">基本信息</h4>
              <div style="display: grid; grid-template-columns: 1fr; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f3f4f6;">
                <div style="display: grid; grid-template-columns: 100px 1fr; gap: 12px;">
                  <span style="color: #6b7280;">服务标题</span>
                  <span style="color: #1f2937;">${item.title || "-"}</span>
                </div>
              </div>
              <div style="display: grid; grid-template-columns: 1fr; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f3f4f6;">
                <div style="display: grid; grid-template-columns: 100px 1fr; gap: 12px;">
                  <span style="color: #6b7280;">一级分类</span>
                  <span style="color: #1f2937;">${item.primary_category_name || "-"}</span>
                </div>
              </div>
              <div style="display: grid; grid-template-columns: 1fr; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f3f4f6;">
                <div style="display: grid; grid-template-columns: 100px 1fr; gap: 12px;">
                  <span style="color: #6b7280;">二级分类</span>
                  <span style="color: #1f2937;">${item.secondary_category_name || "-"}</span>
                </div>
              </div>
              ${servicePriceRow}
              <div style="display: grid; grid-template-columns: 1fr; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f3f4f6;">
                <div style="display: grid; grid-template-columns: 100px 1fr; gap: 12px;">
                  <span style="color: #6b7280;">服务区域</span>
                  <span style="color: #1f2937;">${item.service_areas ? (item.service_areas.split(',').filter(a => a.trim()).length > 0 ? item.service_areas.split(',').filter(a => a.trim()).join('、') : '-') : '-'}</span>
                </div>
              </div>
              <div style="display: grid; grid-template-columns: 1fr; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f3f4f6;">
                <div style="display: grid; grid-template-columns: 100px 1fr; gap: 12px;">
                  <span style="color: #6b7280;">联系方式</span>
                  <span style="color: #1f2937;">${item.contact_info || "-"}</span>
                </div>
              </div>
              <div style="display: grid; grid-template-columns: 1fr; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f3f4f6;">
                <div style="display: grid; grid-template-columns: 100px 1fr; gap: 12px;">
                  <span style="color: #6b7280;">发布者</span>
                  <span style="color: #1f2937;">${item.real_name || "-"}</span>
                </div>
              </div>
              <div style="display: grid; grid-template-columns: 1fr; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f3f4f6;">
                <div style="display: grid; grid-template-columns: 100px 1fr; gap: 12px;">
                  <span style="color: #6b7280;">审核状态</span>
                  <span style="color: #1f2937;">${statusBadge(item.status)}</span>
                </div>
              </div>
              <div style="display: grid; grid-template-columns: 1fr; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f3f4f6;">
                <div style="display: grid; grid-template-columns: 100px 1fr; gap: 12px;">
                  <span style="color: #6b7280;">发布时间</span>
                  <span style="color: #1f2937;">${item.created_at || "-"}</span>
                </div>
              </div>
              ${listingCoversHtml(item)}
              ${item.description ? `
                <div style="margin-top: 16px;">
                  <span style="color: #6b7280; display: block; margin-bottom: 8px;">服务描述</span>
                  <div style="padding: 12px; background: #f9fafb; border-radius: 8px; color: #374151; line-height: 1.6;">${item.description}</div>
                </div>
              ` : ""}
              <h4 style="color: #1f2937; font-weight: 500; margin: 20px 0 16px;">审核记录</h4>
              ${renderListingAuditHistory(item.audits)}
            </div>
          `,
          `<button class="zy-btn zy-btn-secondary zy-btn-sm" id="drawer_close_btn">关闭</button>`
        );
        root.querySelector("#drawer_close_btn").addEventListener("click", closeDrawer);
        bindListingCoverThumbs(drawerBody);
        return;
      }

      if (action === "review") {
        const item = await authFetch(`/api/admin/listings/${id}`, { method: "GET" });
        const servicePriceRowRev = item.service_price
          ? `<div style="display: grid; grid-template-columns: 100px 1fr; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f3f4f6;">
              <span style="color: #6b7280;">服务价格</span>
              <span style="color: #1f2937;">${item.service_price}</span>
            </div>`
          : "";
        openDrawer(
          "审核服务",
          `
            <div style="font-size: 14px;">
              <h4 style="color: #1f2937; font-weight: 500; margin-bottom: 16px;">基本信息</h4>
              <div style="display: grid; grid-template-columns: 1fr; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f3f4f6;">
                <div style="display: grid; grid-template-columns: 100px 1fr; gap: 12px;">
                  <span style="color: #6b7280;">服务标题</span>
                  <span style="color: #1f2937;">${item.title || "-"}</span>
                </div>
              </div>
              <div style="display: grid; grid-template-columns: 1fr; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f3f4f6;">
                <div style="display: grid; grid-template-columns: 100px 1fr; gap: 12px;">
                  <span style="color: #6b7280;">一级分类</span>
                  <span style="color: #1f2937;">${item.primary_category_name || "-"}</span>
                </div>
              </div>
              <div style="display: grid; grid-template-columns: 1fr; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f3f4f6;">
                <div style="display: grid; grid-template-columns: 100px 1fr; gap: 12px;">
                  <span style="color: #6b7280;">二级分类</span>
                  <span style="color: #1f2937;">${item.secondary_category_name || "-"}</span>
                </div>
              </div>
              ${servicePriceRowRev}
              <div style="display: grid; grid-template-columns: 1fr; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f3f4f6;">
                <div style="display: grid; grid-template-columns: 100px 1fr; gap: 12px;">
                  <span style="color: #6b7280;">服务区域</span>
                  <span style="color: #1f2937;">${item.service_areas ? (item.service_areas.split(',').filter(a => a.trim()).length > 0 ? item.service_areas.split(',').filter(a => a.trim()).join('、') : '-') : '-'}</span>
                </div>
              </div>
              <div style="display: grid; grid-template-columns: 1fr; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f3f4f6;">
                <div style="display: grid; grid-template-columns: 100px 1fr; gap: 12px;">
                  <span style="color: #6b7280;">联系方式</span>
                  <span style="color: #1f2937;">${item.contact_info || "-"}</span>
                </div>
              </div>
              <div style="display: grid; grid-template-columns: 1fr; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f3f4f6;">
                <div style="display: grid; grid-template-columns: 100px 1fr; gap: 12px;">
                  <span style="color: #6b7280;">发布者</span>
                  <span style="color: #1f2937;">${item.real_name || "-"}</span>
                </div>
              </div>
              ${listingCoversHtml(item)}
              ${item.description ? `
                <div style="margin-top: 16px;">
                  <span style="color: #6b7280; display: block; margin-bottom: 8px;">服务描述</span>
                  <div style="padding: 12px; background: #f9fafb; border-radius: 8px; color: #374151; line-height: 1.6;">${item.description}</div>
                </div>
              ` : ""}
              <h4 style="color: #1f2937; font-weight: 500; margin: 20px 0 16px;">审核记录</h4>
              ${renderListingAuditHistory(item.audits)}
              <h4 style="color: #1f2937; font-weight: 500; margin: 20px 0 12px;">审核操作</h4>
              <textarea id="audit_note" class="zy-form-textarea" rows="3" placeholder="请输入审核备注（可选）" style="width: 100%; padding: 10px; border: 1px solid #e5e7eb; border-radius: 8px; resize: vertical; margin-bottom: 12px;"></textarea>
            </div>
          `,
          `<button class="zy-btn zy-btn-secondary zy-btn-sm" id="drawer_cancel">取消</button><button class="zy-btn zy-btn-danger zy-btn-sm" id="drawer_reject">驳回</button><button class="zy-btn zy-btn-success zy-btn-sm" id="drawer_approve">通过</button>`
        );

        bindListingCoverThumbs(drawerBody);
        root.querySelector("#drawer_cancel").addEventListener("click", closeDrawer);
        root.querySelector("#drawer_reject").addEventListener("click", async () => {
          const note = root.querySelector("#audit_note").value;
          try {
            await authFetch(`/api/admin/listings/${id}/audit/reject`, {
              method: "POST",
              body: JSON.stringify({ note }),
            });
            showToast({ title: "操作成功", message: "服务已驳回", type: "success" });
            closeDrawer();
            await loadList();
          } catch (err) {
            showToast({ title: "操作失败", message: err.message || "驳回失败", type: "error" });
          }
        });
        root.querySelector("#drawer_approve").addEventListener("click", async () => {
          const note = root.querySelector("#audit_note").value;
          try {
            await authFetch(`/api/admin/listings/${id}/audit/approve`, {
              method: "POST",
              body: JSON.stringify({ note }),
            });
            showToast({ title: "操作成功", message: "服务已通过审核", type: "success" });
            closeDrawer();
            await loadList();
          } catch (err) {
            showToast({ title: "操作失败", message: err.message || "审核失败", type: "error" });
          }
        });
        return;
      }

      if (action === "edit") {
        try {
        const item = await authFetch(`/api/admin/listings/${id}`, { method: "GET" });
        const row = (label, inner) => `<div class="org-form-grid"><label>${escapeHtml(label)}</label><div>${inner}</div></div>`;
        const covers = (item.cover_urls && item.cover_urls.length)
          ? item.cover_urls
          : (item.cover_url ? [item.cover_url] : []);
        const getCategorySelection = (tree, currentId) => {
          const cid = String(currentId || "");
          for (const rootNode of tree || []) {
            if (String(rootNode.id) === cid) {
              return { primaryId: String(rootNode.id), secondaryId: "" };
            }
            const child = (rootNode.children || []).find((c) => String(c.id) === cid);
            if (child) {
              return { primaryId: String(rootNode.id), secondaryId: String(child.id) };
            }
          }
          return { primaryId: "", secondaryId: "" };
        };
        const categorySelection = getCategorySelection(categoryTree, item.category_id);
        const rootCategories = categoryTree || [];
        const rootsWithChildren = rootCategories.filter((rootNode) => (rootNode.children || []).length > 0);
        const primaryNodes = rootsWithChildren.length ? rootsWithChildren.slice() : rootCategories.slice();
        if (categorySelection.primaryId && !primaryNodes.some((rootNode) => String(rootNode.id) === categorySelection.primaryId)) {
          const selectedRoot = rootCategories.find((rootNode) => String(rootNode.id) === categorySelection.primaryId);
          if (selectedRoot) primaryNodes.unshift(selectedRoot);
        }
        const primaryOpts = primaryNodes
          .map((rootNode) => `<option value="${rootNode.id}" ${String(rootNode.id) === categorySelection.primaryId ? "selected" : ""}>${escapeHtml(rootNode.name)}</option>`)
          .join("");
        const priceVal = item.listing_price != null && item.listing_price !== "" ? String(item.listing_price) : "";
        const unitVal = item.listing_price_unit != null && item.listing_price_unit !== "" ? String(item.listing_price_unit) : "次";

        openDrawer(
          "编辑服务",
          `
            <div class="org-service-edit">
              <div class="org-field-section">
                <div class="org-field-title">基本信息</div>
                ${row("发布者", `<span class="org-pub-badge">${escapeHtml(item.real_name || "—")}</span>`)}
                ${row("服务标题", `<input id="adm_ose_title" class="ipt" value="${escapeAttr(item.title)}" placeholder="填写服务名称" />`)}
                ${row("一级分类", `
                  <select id="adm_ose_cat_primary" class="ipt">
                    <option value="">请选择一级分类</option>
                    ${primaryOpts}
                  </select>
                `)}
                ${row("二级分类", `
                  <select id="adm_ose_cat_secondary" class="ipt">
                    <option value="">请选择二级分类</option>
                  </select>
                `)}
                ${row("上架状态", `<select id="adm_ose_status" class="ipt">
          <option value="draft" ${item.status === "draft" ? "selected" : ""}>草稿</option>
          <option value="pending" ${item.status === "pending" ? "selected" : ""}>待审核</option>
          <option value="published" ${item.status === "published" ? "selected" : ""}>已发布</option>
          <option value="rejected" ${item.status === "rejected" ? "selected" : ""}>已驳回</option>
          <option value="disabled" ${item.status === "disabled" ? "selected" : ""}>已下架</option>
        </select>`)}
              </div>
              <div class="org-field-section">
                <div class="org-field-title">定价与联系</div>
                ${row("价格与单位", `<div class="org-price-pair">
              <div>
                <label class="inner" for="adm_ose_price">金额</label>
                <input id="adm_ose_price" class="ipt" value="${escapeAttr(priceVal)}" placeholder="例如 299.00" />
              </div>
              <div>
                <label class="inner" for="adm_ose_punit">单位</label>
                <input id="adm_ose_punit" class="ipt" value="${escapeAttr(unitVal)}" placeholder="次 / 小时 / 天" />
              </div>
            </div>`)}
                ${row("服务区域", `<input id="adm_ose_areas" class="ipt" value="${escapeAttr(item.service_areas)}" placeholder="可服务区域，如：朝阳区、全市" />`)}
                ${row("联系方式", `<input id="adm_ose_contact" class="ipt" value="${escapeAttr(item.contact_info)}" placeholder="电话或微信等" />`)}
              </div>
              <div class="org-field-section org-field-section--covers">
                <div class="org-field-title">封面图片</div>
                <div>
                  <div class="org-cover-sublabel">封面组（${LISTING_MAX_COVERS} 张内）</div>
                  <div id="adm_ose_cov_trigger" class="org-cover-dropzone">
                    <button type="button" class="zy-upload-plus-tile" id="adm_ose_cov_add" title="上传封面">+</button>
                  </div>
                  <input id="adm_ose_cov_files" type="file" accept="image/*" multiple style="display:none;" />
                </div>
              </div>
              <div class="org-field-section">
                <div class="org-field-title">服务描述</div>
                <div class="org-desc-block">
                  <textarea id="adm_ose_desc" class="txt" placeholder="介绍服务内容、流程、注意事项等">${escapeHtml(item.description)}</textarea>
                </div>
              </div>
            </div>
          `,
          `<button class="zy-btn zy-btn-secondary zy-btn-sm" id="adm_ose_cancel">取消</button><button class="zy-btn zy-btn-primary zy-btn-sm" id="adm_ose_save">保存</button>`
        );
        const ct = root.querySelector("#adm_ose_cov_trigger");
        const cf = root.querySelector("#adm_ose_cov_files");
        const primarySelect = root.querySelector("#adm_ose_cat_primary");
        const secondarySelect = root.querySelector("#adm_ose_cat_secondary");
        const renderSecondaryEditOptions = (primaryId, selectedSecondaryId = "") => {
          const primaryNode = rootCategories.find((r) => String(r.id) === String(primaryId));
          const children = primaryNode ? (primaryNode.children || []) : [];
          secondarySelect.innerHTML = '<option value="">请选择二级分类</option>';
          children.forEach((c) => {
            const option = document.createElement("option");
            option.value = String(c.id);
            option.textContent = c.name;
            if (String(c.id) === String(selectedSecondaryId)) option.selected = true;
            secondarySelect.appendChild(option);
          });
          if (children.length === 0 && primaryId) {
            secondarySelect.innerHTML = '<option value="">该一级分类暂无二级分类</option>';
          }
          secondarySelect.disabled = children.length === 0;
        };
        renderSecondaryEditOptions(primarySelect.value, categorySelection.secondaryId);
        primarySelect.addEventListener("change", () => renderSecondaryEditOptions(primarySelect.value, ""));

        let selectedCoverFiles = [];
        let existingCoverUrls = covers.slice(0, LISTING_MAX_COVERS);
        const renderUploadTile = (canAdd) => (canAdd
          ? '<button type="button" class="zy-upload-plus-tile" id="adm_ose_cov_add" title="上传封面">+</button>'
          : "");
        const renderSelectedCovers = () => {
          const existingHtml = existingCoverUrls
            .map((url, index) => `<div class="zy-thumb-item"><img src="${escapeAttr(url)}" class="org-thumb" alt="" /><button type="button" class="zy-thumb-remove" data-cover-type="existing" data-cover-index="${index}" title="删除">×</button></div>`)
            .join("");
          const selectedHtml = selectedCoverFiles
            .map((file, index) => {
              const url = URL.createObjectURL(file);
              return `<div class="zy-thumb-item"><img src="${url}" class="org-thumb" alt="" /><button type="button" class="zy-thumb-remove" data-cover-type="selected" data-cover-index="${index}" title="删除">×</button></div>`;
            })
            .join("");
          const totalCount = existingCoverUrls.length + selectedCoverFiles.length;
          ct.innerHTML = `${existingHtml}${selectedHtml}${renderUploadTile(totalCount < LISTING_MAX_COVERS)}`;
          if (!ct.innerHTML.trim()) {
            ct.innerHTML = renderUploadTile(true);
            return;
          }
        };
        renderSelectedCovers();
        ct.addEventListener("click", (e) => {
          if (e.target.closest("[data-cover-type]")) return;
          if (!e.target.closest("#adm_ose_cov_add")) return;
          cf.click();
        });
        cf.addEventListener("change", () => {
          const incoming = Array.from(cf.files || []);
          const remain = Math.max(0, LISTING_MAX_COVERS - existingCoverUrls.length - selectedCoverFiles.length);
          if (remain > 0) {
            selectedCoverFiles = selectedCoverFiles.concat(incoming.slice(0, remain));
          }
          cf.value = "";
          renderSelectedCovers();
        });
        ct.addEventListener("click", (e) => {
          const btn = e.target.closest("[data-cover-type]");
          if (!btn) return;
          e.preventDefault();
          e.stopPropagation();
          const idx = Number(btn.getAttribute("data-cover-index"));
          if (Number.isNaN(idx)) return;
          const type = btn.getAttribute("data-cover-type");
          if (type === "existing") {
            existingCoverUrls.splice(idx, 1);
          } else {
            selectedCoverFiles.splice(idx, 1);
          }
          renderSelectedCovers();
        });

        root.querySelector("#adm_ose_cancel").addEventListener("click", closeDrawer);
        root.querySelector("#adm_ose_save").addEventListener("click", async () => {
          const primaryCategoryId = primarySelect.value;
          const secondaryCategoryId = secondarySelect.value;
          if (!primaryCategoryId) {
            showToast({ title: "保存失败", message: "请选择一级分类", type: "error" });
            return;
          }
          const selectedPrimaryNode = (categoryTree || []).find((r) => String(r.id) === String(primaryCategoryId));
          const selectedPrimaryChildren = selectedPrimaryNode ? (selectedPrimaryNode.children || []) : [];
          if (selectedPrimaryChildren.length > 0 && !secondaryCategoryId) {
            showToast({ title: "保存失败", message: "该一级分类下有二级分类，请选择二级分类", type: "error" });
            return;
          }
          const payload = new FormData();
          payload.append("title", root.querySelector("#adm_ose_title").value.trim());
          payload.append("category_id", String(Number(primaryCategoryId)));
          if (secondaryCategoryId) payload.append("secondary_category_id", String(Number(secondaryCategoryId)));
          payload.append("listing_price", root.querySelector("#adm_ose_price").value.trim());
          payload.append("listing_price_unit", root.querySelector("#adm_ose_punit").value.trim());
          payload.append("service_areas", root.querySelector("#adm_ose_areas").value.trim());
          payload.append("contact_info", root.querySelector("#adm_ose_contact").value.trim());
          payload.append("status", root.querySelector("#adm_ose_status").value);
          payload.append("description", root.querySelector("#adm_ose_desc").value.trim());
          payload.append("cover_urls", JSON.stringify(existingCoverUrls));

          const cfiles = selectedCoverFiles.slice(0, LISTING_MAX_COVERS);
          cfiles.forEach((f) => payload.append("cover_images", f));
          try {
            await authFetch(`/api/admin/listings/${id}`, {
              method: "PATCH",
              body: payload,
            });
            showToast({ title: "保存成功", message: "服务信息已更新", type: "success" });
            closeDrawer();
            await loadList();
          } catch (err) {
            showToast({ title: "保存失败", message: err.message || "更新失败", type: "error" });
          }
        });
        return;
        } catch (err) {
          console.error("open listing edit failed", err);
          showToast({ title: "打开失败", message: err.message || "编辑页加载失败", type: "error" });
          return;
        }
      }

      if (action === "delete") {
        showConfirm({
          title: "确认删除",
          message: "确定要删除该服务吗？此操作不可恢复。",
          confirmText: "删除",
          cancelText: "取消",
          type: "warning",
          onConfirm: async () => {
            try {
              await authFetch(`/api/admin/listings/${id}`, { method: "DELETE" });
              showToast({ title: "操作成功", message: "服务已删除", type: "success" });
              await loadList();
            } catch (err) {
              showToast({ title: "操作失败", message: err.message || "删除失败", type: "error" });
            }
          },
        });
        return;
      }
    });

    root.querySelector("#listing_query_btn").addEventListener("click", () => {
      currentPage = 1;
      loadList();
    });
    root.querySelector("#listing_title_search").addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        currentPage = 1;
        loadList();
      }
    });

    root.querySelector("#listing_reload_btn").addEventListener("click", () => {
      root.querySelector("#listing_q_search").value = "";
      root.querySelector("#listing_title_search").value = "";
      root.querySelector("#listing_primary_category_filter").value = "";
      root.querySelector("#listing_secondary_category_filter").value = "";
      root.querySelector("#listing_publisher_search").value = "";
      root.querySelector("#listing_date_search").value = "";
      root.querySelector("#listing_status_filter").value = "";
      root.querySelector("#listing_deleted_filter").value = "";
      if (advPanel && advToggle) {
        advPanel.classList.add("is-collapsed");
        advToggle.textContent = "高级筛选";
      }
      currentPage = 1;
      loadList();
    });

    const primarySelect = root.querySelector("#listing_primary_category_filter");
    const secondarySelect = root.querySelector("#listing_secondary_category_filter");
    if (primarySelect && secondarySelect) {
      primarySelect.addEventListener("change", () => {
        currentPage = 1;
        renderSecondaryOptions(primarySelect.value);
        loadList();
      });
      secondarySelect.addEventListener("change", () => {
        currentPage = 1;
        loadList();
      });
    }

    await loadCategories();
    await loadList();
  },
};
