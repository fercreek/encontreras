/**
 * encontreras Dashboard — Client-Side Logic
 *
 * Loads data from /api/data, renders table, handles search, filters, and modal.
 */

// ── State ──────────────────────────────────────────────────────

let allData = [];
let filteredData = [];
let currentFilter = "all";
let currentSearch = "";

// ── Init ───────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
    fetchData();
    setupSearch();
    setupFilters();
    setupModal();
    setupExtractionForm();
    checkStatus();
    setInterval(() => {
        pollData();
        checkStatus();
    }, 5000); // Check for new data and background job status every 5 seconds
});

// ── Background Job Status ────────────────────────────────────

async function checkStatus() {
    try {
        const res = await fetch("/api/status");
        if (res.ok) {
            const data = await res.json();
            const banner = document.getElementById("status-banner");
            const msg = document.getElementById("status-message");
            const btn = document.getElementById("extract-btn");
            
            if (data.running) {
                msg.textContent = `Huey Worker activo: Extrayendo "${data.query}" en ${data.location}... (Los resultados aparecerán aquí al terminar)`;
                banner.classList.remove("hidden");
                
                // Disable extract button while running
                if (btn) {
                    btn.disabled = true;
                    btn.textContent = "Extrayendo...";
                    btn.style.background = "var(--accent-cyan)";
                    btn.style.color = "#000";
                }
            } else {
                banner.classList.add("hidden");
                
                // Re-enable extract button
                if (btn && btn.textContent === "Extrayendo...") {
                    btn.disabled = false;
                    btn.textContent = "Extraer";
                    btn.style.background = "";
                    btn.style.color = "";
                }
            }
        }
    } catch (e) {
        // Fail silently during background polling
    }
}

// ── Web UI Extraction Trigger ────────────────────────────────

function setupExtractionForm() {
    const form = document.getElementById("extract-form");
    const btn = document.getElementById("extract-btn");
    
    if (!form) return;
    
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const query = document.getElementById("extract-query").value.trim();
        const location = document.getElementById("extract-location").value.trim();
        const max_results = document.getElementById("extract-limit").value;
        
        if (!query || !location) return;
        
        const originalText = btn.textContent;
        btn.textContent = "Lanzando...";
        btn.disabled = true;
        
        try {
            const res = await fetch("/api/run", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query, location, max_results: parseInt(max_results) })
            });
            
            if (res.ok) {
                // Instantly trigger checkStatus to show banner without waiting for the next 5s interval
                setTimeout(checkStatus, 500);
                form.reset();
                document.getElementById("extract-limit").value = "10";
            } else {
                const errData = await res.json();
                alert(`Error al lanzar extracción: ${errData.error}`);
                btn.textContent = originalText;
                btn.disabled = false;
            }
        } catch (error) {
            alert(`Error de red: ${error.message}`);
            btn.textContent = originalText;
            btn.disabled = false;
        }
    });
}

// ── Data Fetching ──────────────────────────────────────────────

async function pollData() {
    try {
        const res = await fetch("/api/data");
        const json = await res.json();
        
        if (json.businesses && json.businesses.length > 0) {
            const newDataStr = JSON.stringify(json.businesses);
            const oldDataStr = JSON.stringify(allData);
            
            // Only re-render if data has actually changed
            if (newDataStr !== oldDataStr) {
                allData = json.businesses;
                applyFilters(); // Re-apply existing search/filters and render
                document.getElementById("file-label").textContent = `📄 ${json.file} · ${json.count} registros`;
                updateStats();
            }
        }
    } catch (err) {
        // Fail silently during background polling
    }
}

