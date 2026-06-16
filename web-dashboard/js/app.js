// ============================================================
// DustCheck Web Dashboard - Main Application
// Firebase Realtime DB + Chart.js + Notifications
// 4-particle: PM1.0, PM2.5, PM4.0, PM10
// ============================================================

// ─── State ───
let chart = null;
let currentTab = '24h';
let currentStatType = 'pm25';
let allData = [];       // 24h realtime listener data
let viewMode = 'chart'; // 'chart' | 'table'
const MAX_REALTIME_POINTS = 30;
const dataCache = {};   // { '7d': { data:[], ts: Date.now() }, ... }
const CACHE_TTL = { '7d': 300000, '30d': 300000, '1y': 600000 };

// Dataset visibility — all 4 active by default
let datasetVisible = { pm1: true, pm25: true, pm4: true, pm10: true };

// Chart display settings
let chartSettings = {
    showTimeInTooltip: localStorage.getItem('dustcheck-tooltip-time') !== 'false',
    showMidnightLines: localStorage.getItem('dustcheck-midnight-lines') !== 'false',
};

// Notification state
let prevGrade = { pm25: null, pm10: null };
let notifSettings = {};

// Dataset index mapping
const DS_INDEX = { pm1: 0, pm25: 1, pm4: 2, pm10: 3 };

// Memo state
let memos = [];
let memoAuthenticated = localStorage.getItem('dustcheck-authenticated') === 'true';
let editingMemoId = null;
let showMemos = localStorage.getItem('dustcheck-show-memos') !== 'false'; // defaults to true

// ─── Initialize ───
document.addEventListener('DOMContentLoaded', () => {
    loadTheme();
    loadNotifSettings();
    loadMemoToggleSetting();
    loadCollapsibleStates();
    initFirebase();
    initChart();
    initTabs();
    initStatsTabs();
    initViewToggle();
    initPmCardClick();
    initDatasetToggles();
    initCollapsibles();
    initStatusToggle();
    initSettingsModal();
    initMemos();
    startRelativeTimeUpdater();
    initDatetimeLocalAutoClose();
});

function initDatetimeLocalAutoClose() {
    document.querySelectorAll('input[type="datetime-local"]').forEach(input => {
        input.addEventListener('change', () => {
            input.blur();
        });
    });
}

function updateDataPinState() {
    const pinGroup = document.getElementById('data-pin-group');
    const pinSuccess = document.getElementById('data-pin-success');
    const inputPin = document.getElementById('data-pin');
    
    if (memoAuthenticated) {
        if (pinGroup) pinGroup.style.display = 'none';
        if (pinSuccess) pinSuccess.style.display = 'flex';
    } else {
        if (pinGroup) pinGroup.style.display = '';
        if (pinSuccess) pinSuccess.style.display = 'none';
        if (inputPin) inputPin.value = '';
    }
}

// ─── Firebase Init ───
function initFirebase() {
    try {
        firebase.initializeApp(FIREBASE_CONFIG);
        const db = firebase.database();

        db.ref('latest').on('value', (snap) => {
            const data = snap.val();
            if (data) {
                updateCurrentDisplay(data);
                updateStatus(true, data.time);
                checkNotification(data);
            }
        });

        db.ref('dust_data').orderByChild('timestamp').limitToLast(1440).on('value', (snap) => {
            allData = [];
            snap.forEach((c) => { allData.push(c.val()); });
            updateChart();
            updateStats();
        });

        updateStatus(true);
    } catch (e) {
        console.error('Firebase 초기화 실패:', e);
        updateStatus(false);
        showDemoData();
    }
}

// ─── Display Update ───
function updateCurrentDisplay(data) {
    const pm1 = data.pm1 || 0;
    const pm25 = data.pm25 || 0;
    const pm4 = data.pm4 || 0;
    const pm10 = data.pm10 || 0;

    animateValue('pm1-value', pm1);
    animateValue('pm25-value', pm25);
    animateValue('pm4-value', pm4);
    animateValue('pm10-value', pm10);

    const q1 = getAirQuality('pm1', pm1);
    const q25 = getAirQuality('pm25', pm25);
    const q4 = getAirQuality('pm4', pm4);
    const q10 = getAirQuality('pm10', pm10);

    styleCard('pm1-card', q1);
    styleCard('pm25-card', q25);
    styleCard('pm4-card', q4);
    styleCard('pm10-card', q10);

    // Main grade card (PM1.0 & PM2.5 based)
    const el = (id) => document.getElementById(id);
    const ge = el('grade-emoji'), gl = el('grade-label'), gd = el('grade-desc');
    const idx1 = AIR_QUALITY.pm1.indexOf(q1);
    const idx25 = AIR_QUALITY.pm25.indexOf(q25);
    const worseQ = idx1 >= idx25 ? q1 : q25;

    if (ge) {
        if (q1.emoji === q25.emoji) {
            ge.textContent = q25.emoji;
        } else {
            ge.textContent = `${q1.emoji} ${q25.emoji}`;
        }
    }
    if (gl) {
        gl.innerHTML = `PM1.0 <span style="color:${q1.color}">${q1.label}</span> &middot; PM2.5 <span style="color:${q25.color}">${q25.label}</span>`;
        gl.style.color = '';
    }
    if (gd) gd.textContent = `PM1.0 ${pm1.toFixed(1)} μg/m³ (${q1.labelEn}) \u00B7 PM2.5 ${pm25.toFixed(1)} μg/m³ (${q25.labelEn})`;

    const gc = document.querySelector('.grade-card');
    if (gc) {
        gc.style.borderColor = worseQ.color + '22';
        gc.classList.add('data-pulse');
        setTimeout(() => gc.classList.remove('data-pulse'), 800);
    }

    // Gauges
    updateGauge('pm1', pm1, [10, 25, 50, 100]);
    updateGauge('pm25', pm25, [15, 35, 75, 150]);
    updateGauge('pm4', pm4, [20, 50, 100, 200]);
    updateGauge('pm10', pm10, [30, 80, 150, 300]);
}

function styleCard(cardId, q) {
    const card = document.getElementById(cardId);
    if (!card) return;
    const val = card.querySelector('.pm-card__value');
    if (val) val.style.color = q.color;
    card.style.setProperty('--card-accent', q.color);
    card.style.borderTopColor = q.color;
    const grade = card.querySelector('.pm-card__grade');
    if (grade) {
        grade.textContent = q.label;
        grade.style.background = q.bg;
        grade.style.color = q.color;
    }
}

function animateValue(elementId, targetValue) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const current = parseFloat(el.textContent) || 0;
    const diff = targetValue - current;
    const steps = 15;
    let step = 0;
    const timer = setInterval(() => {
        step++;
        el.textContent = (current + (diff / steps) * step).toFixed(1);
        if (step >= steps) { el.textContent = targetValue.toFixed(1); clearInterval(timer); }
    }, 25);
}

