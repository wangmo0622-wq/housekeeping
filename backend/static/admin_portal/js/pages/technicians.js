window.AdminPortalPages["technicians"] = {
  render: async function (root, token) {
    const MAX_LICENSE_FILES = 6;
    root.innerHTML = `
      <div class="zy-card">
        <div class="zy-card-body">
          <div class="zy-search-toolbar mb-4">
            <div class="zy-search-toolbar-top">
              <div class="zy-search-keyword">
                <label class="zy-search-label">关键词</label>
                <input type="search" id="tech_q_search" placeholder="姓名 / 手机 / 服务类型 / 身份证 / 服务区域" class="zy-form-input w-full" />
              </div>
              <button type="button" id="tech_toggle_advanced" class="zy-btn zy-btn-secondary zy-btn-sm zy-search-advanced-toggle">高级筛选</button>
            </div>
            <div class="zy-search-advanced-panel is-collapsed" id="tech_advanced_panel">
              <div class="zy-search-bar">
        <div class="zy-search-item">
          <label class="zy-search-label">姓名</label>
          <input type="text" id="tech_name_search" placeholder="请输入" class="zy-form-input zy-search-control-md" />
        </div>
        <div class="zy-search-item">
          <label class="zy-search-label">手机号</label>
          <input type="text" id="tech_phone_search" placeholder="请输入" class="zy-form-input zy-search-control-md" />
        </div>
        <div class="zy-search-item">
          <label class="zy-search-label">服务类型</label>
          <input type="text" id="tech_service_search" placeholder="请输入" class="zy-form-input zy-search-control-md" />
        </div>
        <div class="zy-search-item">
          <label class="zy-search-label">工作年限</label>
          <input type="text" id="tech_work_years_search" placeholder="请输入" class="zy-form-input zy-search-control-sm" />
        </div>
        <div class="zy-search-item">
          <label class="zy-search-label">更新时间</label>
          <input type="date" id="tech_date_search" class="zy-form-input zy-search-control-md" />
        </div>
        <div class="zy-search-item has-select">
          <label class="zy-search-label">审核状态</label>
          <select id="tech_status_filter" class="zy-select zy-search-control-sm">
            <option value="">全部状态</option>
            <option value="pending">待审核</option>
            <option value="approved">已通过</option>
            <option value="rejected">未通过</option>
          </select>
        </div>
        <div class="zy-search-actions">
          <button id="tech_reload_btn" class="zy-btn zy-btn-reset zy-btn-sm">重置</button>
          <button id="tech_query_btn" class="zy-btn zy-btn-query zy-btn-sm">查询</button>
        </div>
              </div>
            </div>
          </div>
          <div class="zy-table-scroll">
            <table class="zy-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>姓名</th>
                  <th>性别</th>
                  <th>年龄</th>
                  <th>手机号</th>
                  <th>身份证</th>
                  <th>服务类型</th>
                  <th>工作年限</th>
                  <th>服务区域</th>
                  <th>认证状态</th>
                  <th>推荐状态</th>
                  <th>更新时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody id="tech_tbody"></tbody>
            </table>
          </div>
          <div id="tech_pagination" class="zy-pagination"></div>
        </div>
      </div>

      <!-- 右侧抽屉 -->
      <div id="tech_drawer_overlay" class="zy-drawer-overlay">
        <div class="zy-drawer">
          <div class="zy-drawer-header">
            <h3 class="zy-drawer-title" id="tech_drawer_title">详情</h3>
            <button class="zy-drawer-close" id="tech_drawer_close">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-5 h-5">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
          <div class="zy-drawer-body" id="tech_drawer_body"></div>
          <div class="zy-drawer-footer" id="tech_drawer_footer"></div>
        </div>
      </div>
    `;

    let currentPage = 1;
    let pageSize = 10;
    let totalPages = 0;
    let allItems = [];

    const drawerOverlay = root.querySelector("#tech_drawer_overlay");
    const drawerTitle = root.querySelector("#tech_drawer_title");
    const drawerBody = root.querySelector("#tech_drawer_body");
    const drawerFooter = root.querySelector("#tech_drawer_footer");
    const drawerClose = root.querySelector("#tech_drawer_close");

    function openDrawer(title, bodyHtml, footerHtml) {
      drawerTitle.textContent = title;
      drawerBody.innerHTML = bodyHtml;
      drawerFooter.innerHTML = footerHtml;
      drawerOverlay.classList.add("active");
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

    const techAdvPanel = root.querySelector("#tech_advanced_panel");
    const techAdvToggle = root.querySelector("#tech_toggle_advanced");
    if (techAdvToggle && techAdvPanel) {
      techAdvToggle.addEventListener("click", () => {
        techAdvPanel.classList.toggle("is-collapsed");
        techAdvToggle.textContent = techAdvPanel.classList.contains("is-collapsed") ? "高级筛选" : "收起筛选";
      });
    }

    const runTechSearch = () => {
      currentPage = 1;
      loadList();
    };
    const debouncedTechQ =
      typeof window.adminDebounce === "function"
        ? window.adminDebounce(runTechSearch, 320)
        : runTechSearch;
    root.querySelector("#tech_q_search").addEventListener("input", debouncedTechQ);

    function renderPagination(total, page, totalPages, pageSize) {
      window.renderAdminPagination({
        root,
        containerSelector: "#tech_pagination",
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
      const qSearch = root.querySelector("#tech_q_search").value.trim();
      const nameSearch = root.querySelector("#tech_name_search").value.trim();
      const phoneSearch = root.querySelector("#tech_phone_search").value.trim();
      const serviceSearch = root.querySelector("#tech_service_search").value.trim();
      const workYearsSearch = root.querySelector("#tech_work_years_search").value.trim();
      const dateSearch = root.querySelector("#tech_date_search").value;
      const status = root.querySelector("#tech_status_filter").value;

      const params = new URLSearchParams();
      params.append("page", currentPage);
      params.append("page_size", pageSize);
      if (qSearch) params.append("q", qSearch);
      if (nameSearch) params.append("name", nameSearch);
      if (phoneSearch) params.append("phone", phoneSearch);
      if (serviceSearch) params.append("service_types", serviceSearch);
      if (workYearsSearch) params.append("work_years", workYearsSearch);
      if (dateSearch) params.append("date", dateSearch);
      if (status) params.append("status", status);

      const data = await authFetch(`/api/admin/technicians?${params.toString()}`, { method: "GET" });
      allItems = data.items || [];
      totalPages = data.total_pages || 1;

      const tbody = root.querySelector("#tech_tbody");
      const statusBadge = (v) => {
        const map = {
          pending: '<span class="zy-badge zy-badge-warning">待审核</span>',
          approved: '<span class="zy-badge zy-badge-success">已通过</span>',
          rejected: '<span class="zy-badge zy-badge-danger">未通过</span>'
        };
        return map[v] || v || "-";
      };
      
      const recommendBadge = (isRecommended) => {
        return isRecommended ? '<span class="zy-badge zy-badge-primary">已推荐</span>' : '<span class="zy-badge zy-badge-secondary">未推荐</span>';
      };

      const genderMap = {
        male: '男',
        female: '女',
        '': '-'
      };

      const formatServiceAreas = (areas) => {
        if (!areas) return '-';
        const areaList = areas.split(',').filter(a => a.trim());
        if (areaList.length === 0) return '-';
        if (areaList.length <= 2) return areaList.join('、');
        return areaList.slice(0, 2).join('、') + `等${areaList.length}个区域`;
      };

      const formatWorkYears = (years) => {
        const workYearsMap = {
          0: '一年以下',
          1: '1-3年',
          2: '3-5年',
          3: '5-10年',
          4: '10年以上'
        };
        return workYearsMap[years] || '-';
      };

      if (allItems.length === 0) {
        tbody.innerHTML = adminTableEmptyRow(13);
        renderPagination(0, 1, 0, pageSize);
        return;
      }

      tbody.innerHTML = allItems
        .map((x) => {
          const isPending = x.verification_status === "pending";
          return `
            <tr>
              <td>${x.id}</td>
              <td>${x.real_name || ""}</td>
              <td>${genderMap[x.gender] || '-'}</td>
              <td>${x.age !== null && x.age !== undefined ? x.age + '岁' : '-'}</td>
              <td>${x.phone || ""}</td>
              <td>${x.id_card_no || "-"}</td>
              <td>${x.service_types || "-"}</td>
              <td>${formatWorkYears(x.work_years)}</td>
              <td>${formatServiceAreas(x.service_areas)}</td>
              <td>${statusBadge(x.verification_status)}</td>
              <td>${recommendBadge(x.is_recommended)}</td>
              <td>${x.updated_at || ""}</td>
              <td>
                <div class="zy-actions">
                  ${isPending ? '<a class="zy-action-link text-blue-500" data-action="review" data-id="' + x.id + '">审核</a>' : ''}
                  <a class="zy-action-link" data-action="detail" data-id="${x.id}">详情</a>
                  <a class="zy-action-link text-blue-500" data-action="edit" data-id="${x.id}">编辑</a>
                  <a class="zy-action-link ${x.is_recommended ? 'text-gray-500' : 'text-blue-500'}" data-action="recommend" data-id="${x.id}">${x.is_recommended ? '取消推荐' : '推荐'}</a>
                  <a class="zy-action-link zy-action-link--danger" data-action="delete" data-id="${x.id}">删除</a>
                </div>
              </td>
            </tr>
          `;
        })
        .join("");

      renderPagination(data.total || 0, currentPage, totalPages, pageSize);
    }

    async function toggleRecommend(id) {
      try {
        const response = await authFetch(`/api/admin/technicians/${id}/verification/recommend`, {
          method: "POST",
        });
        if (response.ok) {
          loadList();
        }
      } catch (err) {
        alert(`操作失败: ${err.message || "未知错误"}`);
      }
    }

    function renderVerificationHistory(verifications) {
      if (!verifications || verifications.length === 0) {
        return '<p class="zy-empty-hint zy-empty-hint--tight">暂无审核记录</p>';
      }
      return verifications.map(v => {
        const statusMap = {
          pending: '<span class="zy-badge zy-badge-warning">待审核</span>',
          approved: '<span class="zy-badge zy-badge-success">已通过</span>',
          rejected: '<span class="zy-badge zy-badge-danger">已驳回</span>'
        };
        const typeMap = {
          idcard: '身份证',
          license: '从业资质',
          health: '健康证',
          criminal: '无犯罪记录',
          other: '其他'
        };
        return `
          <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
              <span style="font-weight: 500; color: #1f2937;">${typeMap[v.verification_type] || v.verification_type}</span>
              ${statusMap[v.status] || v.status}
            </div>
            <div style="font-size: 13px; color: #6b7280;">
              ${v.submitted_at ? '提交时间: ' + v.submitted_at : ''}
            </div>
            ${v.reviewed_at ? `
              <div style="font-size: 13px; color: #6b7280; margin-top: 4px;">
                审核时间: ${v.reviewed_at}
              </div>
            ` : ''}
            ${v.admin_note ? `
              <div style="font-size: 13px; color: #374151; margin-top: 8px; padding: 8px; background: #f9fafb; border-radius: 4px;">
                审核备注: ${v.admin_note}
              </div>
            ` : ''}
          </div>
        `;
      }).join("");
    }

    function renderInfoField(label, value) {
      return `
        <div style="display: grid; grid-template-columns: 100px 1fr; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f3f4f6;">
          <span style="color: #6b7280;">${label}</span>
          <span style="color: #1f2937;">${value || '-'}</span>
        </div>
      `;
    }

    function renderEditField(label, controlHtml) {
      return `
        <div style="display: grid; grid-template-columns: 100px 1fr; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f3f4f6; align-items: center;">
          <span style="color: #6b7280;">${label}</span>
          <div style="color: #1f2937;">${controlHtml}</div>
        </div>
      `;
    }

    root.addEventListener("click", async (e) => {
      const btn = e.target.closest("[data-action]");
      if (!btn) return;
      const action = btn.getAttribute("data-action");
      const id = btn.getAttribute("data-id");
      if (!action || !id) return;

      e.preventDefault();

      if (action === "detail") {
        const item = await authFetch(`/api/admin/technicians/${id}`, { method: "GET" });
        const genderMap = { male: '男', female: '女' };
        const formatAreas = (areas) => {
          if (!areas) return '-';
          const list = areas.split(',').filter(a => a.trim());
          return list.length > 0 ? list.join('、') : '-';
        };
        const formatWorkYearsDetail = (years) => {
          const workYearsMap = {
            0: '一年以下',
            1: '1-3年',
            2: '3-5年',
            3: '5-10年',
            4: '10年以上'
          };
          return workYearsMap[years] || '-';
        };
        openDrawer(
          "技师详情",
          `
            <div style="font-size: 14px;">
              <h4 style="color: #1f2937; font-weight: 500; margin-bottom: 16px;">基本信息</h4>
              ${renderInfoField('姓名', item.real_name)}
              ${renderInfoField('性别', genderMap[item.gender] || '-')}
              ${renderInfoField('年龄', item.age !== null && item.age !== undefined ? item.age + '岁' : '-')}
              ${renderInfoField('手机号', item.phone)}
              ${renderInfoField('身份证号', item.id_card_no)}
              ${renderInfoField('个人简介', item.bio || '-')}
              ${renderInfoField('服务类型', item.service_types)}
              ${renderInfoField('工作年限', formatWorkYearsDetail(item.work_years))}

              <h4 style="color: #1f2937; font-weight: 500; margin: 20px 0 12px;">证件照片</h4>
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
                ${item.id_card_front ? `<div style="position: relative;"><span style="color: #6b7280; display: block; margin-bottom: 6px; font-size:12px;">身份证正面</span><div style="cursor:pointer;" onclick="showImgPreview('${item.id_card_front}')"><img src="${item.id_card_front}" style="width: 100%; height: 120px; object-fit: contain; border-radius: 8px; background: #f3f4f6;"></div></div>` : `<div style="position: relative;"><span style="color: #6b7280; display: block; margin-bottom: 6px; font-size:12px;">身份证正面</span><div style="height: 120px; background: #f3f4f6; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #9ca3af; font-size:12px;">未上传</div></div>`}
                ${item.id_card_back ? `<div style="position: relative;"><span style="color: #6b7280; display: block; margin-bottom: 6px; font-size:12px;">身份证反面</span><div style="cursor:pointer;" onclick="showImgPreview('${item.id_card_back}')"><img src="${item.id_card_back}" style="width: 100%; height: 120px; object-fit: contain; border-radius: 8px; background: #f3f4f6;"></div></div>` : `<div style="position: relative;"><span style="color: #6b7280; display: block; margin-bottom: 6px; font-size:12px;">身份证反面</span><div style="height: 120px; background: #f3f4f6; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #9ca3af; font-size:12px;">未上传</div></div>`}
              </div>

              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
                ${item.avatar ? `
                  <div style="position: relative;">
                    <span style="color: #6b7280; display: block; margin-bottom: 6px; font-size:12px;">形象照片</span>
                    <div style="cursor:pointer;" onclick="showImgPreview('${item.avatar}')"><img src="${item.avatar}" style="width: 100%; height: 120px; object-fit: contain; border-radius: 8px; background: #f3f4f6;"></div>
                  </div>
                ` : `
                  <div style="position: relative;">
                    <span style="color: #6b7280; display: block; margin-bottom: 6px; font-size:12px;">形象照片</span>
                    <div style="height: 120px; background: #f3f4f6; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #9ca3af; font-size:12px;">未上传</div>
                  </div>
                `}

                ${item.health_cert ? `
                  <div style="position: relative;">
                    <span style="color: #6b7280; display: block; margin-bottom: 6px; font-size:12px;">健康证</span>
                    <div style="cursor:pointer;" onclick="showImgPreview('${item.health_cert}')"><img src="${item.health_cert}" style="width: 100%; height: 120px; object-fit: contain; border-radius: 8px; background: #f3f4f6;"></div>
                  </div>
                ` : `
                  <div style="position: relative;">
                    <span style="color: #6b7280; display: block; margin-bottom: 6px; font-size:12px;">健康证</span>
                    <div style="height: 120px; background: #f3f4f6; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #9ca3af; font-size:12px;">未上传</div>
                  </div>
                `}
              </div>

              <h4 style="color: #1f2937; font-weight: 500; margin: 20px 0 12px;">执照文件</h4>
              <div style="margin-bottom: 16px;">
                ${item.licenses && item.licenses.length > 0 ? `
                  <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 12px;">
                    ${item.licenses.map((license, index) => {
                      const licenseUrl = typeof license === 'string' ? license : (license && license.url) || '';
                      return `
                      <div style="position: relative;">
                        <span style="color: #6b7280; display: block; margin-bottom: 6px; font-size:12px;">执照${index + 1}</span>
                        <div style="cursor:pointer;" onclick="showImgPreview('${licenseUrl}')" title="执照${index + 1}">
                          <img src="${licenseUrl}" style="width: 100%; height: 120px; object-fit: contain; border-radius: 8px; background: #f3f4f6;">
                        </div>
                      </div>
                    `;
                    }).join('')}
                  </div>
                ` : `
                  <div style="width: 120px; height: 120px; background: #f3f4f6; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #9ca3af; font-size:12px;">未上传</div>
                `}
              </div>

              <h4 style="color: #1f2937; font-weight: 500; margin: 20px 0 16px;">二维码</h4>
              <div style="margin-bottom: 16px;">
                ${item.qrcode ? `
                  <div style="display: flex; flex-direction: column; align-items: center;">
                    <img src="${item.qrcode}" style="width: 200px; height: 200px; object-fit: contain; margin-bottom: 12px;">
                    <span style="color: #6b7280; font-size: 12px;">扫码查看技师详情</span>
                  </div>
                ` : `
                  <div style="width: 200px; height: 200px; background: #f3f4f6; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #9ca3af; font-size:12px;">二维码生成失败</div>
                `}
              </div>

              <h4 style="color: #1f2937; font-weight: 500; margin: 20px 0 16px;">审核记录</h4>
              ${renderVerificationHistory(item.verifications)}
            </div>
          `,
          `<button class="zy-btn zy-btn-secondary zy-btn-sm" id="drawer_close_btn">关闭</button>`
        );
        root.querySelector("#drawer_close_btn").addEventListener("click", closeDrawer);
        return;
      }

      if (action === "review") {
        const item = await authFetch(`/api/admin/technicians/${id}`, { method: "GET" });
        const genderMap = { male: '男', female: '女' };
        const formatAreas = (areas) => {
          if (!areas) return '-';
          const list = areas.split(',').filter(a => a.trim());
          return list.length > 0 ? list.join('、') : '-';
        };
        const formatWorkYearsReview = (years) => {
          const workYearsMap = {
            0: '一年以下',
            1: '1-3年',
            2: '3-5年',
            3: '5-10年',
            4: '10年以上'
          };
          return workYearsMap[years] || '-';
        };
        openDrawer(
          "审核技师",
          `
            <div style="font-size: 14px;">
              <h4 style="color: #1f2937; font-weight: 500; margin-bottom: 16px;">基本信息</h4>
              ${renderInfoField('姓名', item.real_name)}
              ${renderInfoField('性别', genderMap[item.gender] || '-')}
              ${renderInfoField('年龄', item.age !== null && item.age !== undefined ? item.age + '岁' : '-')}
              ${renderInfoField('手机号', item.phone)}
              ${renderInfoField('身份证号', item.id_card_no)}
              ${renderInfoField('个人简介', item.bio || '-')}
              ${renderInfoField('服务类型', item.service_types)}
              ${renderInfoField('工作年限', formatWorkYearsReview(item.work_years))}

              <h4 style="color: #1f2937; font-weight: 500; margin: 20px 0 12px;">证件照片</h4>
              <div style="display: grid; grid-template-columns:1fr 1fr; gap: 16px; margin-bottom: 16px;">
                ${item.id_card_front ? `<div style="position: relative;"><span style="color: #6b7280; display: block; margin-bottom: 6px; font-size:12px;">身份证正面</span><div style="cursor:pointer;" onclick="showImgPreview('${item.id_card_front}')"><img src="${item.id_card_front}" style="width: 100%; height: 120px; object-fit: contain; border-radius: 8px; background: #f3f4f6;"></div></div>` : `<div style="position: relative;"><span style="color: #6b7280; display: block; margin-bottom: 6px; font-size:12px;">身份证正面</span><div style="height: 120px; background: #f3f4f6; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #9ca3af; font-size:12px;">未上传</div></div>`}
                ${item.id_card_back ? `<div style="position: relative;"><span style="color: #6b7280; display: block; margin-bottom: 6px; font-size:12px;">身份证反面</span><div style="cursor:pointer;" onclick="showImgPreview('${item.id_card_back}')"><img src="${item.id_card_back}" style="width: 100%; height: 120px; object-fit: contain; border-radius: 8px; background: #f3f4f6;"></div></div>` : `<div style="position: relative;"><span style="color: #6b7280; display: block; margin-bottom: 6px; font-size:12px;">身份证反面</span><div style="height: 120px; background: #f3f4f6; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #9ca3af; font-size:12px;">未上传</div></div>`}
              </div>

              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
                ${item.avatar ? `
                  <div style="position: relative;">
                    <span style="color: #6b7280; display: block; margin-bottom: 6px; font-size:12px;">形象照片</span>
                    <div style="cursor:pointer;" onclick="showImgPreview('${item.avatar}')"><img src="${item.avatar}" style="width: 100%; height: 120px; object-fit: contain; border-radius: 8px; background: #f3f4f6;"></div>
                  </div>
                ` : `
                  <div style="position: relative;">
                    <span style="color: #6b7280; display: block; margin-bottom: 6px; font-size:12px;">形象照片</span>
                    <div style="height: 120px; background: #f3f4f6; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #9ca3af; font-size:12px;">未上传</div>
                  </div>
                `}

                ${item.health_cert ? `
                  <div style="position: relative;">
                    <span style="color: #6b7280; display: block; margin-bottom: 6px; font-size:12px;">健康证</span>
                    <div style="cursor:pointer;" onclick="showImgPreview('${item.health_cert}')"><img src="${item.health_cert}" style="width: 100%; height: 120px; object-fit: contain; border-radius: 8px; background: #f3f4f6;"></div>
                  </div>
                ` : `
                  <div style="position: relative;">
                    <span style="color: #6b7280; display: block; margin-bottom: 6px; font-size:12px;">健康证</span>
                    <div style="height: 120px; background: #f3f4f6; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #9ca3af; font-size:12px;">未上传</div>
                  </div>
                `}
              </div>

              <h4 style="color: #1f2937; font-weight: 500; margin: 20px 0 12px;">执照文件</h4>
              <div style="margin-bottom: 16px;">
                ${item.licenses && item.licenses.length > 0 ? `
                  <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 12px;">
                    ${item.licenses.map((license, index) => {
                      const licenseUrl = typeof license === 'string' ? license : (license && license.url) || '';
                      return `
                      <div style="position: relative;">
                        <span style="color: #6b7280; display: block; margin-bottom: 6px; font-size:12px;">执照${index + 1}</span>
                        <div style="cursor:pointer;" onclick="showImgPreview('${licenseUrl}')" title="执照${index + 1}">
                          <img src="${licenseUrl}" style="width: 100%; height: 120px; object-fit: contain; border-radius: 8px; background: #f3f4f6;">
                        </div>
                      </div>
                    `;
                    }).join('')}
                  </div>
                ` : `
                  <div style="width: 120px; height: 120px; background: #f3f4f6; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #9ca3af; font-size:12px;">未上传</div>
                `}
              </div>

              <h4 style="color: #1f2937; font-weight: 500; margin: 20px 0 16px;">二维码</h4>
              <div style="margin-bottom: 16px;">
                ${item.qrcode ? `
                  <div style="display: flex; flex-direction: column; align-items: center;">
                    <img src="${item.qrcode}" style="width: 200px; height: 200px; object-fit: contain; margin-bottom: 12px;">
                    <span style="color: #6b7280; font-size: 12px;">扫码查看技师详情</span>
                  </div>
                ` : `
                  <div style="width: 200px; height: 200px; background: #f3f4f6; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #9ca3af; font-size:12px;">二维码生成失败</div>
                `}
              </div>

              <h4 style="color: #1f2937; font-weight: 500; margin: 20px 0 16px;">审核记录</h4>
              ${renderVerificationHistory(item.verifications)}

              <h4 style="color: #1f2937; font-weight: 500; margin: 20px 0 12px;">审核操作</h4>
              <textarea id="verify_note" class="zy-form-textarea" rows="3" placeholder="请输入审核备注（可选）" style="margin-bottom: 12px;"></textarea>
            </div>
          `,
          `<button class="zy-btn zy-btn-secondary zy-btn-sm" id="drawer_cancel">取消</button><button class="zy-btn zy-btn-danger zy-btn-sm" id="drawer_reject">驳回</button><button class="zy-btn zy-btn-success zy-btn-sm" id="drawer_approve">通过</button>`
        );

        root.querySelector("#drawer_cancel").addEventListener("click", closeDrawer);
        root.querySelector("#drawer_reject").addEventListener("click", async () => {
          const note = root.querySelector("#verify_note").value;
          try {
            await authFetch(`/api/admin/technicians/${id}/verification/reject`, {
              method: "POST",
              body: JSON.stringify({ note }),
            });
            showToast({ title: "操作成功", message: "技师认证已驳回", type: "success" });
            closeDrawer();
            await loadList();
          } catch (err) {
            showToast({ title: "操作失败", message: err.message, type: "error" });
          }
        });
        root.querySelector("#drawer_approve").addEventListener("click", async () => {
          const note = root.querySelector("#verify_note").value;
          try {
            await authFetch(`/api/admin/technicians/${id}/verification/approve`, {
              method: "POST",
              body: JSON.stringify({ note }),
            });
            showToast({ title: "操作成功", message: "技师认证已通过", type: "success" });
            closeDrawer();
            await loadList();
          } catch (err) {
            showToast({ title: "操作失败", message: err.message, type: "error" });
          }
        });
        return;
      }

      if (action === "edit") {
        const item = await authFetch(`/api/admin/technicians/${id}`, { method: "GET" });
        const workYearMap = {
          0: "一年以下",
          1: "1-3年",
          2: "3-5年",
          3: "5-10年",
          4: "10年以上",
        };
        const workYearOptions = Object.keys(workYearMap)
          .map((val) => `<option value="${val}" ${String(item.work_years) === val ? "selected" : ""}>${workYearMap[val]}</option>`)
          .join("");
        const verStatusText = (v) =>
          ({ uninitiated: "未发起", pending: "待审核", approved: "已通过", rejected: "未通过" }[v] || v || "—");
        const row = (label, inner) => `<div class="org-form-grid"><label>${escapeHtml(label)}</label><div>${inner}</div></div>`;
        const imgSlot = (idBase, label, url) => {
          const has = !!url;
          return `<div><div style="color:#64748b;font-size:12px;margin-bottom:4px;">${escapeHtml(label)}</div>
          <div id="${idBase}_trigger" class="org-img-slot" style="position:relative;">
            <img id="${idBase}_preview" src="${has ? escapeAttr(url) : ""}" style="${has ? "" : "display:none;"}" alt="" />
            <span id="${idBase}_ph" class="org-img-ph" style="${has ? "display:none;" : ""}">点击上传或替换</span>
            <button id="${idBase}_remove" type="button" class="zy-thumb-remove" style="${has ? "" : "display:none;"}" title="删除">×</button>
          </div>
          <input id="${idBase}_file" type="file" accept="image/*" style="display:none;" /></div>`;
        };
        const bodyHtml = `
        <div class="org-service-edit">
          <div class="org-field-section">
        <div class="org-field-title">基本信息</div>
        ${row("技师 ID", `<span class="org-pub-badge">#${escapeHtml(String(item.id))}</span>`)}
        ${row("当前认证", `<span>${escapeHtml(verStatusText(item.verification_status))}</span>`)}
        ${row("系统认证(调整)", `<select id="ate_pass_status" class="ipt">
          <option value="uninitiated" ${item.verification_status === "uninitiated" ? "selected" : ""}>未发起认证</option>
          <option value="pending" ${item.verification_status === "pending" ? "selected" : ""}>待审核</option>
          <option value="approved" ${item.verification_status === "approved" ? "selected" : ""}>已通过</option>
          <option value="rejected" ${item.verification_status === "rejected" ? "selected" : ""}>未通过</option>
        </select><p class="org-form-hint">后台可直接调整认证状态，请谨慎操作。</p>`)}
        ${row("姓名", `<input id="ate_real_name" class="ipt" value="${escapeAttr(item.real_name)}" />`)}
        ${row("手机号", `<input id="ate_phone" class="ipt" value="${escapeAttr(item.phone)}" />`)}
        ${row("身份证号", `<input id="ate_id_card_no" class="ipt" value="${escapeAttr(item.id_card_no)}" />`)}
        ${row("性别", `<select id="ate_gender" class="ipt"><option value="">未填写</option><option value="male" ${item.gender === "male" ? "selected" : ""}>男</option><option value="female" ${item.gender === "female" ? "selected" : ""}>女</option></select>`)}
        ${row("工作年限", `<select id="ate_work_years" class="ipt">${workYearOptions}</select>`)}
        ${row("服务类型", `<input id="ate_service_types" class="ipt" value="${escapeAttr(item.service_types)}" />`)}
        ${row("服务区域", `<input id="ate_service_areas" class="ipt" value="${escapeAttr(item.service_areas)}" />`)}
        ${row("简介", `<textarea id="ate_bio" class="txt" style="min-height:80px;">${escapeHtml(item.bio)}</textarea>`)}
          </div>
          <div class="org-field-section">
            <div class="org-field-title">证件与材料（点击图片替换）</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
              ${imgSlot("ate_avatar", "形象照", item.avatar)}
              ${imgSlot("ate_health", "健康证", item.health_cert)}
              ${imgSlot("ate_idf", "身份证正面", item.id_card_front)}
              ${imgSlot("ate_idb", "身份证反面", item.id_card_back)}
            </div>
            <div class="org-field-title" style="margin-top:1.25rem;">执照（可删除、可追加）</div>
            <div id="ate_lic_trigger" class="org-cover-dropzone"></div>
            <input id="ate_licenses" type="file" accept="image/*" multiple style="display:none;" />
          </div>
        </div>
        `;
        openDrawer(
          "编辑技师",
          bodyHtml,
          `<button class="zy-btn zy-btn-secondary zy-btn-sm" id="ate_cancel">取消</button><button class="zy-btn zy-btn-primary zy-btn-sm" id="ate_save">保存</button>`
        );
        const bindImg = (base) => {
          const tr = root.querySelector(`#${base}_trigger`);
          const fi = root.querySelector(`#${base}_file`);
          const pr = root.querySelector(`#${base}_preview`);
          const ph = root.querySelector(`#${base}_ph`);
          const rm = root.querySelector(`#${base}_remove`);
          let removed = false;
          tr.addEventListener("click", (e) => {
            if (e.target.closest(`#${base}_remove`)) return;
            fi.click();
          });
          if (rm) {
            rm.addEventListener("click", (e) => {
              e.preventDefault();
              e.stopPropagation();
              fi.value = "";
              pr.src = "";
              pr.style.display = "none";
              if (ph) ph.style.display = "";
              rm.style.display = "none";
              removed = true;
            });
          }
          fi.addEventListener("change", () => {
            const file = fi.files && fi.files[0];
            if (!file) return;
            pr.src = URL.createObjectURL(file);
            pr.style.display = "block";
            if (ph) ph.style.display = "none";
            if (rm) rm.style.display = "";
            removed = false;
          });
          return {
            getRemoved: () => removed,
            getFile: () => (fi.files && fi.files[0]) || null,
          };
        };
        const imageBindings = {
          avatar: bindImg("ate_avatar"),
          health: bindImg("ate_health"),
          idf: bindImg("ate_idf"),
          idb: bindImg("ate_idb"),
        };
        const lt = root.querySelector("#ate_lic_trigger");
        const li = root.querySelector("#ate_licenses");
        let existingLicenses = (Array.isArray(item.licenses) ? item.licenses : [])
          .map((license) => {
            if (typeof license === "string") {
              return { id: null, url: license };
            }
            return { id: license && license.id != null ? Number(license.id) : null, url: (license && license.url) || "" };
          })
          .filter((license) => !!license.url);
        let selectedLicenseFiles = [];
        const renderUploadTile = () => '<button type="button" class="zy-upload-plus-tile" id="ate_lic_add" title="上传执照">+</button>';
        const renderSelectedLicenses = () => {
          const existingHtml = existingLicenses
            .map((license, index) => `<div class="zy-thumb-item"><img src="${escapeAttr(license.url)}" class="org-thumb" alt="" /><button type="button" class="zy-thumb-remove" data-existing-license-index="${index}" title="删除">×</button></div>`)
            .join("");
          const selectedHtml = selectedLicenseFiles
            .map((file, index) => {
              const url = URL.createObjectURL(file);
              return `<div class="zy-thumb-item"><img src="${url}" class="org-thumb" alt="" /><button type="button" class="zy-thumb-remove" data-license-index="${index}" title="删除">×</button></div>`;
            })
            .join("");
          const totalLicenses = existingLicenses.length + selectedLicenseFiles.length;
          const canAddMore = totalLicenses < MAX_LICENSE_FILES;
          const hintHtml = selectedLicenseFiles.length || existingLicenses.length
            ? '<div style="grid-column:1/-1;width:100%;color:#94a3b8;font-size:12px;">支持删除已上传图片；新选择的文件将追加上传</div>'
            : "";
          const uploadTileHtml = canAddMore ? renderUploadTile() : "";
          lt.innerHTML = `${existingHtml}${selectedHtml}${uploadTileHtml}${hintHtml}`;
        };
        renderSelectedLicenses();
        li.addEventListener("change", () => {
          const incoming = Array.from(li.files || []);
          const remain = Math.max(0, MAX_LICENSE_FILES - existingLicenses.length - selectedLicenseFiles.length);
          if (remain > 0) {
            selectedLicenseFiles = selectedLicenseFiles.concat(incoming.slice(0, remain));
          }
          if (incoming.length > remain) {
            showToast({ title: "上传提示", message: `执照最多支持 ${MAX_LICENSE_FILES} 张`, type: "warning" });
          }
          li.value = "";
          renderSelectedLicenses();
        });
        lt.addEventListener("click", (e) => {
          if (e.target.closest("#ate_lic_add")) {
            li.click();
            return;
          }
          const existingBtn = e.target.closest("[data-existing-license-index]");
          if (existingBtn) {
            e.preventDefault();
            const idx = Number(existingBtn.getAttribute("data-existing-license-index"));
            if (Number.isNaN(idx)) return;
            existingLicenses.splice(idx, 1);
            renderSelectedLicenses();
            return;
          }
          const btn = e.target.closest("[data-license-index]");
          if (!btn) return;
          e.preventDefault();
          const idx = Number(btn.getAttribute("data-license-index"));
          if (Number.isNaN(idx)) return;
          selectedLicenseFiles.splice(idx, 1);
          const dt = new DataTransfer();
          selectedLicenseFiles.forEach((f) => dt.items.add(f));
          li.files = dt.files;
          renderSelectedLicenses();
        });
        root.querySelector("#ate_cancel").addEventListener("click", closeDrawer);
        root.querySelector("#ate_save").addEventListener("click", async () => {
          const payload = new FormData();
          payload.append("real_name", root.querySelector("#ate_real_name").value.trim());
          payload.append("phone", root.querySelector("#ate_phone").value.trim());
          payload.append("id_card_no", root.querySelector("#ate_id_card_no").value.trim());
          payload.append("gender", root.querySelector("#ate_gender").value);
          payload.append("work_years", root.querySelector("#ate_work_years").value);
          payload.append("service_types", root.querySelector("#ate_service_types").value.trim());
          payload.append("service_areas", root.querySelector("#ate_service_areas").value.trim());
          payload.append("bio", root.querySelector("#ate_bio").value.trim());
          payload.append("verification_status", root.querySelector("#ate_pass_status").value);
          payload.append("is_disabled", item.is_disabled ? "1" : "0");
          payload.append("is_recommended", item.is_recommended ? "1" : "0");
          const avatarFile = imageBindings.avatar.getFile();
          const healthCertFile = imageBindings.health.getFile();
          const idCardFrontFile = imageBindings.idf.getFile();
          const idCardBackFile = imageBindings.idb.getFile();
          const licenseFiles = selectedLicenseFiles;
          if (avatarFile) payload.append("avatar", avatarFile);
          else if (imageBindings.avatar.getRemoved()) payload.append("remove_avatar", "1");
          if (healthCertFile) payload.append("health_cert", healthCertFile);
          else if (imageBindings.health.getRemoved()) payload.append("remove_health_cert", "1");
          if (idCardFrontFile) payload.append("id_card_front", idCardFrontFile);
          else if (imageBindings.idf.getRemoved()) payload.append("remove_id_card_front", "1");
          if (idCardBackFile) payload.append("id_card_back", idCardBackFile);
          else if (imageBindings.idb.getRemoved()) payload.append("remove_id_card_back", "1");
          existingLicenses.forEach((license) => {
            if (license.id != null) payload.append("kept_license_ids", String(license.id));
            payload.append("kept_license_urls", license.url);
          });
          licenseFiles.forEach((f) => payload.append("licenses", f));
          try {
            await authFetch(`/api/admin/technicians/${id}`, {
              method: "PATCH",
              body: payload,
            });
            showToast({ title: "保存成功", message: "技师信息已更新", type: "success" });
            closeDrawer();
            await loadList();
          } catch (err) {
            showToast({ title: "保存失败", message: err.message || "更新失败", type: "error" });
          }
        });
        return;
      }

      if (action === "delete") {
        showConfirm({
          title: "确认删除",
          message: "确定要删除该技师吗？此操作不可恢复。",
          confirmText: "删除",
          cancelText: "取消",
          type: "warning",
          onConfirm: async () => {
            try {
              await authFetch(`/api/admin/technicians/${id}`, { method: "DELETE" });
              showToast({ title: "操作成功", message: "技师已删除", type: "success" });
              await loadList();
            } catch (err) {
              showToast({ title: "操作失败", message: err.message, type: "error" });
            }
          },
        });
        return;
      }

      if (action === "recommend") {
        try {
          await toggleRecommend(id);
          showToast({ title: "操作成功", message: "推荐状态已更新", type: "success" });
        } catch (err) {
          showToast({ title: "操作失败", message: err.message, type: "error" });
        }
        return;
      }
    });

    root.querySelector("#tech_query_btn").addEventListener("click", () => {
      currentPage = 1;
      loadList();
    });
    root.querySelector("#tech_name_search").addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        currentPage = 1;
        loadList();
      }
    });
    root.querySelector("#tech_phone_search").addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        currentPage = 1;
        loadList();
      }
    });

    root.querySelector("#tech_reload_btn").addEventListener("click", () => {
      root.querySelector("#tech_q_search").value = "";
      root.querySelector("#tech_name_search").value = "";
      root.querySelector("#tech_phone_search").value = "";
      root.querySelector("#tech_service_search").value = "";
      root.querySelector("#tech_work_years_search").value = "";
      root.querySelector("#tech_date_search").value = "";
      root.querySelector("#tech_status_filter").value = "";
      if (techAdvPanel && techAdvToggle) {
        techAdvPanel.classList.add("is-collapsed");
        techAdvToggle.textContent = "高级筛选";
      }
      currentPage = 1;
      loadList();
    });
    await loadList();
  },
};
