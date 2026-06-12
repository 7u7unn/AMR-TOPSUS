    // ============================================================
    //  SYSTEM CLOCK
    // ============================================================
    (function () {
      function tick() {
        const t = new Date().toLocaleTimeString('en-GB', { hour12: false });
        const el = document.getElementById('sysTime');
        const cl = document.getElementById('sbClock');
        if (el) el.textContent = t;
        if (cl) cl.textContent = t;
      }
      tick(); setInterval(tick, 1000);
    })();

    // ============================================================
    //  SIDEBAR TOGGLE
    // ============================================================
    const sidebar = document.getElementById('sidebar');
    document.getElementById('sidebarToggle').addEventListener('click', () => {
      sidebar.classList.toggle('col');
    });

    // ============================================================
    //  VIEW SWITCHING (sidebar nav)
    // ============================================================
    function switchView(viewId) {
      document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
      document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
      document.getElementById('view-' + viewId).classList.add('active');
      document.getElementById('nav-' + viewId).classList.add('active');
      // toolbar
      document.getElementById('toolbar-drive').style.display = viewId === 'drive' ? 'flex' : 'none';
      document.getElementById('toolbar-io').style.display = viewId === 'io' ? 'flex' : 'none';
      document.getElementById('toolbar-topics').style.display = viewId === 'topics' ? 'flex' : 'none';
      const tbNav = document.getElementById('toolbar-navigation');
      if (tbNav) tbNav.style.display = viewId === 'navigation' ? 'flex' : 'none';
      if (viewId === 'navigation' && typeof window.requestNavDraw === 'function') {
        requestAnimationFrame(window.requestNavDraw);
      }
    }

    document.querySelectorAll('.nav-item[data-view]').forEach(item => {
      item.addEventListener('click', () => switchView(item.dataset.view));
    });

    // Also hook up settings nav item
    document.getElementById('nav-settings').addEventListener('click', () => openModal('modalSettings'));

    // ============================================================
    //  PANEL COLLAPSE
    // ============================================================
    document.querySelectorAll('.panel-collapse-btn[data-target]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.getElementById(btn.dataset.target).classList.toggle('coll');
        if (btn.dataset.target === 'p-nav-map' && typeof window.requestNavDraw === 'function') {
          requestAnimationFrame(window.requestNavDraw);
        }
      });
    });

    // ============================================================
    //  TOOLBAR PANEL TOGGLES
    // ============================================================
    document.querySelectorAll('.tb-btn[data-panel]').forEach(btn => {
      btn.addEventListener('click', () => {
        const panelEl = document.getElementById(btn.dataset.panel);
        if (!panelEl) return;
        const hidden = panelEl.classList.toggle('phide');
        btn.classList.toggle('on', !hidden);
        if (btn.dataset.panel === 'p-nav-map' && typeof window.requestNavDraw === 'function') {
          requestAnimationFrame(window.requestNavDraw);
        }
      });
    });

    // ============================================================
    //  MODAL SYSTEM
    // ============================================================
    const backdrop = document.getElementById('modalBackdrop');
    let pendingConfirmFn = null;

    function openModal(id) {
      backdrop.classList.add('open');
      document.getElementById(id).classList.add('open');
    }
    function closeModal(id) {
      backdrop.classList.remove('open');
      document.getElementById(id).classList.remove('open');
    }
    function confirmAction(title, heading, msg, onConfirm) {
      document.getElementById('confirmTitle').textContent = title;
      document.getElementById('confirmHeading').textContent = heading;
      document.getElementById('confirmMsg').textContent = msg;
      pendingConfirmFn = onConfirm;
      openModal('modalConfirm');
    }

    document.getElementById('confirmOk').addEventListener('click', () => {
      if (typeof pendingConfirmFn === 'function') pendingConfirmFn();
      pendingConfirmFn = null;
      closeModal('modalConfirm');
    });

    document.querySelectorAll('[data-close]').forEach(el => {
      el.addEventListener('click', () => closeModal(el.dataset.close));
    });

    backdrop.addEventListener('click', () => {
      document.querySelectorAll('.modal.open').forEach(m => m.classList.remove('open'));
      backdrop.classList.remove('open');
    });

    document.getElementById('openSettings').addEventListener('click', () => openModal('modalSettings'));
    document.getElementById('saveSettings').addEventListener('click', () => {
      closeModal('modalSettings');
      location.reload();
    });

    // ============================================================
    //  IO CONFIGURATION
    // ============================================================
    const DI_CONFIG = [
      { num: 1, name: "FRONT GREEN BTN", desc: "Button 1", topic: "io/di1" },
      { num: 2, name: "FRONT YELLOW BTN", desc: "Button 2", topic: "io/di2" },
      { num: 3, name: "REAR GREEN BTN", desc: "Button 3", topic: "io/di3" },
      { num: 4, name: "REAR YELLOW BTN", desc: "Button 4", topic: "io/di4" },
      { num: 5, name: "UNKNOWN", desc: "Unknown input", topic: "io/di5" },
      { num: 6, name: "UNKNOWN", desc: "Unknown input", topic: "io/di6" },
      { num: 7, name: "UNKNOWN", desc: "Unknown input", topic: "io/di7" },
      { num: 8, name: "UNKNOWN", desc: "Unknown input", topic: "io/di8" },
    ];
    const DO_CONFIG = [
      { num: 1, name: "FRONT YELLOW LAMP", desc: "lampu depan, kuning", topic: "io/do1" },
      { num: 2, name: "REAR YELLOW LAMP", desc: "Front headlight relay", topic: "io/do2" },
      { num: 3, name: "RELAY 1", desc: "unknown relay", topic: "io/do3" },
      { num: 4, name: "MOTOR DRIVER", desc: "relay power driver", topic: "io/do4" },
      { num: 5, name: "FRONT LIFTER", desc: "on = turun, off = naik", topic: "io/do5" },
      { num: 6, name: "BUZZER", desc: "bipping buzzer", topic: "io/do6" },
      { num: 7, name: "REAR LIFTER", desc: "on = turun, off = naik", topic: "io/do7" },
      { num: 8, name: "RELAY 2", desc: "unknown relay", topic: "io/do8" },
    ];

    // Build I/O Map Table
    (function buildMap() {
      const tbody = document.getElementById('ioMapBody');
      let rows = '';
      DI_CONFIG.forEach(ch => {
        rows += `<tr>
      <td style="font-family:var(--fm);font-size:.74rem;color:var(--t3)">${ch.num}</td>
      <td style="font-family:var(--fm);font-weight:700;color:var(--gn)">DI${ch.num}</td>
      <td><span class="tag tag-di">INPUT</span></td>
      <td style="color:var(--t2);font-size:.8rem">${ch.desc}</td>
      <td style="font-family:var(--fm);font-size:.68rem;color:var(--cy)">${ch.topic}</td>
      <td><span class="mini-led" id="map-di${ch.num}"></span></td>
    </tr>`;
      });
      DO_CONFIG.forEach(ch => {
        rows += `<tr>
      <td style="font-family:var(--fm);font-size:.74rem;color:var(--t3)">${ch.num}</td>
      <td style="font-family:var(--fm);font-weight:700;color:var(--or)">DO${ch.num}</td>
      <td><span class="tag tag-do">OUTPUT</span></td>
      <td style="color:var(--t2);font-size:.8rem">${ch.desc}</td>
      <td style="font-family:var(--fm);font-size:.68rem;color:var(--cy)">${ch.topic}</td>
      <td><span class="mini-do" id="map-do${ch.num}"></span></td>
    </tr>`;
      });
      tbody.innerHTML = rows;
    })();

    // Build DI Channels
    const diState = new Array(8).fill(false);
    const doState = new Array(8).fill(false);

    (function buildDI() {
      const cont = document.getElementById('diChannels');
      DI_CONFIG.forEach((ch, i) => {
        const el = document.createElement('div');
        el.className = 'io-channel';
        el.id = `di-ch-${i}`;
        el.innerHTML = `
      <div class="led" id="di-led-${i}"></div>
      <div class="io-ch-info">
        <div class="io-ch-num">DI${ch.num} · ${ch.topic}</div>
        <div class="io-ch-name">${ch.name}</div>
        <div class="io-ch-st" id="di-status-${i}">INACTIVE</div>
      </div>`;
        cont.appendChild(el);
      });
    })();

    (function buildDO() {
      const cont = document.getElementById('doChannels');
      DO_CONFIG.forEach((ch, i) => {
        const el = document.createElement('div');
        el.className = 'io-channel';
        el.id = `do-ch-${i}`;
        el.innerHTML = `
      <div class="toggle-sw">
        <input type="checkbox" id="do-toggle-${i}">
        <label class="tog-track" for="do-toggle-${i}"></label>
      </div>
      <div class="io-ch-info">
        <div class="io-ch-num">DO${ch.num} · ${ch.topic}</div>
        <div class="io-ch-name">${ch.name}</div>
        <div class="io-ch-st" id="do-status-${i}">OFF</div>
      </div>`;
        cont.appendChild(el);
        document.getElementById(`do-toggle-${i}`).addEventListener('change', function () {
          doState[i] = this.checked;
          applyDoUi(i, doState[i]);
          safeSend({ type: 'io_set_single', channel: i + 1, cmd: doState[i] ? 'on' : 'off' });
        });
      });
    })();

    // UI helpers
    function applyDiUi(i, on) {
      const led = document.getElementById(`di-led-${i}`);
      const status = document.getElementById(`di-status-${i}`);
      const row = document.getElementById(`di-ch-${i}`);
      const mapLed = document.getElementById(`map-di${i + 1}`);
      if (led) { led.className = 'led' + (on ? ' on' : ''); }
      if (status) { status.className = 'io-ch-st' + (on ? ' on' : ''); status.textContent = on ? 'ACTIVE' : 'INACTIVE'; }
      if (row) { row.classList.toggle('on-di', on); }
      if (mapLed) { mapLed.className = 'mini-led' + (on ? ' on' : ''); }
    }

    function applyDoUi(i, on) {
      const chk = document.getElementById(`do-toggle-${i}`);
      const status = document.getElementById(`do-status-${i}`);
      const row = document.getElementById(`do-ch-${i}`);
      const mapDo = document.getElementById(`map-do${i + 1}`);
      if (chk) { chk.checked = on; }
      if (status) { status.className = 'io-ch-st' + (on ? ' on-do' : ''); status.textContent = on ? 'ON' : 'OFF'; }
      if (row) { row.classList.toggle('on-do', on); }
      if (mapDo) { mapDo.className = 'mini-do' + (on ? ' on' : ''); }
    }

    function refreshDiByte(byte) {
      let count = 0;
      for (let i = 0; i < 8; i++) {
        const on = !!((byte >> i) & 1);
        if (diState[i] !== on) { diState[i] = on; applyDiUi(i, on); }
        if (on) count++;
      }
      const hex = '0x' + byte.toString(16).toUpperCase().padStart(2, '0');
      document.getElementById('diByteHex').textContent = hex;
      document.getElementById('diByteBadge').textContent = hex;
      document.getElementById('diActiveCount').textContent = count;
      document.getElementById('sbIoDot').className = 'sb-dot' + (count > 0 ? ' ok' : ' warn');
      document.getElementById('sbIoText').textContent = count > 0 ? `${count} ACTIVE` : 'STANDBY';
    }

    function refreshDoByte(byte) {
      let count = 0;
      for (let i = 0; i < 8; i++) {
        const on = !!((byte >> i) & 1);
        if (doState[i] !== on) { doState[i] = on; applyDoUi(i, on); }
        if (on) count++;
      }
      const hex = '0x' + byte.toString(16).toUpperCase().padStart(2, '0');
      document.getElementById('doByteHex').textContent = hex;
      document.getElementById('doByteBadge').textContent = hex;
      document.getElementById('doActiveCount').textContent = count;
      document.getElementById('ioBadge').textContent = `${count}/8`;
    }

    // ============================================================
    //  BULK DO CONTROLS
    // ============================================================
    document.getElementById('doAllOn').addEventListener('click', () => {
      for (let i = 0; i < 8; i++) { doState[i] = true; applyDoUi(i, true); }
      refreshDoByte(0xFF); safeSend({ type: 'io_mask', mask: 0xFF });
    });
    document.getElementById('doAllOff').addEventListener('click', () => {
      for (let i = 0; i < 8; i++) { doState[i] = false; applyDoUi(i, false); }
      refreshDoByte(0x00); safeSend({ type: 'io_mask', mask: 0x00 });
    });
    document.getElementById('doToggleAll').addEventListener('click', () => {
      let mask = 0;
      for (let i = 0; i < 8; i++) { doState[i] = !doState[i]; applyDoUi(i, doState[i]); if (doState[i]) mask |= (1 << i); }
      refreshDoByte(mask); safeSend({ type: 'io_mask', mask });
    });
    // Toolbar bulk
    document.getElementById('tbDoAllOn').addEventListener('click', () => document.getElementById('doAllOn').click());
    document.getElementById('tbDoAllOff').addEventListener('click', () => document.getElementById('doAllOff').click());

    // ============================================================
    //  ROS TOPIC ECHO
    // ============================================================
    let rosTopics = [];
    let topicWs = null;
    let topicReconnectTimer = null;
    let topicManualStop = false;
    const topicSelect1 = document.getElementById('topicSelect1');
    const topicSelect2 = document.getElementById('topicSelect2');
    const topicSearch = document.getElementById('topicSearch');
    const topicHint = document.getElementById('topicHint');
    const topicBadge = document.getElementById('topicBadge');
    const topicActiveCount = document.getElementById('topicActiveCount');
    const topicRate = document.getElementById('topicRate');
    const topicCountChip = document.getElementById('topicCountChip');

    function topicSocketUrl() {
      const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
      const host = location.host || 'localhost:8000';
      return `${protocol}://${host}/ws/topics`;
    }

    function currentTopicSelections() {
      const topics = [topicSelect1.value, topicSelect2.value].map(v => (v || '').trim()).filter(Boolean);
      return [...new Set(topics)].slice(0, 2);
    }

    function setTopicStatus(text, activeCount) {
      if (topicHint) topicHint.textContent = text;
      const countText = `${activeCount || 0}/2`;
      if (topicBadge) topicBadge.textContent = countText;
      if (topicActiveCount) topicActiveCount.textContent = countText;
    }

    function optionLabel(topic) {
      const type = Array.isArray(topic.types) && topic.types.length ? topic.types[0] : 'unknown';
      return `${topic.name}  (${type})`;
    }

    function renderTopicOptions() {
      const filter = (topicSearch.value || '').trim().toLowerCase();
      const visible = rosTopics.filter(topic => !filter || topic.name.toLowerCase().includes(filter));
      const previous = [topicSelect1.value, topicSelect2.value];
      [topicSelect1, topicSelect2].forEach((select, idx) => {
        select.innerHTML = '<option value="">-- idle --</option>';
        visible.forEach(topic => {
          const opt = document.createElement('option');
          opt.value = topic.name;
          opt.textContent = optionLabel(topic);
          select.appendChild(opt);
        });
        if (previous[idx] && visible.some(topic => topic.name === previous[idx])) {
          select.value = previous[idx];
        }
      });
      if (topicCountChip) topicCountChip.textContent = `${rosTopics.length} topics`;
    }

    async function loadRosTopics() {
      setTopicStatus('Loading ROS topic list...', currentTopicSelections().length);
      try {
        const res = await fetch(getApiUrl('/api/topics'), { cache: 'no-store' });
        const payload = await res.json();
        if (!res.ok) throw new Error(payload.detail || 'Failed to load topics');
        rosTopics = Array.isArray(payload.topics) ? payload.topics : [];
        renderTopicOptions();
        if (payload.ros_ready === false) {
          setTopicStatus('ROS node belum siap. Refresh otomatis...', currentTopicSelections().length);
          setTimeout(loadRosTopics, 1500);
        } else {
          setTopicStatus(rosTopics.length ? 'ROS topic list ready.' : 'No ROS topics available.', currentTopicSelections().length);
        }
      } catch (err) {
        rosTopics = [];
        renderTopicOptions();
        setTopicStatus(err && err.message ? err.message : 'Failed to load ROS topics.', 0);
      }
    }

    function clearEchoSlots() {
      [1, 2].forEach(slot => {
        document.getElementById(`echoSlot${slot}`).classList.add('idle');
        document.getElementById(`echoTitle${slot}`).textContent = `Slot ${slot}`;
        document.getElementById(`echoType${slot}`).textContent = 'idle';
        const body = document.getElementById(`echoBody${slot}`);
        body.classList.add('echo-empty');
        body.textContent = 'No topic selected';
      });
      if (topicRate) topicRate.textContent = 'idle';
      setTopicStatus('Echo stopped.', 0);
    }

    function updateEchoSlot(update) {
      const slot = Number(update.slot || 0);
      if (slot < 1 || slot > 2) return;
      const slotEl = document.getElementById(`echoSlot${slot}`);
      const body = document.getElementById(`echoBody${slot}`);
      slotEl.classList.remove('idle');
      document.getElementById(`echoTitle${slot}`).textContent = update.topic || `Slot ${slot}`;
      document.getElementById(`echoType${slot}`).textContent = update.msg_type || 'unknown';
      body.classList.remove('echo-empty');
      body.textContent = JSON.stringify({
        stamp: update.stamp,
        count: update.count,
        data: update.data,
      }, null, 2);
    }

    function stopTopicEcho() {
      topicManualStop = true;
      if (topicReconnectTimer) {
        clearTimeout(topicReconnectTimer);
        topicReconnectTimer = null;
      }
      if (topicWs) {
        try { topicWs.send(JSON.stringify({ type: 'clear' })); } catch (e) { }
        try { topicWs.close(); } catch (e) { }
        topicWs = null;
      }
      clearEchoSlots();
    }

    function startTopicEcho() {
      const topics = currentTopicSelections();
      if (!topics.length) {
        stopTopicEcho();
        setTopicStatus('Pilih minimal satu ROS topic.', 0);
        return;
      }
      if (topics.length > 2) {
        setTopicStatus('Echo dibatasi maksimal 2 ROS topic.', 2);
        return;
      }

      if (topicWs && topicWs.readyState === WebSocket.OPEN) {
        topicWs.send(JSON.stringify({ type: 'subscribe', topics }));
        setTopicStatus('Subscribing...', topics.length);
        return;
      }

      stopTopicEcho();
      topicManualStop = false;
      topicWs = new WebSocket(topicSocketUrl());
      const socket = topicWs;
      socket.onopen = () => {
        socket.send(JSON.stringify({ type: 'subscribe', topics }));
        setTopicStatus('Subscribing...', topics.length);
      };
      socket.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'subscribed') {
            clearEchoSlots();
            const slots = Array.isArray(msg.slots) ? msg.slots : [];
            slots.forEach(slot => updateEchoSlot({
              slot: slot.slot,
              topic: slot.topic,
              msg_type: slot.msg_type,
              stamp: 'waiting',
              count: 0,
              data: { status: 'waiting for message' }
            }));
            setTopicStatus('Echo running.', slots.length);
            if (topicRate) topicRate.textContent = msg.rate_hz ? `${msg.rate_hz} Hz` : '5 Hz';
          } else if (msg.type === 'echo') {
            (msg.updates || []).forEach(updateEchoSlot);
          } else if (msg.type === 'error') {
            setTopicStatus(msg.detail || 'Topic echo error.', currentTopicSelections().length);
          }
        } catch (err) {
          setTopicStatus('Topic echo parse error.', currentTopicSelections().length);
        }
      };
      socket.onclose = () => {
        const isActiveSocket = topicWs === socket;
        if (isActiveSocket) topicWs = null;
        if (!isActiveSocket) return;
        if (topicManualStop) {
          topicManualStop = false;
          return;
        }
        setTopicStatus('Topic echo disconnected.', 0);
      };
      socket.onerror = () => {
        setTopicStatus('Topic echo socket error.', currentTopicSelections().length);
      };
    }

    topicSearch.addEventListener('input', renderTopicOptions);
    document.getElementById('startEcho').addEventListener('click', startTopicEcho);
    document.getElementById('stopEcho').addEventListener('click', stopTopicEcho);
    document.getElementById('tbRefreshTopics').addEventListener('click', loadRosTopics);
    document.getElementById('tbStopEcho').addEventListener('click', stopTopicEcho);
    loadRosTopics();

    // ============================================================
    //  WEBSOCKET
    // ============================================================
    let ws = null, reconnectTimer = null, isConnected = false;
    const statusBadge = document.getElementById('statusBadge');
    const ioConnDot = document.getElementById('ioConnDot');
    const selectedMapLabel = document.getElementById('selectedMapName');
    const btnChooseMap = document.getElementById('btnChooseMap');
    const modalMapSelect = document.getElementById('modalMapSelect');
    const mapPreviewCanvas = document.getElementById('mapPreviewCanvas');
    const mapPreviewEmpty = document.getElementById('mapPreviewEmpty');
    const chooseMapStatus = document.getElementById('chooseMapStatus');
    const btnConfirmChooseMap = document.getElementById('btnConfirmChooseMap');
    window.selectedMapName = '';
    window.availableMaps = [];
    let canvasDrawQueued = false;

    function queueCanvasDraw() {
      if (!window.drawFixedAxesAndRobot || canvasDrawQueued) return;
      canvasDrawQueued = true;
      requestAnimationFrame(() => {
        canvasDrawQueued = false;
        if (window.drawFixedAxesAndRobot) {
          window.drawFixedAxesAndRobot(window.data.x, window.data.y, window.data.theta);
        }
      });
    }

    function updateStatus(t, state) {
      statusBadge.textContent = t;
      statusBadge.className = state;
      ioConnDot.className = 'conn-dot' + (state === 'connected' ? ' ok' : state === 'error' ? ' err' : '');
      const msg = document.getElementById('sbMsg');
      if (msg) msg.textContent = state === 'connected' ? 'WebSocket connected — receiving telemetry data' : state === 'error' ? 'WebSocket disconnected — attempting reconnect...' : 'Connecting to WebSocket server...';
    }

    function setSelectedMapUi(mapName) {
      window.selectedMapName = mapName || '';
      if (selectedMapLabel) {
        selectedMapLabel.textContent = window.selectedMapName || 'No map selected';
        selectedMapLabel.title = window.selectedMapName || 'No map selected';
      }
      if (modalMapSelect && window.selectedMapName) {
        modalMapSelect.value = window.selectedMapName;
      }
    }

    function setChooseMapStatus(text, state = '') {
      if (!chooseMapStatus) return;
      chooseMapStatus.textContent = text;
      chooseMapStatus.className = 'choose-map-status' + (state ? ` ${state}` : '');
    }

    function clearMapPreview(message = 'Pilih map untuk melihat preview.') {
      if (mapPreviewCanvas) {
        const ctx = mapPreviewCanvas.getContext('2d');
        ctx.clearRect(0, 0, mapPreviewCanvas.width, mapPreviewCanvas.height);
        ctx.fillStyle = '#F8FAFC';
        ctx.fillRect(0, 0, mapPreviewCanvas.width, mapPreviewCanvas.height);
      }
      if (mapPreviewEmpty) {
        mapPreviewEmpty.textContent = message;
        mapPreviewEmpty.hidden = false;
      }
    }

    async function drawMapPreview(mapName) {
      if (!mapPreviewCanvas) return;
      if (!mapName) {
        clearMapPreview();
        return;
      }
      setChooseMapStatus(`Memuat preview ${mapName}...`, 'busy');
      try {
        const res = await fetch(getApiUrl(`/api/maps/grid?map_name=${encodeURIComponent(mapName)}`), { cache: 'no-store' });
        const grid = await res.json();
        if (!res.ok) throw new Error(grid.detail || 'Gagal memuat preview map.');

        const ctx = mapPreviewCanvas.getContext('2d');
        const wrap = mapPreviewCanvas.parentElement;
        const rect = wrap ? wrap.getBoundingClientRect() : mapPreviewCanvas.getBoundingClientRect();
        mapPreviewCanvas.width = Math.max(360, Math.round(rect.width || 720));
        mapPreviewCanvas.height = Math.max(240, Math.round(rect.height || 360));
        ctx.fillStyle = '#F8FAFC';
        ctx.fillRect(0, 0, mapPreviewCanvas.width, mapPreviewCanvas.height);

        const img = new ImageData(grid.w, grid.h);
        const bin = atob(grid.b64 || '');
        for (let i = 0; i < bin.length; i++) {
          let val = bin.charCodeAt(i);
          if (val > 127) val -= 256;
          let shade = 225;
          if (val === -1) shade = 218;
          else if (val === 0) shade = 255;
          else if (val >= 99) shade = 20;
          else shade = Math.max(80, 255 - Math.floor(val * 2.2));
          const idx = i * 4;
          img.data[idx] = shade;
          img.data[idx + 1] = shade;
          img.data[idx + 2] = shade;
          img.data[idx + 3] = 255;
        }

        const bitmap = await createImageBitmap(img);
        const scale = Math.min(
          mapPreviewCanvas.width / Math.max(1, grid.w),
          mapPreviewCanvas.height / Math.max(1, grid.h)
        );
        const drawW = grid.w * scale;
        const drawH = grid.h * scale;
        const dx = (mapPreviewCanvas.width - drawW) / 2;
        const dy = (mapPreviewCanvas.height - drawH) / 2;
        ctx.imageSmoothingEnabled = false;
        ctx.drawImage(bitmap, dx, dy, drawW, drawH);
        if (mapPreviewEmpty) mapPreviewEmpty.hidden = true;
        setChooseMapStatus(`Preview ${mapName} siap.`, 'success');
      } catch (err) {
        clearMapPreview(err && err.message ? err.message : 'Gagal memuat preview map.');
        setChooseMapStatus(err && err.message ? err.message : 'Gagal memuat preview map.', 'error');
      }
    }

    async function saveSelectedMap(selectedMap) {
      if (!selectedMap) return;
      if (modalMapSelect) modalMapSelect.disabled = true;
      if (btnConfirmChooseMap) btnConfirmChooseMap.disabled = true;
      setChooseMapStatus(`Menyimpan map ${selectedMap}...`, 'busy');
      try {
        const res = await fetch(getApiUrl('/api/maps/select'), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ map_name: selectedMap }) });
        const pl = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(pl.detail || 'Gagal menyimpan map');
        setSelectedMapUi(selectedMap);
        setChooseMapStatus(pl.message || `Map ${selectedMap} disimpan.`, 'success');
        document.dispatchEvent(new CustomEvent('arya:map-selected', { detail: { mapName: selectedMap } }));
        return true;
      } catch (err) {
        setChooseMapStatus(err && err.message ? err.message : 'Gagal menyimpan map.', 'error');
        return false;
      } finally {
        if (modalMapSelect) modalMapSelect.disabled = !window.availableMaps.length;
        if (btnConfirmChooseMap) btnConfirmChooseMap.disabled = !modalMapSelect || !modalMapSelect.value;
      }
    }

    async function loadAvailableMaps() {
      if (!modalMapSelect) return;
      modalMapSelect.disabled = true;
      if (btnConfirmChooseMap) btnConfirmChooseMap.disabled = true;
      setChooseMapStatus('Memuat daftar map...', 'busy');
      try {
        const res = await fetch(getApiUrl('/api/maps'), { cache: 'no-store' });
        const pl = await res.json();
        const maps = Array.isArray(pl.maps) ? pl.maps : [];
        if (!res.ok) throw new Error(pl.detail || 'Gagal memuat daftar map');
        window.availableMaps = maps;
        modalMapSelect.innerHTML = '';
        if (!maps.length) {
          modalMapSelect.innerHTML = '<option value="">Tidak ada map YAML</option>';
          setSelectedMapUi('');
          clearMapPreview('Folder amr_bringup_headless/maps belum berisi file .yaml.');
          setChooseMapStatus('Folder amr_bringup_headless/maps belum berisi file .yaml.', 'error');
          return;
        }
        maps.forEach(name => {
          const opt = document.createElement('option');
          opt.value = name; opt.textContent = name;
          if (name === pl.selected_map) opt.selected = true;
          modalMapSelect.appendChild(opt);
        });
        modalMapSelect.disabled = false;
        if (btnConfirmChooseMap) btnConfirmChooseMap.disabled = false;
        setSelectedMapUi(pl.selected_map || modalMapSelect.value);
        setChooseMapStatus(`Map aktif: ${window.selectedMapName}.`, 'success');
        document.dispatchEvent(new CustomEvent('arya:maps-loaded', { detail: { mapName: window.selectedMapName } }));
        drawMapPreview(window.selectedMapName);
      } catch (err) {
        window.availableMaps = [];
        modalMapSelect.innerHTML = '<option value="">Gagal load map</option>';
        clearMapPreview(err && err.message ? err.message : 'Gagal memuat daftar map.');
        setChooseMapStatus(err && err.message ? err.message : 'Gagal memuat daftar map.', 'error');
      }
    }

    async function openMapChooser() {
      openModal('modalChooseMap');
      if (!window.availableMaps.length) await loadAvailableMaps();
      else {
        if (modalMapSelect && window.selectedMapName) modalMapSelect.value = window.selectedMapName;
        drawMapPreview(window.selectedMapName || (modalMapSelect && modalMapSelect.value));
      }
      setTimeout(() => modalMapSelect && modalMapSelect.focus(), 40);
    }

    if (btnChooseMap) btnChooseMap.addEventListener('click', openMapChooser);
    if (modalMapSelect) {
      modalMapSelect.addEventListener('change', () => {
        if (btnConfirmChooseMap) btnConfirmChooseMap.disabled = !modalMapSelect.value;
        drawMapPreview(modalMapSelect.value);
      });
    }
    if (btnConfirmChooseMap) {
      btnConfirmChooseMap.addEventListener('click', async () => {
        const nextMap = modalMapSelect ? modalMapSelect.value : '';
        if (!nextMap) {
          setChooseMapStatus('Pilih map dulu.', 'error');
          return;
        }
        if (await saveSelectedMap(nextMap)) closeModal('modalChooseMap');
      });
    }
    loadAvailableMaps();

    const launchMeta = {
      amir_hdl: {
        title: 'Hardware',
        short: 'Hardware',
        buttonId: 'btnLaunchHardware',
        stateId: 'launchStateHardware',
        startHeading: 'START HARDWARE',
        stopHeading: 'STOP HARDWARE',
        startMsg: 'Run alias amir_hdl as a managed hardware launch process?',
        stopMsg: 'Stop Hardware? Nav2, Localization, and Mapping will be stopped first.'
      },
      local_hdl: {
        title: 'Localization',
        short: 'Local',
        buttonId: 'btnLaunchLocal',
        stateId: 'launchStateLocal',
        startHeading: 'START LOCALIZATION',
        stopHeading: 'STOP LOCALIZATION',
        startMsg: 'Run alias local_hdl as a managed background launch process?',
        stopMsg: 'Stop the managed localization launch process?'
      },
      nav_hdl: {
        title: 'Nav2',
        short: 'Nav2',
        buttonId: 'btnLaunchNav',
        stateId: 'launchStateNav',
        startHeading: 'START NAV2',
        stopHeading: 'STOP NAV2',
        startMsg: 'Run alias nav_hdl as a managed background launch process? Localization should already be ready.',
        stopMsg: 'Stop the managed Nav2 launch process?'
      },
      mapping: {
        title: 'Mapping',
        short: 'Mapping',
        buttonId: 'btnLaunchMapping',
        stateId: 'launchStateMapping',
        startHeading: 'START MAPPING',
        stopHeading: 'STOP MAPPING',
        startMsg: 'Run alias mapping as a managed background launch process? Hardware and odometry should already be ready.',
        stopMsg: 'Stop the managed Mapping launch process? Save the map first if the mapping result is needed.'
      },
      record_path: {
        title: 'Path Recording',
        short: 'Record Path',
        buttonId: 'btnLaunchRecordPath',
        stateId: 'launchStateRecordPath',
        startHeading: 'START PATH RECORDING',
        stopHeading: 'STOP PATH RECORDING',
        startMsg: 'Run alias record_path as a managed background launch process? Hardware and Localization should already be ready.',
        stopMsg: 'Stop the managed Path Recording launch process?'
      }
    };
    window.launchStates = {};
    const navLogStream = document.getElementById('navLogStream');
    const navLogEmpty = document.getElementById('navLogEmpty');
    const navLogLastMessages = new Map();

    function formatNavLogTime(date = new Date()) {
      return [date.getHours(), date.getMinutes(), date.getSeconds()]
        .map(value => String(value).padStart(2, '0'))
        .join(':');
    }

    let isPageLoading = true;
    setTimeout(() => { isPageLoading = false; }, 1500);

    function showToast(source, text, state = 'info') {
      const container = document.getElementById('toastContainer');
      if (!container) return;

      const toast = document.createElement('div');
      toast.className = `toast ${state}`;

      const header = document.createElement('div');
      header.className = 'toast-header';

      const title = document.createElement('span');
      title.className = 'toast-title';
      title.textContent = source;

      const time = document.createElement('span');
      time.className = 'toast-time';
      time.textContent = formatNavLogTime();

      header.appendChild(title);
      header.appendChild(time);

      const body = document.createElement('div');
      body.className = 'toast-body';
      body.textContent = text;

      toast.appendChild(header);
      toast.appendChild(body);
      container.appendChild(toast);

      // Trigger animation
      setTimeout(() => toast.classList.add('show'), 50);

      // Remove after 4 seconds
      setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
      }, 4000);
    }

    function addNavLog(source, text, state = '') {
      if (!navLogStream) return;
      const cleanText = String(text || '').trim();
      if (!cleanText) return;
      const cleanSource = String(source || 'Navigation').trim() || 'Navigation';
      const cleanState = String(state || 'info').trim().toLowerCase() || 'info';
      const key = `${cleanSource}|${cleanState}|${cleanText}`;
      if (navLogLastMessages.get(cleanSource) === key) return;
      navLogLastMessages.set(cleanSource, key);

      const row = document.createElement('div');
      row.className = `nav-log-row ${cleanState}`;
      const time = document.createElement('span');
      time.className = 'nav-log-time';
      time.textContent = formatNavLogTime();
      const label = document.createElement('span');
      label.className = 'nav-log-source';
      label.textContent = cleanSource;
      const message = document.createElement('div');
      message.className = 'nav-log-message';
      message.textContent = cleanText;
      row.append(time, label, message);

      if (navLogEmpty) navLogEmpty.hidden = true;
      navLogStream.append(row);
      while (navLogStream.querySelectorAll('.nav-log-row').length > 80) {
        const first = navLogStream.querySelector('.nav-log-row');
        if (!first) break;
        first.remove();
      }
      navLogStream.scrollTop = navLogStream.scrollHeight;

      // Mirror to compact Navigation Controls log stream
      const navControlsLogStream = document.getElementById('navControlsLogStream');
      const navControlsLogEmpty = document.getElementById('navControlsLogEmpty');
      if (navControlsLogStream) {
        const rowClone = row.cloneNode(true);
        if (navControlsLogEmpty) navControlsLogEmpty.hidden = true;
        navControlsLogStream.append(rowClone);
        while (navControlsLogStream.querySelectorAll('.nav-log-row').length > 40) {
          const first = navControlsLogStream.querySelector('.nav-log-row');
          if (!first) break;
          first.remove();
        }
        navControlsLogStream.scrollTop = navControlsLogStream.scrollHeight;
      }

      if (!isPageLoading) {
        showToast(cleanSource, cleanText, cleanState);
      }
    }

    function setLaunchHint(text, state = '') {
      const el = document.getElementById('launchHint');
      if (!el) return;
      el.textContent = text;
      el.className = 'launch-hint' + (state ? ` ${state}` : '');
      addNavLog('Launch', text, state);
      const sb = document.getElementById('sbMsg');
      if (sb) sb.textContent = text;
    }

    function updateLaunchStatuses(statuses) {
      if (!Array.isArray(statuses)) return;
      statuses.forEach(status => {
        const meta = launchMeta[status.name];
        if (!meta) return;
        window.launchStates[status.name] = status;

        const stateEl = document.getElementById(meta.stateId);
        const btn = document.getElementById(meta.buttonId);
        const label = String(status.status || 'stopped').toUpperCase();
        const running = !!status.running || status.status === 'running' || status.status === 'stopping';
        const mappingActive = !!status.running || status.status === 'running';

        if (stateEl) {
          stateEl.textContent = label;
          stateEl.className = `launch-state ${status.status || 'stopped'}`;
        }
        if (btn) {
          btn.textContent = `${running ? 'Stop' : 'Start'} ${meta.short}`;
          btn.classList.toggle('running', running);
          btn.disabled = status.status === 'stopping' || status.status === 'starting';
          btn.title = status.log_path ? `Log: ${status.log_path}` : '';
          btn.setAttribute('aria-pressed', running ? 'true' : 'false');
          btn.setAttribute(
            'aria-label',
            `${running ? 'Stop' : 'Start'} ${meta.title} launch ${status.name}`
          );
        }
        if (status.name === 'mapping') setMappingSavePanelVisible(mappingActive);
        if (status.name === 'record_path') setPathRecorderPanelVisible(mappingActive);
      });
    }

    function requestLaunchToggle(name) {
      const meta = launchMeta[name];
      if (!meta) return;
      const state = window.launchStates[name] || {};
      const running = !!state.running || state.status === 'running' || state.status === 'stopping';
      const type = running ? 'launch_stop' : 'launch_start';
      const title = running ? 'Confirm Stop' : 'Confirm Launch';
      const heading = running ? meta.stopHeading : meta.startHeading;
      const msg = running ? meta.stopMsg : meta.startMsg;

      confirmAction(title, heading, msg, () => {
        setLaunchHint(`${running ? 'Stopping' : 'Starting'} ${meta.title}...`, '');
        safeSend({ type, name });
      });
    }

    Object.keys(launchMeta).forEach(name => {
      const btn = document.getElementById(launchMeta[name].buttonId);
      if (btn) btn.addEventListener('click', () => requestLaunchToggle(name));
    });

    const btnOpenSaveMap = document.getElementById('btnOpenSaveMap');
    const mappingSavePanel = document.getElementById('mappingSavePanel');
    const btnConfirmSaveMap = document.getElementById('btnConfirmSaveMap');
    const saveMapName = document.getElementById('saveMapName');
    const mappingSaveStatus = document.getElementById('mappingSaveStatus');
    const saveMapModalStatus = document.getElementById('saveMapModalStatus');

    function setMappingSavePanelVisible(visible) {
      if (mappingSavePanel) {
        mappingSavePanel.hidden = !visible;
        mappingSavePanel.setAttribute('aria-hidden', visible ? 'false' : 'true');
      }
      if (btnOpenSaveMap) {
        btnOpenSaveMap.disabled = !visible;
        btnOpenSaveMap.setAttribute('aria-disabled', visible ? 'false' : 'true');
      }
      const saveModal = document.getElementById('modalSaveMap');
      if (!visible && saveModal && saveModal.classList.contains('open')) closeModal('modalSaveMap');
    }
    setMappingSavePanelVisible(false);

    const pathRecorderPanel = document.getElementById('pathRecorderPanel');

    function setPathRecorderPanelVisible(visible) {
      if (pathRecorderPanel) {
        pathRecorderPanel.hidden = !visible;
        pathRecorderPanel.setAttribute('aria-hidden', visible ? 'false' : 'true');
      }
    }
    setPathRecorderPanelVisible(false);

    const pathRecorderStatus = document.getElementById('pathRecorderStatus');

    function setPathRecorderStatus(text, state = '') {
      if (pathRecorderStatus) {
        pathRecorderStatus.textContent = text;
        pathRecorderStatus.className = 'path-recorder-status' + (state ? ` ${state}` : '');
      }
      addNavLog('Path Recorder', text, state);
      const sb = document.getElementById('sbMsg');
      if (sb) sb.textContent = text;
    }

    const btnStartRecording = document.getElementById('btnStartRecording');
    const btnStopRecording = document.getElementById('btnStopRecording');
    const btnNameStation = document.getElementById('btnNameStation');
    const pathStationName = document.getElementById('pathStationName');

    if (btnStartRecording) {
      btnStartRecording.addEventListener('click', async () => {
        setPathRecorderStatus('Memulai perekaman path...', 'busy');
        try {
          const res = await fetch(getApiUrl('/api/path_recorder/start'), { method: 'POST' });
          const payload = await res.json().catch(() => ({}));
          if (!res.ok) throw new Error(payload.detail || 'Gagal memulai perekaman');
          setPathRecorderStatus('Perekaman path dimulai.', 'success');
        } catch (err) {
          setPathRecorderStatus(err.message || 'Gagal memulai perekaman.', 'error');
        }
      });
    }

    if (btnStopRecording) {
      btnStopRecording.addEventListener('click', async () => {
        setPathRecorderStatus('Menghentikan perekaman path...', 'busy');
        try {
          const res = await fetch(getApiUrl('/api/path_recorder/stop'), { method: 'POST' });
          const payload = await res.json().catch(() => ({}));
          if (!res.ok) throw new Error(payload.detail || 'Gagal menghentikan perekaman');
          setPathRecorderStatus('Perekaman path dihentikan dan disimpan.', 'success');
        } catch (err) {
          setPathRecorderStatus(err.message || 'Gagal menghentikan perekaman.', 'error');
        }
      });
    }

    if (btnNameStation) {
      btnNameStation.addEventListener('click', async () => {
        const name = pathStationName ? pathStationName.value.trim() : '';
        if (!name) {
          setPathRecorderStatus('Masukkan nama stasiun terlebih dahulu.', 'error');
          return;
        }
        setPathRecorderStatus(`Menamai stasiun: "${name}"...`, 'busy');
        try {
          const res = await fetch(getApiUrl('/api/path_recorder/name_station'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
          });
          const payload = await res.json().catch(() => ({}));
          if (!res.ok) throw new Error(payload.detail || 'Gagal menyimpan nama stasiun');
          setPathRecorderStatus(`Stasiun "${name}" berhasil dinamai dan disimpan.`, 'success');
          if (pathStationName) pathStationName.value = '';
        } catch (err) {
          setPathRecorderStatus(err.message || 'Gagal menyimpan nama stasiun.', 'error');
        }
      });
    }

    function setMappingSaveStatus(text, state = '') {
      [mappingSaveStatus, saveMapModalStatus].forEach(el => {
        if (!el) return;
        el.textContent = text;
        el.className = 'mapping-save-status' + (state ? ` ${state}` : '');
      });
      addNavLog('Save Map', text, state);
      const sb = document.getElementById('sbMsg');
      if (sb) sb.textContent = text;
    }

    function defaultMapFileStem() {
      const d = new Date();
      const pad = value => String(value).padStart(2, '0');
      return `map_${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}_${pad(d.getHours())}${pad(d.getMinutes())}`;
    }

    if (btnOpenSaveMap) {
      btnOpenSaveMap.addEventListener('click', () => {
        if (saveMapName && !saveMapName.value.trim()) saveMapName.value = defaultMapFileStem();
        setMappingSaveStatus('Siap menyimpan map SLAM Toolbox.', '');
        openModal('modalSaveMap');
        setTimeout(() => saveMapName && saveMapName.focus(), 40);
      });
    }

    if (saveMapName) {
      saveMapName.addEventListener('keydown', event => {
        if (event.key === 'Enter' && btnConfirmSaveMap && !btnConfirmSaveMap.disabled) {
          btnConfirmSaveMap.click();
        }
      });
    }

    if (btnConfirmSaveMap) {
      btnConfirmSaveMap.addEventListener('click', async () => {
        const mapName = saveMapName ? saveMapName.value.trim() : '';
        if (!mapName) {
          setMappingSaveStatus('Isi nama file map dulu.', 'error');
          return;
        }

        btnConfirmSaveMap.disabled = true;
        btnConfirmSaveMap.textContent = 'Saving...';
        setMappingSaveStatus('Memanggil /slam_toolbox/save_map dan /slam_toolbox/serialize_map...', 'busy');

        try {
          const res = await fetch(getApiUrl('/api/mapping/save'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ map_name: mapName })
          });
          const payload = await res.json().catch(() => ({}));
          if (!res.ok) throw new Error(payload.detail || payload.message || 'Gagal menyimpan map.');

          setMappingSaveStatus(payload.message || `Map ${payload.map_name || mapName} tersimpan.`, 'success');
          if (typeof loadAvailableMaps === 'function') loadAvailableMaps();
        } catch (err) {
          setMappingSaveStatus(err && err.message ? err.message : 'Gagal menyimpan map.', 'error');
        } finally {
          btnConfirmSaveMap.disabled = false;
          btnConfirmSaveMap.textContent = 'Save';
        }
      });
    }

    const navGoalFinalStates = new Set(['succeeded', 'aborted', 'canceled', 'failed', 'rejected']);
    const navGoalRunningStates = new Set(['queued', 'sent', 'accepted', 'executing', 'canceling']);
    let lastNavGoalModalKey = '';
    let navGoalStatusSeen = false;

    function navGoalUiState(state) {
      if (state === 'succeeded') return 'success';
      if (navGoalFinalStates.has(state) || String(state || '').startsWith('status_')) return 'error';
      if (navGoalRunningStates.has(state)) return 'running';
      if (state === 'fallback_published' || state === 'unknown') return 'warn';
      return '';
    }

    function setNavGoalStatusUi(status) {
      const st = status || {};
      const rawState = String(st.state || 'idle').toLowerCase();
      const label = rawState.replace(/_/g, ' ').toUpperCase();
      const message = st.message || 'Belum ada goal dari web.';
      const uiState = navGoalUiState(rawState);

      const card = document.getElementById('navGoalStatusCard');
      const title = document.getElementById('navGoalStatusTitle');
      const text = document.getElementById('navGoalStatusText');
      const pill = document.getElementById('navGoalStatusPill');
      if (card) card.className = 'nav-goal-status' + (uiState ? ` ${uiState}` : '');
      if (title) title.textContent = rawState === 'idle' ? 'Nav2 Goal' : `Nav2 Goal #${st.seq || 0}`;
      if (text) text.textContent = message;
      if (pill) pill.textContent = label;
      if (rawState !== 'idle') addNavLog('Nav2 Goal', `${label}: ${message}`, uiState || 'info');

      const sb = document.getElementById('sbMsg');
      if (sb && rawState !== 'idle') sb.textContent = `Nav2: ${message}`;

      // Update Nav Status Bar above Pose & Stations
      const navStatusBar = document.getElementById('navStatusBar');
      const navStatusValue = document.getElementById('navStatusValue');
      if (navStatusBar && navStatusValue) {
        navStatusValue.textContent = label || 'IDLE';
        navStatusBar.className = 'nav-status-bar';
        if (rawState === 'idle') {
          navStatusBar.classList.add('status-idle');
        } else if (uiState === 'success') {
          navStatusBar.classList.add('status-success');
        } else if (uiState === 'error') {
          navStatusBar.classList.add('status-error');
        } else if (uiState === 'running') {
          navStatusBar.classList.add('status-running');
        } else {
          navStatusBar.classList.add('status-idle');
        }
      }
    }

    function showNavGoalResultModal(status, uiState) {
      const st = status || {};
      const state = String(st.state || '').toLowerCase();
      const success = uiState === 'success';
      const panel = document.getElementById('navGoalResultPanel');
      const icon = document.getElementById('navGoalResultIcon');
      const bigIcon = document.getElementById('navGoalResultBigIcon');
      const title = document.getElementById('navGoalResultTitle');
      const heading = document.getElementById('navGoalResultHeading');
      const msg = document.getElementById('navGoalResultMsg');
      const meta = document.getElementById('navGoalResultMeta');

      if (panel) panel.className = `modal-panel ${success ? 'modal-success' : 'modal-error'}`;
      if (icon) icon.textContent = success ? 'OK' : '!';
      if (bigIcon) bigIcon.textContent = success ? 'OK' : '!';
      if (title) title.textContent = success ? 'Nav2 Goal Finished' : 'Nav2 Goal Failed';
      if (heading) heading.textContent = success ? 'GOAL FINISHED' : 'GOAL FAILED';
      if (msg) msg.textContent = st.message || (success ? 'Robot mencapai goal.' : 'Robot gagal mencapai goal.');
      if (meta) {
        const pieces = [`STATE: ${state.toUpperCase() || 'UNKNOWN'}`];
        if (st.seq !== undefined) pieces.push(`SEQ: ${st.seq}`);
        if (st.mode) pieces.push(`MODE: ${String(st.mode).toUpperCase()}`);
        if (st.result_status !== undefined) pieces.push(`RESULT: ${st.result_status}`);
        meta.replaceChildren(...pieces.map(item => {
          const el = document.createElement('span');
          el.textContent = item;
          return el;
        }));
      }
      openModal('modalNavGoalResult');
    }

    function updateNavGoalStatus(status) {
      if (!status) return;
      window.navGoalStatus = status;
      const state = String(status.state || 'idle').toLowerCase();
      const uiState = navGoalUiState(state);
      setNavGoalStatusUi(status);

      const isFinal = uiState === 'success' || uiState === 'error';
      const key = `${status.seq || 0}:${state}`;
      if (!navGoalStatusSeen && isFinal) {
        lastNavGoalModalKey = key;
      } else if (isFinal && key !== lastNavGoalModalKey) {
        lastNavGoalModalKey = key;
        showNavGoalResultModal(status, uiState);
      }
      navGoalStatusSeen = true;
    }

    function getApiUrl(url) {
      const port = window.location.port;
      const isDev = (port && port !== '8000' && port !== '80' && port !== '443') || window.location.protocol === 'file:';
      if (isDev) {
        const host = window.location.hostname || '127.0.0.1';
        return `http://${host}:8000${url}`;
      }
      return url;
    }

    function getWsUrl() {
      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      const port = window.location.port;
      const isDev = (port && port !== '8000' && port !== '80' && port !== '443') || window.location.protocol === 'file:';
      if (isDev) {
        const host = window.location.hostname || '127.0.0.1';
        return `${protocol}://${host}:8000/ws`;
      }
      const host = window.location.host || 'localhost:8000';
      return `${protocol}://${host}/ws`;
    }

    function connectWS() {
      if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;
      updateStatus('CONNECTING...', '');
      try { ws = new WebSocket(getWsUrl()); } catch (e) { scheduleReconnect(); return; }
      ws.onopen = () => {
        clearInterval(reconnectTimer);
        reconnectTimer = null;
        isConnected = true;
        updateStatus('CONNECTED', 'connected');
        safeSend({ type: 'mode', value: window.driveMode || 'auto' });
        safeSend({ type: 'launch_status' });
      };
      ws.onclose = () => { isConnected = false; updateStatus('DISCONNECTED', 'error'); scheduleReconnect(); };
      ws.onerror = () => { try { ws.close(); } catch (e) { } };
      ws.onmessage = (e) => {
        try {
          const m = JSON.parse(e.data);
          if (m.voltage !== undefined) {
            const v = m.voltage || 0;
            document.getElementById('volt').textContent = v.toFixed(1);
            
            // Low battery warning banner logic
            const banner = document.getElementById('lowBatteryBanner');
            const bannerVolt = document.getElementById('lowBatteryVoltage');
            if (banner) {
              if (v > 10.0 && v < 50.0) {
                if (bannerVolt) bannerVolt.textContent = v.toFixed(1);
                banner.style.display = 'flex';
              } else {
                banner.style.display = 'none';
              }
            }
          }
          if (m.temp_driver !== undefined) document.getElementById('temp').textContent = (m.temp_driver || 0).toFixed(1);
          
          if (m.front_laser !== undefined && Array.isArray(m.front_laser)) {
            let hasObstacle = false;
            const thresholds = [35, 80, 90, 80, 35]; // Channel specific thresholds in cm
            for (let i = 0; i < 5; i++) {
              const elVal = document.getElementById(`laserCh${i+1}`);
              const elParent = document.getElementById(`laserParent${i+1}`);
              if (elVal && elParent) {
                const val = m.front_laser[i];
                if (val === null || val === undefined || !isFinite(val) || val >= 700.0) {
                  elVal.textContent = 'OOR';
                  elParent.style.background = 'var(--gn-bg)';
                  elParent.style.borderColor = 'var(--gn)';
                  elVal.style.color = 'var(--gn)';
                } else {
                  const cm = Math.round(val);
                  elVal.textContent = `${cm} cm`;
                  if (val < thresholds[i]) { // Under specific channel threshold
                    hasObstacle = true;
                    elParent.style.background = 'var(--rd-bg)';
                    elParent.style.borderColor = 'var(--rd)';
                    elVal.style.color = 'var(--rd)';
                  } else {
                    elParent.style.background = 'var(--gn-bg)';
                    elParent.style.borderColor = 'var(--gn)';
                    elVal.style.color = 'var(--gn)';
                  }
                }
              }
            }
            const statusBadge = document.getElementById('laserStatusBadge');
            const laserPanel = document.getElementById('p-front-laser');
            if (statusBadge) {
              if (hasObstacle) {
                statusBadge.textContent = 'OBSTACLE DETECTED';
                statusBadge.style.color = 'var(--rd)';
                statusBadge.style.borderColor = 'var(--rd)';
                statusBadge.style.background = 'var(--rd-bg)';
                statusBadge.style.animation = 'sbpulse 1s infinite';
                if (laserPanel) {
                  laserPanel.style.borderTopColor = 'var(--rd)';
                }
              } else {
                statusBadge.textContent = 'SAFE';
                statusBadge.style.color = 'var(--gn)';
                statusBadge.style.borderColor = 'var(--gn)';
                statusBadge.style.background = 'rgba(16, 185, 129, 0.1)';
                statusBadge.style.animation = 'none';
                if (laserPanel) {
                  laserPanel.style.borderTopColor = 'var(--gn)';
                }
              }
            }
          }
          if (m.mag_line !== undefined) {
            const magBadge = document.getElementById('magStatusBadge');
            const magText = document.getElementById('deviationText');
            const magIndicator = document.getElementById('deviationIndicator');
            const magPanel = document.getElementById('p-magnetic-sensor');
            
            if (m.mag_line === null || !Array.isArray(m.mag_line) || m.mag_line.length < 2) {
              // No connection or invalid data
              if (magBadge) {
                magBadge.textContent = 'NO DATA';
                magBadge.style.color = 'var(--t2)';
                magBadge.style.borderColor = 'var(--b0)';
                magBadge.style.background = 'var(--s2)';
              }
              if (magText) {
                magText.textContent = '--';
                magText.style.color = 'var(--t1)';
              }
              if (magIndicator) {
                magIndicator.style.left = '50%';
                magIndicator.style.background = 'var(--s3)';
                magIndicator.style.boxShadow = 'none';
              }
              if (magPanel) magPanel.style.borderTopColor = 'var(--b0)';
              // Clear bits
              for (let b = 0; b < 16; b++) {
                const elBit = document.getElementById(`magBit${b}`);
                if (elBit) {
                  elBit.style.background = 'var(--s3)';
                  elBit.style.borderColor = 'var(--b0)';
                  elBit.style.boxShadow = 'none';
                }
              }
            } else {
              const bitmap = parseInt(m.mag_line[0]) || 0;
              const deviation = parseFloat(m.mag_line[1]) || 0.0;
              
              let activeBitsCount = 0;
              for (let b = 0; b < 16; b++) {
                const isActive = (bitmap & (1 << b)) !== 0;
                const elBit = document.getElementById(`magBit${b}`);
                if (elBit) {
                  if (isActive) {
                    activeBitsCount++;
                    elBit.style.background = 'var(--cy)';
                    elBit.style.borderColor = 'var(--cy)';
                    elBit.style.boxShadow = '0 0 6px var(--cy)';
                  } else {
                    elBit.style.background = 'var(--s3)';
                    elBit.style.borderColor = 'var(--b0)';
                    elBit.style.boxShadow = 'none';
                  }
                }
              }
              
              if (bitmap === 0 || activeBitsCount < 3) {
                // Tape dropout
                if (magBadge) {
                  magBadge.textContent = 'OUT OF LINE';
                  magBadge.style.color = 'var(--rd)';
                  magBadge.style.borderColor = 'var(--rd)';
                  magBadge.style.background = 'var(--rd-bg)';
                }
                if (magText) {
                  magText.textContent = 'DROPOUT';
                  magText.style.color = 'var(--rd)';
                }
                if (magIndicator) {
                  magIndicator.style.left = '50%';
                  magIndicator.style.background = 'var(--s3)';
                  magIndicator.style.boxShadow = 'none';
                }
                if (magPanel) magPanel.style.borderTopColor = 'var(--rd)';
              } else {
                // Tracking tape
                if (magBadge) {
                  if (activeBitsCount >= 8) {
                    magBadge.textContent = 'CHECKPOINT';
                    magBadge.style.color = 'var(--yw)';
                    magBadge.style.borderColor = 'var(--yw)';
                    magBadge.style.background = 'rgba(245, 158, 11, 0.1)';
                    if (magPanel) magPanel.style.borderTopColor = 'var(--yw)';
                  } else {
                    magBadge.textContent = 'IN LINE';
                    magBadge.style.color = 'var(--gn)';
                    magBadge.style.borderColor = 'var(--gn)';
                    magBadge.style.background = 'rgba(16, 185, 129, 0.1)';
                    if (magPanel) magPanel.style.borderTopColor = 'var(--cy)';
                  }
                }
                
                if (magText) {
                  const absDev = Math.abs(deviation);
                  magText.style.color = 'var(--t1)';
                  if (absDev <= 3) {
                    magText.textContent = '0 mm';
                  } else {
                    magText.textContent = (deviation > 0 ? '+' : '') + Math.round(deviation) + ' mm';
                  }
                }
                
                if (magIndicator) {
                  // Map deviation -100 to +100 to percent 0% to 100%
                  let percent = 50 + (deviation / 2.0); // dev = -100 -> percent = 0; dev = 100 -> percent = 100
                  percent = Math.max(0, Math.min(100, percent));
                  magIndicator.style.left = percent + '%';
                  magIndicator.style.background = 'var(--cy)';
                  magIndicator.style.boxShadow = '0 0 8px var(--cy)';
                }
              }
            }
          }
          if (m.current_left !== undefined) document.getElementById('curL').textContent = (m.current_left || 0).toFixed(1);
          if (m.current_right !== undefined) document.getElementById('curR').textContent = (m.current_right || 0).toFixed(1);
          if (m.rpm_left !== undefined) document.getElementById('rpmL').textContent = (m.rpm_left || 0).toFixed(1);
          if (m.rpm_right !== undefined) document.getElementById('rpmR').textContent = (m.rpm_right || 0).toFixed(1);
          if (m.x !== undefined) document.getElementById('xPos').textContent = (m.x || 0).toFixed(2);
          if (m.y !== undefined) document.getElementById('yPos').textContent = (m.y || 0).toFixed(2);
          window.data.x = (m.x !== undefined) ? m.x : window.data.x;
          window.data.y = (m.y !== undefined) ? m.y : window.data.y;
          window.data.theta = (m.theta !== undefined) ? m.theta : window.data.theta;
          if (m.amcl_x !== undefined && m.amcl_x !== null) window.amclData.x = m.amcl_x;
          if (m.amcl_y !== undefined && m.amcl_y !== null) window.amclData.y = m.amcl_y;
          if (m.amcl_theta !== undefined && m.amcl_theta !== null) window.amclData.theta = m.amcl_theta;
          if ((m.amcl_x !== undefined && m.amcl_x !== null) || (m.amcl_y !== undefined && m.amcl_y !== null) || (m.amcl_theta !== undefined && m.amcl_theta !== null)) {
            window.amclData.available = true;
            if (typeof window.requestNavDraw === 'function') window.requestNavDraw();
          }
          if (m.theta !== undefined) refreshHeadingDisplay();
          queueCanvasDraw();
          if (m.io_inputs !== undefined) refreshDiByte(m.io_inputs & 0xFF);
          if (m.io_outputs !== undefined) refreshDoByte(m.io_outputs & 0xFF);
          if (m.lidar_motor !== undefined && typeof window.setLidarMotorUi === 'function') window.setLidarMotorUi(!!m.lidar_motor);
          if (m.drive_mode !== undefined && typeof window.setDriveModeUi === 'function') window.setDriveModeUi(m.drive_mode);
          if (m.di_byte !== undefined) refreshDiByte(m.di_byte & 0xFF);
          if (m.do_byte !== undefined) refreshDoByte(m.do_byte & 0xFF);
          if (Array.isArray(m.launches)) updateLaunchStatuses(m.launches);
          if (m.type === 'launch_result') {
            setLaunchHint(m.message || (m.ok ? 'Launch command completed.' : 'Launch command failed.'), m.ok ? 'success' : 'error');
          }
          if (m.nav_goal_status) updateNavGoalStatus(m.nav_goal_status);
          if (m.mission_status && typeof window.updateMissionStatusUi === 'function') window.updateMissionStatusUi(m.mission_status);
          if (m.type === 'mission_queue_ack' && typeof window.updateMissionAckUi === 'function') window.updateMissionAckUi(m);
          if (m.type === 'goal_pose_ack' || m.type === 'initial_pose_ack') {
            const sb = document.getElementById('sbMsg');
            if (sb) sb.textContent = m.message || (m.type === 'goal_pose_ack' ? 'Goal pose sent.' : 'Initial pose sent.');
          }

           if (m.type === 'nav_map' && m.data && typeof window.onNavMap === 'function') window.onNavMap(m.data);
          if (m.type === 'nav_local_costmap' && m.data && typeof window.onNavLocalCostmap === 'function') window.onNavLocalCostmap(m.data);
          if (m.type === 'nav_global_costmap' && m.data && typeof window.onNavGlobalCostmap === 'function') window.onNavGlobalCostmap(m.data);
          if (m.type === 'nav_path' && m.data && typeof window.onNavPath === 'function') window.onNavPath(m.data);
          if (m.type === 'recorded_path' && m.data && typeof window.onRecordedPath === 'function') window.onRecordedPath(m.data);
          if (m.type === 'nav_lidar_scan' && m.data && typeof window.onNavLidarScan === 'function') window.onNavLidarScan(m.data);
        } catch (err) { console.warn('WS parse err', err); }
      };
    }
    function scheduleReconnect() { if (reconnectTimer) return; reconnectTimer = setInterval(() => { if (!isConnected) connectWS(); }, 2000); }
    function safeSend(obj) { if (ws && ws.readyState === WebSocket.OPEN) { try { ws.send(JSON.stringify(obj)); } catch (e) { } } }
    function sendCmd(vx, wz) {
      if ((window.driveMode || 'auto') !== 'manual') return;
      safeSend({ type: 'cmd_vel', linear: vx, angular: wz });
    }

    window.data = { x: 0, y: 0, theta: 0 };
    window.amclData = { x: 0, y: 0, theta: 0, available: false };
    window.driveMode = 'auto';
    let headingUnit = localStorage.getItem('aryaHeadingUnit') === 'deg' ? 'deg' : 'rad';

    function formatHeading(thetaRad) { const theta = Number(thetaRad) || 0; return headingUnit === 'deg' ? (theta * 180 / Math.PI).toFixed(3) : theta.toFixed(3); }
    function refreshHeadingDisplay() {
      const hEl = document.getElementById('heading'), uEl = document.getElementById('headingUnit');
      if (hEl) hEl.textContent = formatHeading(window.data.theta);
      if (uEl) uEl.textContent = headingUnit === 'deg' ? 'degrees' : 'radians';
      document.querySelectorAll('.angle-btn').forEach(b => b.classList.toggle('active', b.dataset.angleUnit === headingUnit));
    }

    connectWS();

    // ============================================================
    //  DRIVE CONTROL
    // ============================================================
    document.addEventListener('DOMContentLoaded', () => {
      const speedSpan = document.getElementById('speed');
      const speedValue = document.getElementById('speedValue');
      const linearBar = document.getElementById('linearBar');
      const angularBar = document.getElementById('angularBar');
      const modeBtn = document.getElementById('modeBtn');
      const speedSlider = document.getElementById('speedSlider');
      const qBtn = document.getElementById('Q');
      const zBtn = document.getElementById('Z');
      const speedIndicator = document.getElementById('speedIndicator');
      const canvas = document.getElementById('odomCanvas');
      const ctx = canvas.getContext('2d');

      document.body.tabIndex = -1; try { document.body.focus(); } catch (e) { }

      let MAX_V = parseFloat(speedSlider.value) || 0.5, MAX_W = 1.2;
      let v = 0.3, w = 0.5;
      let v_target = 0, w_target = 0, v_current = 0, w_current = 0;
      let pressed = new Set(), path = [];
      let zoom = 50;
      let offX = 0, offY = 0;
      let odomPanPointerId = null;
      let odomPanLast = null;
      let mode = window.driveMode || 'auto';
      let lidarMotorOn = true;

      function resizeCanvasToPanel() {
        const rect = canvas.getBoundingClientRect();
        const nextW = Math.max(320, Math.round(rect.width || canvas.parentElement.clientWidth || 700));
        const nextH = Math.max(240, Math.round(rect.height || nextW * 0.48));
        if (canvas.width === nextW && canvas.height === nextH) return false;
        const oldW = canvas.width || nextW;
        const oldH = canvas.height || nextH;
        const hasExistingView = Number.isFinite(offX) && Number.isFinite(offY) && (offX !== 0 || offY !== 0);
        const centerWorld = hasExistingView ? screenToOdomWorld({ x: oldW / 2, y: oldH / 2 }) : { x: 0, y: 0 };
        canvas.width = nextW;
        canvas.height = nextH;
        offX = nextW / 2 - centerWorld.x * zoom;
        offY = nextH / 2 + centerWorld.y * zoom;
        return true;
      }

      function redrawCanvas() {
        resizeCanvasToPanel();
        window.drawFixedAxesAndRobot(window.data.x, window.data.y, window.data.theta);
      }

      document.querySelectorAll('.angle-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          headingUnit = btn.dataset.angleUnit === 'deg' ? 'deg' : 'rad';
          localStorage.setItem('aryaHeadingUnit', headingUnit);
          refreshHeadingDisplay();
        });
      });
      refreshHeadingDisplay();

      window.setLidarMotorUi = function (on) {
        lidarMotorOn = !!on;
        const btn1 = document.getElementById('lidarMotorToggle');
        const btn2 = document.getElementById('tbLidar');
        if (btn1) btn1.textContent = lidarMotorOn ? 'Stop Lidar' : 'Start Lidar';
        if (btn2) btn2.textContent = lidarMotorOn ? 'Stop Lidar' : 'Start Lidar';
      };

      function showSpeedChange(up) {
        speedIndicator.textContent = up ? '▲ SPEED UP' : '▼ SPEED DOWN';
        speedIndicator.classList.add('show');
        setTimeout(() => speedIndicator.classList.remove('show'), 900);
      }

      // Reset with confirmation modal
      function hookReset(btnId, title, heading, msg, action) {
        const el = document.getElementById(btnId);
        if (el) el.onclick = () => confirmAction(title, heading, msg, action);
      }
      hookReset('resetOdom', 'Confirm Reset', 'RESET ODOMETRY', 'This will zero X, Y and heading. Continue?', () => safeSend({ type: 'reset_odom' }));
      hookReset('resetEnc', 'Confirm Reset', 'RESET ENCODER', 'This will zero encoder counts. Continue?', () => safeSend({ type: 'reset_encoder' }));
      hookReset('tbResetOdom', 'Confirm Reset', 'RESET ODOMETRY', 'This will zero X, Y and heading. Continue?', () => safeSend({ type: 'reset_odom' }));
      hookReset('tbResetEnc', 'Confirm Reset', 'RESET ENCODER', 'This will zero encoder counts. Continue?', () => safeSend({ type: 'reset_encoder' }));

      const lidarToggle = () => { const next = !lidarMotorOn; window.setLidarMotorUi(next); safeSend({ type: 'lidar_motor', enabled: next }); };
      document.getElementById('lidarMotorToggle').onclick = lidarToggle;
      const tbLidar = document.getElementById('tbLidar');
      if (tbLidar) tbLidar.onclick = lidarToggle;

      function setDriveMode(nextMode, notifyServer = true) {
        mode = nextMode === 'manual' ? 'manual' : 'auto';
        window.driveMode = mode;
        if (mode === 'auto') {
          pressed.clear();
          v_target = 0;
          w_target = 0;
          v_current = 0;
          w_current = 0;
        }
        modeBtn.textContent = mode === 'manual' ? 'MANUAL MODE' : 'AUTO MODE';
        modeBtn.classList.toggle('active', mode === 'manual');
        if (notifyServer) safeSend({ type: 'mode', value: mode });
        document.getElementById('sbDriveText').textContent = mode.toUpperCase();
        document.getElementById('sbDriveDot').className = 'sb-dot' + (mode === 'auto' ? ' ok' : ' warn');
      }

      window.setDriveModeUi = (nextMode) => setDriveMode(nextMode, false);
      setDriveMode(mode, false);

      modeBtn.onclick = () => {
        setDriveMode(mode === 'manual' ? 'auto' : 'manual', true);
      };

      speedSlider.addEventListener('input', () => { MAX_V = parseFloat(speedSlider.value) || 0.5; speedValue.textContent = MAX_V.toFixed(2); });

      function getCmd(key) {
        key = ('' + key).toLowerCase();
        switch (key) {
          case 'i': return [v, 0]; case ',': return [-v, 0];
          case 'j': return [0, w]; case 'l': return [0, -w];
          case 'u': return [v, w]; case 'o': return [v, -w];
          case 'm': return [-v, -w]; case '.': return [-v, w];
          case 'k': return [0, 0]; default: return null;
        }
      }

      document.querySelectorAll('.btn').forEach(btn => {
        const id = btn.id; if (id === 'Q' || id === 'Z') return;
        const key = btn.dataset.key || id;
        btn.addEventListener('mousedown', () => { if (mode !== 'manual') return; const c = getCmd(key); if (c) { v_target = c[0]; w_target = c[1]; } });
        btn.addEventListener('mouseup', () => { v_target = 0; w_target = 0; });
        btn.addEventListener('mouseleave', () => { v_target = 0; w_target = 0; });
        btn.addEventListener('touchstart', (e) => { e.preventDefault(); if (mode !== 'manual') return; const c = getCmd(key); if (c) { v_target = c[0]; w_target = c[1]; } }, { passive: false });
        btn.addEventListener('touchend', () => { v_target = 0; w_target = 0; });
      });

      function increaseSpeed() { v = Math.min(v + 0.05, MAX_V); speedSpan.textContent = v.toFixed(2); showSpeedChange(true); }
      function decreaseSpeed() { v = Math.max(v - 0.05, 0.05); speedSpan.textContent = v.toFixed(2); showSpeedChange(false); }
      if (qBtn) qBtn.addEventListener('click', increaseSpeed);
      if (zBtn) zBtn.addEventListener('click', decreaseSpeed);

      document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') return;
        const k = ('' + e.key).toLowerCase();
        if (k === 'q') { increaseSpeed(); return; }
        if (k === 'z') { decreaseSpeed(); return; }
        if (pressed.has(k)) return;
        const c = getCmd(k);
        if (c && mode === 'manual') { pressed.add(k); v_target = c[0]; w_target = c[1]; }
      });
      document.addEventListener('keyup', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') return;
        const k = ('' + e.key).toLowerCase();
        if (pressed.has(k)) { pressed.delete(k); v_target = 0; w_target = 0; }
      });
      window.addEventListener('click', (e) => {
        if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'SELECT' && e.target.tagName !== 'TEXTAREA') {
          try { document.body.focus(); } catch (err) { }
        }
      });

      setInterval(() => {
        const accel = 0.05, aa = 0.1;
        if (mode === 'manual') {
          if (Math.abs(v_target - v_current) > accel) v_current += accel * Math.sign(v_target - v_current); else v_current = v_target;
          if (Math.abs(w_target - w_current) > aa) w_current += aa * Math.sign(w_target - w_current); else w_current = w_target;
          sendCmd(v_current, w_current);
        } else {
          v_target = 0;
          w_target = 0;
          v_current = 0;
          w_current = 0;
        }
        if (linearBar) linearBar.style.width = Math.min(100, Math.abs(v_current / (MAX_V || 0.0001)) * 100) + '%';
        if (angularBar) angularBar.style.width = Math.min(100, Math.abs(w_current / (MAX_W || 0.0001)) * 100) + '%';
        const lv = document.getElementById('linVal'); if (lv) lv.textContent = v_current.toFixed(2);
        const av = document.getElementById('angVal'); if (av) av.textContent = w_current.toFixed(2);
        // update status bar
        if (mode === 'auto') {
          document.getElementById('sbDriveText').textContent = 'AUTO';
          document.getElementById('sbDriveDot').className = 'sb-dot ok';
        } else if (Math.abs(v_current) > 0.01 || Math.abs(w_current) > 0.01) {
          document.getElementById('sbDriveText').textContent = `v:${v_current.toFixed(1)} w:${w_current.toFixed(1)}`;
          document.getElementById('sbDriveDot').className = 'sb-dot ok';
        } else {
          document.getElementById('sbDriveText').textContent = 'IDLE';
          document.getElementById('sbDriveDot').className = 'sb-dot warn';
        }
      }, 100);

      // ---- CANVAS ----
      function odomCanvasPointFromEvent(e) {
        const rect = canvas.getBoundingClientRect();
        const sx = canvas.width / Math.max(1, rect.width);
        const sy = canvas.height / Math.max(1, rect.height);
        return {
          x: (e.clientX - rect.left) * sx,
          y: (e.clientY - rect.top) * sy
        };
      }

      function screenToOdomWorld(pt) {
        return {
          x: (pt.x - offX) / zoom,
          y: -(pt.y - offY) / zoom
        };
      }

      function odomWorldToScreen(x, y) {
        return {
          x: offX + x * zoom,
          y: offY - y * zoom
        };
      }

      function clamp(value, min, max) {
        return Math.min(max, Math.max(min, value));
      }

      function odomGridStepMeters() {
        const candidates = [1, 5, 10];
        return candidates.find(step => zoom * step >= 34) || 10;
      }

      function isGridMultiple(value, interval) {
        const ratio = value / interval;
        return Math.abs(ratio - Math.round(ratio)) < 0.000001;
      }

      function formatGridNumber(value) {
        const rounded = Math.round(value);
        return Math.abs(value - rounded) < 0.000001 ? String(rounded) : value.toFixed(1);
      }

      function updateOdomGridScale(stepMeters) {
        const chip = document.getElementById('odomGridScale');
        if (chip) chip.textContent = `GRID ${stepMeters} m`;
      }

      function zoomOdomAtPoint(factor, pivot = { x: canvas.width / 2, y: canvas.height / 2 }) {
        const worldBefore = screenToOdomWorld(pivot);
        zoom = Math.min(220, Math.max(0.5, zoom * factor));
        offX = pivot.x - worldBefore.x * zoom;
        offY = pivot.y + worldBefore.y * zoom;
        window.drawFixedAxesAndRobot(window.data.x, window.data.y, window.data.theta);
      }

      function drawBg() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#F8FAFC';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        const stepMeters = odomGridStepMeters();
        updateOdomGridScale(stepMeters);
        const left = (0 - offX) / zoom;
        const right = (canvas.width - offX) / zoom;
        const top = (offY - 0) / zoom;
        const bottom = (offY - canvas.height) / zoom;
        const xStart = Math.floor(left / stepMeters) * stepMeters;
        const xEnd = Math.ceil(right / stepMeters) * stepMeters;
        const yStart = Math.floor(bottom / stepMeters) * stepMeters;
        const yEnd = Math.ceil(top / stepMeters) * stepMeters;
        const axisLabelX = clamp(offX + 7, 8, canvas.width - 66);
        const axisLabelY = clamp(offY + 14, 16, canvas.height - 8);

        ctx.font = "9px 'IBM Plex Mono',monospace";
        ctx.textBaseline = 'alphabetic';

        for (let x = xStart; x <= xEnd + 0.000001; x += stepMeters) {
          const px = odomWorldToScreen(x, 0).x;
          const major = isGridMultiple(x, 10);
          const mid = isGridMultiple(x, 5);
          ctx.strokeStyle = major ? '#AAB7C4' : mid ? '#C7D2DE' : '#DDE5EE';
          ctx.lineWidth = major ? 1.4 : 1;
          ctx.beginPath();
          ctx.moveTo(Math.round(px) + 0.5, 0);
          ctx.lineTo(Math.round(px) + 0.5, canvas.height);
          ctx.stroke();
          if (Math.abs(x) > 0.000001) {
            const label = `${formatGridNumber(x)}m`;
            ctx.fillStyle = '#405261';
            ctx.fillText(label, px - label.length * 3, axisLabelY);
          }
        }

        for (let y = yStart; y <= yEnd + 0.000001; y += stepMeters) {
          const py = odomWorldToScreen(0, y).y;
          const major = isGridMultiple(y, 10);
          const mid = isGridMultiple(y, 5);
          ctx.strokeStyle = major ? '#AAB7C4' : mid ? '#C7D2DE' : '#DDE5EE';
          ctx.lineWidth = major ? 1.4 : 1;
          ctx.beginPath();
          ctx.moveTo(0, Math.round(py) + 0.5);
          ctx.lineTo(canvas.width, Math.round(py) + 0.5);
          ctx.stroke();
          if (Math.abs(y) > 0.000001) {
            const label = `${formatGridNumber(y)}m`;
            ctx.fillStyle = '#405261';
            ctx.fillText(label, axisLabelX, py + 3);
          }
        }

        ctx.strokeStyle = '#738497';
        ctx.lineWidth = 2;
        if (offX >= -1 && offX <= canvas.width + 1) {
          ctx.beginPath();
          ctx.moveTo(Math.round(offX) + 0.5, 0);
          ctx.lineTo(Math.round(offX) + 0.5, canvas.height);
          ctx.stroke();
        }
        if (offY >= -1 && offY <= canvas.height + 1) {
          ctx.beginPath();
          ctx.moveTo(0, Math.round(offY) + 0.5);
          ctx.lineTo(canvas.width, Math.round(offY) + 0.5);
          ctx.stroke();
        }

        ctx.fillStyle = '#2B3A46';
        ctx.font = "10px 'IBM Plex Mono',monospace";
        ctx.fillText('Y (m)', clamp(offX + 7, 8, canvas.width - 52), 14);
        ctx.fillText('X (m)', canvas.width - 48, clamp(offY - 7, 14, canvas.height - 8));

        if (offX >= 0 && offX <= canvas.width && offY >= 0 && offY <= canvas.height) {
          ctx.fillStyle = '#0A6ED1';
          ctx.beginPath();
          ctx.arc(offX, offY, 3, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      function appendPathPoint(xm, ym) {
        const last = path[path.length - 1];
        if (!last || Math.hypot(last.x - xm, last.y - ym) >= 0.02) {
          path.push({ x: xm, y: ym });
          if (path.length > 700) path.shift();
        }
      }

      function drawTrajectoryPath() {
        if (path.length < 2) return;
        ctx.lineWidth = 2;
        ctx.strokeStyle = 'rgba(10,110,209,0.35)';
        ctx.beginPath();
        path.forEach((p, i) => {
          const screen = odomWorldToScreen(p.x, p.y);
          if (i === 0) ctx.moveTo(screen.x, screen.y);
          else ctx.lineTo(screen.x, screen.y);
        });
        ctx.stroke();
      }

      function drawRobot(xm, ym, theta) {
        appendPathPoint(xm, ym);
        drawTrajectoryPath();
        const robot = odomWorldToScreen(xm, ym);
        const cx = robot.x, cy = robot.y;
        const s = 13, c = Math.cos(theta), si = Math.sin(theta);
        function rot(pt) { return { x: cx + (pt.x * c - pt.y * si), y: cy - (pt.x * si + pt.y * c) }; }
        const r1 = rot({ x: s, y: 0 }), r2 = rot({ x: -s * .6, y: s * .6 }), r3 = rot({ x: -s * .6, y: -s * .6 });
        // Robot body
        ctx.fillStyle = '#405261';
        ctx.beginPath(); ctx.moveTo(r1.x, r1.y); ctx.lineTo(r2.x, r2.y); ctx.lineTo(r3.x, r3.y); ctx.closePath(); ctx.fill();
        ctx.strokeStyle = '#0A6ED1'; ctx.lineWidth = 1.5; ctx.stroke();
        // Heading arrow
        const hx = cx + (s + 9) * c, hy = cy - (s + 9) * si;
        ctx.strokeStyle = '#D95F02'; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(hx, hy); ctx.stroke();
        // Center
        ctx.fillStyle = '#FFFFFF'; ctx.beginPath(); ctx.arc(cx, cy, 2.5, 0, Math.PI * 2); ctx.fill();
        // Heading label
        let deg = theta * 180 / Math.PI; deg = ((deg + 180) % 360) - 180;
        ctx.font = "9px 'IBM Plex Mono',monospace"; ctx.fillStyle = '#5E6B78';
        ctx.fillText(deg.toFixed(1) + ' deg', cx + 18 * c - 12 * si, cy - (18 * si + 12 * c));
      }

      window.drawFixedAxesAndRobot = function (xm, ym, theta) {
        resizeCanvasToPanel();
        drawBg(); drawRobot(xm || 0, ym || 0, (typeof theta === 'number') ? theta : 0);
      };

      document.getElementById('zoomIn').addEventListener('click', () => zoomOdomAtPoint(1.25));
      document.getElementById('zoomOut').addEventListener('click', () => zoomOdomAtPoint(1 / 1.25));
      document.getElementById('resetView').addEventListener('click', () => { resizeCanvasToPanel(); zoom = 50; offX = canvas.width / 2; offY = canvas.height / 2; path = []; window.drawFixedAxesAndRobot(window.data.x, window.data.y, window.data.theta); });

      canvas.addEventListener('pointerdown', e => {
        e.preventDefault();
        odomPanPointerId = e.pointerId;
        odomPanLast = odomCanvasPointFromEvent(e);
        canvas.classList.add('panning');
        try { canvas.setPointerCapture(e.pointerId); } catch (err) { }
      });

      canvas.addEventListener('pointermove', e => {
        if (e.pointerId !== odomPanPointerId || !odomPanLast) return;
        e.preventDefault();
        const pt = odomCanvasPointFromEvent(e);
        offX += pt.x - odomPanLast.x;
        offY += pt.y - odomPanLast.y;
        odomPanLast = pt;
        window.drawFixedAxesAndRobot(window.data.x, window.data.y, window.data.theta);
      });

      function endOdomPan(e) {
        if (e.pointerId !== odomPanPointerId) return;
        odomPanPointerId = null;
        odomPanLast = null;
        canvas.classList.remove('panning');
        try { canvas.releasePointerCapture(e.pointerId); } catch (err) { }
      }

      canvas.addEventListener('pointerup', endOdomPan);
      canvas.addEventListener('pointercancel', endOdomPan);
      canvas.addEventListener('wheel', e => {
        e.preventDefault();
        zoomOdomAtPoint(e.deltaY < 0 ? 1.1 : 0.9, odomCanvasPointFromEvent(e));
      }, { passive: false });

      if ('ResizeObserver' in window) {
        new ResizeObserver(() => requestAnimationFrame(redrawCanvas)).observe(canvas.parentElement);
      } else {
        window.addEventListener('resize', redrawCanvas);
      }
      resizeCanvasToPanel();
      window.drawFixedAxesAndRobot(0, 0, 0);
      speedSpan.textContent = v.toFixed(2);
      speedValue.textContent = MAX_V.toFixed(2);
    });

    // ============================================================
    //  NAVIGATION VIEW LOGIC
    // ============================================================
    document.addEventListener('DOMContentLoaded', () => {
      const navCanvas = document.getElementById('navCanvas');
      if (!navCanvas) return;
      const nctx = navCanvas.getContext('2d');

      let navZoom = 40.0;
      let navOffX = navCanvas.width / 2;
      let navOffY = navCanvas.height / 2;
      let isDragging = false, lastX, lastY, panPointerId = null;
      let mapClickMode = null;
      let poseDraft = null;
      let posePointer = null;
      let navEditorMode = null;
      let zonePointer = null;
      let zoneDraft = null;
      let zoneClicks = [];
      let stationPointer = null;
      const POSE_DRAG_THRESHOLD_PX = 8;

      // Multi-touch pinch-to-zoom tracking
      let navActivePointers = [];
      let initialPinchDistance = null;
      let initialPinchZoom = null;
      let initialPinchCenterWorld = null;

      let mapData = null, localCostmap = null, globalCostmap = null, navPath = null, lidarScan = null, recordedPathData = [];
      let mapBitmap = null, localBitmap = null, globalBitmap = null;
      let activeMapName = '';
      let keepoutZones = [];
      let stations = [];
      let missionQueue = [];
      let missionMode = 'single';
      let editingStationId = null;

      const cMap = document.getElementById('navShowMap');
      const cRobot = document.getElementById('navShowRobot');
      const cFootprint = document.getElementById('navShowFootprint');
      const cLocal = document.getElementById('navShowLocalCostmap');
      const cGlobal = document.getElementById('navShowGlobalCostmap');
      const cPath = document.getElementById('navShowPath');
      const cLidar = document.getElementById('navShowLidar');
      const btnAutoCenter = document.getElementById('navAutoCenter');
      const annotationStatus = document.getElementById('annotationStatus');
      const keepoutZoneList = document.getElementById('keepoutZoneList');
      const stationList = document.getElementById('stationList');
      const missionStatus = document.getElementById('missionStatus');
      const missionQueueList = document.getElementById('missionQueueList');

      let navFollowRobot = true;
      let navDrawQueued = false;

      function getNavPose() {
        const src = window.amclData && window.amclData.available ? window.amclData : window.data;
        return {
          x: Number(src && src.x) || 0,
          y: Number(src && src.y) || 0,
          theta: Number(src && src.theta) || 0
        };
      }

      function centerViewOnRobot(pose = getNavPose()) {
        navOffX = navCanvas.width / 2 - pose.x * navZoom;
        navOffY = navCanvas.height / 2 + pose.y * navZoom;
      }

      function updateAutoCenterUi() {
        if (!btnAutoCenter) return;
        btnAutoCenter.classList.toggle('active', navFollowRobot);
        btnAutoCenter.textContent = navFollowRobot ? 'AUTO CENTER' : 'CENTER ROBOT';
        btnAutoCenter.title = navFollowRobot
          ? 'Robot tetap di tengah map. Drag map untuk mematikan sementara.'
          : 'Klik untuk center ke robot dan aktifkan auto center.';
      }

      function setNavFollowRobot(enabled, redraw = true) {
        navFollowRobot = !!enabled;
        updateAutoCenterUi();
        if (navFollowRobot) centerViewOnRobot();
        if (redraw) requestNavRedraw();
      }

      function resizeNavCanvasToPanel() {
        const rect = navCanvas.getBoundingClientRect();
        const nextW = Math.max(320, Math.round(rect.width || navCanvas.parentElement.clientWidth || 800));
        const nextH = Math.max(260, Math.round(rect.height || navCanvas.parentElement.clientHeight || 400));
        if (navCanvas.width === nextW && navCanvas.height === nextH) return false;

        const oldW = navCanvas.width || nextW;
        const oldH = navCanvas.height || nextH;
        const worldCenter = screenToWorld({ x: oldW / 2, y: oldH / 2 });
        navCanvas.width = nextW;
        navCanvas.height = nextH;

        if (navFollowRobot) {
          centerViewOnRobot();
        } else {
          navOffX = nextW / 2 - worldCenter.x * navZoom;
          navOffY = nextH / 2 + worldCenter.y * navZoom;
        }
        return true;
      }

      function requestNavRedraw() {
        if (navDrawQueued) return;
        navDrawQueued = true;
        requestAnimationFrame(() => {
          navDrawQueued = false;
          drawNav();
        });
      }

      function zoomNav(factor) {
        const center = { x: navCanvas.width / 2, y: navCanvas.height / 2 };
        const worldBefore = screenToWorld(center);
        navZoom = Math.min(220, Math.max(2, navZoom * factor));
        if (navFollowRobot) {
          centerViewOnRobot();
        } else {
          navOffX = center.x - worldBefore.x * navZoom;
          navOffY = center.y + worldBefore.y * navZoom;
        }
        requestNavRedraw();
      }

      updateAutoCenterUi();

      function drawNav() {
        resizeNavCanvasToPanel();
        if (navFollowRobot) centerViewOnRobot();

        const w = navCanvas.width, h = navCanvas.height;
        nctx.clearRect(0, 0, w, h);
        nctx.fillStyle = '#F8FAFC';
        nctx.fillRect(0, 0, w, h);

        nctx.save();
        nctx.translate(navOffX, navOffY);
        nctx.scale(navZoom, navZoom);

        const navPose = getNavPose();

        const drawGrid = (bitmap, data) => {
          if (!bitmap || !data) return;
          if (data.transform_ok === false && data.frame_id !== 'map') return;
          nctx.save();
          nctx.translate(Number(data.ox) || 0, -(Number(data.oy) || 0));
          nctx.rotate(-(Number(data.oyaw) || 0));
          nctx.scale(1, -1);
          const mw = data.w * data.res;
          const mh = data.h * data.res;
          nctx.drawImage(bitmap, 0, 0, mw, mh);
          nctx.restore();
        };

        const drawPoseMarker = (pose) => {
          if (!pose) return;
          nctx.save();
          nctx.translate(pose.x, -pose.y);
          nctx.rotate(-pose.theta);
          nctx.lineWidth = 0.035;
          nctx.strokeStyle = pose.mode === 'initial' ? '#0A6ED1' : '#D95F02';
          nctx.fillStyle = pose.mode === 'initial' ? 'rgba(10,110,209,.18)' : 'rgba(217,95,2,.18)';
          nctx.beginPath();
          nctx.arc(0, 0, 0.16, 0, Math.PI * 2);
          nctx.fill();
          nctx.stroke();
          nctx.beginPath();
          nctx.moveTo(0, 0);
          nctx.lineTo(0.48, 0);
          nctx.stroke();
          nctx.beginPath();
          nctx.moveTo(0.48, 0);
          nctx.lineTo(0.32, 0.12);
          nctx.lineTo(0.32, -0.12);
          nctx.closePath();
          nctx.fill();
          nctx.stroke();
          nctx.restore();
        };

        const drawLidarScan = (scan) => {
          if (!scan || !Array.isArray(scan.points) || !scan.points.length) return;
          nctx.save();
          nctx.translate(navPose.x, -navPose.y);
          nctx.rotate(-navPose.theta);
          nctx.fillStyle = 'rgba(10, 110, 209, 0.75)';
          const radius = Math.max(0.025, 1.8 / navZoom);
          scan.points.forEach(pt => {
            const lx = Number(pt[0]);
            const ly = Number(pt[1]);
            if (!Number.isFinite(lx) || !Number.isFinite(ly)) return;
            nctx.beginPath();
            nctx.arc(lx, -ly, radius, 0, Math.PI * 2);
            nctx.fill();
          });
          nctx.restore();
        };

        const drawZoneShape = (zone, draft = false) => {
          const points = zone && Array.isArray(zone.points) ? zone.points : null;
          if (!points || points.length === 0) return;
          nctx.save();
          nctx.beginPath();
          points.forEach((pt, i) => {
            const x = Number(pt[0]);
            const y = Number(pt[1]);
            if (i === 0) nctx.moveTo(x, -y);
            else nctx.lineTo(x, -y);
          });
          if (points.length >= 3) {
            nctx.closePath();
            nctx.fillStyle = draft ? 'rgba(198,40,40,.12)' : 'rgba(198,40,40,.24)';
            nctx.fill();
          }
          nctx.strokeStyle = draft ? '#D95F02' : '#C62828';
          nctx.lineWidth = Math.max(0.025, 1.5 / navZoom);
          nctx.stroke();

          // Draw handle dots at vertices (excluding the temporary hover preview point at the end)
          points.forEach((pt, i) => {
            if (draft && i === points.length - 1) return;
            nctx.beginPath();
            nctx.arc(pt[0], -pt[1], Math.max(0.02, 4.0 / navZoom), 0, 2 * Math.PI);
            nctx.fillStyle = '#FFFFFF';
            nctx.fill();
            nctx.strokeStyle = draft ? '#D95F02' : '#C62828';
            nctx.lineWidth = Math.max(0.012, 1.5 / navZoom);
            nctx.stroke();
          });
          nctx.restore();
        };

        const drawStationMarker = (station, index) => {
          if (!station || station.enabled === false) return;
          const x = Number(station.x);
          const y = Number(station.y);
          const theta = Number(station.theta) || 0;
          if (!Number.isFinite(x) || !Number.isFinite(y)) return;
          nctx.save();
          nctx.translate(x, -y);
          nctx.rotate(-theta);
          nctx.fillStyle = 'rgba(46,125,50,.18)';
          nctx.strokeStyle = '#2E7D32';
          nctx.lineWidth = Math.max(0.025, 1.4 / navZoom);
          nctx.beginPath();
          nctx.arc(0, 0, 0.18, 0, Math.PI * 2);
          nctx.fill();
          nctx.stroke();
          nctx.beginPath();
          nctx.moveTo(0, 0);
          nctx.lineTo(0.45, 0);
          nctx.stroke();
          nctx.restore();

          nctx.save();
          nctx.scale(1 / navZoom, 1 / navZoom);
          nctx.fillStyle = '#2E7D32';
          nctx.font = "10px 'IBM Plex Mono',monospace";
          nctx.fillText(String(index + 1), x * navZoom + 5, -y * navZoom - 5);
          nctx.restore();
        };

        if (cMap && cMap.checked) drawGrid(mapBitmap, mapData);
        keepoutZones.forEach(zone => {
          if (zone.enabled !== false) drawZoneShape(zone, false);
        });
        if (zoneDraft) drawZoneShape(zoneDraft, true);
        if (cGlobal && cGlobal.checked) drawGrid(globalBitmap, globalCostmap);
        if (cLocal && cLocal.checked) drawGrid(localBitmap, localCostmap);
        if (cLidar && cLidar.checked) drawLidarScan(lidarScan);

        if (cPath && cPath.checked && navPath && navPath.length > 0) {
          nctx.strokeStyle = '#D95F02';
          nctx.lineWidth = 0.05;
          nctx.beginPath();
          navPath.forEach((pt, i) => {
            if (i === 0) nctx.moveTo(pt[0], -pt[1]);
            else nctx.lineTo(pt[0], -pt[1]);
          });
          nctx.stroke();
        }

        if (recordedPathData && recordedPathData.length > 0) {
          nctx.strokeStyle = '#8B5CF6'; // Premium vibrant violet
          nctx.lineWidth = 0.06;
          nctx.beginPath();
          recordedPathData.forEach((pt, i) => {
            if (i === 0) nctx.moveTo(pt[0], -pt[1]);
            else nctx.lineTo(pt[0], -pt[1]);
          });
          nctx.stroke();

          // Draw transverse checkpoints along the path
          recordedPathData.forEach((pt) => {
            if (pt.length > 2 && pt[2] > 0.5) {
              nctx.save();
              nctx.fillStyle = '#F59E0B'; // Premium amber gold
              nctx.strokeStyle = '#FFFFFF';
              nctx.lineWidth = 0.015;
              nctx.beginPath();
              nctx.arc(pt[0], -pt[1], 0.09, 0, Math.PI * 2);
              nctx.fill();
              nctx.stroke();
              
              // Draw an inner glowing red dot
              nctx.fillStyle = '#EF4444'; // Red core
              nctx.beginPath();
              nctx.arc(pt[0], -pt[1], 0.045, 0, Math.PI * 2);
              nctx.fill();
              nctx.restore();
            }
          });
        }

        if (cRobot && cRobot.checked) {
          const rx = navPose.x, ry = navPose.y, rt = navPose.theta;
          nctx.save();
          nctx.translate(rx, -ry);
          nctx.rotate(-rt);
          nctx.fillStyle = 'rgba(64,82,97,0.7)';
          nctx.strokeStyle = '#0A6ED1';
          nctx.lineWidth = 0.02;
          nctx.beginPath();
          nctx.moveTo(0.2, 0);
          nctx.lineTo(-0.15, 0.15);
          nctx.lineTo(-0.15, -0.15);
          nctx.closePath();
          nctx.fill(); nctx.stroke();
          nctx.restore();
        }

        if (cFootprint && cFootprint.checked) {
          const rx = navPose.x, ry = navPose.y, rt = navPose.theta;
          nctx.save();
          nctx.translate(rx, -ry);
          nctx.rotate(-rt);
          nctx.fillStyle = 'rgba(255, 165, 0, 0.15)';
          nctx.strokeStyle = '#D95F02';
          nctx.lineWidth = 0.02;
          nctx.beginPath();
          nctx.moveTo(0.57, -0.21);
          nctx.lineTo(0.57, 0.21);
          nctx.lineTo(-0.57, 0.21);
          nctx.lineTo(-0.57, -0.21);
          nctx.closePath();
          nctx.fill(); nctx.stroke();
          nctx.restore();
        }

        drawPoseMarker(poseDraft);
        stations.forEach(drawStationMarker);

        nctx.restore();
      }

      window.requestNavDraw = requestNavRedraw;

      const processGrid = async (data, isCostmap) => {
        if (!data || !data.b64) return null;
        const bin = atob(data.b64);
        const img = new ImageData(data.w, data.h);
        const d = img.data;
        for (let i = 0; i < bin.length; i++) {
          let val = bin.charCodeAt(i);
          if (val > 127) val -= 256;
          let r = 0, g = 0, b = 0, a = 0;
          if (val === -1) {
            if (!isCostmap) { r = 220; g = 225; b = 230; a = 255; }
          } else if (val === 0) {
            if (!isCostmap) { r = 255; g = 255; b = 255; a = 255; }
          } else if (val >= 99) {
            if (isCostmap) { r = 255; g = 0; b = 0; a = 120; }
            else { r = 0; g = 0; b = 0; a = 255; }
          } else {
            if (isCostmap) { r = 0; g = 150; b = 255; a = Math.floor(val * 2); }
            else { let c = 255 - Math.floor(val * 2.5); r = c; g = c; b = c; a = 255; }
          }
          const idx = i * 4;
          d[idx] = r; d[idx + 1] = g; d[idx + 2] = b; d[idx + 3] = a;
        }
        return await window.createImageBitmap(img);
      };

      window.onNavMap = async (data) => { mapData = data; mapBitmap = await processGrid(data, false); requestNavRedraw(); };
      window.onNavLocalCostmap = async (data) => { localCostmap = data; localBitmap = await processGrid(data, true); requestNavRedraw(); };
      window.onNavGlobalCostmap = async (data) => { globalCostmap = data; globalBitmap = await processGrid(data, true); requestNavRedraw(); };
      window.onNavPath = (data) => { navPath = data; requestNavRedraw(); };
      window.onRecordedPath = (data) => { recordedPathData = data || []; requestNavRedraw(); };
      window.onNavLidarScan = (data) => { lidarScan = data; requestNavRedraw(); };

      function makeAnnotationId(prefix) {
        return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`;
      }

      function currentMapName() {
        return window.selectedMapName || activeMapName;
      }

      function setAnnotationStatus(text, state = '') {
        if (!annotationStatus) return;
        annotationStatus.textContent = text;
        annotationStatus.className = 'annotation-status' + (state ? ` ${state}` : '');
        addNavLog('Restriction', text, state);
      }

      function setMissionStatus(text, state = '') {
        if (!missionStatus) return;
        missionStatus.textContent = text;
        missionStatus.className = 'annotation-status' + (state ? ` ${state}` : '');
        addNavLog('Mission', text, state);
      }

      function formatPoseText(x, y, theta) {
        return `x:${Number(x).toFixed(2)} y:${Number(y).toFixed(2)} th:${(Number(theta) * 180 / Math.PI).toFixed(1)}deg`;
      }

      function zoneFromCorners(a, b) {
        return {
          id: makeAnnotationId('zone'),
          name: `Restriction ${keepoutZones.length + 1}`,
          enabled: true,
          points: [
            [a.x, a.y],
            [b.x, a.y],
            [b.x, b.y],
            [a.x, b.y],
          ]
        };
      }

      function stationPayload(station) {
        return {
          id: station.id,
          name: station.name,
          x: Number(station.x),
          y: Number(station.y),
          theta: Number(station.theta),
          wait_sec: Number(station.wait_sec || 0),
          enabled: station.enabled !== false,
        };
      }

      function fillStationFields(station) {
        document.getElementById('stationName').value = station.name || '';
        document.getElementById('stationX').value = Number(station.x).toFixed(2);
        document.getElementById('stationY').value = Number(station.y).toFixed(2);
        document.getElementById('stationYaw').value = (Number(station.theta || 0) * 180 / Math.PI).toFixed(1);
        document.getElementById('stationWait').value = Number(station.wait_sec || 0).toFixed(0);
      }

      function readStationFields() {
        const name = (document.getElementById('stationName').value || '').trim() || `Station ${stations.length + 1}`;
        const x = parseFloat(document.getElementById('stationX').value);
        const y = parseFloat(document.getElementById('stationY').value);
        const yaw = parseFloat(document.getElementById('stationYaw').value);
        const waitSec = parseFloat(document.getElementById('stationWait').value || '0');
        if (!Number.isFinite(x) || !Number.isFinite(y) || !Number.isFinite(yaw) || !Number.isFinite(waitSec)) return null;
        return {
          id: editingStationId || makeAnnotationId('station'),
          name,
          x,
          y,
          theta: yaw * Math.PI / 180,
          wait_sec: Math.max(0, waitSec),
          enabled: true,
        };
      }

      function renderZoneList() {
        if (!keepoutZoneList) return;
        if (!keepoutZones.length) {
          const empty = document.createElement('div');
          empty.className = 'empty-note';
          empty.textContent = 'Belum ada restriction area.';
          keepoutZoneList.replaceChildren(empty);
          return;
        }
        keepoutZoneList.replaceChildren(...keepoutZones.map((zone, index) => {
          const row = document.createElement('div');
          row.className = 'annotation-row';
          const copy = document.createElement('div');
          const title = document.createElement('strong');
          title.textContent = zone.name || `Restriction ${index + 1}`;
          const meta = document.createElement('span');
          const xs = zone.points.map(point => Number(point[0]));
          const ys = zone.points.map(point => Number(point[1]));
          meta.textContent = `${zone.enabled === false ? 'DISABLED' : 'ACTIVE'} x:${Math.min(...xs).toFixed(2)}..${Math.max(...xs).toFixed(2)} y:${Math.min(...ys).toFixed(2)}..${Math.max(...ys).toFixed(2)}`;
          copy.append(title, meta);
          const actions = document.createElement('div');
          actions.className = 'row-actions';
          const toggle = document.createElement('button');
          toggle.className = 'mini-action-btn';
          toggle.textContent = zone.enabled === false ? 'Enable' : 'Disable';
          toggle.addEventListener('click', () => {
            zone.enabled = zone.enabled === false;
            renderZoneList();
            requestNavRedraw();
          });
          const del = document.createElement('button');
          del.className = 'mini-action-btn dngr';
          del.textContent = 'Delete';
          del.addEventListener('click', () => {
            keepoutZones = keepoutZones.filter(item => item.id !== zone.id);
            renderZoneList();
            requestNavRedraw();
          });
          actions.append(toggle, del);
          row.append(copy, actions);
          return row;
        }));
      }

      function renderStationList() {
        if (!stationList) return;
        if (!stations.length) {
          const empty = document.createElement('div');
          empty.className = 'empty-note';
          empty.textContent = 'Belum ada station.';
          stationList.replaceChildren(empty);
          return;
        }
        stationList.replaceChildren(...stations.map((station, index) => {
          const row = document.createElement('div');
          row.className = 'station-row';
          const copy = document.createElement('div');
          const title = document.createElement('strong');
          title.textContent = station.name || `Station ${index + 1}`;
          const meta = document.createElement('span');
          meta.textContent = `${station.enabled === false ? 'DISABLED ' : ''}${formatPoseText(station.x, station.y, station.theta)}`;
          copy.append(title, meta);
          const actions = document.createElement('div');
          actions.className = 'row-actions';
          const go = document.createElement('button');
          go.className = 'mini-action-btn';
          go.textContent = 'Go';
          go.disabled = station.enabled === false;
          go.addEventListener('click', () => {
            if (missionMode !== 'single') setMissionMode('single');
            if (typeof window.setDriveModeUi === 'function') window.setDriveModeUi('auto');
            safeSend({ type: 'goal_pose', x: station.x, y: station.y, theta: station.theta });
            setMissionStatus(`Single mission menuju ${station.name}.`, 'busy');
          });
          const queue = document.createElement('button');
          queue.className = 'mini-action-btn';
          queue.textContent = 'Queue';
          queue.disabled = station.enabled === false;
          queue.addEventListener('click', () => {
            missionQueue.push(station.id);
            setMissionMode('queue');
            renderMissionQueue();
          });
          const toggle = document.createElement('button');
          toggle.className = 'mini-action-btn';
          toggle.textContent = station.enabled === false ? 'Enable' : 'Disable';
          toggle.addEventListener('click', () => {
            station.enabled = station.enabled === false;
            if (station.enabled === false) missionQueue = missionQueue.filter(id => id !== station.id);
            renderStationList();
            renderMissionQueue();
            requestNavRedraw();
          });
          const edit = document.createElement('button');
          edit.className = 'mini-action-btn';
          edit.textContent = 'Edit';
          edit.addEventListener('click', () => {
            editingStationId = station.id;
            fillStationFields(station);
          });
          const del = document.createElement('button');
          del.className = 'mini-action-btn dngr';
          del.textContent = 'Delete';
          del.addEventListener('click', () => {
            stations = stations.filter(item => item.id !== station.id);
            missionQueue = missionQueue.filter(id => id !== station.id);
            renderStationList();
            renderMissionQueue();
            requestNavRedraw();
          });
          actions.append(go, queue, toggle, edit, del);
          row.append(copy, actions);
          return row;
        }));
      }

      function renderMissionQueue() {
        if (!missionQueueList) return;
        const queueStations = missionQueue.map(id => stations.find(station => station.id === id)).filter(Boolean);
        if (!queueStations.length) {
          const empty = document.createElement('div');
          empty.className = 'empty-note';
          empty.textContent = 'Queue kosong.';
          missionQueueList.replaceChildren(empty);
          return;
        }
        missionQueueList.replaceChildren(...queueStations.map((station, index) => {
          const row = document.createElement('div');
          row.className = 'queue-row';
          const copy = document.createElement('div');
          const title = document.createElement('strong');
          title.textContent = `${index + 1}. ${station.name}`;
          const meta = document.createElement('span');
          meta.textContent = formatPoseText(station.x, station.y, station.theta);
          copy.append(title, meta);
          const actions = document.createElement('div');
          actions.className = 'row-actions';
          const up = document.createElement('button');
          up.className = 'mini-action-btn';
          up.textContent = 'Up';
          up.disabled = index === 0;
          up.addEventListener('click', () => {
            [missionQueue[index - 1], missionQueue[index]] = [missionQueue[index], missionQueue[index - 1]];
            renderMissionQueue();
          });
          const down = document.createElement('button');
          down.className = 'mini-action-btn';
          down.textContent = 'Down';
          down.disabled = index === missionQueue.length - 1;
          down.addEventListener('click', () => {
            [missionQueue[index + 1], missionQueue[index]] = [missionQueue[index], missionQueue[index + 1]];
            renderMissionQueue();
          });
          const del = document.createElement('button');
          del.className = 'mini-action-btn dngr';
          del.textContent = 'Remove';
          del.addEventListener('click', () => {
            missionQueue.splice(index, 1);
            renderMissionQueue();
          });
          actions.append(up, down, del);
          row.append(copy, actions);
          return row;
        }));
      }

      async function loadStaticMap(mapName) {
        if (!mapName) return;
        const res = await fetch(getApiUrl(`/api/maps/grid?map_name=${encodeURIComponent(mapName)}`), { cache: 'no-store' });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Gagal memuat static map.');
        activeMapName = mapName;
        mapData = data;
        mapBitmap = await processGrid(data, false);
        requestNavRedraw();
      }

      async function loadNavAnnotations(mapName) {
        if (!mapName) return;
        setAnnotationStatus('Memuat restriction dan station...', 'busy');
        try {
          await loadStaticMap(mapName);
          const res = await fetch(getApiUrl(`/api/nav_annotations?map_name=${encodeURIComponent(mapName)}`), { cache: 'no-store' });
          const payload = await res.json();
          if (!res.ok) throw new Error(payload.detail || 'Gagal memuat annotation.');
          keepoutZones = Array.isArray(payload.zones) ? payload.zones : [];
          stations = Array.isArray(payload.stations) ? payload.stations : [];
          missionQueue = missionQueue.filter(id => stations.some(station => station.id === id));
          renderZoneList();
          renderStationList();
          renderMissionQueue();
          setAnnotationStatus(payload.keepout_yaml ? `Loaded ${payload.keepout_yaml}.` : 'Restriction/station siap diedit.', 'success');
          requestNavRedraw();
        } catch (err) {
          setAnnotationStatus(err && err.message ? err.message : 'Gagal memuat annotation.', 'error');
        }
      }

      async function saveAnnotations() {
        const mapName = currentMapName();
        if (!mapName) {
          setAnnotationStatus('Pilih map dulu.', 'error');
          return;
        }
        setAnnotationStatus('Menyimpan annotation dan mask keepout...', 'busy');
        try {
          const res = await fetch(getApiUrl('/api/nav_annotations'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              map_name: mapName,
              zones: keepoutZones,
              stations,
            })
          });
          const payload = await res.json().catch(() => ({}));
          if (!res.ok) throw new Error(payload.detail || payload.message || 'Gagal menyimpan annotation.');
          keepoutZones = Array.isArray(payload.zones) ? payload.zones : keepoutZones;
          stations = Array.isArray(payload.stations) ? payload.stations : stations;
          renderZoneList();
          renderStationList();
          renderMissionQueue();
          setAnnotationStatus(payload.message || 'Annotation tersimpan. Restart Nav2 untuk apply.', 'success');
          requestNavRedraw();
        } catch (err) {
          setAnnotationStatus(err && err.message ? err.message : 'Gagal menyimpan annotation.', 'error');
        }
      }

      function setMissionMode(mode) {
        missionMode = mode === 'queue' ? 'queue' : 'single';
        document.querySelectorAll('.mission-mode-btn').forEach(btn => {
          btn.classList.toggle('active', btn.dataset.mode === missionMode);
        });
        setMissionStatus(missionMode === 'queue' ? 'Queued mission siap.' : 'Single mission siap.');
      }

      window.updateMissionStatusUi = function (status) {
        if (!status) return;
        const state = String(status.state || 'idle').toLowerCase();
        const total = Number(status.total || 0);
        const idx = Number(status.current_index || -1);
        let text = status.message || 'Mission idle.';
        if (status.mode === 'queue' && total > 0 && idx >= 0 && status.station) {
          text = `${text} (${idx + 1}/${total}: ${status.station.name || 'station'})`;
        }
        const uiState = state === 'succeeded' ? 'success' : ['failed', 'canceled'].includes(state) ? 'error' : ['starting', 'running', 'executing'].includes(state) ? 'busy' : '';
        setMissionStatus(text, uiState);
      };

      window.updateMissionAckUi = function (message) {
        if (!message) return;
        setMissionStatus(message.message || (message.ok ? 'Mission command accepted.' : 'Mission command failed.'), message.ok ? 'busy' : 'error');
      };

      [cMap, cRobot, cFootprint, cLocal, cGlobal, cPath, cLidar].forEach(c => {
        if (c) c.addEventListener('change', requestNavRedraw);
      });

      function poseFields(mode) {
        return mode === 'initial'
          ? { x: 'initX', y: 'initY', yaw: 'initYaw' }
          : { x: 'goalX', y: 'goalY', yaw: 'goalYaw' };
      }

      function setPoseFields(mode, x, y, theta) {
        const fields = poseFields(mode);
        document.getElementById(fields.x).value = x.toFixed(2);
        document.getElementById(fields.y).value = y.toFixed(2);
        document.getElementById(fields.yaw).value = (theta * 180 / Math.PI).toFixed(1);
      }

      function readPoseFields(mode) {
        const fields = poseFields(mode);
        const x = parseFloat(document.getElementById(fields.x).value);
        const y = parseFloat(document.getElementById(fields.y).value);
        const deg = parseFloat(document.getElementById(fields.yaw).value);
        if (!Number.isFinite(x) || !Number.isFinite(y) || !Number.isFinite(deg)) return null;
        return { x, y, theta: deg * Math.PI / 180 };
      }

      function canvasPointFromEvent(e) {
        const rect = navCanvas.getBoundingClientRect();
        const sx = navCanvas.width / Math.max(1, rect.width);
        const sy = navCanvas.height / Math.max(1, rect.height);
        return {
          x: (e.clientX - rect.left) * sx,
          y: (e.clientY - rect.top) * sy
        };
      }

      function screenToWorld(pt) {
        return {
          x: (pt.x - navOffX) / navZoom,
          y: -(pt.y - navOffY) / navZoom
        };
      }

      function updatePoseDraft(mode, x, y, theta) {
        poseDraft = { mode, x, y, theta };
        requestNavRedraw();
      }

      function sendPose(mode, x, y, theta) {
        if (mode === 'goal') {
          if (typeof window.setDriveModeUi === 'function') window.setDriveModeUi('auto');
          safeSend({ type: 'goal_pose', x, y, theta });
        } else {
          safeSend({ type: 'initial_pose', x, y, theta });
        }
      }

      function applyPoseFromFields(mode) {
        const pose = readPoseFields(mode);
        if (!pose) {
          alert("Isi nilai X, Y, dan Theta (derajat)");
          return;
        }
        updatePoseDraft(mode, pose.x, pose.y, pose.theta);
        sendPose(mode, pose.x, pose.y, pose.theta);
        setMapClickMode(null);
      }

      function setMapClickMode(nextMode) {
        mapClickMode = mapClickMode === nextMode ? null : nextMode;
        if (mapClickMode) setNavEditorMode(null);
        navCanvas.classList.toggle('pose-tool-active', !!mapClickMode);
        navCanvas.style.cursor = mapClickMode ? 'crosshair' : '';

        const goalActive = mapClickMode === 'goal';
        const initActive = mapClickMode === 'initial';
        const btnMapClickGoal = document.getElementById('btnMapClickGoal');
        const btnMapClickInitialPose = document.getElementById('btnMapClickInitialPose');

        if (btnMapClickGoal) {
          btnMapClickGoal.classList.toggle('active', goalActive);
        }
        if (btnMapClickInitialPose) {
          btnMapClickInitialPose.classList.toggle('active', initActive);
        }
        requestNavRedraw();
      }

      function setNavEditorMode(nextMode) {
        navEditorMode = navEditorMode === nextMode ? null : nextMode;
        if (navEditorMode) mapClickMode = null;
        navCanvas.classList.toggle('pose-tool-active', !!navEditorMode || !!mapClickMode);
        navCanvas.style.cursor = navEditorMode ? 'crosshair' : (mapClickMode ? 'crosshair' : '');
        const drawBtn = document.getElementById('btnDrawKeepout');
        const pickBtn = document.getElementById('btnPickStation');
        if (drawBtn) drawBtn.classList.toggle('active', navEditorMode === 'zone');
        if (pickBtn) pickBtn.classList.toggle('active', navEditorMode === 'station');
        
        // Reset drawing variables
        zoneClicks = [];
        zoneDraft = null;
        zonePointer = null;
        stationPointer = null;
        
        requestNavRedraw();
      }

      function startZonePointer(e) {
        e.preventDefault();
        const pt = canvasPointFromEvent(e);
        const world = screenToWorld(pt);
        zonePointer = {
          id: e.pointerId,
          downX: e.clientX,
          downY: e.clientY,
          lastX: pt.x,
          lastY: pt.y,
          dragged: false
        };
        try { navCanvas.setPointerCapture(e.pointerId); } catch (err) { }
        requestNavRedraw();
      }

      function updateZonePointer(e) {
        if (!zonePointer || e.pointerId !== zonePointer.id) return;
        e.preventDefault();
        const pt = canvasPointFromEvent(e);
        const world = screenToWorld(pt);
        const dist = Math.hypot(e.clientX - zonePointer.downX, e.clientY - zonePointer.downY);
        
        if (dist > 6) {
          zonePointer.dragged = true;
        }
        
        if (zonePointer.dragged) {
          navOffX += pt.x - zonePointer.lastX;
          navOffY += pt.y - zonePointer.lastY;
          zonePointer.lastX = pt.x;
          zonePointer.lastY = pt.y;
          requestNavRedraw();
        } else {
          // If we hover/move without panning, update preview
          zoneDraft = {
            points: [...zoneClicks, [world.x, world.y]]
          };
          requestNavRedraw();
        }
      }

      function finishZonePointer(e, shouldCommit) {
        if (!zonePointer || e.pointerId !== zonePointer.id) return;
        e.preventDefault();
        try { navCanvas.releasePointerCapture(e.pointerId); } catch (err) { }
        
        const pt = canvasPointFromEvent(e);
        const world = screenToWorld(pt);
        const dragged = zonePointer.dragged;
        zonePointer = null;
        
        if (shouldCommit && !dragged) {
          // Place a point!
          const newPt = [Number(world.x.toFixed(4)), Number(world.y.toFixed(4))];
          zoneClicks.push(newPt);
          
          if (zoneClicks.length === 4) {
            const newZone = {
              id: makeAnnotationId('zone'),
              name: `Restriction ${keepoutZones.length + 1}`,
              enabled: true,
              points: [...zoneClicks]
            };
            keepoutZones.push(newZone);
            renderZoneList();
            setAnnotationStatus('Restriction area ditambahkan. Klik Save Restrictions untuk membuat mask.', 'success');
            setNavEditorMode(null); // Resets zoneClicks/zoneDraft and exits mode
          } else {
            // Update draft with hover preview point
            zoneDraft = {
              points: [...zoneClicks, [world.x, world.y]]
            };
          }
        }
        requestNavRedraw();
      }

      function startStationPointer(e) {
        e.preventDefault();
        const pt = canvasPointFromEvent(e);
        const world = screenToWorld(pt);
        const existing = readStationFields();
        const theta = existing ? existing.theta : 0;
        stationPointer = {
          id: e.pointerId,
          startScreen: pt,
          startWorld: world,
          dragged: false,
          theta
        };
        fillStationFields({
          name: document.getElementById('stationName').value || `Station ${stations.length + 1}`,
          x: world.x,
          y: world.y,
          theta,
          wait_sec: Number(document.getElementById('stationWait').value || 0)
        });
        try { navCanvas.setPointerCapture(e.pointerId); } catch (err) { }
      }

      function updateStationPointer(e) {
        if (!stationPointer || e.pointerId !== stationPointer.id) return;
        e.preventDefault();
        const pt = canvasPointFromEvent(e);
        const world = screenToWorld(pt);
        const dist = Math.hypot(pt.x - stationPointer.startScreen.x, pt.y - stationPointer.startScreen.y);
        let theta = stationPointer.theta;
        if (dist >= POSE_DRAG_THRESHOLD_PX) {
          stationPointer.dragged = true;
          theta = Math.atan2(world.y - stationPointer.startWorld.y, world.x - stationPointer.startWorld.x);
        }
        fillStationFields({
          name: document.getElementById('stationName').value || `Station ${stations.length + 1}`,
          x: stationPointer.startWorld.x,
          y: stationPointer.startWorld.y,
          theta,
          wait_sec: Number(document.getElementById('stationWait').value || 0)
        });
      }

      function finishStationPointer(e, shouldCommit) {
        if (!stationPointer || e.pointerId !== stationPointer.id) return;
        e.preventDefault();
        try { navCanvas.releasePointerCapture(e.pointerId); } catch (err) { }
        stationPointer = null;
        setNavEditorMode(null);
        if (shouldCommit) {
          const station = readStationFields();
          if (station) {
            const idx = stations.findIndex(item => item.id === station.id);
            editingStationId = null;
            if (idx >= 0) stations[idx] = station;
            else stations.push(station);
            renderStationList();
            setAnnotationStatus('Station ditambahkan. Klik Save Stations untuk menyimpan.', 'success');
            requestNavRedraw();
          }
        }
      }

      function startPosePointer(e) {
        e.preventDefault();
        const pt = canvasPointFromEvent(e);
        const world = screenToWorld(pt);
        const mode = mapClickMode;
        const current = readPoseFields(mode);
        const theta = current ? current.theta : 0;
        posePointer = {
          id: e.pointerId,
          mode,
          startScreen: pt,
          startWorld: world,
          dragged: false
        };
        setPoseFields(mode, world.x, world.y, theta);
        updatePoseDraft(mode, world.x, world.y, theta);
        try { navCanvas.setPointerCapture(e.pointerId); } catch (err) { }
      }

      function updatePosePointer(e) {
        if (!posePointer || e.pointerId !== posePointer.id) return;
        e.preventDefault();
        const pt = canvasPointFromEvent(e);
        const world = screenToWorld(pt);
        const dist = Math.hypot(pt.x - posePointer.startScreen.x, pt.y - posePointer.startScreen.y);
        let theta = poseDraft && poseDraft.mode === posePointer.mode ? poseDraft.theta : 0;
        if (dist >= POSE_DRAG_THRESHOLD_PX) {
          posePointer.dragged = true;
          theta = Math.atan2(world.y - posePointer.startWorld.y, world.x - posePointer.startWorld.x);
        }
        setPoseFields(posePointer.mode, posePointer.startWorld.x, posePointer.startWorld.y, theta);
        updatePoseDraft(posePointer.mode, posePointer.startWorld.x, posePointer.startWorld.y, theta);
      }

      function finishPosePointer(e, shouldPublish) {
        if (!posePointer || e.pointerId !== posePointer.id) return;
        e.preventDefault();
        const finished = posePointer;
        const pose = poseDraft && poseDraft.mode === finished.mode ? poseDraft : null;
        try { navCanvas.releasePointerCapture(e.pointerId); } catch (err) { }
        posePointer = null;
        setMapClickMode(null);
        if (shouldPublish && finished.dragged && pose) {
          sendPose(finished.mode, pose.x, pose.y, pose.theta);
        } else {
          const fields = poseFields(finished.mode);
          document.getElementById(fields.yaw).focus();
        }
      }

      navCanvas.addEventListener('pointerdown', e => {
        // Track active pointers
        navActivePointers = navActivePointers.filter(p => p.id !== e.pointerId);
        navActivePointers.push({
          id: e.pointerId,
          clientX: e.clientX,
          clientY: e.clientY,
          pt: canvasPointFromEvent(e)
        });

        if (navActivePointers.length === 2) {
          // Suspend standard single-pointer pan
          isDragging = false;
          panPointerId = null;
          navCanvas.classList.remove('panning');

          // Initialize pinch parameters
          const p1 = navActivePointers[0];
          const p2 = navActivePointers[1];
          initialPinchDistance = Math.hypot(p1.clientX - p2.clientX, p1.clientY - p2.clientY);
          initialPinchZoom = navZoom;
          
          const centerX = (p1.pt.x + p2.pt.x) / 2;
          const centerY = (p1.pt.y + p2.pt.y) / 2;
          initialPinchCenterWorld = screenToWorld({ x: centerX, y: centerY });
          
          try { navCanvas.setPointerCapture(e.pointerId); } catch (err) { }
          return;
        }

        if (mapClickMode) {
          startPosePointer(e);
          return;
        }
        if (navEditorMode === 'zone') {
          startZonePointer(e);
          return;
        }
        if (navEditorMode === 'station') {
          startStationPointer(e);
          return;
        }

        // Only start single-pointer drag/pan if exactly 1 touch is present
        if (navActivePointers.length === 1) {
          setNavFollowRobot(false, false);
          const pt = canvasPointFromEvent(e);
          isDragging = true;
          panPointerId = e.pointerId;
          lastX = pt.x;
          lastY = pt.y;
          navCanvas.classList.add('panning');
          try { navCanvas.setPointerCapture(e.pointerId); } catch (err) { }
        }
      });

      navCanvas.addEventListener('pointermove', e => {
        // Update tracked pointer coordinates
        const idx = navActivePointers.findIndex(p => p.id === e.pointerId);
        if (idx >= 0) {
          navActivePointers[idx].clientX = e.clientX;
          navActivePointers[idx].clientY = e.clientY;
          navActivePointers[idx].pt = canvasPointFromEvent(e);
        }

        // Handle touch pinch-to-zoom gesture
        if (navActivePointers.length === 2 && initialPinchDistance !== null) {
          e.preventDefault();
          const p1 = navActivePointers[0];
          const p2 = navActivePointers[1];
          const newDist = Math.hypot(p1.clientX - p2.clientX, p1.clientY - p2.clientY);
          if (newDist > 5) {
            const ratio = newDist / initialPinchDistance;
            navZoom = Math.min(220, Math.max(2, initialPinchZoom * ratio));
            
            const centerX = (p1.pt.x + p2.pt.x) / 2;
            const centerY = (p1.pt.y + p2.pt.y) / 2;
            
            if (navFollowRobot) {
              centerViewOnRobot();
            } else {
              navOffX = centerX - initialPinchCenterWorld.x * navZoom;
              navOffY = centerY + initialPinchCenterWorld.y * navZoom;
            }
            requestNavRedraw();
          }
          return;
        }

        if (posePointer) {
          updatePosePointer(e);
          return;
        }
        if (zonePointer) {
          updateZonePointer(e);
          return;
        }
        if (stationPointer) {
          updateStationPointer(e);
          return;
        }
        if (navEditorMode === 'zone' && zoneClicks.length > 0) {
          const world = screenToWorld(canvasPointFromEvent(e));
          zoneDraft = {
            points: [...zoneClicks, [world.x, world.y]]
          };
          requestNavRedraw();
          return;
        }
        if (!isDragging || e.pointerId !== panPointerId) return;
        const pt = canvasPointFromEvent(e);
        navOffX += pt.x - lastX;
        navOffY += pt.y - lastY;
        lastX = pt.x;
        lastY = pt.y;
        requestNavRedraw();
      });

      navCanvas.addEventListener('pointerup', e => {
        // Remove pointer from active list
        navActivePointers = navActivePointers.filter(p => p.id !== e.pointerId);
        if (navActivePointers.length < 2) {
          initialPinchDistance = null;
          initialPinchZoom = null;
          initialPinchCenterWorld = null;
        }

        if (posePointer) {
          finishPosePointer(e, true);
          return;
        }
        if (zonePointer) {
          finishZonePointer(e, true);
          return;
        }
        if (stationPointer) {
          finishStationPointer(e, true);
          return;
        }
        if (e.pointerId === panPointerId) {
          isDragging = false;
          panPointerId = null;
          navCanvas.classList.remove('panning');
          try { navCanvas.releasePointerCapture(e.pointerId); } catch (err) { }
        }

        // Resume standard pan if 1 pointer remains active
        if (navActivePointers.length === 1 && !posePointer && !zonePointer && !stationPointer && !mapClickMode && navEditorMode !== 'zone' && navEditorMode !== 'station') {
          const remaining = navActivePointers[0];
          panPointerId = remaining.id;
          lastX = remaining.pt.x;
          lastY = remaining.pt.y;
          isDragging = true;
          navCanvas.classList.add('panning');
          try { navCanvas.setPointerCapture(remaining.id); } catch (err) { }
        }
      });

      navCanvas.addEventListener('pointercancel', e => {
        // Remove pointer from active list
        navActivePointers = navActivePointers.filter(p => p.id !== e.pointerId);
        if (navActivePointers.length < 2) {
          initialPinchDistance = null;
          initialPinchZoom = null;
          initialPinchCenterWorld = null;
        }

        if (posePointer) {
          finishPosePointer(e, false);
          return;
        }
        if (zonePointer) {
          finishZonePointer(e, false);
          return;
        }
        if (stationPointer) {
          finishStationPointer(e, false);
          return;
        }
        if (e.pointerId === panPointerId) {
          isDragging = false;
          panPointerId = null;
          navCanvas.classList.remove('panning');
          try { navCanvas.releasePointerCapture(e.pointerId); } catch (err) { }
        }

        // Resume standard pan if 1 pointer remains active
        if (navActivePointers.length === 1 && !posePointer && !zonePointer && !stationPointer && !mapClickMode && navEditorMode !== 'zone' && navEditorMode !== 'station') {
          const remaining = navActivePointers[0];
          panPointerId = remaining.id;
          lastX = remaining.pt.x;
          lastY = remaining.pt.y;
          isDragging = true;
          navCanvas.classList.add('panning');
          try { navCanvas.setPointerCapture(remaining.id); } catch (err) { }
        }
      });
      navCanvas.addEventListener('wheel', e => {
        e.preventDefault();
        const pt = canvasPointFromEvent(e);
        const worldBefore = screenToWorld(pt);
        const scale = e.deltaY < 0 ? 1.1 : 0.9;
        navZoom = Math.min(220, Math.max(2, navZoom * scale));
        if (navFollowRobot) {
          centerViewOnRobot();
        } else {
          navOffX = pt.x - worldBefore.x * navZoom;
          navOffY = pt.y + worldBefore.y * navZoom;
        }
        requestNavRedraw();
      }, { passive: false });

      document.getElementById('navZoomIn').onclick = () => zoomNav(1.2);
      document.getElementById('navZoomOut').onclick = () => zoomNav(1 / 1.2);
      document.getElementById('navResetView').onclick = () => {
        navZoom = 40.0;
        resizeNavCanvasToPanel();
        setNavFollowRobot(true, false);
        centerViewOnRobot();
        requestNavRedraw();
      };
      if (btnAutoCenter) btnAutoCenter.onclick = () => setNavFollowRobot(!navFollowRobot);

      if ('ResizeObserver' in window) {
        new ResizeObserver(requestNavRedraw).observe(navCanvas.parentElement);
      } else {
        window.addEventListener('resize', requestNavRedraw);
      }

      setTimeout(() => {
        resizeNavCanvasToPanel();
        if (navFollowRobot) centerViewOnRobot();
        requestNavRedraw();
      }, 200);

      const btnMapClickGoal = document.getElementById('btnMapClickGoal');
      if (btnMapClickGoal) {
        btnMapClickGoal.onclick = () => {
          setMapClickMode('goal');
        };
      }
      const btnMapClickInitialPose = document.getElementById('btnMapClickInitialPose');
      if (btnMapClickInitialPose) {
        btnMapClickInitialPose.onclick = () => {
          setMapClickMode('initial');
        };
      }
      const btnApplyGoal = document.getElementById('btnApplyGoal');
      if (btnApplyGoal) {
        btnApplyGoal.onclick = () => {
          applyPoseFromFields('goal');
        };
      }
      const btnApplyInitialPose = document.getElementById('btnApplyInitialPose');
      if (btnApplyInitialPose) {
        btnApplyInitialPose.onclick = () => {
          applyPoseFromFields('initial');
        };
      }

      const btnDrawKeepout = document.getElementById('btnDrawKeepout');
      if (btnDrawKeepout) btnDrawKeepout.onclick = () => setNavEditorMode('zone');
      const btnClearKeepoutDraft = document.getElementById('btnClearKeepoutDraft');
      if (btnClearKeepoutDraft) btnClearKeepoutDraft.onclick = () => setNavEditorMode(null);
      const btnSaveAnnotations = document.getElementById('btnSaveAnnotations');
      if (btnSaveAnnotations) btnSaveAnnotations.onclick = saveAnnotations;
      const btnPickStation = document.getElementById('btnPickStation');
      if (btnPickStation) btnPickStation.onclick = () => setNavEditorMode('station');
      const btnAddStation = document.getElementById('btnAddStation');
      if (btnAddStation) {
        btnAddStation.onclick = () => {
          const station = readStationFields();
          if (!station) {
            setAnnotationStatus('Isi station X, Y, dan Theta dengan angka valid.', 'error');
            return;
          }
          const idx = stations.findIndex(item => item.id === station.id);
          if (idx >= 0) stations[idx] = station;
          else stations.push(station);
          editingStationId = null;
          renderStationList();
          renderMissionQueue();
          requestNavRedraw();
          setAnnotationStatus('Station ditambahkan/diupdate. Klik Save Stations untuk menyimpan.', 'success');
        };
      }
      const btnSaveStations = document.getElementById('btnSaveStations');
      if (btnSaveStations) btnSaveStations.onclick = saveAnnotations;

      document.querySelectorAll('.mission-mode-btn[data-mode]').forEach(btn => {
        btn.addEventListener('click', () => setMissionMode(btn.dataset.mode));
      });
      const btnStartQueue = document.getElementById('btnStartQueue');
      if (btnStartQueue) {
        btnStartQueue.onclick = () => {
          const queueStations = missionQueue
            .map(id => stations.find(station => station.id === id))
            .filter(station => station && station.enabled !== false);
          if (!queueStations.length) {
            setMissionStatus('Queue kosong.', 'error');
            return;
          }
          setMissionMode('queue');
          safeSend({ type: 'mission_queue_start', stations: queueStations.map(stationPayload) });
          setMissionStatus('Mengirim queued mission...', 'busy');
        };
      }
      const btnCancelQueue = document.getElementById('btnCancelQueue');
      if (btnCancelQueue) btnCancelQueue.onclick = () => safeSend({ type: 'mission_queue_cancel' });
      const btnClearQueue = document.getElementById('btnClearQueue');
      if (btnClearQueue) {
        btnClearQueue.onclick = () => {
          missionQueue = [];
          renderMissionQueue();
          setMissionStatus('Queue dibersihkan.');
        };
      }

      document.addEventListener('arya:maps-loaded', event => loadNavAnnotations(event.detail && event.detail.mapName));
      document.addEventListener('arya:map-selected', event => loadNavAnnotations(event.detail && event.detail.mapName));
      setTimeout(() => {
        if (window.selectedMapName) loadNavAnnotations(window.selectedMapName);
      }, 900);

      // Display Features Toggle
      const btnToggleDisplayFeatures = document.getElementById('btnToggleDisplayFeatures');
      const displayFeaturesContent = document.getElementById('displayFeaturesContent');
      if (btnToggleDisplayFeatures && displayFeaturesContent) {
        btnToggleDisplayFeatures.onclick = () => {
          const section = btnToggleDisplayFeatures.parentElement;
          const isCollapsed = section.classList.toggle('collapsed');
          displayFeaturesContent.style.display = isCollapsed ? 'none' : 'flex';
        };
      }

      // Restrictions Editing Toggle
      const btnEditRestrictions = document.getElementById('btnEditRestrictions');
      const editToolsRestrictions = document.getElementById('editToolsRestrictions');
      if (btnEditRestrictions && editToolsRestrictions) {
        btnEditRestrictions.onclick = () => {
          const isActive = btnEditRestrictions.classList.toggle('active');
          editToolsRestrictions.style.display = isActive ? 'block' : 'none';
          btnEditRestrictions.textContent = isActive ? 'Close' : 'Edit';
        };
      }

      // Stations Editing Toggle
      const btnEditStations = document.getElementById('btnEditStations');
      const editToolsStations = document.getElementById('editToolsStations');
      if (btnEditStations && editToolsStations) {
        btnEditStations.onclick = () => {
          const isActive = btnEditStations.classList.toggle('active');
          editToolsStations.style.display = isActive ? 'block' : 'none';
          btnEditStations.textContent = isActive ? 'Close' : 'Edit';
        };
      }

      renderZoneList();
      renderStationList();
      renderMissionQueue();

      setInterval(() => {
        if (cRobot && cRobot.checked) requestNavRedraw();
      }, 500);
    });