async function fetchData() {
    try {
        const res = await fetch("/api/data");
        
        if (!res.ok) {
            let errMsg = `Error del servidor (${res.status})`;
            try { const errObj = await res.json(); errMsg = errObj.error || errMsg; } catch(e) {}
            showEmpty(`Error: ${errMsg}. ¿Ejecutaste el CLI primero?`);
            return;
        }
        
        const json = await res.json();

        if (json.businesses && json.businesses.length > 0) {
            allData = json.businesses;
            filteredData = [...allData];
            document.getElementById("file-label").textContent = `📄 ${json.file} · ${json.count} registros`;
            updateStats();
            renderTable();
        } else {
            showEmpty("No se encontraron datos. Ejecuta una búsqueda desde aquí o el CLI.");
        }
    } catch (err) {
        showEmpty("Error conectando al servidor. ¿Está corriendo el dashboard?");
    }
}

// ── Stats ──────────────────────────────────────────────────────

function updateStats() {
    const counts = { total: allData.length, 5: 0, 4: 0, 3: 0, weak: 0, spam: 0 };

    allData.forEach(b => {
        const s = b.score ?? -1;
        if (s === 5) counts[5]++;
        else if (s === 4) counts[4]++;
        else if (s === 3) counts[3]++;
        else if (s >= 1) counts.weak++;
        else counts.spam++;
    });

    document.getElementById("stat-total").textContent = counts.total;
    document.getElementById("stat-excellent").textContent = counts[5];
    document.getElementById("stat-good").textContent = counts[4];
    document.getElementById("stat-rescued").textContent = counts[3];
    document.getElementById("stat-weak").textContent = counts.weak;
    document.getElementById("stat-spam").textContent = counts.spam;
}

// ── Search ─────────────────────────────────────────────────────

function setupSearch() {
    const input = document.getElementById("search-input");
    let timeout;
    input.addEventListener("input", () => {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            currentSearch = input.value.toLowerCase().trim();
            applyFilters();
        }, 200);
    });
}

// ── Filters ────────────────────────────────────────────────────

function setupFilters() {
    document.querySelectorAll(".filter-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentFilter = btn.dataset.filter;
            applyFilters();
        });
    });
}

function applyFilters() {
    filteredData = allData.filter(b => {
        // Score filter
        if (currentFilter !== "all") {
            if (currentFilter === "has-email") {
                if (!b.emails) return false;
            } else if (currentFilter === "has-social") {
                if (!b.instagram && !b.tiktok && !b.facebook) return false;
            } else if (currentFilter === "web-issues") {
                if (!b.site_issues || b.site_issues.length === 0) return false;
            } else {
                const score = parseInt(currentFilter);
                if ((b.score ?? -1) !== score) return false;
            }
        }

        // Search filter
        if (currentSearch) {
            const haystack = [
                b.name, b.phone, b.domain, b.emails,
                b.address, b.instagram, b.tiktok, b.facebook,
                b.quality_label
            ].filter(Boolean).join(" ").toLowerCase();
            if (!haystack.includes(currentSearch)) return false;
        }

        return true;
    });

    renderTable();
}

// ── Table Rendering ────────────────────────────────────────────