// ─── Gauge ───
function updateGauge(type, value, thresholds) {
    const valEl = document.getElementById(`gauge-${type}-val`);
    const marker = document.getElementById(`marker-${type}`);
    if (valEl) valEl.textContent = `${value.toFixed(1)} μg/m³`;
    if (!marker) return;

    // thresholds = [좋음max, 보통max, 나쁨max, 매우나쁨 display max]
    // Each segment is 25% wide, map value to correct segment position
    let pct = 0;
    if (value <= thresholds[0]) {
        // 좋음: 0% ~ 25%
        pct = (value / thresholds[0]) * 25;
    } else if (value <= thresholds[1]) {
        // 보통: 25% ~ 50%
        pct = 25 + ((value - thresholds[0]) / (thresholds[1] - thresholds[0])) * 25;
    } else if (value <= thresholds[2]) {
        // 나쁨: 50% ~ 75%
        pct = 50 + ((value - thresholds[1]) / (thresholds[2] - thresholds[1])) * 25;
    } else {
        // 매우나쁨: 75% ~ 100%
        pct = 75 + Math.min(((value - thresholds[2]) / (thresholds[3] - thresholds[2])) * 25, 25);
    }
    pct = Math.min(pct, 100);
    marker.style.left = `${pct}%`;
}

// ─── Chart ───
function initChart() {
    const ctx = document.getElementById('dustChart');
    if (!ctx) return;

    const datasets = PM_TYPES.map(pm => {
        const clr = PM_CHART_COLORS[pm.key];
        return {
            label: pm.label,
            data: [],
            borderColor: clr.border,
            backgroundColor: clr.bg,
            borderWidth: 2,
            pointRadius: 0,
            pointHoverRadius: 4,
            pointHoverBackgroundColor: clr.border,
            fill: false,
            tension: 0.35,
            hidden: !datasetVisible[pm.key],
            spanGaps: false,
        };
    });

    // ─── Midnight Lines Plugin ───
    const midnightPlugin = {
        id: 'midnightLines',
        afterDraw(chartInstance) {
            if (!chartSettings.showMidnightLines) return;
            if (currentTab === 'realtime' || currentTab === '24h') return;
            const { ctx: c, chartArea, scales } = chartInstance;
            if (!chartArea || !scales.x) return;
            const rawTimes = chartInstance._rawTimeStrings;
            if (!rawTimes || !rawTimes.length) return;

            const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
            const lineColor = isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.12)';
            const textColor = isDark ? 'rgba(255,255,255,0.35)' : 'rgba(0,0,0,0.3)';

            c.save();
            rawTimes.forEach((timeStr, i) => {
                if (!timeStr) return;
                const parts = timeStr.split(' ');
                if (parts.length < 2) return;
                const hhmm = parts[1];
                // Check if this point is at or very close to 00:00
                if (hhmm && hhmm.startsWith('00:0')) {
                    const ts = chartInstance._rawTimestamps;
                    const tsVal = ts && ts[i] ? ts[i] : i;
                    const pixelX = scales.x.getPixelForValue(tsVal);
                    if (pixelX < chartArea.left || pixelX > chartArea.right) return;

                    // Draw vertical line
                    c.beginPath();
                    c.setLineDash([6, 3]);
                    c.strokeStyle = lineColor;
                    c.lineWidth = 1;
                    c.moveTo(pixelX, chartArea.top);
                    c.lineTo(pixelX, chartArea.bottom);
                    c.stroke();
                    c.setLineDash([]);

                    // Draw date label at top
                    const dateStr = parts[0].slice(5); // MM-DD
                    c.fillStyle = textColor;
                    c.font = '10px Inter, sans-serif';
                    c.textAlign = 'center';
                    c.fillText(dateStr, pixelX, chartArea.top - 4);
                }
            });
            c.restore();
        }
    };

    // ─── Memo Chart Plugin ───
    const memoPlugin = {
        id: 'memoMarkers',
        afterDraw(chartInstance) {
            if (!showMemos || !memos.length) return;
            const { ctx: c, chartArea, scales } = chartInstance;
            if (!chartArea || !scales.x) return;
            const xScale = scales.x;
            const rawTimestamps = chartInstance._rawTimestamps;
            if (!rawTimestamps || !rawTimestamps.length) return;

            memos.forEach(memo => {
                if (memo.isPrivate && !memoAuthenticated) {
                    memo._pixelX = null;
                    return;
                }
                const memoTs = memo.timestamp;
                if (!memoTs) return;

                // Find closest data point by timestamp
                let closestIdx = -1;
                let closestDist = Infinity;
                rawTimestamps.forEach((ts, i) => {
                    const dist = Math.abs(ts - memoTs);
                    if (dist < closestDist) { closestDist = dist; closestIdx = i; }
                });

                if (closestIdx < 0 || closestDist > 3600000) return; // skip if > 1h away
                const pixelX = xScale.getPixelForValue(rawTimestamps[closestIdx]);
                if (pixelX < chartArea.left || pixelX > chartArea.right) return;

                // Draw dashed vertical line
                c.save();
                c.beginPath();
                c.setLineDash([4, 4]);
                c.strokeStyle = MEMO_COLOR;
                c.lineWidth = 1.5;
                c.globalAlpha = 0.6;
                c.moveTo(pixelX, chartArea.top);
                c.lineTo(pixelX, chartArea.bottom);
                c.stroke();
                c.setLineDash([]);
                c.globalAlpha = 1;

                // Draw triangle marker at top
                const triSize = 7;
                const triY = chartArea.top - 2;
                c.beginPath();
                c.fillStyle = MEMO_COLOR;
                c.moveTo(pixelX, triY + triSize * 2);
                c.lineTo(pixelX - triSize, triY);
                c.lineTo(pixelX + triSize, triY);
                c.closePath();
                c.fill();

                // Draw small circle at the tip
                c.beginPath();
                c.arc(pixelX, triY + triSize * 2 + 2, 2.5, 0, Math.PI * 2);
                c.fillStyle = MEMO_COLOR;
                c.fill();

                c.restore();

                // Store pixel position for click detection
                memo._pixelX = pixelX;
                memo._chartTop = chartArea.top;
            });
        }
    };

    chart = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: { labels: [], datasets },
        plugins: [midnightPlugin, memoPlugin],
        options: {
            responsive: true, maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    backgroundColor: 'rgba(26,29,46,0.92)',
                    titleColor: '#f0f0f5', bodyColor: '#f0f0f5',
                    borderColor: 'rgba(255,255,255,0.1)', borderWidth: 1,
                    cornerRadius: 8, padding: 10,
                    titleFont: { family: 'Inter', weight: '600' },
                    bodyFont: { family: 'Inter' },
                    callbacks: {
                        title: (items) => {
                            if (!items.length) return '';
                            const idx = items[0].dataIndex;
                            const rawTimes = chart._rawTimeStrings;
                            if (chartSettings.showTimeInTooltip && rawTimes && rawTimes[idx]) {
                                // 초 단위 제거 (YYYY-MM-DD HH:MM:SS → YYYY-MM-DD HH:MM)
                                return rawTimes[idx].replace(/:\d{2}$/, '');
                            }
                            return items[0].label;
                        },
                        label: (c) => {
                            if (c.parsed.y === null || c.parsed.y === undefined) return null;
                            return `${c.dataset.label}: ${c.parsed.y.toFixed(1)} μg/m³`;
                        },
                    },
                },
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'hour',
                        displayFormats: {
                            minute: 'HH:mm',
                            hour: 'HH:mm',
                            day: 'MM/dd',
                            week: 'MM/dd',
                            month: 'yy/MM',
                        },
                        tooltipFormat: 'yyyy-MM-dd HH:mm',
                    },
                    grid: { color: 'rgba(0,0,0,0.04)', drawBorder: false },
                    ticks: { color: '#9ca0b4', font: { family: 'Inter', size: 11 }, maxRotation: 0, maxTicksLimit: 8, autoSkip: true },
                },
                y: {
                    grid: { color: 'rgba(0,0,0,0.04)', drawBorder: false },
                    ticks: { color: '#9ca0b4', font: { family: 'Inter', size: 11 } },
                    beginAtZero: true,
                },
            },
            animation: { duration: 500, easing: 'easeOutQuart' },
            onClick(e) {
                if (!handleChartMemoClick(e)) {
                    // No memo marker was clicked - open memo modal with clicked time
                    handleChartTimeClick(e);
                }
            },
            onHover(e) {
                handleChartMemoHover(e);
            },
        },
    });
    updateChartColors();
}

