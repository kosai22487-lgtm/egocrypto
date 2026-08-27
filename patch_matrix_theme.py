import os, re

# ========== 1. Overwrite custom.js with Matrix Theme Support ==========
custom_js = """
// Theme Manager
(function(){
    const validThemes = ['light', 'black', 'animated', 'matrix'];
    const DEFAULT_THEME = 'animated';

    function getTheme() {
        return localStorage.getItem('egocrypto_theme') || DEFAULT_THEME;
    }

    function applyTheme(theme) {
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
    }

    window.setTheme = function(theme) {
        applyTheme(theme);
        updateThemeSelectionUI();
    };

    function updateThemeSelectionUI() {
        const current = getTheme();
        document.querySelectorAll('[data-theme-option]').forEach(el => {
            const val = el.getAttribute('data-theme-option');
            const checkIcon = el.querySelector('i.fa-check');
            if (val === current) {
                el.classList.add('border-teal-500', 'bg-teal-500/20');
                if (checkIcon) checkIcon.classList.remove('hidden');
            } else {
                el.classList.remove('border-teal-500', 'bg-teal-500/20');
                if (checkIcon) checkIcon.classList.add('hidden');
            }
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        applyTheme(getTheme());
        updateThemeSelectionUI();
    });
})();

// ===== Particle Background (Animated Stars) =====
function initParticles() {
    if (document.getElementById('particle-canvas')) return;
    const theme = localStorage.getItem('egocrypto_theme') || 'animated';
    if (theme !== 'animated') return;

    const canvas = document.createElement('canvas');
    canvas.id = 'particle-canvas';
    document.body.appendChild(canvas);
    const ctx = canvas.getContext('2d');
    let width, height, particles = [];

    function resize() {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    class Particle {
        constructor() { this.reset(); }
        reset() {
            this.x = Math.random() * width;
            this.y = Math.random() * height;
            this.size = Math.random() * 1.5 + 0.5;
            this.speedY = Math.random() * 0.5 + 0.1;
            this.speedX = Math.random() * 0.2 - 0.1;
            this.opacity = Math.random() * 0.5 + 0.2;
        }
        update() {
            this.y -= this.speedY;
            this.x += this.speedX;
            if (this.y < -10 || this.x < -10 || this.x > width + 10) this.reset();
        }
        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(255,255,255,${this.opacity})`;
            ctx.fill();
        }
    }

    for (let i = 0; i < 40; i++) particles.push(new Particle());

    function animate() {
        ctx.clearRect(0, 0, width, height);
        particles.forEach(p => { p.update(); p.draw(); });
        requestAnimationFrame(animate);
    }
    animate();
}

// ===== Matrix Rain Effect =====
let matrixCanvas, matrixCtx, matrixAnimationId = null;
const matrixChars = 'アカサタナハマヤラワ0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ';
const matrixFontSize = 14;
let matrixColumns, matrixDrops;

function initMatrixCanvas() {
    matrixCanvas = document.createElement('canvas');
    matrixCanvas.id = 'matrix-canvas';
    matrixCanvas.style.cssText = 'position:fixed; top:0; left:0; width:100%; height:100%; z-index:-1; pointer-events:none;';
    document.body.appendChild(matrixCanvas);
    matrixCtx = matrixCanvas.getContext('2d');

    function resizeMatrix() {
        matrixCanvas.width = window.innerWidth;
        matrixCanvas.height = window.innerHeight;
        matrixColumns = Math.floor(matrixCanvas.width / matrixFontSize);
        matrixDrops = Array(matrixColumns).fill(1);
    }
    resizeMatrix();
    window.addEventListener('resize', resizeMatrix);
}

function drawMatrix() {
    matrixCtx.fillStyle = 'rgba(0, 0, 0, 0.05)';
    matrixCtx.fillRect(0, 0, matrixCanvas.width, matrixCanvas.height);
    matrixCtx.fillStyle = '#0F0';
    matrixCtx.font = matrixFontSize + 'px monospace';

    for (let i = 0; i < matrixDrops.length; i++) {
        const text = matrixChars.charAt(Math.floor(Math.random() * matrixChars.length));
        matrixCtx.fillText(text, i * matrixFontSize, matrixDrops[i] * matrixFontSize);
        if (matrixDrops[i] * matrixFontSize > matrixCanvas.height && Math.random() > 0.975) {
            matrixDrops[i] = 0;
        }
        matrixDrops[i]++;
    }
}

function animateMatrix() {
    drawMatrix();
    matrixAnimationId = requestAnimationFrame(animateMatrix);
}

function startMatrix() {
    if (!matrixCanvas) initMatrixCanvas();
    matrixCanvas.style.display = 'block';
    if (!matrixAnimationId) animateMatrix();
}

function stopMatrix() {
    if (matrixAnimationId) {
        cancelAnimationFrame(matrixAnimationId);
        matrixAnimationId = null;
    }
    if (matrixCanvas) matrixCanvas.style.display = 'none';
}

// ===== Add floating blobs (only for animated theme) =====
document.addEventListener('DOMContentLoaded', () => {
    const theme = localStorage.getItem('egocrypto_theme') || 'animated';
    if (theme === 'animated') {
        initParticles();
        if (!document.querySelector('.background-blob')) {
            const blobDiv = document.createElement('div');
            blobDiv.innerHTML = `<div class="background-blob blob-1"></div><div class="background-blob blob-2"></div><div class="background-blob blob-3"></div>`;
            document.body.appendChild(blobDiv);
        }
    }
    if (theme === 'matrix') {
        startMatrix();
    }
});

// Smooth view switching (fade) for index.html
if (typeof switchTab === 'function') {
    const originalSwitch = switchTab;
    window.switchTab = function(tab) {
        const main = document.querySelector('main');
        if (main) {
            main.style.transition = 'opacity 0.3s';
            main.style.opacity = '0';
            setTimeout(() => {
                originalSwitch(tab);
                main.style.opacity = '1';
            }, 300);
        } else {
            originalSwitch(tab);
        }
    };
}
"""

