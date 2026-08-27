import os

# ========== 1. Overwrite custom.js with theme manager + particle conditional ==========
custom_js = """
// Theme Manager
(function(){
    const validThemes = ['light', 'black', 'animated'];
    const DEFAULT_THEME = 'animated';

    function getTheme() {
        return localStorage.getItem('egocrypto_theme') || DEFAULT_THEME;
    }

    function applyTheme(theme) {
        if (!validThemes.includes(theme)) theme = DEFAULT_THEME;
        document.body.setAttribute('data-theme', theme);
        localStorage.setItem('egocrypto_theme', theme);

        // Toggle particle canvas & blobs
        const canvas = document.getElementById('particle-canvas');
        const blobs = document.querySelectorAll('.background-blob');
        if (theme === 'animated') {
            if (canvas) canvas.style.display = 'block';
            blobs.forEach(b => b.style.display = 'block');
        } else {
            if (canvas) canvas.style.display = 'none';
            blobs.forEach(b => b.style.display = 'none');
        }
    }

    // Expose globally
    window.setTheme = function(theme) {
        applyTheme(theme);
        updateThemeSelectionUI();
    };

    function updateThemeSelectionUI() {
        const current = getTheme();
        document.querySelectorAll('[data-theme-option]').forEach(el => {
            const val = el.getAttribute('data-theme-option');
            if (val === current) {
                el.classList.add('border-teal-500', 'bg-teal-500/20');
            } else {
                el.classList.remove('border-teal-500', 'bg-teal-500/20');
            }
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        applyTheme(getTheme());
        updateThemeSelectionUI();
    });
})();

// Particle Background only when animated theme
(function(){
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

    for (let i = 0; i < 80; i++) particles.push(new Particle());

    function animate() {
        ctx.clearRect(0, 0, width, height);
        particles.forEach(p => { p.update(); p.draw(); });
        requestAnimationFrame(animate);
    }
    animate();
})();

// Add floating blobs only when animated theme
document.addEventListener('DOMContentLoaded', () => {
    const theme = localStorage.getItem('egocrypto_theme') || 'animated';
    if (theme !== 'animated') return;
    if (!document.querySelector('.background-blob')) {
        const blobDiv = document.createElement('div');
        blobDiv.innerHTML = `<div class="background-blob blob-1"></div><div class="background-blob blob-2"></div><div class="background-blob blob-3"></div>`;
        document.body.appendChild(blobDiv);
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
print("✅ custom.js overwritten with theme manager")

# ========== 2. Append theme CSS to custom.css ==========
theme_css = """

/* ==================== THEME CUSTOMIZATION ==================== */
body[data-theme="light"] {
    background: #F5F7FA !important;
    background-image: none !important;
    color: #111827 !important;
}

