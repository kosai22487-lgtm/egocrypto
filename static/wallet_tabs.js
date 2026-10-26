// ==================== Wallet Tabs (Earn/NFTs) ====================
function switchWalletTab(tab) {
    // Hide all containers
    document.getElementById('wallet-coins-container').classList.add('hidden');
    document.getElementById('wallet-earn-container').classList.add('hidden');
    document.getElementById('wallet-nfts-container').classList.add('hidden');

    // Remove active state from all tabs
    document.querySelectorAll('[id^="wallet-tab-"]').forEach(t => {
        t.classList.remove('text-white', 'border-b-2', 'border-white');
        t.classList.add('hover:text-white', 'cursor-pointer', 'pb-2');
    });

    // Activate selected tab
    const activeTab = document.getElementById('wallet-tab-' + tab);
    activeTab.classList.add('text-white', 'border-b-2', 'border-white');
    activeTab.classList.remove('hover:text-white', 'cursor-pointer', 'pb-2');

    // Show content
    if (tab === 'crypto') {
        document.getElementById('wallet-coins-container').classList.remove('hidden');
    } else if (tab === 'earn') {
        renderEarnTab();
        document.getElementById('wallet-earn-container').classList.remove('hidden');
    } else if (tab === 'nfts') {
        renderNftTab();
        document.getElementById('wallet-nfts-container').classList.remove('hidden');
    }
}

