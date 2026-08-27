with open('static/custom.css', 'a') as f:
    f.write('''

/* ==================== LIGHT THEME OVERRIDE ==================== */
body[data-theme="light"] {
    background: #ffffff !important;
    background-color: #ffffff !important;
    background-image: none !important;
    color: #111827 !important;
}

body[data-theme="light"] .glass-card,
body[data-theme="light"] .card,
body[data-theme="light"] .bg-gray-900,
body[data-theme="light"] .bg-gray-950,
body[data-theme="light"] .bg-[#12161f],
body[data-theme="light"] .bg-[#1E2533],
body[data-theme="light"] .feature-card,
body[data-theme="light"] .grid-item {
    background: #ffffff !important;
    background-color: #ffffff !important;
    border: 1px solid #e5e7eb !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    color: #111827 !important;
}

body[data-theme="light"] .text-white {
    color: #111827 !important;
}

body[data-theme="light"] .text-gray-400 {
    color: #4b5563 !important;
}

body[data-theme="light"] header,
body[data-theme="light"] #sidebar,
body[data-theme="light"] nav.fixed.bottom-0 {
    background: rgba(255,255,255,0.92) !important;
    backdrop-filter: blur(12px);
    border-color: #e5e7eb !important;
}

body[data-theme="light"] .sidebar-link {
    color: #4b5563 !important;
}

body[data-theme="light"] .sidebar-link.active {
    background: #e0f2fe !important;
    border-color: #0ea5e9 !important;
    color: #0284c7 !important;
}

body[data-theme="light"] input,
body[data-theme="light"] select,
body[data-theme="light"] textarea {
    background-color: #ffffff !important;
    border: 1px solid #d1d5db !important;
    color: #111827 !important;
}

body[data-theme="light"] .auth-input,
body[data-theme="light"] .reg-input {
    background-color: #f9fafb !important;
    border-color: #d1d5db !important;
}

body[data-theme="light"] .bg-gray-800 {
    background: #f3f4f6 !important;
    color: #111827 !important;
}

body[data-theme="light"] .bg-teal-600,
body[data-theme="light"] .bg-blue-600,
body[data-theme="light"] .bg-indigo-600,
body[data-theme="light"] .btn-primary,
body[data-theme="light"] .auth-btn-gradient {
    background: linear-gradient(135deg, #2563eb, #06b6d4) !important;
    color: #ffffff !important;
}

body[data-theme="light"] table {
    background: #ffffff !important;
}
body[data-theme="light"] thead {
    background: #f9fafb !important;
}
body[data-theme="light"] tbody tr {
    background: #ffffff !important;
    color: #111827 !important;
}
''')

print("✅ Light theme overrides appended successfully.")
