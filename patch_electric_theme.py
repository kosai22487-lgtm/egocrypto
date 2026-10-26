import os, re

# ========== 1. Patch custom.js to include electric theme ==========
with open('static/custom.js', 'r') as f:
    js = f.read()

# Add 'electric' to validThemes
old_valid = "const validThemes = ['light', 'black', 'animated', 'matrix', 'circuit'];"
new_valid = "const validThemes = ['light', 'black', 'animated', 'matrix', 'circuit', 'electric'];"
if old_valid in js:
    js = js.replace(old_valid, new_valid)
    print("✅ validThemes updated with 'electric'")
else:
    js = re.sub(r"const validThemes = \[([^\]]+)\]", r"const validThemes = [\1, 'electric']", js, count=1)
    print("✅ validThemes updated via regex")

# Modify applyTheme to handle electric canvas
old_theme_apply = """    function applyTheme(theme) {
        if (!validThemes.includes(theme)) theme = DEFAULT_THEME;
        document.body.setAttribute('data-theme', theme);
        localStorage.setItem('egocrypto_theme', theme);

        // Particle canvas & blobs
        const particleCanvas = document.getElementById('particle-canvas');
        const blobs = document.querySelectorAll('.background-blob');
        if (theme === 'animated') {
            if (particleCanvas) particleCanvas.style.display = 'block';
            blobs.forEach(b => b.style.display = 'block');
        } else {
            if (particleCanvas) particleCanvas.style.display = 'none';
            blobs.forEach(b => b.style.display = 'none');
        }

        // Matrix canvas
        if (theme === 'matrix') {
            startMatrix();
        } else {
            stopMatrix();
        }
    }"""

new_theme_apply = """    function applyTheme(theme) {
        if (!validThemes.includes(theme)) theme = DEFAULT_THEME;
        document.body.setAttribute('data-theme', theme);
        localStorage.setItem('egocrypto_theme', theme);

        // Particle canvas & blobs
        const particleCanvas = document.getElementById('particle-canvas');
        const blobs = document.querySelectorAll('.background-blob');
        if (theme === 'animated') {
            if (particleCanvas) particleCanvas.style.display = 'block';
            blobs.forEach(b => b.style.display = 'block');
        } else {
            if (particleCanvas) particleCanvas.style.display = 'none';
            blobs.forEach(b => b.style.display = 'none');
        }

        // Matrix canvas
        if (theme === 'matrix') {
            startMatrix();
        } else {
            stopMatrix();
        }

        // Electric circuit canvas
        if (theme === 'electric') {
            startElectric();
        } else {
            stopElectric();
        }
    }"""

if old_theme_apply in js:
    js = js.replace(old_theme_apply, new_theme_apply)
    print("✅ applyTheme updated with electric handling")
else:
    print("⚠️ applyTheme block not found, trying regex...")
    # Fallback: find the function and insert electric lines before closing
    pattern = re.compile(r"(function applyTheme\(theme\) \{[^}]*\})", re.DOTALL)
    if pattern.search(js):
        # We'll just append electric handling right after matrix handling manually by string replace
        js = js.replace("""        // Matrix canvas
        if (theme === 'matrix') {
            startMatrix();
        } else {
            stopMatrix();
        }""", """        // Matrix canvas
        if (theme === 'matrix') {
            startMatrix();
        } else {
            stopMatrix();
        }

        // Electric circuit canvas
        if (theme === 'electric') {
            startElectric();
        } else {
            stopElectric();
        }""")
        print("✅ applyTheme electric handling inserted via string replace")
    else:
        print("❌ applyTheme not found. Manual intervention needed.")

