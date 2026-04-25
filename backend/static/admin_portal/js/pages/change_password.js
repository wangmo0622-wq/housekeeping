window.AdminPortalPages["change_password"] = {
  render: async function (root) {
    root.innerHTML = `
      <div class="zy-card">
        <div class="zy-card-body">
          <div class="zy-page-heading">
            <h2 class="zy-page-heading-title">修改密码</h2>
            <p class="zy-page-heading-desc">修改当前管理员登录密码</p>
          </div>
          <form id="password_form" class="zy-form-stack">
            <div class="zy-form-group">
              <label class="zy-form-label">旧密码 <span class="text-red-500">*</span></label>
              <input type="password" name="old_password" class="zy-form-input" required autocomplete="current-password" />
            </div>
            <div class="zy-form-group">
              <label class="zy-form-label">新密码 <span class="text-red-500">*</span></label>
              <input type="password" name="new_password" class="zy-form-input" required autocomplete="new-password" />
            </div>
            <div class="zy-form-group">
              <label class="zy-form-label">确认新密码 <span class="text-red-500">*</span></label>
              <input type="password" name="confirm_password" class="zy-form-input" required autocomplete="new-password" />
            </div>
            <div class="zy-form-group">
              <button type="submit" class="zy-btn zy-btn-primary">确认修改</button>
            </div>
          </form>
          <div id="password_result" class="mt-4" role="status"></div>
        </div>
      </div>
    `;

    root.querySelector("#password_form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const form = e.target;
      const formData = new FormData(form);
      const oldPassword = formData.get("old_password");
      const newPassword = formData.get("new_password");
      const confirmPassword = formData.get("confirm_password");

      const resultEl = root.querySelector("#password_result");

      if (newPassword !== confirmPassword) {
        resultEl.innerHTML = `<div class="zy-alert zy-alert-error" role="alert">两次输入的新密码不一致</div>`;
        return;
      }

      try {
        await authFetch("/api/admin/change-password", {
          method: "POST",
          body: JSON.stringify({
            old_password: oldPassword,
            new_password: newPassword,
          }),
        });
        resultEl.innerHTML = `<div class="zy-alert zy-alert-success" role="status">密码修改成功，将跳转登录…</div>`;
        form.reset();
        setTimeout(() => {
          localStorage.removeItem("admin_access_token");
          window.location.href = "/admin/login/";
        }, 2000);
      } catch (err) {
        resultEl.innerHTML = `<div class="zy-alert zy-alert-error" role="alert">${adminEscapeHtml(err.message || "修改失败")}</div>`;
      }
    });
  },
};
