document.addEventListener("DOMContentLoaded", () => {
  // Navigation Tabs
  const navItems = document.querySelectorAll(".nav-item");
  const tabPanes = document.querySelectorAll(".tab-pane");

  navItems.forEach(item => {
    item.addEventListener("click", () => {
      const targetTab = item.getAttribute("data-tab");
      navItems.forEach(n => n.classList.remove("active"));
      tabPanes.forEach(p => p.classList.remove("active"));

      item.classList.add("active");
      const targetPane = document.getElementById(`tab-${targetTab}`);
      if (targetPane) targetPane.classList.add("active");

      // Load specific data on tab open
      if (targetTab === "products") loadProducts();
      if (targetTab === "history") loadPosts();
      if (targetTab === "logs") loadLogs();
      if (targetTab === "preview") loadPreview();
    });
  });

  // Toast helper
  function showToast(message) {
    const toast = document.getElementById("toast-msg");
    toast.textContent = message;
    toast.style.display = "block";
    setTimeout(() => {
      toast.style.display = "none";
    }, 3500);
  }

  // Load System Status & Metrics
  async function loadStatus() {
    try {
      const res = await fetch("/api/status");
      const data = await res.json();

      // Dot & Indicator
      const dot = document.getElementById("system-status-dot");
      const statusText = document.getElementById("system-status-text");
      const toggleBtn = document.getElementById("btn-toggle-scheduler");

      if (data.is_running) {
        dot.className = "status-dot";
        statusText.textContent = "오토파일럿 가동 중 (24/7 무인 자동화)";
        toggleBtn.innerHTML = '<i class="ri-pause-line"></i> 일시정지';
      } else {
        dot.className = "status-dot paused";
        statusText.textContent = "오토파일럿 일시 중지됨";
        toggleBtn.innerHTML = '<i class="ri-play-line"></i> 재개하기';
      }

      // Stats
      if (data.stats) {
        document.getElementById("stat-total-products").textContent = (data.stats.total_products || 0).toLocaleString();
        document.getElementById("stat-pending-products").textContent = (data.stats.pending_products || 0).toLocaleString();
        document.getElementById("stat-published-posts").textContent = (data.stats.published_posts || 0).toLocaleString();
        document.getElementById("stat-today-posts").textContent = (data.stats.today_posts || 0).toLocaleString();
      }

      // Golden hours
      if (data.golden_hours) {
        document.getElementById("sidebar-golden-hours").textContent = data.golden_hours.join(" / ");
      }

      // Populate Settings form
      if (data.config) {
        const c = data.config;
        if (c.coupang) {
          document.getElementById("cfg-coupang-access-key").value = c.coupang.access_key || "";
          document.getElementById("cfg-coupang-secret-key").value = c.coupang.secret_key || "";
          document.getElementById("cfg-default-affiliate-link").value = c.coupang.default_affiliate_link || "";
        }
        if (c.llm) {
          document.getElementById("cfg-llm-provider").value = c.llm.provider || "gemini";
          document.getElementById("cfg-gemini-api-key").value = c.llm.gemini_api_key || c.llm.openai_api_key || "";
        }
        if (c.threads) {
          document.getElementById("cfg-threads-user-id").value = c.threads.user_id || "";
          document.getElementById("cfg-threads-token").value = c.threads.access_token || "";
          document.getElementById("cfg-threads-simulation").value = String(c.threads.simulation_mode ?? true);
        }
        if (c.strategy) {
          document.getElementById("cfg-reply-interval").value = c.strategy.reply_interval_seconds || 20;
          document.getElementById("cfg-golden-hours").value = (c.strategy.golden_hours || []).join(", ");
          document.getElementById("cfg-jitter-minutes").value = c.strategy.jitter_minutes || 15;
          document.getElementById("cfg-info-ratio").value = c.strategy.info_post_ratio || 3;
        }
        if (c.notifications) {
          document.getElementById("cfg-discord-webhook").value = c.notifications.discord_webhook || "";
        }
      }
    } catch (e) {
      console.error("Failed to load status:", e);
    }
  }

  // Load Recent Posts for Overview
  async function loadOverviewRecent() {
    try {
      const res = await fetch("/api/posts");
      const posts = await res.json();
      const container = document.getElementById("overview-recent-posts");

      if (!posts || posts.length === 0) {
        container.innerHTML = `<p style="color: var(--text-muted); font-size: 13px;">아직 발행된 포스트가 없습니다.</p>`;
        return;
      }

      container.innerHTML = posts.slice(0, 4).map(p => `
        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); border-radius: 10px; padding: 12px; font-size: 13px;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
            <span class="status-badge ${p.post_type === 'affiliate' ? 'posted' : 'simulated'}">
              ${p.post_type === 'affiliate' ? '💰 수익화 링크글' : '💡 공감 꿀팁글'}
            </span>
            <span style="color: var(--text-muted); font-size: 11px;">${p.published_at || ''}</span>
          </div>
          <div style="color: #E2E8F0; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            ${(p.product_title || p.main_text).substring(0, 40)}...
          </div>
        </div>
      `).join("");
    } catch (e) {
      console.error(e);
    }
  }

  // Load Preview Tab
  async function loadPreview() {
    try {
      const res = await fetch("/api/posts");
      const posts = await res.json();
      if (!posts || posts.length === 0) return;

      const latest = posts[0];
      document.getElementById("preview-main-text").textContent = latest.main_text || "";
      document.getElementById("preview-comment-1").textContent = latest.comment_1 || "없음";
      document.getElementById("preview-comment-2").textContent = latest.comment_2 || "없음";
      document.getElementById("preview-comment-3").textContent = latest.comment_3 || "없음";

      // Cards
      const cardsBox = document.getElementById("preview-cards");
      cardsBox.innerHTML = "";
      if (latest.image_paths) {
        try {
          const paths = JSON.parse(latest.image_paths);
          paths.forEach(p => {
            const filename = p.split(/[\\/]/).pop();
            const img = document.createElement("img");
            img.src = `/images/${filename}`;
            img.alt = "카드뉴스";
            cardsBox.appendChild(img);
          });
        } catch (e) {
          console.error(e);
        }
      }

      // Product Details
      const detailBox = document.getElementById("preview-product-detail");
      if (latest.product_title) {
        detailBox.innerHTML = `
          <div style="display: flex; gap: 14px; margin-bottom: 14px;">
            <div style="flex: 1;">
              <h4 style="font-size: 15px; margin-bottom: 6px;">${latest.product_title}</h4>
              <p style="color: var(--accent-cyan); font-weight: 700; font-size: 16px;">${Number(latest.price || 0).toLocaleString()}원</p>
              <p style="color: var(--text-muted); font-size: 12px; margin-top: 4px;">카테고리: ${latest.category || '생활용품'}</p>
            </div>
          </div>
          <div style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px; border: 1px solid var(--border-color);">
            <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 4px;">연동된 쿠팡 파트너스 딥링크:</div>
            <a href="${latest.comment_1}" target="_blank" style="color: #38BDF8; word-break: break-all; font-size: 12.5px;">클릭하여 링크 테스트 ➔</a>
          </div>
        `;
      } else {
        detailBox.innerHTML = `<p style="color: var(--text-muted);">이 포스트는 1:3 알고리즘 보호용 [순수 공감/정보성 글]입니다. 링크가 배제되었습니다.</p>`;
      }
    } catch (e) {
      console.error(e);
    }
  }

  // Load Products Table
  async function loadProducts() {
    try {
      const res = await fetch("/api/products");
      const products = await res.json();
      const tbody = document.getElementById("products-table-body");

      if (!products || products.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted);">적재된 상품이 없습니다. '1회 즉시 실행'을 누르면 자동으로 수집됩니다.</td></tr>`;
        return;
      }

      tbody.innerHTML = products.map(p => `
        <tr>
          <td><span style="background: rgba(99,102,241,0.2); color: #818CF8; padding: 2px 8px; border-radius: 4px; font-weight: 600;">${p.category}</span></td>
          <td style="max-width: 260px; font-weight: 500;">${p.title}</td>
          <td style="color: #38BDF8; font-weight: 600;">${p.price.toLocaleString()}원</td>
          <td>★ ${p.rating} (${p.review_count.toLocaleString()})</td>
          <td>${p.is_rocket ? '<span style="color: #4ADE80; font-weight: 600;">✓ 로켓배송</span>' : '일반'}</td>
          <td style="font-size: 11px; color: var(--text-muted); max-width: 140px; overflow: hidden; text-overflow: ellipsis;">${p.deeplink || '자동생성 대기'}</td>
          <td><span class="status-badge ${p.status}">${p.status === 'posted' ? '발행완료' : '대기중'}</span></td>
        </tr>
      `).join("");
    } catch (e) {
      console.error(e);
    }
  }

  // Load Posts Table
  async function loadPosts() {
    try {
      const res = await fetch("/api/posts");
      const posts = await res.json();
      const tbody = document.getElementById("posts-table-body");

      if (!posts || posts.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">발행 이력이 없습니다.</td></tr>`;
        return;
      }

      tbody.innerHTML = posts.map(p => `
        <tr>
          <td>#${p.id}</td>
          <td><span class="status-badge ${p.post_type === 'affiliate' ? 'posted' : 'simulated'}">${p.post_type === 'affiliate' ? '수익화글' : '공감/꿀팁글'}</span></td>
          <td>${p.platform}</td>
          <td style="max-width: 320px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${p.main_text}</td>
          <td style="font-size: 12px; color: var(--text-muted);">${p.published_at || '-'}</td>
          <td><span class="status-badge posted">${p.status}</span></td>
        </tr>
      `).join("");
    } catch (e) {
      console.error(e);
    }
  }

  // Load Logs
  async function loadLogs() {
    try {
      const res = await fetch("/api/logs");
      const logs = await res.json();
      const container = document.getElementById("logs-container");

      if (!logs || logs.length === 0) {
        container.innerHTML = `<div class="log-line INFO">[시스템 대기 중...]</div>`;
        return;
      }

      container.innerHTML = logs.map(l => `
        <div class="log-line ${l.level}">
          [${l.timestamp}] [${l.level}] <span class="mod">[${l.module}]</span> ${l.message}
        </div>
      `).join("");
    } catch (e) {
      console.error(e);
    }
  }

  // Action: Trigger 1-Click Affiliate
  const triggerAffiliateBtn = document.getElementById("btn-trigger-affiliate");
  triggerAffiliateBtn.addEventListener("click", async () => {
    triggerAffiliateBtn.disabled = true;
    triggerAffiliateBtn.innerHTML = '<i class="ri-loader-4-line ri-spin"></i> 자동 발행 생성 중...';

    try {
      const res = await fetch("/api/trigger", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ force_affiliate: true })
      });
      const data = await res.json();
      if (data.success) {
        showToast("🚀 수익화 포스트가 성공적으로 생성 및 발행되었습니다!");
        loadStatus();
        loadOverviewRecent();
        loadPreview();
      } else {
        showToast("오류 발생: " + data.error);
      }
    } catch (e) {
      showToast("요청 실패: " + e.message);
    } finally {
      triggerAffiliateBtn.disabled = false;
      triggerAffiliateBtn.innerHTML = '<i class="ri-flashlight-line"></i> 1회 즉시 포스팅 실행';
    }
  });

  // Action: Trigger 1-Click Info Post
  const triggerInfoBtn = document.getElementById("btn-trigger-info");
  if (triggerInfoBtn) {
    triggerInfoBtn.addEventListener("click", async () => {
      triggerInfoBtn.disabled = true;
      triggerInfoBtn.innerHTML = '<i class="ri-loader-4-line ri-spin"></i> 생성 중...';
      try {
        const res = await fetch("/api/trigger", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ force_affiliate: false })
        });
        const data = await res.json();
        if (data.success) {
          showToast("💡 공감/꿀팁글이 성공적으로 발행되었습니다!");
          loadStatus();
          loadOverviewRecent();
          loadPreview();
        }
      } catch (e) {
        showToast("요청 실패: " + e.message);
      } finally {
        triggerInfoBtn.disabled = false;
        triggerInfoBtn.innerHTML = '<i class="ri-heart-line"></i> 공감/꿀팁글 1회 생성';
      }
    });
  }

  // Action: Toggle Scheduler
  const toggleBtn = document.getElementById("btn-toggle-scheduler");
  toggleBtn.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/scheduler/toggle", { method: "POST" });
      const data = await res.json();
      showToast(data.is_running ? "오토파일럿이 가동되었습니다." : "오토파일럿이 일시 정지되었습니다.");
      loadStatus();
    } catch (e) {
      showToast("오류: " + e.message);
    }
  });

  // Action: Save Settings
  document.getElementById("btn-save-settings").addEventListener("click", async (e) => {
    e.preventDefault();
    const goldenRaw = document.getElementById("cfg-golden-hours").value;
    const goldenList = goldenRaw.split(",").map(s => s.trim()).filter(Boolean);

    const updatedConfig = {
      coupang: {
        access_key: document.getElementById("cfg-coupang-access-key").value.trim(),
        secret_key: document.getElementById("cfg-coupang-secret-key").value.trim(),
        sub_id: "thread_auto",
        default_affiliate_link: document.getElementById("cfg-default-affiliate-link").value.trim(),
        use_crawler_fallback: true
      },
      llm: {
        provider: document.getElementById("cfg-llm-provider").value,
        gemini_api_key: document.getElementById("cfg-gemini-api-key").value.trim(),
        openai_api_key: document.getElementById("cfg-gemini-api-key").value.trim(),
        model_name: "gemini-2.5-flash",
        temperature: 0.7
      },
      threads: {
        enabled: true,
        user_id: document.getElementById("cfg-threads-user-id").value.trim(),
        access_token: document.getElementById("cfg-threads-token").value.trim(),
        simulation_mode: document.getElementById("cfg-threads-simulation").value === "true"
      },
      strategy: {
        golden_hours: goldenList,
        jitter_minutes: parseInt(document.getElementById("cfg-jitter-minutes").value) || 15,
        affiliate_ratio: 1,
        info_post_ratio: parseInt(document.getElementById("cfg-info-ratio").value) || 3,
        auto_pilot_enabled: true,
        reply_interval_seconds: parseInt(document.getElementById("cfg-reply-interval").value) || 20
      },
      notifications: {
        discord_webhook: document.getElementById("cfg-discord-webhook").value.trim()
      }
    };

    try {
      const res = await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ config: updatedConfig })
      });
      const data = await res.json();
      if (data.success) {
        showToast("✅ 설정이 성공적으로 저장 및 적용되었습니다!");
        loadStatus();
      }
    } catch (e) {
      showToast("설정 저장 실패: " + e.message);
    }
  });

  // Refresh logs button
  document.getElementById("btn-refresh-logs").addEventListener("click", loadLogs);

  // Initial loads
  loadStatus();
  loadOverviewRecent();
  loadPreview();

  // Auto refresh overview & status every 15s
  setInterval(() => {
    loadStatus();
    loadOverviewRecent();
  }, 15000);
});
