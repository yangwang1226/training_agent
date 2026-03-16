// 场景管理页面 JavaScript

let currentPage = 1;
let pageSize = 10;
let currentStatus = 'all';
let currentSearch = '';
let allScenes = [];
let deleteSceneId = null;

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    loadScenes();
});

/**
 * 加载场景列表
 */
async function loadScenes() {
    try {
        showLoading('loadingState');
        hideElement('emptyState');
        hideElement('tableContainer');
        
        const response = await request('/manage_system/api/scenes');
        
        if (response.success) {
            allScenes = response.data || [];
            updateStats();
            filterAndRenderScenes();
        } else {
            showToast(response.message || '加载失败', 'error');
        }
    } catch (error) {
        console.error('加载场景失败:', error);
        showToast('加载场景列表失败', 'error');
    } finally {
        hideLoading('loadingState');
    }
}

/**
 * 更新统计数据
 */
function updateStats() {
    const totalCount = allScenes.length;
    const presetCount = allScenes.filter(s => s.status === 1).length;
    const customCount = allScenes.filter(s => s.status === 2).length;
    const draftCount = allScenes.filter(s => s.status === 0).length;
    
    document.getElementById('totalScenesCount').textContent = totalCount;
    document.getElementById('presetScenesCount').textContent = presetCount;
    document.getElementById('customScenesCount').textContent = customCount;
    document.getElementById('draftScenesCount').textContent = draftCount;
}

/**
 * 筛选和渲染场景
 */
function filterAndRenderScenes() {
    let filteredScenes = allScenes;
    
    // 按状态筛选
    if (currentStatus !== 'all') {
        filteredScenes = filteredScenes.filter(s => s.status === parseInt(currentStatus));
    }
    
    // 搜索筛选
    if (currentSearch) {
        const searchLower = currentSearch.toLowerCase();
        filteredScenes = filteredScenes.filter(s => 
            s.scene_name.toLowerCase().includes(searchLower) ||
            (s.industry && s.industry.toLowerCase().includes(searchLower))
        );
    }
    
    // 更新计数
    document.getElementById('totalCount').textContent = filteredScenes.length;
    
    // 渲染
    renderScenes(filteredScenes);
}

/**
 * 渲染场景列表
 */
