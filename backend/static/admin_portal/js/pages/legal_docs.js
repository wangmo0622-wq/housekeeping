async function renderLegalDocEditor(root, fixedDocType = "") {
    let aiEditorInstance = null;
    function ensureEditorOverrides() {
      if (document.getElementById("legal-docs-aieditor-overrides")) return;
      const style = document.createElement("style");
      style.id = "legal-docs-aieditor-overrides";
      style.textContent = `
        #doc_editor aie-footer,
        #doc_editor .aie-container-footer {
          display: none !important;
        }
        #doc_editor .aie-container-main {
          border-bottom: none !important;
          box-shadow: none !important;
        }
        #doc_editor .aie-container {
          border: 1px solid #e2e8f0 !important;
          border-radius: 8px !important;
          overflow: hidden !important;
          min-height: 420px;
        }
      `;
      document.head.appendChild(style);
    }
    const getEditorHtml = () => {
      if (!aiEditorInstance) return contentEl.value || "";
      if (typeof aiEditorInstance.getHtml === "function") {
        return aiEditorInstance.getHtml();
      }
      if (typeof aiEditorInstance.getContent === "function") {
        return aiEditorInstance.getContent();
      }
      return contentEl.value || "";
    };
    const setEditorHtml = (html) => {
      const val = html || "";
      if (aiEditorInstance && typeof aiEditorInstance.setHtml === "function") {
        aiEditorInstance.setHtml(val);
      } else if (aiEditorInstance && typeof aiEditorInstance.setContent === "function") {
        aiEditorInstance.setContent(val);
      }
      contentEl.value = val;
    };

    root.innerHTML = `
      <div class="zy-card">
        <div class="zy-card-body">
          ${fixedDocType ? "" : `
          <div class="zy-form-group">
            <label class="zy-form-label">文档类型</label>
            <select id="doc_type" class="zy-select">
              <option value="terms">服务协议</option>
              <option value="privacy">隐私政策</option>
            </select>
          </div>
          `}
          <div class="zy-form-group">
            <label class="zy-form-label">标题</label>
            <input id="doc_title" class="zy-form-input" placeholder="请输入标题" />
          </div>
          <div class="zy-form-group">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;">
              <label class="zy-form-label" style="margin:0;">内容编辑器（支持 HTML）</label>
            </div>
            <div id="doc_editor" style="min-height:420px;"></div>
            <textarea id="doc_content" class="zy-form-input" style="display:none;min-height:420px;" placeholder="请输入协议内容（可粘贴 HTML）"></textarea>
            <div style="font-size:12px;color:#64748b;margin-top:8px;">提示：AI 功能通过服务端调用硅基流，密钥不会暴露到浏览器。</div>
          </div>
          <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;">
            <div id="doc_updated_at" style="font-size:12px;color:#64748b;">-</div>
            <button id="doc_save_btn" class="zy-btn zy-btn-primary zy-btn-sm">保存</button>
          </div>
        </div>
      </div>
    `;

    const docTypeEl = root.querySelector("#doc_type");
    const titleEl = root.querySelector("#doc_title");
    const contentEl = root.querySelector("#doc_content");
    const editorEl = root.querySelector("#doc_editor");
    const updatedEl = root.querySelector("#doc_updated_at");
    const saveBtn = root.querySelector("#doc_save_btn");

    if (fixedDocType && docTypeEl) {
      docTypeEl.value = fixedDocType;
    }
    const getDocType = () => fixedDocType || (docTypeEl ? docTypeEl.value : "");

    async function runEditorAi(prompt, useSelected, editor) {
      const selected = editor && typeof editor.getSelectedText === "function" ? String(editor.getSelectedText() || "") : "";
      const fallback = editor && typeof editor.getText === "function" ? String(editor.getText() || "") : "";
      const source = useSelected ? (selected || fallback) : fallback;
      if (!source.trim()) {
        showToast("请先输入内容再执行 AI", "warning");
        return false;
      }
      const data = await authFetch("/api/admin/ai/rewrite", {
        method: "POST",
        body: JSON.stringify({
          prompt,
          content: source,
        }),
      });
      const text = String(data.text || "").trim();
      if (!text) {
        showToast("AI 未返回内容", "warning");
        return false;
      }
      if (editor && typeof editor.insert === "function") {
        if (typeof editor.focusEnd === "function") editor.focusEnd();
        const chunkSize = 3;
        const delay = 22;
        for (let i = 0; i < text.length; i += chunkSize) {
          const part = text.slice(i, i + chunkSize);
          editor.insert(part);
          await new Promise((resolve) => setTimeout(resolve, delay));
        }
      } else if (editor && typeof editor.insertMarkdown === "function") {
        if (typeof editor.focusEnd === "function") editor.focusEnd();
        editor.insertMarkdown(text);
      } else {
        setEditorHtml(getEditorHtml() + "\n" + text);
      }
      showToast("AI 处理完成", "success");
      return true;
    }

    function ensureAiEditor() {
      const ctor =
        (window.AiEditor && window.AiEditor.AiEditor) ||
        window.AiEditor ||
        (window.AIEditor && window.AIEditor.AiEditor) ||
        window.AIEditor;
      if (!ctor || !editorEl) {
        editorEl.style.display = "none";
        contentEl.style.display = "block";
        return;
      }
      if (aiEditorInstance) return;
      const aiConfig = {
        image: {
          allowBase64: false,
          uploadUrl: "/api/admin/uploads/image",
          uploadFormName: "image",
          uploadHeaders: () => {
            const token = typeof getAdminToken === "function" ? getAdminToken() : "";
            return token ? { Authorization: `Bearer ${token}` } : {};
          },
        },
        video: {
          uploadUrl: "/api/admin/uploads/video",
          uploadFormName: "video",
          uploadHeaders: () => {
            const token = typeof getAdminToken === "function" ? getAdminToken() : "";
            return token ? { Authorization: `Bearer ${token}` } : {};
          },
        },
        attachment: {
          uploadUrl: "/api/admin/uploads/attachment",
          uploadFormName: "attachment",
          uploadHeaders: () => {
            const token = typeof getAdminToken === "function" ? getAdminToken() : "";
            return token ? { Authorization: `Bearer ${token}` } : {};
          },
        },
        ai: {
          menus: [
            {
              icon: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="currentColor" d="M4 19h16v2H4zm2.2-8h11.6L12 4.9z"/></svg>`,
              name: "AI续写",
              onClick: async (_event, editor) => {
                try {
                  showToast("AI 正在处理...", "info", 1200);
                  await runEditorAi("请基于当前内容继续撰写，保持条款语气与风格一致。", false, editor);
                } catch (e) {
                  showToast((e && e.message) || "AI 调用失败", "error");
                }
              },
            },
            {
              icon: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="currentColor" d="M3 5h18v2H3zm0 6h12v2H3zm0 6h18v2H3z"/></svg>`,
              name: "AI优化",
              onClick: async (_event, editor) => {
                try {
                  showToast("AI 正在处理...", "info", 1200);
                  await runEditorAi("请优化这段内容的表达，使其更专业、清晰、适合法律/平台协议文本。", true, editor);
                } catch (e) {
                  showToast((e && e.message) || "AI 调用失败", "error");
                }
              },
            },
            {
              icon: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="currentColor" d="M4 4h16v2H4zm0 6h16v2H4zm0 6h10v2H4z"/></svg>`,
              name: "AI校对",
              onClick: async (_event, editor) => {
                try {
                  showToast("AI 正在处理...", "info", 1200);
                  await runEditorAi("请校对这段文本，修正错别字、语病和标点，并保持原意不变。", true, editor);
                } catch (e) {
                  showToast((e && e.message) || "AI 调用失败", "error");
                }
              },
            },
            {
              icon: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="currentColor" d="M12 2 4 5v6c0 5.55 3.84 10.74 8 11 4.16-.26 8-5.45 8-11V5z"/></svg>`,
              name: "AI摘要",
              onClick: async (_event, editor) => {
                try {
                  showToast("AI 正在处理...", "info", 1200);
                  await runEditorAi("请提炼这段内容的核心要点，输出简明摘要。", true, editor);
                } catch (e) {
                  showToast((e && e.message) || "AI 调用失败", "error");
                }
              },
            },
          ],
        },
      };
      const initCandidates = [
        { ...aiConfig, element: editorEl, content: contentEl.value || "" },
        { ...aiConfig, element: "#doc_editor", content: contentEl.value || "" },
        { ...aiConfig, element: editorEl, html: contentEl.value || "" },
        { ...aiConfig, element: "#doc_editor", html: contentEl.value || "" },
      ];
      try {
        let lastErr = null;
        for (const opts of initCandidates) {
          try {
            aiEditorInstance = new ctor(opts);
            if (aiEditorInstance) break;
          } catch (innerErr) {
            lastErr = innerErr;
          }
        }
        if (!aiEditorInstance && lastErr) throw lastErr;
        editorEl.style.display = "block";
        contentEl.style.display = "none";
      } catch (e) {
        console.warn("AIEditor init failed, fallback to textarea:", e);
        editorEl.style.display = "none";
        contentEl.style.display = "block";
      }
    }

    async function loadDoc() {
      const docType = getDocType();
      const data = await authFetch(`/api/admin/site-documents/${docType}`, { method: "GET" });
      titleEl.value = data.title || "";
      setEditorHtml(data.content || "");
      updatedEl.textContent = data.updated_at ? `最近更新：${data.updated_at}` : "最近更新：-";
    }

    async function saveDoc() {
      const docType = getDocType();
      const payload = {
        title: (titleEl.value || "").trim(),
        content: getEditorHtml(),
      };
      await authFetch(`/api/admin/site-documents/${docType}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      showToast("保存成功", "success");
      await loadDoc();
    }

    if (!fixedDocType && docTypeEl) {
      docTypeEl.addEventListener("change", async () => {
        try {
          await loadDoc();
        } catch (e) {
          showToast(e.message || "加载失败", "error");
        }
      });
    }

    saveBtn.addEventListener("click", async () => {
      try {
        await saveDoc();
      } catch (e) {
        showToast(e.message || "保存失败", "error");
      }
    });

    ensureEditorOverrides();
    ensureAiEditor();
    await loadDoc();
}

window.AdminPortalPages["legal_docs"] = {
  render: async function (root) {
    await renderLegalDocEditor(root, "");
  },
};

window.AdminPortalPages["legal_terms"] = {
  render: async function (root) {
    await renderLegalDocEditor(root, "terms");
  },
};

window.AdminPortalPages["legal_privacy"] = {
  render: async function (root) {
    await renderLegalDocEditor(root, "privacy");
  },
};
