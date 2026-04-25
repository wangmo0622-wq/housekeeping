## 机构门户控制台样式（`organization_portal.css`）

`accounts/templates/organization_portal/console.html` 与 **`home.html`（`/org/` 首页）** 共用 **本地编译** 的样式，不依赖 `cdn.tailwindcss.com`。

- **源文件**：`organization_portal.input.css`（`@import "tailwindcss"` + `@source` 扫描机构门户模板）
- **产物**：`organization_portal.css`（已提交仓库，Docker 构建与 `collectstatic` 可直接使用）
- **修改样式后重新生成**（需在 `static/css` 目录已执行过 `npm install`）：

```bash
cd backend/static/css
npm run build:org-portal
```

依赖见本目录 `package.json`（`tailwindcss` + `@tailwindcss/cli` v4）。

---

## Tailwind + daisyUI 本地编译（无 Node.js）

本目录用于把 Tailwind（standalone 可执行文件）与 daisyUI（`daisyui.mjs` 插件）离线编译成 `output.css`，从而让模板通过 `{% static 'css/output.css' %}` 引用。

> 说明：由于此环境下对 GitHub 下载可能会超时，请在你本机环境执行以下命令。

### 1. 下载依赖文件

macOS（arm64，对应你当前系统）：

```bash
cd backend/static/css

curl -sLo tailwindcss "https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-macos-arm64"
chmod +x tailwindcss

curl -sLO daisyui.mjs "https://github.com/saadeghi/daisyui/releases/latest/download/daisyui.mjs"
curl -sLO daisyui-theme.mjs "https://github.com/saadeghi/daisyui/releases/latest/download/daisyui-theme.mjs"
```

### 2. 生成输出文件

```bash
./tailwindcss -i input.css -o output.css
```

编译完成后，重启（或刷新）你的 Django 页面即可看到样式效果。

