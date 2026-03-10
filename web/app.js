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
});

// ── Data Fetching ──────────────────────────────────────────────

async function fetchData() {
    try {
        const res = await fetch("/api/data");
        const json = await res.json();

        if (json.businesses && json.businesses.length > 0) {
            allData = json.businesses;
            filteredData = [...allData];
            document.getElementById("file-label").textContent = `📄 ${json.file} · ${json.count} registros`;
            updateStats();
            renderTable();
        } else {
            showEmpty("No se encontraron datos. Ejecuta el CLI primero.");
        }
    } catch (err) {
        showEmpty("Error conectando al servidor. ¿Está corriendo?");
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
        const domain = b.domain
            ? `<a class="domain-link" href="${escapeHtml(b.website)}" target="_blank">${escapeHtml(b.domain)}</a>`
            : `<span class="dim">—</span>`;
        const rating = b.rating
            ? `<span class="rating-value">★ ${b.rating}</span>`
            : `<span class="dim">—</span>`;

        return `
            <tr data-index="${i}" onclick="showDetail(${i})">
                <td style="text-align:center"><span class="score-badge score-${score}">${score}</span></td>
                <td><strong>${escapeHtml(b.name || "—")}</strong></td>
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
    if (b.instagram) dots.push(`<span class="social-dot social-ig" title="Instagram">IG</span>`);
    if (b.tiktok) dots.push(`<span class="social-dot social-tk" title="TikTok">TK</span>`);
    if (b.facebook) dots.push(`<span class="social-dot social-fb" title="Facebook">FB</span>`);
    return dots.length > 0
        ? `<div class="social-icons">${dots.join("")}</div>`
        : `<span class="dim">—</span>`;
}

function buildFollowers(b) {
    const parts = [];
    if (b.ig_followers) parts.push(`IG: ${b.ig_followers}`);
    if (b.tiktok_followers) parts.push(`TK: ${b.tiktok_followers}`);
    if (b.fb_followers) parts.push(`FB: ${b.fb_followers}`);
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
        ["Score", `<span class="score-badge score-${score}" style="display:inline-flex">${score}</span> ${b.quality_label || "—"}`],
        ["Categoría", b.category || "—"],
        ["Descripción", b.description ? `<em style="color:var(--text-secondary)">"${escapeHtml(b.description)}"</em>` : "—"],
        ["Teléfono", b.phone || "—"],
        ["Dirección", b.address || "—"],
        ["Horarios", b.hours || "—"],
        ["Website", b.website ? `<a href="${escapeHtml(b.website)}" target="_blank">${escapeHtml(b.domain)}</a>` : "—"],
        ["Salud Web (Oportunidad)", webHealth],
        ["Rating", b.rating ? `★ ${b.rating} (${b.reviews_count || 0} reseñas) ${b.price_level ? '· ' + b.price_level : ''}` : "—"],
        ["Emails", b.emails || "—"],
        ["Instagram", b.instagram ? `<a href="${escapeHtml(b.instagram)}" target="_blank">${escapeHtml(b.instagram)}</a>` : "—"],
        ["TikTok", b.tiktok ? `<a href="${escapeHtml(b.tiktok)}" target="_blank">${escapeHtml(b.tiktok)}</a>` : "—"],
        ["Facebook", b.facebook ? `<a href="${escapeHtml(b.facebook)}" target="_blank">${escapeHtml(b.facebook)}</a>` : "—"],
        ["Seguidores IG", b.ig_followers || "—"],
        ["Seguidores TK", b.tiktok_followers || "—"],
        ["Seguidores FB", b.fb_followers || "—"],
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
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;")
        .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