with open('static/custom.js', 'w') as f:
    f.write(custom_js)
print("✅ custom.js overwritten with Matrix Theme support")

# ========== 2. Append Matrix Theme CSS ==========
matrix_css = """

/* Matrix Theme Overrides */
body[data-theme="matrix"] {
    background: #000 !important;
    background-image: none !important;
    color: #00ff00 !important;
}

body[data-theme="matrix"] .glass-card,
body[data-theme="matrix"] .card,
body[data-theme="matrix"] .bg-gray-900,
body[data-theme="matrix"] .bg-gray-950,
body[data-theme="matrix"] .bg-[#12161f],
body[data-theme="matrix"] .bg-[#1E2533] {
    background: rgba(0, 20, 0, 0.8) !important;
    border-color: rgba(0, 255, 0, 0.3) !important;
    color: #00ff00 !important;
}

body[data-theme="matrix"] .text-white {
    color: #00ff00 !important;
}

body[data-theme="matrix"] .text-gray-400 {
    color: #00cc66 !important;
}

body[data-theme="matrix"] header,
body[data-theme="matrix"] #sidebar,
body[data-theme="matrix"] nav.fixed.bottom-0 {
    background: rgba(0, 0, 0, 0.8) !important;
    border-color: rgba(0, 255, 0, 0.3) !important;
}
"""

with open('static/custom.css', 'a') as f:
    f.write(matrix_css)
print("✅ Matrix Theme CSS appended to custom.css")

# ========== 3. Patch settings.html to add Matrix Theme option ==========
settings_path = 'templates/partials/settings.html'
with open(settings_path, 'r') as f:
    html = f.read()

# Insert Matrix option after the Animated Stars option
old_animated_option = """<div data-theme-option="animated" onclick="setTheme('animated')" class="cursor-pointer bg-[#1E2533] border border-gray-800 rounded-xl p-4 flex items-center justify-between hover:bg-gray-800/50 transition">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-600 to-cyan-400"></div>
                <span class="text-white text-sm">Animated Stars</span>
            </div>
            <i class="fa-solid fa-check text-teal-400 hidden"></i>
        </div>"""

new_animated_plus_matrix = old_animated_option + """
        <div data-theme-option="matrix" onclick="setTheme('matrix')" class="cursor-pointer bg-[#1E2533] border border-gray-800 rounded-xl p-4 flex items-center justify-between hover:bg-gray-800/50 transition">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-green-500 to-black"></div>
                <span class="text-white text-sm">Matrix Rain</span>
            </div>
            <i class="fa-solid fa-check text-teal-400 hidden"></i>
        </div>"""

if old_animated_option in html:
    html = html.replace(old_animated_option, new_animated_plus_matrix)
    print("✅ Matrix Rain option added to App Customization")
else:
    print("⚠️ Animated Stars option not found, trying regex...")
    # Fallback: insert before the closing of the theme options container
    html = re.sub(r'(<div data-theme-option="animated".*?</div>)',
                  r'\1\n        <div data-theme-option="matrix" onclick="setTheme(\'matrix\')" class="cursor-pointer bg-[#1E2533] border border-gray-800 rounded-xl p-4 flex items-center justify-between hover:bg-gray-800/50 transition">\n            <div class="flex items-center gap-3">\n                <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-green-500 to-black"></div>\n                <span class="text-white text-sm">Matrix Rain</span>\n            </div>\n            <i class="fa-solid fa-check text-teal-400 hidden"></i>\n        </div>',
                  html, count=1, flags=re.DOTALL)
    print("✅ Matrix Rain option added via regex fallback")

with open(settings_path, 'w') as f:
    f.write(html)

print("🎉 Matrix theme patch completed. Restart server and hard refresh browser.")