# Append electric canvas functions at end of file
electric_js = """

// ===== Electric Circuit Canvas =====
let electricCanvas, electricCtx, electricAnimationId = null;
let electricTraces = [];
let electricPulses = [];

function initElectricCanvas() {
    electricCanvas = document.createElement('canvas');
    electricCanvas.id = 'electric-canvas';
    electricCanvas.style.cssText = 'position:fixed; top:0; left:0; width:100%; height:100%; z-index:-1; pointer-events:none;';
    document.body.appendChild(electricCanvas);
    electricCtx = electricCanvas.getContext('2d');

    function resizeElectric() {
        electricCanvas.width = window.innerWidth;
        electricCanvas.height = window.innerHeight;
        generateElectricTraces();
        initElectricPulses();
    }
    resizeElectric();
    window.addEventListener('resize', resizeElectric);
}

function generateElectricTraces() {
    electricTraces = [];
    const width = electricCanvas.width;
    const height = electricCanvas.height;
    // IC chip position (center)
    const chipX = width / 2;
    const chipY = height / 2;
    const chipW = 80;
    const chipH = 80;
    // Number of traces
    const numTraces = 24;

    for (let i = 0; i < numTraces; i++) {
        // Start from random point on chip edge
        const side = i % 4;
        let startX, startY;
        switch(side) {
            case 0: // top
                startX = chipX - chipW/2 + Math.random() * chipW;
                startY = chipY - chipH/2;
                break;
            case 1: // right
                startX = chipX + chipW/2;
                startY = chipY - chipH/2 + Math.random() * chipH;
                break;
            case 2: // bottom
                startX = chipX - chipW/2 + Math.random() * chipW;
                startY = chipY + chipH/2;
                break;
            case 3: // left
                startX = chipX - chipW/2;
                startY = chipY - chipH/2 + Math.random() * chipH;
                break;
        }

        // End point at outer edge
        let endX, endY;
        const angle = Math.random() * Math.PI * 2;
        const radius = Math.max(width, height) * 0.7;
        endX = Math.cos(angle) * radius + chipX;
        endY = Math.sin(angle) * radius + chipY;

        // Create path with right-angle bends
        const points = [{x: startX, y: startY}];
        let currentX = startX;
        let currentY = startY;
        // Decide direction: first move horizontally then vertically or vice versa
        if (Math.random() > 0.5) {
            // Horizontal then vertical
            const midX = currentX + (endX - currentX) * (0.3 + Math.random() * 0.4);
            points.push({x: midX, y: currentY});
            points.push({x: midX, y: endY});
        } else {
            const midY = currentY + (endY - currentY) * (0.3 + Math.random() * 0.4);
            points.push({x: currentX, y: midY});
            points.push({x: endX, y: midY});
        }
        points.push({x: endX, y: endY});
        electricTraces.push(points);
    }
}

function initElectricPulses() {
    electricPulses = [];
    const numPulses = 8;
    for (let i = 0; i < numPulses; i++) {
        electricPulses.push({
            traceIndex: Math.floor(Math.random() * electricTraces.length),
            t: Math.random()
        });
    }
}

function drawElectric() {
    electricCtx.clearRect(0, 0, electricCanvas.width, electricCanvas.height);

    // Draw IC chip
    const chipX = electricCanvas.width / 2;
    const chipY = electricCanvas.height / 2;
    electricCtx.fillStyle = '#1a1a1a';
    electricCtx.fillRect(chipX - 40, chipY - 40, 80, 80);
    electricCtx.strokeStyle = '#00ccff';
    electricCtx.lineWidth = 2;
    electricCtx.strokeRect(chipX - 40, chipY - 40, 80, 80);

    // Draw traces
    electricCtx.strokeStyle = 'rgba(0, 255, 255, 0.3)';
    electricCtx.lineWidth = 1.5;
    for (const trace of electricTraces) {
        electricCtx.beginPath();
        electricCtx.moveTo(trace[0].x, trace[0].y);
        for (let i = 1; i < trace.length; i++) {
            electricCtx.lineTo(trace[i].x, trace[i].y);
        }
        electricCtx.stroke();
    }

    // Draw pulses
    for (const pulse of electricPulses) {
        const trace = electricTraces[pulse.traceIndex];
        if (!trace) continue;
        // Interpolate along polyline
        const totalLength = trace.length - 1;
        const idx = Math.floor(pulse.t * totalLength);
        if (idx >= totalLength) idx = totalLength - 1;
        const frac = pulse.t * totalLength - idx;
        const p1 = trace[idx];
        const p2 = trace[idx + 1];
        const x = p1.x + (p2.x - p1.x) * frac;
        const y = p1.y + (p2.y - p1.y) * frac;

        // Glow dot
        electricCtx.beginPath();
        electricCtx.arc(x, y, 3, 0, Math.PI * 2);
        electricCtx.fillStyle = '#00ffcc';
        electricCtx.fill();
        electricCtx.beginPath();
        electricCtx.arc(x, y, 8, 0, Math.PI * 2);
        electricCtx.fillStyle = 'rgba(0, 255, 255, 0.2)';
        electricCtx.fill();

        // Move pulse
        pulse.t += 0.005;
        if (pulse.t > 1) pulse.t = 0;
    }
}

function animateElectric() {
    drawElectric();
    electricAnimationId = requestAnimationFrame(animateElectric);
}

function startElectric() {
    if (!electricCanvas) initElectricCanvas();
    electricCanvas.style.display = 'block';
    if (!electricAnimationId) animateElectric();
}

function stopElectric() {
    if (electricAnimationId) {
        cancelAnimationFrame(electricAnimationId);
        electricAnimationId = null;
    }
    if (electricCanvas) electricCanvas.style.display = 'none';
}
"""