function updateChartColors() {
    if (!chart) return;
    const s = getComputedStyle(document.documentElement);
    const gridClr = s.getPropertyValue('--chart-grid').trim() || 'rgba(0,0,0,0.04)';
    const tickClr = s.getPropertyValue('--chart-tick').trim() || '#9ca0b4';
    chart.options.scales.x.grid.color = gridClr;
    chart.options.scales.y.grid.color = gridClr;
    chart.options.scales.x.ticks.color = tickClr;
    chart.options.scales.y.ticks.color = tickClr;
    chart.update('none');
}

// ─── Dataset Toggle ───
function initDatasetToggles() {
    document.querySelectorAll('.dataset-toggle').forEach(btn => {
        btn.addEventListener('click', () => {
            const key = btn.dataset.key;
            const idx = DS_INDEX[key];
            if (idx === undefined || !chart) return;

            // Toggle
            btn.classList.toggle('active');
            datasetVisible[key] = btn.classList.contains('active');
            chart.data.datasets[idx].hidden = !datasetVisible[key];
            chart.update('none');
        });
    });
}

async function updateChart() {
    if (!chart) return;

    let filtered = [];
    const now = Date.now();

    if (currentTab === 'realtime') {
        filtered = allData.slice(-MAX_REALTIME_POINTS);
        renderChartData(filtered);
    } else if (currentTab === '24h') {
        filtered = allData.filter(d => d.timestamp > now - 86400000);
        renderChartData(filtered);
    } else {
        // 7d, 30d, 1y — fetch if needed
        const cached = dataCache[currentTab];
        if (cached && (now - cached.ts < (CACHE_TTL[currentTab] || 300000))) {
            renderChartData(cached.data);
        } else {
            await fetchPeriodData(currentTab);
        }
    }
}

async function fetchPeriodData(period) {
    showChartLoading(true);
    const now = Date.now();
    let startTs;
    if (period === '7d') startTs = now - 7 * 86400000;
    else if (period === '30d') startTs = now - 30 * 86400000;
    else if (period === '1y') startTs = now - 365 * 86400000;

    try {
        const db = firebase.database();
        const snap = await db.ref('dust_data').orderByChild('timestamp').startAt(startTs).once('value');
        const data = [];
        snap.forEach(c => { data.push(c.val()); });
        dataCache[period] = { data, ts: Date.now() };
        renderChartData(data);
    } catch (e) {
        console.error(`${period} 데이터 로드 실패:`, e);
    }
    showChartLoading(false);
}

function renderChartData(data) {
    if (!chart || data.length === 0) return;

    let filtered = [...data];

    // Sampling for large datasets
    const maxPoints = 300;
    if (filtered.length > maxPoints) {
        const step = Math.ceil(filtered.length / maxPoints);
        filtered = filtered.filter((_, i) => i % step === 0);
    }

    // Gap detection — dynamically determine threshold from actual data intervals
    // Calculate median interval after sampling, then use 3× median as gap threshold
    let gapThreshold = 300000; // default 5 min
    if (filtered.length > 2) {
        const intervals = [];
        for (let i = 1; i < filtered.length; i++) {
            const t1 = filtered[i - 1].timestamp || new Date(filtered[i - 1].time).getTime();
            const t2 = filtered[i].timestamp || new Date(filtered[i].time).getTime();
            if (t2 > t1) intervals.push(t2 - t1);
        }
        if (intervals.length > 0) {
            intervals.sort((a, b) => a - b);
            const median = intervals[Math.floor(intervals.length / 2)];
            gapThreshold = Math.max(median * 3, 120000); // 최소 2분
        }
    }
    const withGaps = [];
    for (let i = 0; i < filtered.length; i++) {
        withGaps.push(filtered[i]);
        if (i < filtered.length - 1) {
            const ts1 = filtered[i].timestamp || new Date(filtered[i].time).getTime();
            const ts2 = filtered[i + 1].timestamp || new Date(filtered[i + 1].time).getTime();
            if (ts2 - ts1 > gapThreshold) {
                // Insert null at midpoint so gap is proportional
                const midTs = Math.round((ts1 + ts2) / 2);
                withGaps.push({ time: '', timestamp: midTs, pm1: null, pm25: null, pm4: null, pm10: null, _gap: true });
            }
        }
    }
    filtered = withGaps;

    // Time scale unit based on current tab
    const timeUnits = { 'realtime': 'minute', '24h': 'hour', '7d': 'day', '30d': 'day', '1y': 'month' };
    chart.options.scales.x.time.unit = timeUnits[currentTab] || 'hour';

    // Clear labels (time scale uses data x values)
    chart.data.labels = [];

    // Store raw timestamps and time strings for plugins
    chart._rawTimestamps = filtered.map(d => d.timestamp || 0);
    chart._rawTimeStrings = filtered.map(d => d.time || '');

    // Use {x: timestamp, y: value} format for time scale
    chart.data.datasets[DS_INDEX.pm1].data = filtered.map(d => ({
        x: d.timestamp || new Date(d.time).getTime(),
        y: d._gap ? null : (d.pm1 || 0)
    }));
    chart.data.datasets[DS_INDEX.pm25].data = filtered.map(d => ({
        x: d.timestamp || new Date(d.time).getTime(),
        y: d._gap ? null : (d.pm25 || 0)
    }));
    chart.data.datasets[DS_INDEX.pm4].data = filtered.map(d => ({
        x: d.timestamp || new Date(d.time).getTime(),
        y: d._gap ? null : (d.pm4 || 0)
    }));
    chart.data.datasets[DS_INDEX.pm10].data = filtered.map(d => ({
        x: d.timestamp || new Date(d.time).getTime(),
        y: d._gap ? null : (d.pm10 || 0)
    }));
    chart.update('none');

    // Update table if in table view (exclude gap entries)
    if (viewMode === 'table') renderTable(data);
}

function showChartLoading(show) {
    const cc = document.getElementById('chart-container');
    const tc = document.getElementById('table-container');
    const cl = document.getElementById('chart-loading');
    if (show) {
        if (cc) cc.style.display = 'none';
        if (tc) tc.style.display = 'none';
        if (cl) cl.style.display = 'flex';
    } else {
        if (cl) cl.style.display = 'none';
        if (viewMode === 'chart' && cc) cc.style.display = 'block';
        if (viewMode === 'table' && tc) tc.style.display = 'block';
    }
}

