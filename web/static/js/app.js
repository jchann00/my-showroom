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
      if (targetTab === "showroom") {
        const iframe = document.getElementById("showroom-iframe");
        if (iframe) iframe.src = "/showroom?t=" + Date.now();
      }
      if (targetTab === "videos") loadVideos();
    });
  });

  // Toast helper
  function showToast(message) {
    const toast = document.getElementById("toast-msg");
    if (!toast) return;
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

      const isShorts = data.config?.modules?.shorts_enabled ?? true;
      const isThreads = data.config?.modules?.threads_enabled ?? false;

      if (data.is_running) {
        if (dot) dot.className = "status-dot";
        if (isShorts && !isThreads) {
          if (statusText) statusText.innerHTML = '오토파일럿 가동 중 (<strong style="color: #38BDF8;">🎬 숏츠 전용</strong> · <span style="color: #94A3B8;">🧵 쓰레드 OFF</span>)';
        } else if (isShorts && isThreads) {
          if (statusText) statusText.innerHTML = '오토파일럿 가동 중 (<strong style="color: #38BDF8;">🎬 숏츠</strong> & <strong style="color: #818CF8;">🧵 쓰레드</strong>)';
        } else if (!isShorts && isThreads) {
          if (statusText) statusText.innerHTML = '오토파일럿 가동 중 (<strong style="color: #818CF8;">🧵 쓰레드 전용</strong>)';
        } else {
          if (statusText) statusText.textContent = "오토파일럿 대기 중 (모듈 꺼짐)";
        }
        if (toggleBtn) toggleBtn.innerHTML = '<i class="ri-pause-line"></i> 일시정지';
      } else {
        if (dot) dot.className = "status-dot paused";
        if (statusText) statusText.textContent = "오토파일럿 일시 중지됨";
        if (toggleBtn) toggleBtn.innerHTML = '<i class="ri-play-line"></i> 재개하기';
      }

      // Stats
      if (data.stats) {
        const elTotal = document.getElementById("stat-total-products");
        const elPending = document.getElementById("stat-pending-products");
        const elPub = document.getElementById("stat-published-posts");
        const elToday = document.getElementById("stat-today-posts");
        if (elTotal) elTotal.textContent = (data.stats.total_products || 0).toLocaleString();
        if (elPending) elPending.textContent = (data.stats.pending_products || 0).toLocaleString();
        if (elPub) elPub.textContent = (data.stats.published_posts || 0).toLocaleString();
        if (elToday) elToday.textContent = (data.stats.today_posts || 0).toLocaleString();
      }

      // Golden hours
      if (data.golden_hours) {
        const ghEl = document.getElementById("sidebar-golden-hours");
        if (ghEl) ghEl.textContent = data.golden_hours.join(" / ");
      }

      // Showroom URL input
      const showroomInput = document.getElementById("showroom-url-input");
      if (showroomInput) showroomInput.value = window.location.origin + "/showroom";

      // Populate Settings form
      if (data.config) {
        const c = data.config;
        if (c.modules) {
          const modShorts = document.getElementById("cfg-module-shorts");
          const modThreads = document.getElementById("cfg-module-threads");
          if (modShorts) modShorts.checked = c.modules.shorts_enabled ?? true;
          if (modThreads) modThreads.checked = c.modules.threads_enabled ?? false;
        }

        // Showroom Public URL
        const publicShowroomInput = document.getElementById("showroom-public-url-input");
        if (publicShowroomInput) publicShowroomInput.value = c.showroom?.public_url || "";

        // YouTube Settings
        const ytEnabled = document.getElementById("cfg-yt-enabled");
        const ytPrivacy = document.getElementById("cfg-yt-privacy");
        if (ytEnabled) ytEnabled.checked = c.youtube?.enabled ?? true;
        if (ytPrivacy) ytPrivacy.value = c.youtube?.privacy_status || "public";

        if (c.tts) {
          const elTtsProv = document.getElementById("cfg-tts-provider");
          const elTtsVoice = document.getElementById("cfg-tts-voice");
          const elTtsSpeed = document.getElementById("cfg-tts-speed");
          const elElvKey = document.getElementById("cfg-elevenlabs-key");
          const elElvVid = document.getElementById("cfg-elevenlabs-voice-id");
          if (elTtsProv) elTtsProv.value = c.tts.provider || "edge_tts";
          if (elTtsVoice) elTtsVoice.value = c.tts.edge_voice || "ko-KR-InJoonNeural";
          if (elTtsSpeed) elTtsSpeed.value = c.tts.speed || "+0%";
          if (elElvKey) elElvKey.value = c.tts.elevenlabs_api_key || "";
          if (elElvVid) elElvVid.value = c.tts.elevenlabs_voice_id || "";
        }

        if (c.coupang) {
          const elKey = document.getElementById("cfg-coupang-access-key");
          const elSec = document.getElementById("cfg-coupang-secret-key");
          const elDef = document.getElementById("cfg-default-affiliate-link");
          if (elKey) elKey.value = c.coupang.access_key || "";
          if (elSec) elSec.value = c.coupang.secret_key || "";
          if (elDef) elDef.value = c.coupang.default_affiliate_link || "";
        }
        if (c.llm) {
          const elProv = document.getElementById("cfg-llm-provider");
          const elLlmKey = document.getElementById("cfg-gemini-api-key");
          if (elProv) elProv.value = c.llm.provider || "gemini";
          if (elLlmKey) elLlmKey.value = c.llm.gemini_api_key || c.llm.openai_api_key || "";
        }
        if (c.threads) {
          const elUid = document.getElementById("cfg-threads-user-id");
          const elTok = document.getElementById("cfg-threads-token");
          const elSim = document.getElementById("cfg-threads-simulation");
          if (elUid) elUid.value = c.threads.user_id || "";
          if (elTok) elTok.value = c.threads.access_token || "";
          if (elSim) elSim.value = String(c.threads.simulation_mode ?? false);
        }
        if (c.strategy) {
          const elInterval = document.getElementById("cfg-reply-interval");
          const elGh = document.getElementById("cfg-golden-hours");
          const elJitter = document.getElementById("cfg-jitter-minutes");
          const elRatio = document.getElementById("cfg-info-ratio");
          if (elInterval) elInterval.value = c.strategy.reply_interval_seconds || 20;
          if (elGh) elGh.value = (c.strategy.golden_hours || []).join(", ");
          if (elJitter) elJitter.value = c.strategy.jitter_minutes || 15;
          if (elRatio) elRatio.value = c.strategy.info_post_ratio || 3;
        }
        if (c.notifications) {
          const elWebhook = document.getElementById("cfg-discord-webhook");
          if (elWebhook) elWebhook.value = c.notifications.discord_webhook || "";
        }
      }

      // Check YouTube OAuth status
      try {
        const ytRes = await fetch("/api/youtube/status");
        const ytData = await ytRes.json();
        const ytBadge = document.getElementById("yt-auth-status-badge");
        if (ytBadge) {
          if (ytData.is_authenticated) {
            ytBadge.style.background = "rgba(34, 197, 94, 0.2)";
            ytBadge.style.color = "#4ADE80";
            ytBadge.textContent = "✅ Google OAuth 연동 완료 (24/7 자동 업로드 가동)";
          } else if (ytData.secrets_file_exists) {
            ytBadge.style.background = "rgba(56, 189, 248, 0.2)";
            ytBadge.style.color = "#38BDF8";
            ytBadge.textContent = "⚡ client_secrets 준비됨 (첫 업로드 시 1회 승인 대기)";
          } else {
            ytBadge.style.background = "rgba(251, 191, 36, 0.15)";
            ytBadge.style.color = "#FBBF24";
            ytBadge.textContent = "💡 시뮬레이션 모드 (client_secrets.json 등록 시 자동 송출)";
          }
        }
      } catch (err) {
        console.error("Failed to load YouTube status:", err);
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
      if (!container) return;

      if (!posts || posts.length === 0) {
        container.innerHTML = `<p style="color: var(--text-muted); font-size: 13px;">아직 발행된 포스트/영상이 없습니다.</p>`;
        return;
      }

      container.innerHTML = posts.slice(0, 4).map(p => `
        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); border-radius: 10px; padding: 12px; font-size: 13px;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
            <span class="status-badge ${p.post_type === 'shorts' ? 'posted' : (p.post_type === 'affiliate' ? 'posted' : 'simulated')}">
              ${p.post_type === 'shorts' ? '🎬 숏츠 영상' : (p.post_type === 'affiliate' ? '💰 수익화 링크글' : '💡 공감 꿀팁글')}
            </span>
            <span style="color: var(--text-muted); font-size: 11px;">${p.published_at || ''}</span>
          </div>
          <div style="color: #E2E8F0; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            ${(p.product_title || p.main_text || '').substring(0, 40)}...
          </div>
          ${p.post_type === 'shorts' ? `
            <div style="margin-top: 8px; display: flex; gap: 8px;">
              <button class="btn btn-secondary" onclick="document.querySelector('[data-tab=videos]').click()" style="font-size: 11px; padding: 4px 8px;">
                <i class="ri-play-circle-line"></i> 영상 보러가기
              </button>
              <button class="btn btn-primary" onclick="document.querySelector('[data-tab=showroom]').click()" style="font-size: 11px; padding: 4px 8px; background: #0284C7;">
                <i class="ri-store-2-line"></i> 쇼룸 카탈로그 보기
              </button>
            </div>
          ` : ''}
        </div>
      `).join("");

      // Update Spotlight Card with latest video
      try {
        const vRes = await fetch("/api/videos");
        const videos = await vRes.json();
        if (videos && videos.length > 0) {
          const latestVideo = videos[0];
          const vidPlayer = document.getElementById("spotlight-video");
          const vidTitle = document.getElementById("spotlight-title");
          const vidMeta = document.getElementById("spotlight-meta");
          const vidYtTitle = document.getElementById("spotlight-yt-title");
          const vidYtDesc = document.getElementById("spotlight-yt-desc");
          const dlBtn = document.getElementById("spotlight-download-btn");

          if (vidPlayer && !vidPlayer.src.includes(latestVideo.filename)) {
            vidPlayer.src = latestVideo.url;
          }
          if (vidTitle) vidTitle.textContent = latestVideo.filename;
          if (vidMeta) vidMeta.textContent = `💾 ${latestVideo.size_mb} MB · 🕒 ${latestVideo.created_at || '방금 전'}`;
          if (dlBtn) {
            dlBtn.href = latestVideo.url;
            dlBtn.download = latestVideo.filename;
          }

          const latestShortPost = posts.find(p => p.post_type === 'shorts');
          if (latestShortPost) {
            if (vidTitle && latestShortPost.product_title) {
              vidTitle.textContent = latestShortPost.product_title;
            }
            if (vidYtTitle) vidYtTitle.textContent = latestShortPost.main_text || `[추천] ${latestShortPost.product_title} 솔직후기 #shorts`;
            if (vidYtDesc) vidYtDesc.textContent = latestShortPost.comment_1 || "프로필 쇼룸 링크에서 최저가 확인하세요!\n#shorts #쿠팡 #살림꿀템";
          } else {
            if (vidYtTitle) vidYtTitle.textContent = `[추천] ${latestVideo.filename.replace('_shorts.mp4', '')} 솔직후기 #shorts`;
            if (vidYtDesc) vidYtDesc.textContent = "프로필 쇼룸 링크에서 최저가 확인하세요!\n#shorts #쿠팡 #살림꿀템";
          }
        }
      } catch (err) {
        console.error("Failed to update spotlight:", err);
      }
    } catch (e) {
      console.error(e);
    }
  }

  // Load Videos Grid
  async function loadVideos() {
    const container = document.getElementById("videos-grid-container");
    if (!container) return;

    try {
      const res = await fetch("/api/videos");
      const videos = await res.json();

      if (!videos || videos.length === 0) {
        container.innerHTML = `
          <div style="grid-column: 1/-1; padding: 40px 20px; text-align: center; color: var(--text-muted); background: rgba(255,255,255,0.02); border-radius: 12px; border: 1px dashed var(--border-color);">
            <i class="ri-movie-line" style="font-size: 42px; display: block; margin-bottom: 12px; color: #F43F5E;"></i>
            <p style="font-size: 15px; font-weight: 600; color: #E2E8F0; margin-bottom: 6px;">아직 생성된 숏츠 영상이 없습니다.</p>
            <p style="font-size: 13px;">우측 상단 <strong>[🎬 15초 숏츠 영상 제작 & 쇼룸 갱신]</strong> 버튼을 누르면 즉시 첫 영상이 제작됩니다!</p>
          </div>
        `;
        return;
      }

      container.innerHTML = videos.map(v => `
        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); border-radius: 14px; overflow: hidden; display: flex; flex-direction: column;">
          <div style="background: #000; display: flex; justify-content: center; align-items: center; max-height: 420px; overflow: hidden;">
            <video src="${v.url}" controls playsinline preload="metadata" style="max-height: 400px; width: 100%; object-fit: contain;"></video>
          </div>
          <div style="padding: 14px; display: flex; flex-direction: column; gap: 8px; flex: 1;">
            <div style="font-weight: 600; font-size: 13.5px; color: #F8FAFC; line-height: 1.4; word-break: break-all;">${v.filename}</div>
            <div style="font-size: 12px; color: var(--text-muted); display: flex; justify-content: space-between;">
              <span>💾 ${v.size_mb} MB</span>
              <span>🕒 ${v.created_at || ''}</span>
            </div>
            <div style="margin-top: auto; display: flex; gap: 8px; padding-top: 6px;">
              <a href="${v.url}" download="${v.filename}" class="btn btn-secondary" style="flex: 1; text-align: center; text-decoration: none; font-size: 12px; padding: 8px;">
                <i class="ri-download-line"></i> 다운로드
              </a>
              <button class="btn btn-primary" onclick="navigator.clipboard.writeText(window.location.origin + '${v.url}'); alert('영상 링크가 복사되었습니다!');" style="font-size: 12px; padding: 8px 12px;">
                <i class="ri-file-copy-line"></i>
              </button>
            </div>
          </div>
        </div>
      `).join("");
    } catch (e) {
      console.error("loadVideos error:", e);
      container.innerHTML = `<p style="color: #F87171;">영상 목록 로드 실패: ${e.message}</p>`;
    }
  }

  // Load Preview Tab
  async function loadPreview() {
    try {
      const res = await fetch("/api/posts");
      const posts = await res.json();
      if (!posts || posts.length === 0) return;

      const latest = posts[0];
      const mainTextEl = document.getElementById("preview-main-text");
      const c1El = document.getElementById("preview-comment-1");
      const c2El = document.getElementById("preview-comment-2");
      const c3El = document.getElementById("preview-comment-3");

      if (mainTextEl) mainTextEl.textContent = latest.main_text || "";
      if (c1El) c1El.textContent = latest.comment_1 || "없음";
      if (c2El) c2El.textContent = latest.comment_2 || "없음";
      if (c3El) c3El.textContent = latest.comment_3 || "없음";

      // Cards
      const cardsBox = document.getElementById("preview-cards");
      if (cardsBox) {
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
      }

      // Product Details
      const detailBox = document.getElementById("preview-product-detail");
      if (detailBox) {
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
      if (!tbody) return;

      if (!products || products.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted);">적재된 상품이 없습니다. 버튼을 누르면 자동으로 수집됩니다.</td></tr>`;
        return;
      }

      tbody.innerHTML = products.map(p => {
        const linkDisplay = p.deeplink 
          ? `<a href="${p.deeplink}" target="_blank" rel="noopener noreferrer" style="color: #38BDF8; font-size: 12px; text-decoration: underline; display: inline-flex; align-items: center; gap: 4px;">
               <i class="ri-external-link-line"></i> ${p.deeplink.includes('np/search') ? '쿠팡 검색결과 열기' : '파트너스 링크 열기'}
             </a>`
          : '<span style="color: var(--text-muted); font-size: 12px;">대기중</span>';

        return `
        <tr>
          <td><strong style="color: #F43F5E; font-size: 14px;">#${p.showroom_num || '-'}</strong></td>
          <td><span style="background: rgba(99,102,241,0.2); color: #818CF8; padding: 2px 8px; border-radius: 4px; font-weight: 600;">${p.category}</span></td>
          <td style="max-width: 240px; font-weight: 500;">${p.title}</td>
          <td style="color: #38BDF8; font-weight: 600;">${p.price.toLocaleString()}원</td>
          <td>★ ${p.rating} (${p.review_count.toLocaleString()})</td>
          <td>${p.is_rocket ? '<span style="color: #4ADE80; font-weight: 600;">✓ 로켓배송</span>' : '일반'}</td>
          <td>${linkDisplay}</td>
          <td>
            <button class="btn btn-secondary btn-edit-link" 
                    data-id="${p.product_id}" 
                    data-title="${encodeURIComponent(p.title)}" 
                    data-link="${encodeURIComponent(p.deeplink || '')}" 
                    style="font-size: 11px; padding: 4px 8px;">
              <i class="ri-edit-line"></i> 링크 수정
            </button>
          </td>
        </tr>
      `;
      }).join("");

      // Bind edit link buttons
      tbody.querySelectorAll(".btn-edit-link").forEach(btn => {
        btn.addEventListener("click", async () => {
          const pid = btn.dataset.id;
          const ptitle = decodeURIComponent(btn.dataset.title);
          const currentLink = decodeURIComponent(btn.dataset.link);
          const newLink = prompt(`[${ptitle}]\n\n이 상품에 적용할 쿠팡 파트너스 링크 또는 쿠팡 상품 URL을 입력하세요:\n(미입력 시 쿠팡 검색결과로 자동 연결됩니다)`, currentLink);
          if (newLink !== null && newLink.trim()) {
            try {
              const uRes = await fetch("/api/products/update-link", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ product_id: pid, new_link: newLink.trim() })
              });
              const uData = await uRes.json();
              if (uData.success) {
                showToast("✅ " + uData.message);
                loadProducts();
                const iframe = document.getElementById("showroom-iframe");
                if (iframe) iframe.src = "/showroom?t=" + Date.now();
              } else {
                showToast("⚠️ " + (uData.error || "수정 실패"));
              }
            } catch (err) {
              showToast("오류: " + err.message);
            }
          }
        });
      });
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
      if (!tbody) return;

      if (!posts || posts.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">발행 이력이 없습니다.</td></tr>`;
        return;
      }

      tbody.innerHTML = posts.map(p => `
        <tr>
          <td>#${p.id}</td>
          <td><span class="status-badge ${p.post_type === 'shorts' ? 'posted' : (p.post_type === 'affiliate' ? 'posted' : 'simulated')}">${p.post_type === 'shorts' ? '숏츠영상' : (p.post_type === 'affiliate' ? '수익화글' : '공감/꿀팁글')}</span></td>
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
      if (!container) return;

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

  // Action: Trigger Shorts Cycle (Shorts Video + Showroom Update)
  const triggerShortsBtn = document.getElementById("btn-trigger-shorts");
  if (triggerShortsBtn) {
    triggerShortsBtn.addEventListener("click", async () => {
      triggerShortsBtn.disabled = true;
      triggerShortsBtn.innerHTML = '<i class="ri-loader-4-line ri-spin"></i> 🎬 숏츠 영상 제작 및 쇼룸 갱신 중...';

      try {
        const res = await fetch("/api/trigger/shorts", { method: "POST" });
        const data = await res.json();
        if (data.success) {
          showToast("🎉 15초 숏츠 영상 제작 & 모바일 쇼룸 갱신이 완료되었습니다!");
          loadStatus();
          loadOverviewRecent();
          loadVideos();
          const iframe = document.getElementById("showroom-iframe");
          if (iframe) iframe.src = "/showroom?t=" + Date.now();
        } else {
          showToast("오류 발생: " + (data.error || "알 수 없는 오류"));
        }
      } catch (e) {
        showToast("요청 실패: " + e.message);
      } finally {
        triggerShortsBtn.disabled = false;
        triggerShortsBtn.innerHTML = '<i class="ri-movie-line"></i> 🎬 15초 숏츠 영상 제작 & 쇼룸 갱신';
      }
    });
  }

  // Action: Trigger Threads Post (Separated)
  const triggerThreadsBtn = document.getElementById("btn-trigger-threads");
  if (triggerThreadsBtn) {
    triggerThreadsBtn.addEventListener("click", async () => {
      triggerThreadsBtn.disabled = true;
      triggerThreadsBtn.innerHTML = '<i class="ri-loader-4-line ri-spin"></i> 🧵 쓰레드 발행 중...';

      try {
        const res = await fetch("/api/trigger/threads", { method: "POST" });
        const data = await res.json();
        if (data.success) {
          showToast("🚀 쓰레드 포스팅이 완료되었습니다!");
          loadStatus();
          loadOverviewRecent();
          loadPreview();
          loadPosts();
        } else {
          showToast("오류 발생: " + (data.error || "알 수 없는 오류"));
        }
      } catch (e) {
        showToast("요청 실패: " + e.message);
      } finally {
        triggerThreadsBtn.disabled = false;
        triggerThreadsBtn.innerHTML = '<i class="ri-threads-line"></i> 🧵 쓰레드 즉시 발행';
      }
    });
  }

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

  // Action: Copy Showroom URL
  const copyShowroomBtn = document.getElementById("btn-copy-showroom-url");
  if (copyShowroomBtn) {
    copyShowroomBtn.addEventListener("click", () => {
      const showroomInput = document.getElementById("showroom-url-input");
      if (showroomInput) {
        navigator.clipboard.writeText(showroomInput.value).then(() => {
          showToast("📋 쇼룸 웹페이지 주소가 복사되었습니다! (유튜브 프로필에 등록하세요)");
        }).catch(() => {
          showroomInput.select();
          document.execCommand("copy");
          showToast("📋 쇼룸 주소가 복사되었습니다!");
        });
      }
    });
  }

  // Action: Copy Spotlight YouTube Title & Description
  const btnCopySpotTitle = document.getElementById("btn-copy-spotlight-title");
  if (btnCopySpotTitle) {
    btnCopySpotTitle.addEventListener("click", () => {
      const text = document.getElementById("spotlight-yt-title")?.textContent || "";
      navigator.clipboard.writeText(text).then(() => showToast("📋 유튜브 제목이 복사되었습니다!"));
    });
  }

  const btnCopySpotDesc = document.getElementById("btn-copy-spotlight-desc");
  if (btnCopySpotDesc) {
    btnCopySpotDesc.addEventListener("click", () => {
      const text = document.getElementById("spotlight-yt-desc")?.textContent || "";
      navigator.clipboard.writeText(text).then(() => showToast("📋 유튜브 설명/해시태그가 복사되었습니다!"));
    });
  }

  // Action: Refresh Showroom Iframe
  const refreshShowroomBtn = document.getElementById("btn-refresh-showroom");
  if (refreshShowroomBtn) {
    refreshShowroomBtn.addEventListener("click", () => {
      const iframe = document.getElementById("showroom-iframe");
      if (iframe) iframe.src = "/showroom?t=" + Date.now();
      showToast("🔄 모바일 쇼룸 화면을 새로고침했습니다.");
    });
  }

  // Action: Refresh Videos List
  const refreshVideosBtn = document.getElementById("btn-refresh-videos");
  if (refreshVideosBtn) {
    refreshVideosBtn.addEventListener("click", () => {
      loadVideos();
      showToast("🔄 영상 목록을 새로고침했습니다.");
    });
  }

  // Action: Deploy Showroom to GitHub Pages
  const btnDeployGithub = document.getElementById("btn-deploy-github");
  if (btnDeployGithub) {
    btnDeployGithub.addEventListener("click", async () => {
      btnDeployGithub.disabled = true;
      btnDeployGithub.innerHTML = '<i class="ri-loader-4-line ri-spin"></i> GitHub 배포 중...';
      try {
        const res = await fetch("/api/showroom/deploy-github", { method: "POST" });
        const data = await res.json();
        if (data.success) {
          showToast("🎉 " + data.message);
        } else {
          showToast("⚠️ " + (data.error || "배포 실패"));
        }
      } catch (e) {
        showToast("요청 실패: " + e.message);
      } finally {
        btnDeployGithub.disabled = false;
        btnDeployGithub.innerHTML = '<i class="ri-upload-cloud-line"></i> GitHub 배포/동기화';
      }
    });
  }

  // Action: Quick Save Showroom Public URL
  const btnSavePublicUrl = document.getElementById("btn-save-public-url");
  if (btnSavePublicUrl) {
    btnSavePublicUrl.addEventListener("click", async () => {
      const publicUrl = document.getElementById("showroom-public-url-input")?.value.trim() || "";
      try {
        const statusRes = await fetch("/api/status");
        const statusData = await statusRes.json();
        const currentConfig = statusData.config || {};
        currentConfig.showroom = currentConfig.showroom || {};
        currentConfig.showroom.public_url = publicUrl;

        const res = await fetch("/api/settings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ config: currentConfig })
        });
        const data = await res.json();
        if (data.success) {
          showToast("✅ 공개 쇼룸 URL이 저장되었습니다! (숏츠 설명에 자동 삽입)");
          loadStatus();
        }
      } catch (e) {
        showToast("저장 실패: " + e.message);
      }
    });
  }

  // Action: Toggle Scheduler
  const toggleBtn = document.getElementById("btn-toggle-scheduler");
  if (toggleBtn) {
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
  }

  // Action: Save Settings
  const saveSettingsBtn = document.getElementById("btn-save-settings");
  if (saveSettingsBtn) {
    saveSettingsBtn.addEventListener("click", async (e) => {
      e.preventDefault();
      const goldenRaw = document.getElementById("cfg-golden-hours") ? document.getElementById("cfg-golden-hours").value : "07:30, 12:30, 21:30";
      const goldenList = goldenRaw.split(",").map(s => s.trim()).filter(Boolean);

      const modShorts = document.getElementById("cfg-module-shorts");
      const modThreads = document.getElementById("cfg-module-threads");

      const updatedConfig = {
        modules: {
          shorts_enabled: modShorts ? modShorts.checked : true,
          threads_enabled: modThreads ? modThreads.checked : false,
          showroom_enabled: true
        },
        showroom: {
          public_url: (document.getElementById("showroom-public-url-input")?.value || "").trim()
        },
        youtube: {
          enabled: document.getElementById("cfg-yt-enabled") ? document.getElementById("cfg-yt-enabled").checked : true,
          privacy_status: document.getElementById("cfg-yt-privacy")?.value || "public",
          simulation_mode: false
        },
        tts: {
          provider: document.getElementById("cfg-tts-provider")?.value || "edge_tts",
          edge_voice: document.getElementById("cfg-tts-voice")?.value || "ko-KR-InJoonNeural",
          speed: document.getElementById("cfg-tts-speed")?.value || "+0%",
          elevenlabs_api_key: (document.getElementById("cfg-elevenlabs-key")?.value || "").trim(),
          elevenlabs_voice_id: (document.getElementById("cfg-elevenlabs-voice-id")?.value || "").trim()
        },
        coupang: {
          access_key: (document.getElementById("cfg-coupang-access-key")?.value || "").trim(),
          secret_key: (document.getElementById("cfg-coupang-secret-key")?.value || "").trim(),
          sub_id: "thread_auto",
          default_affiliate_link: (document.getElementById("cfg-default-affiliate-link")?.value || "").trim(),
          use_crawler_fallback: true
        },
        llm: {
          provider: document.getElementById("cfg-llm-provider")?.value || "gemini",
          gemini_api_key: (document.getElementById("cfg-gemini-api-key")?.value || "").trim(),
          openai_api_key: (document.getElementById("cfg-gemini-api-key")?.value || "").trim(),
          model_name: "gemini-2.5-flash",
          temperature: 0.7
        },
        threads: {
          enabled: modThreads ? modThreads.checked : false,
          user_id: (document.getElementById("cfg-threads-user-id")?.value || "").trim(),
          access_token: (document.getElementById("cfg-threads-token")?.value || "").trim(),
          simulation_mode: document.getElementById("cfg-threads-simulation")?.value === "true"
        },
        strategy: {
          golden_hours: goldenList,
          jitter_minutes: parseInt(document.getElementById("cfg-jitter-minutes")?.value) || 15,
          affiliate_ratio: 1,
          info_post_ratio: parseInt(document.getElementById("cfg-info-ratio")?.value) || 3,
          auto_pilot_enabled: true,
          reply_interval_seconds: parseInt(document.getElementById("cfg-reply-interval")?.value) || 20
        },
        notifications: {
          discord_webhook: (document.getElementById("cfg-discord-webhook")?.value || "").trim()
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
  }

  // Refresh logs button
  const refreshLogsBtn = document.getElementById("btn-refresh-logs");
  if (refreshLogsBtn) {
    refreshLogsBtn.addEventListener("click", loadLogs);
  }

  // Initial loads
  loadStatus();
  loadOverviewRecent();
  loadVideos();

  // Auto refresh overview & status every 15s
  setInterval(() => {
    loadStatus();
    loadOverviewRecent();
  }, 15000);
});
