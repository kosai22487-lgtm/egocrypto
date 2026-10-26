with open('static/custom.css', 'a') as f:
    f.write('''

/* ==================== LIGHT THEME SPECIFICATIONS ==================== */
body[data-theme="light"] {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    background-image: none !important;
}

/* Boxes (Receiving, Deposit, Buy with Cards) */
body[data-theme="light"] .glass-card,
body[data-theme="light"] .card,
body[data-theme="light"] .bg-gray-900,
body[data-theme="light"] .bg-gray-950,
body[data-theme="light"] .bg-[#12161f],
body[data-theme="light"] .bg-[#1E2533],
body[data-theme="light"] .feature-card,
body[data-theme="light"] .grid-item {
    background: #F3F4F6 !important;
    background-color: #F3F4F6 !important;
    border: 1px solid #E5E7EB !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03) !important;
    color: #111827 !important;
    border-radius: 12px !important; /* rounded-xl */
}

/* Main title */
body[data-theme="light"] h1,
body[data-theme="light"] h2,
body[data-theme="light"] h3,
body[data-theme="light"] .hero-title,
body[data-theme="light"] .auth-title,
body[data-theme="light"] .reg-title {
    color: #111827 !important;
    font-weight: 700 !important;
}

/* Box labels (Receive crypto, Deposit...) */
body[data-theme="light"] .font-bold,
body[data-theme="light"] .font-semibold {
    color: #000000 !important;
    font-weight: 600 !important;
}

/* Icon + text (Bitcoin 0 BTC, Ethereum) */
body[data-theme="light"] .text-gray-600,
body[data-theme="light"] .text-gray-700,
body[data-theme="light"] .text-gray-500 {
    color: #4B5563 !important;
}

/* Prices ($0.00) */
body[data-theme="light"] .text-gray-400 {
    color: #6B7280 !important;
}

/* Specific text overrides */
body[data-theme="light"] .text-white {
    color: #111827 !important;
}

/* Bottom Navigation */
body[data-theme="light"] nav.fixed.bottom-0 {
    background: #FFFFFF !important;
    border-top: 1px solid #E5E7EB !important;
}

body[data-theme="light"] nav.fixed.bottom-0 i,
body[data-theme="light"] nav.fixed.bottom-0 .fa-solid {
    color: #9CA3AF !important; /* text-gray-400 */
}

body[data-theme="light"] nav.fixed.bottom-0 .bg-teal-500\\/10,
body[data-theme="light"] nav.fixed.bottom-0 .active {
    color: #111827 !important; /* active icon black */
}

/* Icon colors for Bitcoin, Ethereum, etc (if using text icons) */
body[data-theme="light"] .fa-bitcoin,
body[data-theme="light"] .bitcoin-icon {
    color: #F7931A !important;
}
body[data-theme="light"] .fa-ethereum,
body[data-theme="light"] .ethereum-icon {
    color: #627EEA !important;
}
body[data-theme="light"] .fa-qrcode,
body[data-theme="light"] .fa-barcode {
    color: #000000 !important;
}

/* Inputs and selects */
body[data-theme="light"] input,
body[data-theme="light"] select,
body[data-theme="light"] textarea {
    background-color: #FFFFFF !important;
    border: 1px solid #D1D5DB !important;
    color: #111827 !important;
}

body[data-theme="light"] .auth-input,
body[data-theme="light"] .reg-input {
    background-color: #F9FAFB !important;
    border-color: #D1D5DB !important;
}
''')

print("✅ Light theme specification CSS appended successfully.")
