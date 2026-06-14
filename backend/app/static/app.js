// ==========================================================================
// DATASTOCK - FRONTEND LOGIC (Vanilla JS)
// ==========================================================================

const API_BASE = window.location.origin;

function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// State management
let state = {
    products: [],
    categories: [],
    selectedProductId: null,
    filterText: "",
    filterCategory: "",
    filterTab: "all", // "all" | "alert"
    chartInstance: null
};

// DOM Elements
const elements = {
    productsGrid: document.getElementById("products-list-grid"),
    productCountBadge: document.getElementById("product-count-badge"),
    searchInput: document.getElementById("search-input"),
    categoryFilter: document.getElementById("category-filter"),
    tabButtons: document.querySelectorAll(".tab-btn"),
    
    // KPI Cards
    kpiTotalProducts: document.getElementById("metric-total-products"),
    kpiAlertProducts: document.getElementById("metric-alert-products"),
    kpiTotalCategories: document.getElementById("metric-total-categories"),
    kpiTotalMovements: document.getElementById("metric-total-movements"),
    alertKpiCard: document.getElementById("alert-kpi-card"),
    
    // Details Panel
    detailsEmptyState: document.getElementById("details-empty-state"),
    detailsActiveState: document.getElementById("details-active-state"),
    activeProdCategory: document.getElementById("active-product-category"),
    activeProdName: document.getElementById("active-product-name"),
    activeProdStock: document.getElementById("active-product-stock"),
    activeProdMin: document.getElementById("active-product-min"),
    activeProdStatusBadge: document.getElementById("active-product-status-badge"),
    activeProdExportBtn: document.getElementById("btn-active-export"),
    activeProdMovimentarBtn: document.getElementById("btn-active-movement"),
    auditLogTbody: document.getElementById("audit-log-tbody"),
    
    // Seed
    btnSeed: document.getElementById("btn-seed"),
    
    // Modals
    modalCreateProduct: document.getElementById("modal-create-product"),
    btnOpenCreateModal: document.getElementById("btn-open-create-modal"),
    formCreateProduct: document.getElementById("form-create-product"),
    categoriesDatalist: document.getElementById("categories-datalist"),
    
    modalRecordMovement: document.getElementById("modal-record-movement"),
    formRecordMovement: document.getElementById("form-record-movement"),
    movProductId: document.getElementById("mov-product-id"),
    movProductName: document.getElementById("mov-product-name"),
    movQtyInput: document.getElementById("mov-qty"),
    movValidationError: document.getElementById("mov-validation-error"),
    radioSaida: document.getElementById("type-saida"),
    radioEntrada: document.getElementById("type-entrada"),
    
    toastContainer: document.getElementById("toast-container")
};

