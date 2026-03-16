// 预设场景管理页面 JavaScript

let currentPage = 1;
let pageSize = 10;
let currentIndustry = 'all';
let currentSearch = '';
let allScenes = [];

// 行业映射
const INDUSTRY_MAP = {
    'automobile': { name: '汽车销售', icon: '🚗', color: '#3b82f6' },
    'education': { name: '教育培训', icon: '📚', color: '#10b981' },
    'realestate': { name: '房产销售', icon: '🏠', color: '#f59e0b' },
    'insurance': { name: '保险金融', icon: '💼', color: '#8b5cf6' }
};

// 难度映射
const DIFFICULTY_MAP = {
    1: { text: '简单', class: 'badge-success' },
    2: { text: '中等', class: 'badge-warning' },
    3: { text: '困难', class: 'badge-danger' }
};

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    loadScenes();
});

/**
 * 加载预设场景列表
 */
async function loadScenes() {
    try {
        showLoading('loadingState');
        hideElement('emptyState');
        hideElement('tableContainer');
        
        const response = await request('/manage_system/api/preset-scenes');
        
        if (response.success) {
            allScenes = response.data || [];
            updateStats();
            filterAndRenderScenes();
        } else {
            showToast(response.message || '加载失败', 'error');
        }
    } catch (error) {
        console.error('加载预设场景失败:', error);
        showToast('加载预设场景列表失败', 'error');
    } finally {
        hideLoading('loadingState');
    }
}

/**
 * 更新统计数据
 */
function updateStats() {
    const totalCount = allScenes.length;
    const industries = new Set(allScenes.map(s => s.industry_code));
    const totalUsage = allScenes.reduce((sum, s) => sum + (s.usage_count || 0), 0);
    
    // 找出最热场景
    const hotScene = allScenes.reduce((max, s) => 
        (s.usage_count || 0) > (max.usage_count || 0) ? s : max
    , allScenes[0] || {});
    
    document.getElementById('totalCount').textContent = totalCount;
    document.getElementById('industryCount').textContent = industries.size;
    document.getElementById('totalUsage').textContent = totalUsage;
    document.getElementById('hotScene').textContent = hotScene.scene_name ? 
        hotScene.scene_name.substring(0, 8) + '...' : '-';
}

/**
 * 筛选并渲染场景列表
 */
function filterAndRenderScenes() {
    let filteredScenes = allScenes;
    
    // 按行业筛选
    if (currentIndustry !== 'all') {
        filteredScenes = filteredScenes.filter(s => s.industry_code === currentIndustry);
    }
    
    // 按名称搜索
    if (currentSearch) {
        filteredScenes = filteredScenes.filter(s => 
            s.scene_name.toLowerCase().includes(currentSearch.toLowerCase())
        );
    }
    
    if (filteredScenes.length === 0) {
        showElement('emptyState');
        hideElement('scenesGrid');
        return;
    }
    
    renderScenesGrid(filteredScenes);
    hideElement('emptyState');
    showElement('scenesGrid');
}

/**
 * 渲染场景网格
 */
function renderScenesGrid(scenes) {
    const grid = document.getElementById('scenesGrid');
    grid.innerHTML = '';
    
    scenes.forEach(scene => {
        const card = createSceneCard(scene);
        grid.appendChild(card);
    });
}

/**
 * 创建场景卡片
 */
function createSceneCard(scene) {
    const card = document.createElement('div');
    card.className = 'scene-card';
    
    const industry = INDUSTRY_MAP[scene.industry_code] || { name: scene.industry_code, icon: '📦', color: '#6b7280' };
    const difficulty = DIFFICULTY_MAP[scene.difficulty] || { text: '未知', class: 'badge-secondary' };
    const isHot = (scene.usage_count || 0) > 100;
    const isNew = isSceneNew(scene.created_time);
    
    // 难度星星
    const stars = '⭐'.repeat(scene.difficulty || 1);
    const difficultyClass = scene.difficulty === 1 ? 'easy' : scene.difficulty === 2 ? 'medium' : 'hard';
    
    card.innerHTML = `
        <div class="scene-card-header">
            <div class="scene-industry ${scene.industry_code}">
                <span>${industry.icon}</span>
                <span>${industry.name}</span>
            </div>
            <div class="scene-badges">
                ${isHot ? '<span class="scene-badge hot">热门</span>' : ''}
                ${isNew ? '<span class="scene-badge new">NEW</span>' : ''}
            </div>
        </div>
        
        <div class="scene-card-body">
            <div class="scene-name">${escapeHtml(scene.scene_name)}</div>
            <div class="scene-description">${escapeHtml(scene.scene_description || '暂无描述')}</div>
            
            <div class="scene-roles">
                <div class="scene-role">
                    <span class="scene-role-label">👤 AI:</span>
                    <span>${escapeHtml(scene.ai_role || '未设置')}</span>
                </div>
                <div class="scene-role">
                    <span class="scene-role-label">👨‍💼 学员:</span>
                    <span>${escapeHtml(scene.user_role || '未设置')}</span>
                </div>
            </div>
        </div>
        
        <div class="scene-card-footer">
            <div class="scene-difficulty">
                <span>🎯 难度:</span>
                <span class="difficulty-stars ${difficultyClass}">${stars}</span>
            </div>
            <div class="scene-usage">
                <span>🔥</span>
                <span>使用 ${scene.usage_count || 0}次</span>
            </div>
        </div>
        
        <div class="scene-card-actions">
            <button class="btn btn-outline btn-sm" onclick="viewSceneDetail('${scene.scene_code}'); event.stopPropagation();">
                📖 查看详情
            </button>
            <button class="btn btn-primary btn-sm" onclick="useScene('${scene.scene_code}'); event.stopPropagation();">
                ▶️ 立即使用
            </button>
        </div>
    `;
    
    // 点击卡片也可以使用场景
    card.addEventListener('click', () => useScene(scene.scene_code));
    
    return card;
}

