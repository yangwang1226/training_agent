// 自定义场景管理页面 JavaScript

let allScenes = [];
let currentStatus = 'all';
let currentIndustry = 'all';
let currentSort = 'latest';
let currentSearch = '';
let deleteSceneId = null;

// 状态映射
const STATUS_MAP = {
    0: { text: '草稿', class: 'draft', icon: '⚪' },
    1: { text: '已完成', class: 'completed', icon: '🔵' },
    2: { text: '进行中', class: 'active', icon: '🟢' },
    3: { text: '已归档', class: 'archived', icon: '🔴' }
};

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    loadScenes();
});

/**
 * 加载自定义场景列表
 */
async function loadScenes() {
    try {
        showLoading('loadingState');
        hideElement('emptyState');
        hideElement('scenesList');
        
        const response = await request('/manage_system/api/scenes');
        
        if (response.success) {
            allScenes = response.data || [];
            updateStats();
            filterAndRenderScenes();
        } else {
            showToast(response.message || '加载失败', 'error');
        }
    } catch (error) {
        console.error('加载自定义场景失败:', error);
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
    const activeCount = allScenes.filter(s => s.status === 2).length;
    const completedCount = allScenes.filter(s => s.status === 1).length;
    
    // 计算平均完成率（这里简化处理，实际可能需要从训练记录计算）
    const avgCompletion = totalCount > 0 ? 
        Math.round((completedCount / totalCount) * 100) : 0;
    
    document.getElementById('totalCount').textContent = totalCount;
    document.getElementById('activeCount').textContent = activeCount;
    document.getElementById('completedCount').textContent = completedCount;
    document.getElementById('avgCompletion').textContent = avgCompletion + '%';
}

/**
 * 筛选并渲染场景列表
 */
function filterAndRenderScenes() {
    let filteredScenes = allScenes;
    
    // 按状态筛选
    if (currentStatus !== 'all') {
        filteredScenes = filteredScenes.filter(s => s.status == currentStatus);
    }
    
    // 按行业筛选
    if (currentIndustry !== 'all') {
        filteredScenes = filteredScenes.filter(s => 
            (s.industry || '其他') === currentIndustry
        );
    }
    
    // 按名称或描述搜索
    if (currentSearch) {
        filteredScenes = filteredScenes.filter(s => 
            s.scene_name.toLowerCase().includes(currentSearch.toLowerCase()) ||
            (s.scene_prompt && s.scene_prompt.toLowerCase().includes(currentSearch.toLowerCase()))
        );
    }
    
    // 排序
    filteredScenes = sortScenes(filteredScenes, currentSort);
    
    if (filteredScenes.length === 0) {
        showElement('emptyState');
        hideElement('scenesList');
        return;
    }
    
    renderScenesList(filteredScenes);
    hideElement('emptyState');
    showElement('scenesList');
}

/**
 * 排序场景
 */
function sortScenes(scenes, sortType) {
    const sorted = [...scenes];
    
    switch(sortType) {
        case 'latest':
            return sorted.sort((a, b) => 
                new Date(b.created_at) - new Date(a.created_at)
            );
        case 'updated':
            return sorted.sort((a, b) => 
                new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at)
            );
        case 'training':
            return sorted.sort((a, b) => 
                (b.training_count || 0) - (a.training_count || 0)
            );
        default:
            return sorted;
    }
}

/**
 * 渲染场景列表
 */
function renderScenesList(scenes) {
    const list = document.getElementById('scenesList');
    list.innerHTML = '';
    
    scenes.forEach(scene => {
        const card = createSceneCard(scene);
        list.appendChild(card);
    });
}

/**
 * 创建场景卡片
 */