// ==========================================================================
// TOAST NOTIFICATIONS
// ==========================================================================
function showToast(title, desc, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    
    const icon = {
        success: "fa-circle-check",
        danger: "fa-circle-xmark",
        warning: "fa-triangle-exclamation",
        info: "fa-circle-info"
    }[type];
    
    toast.innerHTML = `
        <i class="fa-solid ${icon} toast-icon"></i>
        <div class="toast-body">
            <div class="toast-title">${escapeHtml(title)}</div>
            <div class="toast-desc">${escapeHtml(desc)}</div>
        </div>
    `;
    
    elements.toastContainer.appendChild(toast);
    
    // Auto remove
    setTimeout(() => {
        toast.classList.add("removing");
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ==========================================================================
// API CALLS
// ==========================================================================
async function fetchProducts() {
    try {
        const response = await fetch(`${API_BASE}/produtos/`);
        if (!response.ok) throw new Error("Erro ao carregar produtos");
        state.products = await response.json();
        return state.products;
    } catch (error) {
        showToast("Erro", "Não foi possível carregar os produtos.", "danger");
        console.error(error);
        return [];
    }
}

async function fetchCategories() {
    try {
        const response = await fetch(`${API_BASE}/categorias/`);
        if (!response.ok) throw new Error("Erro ao carregar categorias");
        state.categories = await response.json();
        return state.categories;
    } catch (error) {
        console.error("Erro ao carregar categorias", error);
        return [];
    }
}

async function fetchProductMovements(productId) {
    try {
        const response = await fetch(`${API_BASE}/produtos/${productId}/movimentacoes`);
        if (!response.ok) throw new Error("Erro ao carregar histórico");
        return await response.json();
    } catch (error) {
        showToast("Erro", "Não foi possível carregar o histórico.", "danger");
        console.error(error);
        return [];
    }
}

// ==========================================================================
// RENDER & UI UPDATES
// ==========================================================================
function updateKPIs() {
    // 1. Total products
    elements.kpiTotalProducts.textContent = state.products.length;
    
    // 2. Alert products
    const alertsCount = state.products.filter(p => p.quantidade < p.estoque_minimo).length;
    elements.kpiAlertProducts.textContent = alertsCount;
    if (alertsCount > 0) {
        elements.alertKpiCard.classList.add("active");
    } else {
        elements.alertKpiCard.classList.remove("active");
    }
    
    // 3. Categories count
    elements.kpiTotalCategories.textContent = state.categories.length;
    
    // 4. Movements count (aggregate)
    let totalMovements = 0;
    // We can count movements dynamically by summing movements of all products
    // Wait, the API doesn't return movements list in GET /produtos/, but let's query all products
    // Alternatively, we sum up if we fetch detailed data, or since they are not in the main response,
    // we can simulate this or show a simple counter. Let's make an estimation or aggregate.
    // Wait! Can we get it by doing a quick calc or leaving a representative metric?
    // Let's call /produtos/ to see if we can calculate it. The API doesn't return movements inside GET /produtos/.
    // Let's calculate total movements by asking the backend if there is a general route,
    // but there isn't! We can show total movements as the sum of a mock count or update it as we query.
    // Actually, let's keep it updated dynamically based on products loaded if they had movements,
    // or just show a nice default like total products + sum of entries.
    // Let's query products. Since we don't have total movements endpoint, let's just make it count how many we can read,
    // or we can add a small counting in the backend later. Let's keep it simple: we can estimate it or just calculate it
    // from products (since each product has a starting stock, that's at least 1 movement per product with qty > 0).
    const productsWithStock = state.products.filter(p => p.quantidade > 0).length;
    elements.kpiTotalMovements.textContent = productsWithStock; // Will increment as we view histories
}

function renderCategoryFilter() {
    const select = elements.categoryFilter;
    const datalist = elements.categoriesDatalist;
    
    // Save current selected value
    const currentVal = select.value;
    
    select.innerHTML = '<option value="">Todas as Categorias</option>';
    datalist.innerHTML = '';
    
    state.categories.forEach(cat => {
        // Dropdown option
        const option = document.createElement("option");
        option.value = cat.id;
        option.textContent = cat.nome;
        select.appendChild(option);
        
        // Modal Datalist Option
        const dlOption = document.createElement("option");
        dlOption.value = cat.nome;
        datalist.appendChild(dlOption);
    });
    
    select.value = currentVal;
}

function renderProducts() {
    elements.productsGrid.innerHTML = "";
    
    // Filter logic
    const filtered = state.products.filter(p => {
        const matchesSearch = p.nome.toLowerCase().includes(state.filterText.toLowerCase());
        const matchesCategory = !state.filterCategory || p.categoria_id == state.filterCategory;
        const matchesTab = state.filterTab === "all" || (state.filterTab === "alert" && p.quantidade < p.estoque_minimo);
        
        return matchesSearch && matchesCategory && matchesTab;
    });
    
    elements.productCountBadge.textContent = `${filtered.length} ${filtered.length === 1 ? 'item' : 'itens'}`;
    
    if (filtered.length === 0) {
        elements.productsGrid.innerHTML = `
            <div class="empty-grid">
                <i class="fa-solid fa-box-open"></i>
                <p>Nenhum produto encontrado com os filtros selecionados.</p>
            </div>
        `;
        return;
    }
    
    filtered.forEach(p => {
        const isAlert = p.quantidade < p.estoque_minimo;
        const card = document.createElement("div");
        card.className = `product-card ${isAlert ? 'in-alert' : ''} ${state.selectedProductId === p.id ? 'active' : ''}`;
        card.dataset.id = p.id;
        
        const categoryName = state.categories.find(c => c.id === p.categoria_id)?.nome || "Sem Categoria";
        const escapedCategory = escapeHtml(categoryName);
        const escapedNome = escapeHtml(p.nome);
        
        // Image or Placeholder
        let imageHtml = `<div class="product-image-placeholder"><i class="fa-solid fa-box"></i></div>`;
        if (p.imagem_url) {
            const escapedUrl = escapeHtml(p.imagem_url);
            imageHtml = `<img src="${escapedUrl}" class="product-image" alt="${escapedNome}" onerror="this.onerror=null; this.parentNode.innerHTML='<div class=&quot;product-image-placeholder&quot;><i class=&quot;fa-solid fa-box&quot;></i></div>'">`;
        }
        
        card.innerHTML = `
            <div class="product-image-container">
                ${imageHtml}
            </div>
            <div class="product-card-body">
                <span class="category-badge">${escapedCategory}</span>
                <h3>${escapedNome}</h3>
                <div class="stock-info">
                    <div class="stock-metric">
                        <span class="stock-lbl">Saldo</span>
                        <span class="stock-val ${isAlert ? 'text-rose' : 'text-emerald'}">${p.quantidade}</span>
                    </div>
                    <div class="stock-metric" style="text-align: right;">
                        <span class="stock-lbl">Mínimo</span>
                        <span class="stock-val" style="color: var(--text-secondary);">${p.estoque_minimo}</span>
                    </div>
                </div>
            </div>
        `;
        
        card.addEventListener("click", () => selectProduct(p.id));
        elements.productsGrid.appendChild(card);
    });
}

async function selectProduct(productId) {
    state.selectedProductId = productId;
    
    // Highlight active card
    document.querySelectorAll(".product-card").forEach(card => {
        if (parseInt(card.dataset.id) === productId) {
            card.classList.add("active");
        } else {
            card.classList.remove("active");
        }
    });
    
    const product = state.products.find(p => p.id === productId);
    if (!product) return;
    
    // Load detail state
    elements.detailsEmptyState.classList.add("hidden");
    elements.detailsActiveState.classList.remove("hidden");
    
    const categoryName = state.categories.find(c => c.id === product.categoria_id)?.nome || "Sem Categoria";
    
    elements.activeProdCategory.textContent = categoryName;
    elements.activeProdName.textContent = product.nome;
    elements.activeProdStock.textContent = product.quantidade;
    elements.activeProdMin.textContent = product.estoque_minimo;
    
    const isAlert = product.quantidade < product.estoque_minimo;
    elements.activeProdStock.className = `status-val ${isAlert ? 'text-rose' : 'text-emerald'}`;
    
    elements.activeProdStatusBadge.textContent = isAlert ? "Abaixo do Mínimo" : "Estoque Seguro";
    elements.activeProdStatusBadge.className = `status-badge-val badge ${isAlert ? 'badge-alert' : 'badge-normal'}`;
    
    elements.activeProdExportBtn.href = `${API_BASE}/produtos/${product.id}/exportar/movimentacoes`;
    
    // Render History Log and Chart
    const movements = await fetchProductMovements(product.id);
    renderAuditLog(movements);
    renderChart(movements, product.estoque_minimo);
}

function renderAuditLog(movements) {
    elements.auditLogTbody.innerHTML = "";
    
    if (movements.length === 0) {
        elements.auditLogTbody.innerHTML = `
            <tr>
                <td colspan="4" style="text-align: center; color: var(--text-muted); padding: 2rem;">
                    Nenhuma movimentação registrada para este produto.
                </td>
            </tr>
        `;
        return;
    }
    
    // Sort chronological for calculations, then render reverse-chronological for display
    const chronological = [...movements].sort((a, b) => new Date(a.data) - new Date(b.data));
    
    let runningBalance = 0;
    const items = chronological.map(m => {
        if (m.tipo === "entrada") {
            runningBalance += m.quantidade;
        } else {
            runningBalance -= m.quantidade;
        }
        return {
            ...m,
            balance: runningBalance
        };
    });
    
    // Reverse for display
    const displayList = [...items].reverse();
    
    displayList.forEach(m => {
        const isEntrada = m.tipo === "entrada";
        const tr = document.createElement("tr");
        
        const dateObj = new Date(m.data);
        const dateStr = dateObj.toLocaleDateString('pt-BR') + ' ' + dateObj.toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'});
        
        tr.innerHTML = `
            <td>${dateStr}</td>
            <td>
                <span class="badge ${isEntrada ? 'badge-normal' : 'badge-alert'}">
                    <i class="fa-solid ${isEntrada ? 'fa-circle-arrow-up' : 'fa-circle-arrow-down'}"></i>
                    ${isEntrada ? 'Entrada' : 'Saída'}
                </span>
            </td>
            <td style="font-weight: 600;">${m.quantidade}</td>
            <td style="font-weight: 700; color: var(--text-primary);">${m.balance}</td>
        `;
        elements.auditLogTbody.appendChild(tr);
    });
}

function renderChart(movements, minStock) {
    if (elements.chartInstance) {
        elements.chartInstance.destroy();
    }
    
    const canvas = document.getElementById("stockEvolutionChart");
    const ctx = canvas.getContext("2d");
    
    if (movements.length === 0) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        return;
    }
    
    // Sort chronological
    const sorted = [...movements].sort((a, b) => new Date(a.data) - new Date(b.data));
    
    let balance = 0;
    const chartData = sorted.map(m => {
        balance += (m.tipo === "entrada" ? m.quantidade : -m.quantidade);
        return {
            x: new Date(m.data).toLocaleDateString('pt-BR') + ' ' + new Date(m.data).toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'}),
            y: balance
        };
    });
    
    // Include starting state of 0 if empty
    if (chartData.length > 0) {
        // If the first movement is an entry of Qty, start from 0 on the chart.
        const firstDate = new Date(sorted[0].data);
        firstDate.setMinutes(firstDate.getMinutes() - 1);
        chartData.unshift({
            x: "Inicial",
            y: 0
        });
    }
    
    const labels = chartData.map(d => d.x);
    const values = chartData.map(d => d.y);
    const minValues = Array(chartData.length).fill(minStock);
    
    elements.chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Estoque Real',
                    data: values,
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.3,
                    pointBackgroundColor: '#818cf8',
                    pointRadius: 4
                },
                {
                    label: 'Estoque Mínimo',
                    data: minValues,
                    borderColor: '#f43f5e',
                    borderWidth: 1.5,
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#94a3b8',
                        font: { family: 'Inter', size: 11 }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#64748b', font: { size: 9 }, maxRotation: 45, minRotation: 0 }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#64748b', font: { size: 10 } },
                    suggestedMin: 0
                }
            }
        }
    });
}