/**
 * 判断场景是否为新场景（7天内）
 */
function isSceneNew(createdTime) {
    if (!createdTime) return false;
    const created = new Date(createdTime);
    const now = new Date();
    const diffDays = (now - created) / (1000 * 60 * 60 * 24);
    return diffDays <= 7;
}



/**
 * 按行业筛选
 */
function filterByIndustry(industry) {
    currentIndustry = industry;
    
    // 更新激活状态
    document.querySelectorAll('.industry-tab').forEach(tab => {
        if (tab.dataset.industry === industry) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
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
 * 刷新场景列表
 */
function refreshScenes() {
    loadScenes();
}

/**
 * 使用场景 - 在管理系统内打开场景配置页面
 */
function useScene(sceneCode) {
    // 在管理系统内跳转到场景配置页面
    window.location.href = `/manage_system/scene-config?scene_code=${sceneCode}`;
}

/**
 * 查看场景详情
 */
async function viewSceneDetail(sceneCode) {
    try {
        const response = await request(`/manage_system/api/preset-scenes/${sceneCode}`);
        
        if (response.success) {
            const scene = response.data;
            const difficulty = DIFFICULTY_MAP[scene.difficulty] || { text: '未知', class: 'badge-secondary' };
            
            const industry = INDUSTRY_MAP[scene.industry_code] || { name: scene.industry_code, icon: '📦' };
            const detailHtml = `
                <div class="scene-detail">
                    <div class="scene-detail-section">
                        <h4>📋 基本信息</h4>
                        <div class="scene-detail-grid">
                            <div class="scene-detail-item">
                                <label>场景名称</label>
                                <span>${escapeHtml(scene.scene_name)}</span>
                            </div>
                            <div class="scene-detail-item">
                                <label>所属行业</label>
                                <span>${industry.icon} ${industry.name}</span>
                            </div>
                            <div class="scene-detail-item">
                                <label>场景代码</label>
                                <code>${scene.scene_code}</code>
                            </div>
                            <div class="scene-detail-item">
                                <label>难度等级</label>
                                <span class="badge ${difficulty.class}">${difficulty.text}</span>
                            </div>
                            <div class="scene-detail-item">
                                <label>使用次数</label>
                                <span>${scene.usage_count || 0} 次</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="scene-detail-section">
                        <h4>📝 场景描述</h4>
                        <div class="scene-detail-text">${escapeHtml(scene.scene_description || '暂无描述')}</div>
                    </div>
                    
                    <div class="scene-detail-section">
                        <h4>👥 角色设定</h4>
                        <div class="scene-detail-grid">
                            <div class="scene-detail-item">
                                <label>AI角色</label>
                                <span>${escapeHtml(scene.ai_role || '未设置')}</span>
                            </div>
                            <div class="scene-detail-item">
                                <label>学员角色</label>
                                <span>${escapeHtml(scene.user_role || '未设置')}</span>
                            </div>
                        </div>
                    </div>
                    
                    ${scene.opening_line ? `
                    <div class="scene-detail-section">
                        <h4>💬 开场白</h4>
                        <div class="scene-detail-text">${escapeHtml(scene.opening_line)}</div>
                    </div>
                    ` : ''}
                    
                    <div class="scene-detail-actions">
                        <button class="btn btn-outline" onclick="closeSceneDetail()">取消</button>
                        <button class="btn btn-primary" onclick="useScene('${scene.scene_code}')" style="flex: 2;">▶️ 立即使用</button>
                    </div>
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

// 点击模态框外部关闭
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        closeSceneDetail();
    }
});