// ─── Table View ───
function renderTable(data) {
    const tbody = document.getElementById('data-table-body');
    if (!tbody) return;

    const reversed = [...data].reverse().slice(0, 200); // Latest first, max 200 rows
    tbody.innerHTML = reversed.map(d => {
        const q25 = getAirQuality('pm25', d.pm25 || 0);
        const ts = d.timestamp || new Date(d.time).getTime();
        return `<tr class="table-row-memo" data-time="${d.time || ''}" title="클릭하여 메모 추가">
            <td>${d.time || '--'}</td>
            <td>${(d.pm1 || 0).toFixed(1)}</td>
            <td>${(d.pm25 || 0).toFixed(1)}</td>
            <td>${(d.pm4 || 0).toFixed(1)}</td>
            <td>${(d.pm10 || 0).toFixed(1)}</td>
            <td><span class="status-badge" style="background:${q25.color}20;color:${q25.color};">${q25.label}</span></td>
            <td>
                <button class="icon-btn data-delete-row-btn" data-ts="${ts}" title="이 항목 삭제" style="padding:4px; font-size:12px;">🗑️</button>
            </td>
        </tr>`;
    }).join('');

    // Add click handler    // Table row click to memo, and stop propagation for delete button
    document.querySelectorAll('.table-row-memo').forEach(tr => {
        tr.addEventListener('click', (e) => {
            if (e.target.closest('.data-delete-row-btn')) return; // Ignore if delete button clicked
            const t = tr.dataset.time;
            if (t) openMemoModalWithTime(t);
        });
    });

    // Delete row events
    document.querySelectorAll('.data-delete-row-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const ts = btn.dataset.ts;
            if (ts) deleteDataEntry(ts);
        });
    });
}

// ─── Tabs ───
function initTabs() {
    document.querySelectorAll('.chart-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.chart-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentTab = tab.dataset.period;
            updateChart();
        });
    });
}

// ─── View Toggle (Chart / Table) ───
function initViewToggle() {
    const btn = document.getElementById('btn-view-toggle');
    const btnManage = document.getElementById('btn-data-manage');
    if (!btn) return;
    btn.addEventListener('click', () => {
        viewMode = viewMode === 'chart' ? 'table' : 'chart';
        const cc = document.getElementById('chart-container');
        const tc = document.getElementById('table-container');
        const filters = document.getElementById('dataset-filters');
        const iconTable = btn.querySelector('.icon-table');
        const iconChart = btn.querySelector('.icon-chart');

        if (viewMode === 'table') {
            if (cc) cc.style.display = 'none';
            if (tc) tc.style.display = 'block';
            if (filters) filters.style.display = 'none';
            if (iconTable) iconTable.style.display = 'none';
            if (iconChart) iconChart.style.display = 'block';
            btn.title = '차트 보기';
            // Render table with current data
            const cached = dataCache[currentTab];
            const data = (currentTab === 'realtime' || currentTab === '24h') ? allData : (cached ? cached.data : allData);
            renderTable(data);
        } else {
            if (cc) cc.style.display = 'block';
            if (tc) tc.style.display = 'none';
            if (filters) filters.style.display = 'flex';
            if (iconTable) iconTable.style.display = 'block';
            if (iconChart) iconChart.style.display = 'none';
            btn.title = '테이블 보기';
        }
    });
}

// ─── Stats Tabs (PM1.0 / PM2.5 / PM4.0 / PM10) ───
function initStatsTabs() {
    document.querySelectorAll('.stats-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.stats-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentStatType = tab.dataset.stat;
            updateStats();
        });
    });
}

function updateStats() {
    if (allData.length === 0) return;

    const today = new Date().toISOString().slice(0, 10);
    const todayData = allData.filter(d => d.time && d.time.startsWith(today));
    const dataset = todayData.length > 0 ? todayData : allData.slice(-60);

    const key = currentStatType; // 'pm1', 'pm25', 'pm4', or 'pm10'
    const values = dataset.map(d => d[key] || 0);
    const max = Math.max(...values);
    const min = Math.min(...values);
    const avg = values.reduce((a, b) => a + b, 0) / values.length;

    const el = (id) => document.getElementById(id);
    if (el('stat-max')) el('stat-max').textContent = max.toFixed(1);
    if (el('stat-min')) el('stat-min').textContent = min.toFixed(1);
    if (el('stat-avg')) el('stat-avg').textContent = avg.toFixed(1);
}

// Theme loading is kept separate
function loadTheme() {
    const saved = localStorage.getItem('dustcheck-theme');
    if (saved === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
        const meta = document.querySelector('meta[name="theme-color"]');
        if (meta) meta.content = '#0f1117';
    }
}

// ─── PM Card Click → Scroll to Gauge ───
function initPmCardClick() {
    document.querySelectorAll('.pm-card').forEach(card => {
        card.addEventListener('click', () => {
            const gauge = document.getElementById('gauge-section');
            if (gauge) gauge.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
    });
}

// ─── Collapsible Sections ───
function loadCollapsibleStates() {
    const saved = localStorage.getItem('dustcheck-collapsed');
    if (!saved) return;
    try {
        const states = JSON.parse(saved);
        Object.entries(states).forEach(([targetId, isCollapsed]) => {
            if (isCollapsed) {
                const body = document.getElementById(targetId);
                const header = document.querySelector(`[data-target="${targetId}"]`);
                if (body) body.classList.remove('open');
                if (header) header.setAttribute('aria-expanded', 'false');
            }
        });
    } catch (e) { /* ignore */ }
}

function initCollapsibles() {
    document.querySelectorAll('.collapsible-header').forEach(header => {
        header.addEventListener('click', () => {
            const targetId = header.dataset.target;
            const body = document.getElementById(targetId);
            if (!body) return;

            const isOpen = body.classList.contains('open');
            body.classList.toggle('open');
            header.setAttribute('aria-expanded', isOpen ? 'false' : 'true');

            // Save state
            saveCollapsibleStates();
        });
    });
}

function saveCollapsibleStates() {
    const states = {};
    document.querySelectorAll('.collapsible-header').forEach(header => {
        const targetId = header.dataset.target;
        states[targetId] = header.getAttribute('aria-expanded') === 'false';
    });
    localStorage.setItem('dustcheck-collapsed', JSON.stringify(states));
}

// ─── Settings Modal (Unified Notif, Theme, Data Management) ───
function initSettingsModal() {
    const btnSettings = document.getElementById('btn-settings');
    const modal = document.getElementById('settings-modal');
    const closeBtn = document.getElementById('settings-modal-close');
    
    if (btnSettings) {
        btnSettings.addEventListener('click', () => {
            modal.style.display = '';
            requestNotifPermission();
            
            // Refresh data tab PIN state
            updateDataPinState();
        });
    }

    const closeModal = () => { if (modal) modal.style.display = 'none'; };
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (modal) modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    // Tab switching
    document.querySelectorAll('.settings-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.settings-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.settings-pane').forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            const target = document.getElementById(tab.dataset.tab);
            if (target) target.classList.add('active');
        });
    });

    // Theme toggle
    const btnTheme = document.getElementById('btn-settings-theme');
    if (btnTheme) {
        const updateThemeBtnText = () => {
            const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
            btnTheme.textContent = isDark ? '라이트 모드로 전환' : '다크 모드로 전환';
        };
        btnTheme.addEventListener('click', () => {
            const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
            document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
            localStorage.setItem('dustcheck-theme', isDark ? 'light' : 'dark');
            updateChartColors();
            const meta = document.querySelector('meta[name="theme-color"]');
            if (meta) meta.content = isDark ? '#f5f7fb' : '#0f1117';
            updateThemeBtnText();
        });
        updateThemeBtnText();
    }

    // Chart settings (tooltip time, midnight lines)
    const cbTooltipTime = document.getElementById('settings-tooltip-time');
    const cbMidnightLines = document.getElementById('settings-midnight-lines');
    if (cbTooltipTime) {
        cbTooltipTime.checked = chartSettings.showTimeInTooltip;
        cbTooltipTime.addEventListener('change', () => {
            chartSettings.showTimeInTooltip = cbTooltipTime.checked;
            localStorage.setItem('dustcheck-tooltip-time', cbTooltipTime.checked ? 'true' : 'false');
        });
    }
    if (cbMidnightLines) {
        cbMidnightLines.checked = chartSettings.showMidnightLines;
        cbMidnightLines.addEventListener('change', () => {
            chartSettings.showMidnightLines = cbMidnightLines.checked;
            localStorage.setItem('dustcheck-midnight-lines', cbMidnightLines.checked ? 'true' : 'false');
            if (chart) chart.update('none');
        });
    }

    // Notif test
    const testBtn = document.getElementById('btn-notif-test');
    if (testBtn) {
        testBtn.addEventListener('click', () => {
            sendNotification('🔔 테스트 알림', '알림이 정상적으로 작동합니다!');
        });
    }

    // Notif checkbox listeners
    document.querySelectorAll('.notif-check input').forEach(cb => {
        cb.addEventListener('change', () => {
            notifSettings[cb.dataset.key] = cb.checked;
            localStorage.setItem('dustcheck-notif', JSON.stringify(notifSettings));
        });
    });

    // Data Management
    const btnDelRange = document.getElementById('btn-delete-range');
    const btnDelAll = document.getElementById('btn-delete-all');
    if (btnDelRange) btnDelRange.addEventListener('click', deleteDataRange);
    if (btnDelAll) btnDelAll.addEventListener('click', deleteAllData);

    // Admin PIN Auth in Settings Modal
    const btnDataPinAuth = document.getElementById('btn-data-pin-auth');
    const btnDataPinLogout = document.getElementById('btn-data-pin-logout');
    const inputDataPin = document.getElementById('data-pin');

    if (btnDataPinAuth) {
        btnDataPinAuth.addEventListener('click', () => {
            const pinVal = inputDataPin ? inputDataPin.value : '';
            if (pinVal === MEMO_PIN) {
                memoAuthenticated = true;
                localStorage.setItem('dustcheck-authenticated', 'true');
                alert('관리자 모드로 인증되었습니다.');
                updateDataPinState();
                
                // Immediately refresh Memo List and Chart
                if (chart) chart.update('none');
                renderMemoList();
            } else {
                alert('PIN 번호가 올바르지 않습니다.');
            }
        });
    }

    if (inputDataPin && btnDataPinAuth) {
        inputDataPin.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                btnDataPinAuth.click();
            }
        });
    }

    if (btnDataPinLogout) {
        btnDataPinLogout.addEventListener('click', handlePinOut);
    }

    // Set default times for range deletion
    const endInput = document.getElementById('data-end-time');
    const startInput = document.getElementById('data-start-time');
    if (endInput && startInput) {
        const now = new Date();
        const localNow = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
        const localStart = new Date(localNow.getTime() - 3600000);
        endInput.value = localNow.toISOString().slice(0, 16);
        startInput.value = localStart.toISOString().slice(0, 16);
    }
}

