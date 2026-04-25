window.AdminPortalPages["llm_providers"] = {
  render: async function (root) {
    root.innerHTML = `
      <div class="zy-card">
        <div class="zy-card-body">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:12px;">
            <h3 style="margin:0;font-size:18px;font-weight:600;">大模型管理</h3>
            <button id="btn-refresh-llm" class="zy-btn zy-btn-secondary zy-btn-sm">刷新</button>
          </div>
          <div id="llm-list"></div>
        </div>
      </div>
    `;

    const listEl = root.querySelector("#llm-list");
    const refreshBtn = root.querySelector("#btn-refresh-llm");

    function cardHtml(item) {
      const activeTag = item.is_active
        ? `<span class="zy-badge zy-badge-success">当前生效</span>`
        : `<span class="zy-badge">未生效</span>`;
      const enabledTag = item.is_enabled
        ? `<span class="zy-badge zy-badge-info">已启用</span>`
        : `<span class="zy-badge zy-badge-warning">已停用</span>`;
      return `
        <div class="zy-card" style="margin-bottom:12px;border:1px solid #e2e8f0;">
          <div class="zy-card-body">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:10px;">
              <div style="display:flex;gap:8px;align-items:center;">
                <strong>${adminEscapeHtml(item.display_name || item.provider)}</strong>
                ${activeTag}
                ${enabledTag}
              </div>
              <button class="zy-btn zy-btn-sm zy-btn-primary" data-role="activate" data-provider="${item.provider}" ${item.is_active ? "disabled" : ""}>设为当前</button>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
              <div>
                <label class="zy-form-label">API Base URL</label>
                <input class="zy-form-input" data-field="base_url" data-provider="${item.provider}" value="${adminEscapeHtml(item.base_url || "")}" />
              </div>
              <div>
                <label class="zy-form-label">模型名</label>
                <input class="zy-form-input" data-field="model_name" data-provider="${item.provider}" value="${adminEscapeHtml(item.model_name || "")}" />
              </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr auto auto;gap:10px;align-items:end;margin-top:10px;">
              <div>
                <label class="zy-form-label">API Key（留空表示不修改）</label>
                <input class="zy-form-input" data-field="api_key" data-provider="${item.provider}" placeholder="已配置：${adminEscapeHtml(item.api_key_masked || "未配置")}" />
              </div>
              <label style="display:flex;align-items:center;gap:6px;font-size:13px;color:#334155;">
                <input type="checkbox" data-field="is_enabled" data-provider="${item.provider}" ${item.is_enabled ? "checked" : ""} />
                启用
              </label>
              <button class="zy-btn zy-btn-sm" data-role="save" data-provider="${item.provider}">保存</button>
            </div>
            <div style="margin-top:8px;font-size:12px;color:#64748b;">最近更新：${adminEscapeHtml(item.updated_at || "-")}</div>
          </div>
        </div>
      `;
    }

    async function load() {
      const data = await authFetch("/api/admin/llm-providers", { method: "GET" });
      const items = data.items || [];
      listEl.innerHTML = items.map(cardHtml).join("") || `<div class="zy-alert zy-alert-warning">暂无配置</div>`;
    }

    listEl.addEventListener("click", async (e) => {
      const saveBtn = e.target.closest('[data-role="save"]');
      const activateBtn = e.target.closest('[data-role="activate"]');
      if (saveBtn) {
        const provider = saveBtn.getAttribute("data-provider");
        if (!provider) return;
        const baseUrlEl = listEl.querySelector(`[data-field="base_url"][data-provider="${provider}"]`);
        const modelEl = listEl.querySelector(`[data-field="model_name"][data-provider="${provider}"]`);
        const keyEl = listEl.querySelector(`[data-field="api_key"][data-provider="${provider}"]`);
        const enabledEl = listEl.querySelector(`[data-field="is_enabled"][data-provider="${provider}"]`);
        try {
          await authFetch(`/api/admin/llm-providers/${provider}`, {
            method: "PATCH",
            body: JSON.stringify({
              base_url: baseUrlEl ? baseUrlEl.value : "",
              model_name: modelEl ? modelEl.value : "",
              api_key: keyEl ? keyEl.value : "",
              is_enabled: !!(enabledEl && enabledEl.checked),
            }),
          });
          showToast("保存成功", "success");
          await load();
        } catch (err) {
          showToast(err.message || "保存失败", "error");
        }
        return;
      }
      if (activateBtn) {
        const provider = activateBtn.getAttribute("data-provider");
        if (!provider) return;
        try {
          await authFetch(`/api/admin/llm-providers/${provider}/activate`, { method: "POST", body: "{}" });
          showToast("切换成功", "success");
          await load();
        } catch (err) {
          showToast(err.message || "切换失败", "error");
        }
      }
    });

    refreshBtn.addEventListener("click", async () => {
      try {
        await load();
        showToast("已刷新", "success");
      } catch (err) {
        showToast(err.message || "刷新失败", "error");
      }
    });

    await load();
  },
};
