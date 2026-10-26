import os, re

# ========== 1. Update custom.js validThemes to include circuit ==========
with open('static/custom.js', 'r') as f:
    js = f.read()

old_valid = "const validThemes = ['light', 'black', 'animated', 'matrix'];"
new_valid = "const validThemes = ['light', 'black', 'animated', 'matrix', 'circuit'];"

if old_valid in js:
    js = js.replace(old_valid, new_valid)
    print("✅ validThemes updated to include 'circuit'.")
else:
    print("⚠️ validThemes line not found, trying regex...")
    # Fallback: find the array and insert circuit
    js = re.sub(r"const validThemes = \[([^\]]+)\]", r"const validThemes = [\1, 'circuit']", js, count=1)
    print("✅ validThemes updated via regex.")

with open('static/custom.js', 'w') as f:
    f.write(js)

# ========== 2. Append circuit theme CSS ==========
circuit_css = """

/* Circuit Grid Theme */
body[data-theme="circuit"] {
    background-color: #0a0f1a !important;
    background-image:
        linear-gradient(rgba(0, 255, 255, 0.08) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 255, 255, 0.08) 1px, transparent 1px),
        radial-gradient(circle at 25% 25%, rgba(0, 255, 255, 0.12) 0%, transparent 50%),
        radial-gradient(circle at 75% 75%, rgba(0, 255, 255, 0.12) 0%, transparent 50%) !important;
    background-size: 40px 40px, 40px 40px, 100% 100%, 100% 100% !important;
    color: #00e5ff !important;
}

body[data-theme="circuit"] .glass-card,
body[data-theme="circuit"] .card,
body[data-theme="circuit"] .bg-gray-900,
body[data-theme="circuit"] .bg-gray-950,
body[data-theme="circuit"] .bg-[#12161f],
body[data-theme="circuit"] .bg-[#1E2533] {
    background: rgba(16, 30, 50, 0.85) !important;
    border-color: rgba(0, 255, 255, 0.25) !important;
    color: #00e5ff !important;
}

body[data-theme="circuit"] .text-white {
    color: #e0f7fa !important;
}

body[data-theme="circuit"] .text-gray-400 {
    color: #80deea !important;
}

body[data-theme="circuit"] header,
body[data-theme="circuit"] #sidebar,
body[data-theme="circuit"] nav.fixed.bottom-0 {
    background: rgba(10, 15, 26, 0.85) !important;
    border-color: rgba(0, 255, 255, 0.2) !important;
}
"""

with open('static/custom.css', 'a') as f:
    f.write(circuit_css)
print("✅ Circuit Theme CSS appended.")

# ========== 3. Add Circuit Theme option in settings.html ==========
settings_path = 'templates/partials/settings.html'
with open(settings_path, 'r') as f:
    html = f.read()

# Insert after Matrix Rain option
old_matrix_option = """<div data-theme-option="matrix" onclick="setTheme('matrix')" class="cursor-pointer bg-[#1E2533] border border-gray-800 rounded-xl p-4 flex items-center justify-between hover:bg-gray-800/50 transition">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-green-500 to-black"></div>
                <span class="text-white text-sm">Matrix Rain</span>
            </div>
            <i class="fa-solid fa-check text-teal-400 hidden"></i>
        </div>"""

new_matrix_plus_circuit = old_matrix_option + """
        <div data-theme-option="circuit" onclick="setTheme('circuit')" class="cursor-pointer bg-[#1E2533] border border-gray-800 rounded-xl p-4 flex items-center justify-between hover:bg-gray-800/50 transition">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-900"></div>
                <span class="text-white text-sm">Circuit Grid</span>
            </div>
            <i class="fa-solid fa-check text-teal-400 hidden"></i>
        </div>"""

if old_matrix_option in html:
    html = html.replace(old_matrix_option, new_matrix_plus_circuit)
    print("✅ Circuit Grid option added to App Customization.")
else:
    # Fallback: insert before closing of theme container
    html = re.sub(r'(<div data-theme-option="matrix".*?</div>)',
                  r'\1\n        <div data-theme-option="circuit" onclick="setTheme(\'circuit\')" class="cursor-pointer bg-[#1E2533] border border-gray-800 rounded-xl p-4 flex items-center justify-between hover:bg-gray-800/50 transition">\n            <div class="flex items-center gap-3">\n                <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-900"></div>\n                <span class="text-white text-sm">Circuit Grid</span>\n            </div>\n            <i class="fa-solid fa-check text-teal-400 hidden"></i>\n        </div>',
                  html, count=1, flags=re.DOTALL)
    print("✅ Circuit Grid option added via regex fallback.")

with open(settings_path, 'w') as f:
    f.write(html)

print("🎉 Circuit theme patch completed. Restart server and hard refresh browser.")