function loadNotifSettings() {
    const saved = localStorage.getItem('dustcheck-notif');
    if (saved) {
        try { notifSettings = JSON.parse(saved); } catch(e) { notifSettings = {}; }
    }
    // Apply saved settings to checkboxes
    setTimeout(() => {
        document.querySelectorAll('.notif-check input').forEach(cb => {
            const key = cb.dataset.key;
            if (key in notifSettings) {
                cb.checked = notifSettings[key];
            } else {
                notifSettings[key] = cb.checked; // use default from HTML
            }
        });
    }, 0);
}

function loadMemoToggleSetting() {
    const showMemosCheckbox = document.getElementById('settings-show-memos');
    if (showMemosCheckbox) {
        showMemosCheckbox.checked = showMemos;
        showMemosCheckbox.addEventListener('change', () => {
            showMemos = showMemosCheckbox.checked;
            localStorage.setItem('dustcheck-show-memos', showMemos ? 'true' : 'false');
            applyMemoVisibility();
        });
    }
    applyMemoVisibility();
}

function applyMemoVisibility() {
    const btnAddMemo = document.getElementById('btn-add-memo');
    const memoSection = document.getElementById('memo-section');
    if (showMemos) {
        if (btnAddMemo) btnAddMemo.style.display = '';
        if (memoSection) memoSection.style.display = '';
    } else {
        if (btnAddMemo) btnAddMemo.style.display = 'none';
        if (memoSection) memoSection.style.display = 'none';
        // Also hide popover if any
        const pop = document.getElementById('memo-popover');
        if (pop) pop.style.display = 'none';
    }
    // Update chart to show/hide memo markers
    if (chart) {
        chart.update('none');
    }
}