// ==================== Earn Tab ====================
function renderEarnTab() {
    const container = document.getElementById('wallet-earn-container');

    // Stablecoin Earn (20 items)
    const stablecoins = [
        { symbol: 'USDT', name: 'Tether', apy: '2.67', price: '$1.00', change: '+0.01%' },
        { symbol: 'USDC', name: 'USD Coin', apy: '4.20', price: '$1.00', change: '+0.00%' },
        { symbol: 'DAI', name: 'Dai', apy: '3.10', price: '$1.00', change: '+0.02%' },
        { symbol: 'BUSD', name: 'Binance USD', apy: '2.50', price: '$1.00', change: '+0.01%' },
        { symbol: 'TUSD', name: 'TrueUSD', apy: '2.20', price: '$1.00', change: '+0.00%' },
        { symbol: 'USDP', name: 'Pax Dollar', apy: '2.80', price: '$1.00', change: '+0.01%' },
        { symbol: 'GUSD', name: 'Gemini Dollar', apy: '2.10', price: '$1.00', change: '+0.00%' },
        { symbol: 'FRAX', name: 'Frax', apy: '3.50', price: '$1.00', change: '+0.03%' },
        { symbol: 'LUSD', name: 'Liquity USD', apy: '1.90', price: '$1.00', change: '+0.00%' },
        { symbol: 'sUSD', name: 'sUSD', apy: '2.40', price: '$1.00', change: '+0.01%' },
        // Additional 10 stablecoins
        { symbol: 'FDUSD', name: 'First Digital USD', apy: '2.90', price: '$1.00', change: '+0.01%' },
        { symbol: 'EURS', name: 'STASIS EURS', apy: '1.80', price: '$1.08', change: '+0.05%' },
        { symbol: 'EURT', name: 'Tether EURt', apy: '1.60', price: '$1.08', change: '+0.03%' },
        { symbol: 'XSGD', name: 'XSGD', apy: '2.00', price: '$0.74', change: '+0.02%' },
        { symbol: 'ZUSD', name: 'ZUSD', apy: '2.30', price: '$1.00', change: '+0.00%' },
        { symbol: 'MIM', name: 'Magic Internet Money', apy: '3.20', price: '$0.99', change: '+0.10%' },
        { symbol: 'USTC', name: 'TerraClassicUSD', apy: '1.50', price: '$0.02', change: '-0.20%' },
        { symbol: 'TRUMP', name: 'TrumpCoin', apy: '2.70', price: '$0.10', change: '+0.50%' },
        { symbol: 'XCHF', name: 'CryptoFranc', apy: '1.75', price: '$1.10', change: '+0.01%' },
        { symbol: 'CADC', name: 'CAD Coin', apy: '1.95', price: '$0.74', change: '+0.02%' }
    ];

    // Native AI Staking (20 items)
    const nativeStaking = [
        { symbol: 'ETH', name: 'Ethereum', price: '$1,899.24', change: '+0.48%', apy: '2.51' },
        { symbol: 'BNB', name: 'BNB Smart Chain', price: '$603.46', change: '+0.06%', apy: '1.98' },
        { symbol: 'SOL', name: 'Solana', price: '$75.58', change: '+0.65%', apy: '5.44' },
        { symbol: 'BTC', name: 'Bitcoin', price: '$64,200', change: '+0.25%', apy: '1.20' },
        { symbol: 'ADA', name: 'Cardano', price: '$0.35', change: '+0.80%', apy: '3.10' },
        { symbol: 'DOT', name: 'Polkadot', price: '$4.20', change: '+0.30%', apy: '4.00' },
        { symbol: 'MATIC', name: 'Polygon', price: '$0.52', change: '+0.55%', apy: '3.80' },
        { symbol: 'AVAX', name: 'Avalanche', price: '$28.50', change: '+0.70%', apy: '5.00' },
        { symbol: 'LINK', name: 'Chainlink', price: '$13.20', change: '+0.40%', apy: '2.90' },
        { symbol: 'ATOM', name: 'Cosmos', price: '$6.80', change: '+0.60%', apy: '6.00' },
        // Additional 10 native staking
        { symbol: 'XRP', name: 'XRP', price: '$0.52', change: '+0.30%', apy: '2.10' },
        { symbol: 'DOGE', name: 'Dogecoin', price: '$0.12', change: '+0.45%', apy: '1.80' },
        { symbol: 'LTC', name: 'Litecoin', price: '$70.24', change: '+0.20%', apy: '2.40' },
        { symbol: 'UNI', name: 'Uniswap', price: '$6.45', change: '+0.35%', apy: '3.30' },
        { symbol: 'ICP', name: 'Internet Computer', price: '$8.75', change: '+0.30%', apy: '4.50' },
        { symbol: 'FIL', name: 'Filecoin', price: '$4.15', change: '+0.25%', apy: '3.00' },
        { symbol: 'XLM', name: 'Stellar', price: '$0.11', change: '+0.15%', apy: '1.90' },
        { symbol: 'TRX', name: 'TRON', price: '$0.09', change: '+0.10%', apy: '2.00' },
        { symbol: 'ETC', name: 'Ethereum Classic', price: '$18.90', change: '+0.50%', apy: '2.80' },
        { symbol: 'NEAR', name: 'NEAR Protocol', price: '$4.80', change: '+0.60%', apy: '5.50' }
    ];

    function renderItem(item) {
        const logo = `https://assets.coincap.io/assets/icons/${item.symbol.toLowerCase()}@2x.png`;
        return `<div class="flex items-center justify-between p-2 rounded-xl hover:bg-gray-800/30 transition cursor-pointer" onclick="window.location.href='/ai-arbitrage'">
            <div class="flex items-center space-x-3">
                <img src="${logo}" alt="${item.symbol}" class="w-8 h-8 rounded-full" onerror="this.style.display='none'">
                <div>
                    <div class="text-white font-medium text-sm">${item.name}</div>
                    <div class="text-xs text-gray-400">${item.price} <span class="text-emerald-400">${item.change}</span></div>
                </div>
            </div>
            <div class="text-right">
                <div class="text-[10px] text-gray-400">up to</div>
                <div class="text-sm font-bold text-white">${item.apy}% <span class="text-xs text-gray-400">APY</span></div>
            </div>
        </div>`;
    }

    function buildSection(title, items) {
        const safeId = title.replace(/\s/g, '');
        return `<div class="mb-6">
            <h4 class="text-sm font-bold text-white mb-2">${title}</h4>
            <div class="bg-gray-900/50 border border-gray-800 rounded-2xl p-3">
                <div class="space-y-1" id="items-${safeId}">
                    ${items.slice(0, 3).map(renderItem).join('')}
                </div>
                <div id="extra-${safeId}" class="hidden space-y-1">
                    ${items.slice(3).map(renderItem).join('')}
                </div>
                <button type="button" onclick="toggleEarnExtra('${safeId}', this)" class="w-full text-center text-xs text-teal-400 hover:text-teal-300 py-2 font-semibold">
                    <span class="view-all-text">View all</span> <span class="chevron">›</span>
                </button>
            </div>
        </div>`;
    }

    container.innerHTML = buildSection('Stablecoin Earn', stablecoins) + buildSection('Native AI Staking', nativeStaking);
}

function toggleEarnExtra(sectionId, btn) {
    const extra = document.getElementById('extra-' + sectionId);
    const text = btn.querySelector('.view-all-text');
    const chevron = btn.querySelector('.chevron');
    if (extra.classList.contains('hidden')) {
        extra.classList.remove('hidden');
        text.textContent = 'View less';
        chevron.textContent = '⌄';
    } else {
        extra.classList.add('hidden');
        text.textContent = 'View all';
        chevron.textContent = '›';
    }
}