function createSceneCard(scene) {
    const card = document.createElement('div');
    card.className = 'custom-scene-card';
    
    const status = STATUS_MAP[scene.status] || STATUS_MAP[0];
    const industry = scene.industry || '其他';
    const trainingCount = scene.training_count || 0;
    
    // 提取场景描述（从prompt中）
    const description = scene.scene_prompt ? 
        scene.scene_prompt.substring(0, 100) + '...' : 
        '暂无描述';
    
    card.innerHTML = `
        <div class="scene-card-header">
            <div class="scene-title-row">
                <span class="scene-status-badge ${status.class}">
                    <span>${status.icon}</span>
                    <span>${status.text}</span>
                </span>
                <h3 class="scene-title">${escapeHtml(scene.scene_name)}</h3>
            </div>
            <button class="scene-menu-btn" onclick="event.stopPropagation();">操作 ▼</button>
        </div>
        
        <div class="scene-description">
            ${escapeHtml(description)}
        </div>
        
        <div class="scene-meta">
            <div class="scene-meta-item">
                <span>🏢</span>
                <span>${industry}</span>
            </div>
            <div class="scene-meta-item">
                <span>👤</span>
                <span>${escapeHtml(scene.role_type || '未设置角色')}</span>
            </div>
        </div>
        
        <div class="scene-stats">
            <div class="scene-stat-item">
                <span>📅</span>
                <span>${formatDateTime(scene.created_at)} 创建</span>
            </div>
            <div class="scene-stat-item">
                <span>🎯</span>
                <span>训练 ${trainingCount} 次</span>
            </div>
        </div>
        
        <div class="scene-actions">
            <button class="btn btn-outline btn-sm" onclick="viewSceneDetail(${scene.id}); event.stopPropagation();">
                📖 查看详情
            </button>
            <button class="btn btn-outline btn-sm" onclick="editScene(${scene.id}); event.stopPropagation();">
                ✏️ 编辑
            </button>
            <button class="btn btn-primary btn-sm" onclick="startTraining(${scene.id}); event.stopPropagation();">
                ▶️ 开始训练
            </button>
            <button class="btn btn-outline btn-sm" onclick="viewRecords(${scene.id}); event.stopPropagation();">
                📊 查看记录
            </button>
            <button class="btn btn-danger btn-sm" onclick="deleteScene(${scene.id}, '${escapeHtml(scene.scene_name)}'); event.stopPropagation();">
                🗑️ 删除
            </button>
        </div>
    `;
    
    return card;
}

/**
 * 按状态筛选
 */
