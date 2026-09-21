/* ═══════════════════════════════════════════════════════════════════
   Chart Renderer — South Indian / North Indian / KP / Western charts
   Draws astrological birth charts on HTML5 Canvas
   ═══════════════════════════════════════════════════════════════════ */

class ChartRenderer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.dpr = window.devicePixelRatio || 1;
    }

    /** Set up HiDPI canvas */
    _setupHiDPI(size) {
        this.canvas.width = size * this.dpr;
        this.canvas.height = size * this.dpr;
        this.canvas.style.width = size + 'px';
        this.canvas.style.height = size + 'px';
        this.ctx.scale(this.dpr, this.dpr);
        this.size = size;
        this.cx = size / 2;
        this.cy = size / 2;
    }

    /** Main render dispatcher */
    render(chartData, system) {
        const size = Math.min(600, this.canvas.parentElement.clientWidth - 60);
        this._setupHiDPI(size);
        this.ctx.clearRect(0, 0, size, size);

        if (system === 'vedic') {
            this._renderSouthIndian(chartData);
        } else if (system === 'kp') {
            this._renderKPChart(chartData);
        } else {
            this._renderWesternWheel(chartData);
        }
    }

    /* ─── Color Palette ─────────────────────────────────────── */
    _colors() {
        return {
            bg: '#0a0a1a',
            line: 'rgba(167, 139, 250, 0.3)',
            lineStrong: 'rgba(167, 139, 250, 0.5)',
            text: '#f0f0ff',
            textDim: 'rgba(240, 240, 255, 0.5)',
            accent: '#a78bfa',
            amber: '#f59e0b',
            cyan: '#06b6d4',
            emerald: '#10b981',
            rose: '#f43f5e',
            planets: {
                Sun: '#f59e0b',
                Moon: '#e2e8f0',
                Mars: '#ef4444',
                Mercury: '#10b981',
                Jupiter: '#f59e0b',
                Venus: '#ec4899',
                Saturn: '#6366f1',
                Rahu: '#8b5cf6',
                Ketu: '#a78bfa',
                Uranus: '#06b6d4',
                Neptune: '#3b82f6',
                Pluto: '#9333ea',
            },
            zodiac: [
                '#ef4444', '#10b981', '#f59e0b', '#e2e8f0',
                '#f59e0b', '#10b981', '#ec4899', '#ef4444',
                '#8b5cf6', '#6366f1', '#06b6d4', '#3b82f6'
            ]
        };
    }

    _zodiacGlyphs() {
        return ['♈','♉','♊','♋','♌','♍','♎','♏','♐','♑','♒','♓'];
    }

    _zodiacNames() {
        return [
            'Aries','Taurus','Gemini','Cancer','Leo','Virgo',
            'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'
        ];
    }

    _vedicNames() {
        return [
            'Mesha','Vrishabha','Mithuna','Karka','Simha','Kanya',
            'Tula','Vrishchika','Dhanu','Makara','Kumbha','Meena'
        ];
    }

    _planetGlyphs() {
        return {
            Sun: '☉', Moon: '☽', Mars: '♂', Mercury: '☿',
            Jupiter: '♃', Venus: '♀', Saturn: '♄',
            Rahu: '☊', Ketu: '☋',
            Uranus: '♅', Neptune: '♆', Pluto: '♇',
            Surya: '☉', Chandra: '☽', Mangala: '♂', Budha: '☿',
            Guru: '♃', Shukra: '♀', Shani: '♄',
        };
    }

    /* ─── SOUTH INDIAN CHART (Vedic) ────────────────────────── */
    _renderSouthIndian(data) {
        const ctx = this.ctx;
        const s = this.size;
        const c = this._colors();
        const pad = 30;
        const boxW = (s - pad * 2) / 4;
        const boxH = (s - pad * 2) / 4;
        const ox = pad;
        const oy = pad;

        // South Indian: 12 houses in fixed zodiac positions
        // Box layout (row, col):
        //   Pi Ar Ta Ge
        //   Aq .. .. Ca
        //   Cp .. .. Le
        //   Sg Sc Li Vi
        const positions = [
            [0, 1], // 0: Aries (Mesha)
            [0, 2], // 1: Taurus
            [0, 3], // 2: Gemini
            [1, 3], // 3: Cancer
            [2, 3], // 4: Leo
            [3, 3], // 5: Virgo
            [3, 2], // 6: Libra
            [3, 1], // 7: Scorpio
            [3, 0], // 8: Sagittarius
            [2, 0], // 9: Capricorn
            [1, 0], // 10: Aquarius
            [0, 0], // 11: Pisces
        ];

        // Draw grid
        ctx.strokeStyle = c.lineStrong;
        ctx.lineWidth = 1.5;
        for (let r = 0; r <= 4; r++) {
            ctx.beginPath();
            ctx.moveTo(ox, oy + r * boxH);
            ctx.lineTo(ox + 4 * boxW, oy + r * boxH);
            ctx.stroke();
        }
        for (let col = 0; col <= 4; col++) {
            ctx.beginPath();
            ctx.moveTo(ox + col * boxW, oy);
            ctx.lineTo(ox + col * boxW, oy + 4 * boxH);
            ctx.stroke();
        }

        // Center box: chart label
        ctx.fillStyle = 'rgba(167, 139, 250, 0.08)';
        ctx.fillRect(ox + boxW, oy + boxH, boxW * 2, boxH * 2);
        ctx.font = `600 ${Math.max(12, s * 0.025)}px "Outfit", sans-serif`;
        ctx.fillStyle = c.textDim;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('RASHI', this.cx, this.cy - 8);
        ctx.font = `500 ${Math.max(10, s * 0.018)}px "Inter", sans-serif`;
        ctx.fillText('South Indian', this.cx, this.cy + 12);

        // Determine ascendant sign index
        let ascIdx = 0;
        if (data.grahas || data.planets) {
            const asc = data.ascendant_sign || data.ascendant || '';
            const vedNames = this._vediacNames ? this._vediacNames() : this._vedicNames();
            const westNames = this._zodiacNames();
            ascIdx = vedNames.findIndex(n => asc.includes(n));
            if (ascIdx < 0) ascIdx = westNames.findIndex(n => asc.includes(n));
            if (ascIdx < 0) ascIdx = 0;
        }

        // Draw sign names and glyphs
        const glyphs = this._zodiacGlyphs();
        const vedNames = this._vedicNames();
        for (let i = 0; i < 12; i++) {
            const [r, col] = positions[i];
            const bx = ox + col * boxW;
            const by = oy + r * boxH;

            // Sign glyph + name
            ctx.font = `${Math.max(14, s * 0.028)}px sans-serif`;
            ctx.fillStyle = c.zodiac[i];
            ctx.textAlign = 'left';
            ctx.textBaseline = 'top';
            ctx.fillText(glyphs[i], bx + 5, by + 3);

            ctx.font = `500 ${Math.max(8, s * 0.016)}px "Inter", sans-serif`;
            ctx.fillStyle = c.textDim;
            ctx.fillText(vedNames[i], bx + 22, by + 7);

            // House number (relative to ascendant)
            const houseNum = ((i - ascIdx + 12) % 12) + 1;
            if (houseNum === 1) {
                // Mark ascendant
                ctx.fillStyle = c.amber;
                ctx.font = `700 ${Math.max(9, s * 0.016)}px "JetBrains Mono", monospace`;
                ctx.textAlign = 'right';
                ctx.textBaseline = 'top';
                ctx.fillText('Asc', bx + boxW - 5, by + 3);
            }
        }

        // Place planets
        const planets = data.grahas || data.planets || [];
        const planetGlyphs = this._planetGlyphs();

        // Group planets by sign index
        const signPlanets = {};
        for (const p of planets) {
            const pName = p.name || p.western_name || '';
            let signIdx = -1;
            if (p.rashi_index !== undefined) {
                signIdx = p.rashi_index;
            } else if (p.sign_index !== undefined) {
                signIdx = p.sign_index;
            } else if (p.rashi) {
                signIdx = this._vedicNames().findIndex(n => p.rashi === n);
            } else if (p.sign) {
                signIdx = this._zodiacNames().findIndex(n => p.sign === n);
            } else if (p.longitude !== undefined) {
                signIdx = Math.floor(p.longitude / 30);
            }
            if (signIdx < 0 || signIdx > 11) continue;
            if (!signPlanets[signIdx]) signPlanets[signIdx] = [];
            signPlanets[signIdx].push(pName);
        }

        // Render grouped planets in each box
        for (const [idx, pList] of Object.entries(signPlanets)) {
            const si = parseInt(idx);
            const [r, col] = positions[si];
            const bx = ox + col * boxW;
            const by = oy + r * boxH;

            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';

            const maxPerRow = 3;
            const rows = Math.ceil(pList.length / maxPerRow);
            const fontSize = Math.max(9, Math.min(s * 0.022, 14));

            for (let pi = 0; pi < pList.length; pi++) {
                const row = Math.floor(pi / maxPerRow);
                const colInRow = pi % maxPerRow;
                const totalInRow = Math.min(maxPerRow, pList.length - row * maxPerRow);

                const px = bx + (boxW / (totalInRow + 1)) * (colInRow + 1);
                const py = by + boxH * 0.45 + row * (fontSize + 6);

                const name = pList[pi];
                const abbrev = name.substring(0, 2);
                const glyph = planetGlyphs[name] || abbrev;

                ctx.font = `${fontSize}px sans-serif`;
                ctx.fillStyle = c.planets[name] || c.text;
                ctx.fillText(glyph, px, py);

                ctx.font = `500 ${Math.max(7, fontSize - 3)}px "Inter", sans-serif`;
                ctx.fillStyle = c.textDim;
                ctx.fillText(abbrev, px, py + fontSize);
            }
        }
    }

    /* ─── KP CHART (Placidus with sub-lords) ────────────────── */
    _renderKPChart(data) {
        const ctx = this.ctx;
        const s = this.size;
        const c = this._colors();

        const outerR = s * 0.44;
        const midR = s * 0.34;
        const innerR = s * 0.22;
        const cx = this.cx;
        const cy = this.cy;

        // Background circle
        ctx.beginPath();
        ctx.arc(cx, cy, outerR + 10, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(167, 139, 250, 0.03)';
        ctx.fill();

        // Get cusps for house boundaries
        const cusps = data.kp_cusps || data.cusps || [];
        const ascLong = cusps.length > 0 ? (cusps[0]?.longitude || 0) : 0;
        const glyphs = this._zodiacGlyphs();

        // Draw zodiac ring
        for (let i = 0; i < 12; i++) {
            const startAngle = (i * 30 - 90 - ascLong) * Math.PI / 180;
            const endAngle = ((i + 1) * 30 - 90 - ascLong) * Math.PI / 180;

            ctx.beginPath();
            ctx.arc(cx, cy, outerR, startAngle, endAngle);
            ctx.arc(cx, cy, midR, endAngle, startAngle, true);
            ctx.closePath();
            ctx.fillStyle = `${c.zodiac[i]}11`;
            ctx.fill();
            ctx.strokeStyle = c.line;
            ctx.lineWidth = 1;
            ctx.stroke();

            // Zodiac glyph
            const midAngle = (startAngle + endAngle) / 2;
            const glyphR = (outerR + midR) / 2;
            const gx = cx + Math.cos(midAngle) * glyphR;
            const gy = cy + Math.sin(midAngle) * glyphR;
            ctx.font = `${Math.max(14, s * 0.028)}px sans-serif`;
            ctx.fillStyle = c.zodiac[i];
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(glyphs[i], gx, gy);
        }

        // Draw house cusps (lines from inner to outer)
        for (let i = 0; i < cusps.length && i < 12; i++) {
            const cuspLong = cusps[i]?.longitude || (i * 30);
            const angle = (cuspLong - 90 - ascLong) * Math.PI / 180;

            ctx.beginPath();
            ctx.moveTo(cx + Math.cos(angle) * innerR, cy + Math.sin(angle) * innerR);
            ctx.lineTo(cx + Math.cos(angle) * outerR, cy + Math.sin(angle) * outerR);
            ctx.strokeStyle = c.lineStrong;
            ctx.lineWidth = i === 0 ? 2.5 : 1;
            ctx.stroke();

            // House number
            const nextCusp = cusps[(i + 1) % 12]?.longitude || ((i + 1) * 30);
            let midLong = (cuspLong + nextCusp) / 2;
            if (nextCusp < cuspLong) midLong = ((cuspLong + nextCusp + 360) / 2) % 360;
            const numAngle = (midLong - 90 - ascLong) * Math.PI / 180;
            const numR = (innerR + midR) / 2;
            const nx = cx + Math.cos(numAngle) * numR;
            const ny = cy + Math.sin(numAngle) * numR;

            ctx.font = `600 ${Math.max(10, s * 0.02)}px "JetBrains Mono", monospace`;
            ctx.fillStyle = c.textDim;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(`${i + 1}`, nx, ny);

            // Sub-lord label near the cusp
            const subLord = cusps[i]?.sub_lord || '';
            if (subLord) {
                const labelR = midR + (outerR - midR) * 0.15;
                const labelAngle = (cuspLong - 90 - ascLong + 4) * Math.PI / 180;
                const lx = cx + Math.cos(labelAngle) * labelR;
                const ly = cy + Math.sin(labelAngle) * labelR;

                ctx.save();
                ctx.translate(lx, ly);
                ctx.rotate(labelAngle + Math.PI / 2);
                ctx.font = `500 ${Math.max(7, s * 0.013)}px "JetBrains Mono", monospace`;
                ctx.fillStyle = c.cyan;
                ctx.textAlign = 'left';
                ctx.fillText(subLord.substring(0, 3), 0, 0);
                ctx.restore();
            }
        }

        // Inner circle
        ctx.beginPath();
        ctx.arc(cx, cy, innerR, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(10, 10, 26, 0.8)';
        ctx.fill();
        ctx.strokeStyle = c.lineStrong;
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Center label
        ctx.font = `600 ${Math.max(11, s * 0.022)}px "Outfit", sans-serif`;
        ctx.fillStyle = c.accent;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('KP CHART', cx, cy - 8);
        ctx.font = `400 ${Math.max(8, s * 0.015)}px "Inter", sans-serif`;
        ctx.fillStyle = c.textDim;
        ctx.fillText('Placidus • Sub-Lord', cx, cy + 10);

        // Plot planets
        const planets = data.kp_planets || data.grahas || data.planets || [];
        const planetGlyphs = this._planetGlyphs();
        const plotted = [];

        for (const p of planets) {
            const name = p.name || p.western_name || '';
            const long = p.longitude || 0;
            const angle = (long - 90 - ascLong) * Math.PI / 180;
            let plotR = (innerR + midR) / 2 + 8;

            // Avoid overlap
            for (const pp of plotted) {
                const dist = Math.abs(long - pp.long);
                if (dist < 8 || dist > 352) {
                    plotR -= 14;
                    break;
                }
            }

            const px = cx + Math.cos(angle) * plotR;
            const py = cy + Math.sin(angle) * plotR;

            const glyph = planetGlyphs[name] || name.substring(0, 2);
            ctx.font = `${Math.max(13, s * 0.025)}px sans-serif`;
            ctx.fillStyle = c.planets[name] || c.text;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(glyph, px, py);

            plotted.push({ long, px, py });
        }

        // Ascendant marker arrow
        if (cusps.length > 0) {
            const ascAngle = -Math.PI / 2; // Ascendant is always at top after rotation
            const arrowLen = 12;
            ctx.beginPath();
            ctx.moveTo(cx + Math.cos(ascAngle) * (outerR + 2), cy + Math.sin(ascAngle) * (outerR + 2));
            ctx.lineTo(cx + Math.cos(ascAngle - 0.15) * (outerR + arrowLen), cy + Math.sin(ascAngle - 0.15) * (outerR + arrowLen));
            ctx.lineTo(cx + Math.cos(ascAngle + 0.15) * (outerR + arrowLen), cy + Math.sin(ascAngle + 0.15) * (outerR + arrowLen));
            ctx.closePath();
            ctx.fillStyle = c.amber;
            ctx.fill();
        }
    }

    /* ─── WESTERN WHEEL CHART ───────────────────────────────── */
    _renderWesternWheel(data) {
        const ctx = this.ctx;
        const s = this.size;
        const c = this._colors();

        const outerR = s * 0.44;
        const midR = s * 0.36;
        const innerR = s * 0.28;
        const planetR = s * 0.2;
        const cx = this.cx;
        const cy = this.cy;

        const houses = data.houses || [];
        const ascLong = houses.length > 0 ? (houses[0]?.cusp_longitude || 0) : 0;
        const glyphs = this._zodiacGlyphs();

        // Zodiac ring
        for (let i = 0; i < 12; i++) {
            const startAngle = (i * 30 - 90 - ascLong) * Math.PI / 180;
            const endAngle = ((i + 1) * 30 - 90 - ascLong) * Math.PI / 180;

            ctx.beginPath();
            ctx.arc(cx, cy, outerR, startAngle, endAngle);
            ctx.arc(cx, cy, midR, endAngle, startAngle, true);
            ctx.closePath();
            ctx.fillStyle = `${c.zodiac[i]}11`;
            ctx.fill();
            ctx.strokeStyle = c.line;
            ctx.lineWidth = 1;
            ctx.stroke();

            // Sign dividers
            ctx.beginPath();
            ctx.moveTo(cx + Math.cos(startAngle) * midR, cy + Math.sin(startAngle) * midR);
            ctx.lineTo(cx + Math.cos(startAngle) * outerR, cy + Math.sin(startAngle) * outerR);
            ctx.strokeStyle = c.line;
            ctx.lineWidth = 1;
            ctx.stroke();

            // Glyphs
            const midAngle = (startAngle + endAngle) / 2;
            const glyphDist = (outerR + midR) / 2;
            ctx.font = `${Math.max(14, s * 0.028)}px sans-serif`;
            ctx.fillStyle = c.zodiac[i];
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(glyphs[i], cx + Math.cos(midAngle) * glyphDist, cy + Math.sin(midAngle) * glyphDist);
        }

        // House cusps
        for (let i = 0; i < houses.length && i < 12; i++) {
            const cuspLong = houses[i]?.cusp_longitude || (i * 30);
            const angle = (cuspLong - 90 - ascLong) * Math.PI / 180;

            ctx.beginPath();
            ctx.moveTo(cx + Math.cos(angle) * innerR, cy + Math.sin(angle) * innerR);
            ctx.lineTo(cx + Math.cos(angle) * midR, cy + Math.sin(angle) * midR);
            ctx.strokeStyle = i === 0 || i === 3 || i === 6 || i === 9 ? c.lineStrong : c.line;
            ctx.lineWidth = i === 0 || i === 3 || i === 6 || i === 9 ? 2 : 1;
            ctx.stroke();

            // House numbers
            const nextCusp = houses[(i + 1) % 12]?.cusp_longitude || ((i + 1) * 30);
            let midLong = (cuspLong + nextCusp) / 2;
            if (nextCusp < cuspLong) midLong = ((cuspLong + nextCusp + 360) / 2) % 360;
            const numAngle = (midLong - 90 - ascLong) * Math.PI / 180;
            const numDist = (innerR + midR) / 2;

            ctx.font = `600 ${Math.max(10, s * 0.018)}px "JetBrains Mono", monospace`;
            ctx.fillStyle = c.textDim;
            ctx.fillText(`${i + 1}`, cx + Math.cos(numAngle) * numDist, cy + Math.sin(numAngle) * numDist);
        }

        // Inner circle
        ctx.beginPath();
        ctx.arc(cx, cy, innerR, 0, Math.PI * 2);
        ctx.strokeStyle = c.lineStrong;
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Center
        ctx.fillStyle = 'rgba(10, 10, 26, 0.9)';
        ctx.beginPath();
        ctx.arc(cx, cy, planetR * 0.45, 0, Math.PI * 2);
        ctx.fill();
        ctx.font = `600 ${Math.max(10, s * 0.02)}px "Outfit", sans-serif`;
        ctx.fillStyle = c.accent;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('WESTERN', cx, cy - 6);
        ctx.font = `400 ${Math.max(8, s * 0.014)}px "Inter", sans-serif`;
        ctx.fillStyle = c.textDim;
        ctx.fillText('Tropical', cx, cy + 10);

        // Planets
        const planets = data.planets || [];
        const planetGlyphs = this._planetGlyphs();

        for (const p of planets) {
            const name = p.name || '';
            const long = p.longitude || 0;
            const angle = (long - 90 - ascLong) * Math.PI / 180;
            const pr = innerR - 18;

            const px = cx + Math.cos(angle) * pr;
            const py = cy + Math.sin(angle) * pr;

            const glyph = planetGlyphs[name] || name.substring(0, 2);
            ctx.font = `${Math.max(13, s * 0.025)}px sans-serif`;
            ctx.fillStyle = c.planets[name] || c.text;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(glyph, px, py);
        }

        // ASC marker
        const ascAngle = -Math.PI / 2;
        ctx.beginPath();
        ctx.moveTo(cx + Math.cos(ascAngle) * (outerR + 2), cy + Math.sin(ascAngle) * (outerR + 2));
        ctx.lineTo(cx + Math.cos(ascAngle - 0.15) * (outerR + 12), cy + Math.sin(ascAngle - 0.15) * (outerR + 12));
        ctx.lineTo(cx + Math.cos(ascAngle + 0.15) * (outerR + 12), cy + Math.sin(ascAngle + 0.15) * (outerR + 12));
        ctx.closePath();
        ctx.fillStyle = c.amber;
        ctx.fill();
    }
}

// Export globally
window.ChartRenderer = ChartRenderer;