body[data-theme="light"] .bg-gray-900,
body[data-theme="light"] .bg-gray-950,
body[data-theme="light"] .bg-[#12161f],
body[data-theme="light"] .bg-[#1E2533],
body[data-theme="light"] .card,
body[data-theme="light"] .glass-card {
    background: #ffffff !important;
    border: 1px solid rgba(0,0,0,0.08) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    color: #111827 !important;
}

body[data-theme="light"] .text-white {
    color: #111827 !important;
}

body[data-theme="light"] .text-gray-400 {
    color: #4B5563 !important;
}

body[data-theme="light"] header,
body[data-theme="light"] #sidebar,
body[data-theme="light"] nav.fixed.bottom-0 {
    background: rgba(255,255,255,0.8) !important;
    border-color: rgba(0,0,0,0.1) !important;
}

body[data-theme="black"] {
    background: #000000 !important;
    background-image: none !important;
    color: #ffffff !important;
}

body[data-theme="black"] .card,
body[data-theme="black"] .glass-card {
    background: #111111 !important;
    border: 1px solid #222 !important;
}
"""

with open('static/custom.css', 'a') as f:
    f.write(theme_css)
print("✅ Theme CSS appended to custom.css")

# ========== 3. Patch settings.html ==========
settings_path = 'templates/partials/settings.html'
with open(settings_path, 'r') as f:
    html = f.read()

# Replace App Customization button onclick
html = html.replace(
    """<button onclick="alert('App Customization coming soon')" class="w-full bg-[#1E2533] border border-gray-800 rounded-xl p-4 flex items-center justify-between text-white text-sm hover:bg-gray-800/50 transition">""",
    """<button onclick="showAppCustomization()" class="w-full bg-[#1E2533] border border-gray-800 rounded-xl p-4 flex items-center justify-between text-white text-sm hover:bg-gray-800/50 transition">"""
)

# Add App Customization section after Security Section
app_section = """
<!-- App Customization Section (Hidden) -->
<div id="app-customization-section" class="hidden mb-8">
    <button onclick="showSection('menu')" class="w-full bg-gray-800 hover:bg-gray-700 text-white font-bold py-2.5 rounded-xl text-sm transition mb-4">
        <i class="fa-solid fa-arrow-left mr-2"></i>Back to Settings
    </button>

    <h3 class="text-teal-400 font-bold mb-4 text-sm"><i class="fa-solid fa-palette mr-2"></i>App Theme</h3>
    <div class="space-y-3">
        <div data-theme-option="light" onclick="setTheme('light')" class="cursor-pointer bg-[#1E2533] border border-gray-800 rounded-xl p-4 flex items-center justify-between hover:bg-gray-800/50 transition">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-white border border-gray-300"></div>
                <span class="text-white text-sm">Light Theme</span>
            </div>
            <i class="fa-solid fa-check text-teal-400 hidden"></i>
        </div>
        <div data-theme-option="black" onclick="setTheme('black')" class="cursor-pointer bg-[#1E2533] border border-gray-800 rounded-xl p-4 flex items-center justify-between hover:bg-gray-800/50 transition">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-black border border-gray-500"></div>
                <span class="text-white text-sm">Black Theme</span>
            </div>
            <i class="fa-solid fa-check text-teal-400 hidden"></i>
        </div>
        <div data-theme-option="animated" onclick="setTheme('animated')" class="cursor-pointer bg-[#1E2533] border border-gray-800 rounded-xl p-4 flex items-center justify-between hover:bg-gray-800/50 transition">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-600 to-cyan-400"></div>
                <span class="text-white text-sm">Animated Stars</span>
            </div>
            <i class="fa-solid fa-check text-teal-400 hidden"></i>
        </div>
    </div>
</div>
"""
# Insert before Log Out button
html = html.replace('<!-- Log Out -->', app_section + '\n<!-- Log Out -->')

# Update showSection function to handle app section
html = html.replace(
    """function showSection(section) {
        const mainMenu = document.getElementById('main-menu');
        document.getElementById('account-section').classList.add('hidden');
        document.getElementById('security-section').classList.add('hidden');
        if (section === 'account') {
            document.getElementById('account-section').classList.remove('hidden');
            mainMenu.classList.add('hidden');
        } else if (section === 'security') {
            document.getElementById('security-section').classList.remove('hidden');
            mainMenu.classList.add('hidden');
        } else {
            mainMenu.classList.remove('hidden');
        }
    }""",
    """function showSection(section) {
        const mainMenu = document.getElementById('main-menu');
        document.getElementById('account-section').classList.add('hidden');
        document.getElementById('security-section').classList.add('hidden');
        document.getElementById('app-customization-section').classList.add('hidden');
        if (section === 'account') {
            document.getElementById('account-section').classList.remove('hidden');
            mainMenu.classList.add('hidden');
        } else if (section === 'security') {
            document.getElementById('security-section').classList.remove('hidden');
            mainMenu.classList.add('hidden');
        } else if (section === 'app') {
            document.getElementById('app-customization-section').classList.remove('hidden');
            mainMenu.classList.add('hidden');
        } else {
            mainMenu.classList.remove('hidden');
        }
    }

    function showAppCustomization() {
        showSection('app');
    }"""
)

with open(settings_path, 'w') as f:
    f.write(html)
print("✅ settings.html patched with App Customization section")

print("🎉 Theme customization patch completed. Restart server and hard refresh browser.")
