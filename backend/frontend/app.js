/* ═══════════════════════════════════════════════════════════════════
   Personal AI Astrologer — Application Logic
   ═══════════════════════════════════════════════════════════════════ */

(function () {
    'use strict';

    /* ─── State ─────────────────────────────────────────────── */
    const state = {
        selectedSystem: null,
        chartData: null,        // raw chart computation data
        analysisData: null,     // horoscope analysis response
    };

    /* ─── DOM References ────────────────────────────────────── */
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    const stepSystem = $('#step-system');
    const stepDetails = $('#step-details');
    const stepResults = $('#step-results');

    const systemCards = $$('.system-card');
    const birthForm = $('#birth-form');
    const btnBackStep1 = $('#btn-back-step1');
    const btnGenerate = $('#btn-generate');
    const btnNewReading = $('#btn-new-reading');
    const btnDownload = $('#btn-download');

    /* ─── Star Background ───────────────────────────────────── */
    function initStarCanvas() {
        const canvas = $('#star-canvas');
        const ctx = canvas.getContext('2d');
        let w, h, stars = [];

        function resize() {
            w = canvas.width = window.innerWidth;
            h = canvas.height = window.innerHeight;
        }

        function createStars() {
            stars = [];
            const count = Math.floor((w * h) / 4000);
            for (let i = 0; i < count; i++) {
                stars.push({
                    x: Math.random() * w,
                    y: Math.random() * h,
                    r: Math.random() * 1.5 + 0.3,
                    alpha: Math.random() * 0.8 + 0.2,
                    speed: Math.random() * 0.0015 + 0.0005,
                    phase: Math.random() * Math.PI * 2,
                });
            }
        }

        function draw(t) {
            ctx.clearRect(0, 0, w, h);
            for (const s of stars) {
                const a = s.alpha * (0.5 + 0.5 * Math.sin(t * s.speed + s.phase));
                ctx.beginPath();
                ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(200, 200, 255, ${a})`;
                ctx.fill();
            }
            requestAnimationFrame(draw);
        }

        resize();
        createStars();
        requestAnimationFrame(draw);
        window.addEventListener('resize', () => { resize(); createStars(); });
    }

    /* ─── Coordinate Formatting & Parsing ────────────────────── */
    function formatLat(lat) {
        const dir = lat >= 0 ? 'N' : 'S';
        return `${Math.abs(lat).toFixed(2)}° ${dir}`;
    }

    function formatLon(lon) {
        const dir = lon >= 0 ? 'E' : 'W';
        return `${Math.abs(lon).toFixed(2)}° ${dir}`;
    }

    function formatCoords(lat, lon) {
        return `${formatLat(lat)}, ${formatLon(lon)}`;
    }

    function parseLat(str) {
        if (typeof str === 'number') return Math.max(-90, Math.min(90, str));
        if (!str || typeof str !== 'string') return null;
        const clean = str.trim().toUpperCase();
        const isSouth = clean.includes('S') || clean.startsWith('-');
        const num = parseFloat(clean.replace(/[^0-9.]/g, ''));
        if (isNaN(num)) return null;
        const val = isSouth ? -num : num;
        return Math.max(-90, Math.min(90, val));
    }

    function parseLon(str) {
        if (typeof str === 'number') return Math.max(-180, Math.min(180, str));
        if (!str || typeof str !== 'string') return null;
        const clean = str.trim().toUpperCase();
        const isWest = clean.includes('W') || clean.startsWith('-');
        const num = parseFloat(clean.replace(/[^0-9.]/g, ''));
        if (isNaN(num)) return null;
        const val = isWest ? -num : num;
        return Math.max(-180, Math.min(180, val));
    }

    /* ─── Map & Pinpoint Engine ─────────────────────────────── */
    let locationMap = null;
    let locationMarker = null;

    function updateCoordinates(lat, lon, moveMap = true, lookupTz = true) {
        lat = Math.max(-90, Math.min(90, lat));
        lon = Math.max(-180, Math.min(180, lon));

        const latInput = $('#input-latitude');
        const lonInput = $('#input-longitude');
        const latStrInput = $('#input-latitude-str');
        const lonStrInput = $('#input-longitude-str');
        const badgeText = $('#badge-coords-text');

        if (latInput) latInput.value = lat.toFixed(4);
        if (lonInput) lonInput.value = lon.toFixed(4);
        if (latStrInput) latStrInput.value = formatLat(lat);
        if (lonStrInput) lonStrInput.value = formatLon(lon);
        if (badgeText) badgeText.textContent = formatCoords(lat, lon);

        if (locationMarker) {
            locationMarker.setLatLng([lat, lon]);
        }
        if (moveMap && locationMap) {
            locationMap.panTo([lat, lon]);
        }
        if (lookupTz) {
            lookupTimezoneForCoords(lat, lon);
        }
    }

    async function lookupTimezoneForCoords(lat, lon) {
        try {
            const dateVal = $('#input-date') ? $('#input-date').value : '';
            const timeVal = $('#input-time') ? $('#input-time').value : '';
            let url = `/api/v1/charts/timezone-lookup?latitude=${lat}&longitude=${lon}`;
            if (dateVal) url += `&date=${dateVal}`;
            if (timeVal) url += `&time=${timeVal}`;

            const res = await fetch(url);
            if (res.ok) {
                const data = await res.json();
                const tzSelect = $('#input-timezone');
                if (tzSelect && data.utc_offset !== undefined) {
                    const targetOffset = data.utc_offset;
                    let bestOpt = null;
                    let minDiff = Infinity;
                    for (const opt of tzSelect.options) {
                        const diff = Math.abs(parseFloat(opt.value) - targetOffset);
                        if (diff < minDiff) {
                            minDiff = diff;
                            bestOpt = opt;
                        }
                    }
                    if (bestOpt && minDiff <= 0.1) {
                        tzSelect.value = bestOpt.value;
                    }
                }
            }
        } catch { /* optional */ }
    }

    function initLocationMap() {
        const mapEl = $('#birth-location-map');
        if (!mapEl || typeof L === 'undefined') return;
        if (locationMap) return;

        const defaultLat = 28.6139;
        const defaultLng = 77.2090;

        locationMap = L.map('birth-location-map', {
            center: [defaultLat, defaultLng],
            zoom: 5,
            zoomControl: true,
        });

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            maxZoom: 18,
        }).addTo(locationMap);

        const celestialIcon = L.divIcon({
            className: 'custom-celestial-pin',
            html: '<div class="pin-pulse"></div><div class="pin-core"></div>',
            iconSize: [28, 28],
            iconAnchor: [14, 14],
        });

        locationMarker = L.marker([defaultLat, defaultLng], {
            icon: celestialIcon,
            draggable: true,
        }).addTo(locationMap);

        locationMarker.on('dragend', (e) => {
            const pos = e.target.getLatLng();
            updateCoordinates(pos.lat, pos.lng, false, true);
        });

        locationMap.on('click', (e) => {
            updateCoordinates(e.latlng.lat, e.latlng.lng, true, true);
        });

        updateCoordinates(defaultLat, defaultLng, false, false);
    }

    function initPlaceSearch() {
        const searchInput = $('#input-place-search');
        const btnSearch = $('#btn-search-place');
        const btnClear = $('#btn-clear-place');
        const suggestionsList = $('#place-suggestions');

        if (!searchInput) return;

        let debounceTimer = null;

        async function performSearch(query) {
            if (!query || query.trim().length < 2) {
                suggestionsList.style.display = 'none';
                suggestionsList.innerHTML = '';
                return;
            }

            try {
                const res = await fetch(`/api/v1/charts/geo-search?q=${encodeURIComponent(query.trim())}`);
                if (!res.ok) return;
                const places = await res.json();
                renderSuggestions(places);
            } catch (err) {
                console.warn('Place search error:', err);
            }
        }

        function renderSuggestions(places) {
            if (!places || places.length === 0) {
                suggestionsList.style.display = 'none';
                suggestionsList.innerHTML = '';
                return;
            }

            suggestionsList.innerHTML = places.map((p, i) => `
                <li class="place-suggestion-item" data-index="${i}">
                    <span class="place-item-name">${escHtml(p.short_name)}</span>
                    <span class="place-item-coords">📍 Decimal Coordinates: ${escHtml(p.formatted_coordinates)}</span>
                </li>
            `).join('');

            suggestionsList.style.display = 'block';

            suggestionsList.querySelectorAll('.place-suggestion-item').forEach(item => {
                item.addEventListener('click', () => {
                    const idx = parseInt(item.dataset.index);
                    const place = places[idx];
                    if (place) {
                        selectPlace(place);
                    }
                });
            });
        }

        function selectPlace(place) {
            searchInput.value = place.short_name;
            suggestionsList.style.display = 'none';
            if (btnClear) btnClear.style.display = 'inline-block';

            if (locationMap) {
                locationMap.flyTo([place.latitude, place.longitude], 10, { duration: 1.2 });
            }
            updateCoordinates(place.latitude, place.longitude, false, true);
        }

        searchInput.addEventListener('input', (e) => {
            const val = e.target.value;
            if (btnClear) btnClear.style.display = val ? 'inline-block' : 'none';
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => performSearch(val), 350);
        });

        if (btnSearch) {
            btnSearch.addEventListener('click', () => {
                performSearch(searchInput.value);
            });
        }

        if (btnClear) {
            btnClear.addEventListener('click', () => {
                searchInput.value = '';
                btnClear.style.display = 'none';
                suggestionsList.style.display = 'none';
                searchInput.focus();
            });
        }

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.place-search-container')) {
                suggestionsList.style.display = 'none';
            }
        });

        const latStrInput = $('#input-latitude-str');
        const lonStrInput = $('#input-longitude-str');

        if (latStrInput) {
            latStrInput.addEventListener('change', () => {
                const parsed = parseLat(latStrInput.value);
                const currentLon = parseLon($('#input-longitude-str') ? $('#input-longitude-str').value : '77.21° E') ?? 77.2090;
                if (parsed !== null) {
                    updateCoordinates(parsed, currentLon, true, true);
                } else {
                    latStrInput.value = formatLat(parseFloat($('#input-latitude').value) || 28.6139);
                }
            });
        }

        if (lonStrInput) {
            lonStrInput.addEventListener('change', () => {
                const currentLat = parseLat($('#input-latitude-str') ? $('#input-latitude-str').value : '28.61° N') ?? 28.6139;
                const parsed = parseLon(lonStrInput.value);
                if (parsed !== null) {
                    updateCoordinates(currentLat, parsed, true, true);
                } else {
                    lonStrInput.value = formatLon(parseFloat($('#input-longitude').value) || 77.2090);
                }
            });
        }
    }

    /* ─── Step Navigation ───────────────────────────────────── */
    function showStep(step) {
        [stepSystem, stepDetails, stepResults].forEach(s => s.classList.remove('active-step'));
        step.classList.add('active-step');
        window.scrollTo({ top: 0, behavior: 'smooth' });

        if (step === stepDetails) {
            setTimeout(() => {
                if (locationMap) {
                    locationMap.invalidateSize();
                } else {
                    initLocationMap();
                }
            }, 250);
        }
    }

    /* ─── System Selection ──────────────────────────────────── */
    function handleSystemSelect(system) {
        state.selectedSystem = system;
        systemCards.forEach(card => {
            card.classList.toggle('selected', card.dataset.system === system);
        });

        // Update form based on system
        const ayanamsaGroup = $('#ayanamsa-group');
        const houseSystemGroup = $('#house-system-group');
        const ayanamsaSelect = $('#input-ayanamsa');
        const houseSelect = $('#input-house-system');

        if (system === 'vedic') {
            ayanamsaGroup.style.display = '';
            houseSystemGroup.style.display = '';
            ayanamsaSelect.value = 'lahiri';
            houseSelect.value = 'whole_sign';
        } else if (system === 'kp') {
            ayanamsaGroup.style.display = '';
            houseSystemGroup.style.display = '';
            ayanamsaSelect.value = 'krishnamurti';
            houseSelect.value = 'placidus';
        } else {
            ayanamsaGroup.style.display = 'none';
            houseSystemGroup.style.display = '';
            houseSelect.value = 'placidus';
        }

        // Auto-advance to step 2
        setTimeout(() => showStep(stepDetails), 300);
    }

    systemCards.forEach(card => {
        card.addEventListener('click', () => handleSystemSelect(card.dataset.system));
    });

    btnBackStep1.addEventListener('click', () => showStep(stepSystem));
    btnNewReading.addEventListener('click', () => showStep(stepSystem));

    /* ─── Form Submission ───────────────────────────────────── */
    birthForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await generateHoroscope();
    });

    async function generateHoroscope() {
        const name = $('#input-name').value.trim() || 'Native';
        const date = $('#input-date').value;
        const time = $('#input-time').value;
        const tz = parseFloat($('#input-timezone').value);

        // Parse coordinates from decimal directional format
        const latStr = $('#input-latitude-str') ? $('#input-latitude-str').value : '';
        const lngStr = $('#input-longitude-str') ? $('#input-longitude-str').value : '';
        let lat = parseLat(latStr);
        let lng = parseLon(lngStr);
        if (lat === null) lat = parseFloat($('#input-latitude').value);
        if (lng === null) lng = parseFloat($('#input-longitude').value);

        const focus = $('#input-focus').value;

        if (!date || !time || isNaN(lat) || isNaN(lng)) {
            alert('Please fill in all required fields.');
            return;
        }

        // Compute UTC datetime
        const localDt = new Date(`${date}T${time}`);
        const utcMs = localDt.getTime() - (tz * 3600 * 1000);
        const utcDt = new Date(utcMs);
        const utcIso = utcDt.toISOString().replace('Z', '');

        // Build request payload
        const system = state.selectedSystem;
        const payload = {
            name: name,
            utc_datetime: utcIso,
            latitude: lat,
            longitude: lng,
            system: system,
            focus: focus,
            ayanamsa: system === 'western' ? 'lahiri' : $('#input-ayanamsa').value,
            house_system: $('#input-house-system').value,
            language: 'en',
        };

        // UI feedback
        const btnText = btnGenerate.querySelector('.btn-text');
        const btnLoader = btnGenerate.querySelector('.btn-loader');
        btnText.style.display = 'none';
        btnLoader.style.display = 'inline-flex';
        btnGenerate.disabled = true;

        try {
            // Call the analysis endpoint
            const endpoint = focus === 'life_blueprint'
                ? '/api/v1/analysis/life-blueprint'
                : '/api/v1/analysis/horoscope';

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData?.error?.message || `Server error: ${response.status}`);
            }

            state.analysisData = await response.json();

            // Also get raw chart data for visualization
            try {
                const chartResp = await fetch('/api/v1/charts/calculate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        utc_datetime: utcIso,
                        latitude: lat,
                        longitude: lng,
                        astrology_system: system,
                        house_system: payload.house_system,
                        ayanamsa: payload.ayanamsa,
                    }),
                });
                if (chartResp.ok) {
                    state.chartData = await chartResp.json();
                }
            } catch { /* chart viz is optional */ }

            renderResults();
            showStep(stepResults);

        } catch (err) {
            alert(`Error generating horoscope:\n\n${err.message}`);
        } finally {
            btnText.style.display = '';
            btnLoader.style.display = 'none';
            btnGenerate.disabled = false;
        }
    }

    /* ─── Render Results ────────────────────────────────────── */
    function renderResults() {
        const data = state.analysisData;
        if (!data) return;

        const system = state.selectedSystem;
        const systemLabel = { vedic: 'Vedic (Jyotish)', kp: 'KP (Krishnamurti)', western: 'Western (Tropical)' }[system] || system;

        // Title
        $('#results-title').textContent = `${data.name}'s Celestial Blueprint`;
        $('#results-subtitle').textContent = `${systemLabel} Analysis • ${data.focus?.replace('_', ' ').toUpperCase()} • ${data.engine_source}`;

        // Quick Stats
        renderQuickStats(data);

        // Chart Visualization
        renderChart();

        // Analysis Sections
        renderSections(data.sections || []);

        // Timeline
        renderTimeline(data.timeline || []);

        // Life Stages
        renderLifeStages(data.life_stages || []);

        // Gemstones
        renderGemstones(data.gemstone_recommendations || []);

        // Remedies
        renderRemedies(data.spiritual_remedies || []);

        // Formatted Reading
        renderFormattedReading(data.formatted_reading || '');
    }

    function renderQuickStats(data) {
        const container = $('#quick-stats');
        const stats = [
            { label: 'Ascendant', value: data.ascendant || '—' },
            { label: 'Sun Sign', value: data.sun_sign || '—' },
            { label: 'Moon Sign', value: data.moon_sign || '—' },
        ];

        if (data.current_mahadasha) {
            stats.push({ label: 'Mahadasha', value: data.current_mahadasha });
        }
        if (data.current_antardasha) {
            stats.push({ label: 'Antardasha', value: data.current_antardasha });
        }
        if (data.current_pratyantardasha) {
            stats.push({ label: 'Pratyantardasha', value: data.current_pratyantardasha });
        }

        container.innerHTML = stats.map(s => `
            <div class="stat-item">
                <div class="stat-label">${s.label}</div>
                <div class="stat-value">${s.value}</div>
            </div>
        `).join('');
    }

    function renderChart() {
        const chartData = state.chartData || {};
        const canvas = $('#chart-canvas');
        const system = state.selectedSystem;

        const titleMap = {
            vedic: '🕉️ Rashi Chart (South Indian)',
            kp: '🔬 KP Chart (Placidus Wheel)',
            western: '♈ Western Wheel Chart'
        };
        $('#chart-viz-title').textContent = titleMap[system] || 'Birth Chart';

        try {
            const renderer = new ChartRenderer(canvas);
            renderer.render(chartData, system);
        } catch (err) {
            console.warn('Chart rendering failed:', err);
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.font = '14px Inter, sans-serif';
            ctx.fillStyle = 'rgba(240, 240, 255, 0.4)';
            ctx.textAlign = 'center';
            ctx.fillText('Chart visualization unavailable', canvas.width / 2, canvas.height / 2);
        }
    }

    function renderSections(sections) {
        const container = $('#analysis-sections');
        if (!sections.length) {
            container.innerHTML = '<p style="color: var(--text-tertiary);">No sections available.</p>';
            return;
        }

        container.innerHTML = sections.map((sec, idx) => `
            <div class="analysis-section ${idx < 3 ? 'open' : ''}" id="section-${sec.id}">
                <div class="section-header" onclick="this.parentElement.classList.toggle('open')">
                    <h4>${sec.title}</h4>
                    <span class="section-toggle">▼</span>
                </div>
                <div class="section-body">
                    ${sec.key_points?.length ? `
                        <div class="key-points">
                            ${sec.key_points.map(kp => `<div class="key-point">${escHtml(kp)}</div>`).join('')}
                        </div>
                    ` : ''}
                    ${sec.rules_applied?.length ? `
                        <div style="margin-top: 0.75rem;">
                            ${sec.rules_applied.map(r => `<div class="rule-applied">${escHtml(r)}</div>`).join('')}
                        </div>
                    ` : ''}
                    ${sec.conclusions?.length ? `
                        <div style="margin-top: 0.75rem;">
                            ${sec.conclusions.map(c => `<div class="conclusion">${escHtml(c)}</div>`).join('')}
                        </div>
                    ` : ''}
                    ${sec.raw_markdown ? `
                        <div class="section-markdown">${escHtml(sec.raw_markdown)}</div>
                    ` : ''}
                </div>
            </div>
        `).join('');
    }

    function renderTimeline(items) {
        const container = $('#timeline-container');
        const itemsDiv = $('#timeline-items');
        if (!items.length) {
            container.style.display = 'none';
            return;
        }
        container.style.display = '';
        itemsDiv.innerHTML = items.map(t => `
            <div class="timeline-item">
                <div class="timeline-timeframe">${escHtml(t.timeframe)}</div>
                <div class="timeline-phase">${escHtml(t.phase)}</div>
                <div class="timeline-prediction">${escHtml(t.prediction)}</div>
            </div>
        `).join('');
    }

    function renderLifeStages(stages) {
        const container = $('#life-stages-container');
        const itemsDiv = $('#life-stages-items');
        if (!stages.length) {
            container.style.display = 'none';
            return;
        }
        container.style.display = '';
        itemsDiv.innerHTML = stages.map(s => `
            <div class="life-stage-card" data-stage="${s.stage_number}">
                <div class="life-stage-header">
                    <span class="life-stage-age">${escHtml(s.age_bracket)}</span>
                    <span class="life-stage-title">${escHtml(s.title)}</span>
                </div>
                <div class="life-stage-dasha">⏱ ${escHtml(s.dasha_context)}</div>
                ${s.key_themes?.length ? `
                    <div class="life-stage-themes">
                        ${s.key_themes.map(t => `<span class="theme-tag">${escHtml(t)}</span>`).join('')}
                    </div>
                ` : ''}
                ${s.milestones?.length ? `
                    <ul class="life-stage-milestones">
                        ${s.milestones.map(m => `<li>${escHtml(m)}</li>`).join('')}
                    </ul>
                ` : ''}
                ${s.guidance ? `<div class="life-stage-guidance">${escHtml(s.guidance)}</div>` : ''}
            </div>
        `).join('');
    }

    function renderGemstones(gems) {
        const container = $('#gemstones-container');
        const itemsDiv = $('#gemstone-items');
        if (!gems.length) {
            container.style.display = 'none';
            return;
        }
        container.style.display = '';
        itemsDiv.innerHTML = gems.map(g => `
            <div class="gemstone-card ${g.is_contraindicated ? 'gem-contraindicated' : 'gem-recommended'}">
                <div class="gemstone-icon">${g.is_contraindicated ? '⚠️' : '💎'}</div>
                <div class="gemstone-info">
                    <h4>${escHtml(g.gemstone)} (${escHtml(g.sanskrit_name)})</h4>
                    <div class="gem-meta">${escHtml(g.category)} • ${escHtml(g.ruling_planet)} • ${escHtml(g.finger)} • ${escHtml(g.metal)}</div>
                    <div class="gem-rationale">${escHtml(g.rationale)}</div>
                </div>
            </div>
        `).join('');
    }

    function renderRemedies(remedies) {
        const container = $('#remedies-container');
        const itemsDiv = $('#remedy-items');
        if (!remedies.length) {
            container.style.display = 'none';
            return;
        }
        container.style.display = '';
        itemsDiv.innerHTML = remedies.map(r => `
            <div class="remedy-card">
                <div class="remedy-category">${escHtml(r.category)} — ${escHtml(r.target_planet)}</div>
                <h4>${escHtml(r.title)}</h4>
                <div class="remedy-details">${escHtml(r.description)}</div>
                ${r.mantra_or_practice ? `<code class="remedy-mantra">${escHtml(r.mantra_or_practice)}</code>` : ''}
                <div style="font-size:0.75rem; color:var(--text-tertiary); margin-top:0.3rem;">
                    📅 ${escHtml(r.timing_or_day)}
                </div>
            </div>
        `).join('');
    }

    function renderFormattedReading(text) {
        const container = $('#formatted-reading');
        container.textContent = text || 'No formatted reading available.';
    }

    /* ─── Download Report ───────────────────────────────────── */
    btnDownload.addEventListener('click', () => {
        const data = state.analysisData;
        if (!data) return;

        const text = data.formatted_reading || JSON.stringify(data, null, 2);
        const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${data.name}_horoscope_${data.system}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    });

    /* ─── Utility ───────────────────────────────────────────── */
    function escHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    /* ─── Initialize ────────────────────────────────────────── */
    initStarCanvas();
    initLocationMap();
    initPlaceSearch();

})();
