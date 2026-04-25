window.AdminPortalPages["profile"] = {
  render: async function (root) {
    root.innerHTML = `
      <div class="zy-card">
        <div class="zy-card-body">
          <div class="zy-page-heading">
            <h2 class="zy-page-heading-title">个人资料</h2>
            <p class="zy-page-heading-desc">查看和修改个人信息</p>
          </div>
          <form id="profile_form" class="zy-form-stack">
            <div class="zy-form-group">
              <label class="zy-form-label">用户名</label>
              <input type="text" name="username" class="zy-form-input" disabled id="profile_username" />
            </div>
            <div class="zy-form-group">
              <label class="zy-form-label">姓名</label>
              <input type="text" name="first_name" class="zy-form-input" id="profile_first_name" autocomplete="name" />
            </div>
            <div class="zy-form-group">
              <label class="zy-form-label">邮箱</label>
              <input type="email" name="email" class="zy-form-input" id="profile_email" autocomplete="email" />
            </div>
            <div class="zy-form-group">
              <button type="submit" class="zy-btn zy-btn-primary">保存修改</button>
            </div>
          </form>
          <div id="profile_result" class="mt-4" role="status"></div>
        </div>
      </div>
    `;

    async function loadProfile() {
      try {
        const data = await authFetch("/api/admin/profile", { method: "GET" });
        root.querySelector("#profile_username").value = data.username || "";
        root.querySelector("#profile_first_name").value = data.first_name || "";
        root.querySelector("#profile_email").value = data.email || "";
      } catch (e) {
        console.error("加载个人资料失败", e);
        root.querySelector("#profile_result").innerHTML = `<div class="zy-alert zy-alert-error">加载失败，请刷新重试</div>`;
      }
    }

    root.querySelector("#profile_form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const form = e.target;
      const formData = new FormData(form);
      const resultEl = root.querySelector("#profile_result");

      try {
        await authFetch("/api/admin/profile", {
          method: "PATCH",
          body: JSON.stringify({
            first_name: formData.get("first_name"),
            email: formData.get("email"),
          }),
        });
        resultEl.innerHTML = `<div class="zy-alert zy-alert-success">保存成功</div>`;
        if (typeof loadCurrentUser === "function") {
          await loadCurrentUser();
        }
      } catch (err) {
        resultEl.innerHTML = `<div class="zy-alert zy-alert-error">${adminEscapeHtml(err.message || "保存失败")}</div>`;
      }
    });

    await loadProfile();
  },
};