function renderTable() {
    const tbody = document.getElementById("table-body");

    if (filteredData.length === 0) {
        tbody.innerHTML = `
            <tr><td colspan="8" class="empty-state">
                <div class="empty-icon">🔍</div>
                <div>Sin resultados para los filtros actuales</div>
            </td></tr>`;
        return;
    }

    tbody.innerHTML = filteredData.map((b, i) => {
        const score = b.score ?? 0;
        const socials = buildSocialDots(b);
        const followers = buildFollowers(b);
        const emails = b.emails
            ? `<span class="email-text">${escapeHtml(b.emails)}</span>`
            : `<span class="dim">—</span>`;
            
        let webScoreHtml = "";
        if (b.website && b.domain && b.site_status) {
            let webScore = 1; // Default to 1 if it's dead
            if (b.site_status === "OK") {
                if (!b.site_issues || b.site_issues.length === 0) webScore = 5;
                else if (b.site_issues.length === 1) webScore = 4;
                else webScore = 3;
            }
            const colorVar = `var(--score-${webScore === 5 ? 5 : (webScore === 4 ? 4 : (webScore===3?3:1))})`;
            webScoreHtml = `<span style="margin-left:6px; font-size:0.75rem; color:${colorVar}; padding: 2px 4px; border-radius:4px; background:rgba(255,255,255,0.05)" title="Calidad Web">★ ${webScore}</span>`;
        }
            
        const domain = b.domain
            ? `<div style="display:flex; align-items:center;"><a class="domain-link" href="${escapeHtml(b.website)}" target="_blank">${escapeHtml(b.domain)}</a>${webScoreHtml}</div>`
            : `<span class="dim">—</span>`;
        const rating = b.rating
            ? `<span class="rating-value">★ ${b.rating}</span>`
            : `<span class="dim">—</span>`;

        return `
            <tr data-index="${i}" onclick="showDetail(${i})">
                <td style="text-align:center"><span class="score-badge score-${score}">${score}</span></td>
                <td><strong>${escapeHtml(b.name || "—")}</strong>${b.context ? ' <span title="Analizado por IA" style="cursor:help">🧠</span>' : ''}</td>
                <td>${escapeHtml(b.phone || "—")}</td>
                <td>${domain}</td>
                <td>${emails}</td>
                <td>${socials}</td>
                <td>${followers}</td>
                <td class="rating-cell">${rating}</td>
            </tr>`;
    }).join("");
}

function buildSocialDots(b) {
    const dots = [];
    if (b.instagram) dots.push(`<a class="social-dot social-ig" style="text-decoration:none;" title="Instagram" href="${escapeHtml(b.instagram)}" target="_blank">IG</a>`);
    if (b.tiktok) dots.push(`<a class="social-dot social-tk" style="text-decoration:none;" title="TikTok" href="${escapeHtml(b.tiktok)}" target="_blank">TK</a>`);
    if (b.facebook) dots.push(`<a class="social-dot social-fb" style="text-decoration:none;" title="Facebook" href="${escapeHtml(b.facebook)}" target="_blank">FB</a>`);
    return dots.length > 0
        ? `<div class="social-icons">${dots.join("")}</div>`
        : `<span class="dim">—</span>`;
}

function buildFollowers(b) {
    const parts = [];
    const isValid = (f) => f && f.toString().trim() !== "" && f.toString().trim() !== "." && f.toString().trim() !== "-";
    
    if (isValid(b.ig_followers)) parts.push(`IG: ${escapeHtml(b.ig_followers)}`);
    if (isValid(b.tiktok_followers)) parts.push(`TK: ${escapeHtml(b.tiktok_followers)}`);
    if (isValid(b.fb_followers)) parts.push(`FB: ${escapeHtml(b.fb_followers)}`);
    
    return parts.length > 0
        ? `<span class="email-text">${parts.join(" · ")}</span>`
        : `<span class="dim">—</span>`;
}

// ── Modal Detail ───────────────────────────────────────────────

function setupModal() {
    document.getElementById("modal-close").addEventListener("click", closeModal);
    document.getElementById("modal-overlay").addEventListener("click", (e) => {
        if (e.target === e.currentTarget) closeModal();
    });
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") closeModal();
    });
}

