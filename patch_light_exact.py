with open('static/custom.css', 'a') as f:
    f.write('''

/* ==================== LIGHT THEME EXACT COLOR OVERRIDES ==================== */
body[data-theme="light"] {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
}

/* Dark arbitrary background classes to light gray */
body[data-theme="light"] .bg-\\[\\#1C212E\\],
body[data-theme="light"] .bg-\\[\\#12161f\\],
body[data-theme="light"] .bg-\\[\\#1E2533\\],
body[data-theme="light"] .bg-\\[\\#0B0E14\\] {
    background: #F3F4F6 !important;
    background-color: #F3F4F6 !important;
    border-color: #E5E7EB !important;
}

/* Text color overrides */
body[data-theme="light"] .text-white {
    color: #111827 !important;
}
body[data-theme="light"] .text-gray-400 {
    color: #6B7280 !important;
}
body[data-theme="light"] .text-gray-500 {
    color: #6B7280 !important;
}
body[data-theme="light"] .text-gray-600 {
    color: #4B5563 !important;
}
body[data-theme="light"] .text-gray-300 {
    color: #9CA3AF !important;
}

/* Main Wallet Card (white) */
body[data-theme="light"] .bg-gray-900,
body[data-theme="light"] .bg-gray-950 {
    background: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
}

/* Boxes (Receive, Deposit, Cards) */
body[data-theme="light"] .bg-gray-100,
body[data-theme="light"] .bg-gray-50,
body[data-theme="light"] .feature-card,
body[data-theme="light"] .grid-item {
    background: #F3F4F6 !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 12px !important;
}

/* Buttons - View All */
body[data-theme="light"] .bg-gray-100 {
    background: #F3F4F6 !important;
}

/* Bottom Navigation */
body[data-theme="light"] nav.fixed.bottom-0 {
    background: #FFFFFF !important;
    border-top: 1px solid #E5E7EB !important;
}
body[data-theme="light"] nav.fixed.bottom-0 i,
body[data-theme="light"] nav.fixed.bottom-0 .fa-solid {
    color: #9CA3AF !important;
}
body[data-theme="light"] nav.fixed.bottom-0 .active,
body[data-theme="light"] nav.fixed.bottom-0 .bg-teal-500\\/10,
body[data-theme="light"] nav.fixed.bottom-0 .text-teal-400 {
    color: #111827 !important;
}

/* Icon Colors */
body[data-theme="light"] .fa-bitcoin,
body[data-theme="light"] .bitcoin-symbol,
body[data-theme="light"] [class*="bitcoin"] {
    color: #F7931A !important;
}
body[data-theme="light"] .fa-ethereum,
body[data-theme="light"] .ethereum-symbol,
body[data-theme="light"] [class*="ethereum"] {
    color: #627EEA !important;
}
body[data-theme="light"] .fa-qrcode {
    color: #000000 !important;
}

/* Main Wallet Icon (blue) */
body[data-theme="light"] .bg-blue-500,
body[data-theme="light"] .bg-blue-600,
body[data-theme="light"] .bg-indigo-600,
body[data-theme="light"] .bg-teal-600 {
    background: #3B82F6 !important;
    color: white !important;
}

/* Inputs */
body[data-theme="light"] input,
body[data-theme="light"] select,
body[data-theme="light"] textarea {
    background-color: #FFFFFF !important;
    border: 1px solid #D1D5DB !important;
    color: #111827 !important;
}
''')

print("✅ Light theme exact overrides appended.")
