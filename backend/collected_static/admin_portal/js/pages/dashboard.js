window.AdminPortalPages = window.AdminPortalPages || {};

window.AdminPortalPages.dashboard = {
  render: async function(root) {
    root.innerHTML = `
      <div class="dashboard-container">
        <!-- 欢迎区域 -->
        <div class="welcome-section">
          <div class="welcome-content">
            <h1 class="welcome-title">欢迎回来，管理员</h1>
            <p class="welcome-subtitle">家政服务管理平台 · 实时数据监控中心</p>
          </div>
          <div class="welcome-date">
            <span id="current-date"></span>
          </div>
        </div>

        <!-- 统计卡片区域 -->
        <div class="stats-grid">
          <div class="stat-card stat-card-pending">
            <div class="stat-icon-wrapper stat-icon-orange">
              <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
            </div>
            <div class="stat-content">
              <div class="stat-label">待审核技师</div>
              <div id="d-p-tech" class="stat-value">--</div>
              <div class="stat-trend">
                <span class="trend-badge">需处理</span>
              </div>
            </div>
          </div>

          <div class="stat-card stat-card-pending">
            <div class="stat-icon-wrapper stat-icon-blue">
              <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
              </svg>
            </div>
            <div class="stat-content">
              <div class="stat-label">待审核机构</div>
              <div id="d-p-org" class="stat-value">--</div>
              <div class="stat-trend">
                <span class="trend-badge">需处理</span>
              </div>
            </div>
          </div>

          <div class="stat-card stat-card-pending">
            <div class="stat-icon-wrapper stat-icon-purple">
              <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/>
              </svg>
            </div>
            <div class="stat-content">
              <div class="stat-label">待审核服务</div>
              <div id="d-p-service" class="stat-value">--</div>
              <div class="stat-trend">
                <span class="trend-badge">需处理</span>
              </div>
            </div>
          </div>

          <div class="stat-card stat-card-total">
            <div class="stat-icon-wrapper stat-icon-green">
              <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
              </svg>
            </div>
            <div class="stat-content">
              <div class="stat-label">认证技师总数</div>
              <div id="d-s-verified-tech" class="stat-value">--</div>
              <div class="stat-trend">
                <span class="trend-text">平台认证技师</span>
              </div>
            </div>
          </div>

          <div class="stat-card stat-card-total">
            <div class="stat-icon-wrapper stat-icon-cyan">
              <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/>
              </svg>
            </div>
            <div class="stat-content">
              <div class="stat-label">注册用户总数</div>
              <div id="d-s-users" class="stat-value">--</div>
              <div class="stat-trend">
                <span class="trend-text">注册用户</span>
              </div>
            </div>
          </div>

          <div class="stat-card stat-card-total">
            <div class="stat-icon-wrapper stat-icon-pink">
              <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
              </svg>
            </div>
            <div class="stat-content">
              <div class="stat-label">服务总数</div>
              <div id="d-s-services" class="stat-value">--</div>
              <div class="stat-trend">
                <span class="trend-text">已发布服务</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 主要内容区域 -->
        <div class="dashboard-main-grid">
          <!-- 快捷处理 -->
          <div class="dashboard-panel">
            <div class="panel-header">
              <div class="panel-icon panel-icon-orange">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                </svg>
              </div>
              <h3 class="panel-title">快捷处理</h3>
            </div>
            <div class="panel-body">
              <div id="d-quick-actions" class="quick-actions-list">
                <div class="loading-state">
                  <div class="loading-spinner"></div>
                  <span>加载中...</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 数据趋势 -->
          <div class="dashboard-panel panel-large">
            <div class="panel-header">
              <div class="panel-icon panel-icon-blue">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"/>
                </svg>
              </div>
              <h3 class="panel-title">运营趋势（近12个月）</h3>
            </div>
            <div class="panel-body">
              <div class="chart-container">
                <canvas id="d-trend-chart"></canvas>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    // 设置当前日期
    const dateEl = root.querySelector('#current-date');
    if (dateEl) {
      const now = new Date();
      const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' };
      dateEl.textContent = now.toLocaleDateString('zh-CN', options);
    }

    // 加载数据
    try {
      const data = await authFetch("/api/admin/dashboard", { method: "GET" });
      const pending = data.pending || {};
      const statistics = data.statistics || {};
      const trends = data.trends || {};
      const quick = data.quick_actions || [];

      // 更新统计数据
      this.updateStatValue(root, "#d-p-tech", pending.pending_technician_verify || 0);
      this.updateStatValue(root, "#d-p-org", pending.pending_organization_verify || 0);
      this.updateStatValue(root, "#d-p-service", pending.pending_service_audit || 0);
      this.updateStatValue(root, "#d-s-verified-tech", statistics.verified_technicians || 0);
      this.updateStatValue(root, "#d-s-users", statistics.total_users || 0);
      this.updateStatValue(root, "#d-s-services", statistics.total_services || 0);

      // 渲染快捷操作
      const quickRoot = root.querySelector("#d-quick-actions");
      if (quick.length === 0) {
        quickRoot.innerHTML = `
          <div class="empty-state">
            <div class="empty-icon">✓</div>
            <div class="empty-text">暂无待处理事项</div>
            <div class="empty-subtext">所有任务已处理完毕</div>
          </div>
        `;
      } else {
        quickRoot.innerHTML = quick.map((x) => `
          <div class="quick-action-item">
            <div class="quick-action-info">
              <div class="quick-action-title">${x.title}</div>
              <div class="quick-action-meta">
                <span class="quick-count">${x.count || 0} 条待处理</span>
              </div>
            </div>
            <a href="${x.url || '#'}" class="quick-action-btn">
              去处理
              <svg class="btn-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/>
              </svg>
            </a>
          </div>
        `).join("");
      }

      // 渲染图表
      const trendCanvas = root.querySelector("#d-trend-chart");
      if (trendCanvas && window.Chart) {
        new Chart(trendCanvas, {
          type: "line",
          data: {
            labels: trends.months || [],
            datasets: [
              { 
                label: "注册用户", 
                data: trends.user_counts || [], 
                borderColor: "#3b82f6", 
                backgroundColor: "rgba(59,130,246,.15)", 
                tension: 0.4, 
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6
              },
              { 
                label: "技师新增", 
                data: trends.technician_counts || [], 
                borderColor: "#10b981", 
                backgroundColor: "rgba(16,185,129,.15)", 
                tension: 0.4, 
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6
              },
              { 
                label: "服务发布", 
                data: trends.service_counts || [], 
                borderColor: "#f59e0b", 
                backgroundColor: "rgba(245,158,11,.15)", 
                tension: 0.4, 
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
              mode: 'index',
              intersect: false,
            },
            plugins: { 
              legend: { 
                position: "bottom",
                labels: {
                  usePointStyle: true,
                  padding: 20,
                  font: { size: 12 }
                }
              } 
            },
            scales: {
              x: {
                grid: { display: false }
              },
              y: {
                beginAtZero: true,
                grid: { color: 'rgba(0,0,0,0.05)' }
              }
            }
          },
        });
      }
    } catch (err) {
      root.querySelector("#d-quick-actions").innerHTML = `
        <div class="error-state">
          <div class="error-icon">⚠</div>
          <div class="error-text">加载失败</div>
          <div class="error-subtext">${err.message || "请刷新页面重试"}</div>
        </div>
      `;
    }
  },

  updateStatValue: function(root, selector, value) {
    const el = root.querySelector(selector);
    if (el) {
      // 数字动画效果
      const target = parseInt(value) || 0;
      const duration = 800;
      const start = 0;
      const startTime = performance.now();
      
      const animate = (currentTime) => {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easeProgress = 1 - Math.pow(1 - progress, 3); // easeOutCubic
        const current = Math.floor(start + (target - start) * easeProgress);
        el.textContent = current.toLocaleString();
        
        if (progress < 1) {
          requestAnimationFrame(animate);
        }
      };
      
      requestAnimationFrame(animate);
    }
  }
};