function showDetail(index) {
    const b = filteredData[index];
    if (!b) return;

    const score = b.score ?? 0;

    // Formatting web health
    let webHealth = "—";
    if (b.site_status) {
        let statusBadge = '';
        if (b.site_status === "OK" && (!b.site_issues || !b.site_issues.length)) {
            statusBadge = `<span style="color:var(--score-5); font-weight:600">✅ OK (Optimizada)</span>`;
        } else if (b.site_status === "OK") {
            statusBadge = `<span style="color:var(--score-3); font-weight:600">⚠️ OK (Con temas de SEO/Móvil)</span>`;
        } else {
            statusBadge = `<span style="color:var(--score-1); font-weight:600">🛑 Caída / Error (${b.site_status})</span>`;
        }

        let issuesList = '';
        if (b.site_issues && b.site_issues.length) {
            issuesList = `<br><span style="font-size:0.75rem; color:var(--score-1)">Problemas: ${escapeHtml(b.site_issues)}</span>`;
        }
        webHealth = statusBadge + issuesList;
    }

    const fields = [
        ["Score", `<span class="score-badge score-${score}" style="display:inline-flex">${score}</span> ${escapeHtml(b.quality_label) || "—"}`],
        ["Categoría", escapeHtml(b.category) || "—"],
        ["Descripción", b.description ? `<em style="color:var(--text-secondary)">"${escapeHtml(b.description)}"</em>` : "—"],
        ["Teléfono", escapeHtml(b.phone) || "—"],
        ["Dirección", escapeHtml(b.address) || "—"],
        ["Horarios", escapeHtml(b.hours) || "—"],
        ["Website", b.website ? `<a href="${escapeHtml(b.website)}" target="_blank">${escapeHtml(b.domain)}</a>` : "—"],
        ["Salud Web (Oportunidad)", webHealth],
        ["Rating", b.rating ? `★ ${escapeHtml(String(b.rating))} (${escapeHtml(String(b.reviews_count || 0))} reseñas) ${b.price_level ? '· ' + escapeHtml(b.price_level) : ''}` : "—"],
        ["Emails", escapeHtml(b.emails) || "—"],
        ["Instagram", b.instagram ? `<a href="${escapeHtml(b.instagram)}" target="_blank">${escapeHtml(b.instagram)}</a>` : "—"],
        ["TikTok", b.tiktok ? `<a href="${escapeHtml(b.tiktok)}" target="_blank">${escapeHtml(b.tiktok)}</a>` : "—"],
        ["Facebook", b.facebook ? `<a href="${escapeHtml(b.facebook)}" target="_blank">${escapeHtml(b.facebook)}</a>` : "—"],
        ["Seguidores IG", escapeHtml(b.ig_followers) || "—"],
        ["Seguidores TK", escapeHtml(b.tiktok_followers) || "—"],
        ["Seguidores FB", escapeHtml(b.fb_followers) || "—"],
        ["🧠 Contexto IA", b.context ? `<em style="color:var(--accent-primary)">${escapeHtml(b.context)}</em>` : '<span style="color:var(--text-secondary)">Pendiente — ejecuta <code>make synthesize</code></span>'],
        ["💡 Why They Matter", b.why_they_matter ? `<em style="color:var(--score-5)">${escapeHtml(b.why_they_matter)}</em>` : "—"],
        ["💬 Icebreaker (DM)", b.icebreaker ? `<div style="background:var(--bg-secondary);padding:0.75rem;border-radius:8px;border-left:3px solid var(--accent-primary);margin-top:0.25rem;white-space:pre-wrap;">${escapeHtml(b.icebreaker)}</div>` : "—"],
        ["Google Maps", b.maps_url ? `<a href="${escapeHtml(b.maps_url)}" target="_blank">Abrir ficha Maps ↗</a>` : "—"]
    ];

    const rows = fields.map(([label, value]) =>
        `<div class="detail-row">
            <span class="detail-label">${label}</span>
            <span class="detail-value">${value}</span>
        </div>`
    ).join("");

    document.getElementById("modal-content").innerHTML = `
        <h2>${escapeHtml(b.name || "Sin nombre")}</h2>
        ${rows}
    `;

    document.getElementById("modal-overlay").classList.add("active");
}

function closeModal() {
    document.getElementById("modal-overlay").classList.remove("active");
}

// ── Utilities ──────────────────────────────────────────────────

function showEmpty(msg) {
    document.getElementById("table-body").innerHTML = `
        <tr><td colspan="8" class="empty-state">
            <div class="empty-icon">📭</div>
            <div>${msg}</div>
        </td></tr>`;
}

function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;")
        .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
