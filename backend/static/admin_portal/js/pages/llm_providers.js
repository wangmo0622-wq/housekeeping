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

    const MODEL_OPTIONS = {
      alibaba: [
        { value: "qwen-plus", label: "通义千问-plus" },
        { value: "qwen-max", label: "通义千问-max" },
        { value: "qwen-long", label: "通义千问-long" },
      ],
      siliconflow: [
        // DeepSeek 系列
        { value: "deepseek-ai/DeepSeek-V3", label: "DeepSeek-V3" },
        { value: "deepseek-ai/DeepSeek-V3.1", label: "DeepSeek-V3.1" },
        { value: "deepseek-ai/DeepSeek-V3.2", label: "DeepSeek-V3.2" },
        { value: "deepseek-ai/DeepSeek-R1", label: "DeepSeek-R1" },
        { value: "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B", label: "DeepSeek-R1-Distill-Qwen-7B" },
        { value: "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B", label: "DeepSeek-R1-Distill-Qwen-14B" },
        { value: "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B", label: "DeepSeek-R1-Distill-Qwen-32B" },
        { value: "deepseek-ai/DeepSeek-R1-Distill-Llama-8B", label: "DeepSeek-R1-Distill-Llama-8B" },
        { value: "Pro/deepseek-ai/DeepSeek-V3", label: "Pro/DeepSeek-V3" },
        { value: "Pro/deepseek-ai/DeepSeek-R1", label: "Pro/DeepSeek-R1" },
        // Qwen/通义千问系列
        { value: "Qwen/Qwen-plus", label: "通义千问-plus" },
        { value: "Qwen/Qwen-max", label: "通义千问-max" },
        { value: "Qwen/Qwen2-7B-Instruct", label: "通义千问-Qwen2-7B (免费)" },
        { value: "Qwen/Qwen2-72B-Instruct", label: "通义千问-Qwen2-72B" },
        { value: "Qwen/Qwen2-57B-A14B-Instruct", label: "通义千问-Qwen2-57B-A14B" },
        { value: "Qwen/Qwen1.5-7B-Chat", label: "通义千问-Qwen1.5-7B (免费)" },
        { value: "Qwen/Qwen1.5-14B-Chat", label: "通义千问-Qwen1.5-14B" },
        { value: "Qwen/Qwen1.5-32B-Chat", label: "通义千问-Qwen1.5-32B" },
        { value: "Qwen/Qwen1.5-110B-Chat", label: "通义千问-Qwen1.5-110B" },
        { value: "Qwen/Qwen3-235B-A22B", label: "通义千问-Qwen3-235B-A22B" },
        // GLM 系列
        { value: "THUDM/glm-4-9b-chat", label: "智谱-GLM-4-9B (免费)" },
        { value: "THUDM/glm-4.6", label: "智谱-GLM-4.6" },
        { value: "THUDM/glm-4.7", label: "智谱-GLM-4.7" },
        { value: "THUDM/glm-Z1-32B-0414", label: "智谱-GLM-Z1-32B" },
        { value: "Pro/zai-org/GLM-5.1", label: "Pro/智谱-GLM-5.1" },
        // Kimi 系列
        { value: "moonshotai/Kimi-K2-Instruct", label: "Kimi-K2-Instruct" },
        { value: "moonshotai/Kimi-K2-Instruct-0905", label: "Kimi-K2-Instruct-0905" },
        { value: "moonshotai/Kimi-K2.5", label: "Kimi-K2.5" },
        { value: "moonshotai/Kimi-K2-Thinking", label: "Kimi-K2-Thinking" },
        { value: "Pro/moonshotai/Kimi-K2-Instruct", label: "Pro/Kimi-K2-Instruct" },
        // MiniMax 系列
        { value: "MiniMax/M1", label: "MiniMax-M1" },
        { value: "MiniMax/M2", label: "MiniMax-M2" },
        { value: "MiniMax/M2.5", label: "MiniMax-M2.5" },
        // 其他模型
        { value: "internlm/internlm2_5-7b-chat", label: "InternLM2.5-7B (免费)" },
        { value: "mistralai/Mistral-7B-Instruct-v0.2", label: "Mistral-7B (免费)" },
      ],
      deepseek: [
        { value: "deepseek-chat", label: "DeepSeek-Chat" },
        { value: "deepseek-v3", label: "DeepSeek-V3" },
        { value: "deepseek-v3.1", label: "DeepSeek-V3.1" },
        { value: "deepseek-r1", label: "DeepSeek-R1" },
        { value: "deepseek-r1-distill-qwen-7b", label: "DeepSeek-R1-Distill-Qwen-7B" },
        { value: "deepseek-r1-distill-qwen-14b", label: "DeepSeek-R1-Distill-Qwen-14B" },
        { value: "deepseek-r1-distill-qwen-32b", label: "DeepSeek-R1-Distill-Qwen-32B" },
        { value: "deepseek-r1-distill-llama-8b", label: "DeepSeek-R1-Distill-Llama-8B" },
      ],
    };

    function getModelSelectHtml(provider, currentModelId) {
      const options = MODEL_OPTIONS[provider] || [];
      const opts = options
        .map((o) => `<option value="${o.value}" ${o.value === currentModelId ? "selected" : ""}>${o.label}</option>`)
        .join("");
      return `<select class="zy-select" data-field="model_id" data-provider="${provider}" style="width:100%;">
        <option value="">请选择模型（可选）</option>
        ${opts}
        <option value="__custom__" ${currentModelId && !options.find(o => o.value === currentModelId) ? "selected" : ""}>自定义模型...</option>
      </select>`;
    }

    function cardHtml(item) {
      const activeTag = item.is_active
        ? `<span class="zy-badge zy-badge-success">当前生效</span>`
        : `<span class="zy-badge">未生效</span>`;
      const enabledTag = item.is_enabled
        ? `<span class="zy-badge zy-badge-info">已启用</span>`
        : `<span class="zy-badge zy-badge-warning">已停用</span>`;
      const modelSelectHtml = getModelSelectHtml(item.provider, item.model_id || item.model_name || "");
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
                <label class="zy-form-label">模型选择</label>
                ${modelSelectHtml}
              </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px;" id="model_custom_row_${item.provider}">
              <div>
                <label class="zy-form-label">自定义模型名</label>
                <input class="zy-form-input" data-field="model_name" data-provider="${item.provider}" value="${adminEscapeHtml(item.model_name || "")}" placeholder="选择自定义模型时请输入" />
              </div>
              <div></div>
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
      listEl.querySelectorAll("select[data-field=\"model_id\"]").forEach((sel) => {
        sel.addEventListener("change", function () {
          const provider = this.getAttribute("data-provider");
          const customRow = document.getElementById(`model_custom_row_${provider}`);
          if (!customRow) return;
          const modelNameInput = customRow.querySelector('[data-field="model_name"]');
          if (!modelNameInput) return;
          if (this.value === "__custom__") {
            modelNameInput.removeAttribute("readonly");
            modelNameInput.focus();
          } else if (this.value) {
            modelNameInput.value = this.value;
            modelNameInput.setAttribute("readonly", "readonly");
          } else {
            modelNameInput.value = "";
            modelNameInput.removeAttribute("readonly");
          }
        });
        const provider = sel.getAttribute("data-provider");
        const customRow = document.getElementById(`model_custom_row_${provider}`);
        if (customRow) {
          const modelNameInput = customRow.querySelector('[data-field="model_name"]');
          if (modelNameInput && sel.value && sel.value !== "__custom__") {
            modelNameInput.setAttribute("readonly", "readonly");
          }
        }
      });
    }

    listEl.addEventListener("click", async (e) => {
      const saveBtn = e.target.closest('[data-role="save"]');
      const activateBtn = e.target.closest('[data-role="activate"]');
      if (saveBtn) {
        const provider = saveBtn.getAttribute("data-provider");
        if (!provider) return;
        const baseUrlEl = listEl.querySelector(`[data-field="base_url"][data-provider="${provider}"]`);
        const modelIdEl = listEl.querySelector(`[data-field="model_id"][data-provider="${provider}"]`);
        const modelNameEl = listEl.querySelector(`[data-field="model_name"][data-provider="${provider}"]`);
        const keyEl = listEl.querySelector(`[data-field="api_key"][data-provider="${provider}"]`);
        const enabledEl = listEl.querySelector(`[data-field="is_enabled"][data-provider="${provider}"]`);
        let modelId = modelIdEl ? modelIdEl.value : "";
        if (modelId === "__custom__") {
          modelId = modelNameEl ? modelNameEl.value : "";
        }
        try {
          await authFetch(`/api/admin/llm-providers/${provider}`, {
            method: "PATCH",
            body: JSON.stringify({
              base_url: baseUrlEl ? baseUrlEl.value : "",
              model_id: modelId,
              model_name: modelNameEl ? modelNameEl.value : "",
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
