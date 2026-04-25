window.AdminPortalPages["organizations"] = {
  render: async function (root) {
    root.innerHTML = `
      <div class="zy-card">
        <div class="zy-card-body">
          <div class="zy-toolbar-row">
            <div>
              <label class="zy-search-label" for="org_q">关键词</label>
              <input id="org_q" class="zy-form-input zy-form-input--md" placeholder="企业名 / 联系人 / 手机号" />
            </div>
            <div>
              <label class="zy-search-label" for="org_status">认证状态</label>
              <select id="org_status" class="zy-select zy-form-input--sm">
                <option value="">全部(不含未发起)</option>
                <option value="all">全部(含未发起)</option>
                <option value="uninitiated">未发起认证</option>
                <option value="pending">待审核</option>
                <option value="approved">已通过</option>
                <option value="rejected">未通过</option>
              </select>
            </div>
            <button type="button" id="org_search" class="zy-btn zy-btn-primary zy-btn-sm">查询</button>
          </div>
          <div class="zy-table-scroll">
            <table class="zy-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>企业名称</th>
                  <th>联系人</th>
                  <th>联系电话</th>
                  <th>认证状态</th>
                  <th>活跃技师</th>
                  <th>待处理解绑</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody id="org_tbody"></tbody>
            </table>
          </div>
        </div>
      </div>
      <div id="org_drawer_overlay" class="zy-drawer-overlay">
        <div class="zy-drawer">
          <div class="zy-drawer-header">
            <h3 class="zy-drawer-title" id="org_drawer_title">详情</h3>
            <button class="zy-drawer-close" id="org_drawer_close" type="button">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-5 h-5">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
          <div class="zy-drawer-body" id="org_drawer_body"></div>
          <div class="zy-drawer-footer" id="org_drawer_footer"></div>
        </div>
      </div>
    `;
    const drawerOverlay = root.querySelector("#org_drawer_overlay");
    const drawerTitle = root.querySelector("#org_drawer_title");
    const drawerBody = root.querySelector("#org_drawer_body");
    const drawerFooter = root.querySelector("#org_drawer_footer");
    const drawerClose = root.querySelector("#org_drawer_close");

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

    const statusText = (v) =>
      ({ uninitiated: "未发起", pending: "待审核", approved: "已通过", rejected: "未通过" }[v] || v || "-");

    const actionButtons = (x) => {
      const actions = [`<a class="zy-action-link" data-action="detail" data-id="${x.id}">详情</a>`];
      if (x.verification_status === "pending") {
        actions.push(
          `<a class="zy-action-link zy-action-link--success" data-action="approve" data-id="${x.id}">通过</a>`
        );
        actions.push(
          `<a class="zy-action-link zy-action-link--danger" data-action="reject" data-id="${x.id}">驳回</a>`
        );
      }
      actions.push(
        `<a class="zy-action-link ${x.is_disabled ? "zy-action-link--success" : "zy-action-link--danger"}" data-action="${x.is_disabled ? "enable" : "disable"}" data-id="${x.id}">${x.is_disabled ? "启用" : "禁用"}</a>`
      );
      return actions.join("");
    };

    const renderOrgDetailHtml = (item) => {
      const baseLines = [
        { label: "机构 ID", value: String(item.id || "-") },
        { label: "企业名称", value: item.company_name || "-" },
        { label: "联系人", value: item.contact_person || "-" },
        { label: "联系电话", value: item.contact_phone || "-" },
        { label: "机构地址", value: item.address || "-" },
        { label: "统一社会信用代码", value: item.business_license_number || "-" },
      ];
      const accountLines = [
        { label: "账号 ID", value: String(item.user_id || "-") },
        { label: "用户名", value: item.username || "-" },
        { label: "认证状态", value: statusText(item.verification_status) },
        { label: "账号状态", value: item.is_disabled ? "已禁用" : "正常" },
        { label: "创建时间", value: item.created_at || "-" },
        { label: "更新时间", value: item.updated_at || "-" },
      ];
      const techCount = Array.isArray(item.technicians) ? item.technicians.length : 0;
      const techLines = [{ label: "绑定技师数", value: String(techCount) }];
      const licenseHtml = item.business_license
        ? `<div style="margin-top:.5rem;"><img src="${adminEscapeHtml(item.business_license)}" alt="营业执照" style="max-width:100%;max-height:220px;border:1px solid #e5e7eb;border-radius:8px;background:#fff;object-fit:contain;" /></div>`
        : `<div class="zy-empty-hint zy-empty-hint--tight" style="text-align:left;padding:.5rem 0;">未上传营业执照</div>`;

      return `
        <div>
          <div class="zy-detail-section-title">机构信息</div>
          ${adminDetailLinesHtml(baseLines)}
          <div class="zy-detail-section-title">账号信息</div>
          ${adminDetailLinesHtml(accountLines)}
          <div class="zy-detail-section-title">资质与关联</div>
          ${adminDetailLinesHtml(techLines)}
          ${licenseHtml}
        </div>
      `;
    };

    async function loadList() {
      const q = root.querySelector("#org_q").value.trim();
      const verification_status = root.querySelector("#org_status").value;
      const params = new URLSearchParams();
      if (q) params.append("q", q);
      if (verification_status) params.append("verification_status", verification_status);
      const data = await authFetch(`/api/admin/organizations?${params.toString()}`, { method: "GET" });
      const items = data.items || [];
      const tbody = root.querySelector("#org_tbody");
      if (!items.length) {
        tbody.innerHTML = adminTableEmptyRow(8);
        return;
      }
      tbody.innerHTML = items
        .map(
          (x) => `
        <tr>
          <td>${x.id}</td>
          <td>${x.company_name || "-"}</td>
          <td>${x.contact_person || "-"}</td>
          <td>${x.contact_phone || "-"}</td>
          <td>${statusText(x.verification_status)}</td>
          <td>${x.active_technician_count || 0}</td>
          <td>${x.pending_unbind_count || 0}</td>
          <td><div class="zy-actions">${actionButtons(x)}</div></td>
        </tr>
      `
        )
        .join("");
    }

    root.addEventListener("click", async (e) => {
      const btn = e.target.closest("[data-action]");
      if (!btn) return;
      const id = btn.getAttribute("data-id");
      const action = btn.getAttribute("data-action");
      if (!id || !action) return;

      try {
        if (action === "detail") {
          const item = await authFetch(`/api/admin/organizations/${id}`, { method: "GET" });
          openDrawer(
            `机构详情 #${item.id}`,
            renderOrgDetailHtml(item),
            `<button class="zy-btn zy-btn-secondary zy-btn-sm" id="org_drawer_close_btn" type="button">关闭</button>`
          );
          root.querySelector("#org_drawer_close_btn").addEventListener("click", closeDrawer);
          return;
        }
        await authFetch(`/api/admin/organizations/${id}/review/${action}`, { method: "POST", body: "{}" });
        showToast("操作成功", "success");
        await loadList();
      } catch (err) {
        showToast(err.message || "操作失败", "error");
      }
    });

    root.querySelector("#org_search").addEventListener("click", loadList);
    root.querySelector("#org_q").addEventListener("keydown", (e) => {
      if (e.key === "Enter") loadList();
    });
    await loadList();
  },
};
