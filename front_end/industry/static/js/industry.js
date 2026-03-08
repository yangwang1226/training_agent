// ============================================
// AI智能教练 - 行业选择页面 JavaScript
// ============================================

// 行业配置（映射行业代码到显示信息）
const INDUSTRY_CONFIG = {
    'automobile': {
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9L18 10l-2.5-5.5C15.2 3.9 14.6 3.5 14 3.5H10c-.6 0-1.2.4-1.5 1L6 10l-2.5 1.1C2.7 11.3 2 12.1 2 13v3c0 .6.4 1 1 1h2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/><path d="M14 17H10" stroke-linecap="round"/><path d="M6 10h12" stroke-linecap="round"/></svg>',
        name: '汽车销售',
        tag: { type: 'hot', text: '热门' }
    },
    'education': {
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c0 1.66 2.69 3 6 3s6-1.34 6-3v-5"/></svg>',
        name: '教育培训',
        tag: null
    }
};

// 场景图标映射
const SCENE_ICON_MAP = {
    'user_group': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    'layers': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>',
    'dollar': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
    'gift': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6M18 9h1.5a2.5 2.5 0 0 0 0-5H18M6 9h12M6 9v11a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V9"/><path d="M10 9V5a2 2 0 0 1 4 0v4"/></svg>',
    'phone': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.362 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.574 2.81.7A2 2 0 0 1 22 16.92z"/></svg>',
    'message': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
    'graduation': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c0 1.66 2.69 3 6 3s6-1.34 6-3v-5"/></svg>',
    'search': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>',
    'card': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><path d="M1 10h22"/></svg>',
    'refresh': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>'
};

// 从数据库加载的行业数据（初始为空，通过 API 加载）
let INDUSTRY_DATA = [];

// DOM 元素
const industryGrid = document.getElementById('industryGrid');
const sceneModalOverlay = document.getElementById('sceneModalOverlay');
const sceneModalClose = document.getElementById('sceneModalClose');
const modalIndustryIcon = document.getElementById('modalIndustryIcon');
const modalIndustryName = document.getElementById('modalIndustryName');
const sceneList = document.getElementById('sceneList');
const toast = document.getElementById('toast');

// ============================================
// 初始化
// ============================================
document.addEventListener('DOMContentLoaded', async () => {
    initEventListeners();
    await loadIndustryData();
    renderIndustryCards();
});

// ============================================
// 从 API 加载行业数据
// ============================================
async function loadIndustryData() {
    try {
        // 显示加载状态
        industryGrid.innerHTML = '<div style="text-align: center; padding: 40px; color: #666;">加载中...</div>';
        
        // 获取行业列表
        const industriesResponse = await fetch('/api/preset-scene/industries');
        const industriesData = await industriesResponse.json();
        
        if (!industriesData.success) {
            throw new Error('获取行业列表失败');
        }
        
        // 为每个行业加载场景
        INDUSTRY_DATA = [];
        for (const industryInfo of industriesData.industries) {
            const industryCode = industryInfo.industry_code;
            const config = INDUSTRY_CONFIG[industryCode];
            
            if (!config) continue; // 跳过未配置的行业
            
            // 获取该行业的场景列表
            const scenesResponse = await fetch(`/api/preset-scene/industry/${industryCode}`);
            const scenesData = await scenesResponse.json();
            
            if (!scenesData.success) continue;
            
            // 转换场景数据格式
            const scenes = scenesData.scenes.map(scene => ({
                id: scene.scene_code,
                icon: getSceneIcon(scene.scene_code),
                name: scene.scene_name,
                desc: scene.scene_description,
                difficulty: scene.difficulty || 'medium',
                aiRole: scene.ai_role,
                userRole: scene.user_role
            }));
            
            INDUSTRY_DATA.push({
                id: industryCode,
                icon: config.icon,
                name: config.name,
                sceneCount: scenes.length,
                tag: config.tag,
                scenes: scenes
            });
        }
        
        console.log('加载的行业数据:', INDUSTRY_DATA);
    } catch (error) {
        console.error('加载行业数据失败:', error);
        showToast('加载数据失败，请刷新页面重试', 'error');
        // 显示错误信息
        industryGrid.innerHTML = '<div style="text-align: center; padding: 40px; color: #f44;">加载失败，请刷新页面重试</div>';
    }
}

// ============================================
// 获取场景图标（根据场景代码智能匹配）
// ============================================
function getSceneIcon(sceneCode) {
    // 根据场景代码关键词匹配图标
    if (sceneCode.includes('visit') || sceneCode.includes('consult')) return SCENE_ICON_MAP.user_group;
    if (sceneCode.includes('drive') || sceneCode.includes('trial')) return SCENE_ICON_MAP.layers;
    if (sceneCode.includes('price') || sceneCode.includes('nego')) return SCENE_ICON_MAP.dollar;
    if (sceneCode.includes('competitor')) return SCENE_ICON_MAP.gift;
    if (sceneCode.includes('followup') || sceneCode.includes('phone')) return SCENE_ICON_MAP.phone;
    if (sceneCode.includes('message')) return SCENE_ICON_MAP.message;
    if (sceneCode.includes('graduation')) return SCENE_ICON_MAP.graduation;
    if (sceneCode.includes('needs') || sceneCode.includes('search')) return SCENE_ICON_MAP.search;
    if (sceneCode.includes('renew') || sceneCode.includes('refresh')) return SCENE_ICON_MAP.refresh;
    if (sceneCode.includes('card') || sceneCode.includes('pay')) return SCENE_ICON_MAP.card;
    
    // 默认图标
    return SCENE_ICON_MAP.user_group;
}