with open('static/custom.js', 'a') as f:
    f.write(electric_js)
print("✅ Electric circuit canvas functions appended to custom.js")

# ========== 2. Append Electric Theme CSS ==========
electric_css = """

/* Electric Circuit Theme */
body[data-theme="electric"] {
    background: #000 !important;
    background-image: none !important;
    color: #00ffcc !important;
}

body[data-theme="electric"] .glass-card,
body[data-theme="electric"] .card,
body[data-theme="electric"] .bg-gray-900,
body[data-theme="electric"] .bg-gray-950,
body[data-theme="electric"] .bg-[#12161f],
body[data-theme="electric"] .bg-[#1E2533] {
    background: rgba(0, 10, 20, 0.85) !important;
    border-color: rgba(0, 255, 255, 0.25) !important;
    color: #00ffcc !important;
}

body[data-theme="electric"] .text-white {
    color: #e0ffff !important;
}

body[data-theme="electric"] .text-gray-400 {
    color: #80deea !important;
}

body[data-theme="electric"] header,
body[data-theme="electric"] #sidebar,
body[data-theme="electric"] nav.fixed.bottom-0 {
    background: rgba(0, 0, 0, 0.85) !important;
    border-color: rgba(0, 255, 255, 0.2) !important;
}
"""

with open('static/custom.css', 'a') as f:
    f.write(electric_css)
print("✅ Electric Theme CSS appended to custom.css")

# ========== 3. Add Electric Theme option in settings.html ==========
settings_path = 'templates/partials/settings.html'
with open(settings_path, 'r') as f:
    html = f.read()

# Insert after Grid Theme option (data-theme-option="circuit")
old_grid_option = """<div data-theme-option="circuit" onclick="setTheme('circuit')" class="cursor-pointer bg-[#1E2533] border border-gray-800 rounded-xl p-4 flex items-center justify-between hover:bg-gray-800/50 transition">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-900"></div>
                <span class="text-white text-sm">Grid Theme</span>
            </div>
            <i class="fa-solid fa-check text-teal-400 hidden"></i>
        </div>"""

new_grid_plus_electric = old_grid_option + """
        <div data-theme-option="electric" onclick="setTheme('electric')" class="cursor-pointer bg-[#1E2533] border border-gray-800 rounded-xl p-4 flex items-center justify-between hover:bg-gray-800/50 transition">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-green-400 to-blue-700"></div>
                <span class="text-white text-sm">Electric Circuit</span>
            </div>
            <i class="fa-solid fa-check text-teal-400 hidden"></i>
        </div>"""

if old_grid_option in html:
    html = html.replace(old_grid_option, new_grid_plus_electric)
    print("✅ Electric Circuit option added to App Customization")
else:
    # Fallback: try to find Grid Theme span and insert after its parent div
    html = re.sub(r'(<div data-theme-option="circuit".*?</div>)',
                  r'\1\n        <div data-theme-option="electric" onclick="setTheme(\'electric\')" class="cursor-pointer bg-[#1E2533] border border-gray-800 rounded-xl p-4 flex items-center justify-between hover:bg-gray-800/50 transition">\n            <div class="flex items-center gap-3">\n                <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-green-400 to-blue-700"></div>\n                <span class="text-white text-sm">Electric Circuit</span>\n            </div>\n            <i class="fa-solid fa-check text-teal-400 hidden"></i>\n        </div>',
                  html, count=1, flags=re.DOTALL)
    print("✅ Electric Circuit option added via regex fallback")

with open(settings_path, 'w') as f:
    f.write(html)

print("🎉 Electric circuit theme patch completed. Restart server and hard refresh browser.")
