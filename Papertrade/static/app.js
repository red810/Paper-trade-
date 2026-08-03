const API_BASE = ""; // Same origin
let activeToken = localStorage.getItem("papertrade_token") || null;
let activeUser = localStorage.getItem("papertrade_user") || null;
let currentQuotedPrice = 0;
let currentQuotedSymbol = "";

// Toast helper
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  let icon = "fa-circle-info";
  if (type === "success") icon = "fa-circle-check";
  if (type === "error") icon = "fa-triangle-exclamation";
  
  toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
  container.appendChild(toast);
  
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Auth Tab Switcher
function switchAuthTab(tab) {
  const tabLogin = document.getElementById("tab-login");
  const tabRegister = document.getElementById("tab-register");
  const formLogin = document.getElementById("form-login");
  const formRegister = document.getElementById("form-register");
  const alertBox = document.getElementById("auth-alert");

  alertBox.classList.add("hidden");

  if (tab === "login") {
    tabLogin.classList.add("active");
    tabRegister.classList.remove("active");
    formLogin.classList.remove("hidden");
    formRegister.classList.add("hidden");
  } else {
    tabRegister.classList.add("active");
    tabLogin.classList.remove("active");
    formRegister.classList.remove("hidden");
    formLogin.classList.add("hidden");
  }
}

// Subtab Switcher
function switchSubtab(subtab) {
  const subtabs = ["leaderboard", "badges", "history"];
  subtabs.forEach((st) => {
    const btn = document.getElementById(`subtab-${st}`);
    const panel = document.getElementById(`panel-${st}`);
    if (st === subtab) {
      btn.classList.add("active");
      panel.classList.remove("hidden");
    } else {
      btn.classList.remove("active");
      panel.classList.add("hidden");
    }
  });
}