function filterByStatus(status) {
    currentStatus = status;
    
    // 更新激活状态
    document.querySelectorAll('.filter-btn[data-status]').forEach(btn => {
        if (btn.dataset.status == status) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    filterAndRenderScenes();
}

/**
 * 按行业筛选
 */
function filterByIndustry(industry) {
    currentIndustry = industry;
    
    // 更新激活状态
    document.querySelectorAll('.filter-btn[data-industry]').forEach(btn => {
        if (btn.dataset.industry === industry) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    filterAndRenderScenes();
}

/**
 * 排序
 */
function sortBy(sortType) {
    currentSort = sortType;
    
    // 更新激活状态
    document.querySelectorAll('.filter-btn[data-sort]').forEach(btn => {
        if (btn.dataset.sort === sortType) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    filterAndRenderScenes();
}

/**
 * 搜索处理
 */
let searchTimeout;
function handleSearch() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        currentSearch = document.getElementById('searchInput').value.trim();
        filterAndRenderScenes();
    }, 300);
}

/**
 * 创建新场景
 */
function createNewScene() {
    window.location.href = '/manage_system/scenes/create-custom';
}

/**
 * 查看场景详情
 */
async function viewSceneDetail(sceneId) {
    try {
        const response = await request(`/manage_system/api/scenes/${sceneId}`);
        
        if (response.success) {
            const scene = response.data;
            const status = STATUS_MAP[scene.status] || STATUS_MAP[0];
            
            const detailHtml = `
                <div class="detail-section">
                    <h4>📋 基本信息</h4>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <label>场景名称</label>
                            <span>${escapeHtml(scene.scene_name)}</span>
                        </div>
                        <div class="detail-item">
                            <label>创建时间</label>
                            <span>${formatDateTime(scene.created_at)}</span>
                        </div>
                        <div class="detail-item">
                            <label>所属行业</label>
                            <span>${escapeHtml(scene.industry || '其他')}</span>
                        </div>
                        <div class="detail-item">
                            <label>场景状态</label>
                            <span class="scene-status-badge ${status.class}">
                                ${status.icon} ${status.text}
                            </span>
                        </div>
                    </div>
                </div>
                
                <div class="detail-section">
                    <h4>📝 场景配置</h4>
                    ${scene.scene_prompt ? `
                        <div style="margin-bottom: 12px;">
                            <label style="font-weight: 500; color: #6b7280; font-size: 13px; display: block; margin-bottom: 4px;">场景提示词</label>
                            <div class="detail-text">${escapeHtml(scene.scene_prompt)}</div>
                        </div>
                    ` : ''}
                    ${scene.background_hint ? `
                        <div style="margin-bottom: 12px;">
                            <label style="font-weight: 500; color: #6b7280; font-size: 13px; display: block; margin-bottom: 4px;">背景信息</label>
                            <div class="detail-text">${escapeHtml(scene.background_hint)}</div>
                        </div>
                    ` : ''}
                    ${scene.role_type || scene.role_description ? `
                        <div>
                            <label style="font-weight: 500; color: #6b7280; font-size: 13px; display: block; margin-bottom: 4px;">角色设定</label>
                            <div class="detail-text">
                                ${scene.role_type ? `<strong>${escapeHtml(scene.role_type)}</strong><br>` : ''}
                                ${scene.role_description ? escapeHtml(scene.role_description) : ''}
                            </div>
                        </div>
                    ` : ''}
                </div>
                
                <div class="detail-section">
                    <h4>📊 训练统计</h4>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <label>训练次数</label>
                            <span>${scene.training_count || 0} 次</span>
                        </div>
                        <div class="detail-item">
                            <label>最近训练</label>
                            <span>${formatDateTime(scene.updated_at || scene.created_at)}</span>
                        </div>
                    </div>
                </div>
                
                ${scene.dimension_config ? `
                <div class="detail-section">
                    <h4>🎯 考核维度</h4>
                    <div class="dimension-tags">
                        ${JSON.parse(scene.dimension_config).map(d => 
                            `<span class="dimension-tag">${escapeHtml(d.name || d)}</span>`
                        ).join('')}
                    </div>
                </div>
                ` : ''}
                
                <div style="display: flex; gap: 12px; margin-top: 24px; padding-top: 24px; border-top: 1px solid #e5e7eb;">
                    <button class="btn btn-outline" onclick="closeSceneDetail()" style="flex: 1;">关闭</button>
                    <button class="btn btn-outline" onclick="editScene(${scene.id})" style="flex: 1;">✏️ 编辑场景</button>
                    <button class="btn btn-primary" onclick="startTraining(${scene.id})" style="flex: 2;">▶️ 开始训练</button>
                </div>
            `;
            
            document.getElementById('detailModalTitle').textContent = scene.scene_name;
            document.getElementById('sceneDetailBody').innerHTML = detailHtml;
            showElement('sceneDetailModal');
        } else {
            showToast(response.message || '加载详情失败', 'error');
        }
    } catch (error) {
        console.error('查看场景详情失败:', error);
        showToast('查看场景详情失败', 'error');
    }
}

/**
 * 关闭详情模态框
 */
function closeSceneDetail() {
    hideElement('sceneDetailModal');
}

/**
 * 编辑场景
 */
function editScene(sceneId) {
    window.location.href = `/manage_system/scenes/edit/${sceneId}`;
}

/**
 * 开始训练
 */
function startTraining(sceneId, provider = 'qwen') {
    window.location.href = `/realtime/${sceneId}?provider=${provider}`;
}

/**
 * 查看训练记录
 */
function viewRecords(sceneId) {
    // 跳转到训练记录页面
    showToast('训练记录功能开发中...', 'info');
}

/**
 * 删除场景
 */
function deleteScene(sceneId, sceneName) {
    deleteSceneId = sceneId;
    document.getElementById('deleteSceneName').textContent = sceneName;
    showElement('deleteConfirmModal');
}

/**
 * 确认删除
 */
async function confirmDelete() {
    if (!deleteSceneId) return;
    
    try {
        const btn = document.getElementById('confirmDeleteBtn');
        btn.disabled = true;
        btn.textContent = '删除中...';
        
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
        const btn = document.getElementById('confirmDeleteBtn');
        btn.disabled = false;
        btn.textContent = '确认删除';
    }
}

/**
 * 关闭删除确认
 */
function closeDeleteConfirm() {
    hideElement('deleteConfirmModal');
    deleteSceneId = null;
}

// 点击模态框外部关闭
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        closeSceneDetail();
        closeDeleteConfirm();
    }
});