function requestNotifPermission() {
    if (!('Notification' in window)) return;
    if (Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

function sendNotification(title, body) {
    if (!('Notification' in window) || Notification.permission !== 'granted') {
        // Fallback: alert
        if (Notification.permission === 'default') Notification.requestPermission();
        return;
    }
    new Notification(title, { body, icon: '🌬️' });
}

function checkNotification(data) {
    const pm25 = data.pm25 || 0;
    const pm10 = data.pm10 || 0;

    const curPm25 = getAirQuality('pm25', pm25);
    const curPm10 = getAirQuality('pm10', pm10);

    if (prevGrade.pm25 !== null) {
        const transKey25 = getTransitionKey('pm25', prevGrade.pm25, curPm25.label);
        if (transKey25 && notifSettings[transKey25]) {
            const isWorsen = isWorsening(prevGrade.pm25, curPm25.label);
            const icon = isWorsen ? '🚨' : '✅';
            const prefix = isWorsen ? '공기질 악화' : '공기질 개선';
            sendNotification(`${icon} ${prefix}`, `PM2.5가 ${curPm25.label} 단계(${pm25.toFixed(1)} μg/m³)로 변경되었습니다.`);
        }
    }
    if (prevGrade.pm10 !== null) {
        const transKey10 = getTransitionKey('pm10', prevGrade.pm10, curPm10.label);
        if (transKey10 && notifSettings[transKey10]) {
            const isWorsen = isWorsening(prevGrade.pm10, curPm10.label);
            const icon = isWorsen ? '🚨' : '✅';
            const prefix = isWorsen ? '공기질 악화' : '공기질 개선';
            sendNotification(`${icon} ${prefix}`, `PM10이 ${curPm10.label} 단계(${pm10.toFixed(1)} μg/m³)로 변경되었습니다.`);
        }
    }

    prevGrade.pm25 = curPm25.label;
    prevGrade.pm10 = curPm10.label;
}

function getTransitionKey(type, fromLabel, toLabel) {
    if (fromLabel === toLabel) return null;
    const map = {
        '좋음_보통': 'good_normal', '보통_나쁨': 'normal_bad', '나쁨_매우나쁨': 'bad_vbad',
        '나쁨_보통': 'bad_normal', '보통_좋음': 'normal_good',
        '매우나쁨_나쁨': 'bad_normal', // map vbad→bad same as bad→normal for simplicity
    };
    const key = `${fromLabel}_${toLabel}`;
    const mapped = map[key];
    return mapped ? `${type}_${mapped}` : null;
}

function isWorsening(fromLabel, toLabel) {
    const order = ['좋음', '보통', '나쁨', '매우나쁨'];
    return order.indexOf(toLabel) > order.indexOf(fromLabel);
}

// ─── Status ───
let lastUpdateTime = null;
let statusShowAbsolute = false; // false = relative ("1분 전"), true = absolute ("2026-05-18 11:32:01")

function initStatusToggle() {
    const statusEl = document.querySelector('.header__status');
    if (!statusEl) return;
    statusEl.style.cursor = 'pointer';
    statusEl.title = '클릭하여 시간 표시 전환';
    statusEl.addEventListener('click', () => {
        if (!lastUpdateTime) return;
        statusShowAbsolute = !statusShowAbsolute;
        refreshStatusText();
    });
}

function refreshStatusText() {
    const text = document.getElementById('status-text');
    if (!text || !lastUpdateTime) return;
    if (statusShowAbsolute) {
        text.textContent = `마지막 업데이트: ${lastUpdateTime}`;
    } else {
        text.textContent = `마지막 업데이트: ${getRelativeTime(lastUpdateTime)}`;
    }
}

function updateStatus(online, lastTime) {
    const dot = document.getElementById('status-dot');
    const text = document.getElementById('status-text');
    if (dot) dot.className = online ? 'status-dot' : 'status-dot offline';
    if (lastTime) lastUpdateTime = lastTime;
    if (text) {
        if (online && lastTime) {
            refreshStatusText();
        } else if (online) {
            text.textContent = '연결 중...';
        } else {
            text.textContent = '오프라인 (데모 모드)';
        }
    }
}

function getRelativeTime(timeStr) {
    try {
        const d = new Date(timeStr.replace(' ', 'T'));
        const diff = Math.floor((Date.now() - d.getTime()) / 1000);
        if (diff < 10) return '방금 전';
        if (diff < 60) return `${diff}초 전`;
        if (diff < 3600) return `${Math.floor(diff / 60)}분 전`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}시간 전`;
        return timeStr;
    } catch (e) {
        return timeStr;
    }
}

function startRelativeTimeUpdater() {
    setInterval(() => {
        if (lastUpdateTime && !statusShowAbsolute) {
            refreshStatusText();
        }
    }, 10000);
}

// ─── Demo Data ───
function showDemoData() {
    updateCurrentDisplay({ pm1: 8.2, pm25: 12.4, pm4: 14.7, pm10: 18.3, time: new Date().toLocaleString('ko-KR') });
    allData = [];
    for (let i = 29; i >= 0; i--) {
        const t = new Date(Date.now() - i * 60000);
        allData.push({
            time: t.toISOString().replace('T', ' ').slice(0, 19),
            timestamp: t.getTime(),
            pm1: 5 + Math.random() * 15,
            pm25: 10 + Math.random() * 20,
            pm4: 12 + Math.random() * 22,
            pm10: 15 + Math.random() * 25,
        });
    }
    updateChart();
}

// ─── Memo System ───
function initMemos() {
    // Listen for memos from Firebase
    const db = firebase.database();
    db.ref('memos').on('value', snap => {
        memos = [];
        if (snap.exists()) {
            snap.forEach(child => {
                memos.push({ id: child.key, ...child.val() });
            });
        }
        if (chart) chart.update('none');
        renderMemoList();
    });

    // Modal open
    const btnAdd = document.getElementById('btn-add-memo');
    if (btnAdd) btnAdd.addEventListener('click', () => openMemoModal());

    // Modal close
    const btnClose = document.getElementById('memo-modal-close');
    const btnCancel = document.getElementById('memo-cancel');
    if (btnClose) btnClose.addEventListener('click', closeMemoModal);
    if (btnCancel) btnCancel.addEventListener('click', closeMemoModal);

    // Modal save
    const btnSave = document.getElementById('memo-save');
    if (btnSave) btnSave.addEventListener('click', saveMemo);

    // Popover close
    const popClose = document.getElementById('memo-popover-close');
    if (popClose) popClose.addEventListener('click', () => {
        document.getElementById('memo-popover').style.display = 'none';
    });

    // Close popover on outside click
    document.addEventListener('click', (e) => {
        const pop = document.getElementById('memo-popover');
        if (pop && pop.style.display !== 'none' && !pop.contains(e.target)) {
            pop.style.display = 'none';
        }
    });

    // Overlay click to close modal
    const modal = document.getElementById('memo-modal');
    if (modal) modal.addEventListener('click', (e) => {
        if (e.target === modal) closeMemoModal();
    });
}

function verifyAdminPin() {
    if (memoAuthenticated) return true;
    const pinVal = document.getElementById('data-pin').value;
    if (pinVal === MEMO_PIN) {
        memoAuthenticated = true;
        localStorage.setItem('dustcheck-authenticated', 'true');
        
        // Update PIN state in settings panel
        updateDataPinState();
        
        // Immediately refresh Memo List and Chart
        if (chart) chart.update('none');
        renderMemoList();
        return true;
    }
    alert('PIN 번호가 올바르지 않습니다.');
    return false;
}

function deleteDataEntry(ts) {
    if (!memoAuthenticated) {
        const pin = prompt('데이터 삭제를 위해 관리자 PIN을 입력하세요:');
        if (pin !== MEMO_PIN) {
            alert('PIN 번호가 올바르지 않습니다.');
            return;
        }
        memoAuthenticated = true;
        localStorage.setItem('dustcheck-authenticated', 'true');
        if (chart) chart.update('none');
        renderMemoList();
    }
    if (confirm('해당 측정 기록을 삭제하시겠습니까?')) {
        firebase.database().ref('dust_data').orderByChild('timestamp').equalTo(Number(ts)).once('value', snap => {
            if (snap.exists()) {
                const updates = {};
                snap.forEach(child => { updates[child.key] = null; });
                firebase.database().ref('dust_data').update(updates);
            }
        });
    }
}

function deleteDataRange() {
    if (!verifyAdminPin()) return;
    const startVal = document.getElementById('data-start-time').value;
    const endVal = document.getElementById('data-end-time').value;
    if (!startVal || !endVal) {
        alert('시작 시간과 종료 시간을 모두 선택해주세요.');
        return;
    }

    const startTs = new Date(startVal).getTime();
    const endTs = new Date(endVal).getTime();
    if (startTs >= endTs) {
        alert('종료 시간이 시작 시간보다 빨라야 합니다.');
        return;
    }

    if (confirm('지정된 구간의 데이터를 모두 삭제하시겠습니까?\n이 작업은 복구할 수 없습니다.')) {
        const db = firebase.database();
        db.ref('dust_data').orderByChild('timestamp').startAt(startTs).endAt(endTs).once('value', snap => {
            if (snap.exists()) {
                const updates = {};
                snap.forEach(child => { updates[child.key] = null; });
                db.ref('dust_data').update(updates).then(() => {
                    alert('구간 데이터가 삭제되었습니다.');
                    const modal = document.getElementById('settings-modal');
                    if (modal) modal.style.display = 'none';
                });
            } else {
                alert('해당 구간에 삭제할 데이터가 없습니다.');
            }
        });
    }
}

function deleteAllData() {
    if (!verifyAdminPin()) return;
    if (confirm('⚠️ 정말로 모든 센서 데이터를 영구적으로 삭제하시겠습니까?\n이 작업은 절대 복구할 수 없습니다!')) {
        const db = firebase.database();
        db.ref('dust_data').remove().then(() => {
            alert('모든 데이터가 삭제되었습니다.');
            const modal = document.getElementById('settings-modal');
            if (modal) modal.style.display = 'none';
            location.reload(); // Reload to clear local cached arrays
        }).catch(err => {
            alert('삭제 실패: ' + err.message);
        });
    }
}

function openMemoModal(timeStr = null, editId = null, text = null) {
    const modal = document.getElementById('memo-modal');
    const timeInput = document.getElementById('memo-time');
    const textInput = document.getElementById('memo-text');
    const errorEl = document.getElementById('memo-error');
    const pinGroup = document.getElementById('memo-pin-group');
    const isPrivateCheckbox = document.getElementById('memo-is-private');

    editingMemoId = editId;

    if (timeStr && timeStr.length >= 16) {
        timeInput.value = timeStr.slice(0, 10) + 'T' + timeStr.slice(11, 16);
    } else {
        const now = new Date();
        const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
        timeInput.value = local.toISOString().slice(0, 16);
    }
    
    textInput.value = text || '';
    errorEl.style.display = 'none';

    // Set private checkbox status
    if (editingMemoId && isPrivateCheckbox) {
        const memo = memos.find(m => m.id === editingMemoId);
        isPrivateCheckbox.checked = memo ? !!memo.isPrivate : false;
    } else if (isPrivateCheckbox) {
        isPrivateCheckbox.checked = false;
    }

    if (memoAuthenticated) {
        pinGroup.style.display = 'none';
    } else {
        pinGroup.style.display = '';
        document.getElementById('memo-pin').value = '';
    }

    modal.style.display = '';
}

function openMemoModalWithTime(timeStr) {
    openMemoModal(timeStr);
}

function closeMemoModal() {
    editingMemoId = null;
    document.getElementById('memo-modal').style.display = 'none';
}

function saveMemo() {
    const timeVal = document.getElementById('memo-time').value;
    const textVal = document.getElementById('memo-text').value.trim();
    const pinVal = document.getElementById('memo-pin').value;
    const errorEl = document.getElementById('memo-error');
    const isPrivateCheckbox = document.getElementById('memo-is-private');
    const isPrivateVal = isPrivateCheckbox ? isPrivateCheckbox.checked : false;

    // Validate
    if (!timeVal) { showMemoError('시간을 선택해주세요.'); return; }
    if (!textVal) { showMemoError('메모 내용을 입력해주세요.'); return; }

    // PIN check
    if (!memoAuthenticated) {
        if (pinVal !== MEMO_PIN) {
            showMemoError('PIN 번호가 올바르지 않습니다.'); return;
        }
        memoAuthenticated = true;
        localStorage.setItem('dustcheck-authenticated', 'true');
        
        // Update other views immediately
        if (chart) chart.update('none');
        renderMemoList();
        const pinGroup = document.getElementById('data-pin-group');
        if (pinGroup) pinGroup.style.display = 'none';
    }

    // Build time string in "YYYY-MM-DD HH:MM:SS" format
    const dt = new Date(timeVal);
    const timeStr = dt.getFullYear() + '-' +
        String(dt.getMonth() + 1).padStart(2, '0') + '-' +
        String(dt.getDate()).padStart(2, '0') + ' ' +
        String(dt.getHours()).padStart(2, '0') + ':' +
        String(dt.getMinutes()).padStart(2, '0') + ':00';

    // Save to Firebase
    const db = firebase.database();
    const memoData = {
        text: textVal,
        time: timeStr,
        timestamp: dt.getTime(),
        isPrivate: isPrivateVal,
    };

    if (editingMemoId) {
        db.ref('memos/' + editingMemoId).update(memoData).then(() => {
            closeMemoModal();
        }).catch(err => {
            showMemoError('저장 실패: ' + err.message);
        });
    } else {
        db.ref('memos').push(memoData).then(() => {
            closeMemoModal();
        }).catch(err => {
            showMemoError('저장 실패: ' + err.message);
        });
    }
}

function showMemoError(msg) {
    const el = document.getElementById('memo-error');
    el.textContent = msg;
    el.style.display = '';
}

function handleChartMemoHover(e) {
    if (!showMemos || !memos.length || !chart) return;
    const hoverX = e.x !== undefined ? e.x : (e.native ? e.native.offsetX : 0);
    const hoverY = e.y !== undefined ? e.y : (e.native ? e.native.offsetY : 0);

    const hitMemo = memos.find(m => {
        if (m._pixelX == null) return false;
        if (m.isPrivate && !memoAuthenticated) return false;
        return Math.abs(m._pixelX - hoverX) < 15 && hoverY < (m._chartTop || 50) + 30;
    });

    const pop = document.getElementById('memo-popover');
    if (!pop) return;

    if (hitMemo) {
        chart.canvas.style.cursor = 'pointer';
        document.getElementById('memo-popover-time').textContent = hitMemo.time;
        document.getElementById('memo-popover-text').textContent = hitMemo.text;

        const canvasRect = chart.canvas.getBoundingClientRect();
        let left = canvasRect.left + hitMemo._pixelX;
        let top = canvasRect.top + (hitMemo._chartTop || 20) - 60;
        if (left + 260 > window.innerWidth) left = window.innerWidth - 280;
        if (left < 10) left = 10;
        if (top < 10) top = canvasRect.top + (hitMemo._chartTop || 20) + 30;

        pop.style.left = left + 'px';
        pop.style.top = top + 'px';
        pop.style.display = 'block';
    } else {
        chart.canvas.style.cursor = 'default';
        pop.style.display = 'none';
    }
}

function handleChartMemoClick(e) {
    if (!showMemos || !memos.length || !chart) return false;
    const clickX = e.x !== undefined ? e.x : (e.native ? e.native.offsetX : 0);
    const clickY = e.y !== undefined ? e.y : (e.native ? e.native.offsetY : 0);

    const hitMemo = memos.find(m => {
        if (m._pixelX == null) return false;
        if (m.isPrivate && !memoAuthenticated) return false;
        return Math.abs(m._pixelX - clickX) < 15 && clickY < (m._chartTop || 50) + 30;
    });

    if (!hitMemo) return false;

    // Show popover (also handled by hover, but kept for mobile/click intent)
    const pop = document.getElementById('memo-popover');
    if (!pop) return true;
    document.getElementById('memo-popover-time').textContent = hitMemo.time;
    document.getElementById('memo-popover-text').textContent = hitMemo.text;

    const canvasRect = chart.canvas.getBoundingClientRect();
    let left = canvasRect.left + hitMemo._pixelX;
    let top = canvasRect.top + (hitMemo._chartTop || 20) - 60;
    if (left + 260 > window.innerWidth) left = window.innerWidth - 280;
    if (left < 10) left = 10;
    if (top < 10) top = canvasRect.top + (hitMemo._chartTop || 20) + 30;

    pop.style.left = left + 'px';
    pop.style.top = top + 'px';
    pop.style.display = 'block';
    return true;
}

function handleChartTimeClick(e) {
    if (!showMemos) return;
    if (!chart || !chart._rawTimestamps) return;
    const clickX = e.x !== undefined ? e.x : (e.native ? e.native.offsetX : 0);
    const xScale = chart.scales.x;
    if (!xScale) return;

    // Map pixel X to nearest data index
    const idx = Math.round(xScale.getValueForPixel(clickX));
    const ts = chart._rawTimestamps[idx];
    if (!ts) return;

    const dt = new Date(ts);
    const timeStr = dt.getFullYear() + '-' +
        String(dt.getMonth() + 1).padStart(2, '0') + '-' +
        String(dt.getDate()).padStart(2, '0') + ' ' +
        String(dt.getHours()).padStart(2, '0') + ':' +
        String(dt.getMinutes()).padStart(2, '0') + ':' +
        String(dt.getSeconds()).padStart(2, '0');

    openMemoModalWithTime(timeStr);
}

// ─── Memo List ───
function renderMemoList() {
    const listEl = document.getElementById('memo-list-body');
    if (!listEl) return;

    // Filter out private memos if not authenticated
    const visibleMemos = memos.filter(m => memoAuthenticated || !m.isPrivate);

    let html = '';

    // Render the unlock / session status bar
    if (memoAuthenticated) {
        html += `
            <div class="memo-unlock-bar">
                <div class="memo-unlock-bar__status">
                    <span>🔓 <strong>관리자 모드</strong> (비공개 메모 활성화됨)</span>
                </div>
                <button class="btn-secondary" id="btn-pin-out" style="padding: 4px 10px; font-size: 0.78rem; border-color: #ef4444; color: #ef4444; margin-top: 0; margin-bottom: 0;">로그아웃 (PIN Out)</button>
            </div>
        `;
    } else {
        html += `
            <div class="memo-unlock-bar">
                <div class="memo-unlock-bar__status">
                    <span>🔒 <strong>게스트 모드</strong> (비공개 메모 숨김됨)</span>
                </div>
                <div class="memo-unlock-bar__form">
                    <input type="password" id="memo-list-pin" placeholder="PIN 입력" style="padding: 4px 8px; font-size: 0.78rem; width: 80px; border: 1.5px solid var(--border-card); border-radius: 6px; background: var(--bg-input); color: var(--text-primary); outline: none;" maxlength="8">
                    <button class="btn-primary" id="btn-pin-in" style="padding: 4px 10px; font-size: 0.78rem; background: #8b5cf6; color: white; border: none; border-radius: 6px; cursor: pointer;">인증</button>
                </div>
            </div>
        `;
    }

    if (visibleMemos.length === 0) {
        html += '<p style="text-align:center;color:var(--text-dim);padding:16px;font-size:0.85rem">메모가 없습니다. 차트나 테이블을 클릭하여 메모를 추가하세요.</p>';
        listEl.innerHTML = html;
        attachUnlockBarHandlers();
        return;
    }

    const sorted = [...visibleMemos].sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
    
    html += `
        <div class="memo-list-actions">
            <label class="memo-check-all"><input type="checkbox" id="memo-check-all-cb"> 전체 선택</label>
            <button class="btn-secondary btn-sm" id="memo-bulk-delete" style="padding:4px 8px; font-size:0.75rem;">선택 삭제</button>
        </div>
    `;

    html += sorted.map(m => {
        const badgeClass = m.isPrivate ? 'private' : 'public';
        const badgeLabel = m.isPrivate ? '비공개' : '공개';
        return `
            <div class="memo-item" data-id="${m.id}">
                <input type="checkbox" class="memo-select-cb" data-id="${m.id}">
                <div class="memo-item__info">
                    <div style="display:flex; align-items:center; gap:6px;">
                        <span class="memo-item__time">${m.time || ''}</span>
                        <span class="memo-badge ${badgeClass}">${badgeLabel}</span>
                    </div>
                    <span class="memo-item__text">${m.text || ''}</span>
                </div>
                <div class="memo-item__actions">
                    <button class="memo-item__btn memo-edit-btn" data-id="${m.id}" title="편집">✏️</button>
                    <button class="memo-item__btn memo-delete-btn" data-id="${m.id}" title="삭제">🗑️</button>
                </div>
            </div>
        `;
    }).join('');
    
    listEl.innerHTML = html;

    // Attach edit/delete handlers
    listEl.querySelectorAll('.memo-delete-btn').forEach(btn => {
        btn.addEventListener('click', () => deleteMemo(btn.dataset.id));
    });
    listEl.querySelectorAll('.memo-edit-btn').forEach(btn => {
        btn.addEventListener('click', () => editMemo(btn.dataset.id));
    });

    // Bulk actions
    const checkAll = document.getElementById('memo-check-all-cb');
    const cbs = listEl.querySelectorAll('.memo-select-cb');
    const bulkDel = document.getElementById('memo-bulk-delete');

    if (checkAll) {
        checkAll.addEventListener('change', (e) => {
            cbs.forEach(cb => cb.checked = e.target.checked);
        });
    }

    if (bulkDel) {
        bulkDel.addEventListener('click', () => {
            const selectedIds = Array.from(cbs).filter(cb => cb.checked).map(cb => cb.dataset.id);
            if (selectedIds.length === 0) return;
            if (confirm(`선택한 ${selectedIds.length}개의 메모를 삭제하시겠습니까?`)) {
                if (!memoAuthenticated) {
                    const pin = prompt("PIN 번호를 입력하세요:");
                    if (pin !== MEMO_PIN) { alert("PIN 번호가 올바르지 않습니다."); return; }
                    memoAuthenticated = true;
                    localStorage.setItem('dustcheck-authenticated', 'true');
                    
                    // Update views
                    if (chart) chart.update('none');
                    const pinGroup = document.getElementById('data-pin-group');
                    if (pinGroup) pinGroup.style.display = 'none';
                }
                const updates = {};
                selectedIds.forEach(id => updates[id] = null);
                firebase.database().ref('memos').update(updates);
            }
        });
    }

    attachUnlockBarHandlers();
}

function attachUnlockBarHandlers() {
    const btnPinOut = document.getElementById('btn-pin-out');
    if (btnPinOut) {
        btnPinOut.addEventListener('click', handlePinOut);
    }

    const btnPinIn = document.getElementById('btn-pin-in');
    const inputPin = document.getElementById('memo-list-pin');
    if (btnPinIn && inputPin) {
        const tryPinIn = () => {
            const val = inputPin.value;
            if (val === MEMO_PIN) {
                memoAuthenticated = true;
                localStorage.setItem('dustcheck-authenticated', 'true');
                alert('관리자 모드로 인증되었습니다.');
                
                // Immediately refresh PIN input display in Settings modal data tab
                const pinGroup = document.getElementById('data-pin-group');
                if (pinGroup) pinGroup.style.display = 'none';
                
                // Update views
                if (chart) chart.update('none');
                renderMemoList();
            } else {
                alert('PIN 번호가 올바르지 않습니다.');
            }
        };

        btnPinIn.addEventListener('click', tryPinIn);
        inputPin.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') tryPinIn();
        });
    }
}

function handlePinOut() {
    memoAuthenticated = false;
    localStorage.removeItem('dustcheck-authenticated');
    alert('관리자 모드에서 로그아웃되었습니다.');
    
    // Immediately refresh PIN input display in Settings modal data tab
    updateDataPinState();
    
    // Update views
    if (chart) chart.update('none');
    renderMemoList();
}

function editMemo(id) {
    const memo = memos.find(m => m.id === id);
    if (!memo) return;
    openMemoModal(memo.time, memo.id, memo.text);
}

function deleteMemo(id) {
    if (confirm('이 메모를 삭제하시겠습니까?')) {
        if (!memoAuthenticated) {
            const pin = prompt("PIN 번호를 입력하세요:");
            if (pin !== MEMO_PIN) { alert("PIN 번호가 올바르지 않습니다."); return; }
            memoAuthenticated = true;
            localStorage.setItem('dustcheck-authenticated', 'true');
            if (chart) chart.update('none');
            renderMemoList();
            const pinGroup = document.getElementById('data-pin-group');
            if (pinGroup) pinGroup.style.display = 'none';
        }
        firebase.database().ref('memos/' + id).remove();
    }
}