// Auth Handlers
async function handleLogin(e) {
  e.preventDefault();
  const usernameInput = document.getElementById("login-username").value.trim();
  const passwordInput = document.getElementById("login-password").value;
  const alertBox = document.getElementById("auth-alert");

  alertBox.classList.add("hidden");

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ username: usernameInput, password: passwordInput })
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Login failed");
    }

    activeToken = data.access_token;
    activeUser = usernameInput;
    localStorage.setItem("papertrade_token", activeToken);
    localStorage.setItem("papertrade_user", activeUser);

    showToast(`Welcome back, ${activeUser}!`, "success");
    initApp();
  } catch (err) {
    alertBox.textContent = err.message;
    alertBox.className = "alert alert-error";
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const username = document.getElementById("reg-username").value.trim();
  const email = document.getElementById("reg-email").value.trim();
  const password = document.getElementById("reg-password").value;
  const alertBox = document.getElementById("auth-alert");

  alertBox.classList.add("hidden");

  try {
    const res = await fetch(`${API_BASE}/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password })
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Registration failed");
    }

    showToast("Account created successfully! Logging you in...", "success");

    // Automatically log in
    document.getElementById("login-username").value = username;
    document.getElementById("login-password").value = password;
    switchAuthTab("login");
    
    // Auto submit login
    const loginRes = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ username, password })
    });

    const loginData = await loginRes.json();
    if (loginRes.ok) {
      activeToken = loginData.access_token;
      activeUser = username;
      localStorage.setItem("papertrade_token", activeToken);
      localStorage.setItem("papertrade_user", activeUser);
      initApp();
    }
  } catch (err) {
    alertBox.textContent = err.message;
    alertBox.className = "alert alert-error";
  }
}

function logout() {
  activeToken = null;
  activeUser = null;
  localStorage.removeItem("papertrade_token");
  localStorage.removeItem("papertrade_user");
  document.getElementById("app-screen").classList.add("hidden");
  document.getElementById("auth-screen").classList.remove("hidden");
  showToast("Logged out successfully.", "info");
}

// App Logic
function getHeaders() {
  return {
    "Authorization": `Bearer ${activeToken}`,
    "Content-Type": "application/json"
  };
}

async function initApp() {
  if (!activeToken) {
    document.getElementById("auth-screen").classList.remove("hidden");
    document.getElementById("app-screen").classList.add("hidden");
    return;
  }

  document.getElementById("auth-screen").classList.add("hidden");
  document.getElementById("app-screen").classList.remove("hidden");
  document.getElementById("user-display-name").textContent = activeUser || "Trader";

  await refreshData();
}

async function refreshData() {
  if (!activeToken) return;

  try {
    await Promise.all([
      fetchSummary(),
      fetchHoldings(),
      fetchWatchlist(),
      fetchLeaderboard(),
      fetchBadges(),
      fetchHistory()
    ]);
  } catch (err) {
    if (err.message.includes("401") || err.message.includes("credentials")) {
      logout();
    }
  }
}

async function fetchSummary() {
  const res = await fetch(`${API_BASE}/portfolio/summary`, { headers: getHeaders() });
  if (!res.ok) return;
  const data = await res.json();
  
  document.getElementById("metric-net-worth").textContent = `$${data.net_worth.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
  document.getElementById("metric-cash-balance").textContent = `$${data.cash_balance.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
  document.getElementById("metric-invested-val").textContent = `$${data.invested_value.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
}

async function fetchHoldings() {
  const res = await fetch(`${API_BASE}/portfolio/holdings`, { headers: getHeaders() });
  if (!res.ok) return;
  const holdings = await res.json();

  const tbody = document.getElementById("holdings-tbody");
  if (holdings.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty-state">No holdings yet. Buy your first stock from the Live Trade Terminal!</td></tr>`;
    return;
  }

  tbody.innerHTML = holdings.map(h => {
    const isProfit = h.profit_loss >= 0;
    const pClass = isProfit ? "badge-profit" : "badge-loss";
    const pSign = isProfit ? "+" : "";
    return `
      <tr>
        <td><strong>${h.symbol}</strong></td>
        <td>${h.quantity}</td>
        <td>$${h.avg_buy_price.toFixed(2)}</td>
        <td>$${h.current_price.toFixed(2)}</td>
        <td>$${h.current_value.toFixed(2)}</td>
        <td class="${pClass}">${pSign}$${h.profit_loss.toFixed(2)} (${pSign}${h.profit_loss_percent.toFixed(2)}%)</td>
      </tr>
    `;
  }).join("");
}

async function fetchWatchlist() {
  const res = await fetch(`${API_BASE}/watchlist/`, { headers: getHeaders() });
  if (!res.ok) return;
  const items = await res.json();

  const tbody = document.getElementById("watchlist-tbody");
  if (items.length === 0) {
    tbody.innerHTML = `<tr><td colspan="3" class="empty-state">Your watchlist is empty. Search and add symbols above.</td></tr>`;
    return;
  }

  tbody.innerHTML = items.map(i => {
    const priceStr = i.current_price ? `$${i.current_price.toFixed(2)}` : "N/A";
    return `
      <tr>
        <td><strong>${i.symbol}</strong></td>
        <td>${priceStr}</td>
        <td>
          <button onclick="selectTicker('${i.symbol}')" class="btn btn-secondary btn-sm"><i class="fa-solid fa-chart-line"></i> Trade</button>
          <button onclick="removeFromWatchlist('${i.symbol}')" class="btn btn-rose btn-sm" style="padding:4px 8px;" title="Remove"><i class="fa-solid fa-trash"></i></button>
        </td>
      </tr>
    `;
  }).join("");
}

async function fetchLeaderboard() {
  const res = await fetch(`${API_BASE}/portfolio/leaderboard`, { headers: getHeaders() });
  if (!res.ok) return;
  const leaderboard = await res.json();

  const tbody = document.getElementById("leaderboard-tbody");
  tbody.innerHTML = leaderboard.map(l => `
    <tr>
      <td><strong>#${l.rank}</strong></td>
      <td>${l.username} ${l.username === activeUser ? '<span style="color:var(--accent-blue);">(You)</span>' : ''}</td>
      <td>$${l.cash_balance.toLocaleString('en-US', {minimumFractionDigits:2})}</td>
      <td>$${l.invested_value.toLocaleString('en-US', {minimumFractionDigits:2})}</td>
      <td><strong>$${l.net_worth.toLocaleString('en-US', {minimumFractionDigits:2})}</strong></td>
    </tr>
  `).join("");
}

async function fetchBadges() {
  const res = await fetch(`${API_BASE}/badges/`, { headers: getHeaders() });
  if (!res.ok) return;
  const badges = await res.json();

  document.getElementById("metric-badges-count").textContent = `${badges.length} Badge${badges.length === 1 ? '' : 's'}`;

  const grid = document.getElementById("badges-grid");
  if (badges.length === 0) {
    grid.innerHTML = `<div class="empty-state" style="grid-column: 1/-1;">No achievements unlocked yet. Execute trades to earn badges!</div>`;
    return;
  }

  grid.innerHTML = badges.map(b => `
    <div class="badge-card">
      <i class="fa-solid fa-award"></i>
      <h4>${b.badge_name}</h4>
      <span>Earned ${new Date(b.earned_at).toLocaleDateString()}</span>
    </div>
  `).join("");
}

async function fetchHistory() {
  const res = await fetch(`${API_BASE}/portfolio/transactions`, { headers: getHeaders() });
  if (!res.ok) return;
  const txs = await res.json();

  const tbody = document.getElementById("history-tbody");
  if (txs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-state">No transactions recorded yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = txs.map(t => {
    const isBuy = t.type === "BUY";
    const typeClass = isBuy ? "badge-profit" : "badge-loss";
    return `
      <tr>
        <td>${new Date(t.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</td>
        <td class="${typeClass}"><strong>${t.type}</strong></td>
        <td><strong>${t.symbol}</strong></td>
        <td>${t.quantity}</td>
        <td>$${t.price.toFixed(2)}</td>
      </tr>
    `;
  }).join("");
}

// Quote & Trading
function selectTicker(symbol) {
  document.getElementById("trade-symbol-input").value = symbol;
  fetchStockPrice();
}

async function fetchStockPrice() {
  const symbolInput = document.getElementById("trade-symbol-input").value.trim().toUpperCase();
  if (!symbolInput) {
    showToast("Please enter a stock symbol (e.g. AAPL)", "error");
    return;
  }

  document.getElementById("quote-status").textContent = "Fetching live market quote...";

  try {
    const res = await fetch(`${API_BASE}/market/price/${symbolInput}`);
    const data = await res.json();
    
    if (!res.ok) {
      throw new Error(data.detail || "Symbol not found");
    }

    currentQuotedSymbol = data.symbol;
    currentQuotedPrice = data.price;

    document.getElementById("quote-symbol").textContent = data.symbol;
    document.getElementById("quote-price").textContent = `$${data.price.toFixed(2)}`;
    document.getElementById("quote-status").textContent = `Live quote loaded successfully`;
    
    updateEstimatedTotal();
  } catch (err) {
    document.getElementById("quote-status").textContent = err.message;
    showToast(err.message, "error");
  }
}

function updateEstimatedTotal() {
  const qty = parseInt(document.getElementById("trade-qty").value) || 1;
  const total = currentQuotedPrice * qty;
  document.getElementById("estimated-cost").textContent = `$${total.toFixed(2)}`;
}

async function executeTrade(type) {
  const symbol = currentQuotedSymbol || document.getElementById("trade-symbol-input").value.trim().toUpperCase();
  const quantity = parseInt(document.getElementById("trade-qty").value);

  if (!symbol) {
    showToast("Please quote a stock symbol first.", "error");
    return;
  }
  if (!quantity || quantity <= 0) {
    showToast("Quantity must be at least 1.", "error");
    return;
  }

  const endpoint = type === "BUY" ? "/trade/buy" : "/trade/sell";

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ symbol, quantity })
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Trade failed");
    }

    showToast(`Successfully ${type === 'BUY' ? 'bought' : 'sold'} ${quantity} share(s) of ${symbol}!`, "success");
    await refreshData();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function addCurrentToWatchlist() {
  const symbol = currentQuotedSymbol || document.getElementById("trade-symbol-input").value.trim().toUpperCase();
  if (!symbol) {
    showToast("Please enter or quote a stock symbol first.", "error");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/watchlist/add`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ symbol })
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Failed to add to watchlist");
    }

    showToast(`${symbol} added to your watchlist!`, "success");
    fetchWatchlist();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function removeFromWatchlist(symbol) {
  try {
    const res = await fetch(`${API_BASE}/watchlist/remove/${symbol}`, {
      method: "DELETE",
      headers: getHeaders()
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Failed to remove item");
    }

    showToast(`${symbol} removed from watchlist.`, "info");
    fetchWatchlist();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Auto init on page load
document.addEventListener("DOMContentLoaded", initApp);