function renderScenes(scenes) {
    const tbody = document.getElementById('scenesTableBody');
    
    if (scenes.length === 0) {
        showElement('emptyState');
        hideElement('tableContainer');
        hideElement('paginationContainer');
        return;
    }
    
    hideElement('emptyState');
    showElement('tableContainer');
    
    // 分页
    const totalPages = Math.ceil(scenes.length / pageSize);
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const pageScenes = scenes.slice(startIndex, endIndex);
    
    // 渲染表格
    tbody.innerHTML = pageScenes.map(scene => `
        <tr>
            <td>${scene.id}</td>
            <td>
                <div class="scene-name-cell">
                    <div class="scene-icon">${getSceneIcon(scene.industry)}</div>
                    <div class="scene-info">
                        <div class="scene-name">${escapeHtml(scene.scene_name)}</div>
                        <div class="scene-meta">
                            ${scene.role_type ? `<span>AI角色: ${escapeHtml(scene.role_type)}</span>` : ''}
                        </div>
                    </div>
                </div>
            </td>
            <td>
                ${scene.industry ? `<span class="industry-tag">${escapeHtml(scene.industry)}</span>` : '-'}
            </td>
            <td>
                ${getStatusBadge(scene.status)}
            </td>
            <td>
                <div class="training-count">
                    <span class="count">${scene.training_count || 0}</span>
                    <span>次</span>
                </div>
            </td>
            <td>${formatDateTime(scene.created_time)}</td>
            <td>
                <div class="table-actions">
                    <button class="btn btn-link btn-sm" onclick="viewSceneDetail(${scene.id})" title="查看详情">
                        👁️ 查看
                    </button>
                    <button class="btn btn-link btn-sm" onclick="editScene(${scene.id})" title="编辑">
                        ✏️ 编辑
                    </button>
                    <button class="btn btn-link btn-sm text-danger" onclick="deleteScene(${scene.id}, '${escapeHtml(scene.scene_name)}')" title="删除">
                        🗑️ 删除
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
    
    // 渲染分页
    if (totalPages > 1) {
        renderPagination(totalPages);
        showElement('paginationContainer');
    } else {
        hideElement('paginationContainer');
    }
}

/**
 * 渲染分页
 */
function renderPagination(totalPages) {
    const container = document.getElementById('paginationContainer');
    let html = '';
    
    // 上一页
    html += `<button class="pagination-btn" ${currentPage === 1 ? 'disabled' : ''} onclick="changePage(${currentPage - 1})">上一页</button>`;
    
    // 页码
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
            html += `<button class="pagination-btn ${i === currentPage ? 'active' : ''}" onclick="changePage(${i})">${i}</button>`;
        } else if (i === currentPage - 3 || i === currentPage + 3) {
            html += `<span class="pagination-ellipsis">...</span>`;
        }
    }
    
    // 下一页
    html += `<button class="pagination-btn" ${currentPage === totalPages ? 'disabled' : ''} onclick="changePage(${currentPage + 1})">下一页</button>`;
    
    container.innerHTML = html;
}

/**
 * 切换页码
 */
function changePage(page) {
    currentPage = page;
    filterAndRenderScenes();
}

/**
 * 按状态筛选
 */
function filterByStatus(status) {
    currentStatus = status;
    currentPage = 1;
    
    // 更新标签状态
    document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.classList.remove('active');
        if (tab.dataset.status == status) {
            tab.classList.add('active');
        }
    });
    
    filterAndRenderScenes();
}

/**
 * 搜索处理
 */
const handleSearch = debounce(function() {
    currentSearch = document.getElementById('searchInput').value.trim();
    currentPage = 1;
    filterAndRenderScenes();
}, 300);

/**
 * 刷新场景列表
 */
function refreshScenes() {
    currentPage = 1;
    loadScenes();
}

/**
 * 查看场景详情
 */
async function viewSceneDetail(sceneId) {
    try {
        const response = await request(`/manage_system/api/scenes/${sceneId}`);
        
        if (response.success) {
            const scene = response.data;
            showSceneDetailModal(scene);
        } else {
            showToast(response.message || '加载失败', 'error');
        }
    } catch (error) {
        console.error('加载场景详情失败:', error);
        showToast('加载场景详情失败', 'error');
    }
}

/**
 * 显示场景详情模态框
 */
function showSceneDetailModal(scene) {
    const modal = document.getElementById('sceneDetailModal');
    const body = document.getElementById('sceneDetailBody');
    
    // 解析维度配置
    let dimensionConfig = [];
    if (scene.dimension_config) {
        try {
            const config = JSON.parse(scene.dimension_config);
            dimensionConfig = config.dimensions || [];
        } catch (e) {
            console.error('解析维度配置失败:', e);
        }
    }
    
    // 解析SOP清单
    let sopChecklist = [];
    if (scene.sop_checklist) {
        try {
            sopChecklist = JSON.parse(scene.sop_checklist);
        } catch (e) {
            console.error('解析SOP清单失败:', e);
        }
    }
    
    body.innerHTML = `
        <div class="scene-detail-section">
            <h4 class="detail-section-title">基本信息</h4>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">场景名称</div>
                    <div class="detail-value">${escapeHtml(scene.scene_name)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">场景状态</div>
                    <div class="detail-value">${getStatusBadge(scene.status)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">所属行业</div>
                    <div class="detail-value">${scene.industry || '-'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">训练目标</div>
                    <div class="detail-value">${escapeHtml(scene.training_goal || '-')}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">创建时间</div>
                    <div class="detail-value">${formatDateTime(scene.created_time)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">训练次数</div>
                    <div class="detail-value">${scene.training_count || 0} 次</div>
                </div>
            </div>
        </div>
        
        <div class="scene-detail-section">
            <h4 class="detail-section-title">角色设定</h4>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">AI角色类型</div>
                    <div class="detail-value">${escapeHtml(scene.role_type || '-')}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">角色描述</div>
                    <div class="detail-value">${escapeHtml(scene.role_description || '-')}</div>
                </div>
            </div>
        </div>
        
        ${scene.background_hint ? `
        <div class="scene-detail-section">
            <h4 class="detail-section-title">场景背景</h4>
            <div class="detail-value-block">${escapeHtml(scene.background_hint)}</div>
        </div>
        ` : ''}
        
        ${dimensionConfig.length > 0 ? `
        <div class="scene-detail-section">
            <h4 class="detail-section-title">评估维度 (${dimensionConfig.length}个)</h4>
            <ul class="dimension-list">
                ${dimensionConfig.map(dim => `
                    <li class="dimension-item">
                        <span class="dimension-name">${escapeHtml(dim.name)}</span>
                        <span class="dimension-weight">权重: ${dim.weight || 0}%</span>
                    </li>
                `).join('')}
            </ul>
        </div>
        ` : ''}
        
        ${sopChecklist.length > 0 ? `
        <div class="scene-detail-section">
            <h4 class="detail-section-title">SOP质检清单 (${sopChecklist.length}项)</h4>
            <ul class="sop-list">
                ${sopChecklist.map((item, index) => `
                    <li class="sop-item">
                        <div class="sop-item-number">${index + 1}</div>
                        <div class="sop-item-content">
                            <div class="sop-item-name">${escapeHtml(item.item_name || item.name)}</div>
                            ${item.keywords ? `<div class="sop-item-keywords">关键词: ${escapeHtml(item.keywords.join(', '))}</div>` : ''}
                        </div>
                    </li>
                `).join('')}
            </ul>
        </div>
        ` : ''}
    `;
    
    modal.style.display = 'flex';
}

/**
 * 关闭场景详情
 */
function closeSceneDetail() {
    document.getElementById('sceneDetailModal').style.display = 'none';
}

/**
 * 创建场景
 */
function createScene() {
    // 跳转到自定义场景创建页面
    window.location.href = '/manage_system/scenes/create-custom';
}

/**
 * 编辑场景
 */
function editScene(sceneId) {
    // 跳转到场景编辑页面
    window.location.href = `/manage_system/scenes/edit/${sceneId}`;
}

/**
 * 删除场景
 */
function deleteScene(sceneId, sceneName) {
    deleteSceneId = sceneId;
    document.getElementById('deleteSceneName').textContent = sceneName;
    document.getElementById('deleteConfirmModal').style.display = 'flex';
}

/**
 * 关闭删除确认
 */
function closeDeleteConfirm() {
    document.getElementById('deleteConfirmModal').style.display = 'none';
    deleteSceneId = null;
}

/**
 * 确认删除
 */
async function confirmDelete() {
    if (!deleteSceneId) return;
    
    const btn = document.getElementById('confirmDeleteBtn');
    const originalText = btn.innerHTML;
    
    try {
        btn.disabled = true;
        btn.innerHTML = '<span class="loading"></span> 删除中...';
        
        const response = await request(`/manage_system/api/scenes/${deleteSceneId}`, {
            method: 'DELETE'
        });
        
        if (response.success) {
            showToast('删除成功', 'success');
            closeDeleteConfirm();
            loadScenes();
        } else {
            showToast(response.message || '删除失败', 'error');
        }
    } catch (error) {
        console.error('删除场景失败:', error);
        showToast('删除场景失败', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

/**
 * 获取状态徽章HTML
 */
function getStatusBadge(status) {
    const statusMap = {
        0: { text: '草稿', class: 'status-draft' },
        1: { text: '预设场景', class: 'status-preset' },
        2: { text: '自定义', class: 'status-custom' },
        9: { text: '已归档', class: 'status-archived' }
    };
    
    const config = statusMap[status] || { text: '未知', class: 'status-draft' };
    return `<span class="status-badge ${config.class}">${config.text}</span>`;
}

/**
 * 获取场景图标
 */
function getSceneIcon(industry) {
    const iconMap = {
        '汽车': '🚗',
        '教育': '📚',
        '保险': '🛡️',
        '零售': '🛒',
        '金融': '💰',
        '医疗': '🏥',
        '房产': '🏠'
    };
    return iconMap[industry] || '🎯';
}

/**
 * HTML转义
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 显示元素
 */
function showElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'block';
    }
}

/**
 * 隐藏元素
 */
function hideElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'none';
    }
}