// ============================================
// 渲染行业卡片
// ============================================
function renderIndustryCards() {
    let html = '';

    // 渲染行业卡片
    INDUSTRY_DATA.forEach(industry => {
        const tagHtml = industry.tag
            ? `<span class="card-tag ${industry.tag.type}">${industry.tag.text}</span>`
            : '<span class="card-tag" style="visibility: hidden;">&nbsp;</span>';

        html += `
            <div class="industry-card" data-industry-id="${industry.id}" onclick="openSceneModal('${industry.id}')">
                <div class="card-icon">${industry.icon}</div>
                <div class="card-title">${industry.name}</div>
                <div class="card-scene-count">${industry.sceneCount}个场景</div>
                ${tagHtml}
                <button class="btn-view-scenes" onclick="event.stopPropagation(); openSceneModal('${industry.id}')">查看场景</button>
            </div>
        `;
    });

    // 自定义创建卡片（使用 SVG 图标）
    const customIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 5v14M5 12h14" stroke-linecap="round" stroke-linejoin="round"/></svg>';
    html += `
        <div class="industry-card custom-card" onclick="goToCustomCreate()">
            <div class="card-icon">${customIcon}</div>
            <div class="card-title">自定义创建</div>
            <p class="custom-desc">完全定制你的训练场景<br>适配任何行业和角色</p>
            <button class="btn-custom-start" onclick="event.stopPropagation(); goToCustomCreate()">立即开始</button>
        </div>
    `;

    industryGrid.innerHTML = html;
}

// ============================================
// 事件监听
// ============================================
function initEventListeners() {
    // 关闭模态框按钮
    sceneModalClose.addEventListener('click', closeSceneModal);

    // 点击遮罩层关闭模态框
    sceneModalOverlay.addEventListener('click', (e) => {
        if (e.target === sceneModalOverlay) {
            closeSceneModal();
        }
    });

    // ESC 键关闭模态框
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeSceneModal();
        }
    });
}

// ============================================
// 打开场景选择模态框
// ============================================
function openSceneModal(industryId) {
    const industry = INDUSTRY_DATA.find(item => item.id === industryId);
    if (!industry) return;

    // 设置模态框标题（使用 SVG 图标）
    modalIndustryIcon.innerHTML = industry.icon;
    modalIndustryIcon.style.cssText = 'display: inline-flex; width: 28px; height: 28px; vertical-align: middle;';
    modalIndustryName.textContent = industry.name;

    // 渲染场景列表
    let scenesHtml = '';
    industry.scenes.forEach(scene => {
        const difficultyMap = {
            easy: { text: '入门', class: 'difficulty-easy' },
            medium: { text: '进阶', class: 'difficulty-medium' },
            hard: { text: '高级', class: 'difficulty-hard' }
        };
        const diff = difficultyMap[scene.difficulty] || difficultyMap.medium;

        scenesHtml += `
            <div class="scene-item" onclick="selectScene('${industry.id}', '${scene.id}')">
                <div class="scene-item-left">
                    <div class="scene-item-icon">${scene.icon}</div>
                    <div class="scene-item-info">
                        <div class="scene-item-name">
                            ${scene.name}
                            <span class="scene-item-tag ${diff.class}">${diff.text}</span>
                        </div>
                        <div class="scene-item-desc">${scene.desc}</div>
                    </div>
                </div>
                <span class="scene-item-arrow">→</span>
            </div>
        `;
    });

    sceneList.innerHTML = scenesHtml;

    // 显示模态框
    sceneModalOverlay.classList.add('show');
    document.body.style.overflow = 'hidden';
}

// ============================================
// 关闭场景选择模态框
// ============================================
function closeSceneModal() {
    sceneModalOverlay.classList.remove('show');
    document.body.style.overflow = '';
}

// ============================================
// 选择场景 → 跳转到场景创建页面
// ============================================
async function selectScene(industryId, sceneId) {
    const industry = INDUSTRY_DATA.find(item => item.id === industryId);
    const scene = industry ? industry.scenes.find(s => s.id === sceneId) : null;

    if (!industry || !scene) return;

    closeSceneModal();

    // 增加场景使用次数
    try {
        await fetch(`/api/preset-scene/use/${sceneId}`, { method: 'POST' });
    } catch (error) {
        console.error('更新使用次数失败:', error);
    }

    // 跳转到场景创建页面，带上行业和场景信息
    const params = new URLSearchParams({
        industry: industry.name,
        scene: scene.name,
        scene_desc: scene.desc,
        scene_code: sceneId
    });

    showToast(`正在进入「${scene.name}」场景...`, 'success');

    setTimeout(() => {
        window.location.href = `/scene/create/?${params.toString()}`;
    }, 600);
}

// ============================================
// 跳转到自定义创建页面
// ============================================
function goToCustomCreate() {
    window.location.href = '/scene/create/';
}

// ============================================
// Toast 提示
// ============================================
function showToast(message, type = 'success') {
    toast.textContent = message;
    toast.className = `toast ${type} show`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 2500);
}