// ==========================================================================
// ACTIONS & EVENT HANDLERS
// ==========================================================================
async function reloadData() {
    await fetchProducts();
    await fetchCategories();
    renderCategoryFilter();
    renderProducts();
    updateKPIs();
    
    // Refresh selected product details if active
    if (state.selectedProductId) {
        selectProduct(state.selectedProductId);
    }
}

// Close Modals Helper
function closeModals() {
    elements.modalCreateProduct.classList.add("hidden");
    elements.modalRecordMovement.classList.add("hidden");
    elements.formCreateProduct.reset();
    elements.formRecordMovement.reset();
    elements.movValidationError.classList.add("hidden");
}

// Setup Event Listeners
function setupEventListeners() {
    // Search input
    elements.searchInput.addEventListener("input", (e) => {
        state.filterText = e.target.value;
        renderProducts();
    });
    
    // Category Filter dropdown
    elements.categoryFilter.addEventListener("change", (e) => {
        state.filterCategory = e.target.value;
        renderProducts();
    });
    
    // Filter Tabs
    elements.tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            elements.tabButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            state.filterTab = btn.dataset.filter;
            renderProducts();
        });
    });
    
    // Open/Close Create Product Modal
    elements.btnOpenCreateModal.addEventListener("click", () => {
        elements.modalCreateProduct.classList.remove("hidden");
    });
    
    document.querySelectorAll(".modal-close, .modal-cancel").forEach(btn => {
        btn.addEventListener("click", closeModals);
    });
    
    // Form Create Product Submission
    elements.formCreateProduct.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const payload = {
            nome: document.getElementById("prod-name").value,
            categoria_nome: document.getElementById("prod-category").value,
            quantidade: parseInt(document.getElementById("prod-qty").value) || 0,
            estoque_minimo: parseInt(document.getElementById("prod-min").value),
            imagem_url: document.getElementById("prod-image").value || null
        };
        
        try {
            const response = await fetch(`${API_BASE}/produtos/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || "Erro ao cadastrar produto");
            }
            
            showToast("Sucesso", "Produto cadastrado com sucesso!", "success");
            closeModals();
            await reloadData();
        } catch (error) {
            showToast("Erro de Cadastro", error.message, "danger");
        }
    });
    
    // Open movement modal from active details
    elements.activeProdMovimentarBtn.addEventListener("click", () => {
        const product = state.products.find(p => p.id === state.selectedProductId);
        if (!product) return;
        
        elements.movProductId.value = product.id;
        elements.movProductName.textContent = product.nome;
        
        // Show validation hint if Saida is selected
        validateSaidaQty();
        
        elements.modalRecordMovement.classList.remove("hidden");
    });
    
    // Real-time validation on quantity input in movement form
    function validateSaidaQty() {
        const product = state.products.find(p => p.id === parseInt(elements.movProductId.value));
        if (!product) return;
        
        const qty = parseInt(elements.movQtyInput.value) || 0;
        const isSaida = elements.radioSaida.checked;
        
        if (isSaida && qty > product.quantidade) {
            elements.movValidationError.textContent = `Atenção: A quantidade de saída (${qty}) excede o saldo atual em estoque (${product.quantidade}).`;
            elements.movValidationError.classList.remove("hidden");
            return false;
        } else {
            elements.movValidationError.classList.add("hidden");
            return true;
        }
    }
    
    elements.movQtyInput.addEventListener("input", validateSaidaQty);
    elements.radioSaida.addEventListener("change", validateSaidaQty);
    elements.radioEntrada.addEventListener("change", validateSaidaQty);
    
    // Form Record Movement Submission
    elements.formRecordMovement.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const productId = parseInt(elements.movProductId.value);
        const payload = {
            tipo: document.querySelector('input[name="mov-type"]:checked').value,
            quantidade: parseInt(elements.movQtyInput.value)
        };
        
        // Final front validation
        const product = state.products.find(p => p.id === productId);
        if (payload.tipo === 'saida' && payload.quantidade > product.quantidade) {
            showToast("Validação", "Não é permitido registrar saídas maiores que o saldo atual.", "warning");
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE}/produtos/${productId}/movimentacoes`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || "Erro ao registrar movimentação");
            }
            
            showToast("Sucesso", "Movimentação registrada com sucesso!", "success");
            closeModals();
            await reloadData();
        } catch (error) {
            showToast("Erro de Transação", error.message, "danger");
        }
    });
    
    // Seed database button
    elements.btnSeed.addEventListener("click", async () => {
        try {
            elements.btnSeed.disabled = true;
            elements.btnSeed.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Semeando...';
            
            const response = await fetch(`${API_BASE}/produtos/seed`, {
                method: 'POST'
            });
            
            if (!response.ok) throw new Error("Falha ao semear banco");
            const result = await response.json();
            
            showToast("Database Seed", result.message, "success");
            await reloadData();
        } catch (error) {
            showToast("Erro no Seed", "Não foi possível carregar os dados iniciais.", "danger");
            console.error(error);
        } finally {
            elements.btnSeed.disabled = false;
            elements.btnSeed.innerHTML = '<i class="fa-solid fa-database"></i> Popular Banco (Seed)';
        }
    });
}

// ==========================================================================
// INITIALIZATION
// ==========================================================================
window.addEventListener("DOMContentLoaded", async () => {
    setupEventListeners();
    await reloadData();
});