// ==================== NFTs Tab ====================
const nftStaticData = [
    // Original 10
    { symbol: 'BTC', name: 'Bitcoin', price: '$64,200', change: '+0.25%' },
    { symbol: 'ETH', name: 'Ethereum', price: '$1,899.24', change: '+0.48%' },
    { symbol: 'USDT', name: 'Tether', price: '$1.00', change: '+0.01%' },
    { symbol: 'SOL', name: 'Solana', price: '$75.58', change: '+0.65%' },
    { symbol: 'BNB', name: 'BNB', price: '$603.46', change: '+0.06%' },
    { symbol: 'XRP', name: 'XRP', price: '$0.52', change: '+0.30%' },
    { symbol: 'ADA', name: 'Cardano', price: '$0.35', change: '+0.80%' },
    { symbol: 'DOGE', name: 'Dogecoin', price: '$0.12', change: '+0.45%' },
    { symbol: 'DOT', name: 'Polkadot', price: '$4.20', change: '+0.30%' },
    { symbol: 'MATIC', name: 'Polygon', price: '$0.52', change: '+0.55%' },
    // Additional 10
    { symbol: 'LTC', name: 'Litecoin', price: '$70.24', change: '+0.20%' },
    { symbol: 'LINK', name: 'Chainlink', price: '$13.20', change: '+0.40%' },
    { symbol: 'UNI', name: 'Uniswap', price: '$6.45', change: '+0.35%' },
    { symbol: 'AVAX', name: 'Avalanche', price: '$28.50', change: '+0.70%' },
    { symbol: 'ATOM', name: 'Cosmos', price: '$6.80', change: '+0.60%' },
    { symbol: 'XLM', name: 'Stellar', price: '$0.11', change: '+0.15%' },
    { symbol: 'TRX', name: 'TRON', price: '$0.09', change: '+0.10%' },
    { symbol: 'ETC', name: 'Ethereum Classic', price: '$18.90', change: '+0.50%' },
    { symbol: 'FIL', name: 'Filecoin', price: '$4.15', change: '+0.25%' },
    { symbol: 'ICP', name: 'Internet Computer', price: '$8.75', change: '+0.30%' }
];

function renderNftTab() {
    const container = document.getElementById('wallet-nfts-container');
    
    // Fetch live prices from CoinGecko
    fetch('/api/coingecko/markets')
        .then(r => r.json())
        .then(liveData => {
            if (liveData && liveData.length > 0) {
                const priceMap = {};
                liveData.forEach(c => { priceMap[c.symbol] = c; });
                
                // Update nftStaticData with live prices
                nftStaticData.forEach(item => {
                    const live = priceMap[item.symbol];
                    if (live) {
                        item.price = '$' + live.current_price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
                        item.change = (live.price_change_percentage_24h >= 0 ? '+' : '') + live.price_change_percentage_24h.toFixed(2) + '%';
                    }
                });
                
                document.getElementById('nft-list-container').innerHTML = buildList(nftStaticData);
            }
        })
        .catch(err => console.error('NFT price fetch error:', err));

    function buildSearchBar() {
        return `<div class="px-3 py-2 rounded-full bg-gray-800/60 flex items-center gap-2 mb-3">
            <i class="fa-solid fa-search text-gray-400 text-xs"></i>
            <input type="text" placeholder="Search coins" class="bg-transparent flex-1 text-sm text-white placeholder-gray-500 focus:outline-none" oninput="filterNftList(this.value)">
            <i class="fa-solid fa-xmark text-gray-400 text-xs cursor-pointer" onclick="clearNftSearch()"></i>
        </div>`;
    }

    function buildList(items) {
        return items.map(item => {
            const logo = `https://assets.coincap.io/assets/icons/${item.symbol.toLowerCase()}@2x.png`;
            const changeNum = parseFloat(item.change.replace('%', '')) || 0;
            const changeColor = changeNum >= 0 ? 'text-emerald-400' : 'text-rose-400';
            return `<div class="flex items-center justify-between py-3 px-1 border-b border-gray-800/50 cursor-pointer" onclick="window.location.href='/ai-arbitrage'">
                <div class="flex items-center gap-3">
                    <img src="${logo}" alt="${item.symbol}" class="w-8 h-8 rounded-full" onerror="this.style.display='none'">
                    <div>
                        <div class="text-white text-sm font-semibold">${item.name}</div>
                        <div class="text-xs text-gray-400">${item.symbol} · $${item.price}</div>
                    </div>
                </div>
                <div class="text-right">
                    <div class="text-white text-sm font-bold">${item.price}</div>
                    <div class="text-xs ${changeColor}">${item.change}</div>
                </div>
            </div>`;
        }).join('');
    }

    container.innerHTML = `
        ${buildSearchBar()}
        <div class="flex justify-between items-center mb-2">
            <h4 class="text-white font-bold text-sm">Crypto</h4>
            <div class="flex items-center gap-1 text-xs text-gray-400">
                <i class="fa-solid fa-globe"></i> All Networks <i class="fa-solid fa-chevron-down"></i>
            </div>
        </div>
        <div id="nft-list-container">
            ${buildList(nftStaticData)}
        </div>
    `;

    window.nftData = nftStaticData;
    window.filterNftList = function(value) {
        const filtered = nftStaticData.filter(item =>
            item.name.toLowerCase().includes(value.toLowerCase()) ||
            item.symbol.toLowerCase().includes(value.toLowerCase())
        );
        document.getElementById('nft-list-container').innerHTML = buildList(filtered);
    };
    window.clearNftSearch = function() {
        document.querySelector('#wallet-nfts-container input').value = '';
        document.getElementById('nft-list-container').innerHTML = buildList(nftStaticData);
    };
}
