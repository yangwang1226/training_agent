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
            
            // 如果行业未在配置中，使用默认配置
            const industryIcon = config?.icon || '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>';
            const industryName = config?.name || industryInfo.industry_name || industryCode;
            const industryTag = config?.tag || null;
            
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
                icon: industryIcon,
                name: industryName,
                sceneCount: scenes.length,
                tag: industryTag,
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
// 选择场景 → 打开背景补充弹窗
// ============================================

// 当前选中的场景信息（供弹窗使用）
let selectedIndustry = null;
let selectedScene = null;

async function selectScene(industryId, sceneId) {
    const industry = INDUSTRY_DATA.find(item => item.id === industryId);
    const scene = industry ? industry.scenes.find(s => s.id === sceneId) : null;

    if (!industry || !scene) return;

    // 保存选中信息
    selectedIndustry = industry;
    selectedScene = scene;

    // 关闭场景选择弹窗
    closeSceneModal();

    // 增加场景使用次数
    try {
        await fetch(`/api/preset-scene/use/${sceneId}`, { method: 'POST' });
    } catch (error) {
        console.error('更新使用次数失败:', error);
    }

        // 跳转到场景配置页面
    setTimeout(() => {
        window.location.href = `/industry/scene-config?scene_code=${scene.id}`;
    }, 300);
}

// ============================================
// 背景补充弹窗
// ============================================
const bgModalOverlay = document.getElementById('bgModalOverlay');
const bgModalClose = document.getElementById('bgModalClose');
const bgBackgroundInput = document.getElementById('bgBackgroundInput');
const bgCharCount = document.getElementById('bgCharCount');
const bgQuickTags = document.getElementById('bgQuickTags');
const bgBtnStart = document.getElementById('bgBtnStart');

// 各场景对应的快捷示例
const QUICK_TAG_MAP = {
    // 汽车销售
    'auto_first_visit': [
        '年轻白领，首次购车，预算15万',
        '中年男性，换车需求，关注商务感',
        '带家人来看，关注空间和安全性',
        '客户对比了多家4S店，比较谨慎'
    ],
    'auto_test_drive': [
        '客户已看过车，想体验驾驶感受',
        '客户犹豫不决，需要推一把',
        '客户时间紧张，需要高效安排'
    ],
    'auto_price_nego': [
        '客户拿到了竞品的更低报价',
        '客户预算有限，但很喜欢这款车',
        '客户想要更多赠品和优惠'
    ],
    'auto_competitor': [
        '客户在对比同级别日系车',
        '客户觉得竞品性价比更高',
        '客户朋友推荐了竞品品牌'
    ],
    'auto_followup': [
        '客户上周来看过车，还没决定',
        '客户已经3天没回消息了',
        '客户说再考虑考虑'
    ],
    // 教育培训
    'edu_consult': [
        '家长关心师资力量和教学效果',
        '孩子成绩中等，想提升数学',
        '家长对比了多家机构'
    ],
    'edu_trial': [
        '家长时间不太方便',
        '孩子对学习不太感兴趣',
        '家长想先了解课程体系'
    ],
    'edu_needs': [
        '初二学生，数学基础薄弱',
        '高一学生，想冲刺重点大学',
        '小学生，注意力不集中'
    ],
    'edu_price': [
        '家长觉得课时费偏高',
        '家长想要分期付款',
        '家长要求打折优惠'
    ],
    'edu_renew': [
        '家长对学习效果不太满意',
        '家长觉得课程太贵想换机构',
        '学生自己不想继续上课了'
    ]
};

// 默认快捷标签（通用）
const DEFAULT_QUICK_TAGS = [
    '客户态度友好，比较容易沟通',
    '客户比较谨慎，需要耐心引导',
    '客户时间紧张，希望高效沟通'
];

// 全局变量：存储当前场景的完整配置
let currentSceneConfig = {
    sceneCode: '',
    sceneName: '',
    sceneDescription: '',
    industryCode: '',
    aiRole: '',
    userRole: '',
    difficulty: '',
    duration: 600,
    openingLine: '',
    fixedQuestions: [],
    relatedQuestions: [],
    sopChecklist: []
};

// 原始预设数据（用于恢复默认）
let originalPresetData = null;

async function openBackgroundModal(industry, scene) {
    try {
        // 显示加载状态
        bgBtnStart.classList.add('loading');
        bgBtnStart.innerHTML = '<span class="spinner"></span>加载中...';
        
        // 调用新 API 获取完整配置
        const response = await fetch(`/api/preset-scene/config/${scene.id}`);
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || '加载场景配置失败');
        }
        
        const config = result.data;
        
        // 保存到全局变量
        currentSceneConfig = {
            sceneCode: config.scene_code,
            sceneName: config.scene_name,
            sceneDescription: config.scene_description,
            industryCode: config.industry_code,
            aiRole: config.ai_role,
            userRole: config.user_role,
            difficulty: config.difficulty,
            duration: config.estimated_duration,
            openingLine: config.opening_line,
            fixedQuestions: JSON.parse(JSON.stringify(config.fixed_questions || [])), // 深拷贝
            relatedQuestions: JSON.parse(JSON.stringify(config.related_questions || [])),
            sopChecklist: JSON.parse(JSON.stringify(config.sop_checklist || []))
        };
        
        // 保存原始数据（用于恢复默认）
        originalPresetData = JSON.parse(JSON.stringify(config));
        
        // 填充场景基础信息
        document.getElementById('bgSceneIcon').innerHTML = scene.icon;
        document.getElementById('bgSceneName').textContent = config.scene_name;
        document.getElementById('bgSceneDesc').textContent = config.scene_description;
        document.getElementById('bgAiRole').textContent = config.ai_role;
        document.getElementById('bgUserRole').textContent = config.user_role;
        
        // 填充难度和时长
        const difficultyMap = { 'easy': '简单', 'medium': '中等', 'hard': '困难' };
        document.getElementById('bgDifficulty').textContent = difficultyMap[config.difficulty] || '中等';
        document.getElementById('bgDuration').textContent = `约${Math.round(config.estimated_duration / 60)}分钟`;
        
        // 清空并重置背景输入
        bgBackgroundInput.value = '';
        bgCharCount.textContent = '0';
        
        // 渲染快捷标签
        const tags = QUICK_TAG_MAP[scene.id] || DEFAULT_QUICK_TAGS;
        bgQuickTags.innerHTML = tags.map(tag =>
            `<button class="bg-quick-tag" onclick="fillQuickTag(this, '${tag.replace(/'/g, "\\'")}')">${tag}</button>`
        ).join('');
        
        // 填充AI开场白
        const bgOpeningInput = document.getElementById('bgOpeningInput');
        if (bgOpeningInput) {
            bgOpeningInput.value = config.opening_line || '';
        }
        
        // 渲染固定问题列表
        renderFixedQuestions(config.fixed_questions || []);
        
        // 渲染关联问题列表
        renderRelatedQuestions(config.related_questions || []);
        
        // 渲染SOP质检项列表
        renderSopChecklist(config.sop_checklist || []);
        
        // 重置按钮状态
        bgBtnStart.classList.remove('loading');
        bgBtnStart.innerHTML = '开始训练 <span class="bg-btn-arrow">→</span>';
        
        // 显示弹窗
        bgModalOverlay.classList.add('show');
        document.body.style.overflow = 'hidden';
        
    } catch (error) {
        console.error('加载场景配置失败:', error);
        alert('加载场景配置失败，请重试');
        bgBtnStart.classList.remove('loading');
        bgBtnStart.innerHTML = '开始训练 <span class="bg-btn-arrow">→</span>';
    }
}

function closeBackgroundModal() {
    bgModalOverlay.classList.remove('show');
    document.body.style.overflow = '';
    
    // 清空待保存的质检项缓存（如果用户取消了）
    if (typeof clearPendingSopItems === 'function') {
        clearPendingSopItems();
    }
}

// 填充快捷标签
function fillQuickTag(el, text) {
    bgBackgroundInput.value = text;
    bgCharCount.textContent = text.length;

    // 切换选中状态
    document.querySelectorAll('.bg-quick-tag').forEach(tag => tag.classList.remove('selected'));
    el.classList.add('selected');

    // 聚焦输入框方便编辑
    bgBackgroundInput.focus();
}

// 字符计数
bgBackgroundInput.addEventListener('input', () => {
    bgCharCount.textContent = bgBackgroundInput.value.length;
    // 取消快捷标签选中
    document.querySelectorAll('.bg-quick-tag').forEach(tag => tag.classList.remove('selected'));
});

// 关闭弹窗事件
bgModalClose.addEventListener('click', closeBackgroundModal);
bgModalOverlay.addEventListener('click', (e) => {
    if (e.target === bgModalOverlay) closeBackgroundModal();
});
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && bgModalOverlay.classList.contains('show')) {
        closeBackgroundModal();
    }
});

// 开始训练按钮 → 根据是否填写背景决定行为
bgBtnStart.addEventListener('click', () => {
    const background = bgBackgroundInput.value.trim();
    submitWithBackground(background);
});

// 提交并跳转：直接调用预设场景生成 API，生成完整提示词后跳转到 realtime 页面
async function submitWithBackground(backgroundHint) {
    if (!selectedIndustry || !selectedScene) return;

    // 按钮加载状态
    bgBtnStart.classList.add('loading');
    bgBtnStart.innerHTML = '正在生成场景...';
    bgBtnStart.disabled = true;

    const message = backgroundHint 
        ? `正在为「${selectedScene.name}」生成定制场景，请稍候...`
        : `正在准备「${selectedScene.name}」场景，请稍候...`;
    showToast(message, 'success');

        try {
        // 获取AI开场白
        const openingInput = document.getElementById('bgOpeningInput');
        const openingLine = openingInput ? openingInput.value.trim() : currentSceneConfig.openingLine;
        
        // 直接调用预设场景生成 API（包含完整配置）
        const response = await fetch('/api/scene/generate-from-preset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                scene_code: selectedScene.id,
                user_background: backgroundHint || null,
                custom_requirements: null,
                // 新增配置项
                opening_line: openingLine,
                fixed_questions: currentSceneConfig.fixedQuestions,
                related_questions: currentSceneConfig.relatedQuestions,
                sop_checklist: currentSceneConfig.sopChecklist
            })
        });

                        const data = await response.json();

        if (data.success) {
            const sceneId = data.scene_id;
            
            // 保存场景ID供 SOP 配置使用
            if (typeof window.currentSceneId !== 'undefined' || typeof currentSceneId !== 'undefined') {
                window.currentSceneId = sceneId;
                if (typeof currentSceneId !== 'undefined') {
                    currentSceneId = sceneId;
                }
            }
            
            showToast(`场景「${selectedScene.name}」生成成功！`, 'success');
            
            // 如果有待保存的质检项，自动保存到场景
            if (typeof pendingSopItems !== 'undefined' && pendingSopItems && pendingSopItems.length > 0) {
                console.log('检测到待保存的质检项，自动保存到场景...');
                showToast('正在保存质检项...', 'info');
                
                // 调用保存函数
                const saved = await saveSopItemsToServer(sceneId, pendingSopItems);
                
                if (saved) {
                    showToast('质检项保存成功！正在进入对练...', 'success');
                    pendingSopItems = null;  // 清空缓存
                } else {
                    showToast('质检项保存失败，但场景已生成', 'warning');
                }
            } else {
                showToast('正在进入对练...', 'success');
            }

            // 延迟跳转到 realtime 页面
            setTimeout(() => {
                window.location.href = data.redirect_url;
            }, 1500);
        } else {
            showToast('场景生成失败：' + (data.error || '未知错误'), 'error');
            // 恢复按钮状态
            resetBackgroundModalButtons();
        }
    } catch (error) {
        console.error('生成场景失败:', error);
        showToast('网络错误，请重试', 'error');
        // 恢复按钮状态
        resetBackgroundModalButtons();
    }
}

// 恢复背景弹窗按钮状态
function resetBackgroundModalButtons() {
    bgBtnStart.classList.remove('loading');
    bgBtnStart.innerHTML = '开始训练 <span class="bg-btn-arrow">→</span>';
    bgBtnStart.disabled = false;
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
// ========== SOP 质检项配置功能 ==========
let currentSopChecklist = [];

// SOP 区域折叠/展开
const bgSopToggle = document.getElementById('bgSopToggle');
const bgSopSection = document.getElementById('bgSopSection');
const bgSopContent = document.getElementById('bgSopContent');

if (bgSopToggle) {
    bgSopToggle.addEventListener('click', () => {
        const isExpanded = bgSopContent.style.display !== 'none';
        bgSopContent.style.display = isExpanded ? 'none' : 'block';
        bgSopSection.classList.toggle('expanded', !isExpanded);
    });
}

// 配置质检项按钮
const bgSopBtnConfig = document.getElementById('bgSopBtnConfig');
if (bgSopBtnConfig) {
    bgSopBtnConfig.addEventListener('click', () => {
        openSopConfigModal();
    });
}

// 打开 SOP 配置弹窗
function openSopConfigModal() {
    const sceneCode = selectedScene?.id;
    if (!sceneCode) {
        showToast('请先选择场景', 'error');
        return;
    }
    
    // 在新窗口打开配置页面
    const configUrl = `/sop/config?scene=${sceneCode}&inline=true`;
    window.open(configUrl, 'sopConfig', 'width=1200,height=800');
    
    // 监听窗口关闭事件，刷新预览
    const checkWindow = setInterval(() => {
        const win = window.open('', 'sopConfig');
        if (win && win.closed) {
            clearInterval(checkWindow);
            loadSopPreview(sceneCode);
        }
    }, 500);
}

// 加载 SOP 预览
async function loadSopPreview(sceneCode) {
    try {
        // 加载预设场景的默认质检项（只读模板）
        const response = await fetch(`/api/sop/checklist/preset/${sceneCode}`);
        const data = await response.json();
        
        if (data.success && data.data.checklist) {
            currentSopChecklist = data.data.checklist;
            renderSopPreview(data.data.checklist);
        }
    } catch (error) {
        console.error('加载 SOP 预览失败:', error);
    }
}

// 渲染 SOP 预览
function renderSopPreview(checklist) {
    const preview = document.getElementById('bgSopPreview');
    
    if (!checklist || checklist.length === 0) {
        preview.innerHTML = '<div class="bg-sop-empty"><span>暂未配置质检项</span></div>';
        return;
    }
    
    const mustDoCount = checklist.filter(item => item.check_type === 'must_do').length;
    const mustNotCount = checklist.filter(item => item.check_type === 'must_not').length;
    
    preview.innerHTML = `
        <div class="bg-sop-items">
            <div class="bg-sop-item must-do">
                <span class="bg-sop-item-icon">✓</span>
                <span class="bg-sop-item-name">必须做</span>
                <span class="bg-sop-item-count">${mustDoCount} 项</span>
            </div>
            <div class="bg-sop-item must-not">
                <span class="bg-sop-item-icon">✗</span>
                <span class="bg-sop-item-name">禁止做</span>
                <span class="bg-sop-item-count">${mustNotCount} 项</span>
            </div>
        </div>
    `;
}

// ============================================
// 渲染配置列表函数
// ============================================

// 渲染固定问题列表
function renderFixedQuestions(questions) {
    const container = document.getElementById('fixedQuestionList');
    const countEl = document.getElementById('fixedQuestionCount');
    
    if (!container || !countEl) return;
    
    countEl.textContent = `共${questions.length}个问题`;
    container.innerHTML = '';
    
    questions.forEach((q, index) => {
        const item = document.createElement('div');
        item.className = 'question-item';
        item.innerHTML = `
            <div class="question-number">${index + 1}</div>
            <div class="question-content">
                <input type="text" 
                    class="question-input" 
                    value="${q.question || ''}" 
                    data-index="${index}"
                    placeholder="请输入问题">
            </div>
            <div class="question-actions">
                <button class="btn-icon btn-delete" onclick="deleteFixedQuestion(${index})" title="删除">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                </button>
            </div>
        `;
        container.appendChild(item);
        
        // 绑定输入事件
        const input = item.querySelector('.question-input');
        input.addEventListener('input', (e) => {
            currentSceneConfig.fixedQuestions[index].question = e.target.value;
        });
    });
}

// 渲染关联问题列表
function renderRelatedQuestions(questions) {
    const container = document.getElementById('relatedQuestionList');
    const countEl = document.getElementById('relatedQuestionCount');
    
    if (!container || !countEl) return;
    
    countEl.textContent = `共${questions.length}个关联问题`;
    container.innerHTML = '';
    
    questions.forEach((q, index) => {
        const keywords = Array.isArray(q.trigger_keywords) ? q.trigger_keywords.join('、') : '';
        const item = document.createElement('div');
        item.className = 'related-question-item';
        item.innerHTML = `
            <div class="related-question-header">
                <span class="related-question-id">${q.id || '关联问题' + (index + 1)}</span>
                <span class="related-question-keywords">触发词：${keywords}</span>
            </div>
            <div class="related-question-content">
                <input type="text" 
                    class="question-input" 
                    value="${q.question || ''}" 
                    data-index="${index}"
                    placeholder="请输入问题">
            </div>
            <div class="question-actions">
                <button class="btn-icon btn-delete" onclick="deleteRelatedQuestion(${index})" title="删除">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                </button>
            </div>
        `;
        container.appendChild(item);
        
        // 绑定输入事件
        const input = item.querySelector('.question-input');
        input.addEventListener('input', (e) => {
            currentSceneConfig.relatedQuestions[index].question = e.target.value;
        });
    });
}

// 渲染SOP质检项列表
function renderSopChecklist(checklist) {
    const container = document.getElementById('sopList');
    const countEl = document.getElementById('sopChecklistCount');
    
    if (!container || !countEl) return;
    
    countEl.textContent = `共${checklist.length}个质检项`;
    container.innerHTML = '';
    
    checklist.forEach((item, index) => {
        const div = document.createElement('div');
        div.className = 'sop-item';
        const title = item.title || item.name || item.check_point || '';
        const description = item.description || item.check_criteria || '';
        
        div.innerHTML = `
            <div class="sop-checkbox">
                <input type="checkbox" checked disabled>
            </div>
            <div class="sop-content">
                <div class="sop-title">${index + 1}. ${title}</div>
                <div class="sop-description">${description}</div>
            </div>
            <div class="question-actions">
                <button class="btn-icon btn-delete" onclick="deleteSopItem(${index})" title="删除">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                </button>
            </div>
        `;
        container.appendChild(div);
    });
}

// ============================================
// 删除和添加操作
// ============================================

function deleteFixedQuestion(index) {
    if (confirm('确定要删除这个问题吗？')) {
        currentSceneConfig.fixedQuestions.splice(index, 1);
        renderFixedQuestions(currentSceneConfig.fixedQuestions);
    }
}

function deleteRelatedQuestion(index) {
    if (confirm('确定要删除这个关联问题吗？')) {
        currentSceneConfig.relatedQuestions.splice(index, 1);
        renderRelatedQuestions(currentSceneConfig.relatedQuestions);
    }
}

function deleteSopItem(index) {
    if (confirm('确定要删除这个质检项吗？')) {
        currentSceneConfig.sopChecklist.splice(index, 1);
        renderSopChecklist(currentSceneConfig.sopChecklist);
    }
}

// ============================================
// 恢复默认按钮事件
// ============================================

const btnRestoreOpening = document.getElementById('btnRestoreOpening');
if (btnRestoreOpening) {
    btnRestoreOpening.addEventListener('click', () => {
        if (originalPresetData) {
            const input = document.getElementById('bgOpeningInput');
            if (input) {
                input.value = originalPresetData.opening_line || '';
                currentSceneConfig.openingLine = originalPresetData.opening_line || '';
            }
        }
    });
}

const btnRestoreFixed = document.getElementById('btnRestoreFixed');
if (btnRestoreFixed) {
    btnRestoreFixed.addEventListener('click', () => {
        if (originalPresetData && originalPresetData.fixed_questions) {
            currentSceneConfig.fixedQuestions = JSON.parse(JSON.stringify(originalPresetData.fixed_questions));
            renderFixedQuestions(currentSceneConfig.fixedQuestions);
        }
    });
}

const btnRestoreRelated = document.getElementById('btnRestoreRelated');
if (btnRestoreRelated) {
    btnRestoreRelated.addEventListener('click', () => {
        if (originalPresetData && originalPresetData.related_questions) {
            currentSceneConfig.relatedQuestions = JSON.parse(JSON.stringify(originalPresetData.related_questions));
            renderRelatedQuestions(currentSceneConfig.relatedQuestions);
        }
    });
}

const btnRestoreSop = document.getElementById('btnRestoreSop');
if (btnRestoreSop) {
    btnRestoreSop.addEventListener('click', () => {
        if (originalPresetData && originalPresetData.sop_checklist) {
            currentSceneConfig.sopChecklist = JSON.parse(JSON.stringify(originalPresetData.sop_checklist));
            renderSopChecklist(currentSceneConfig.sopChecklist);
        }
    });
}

// ============================================
// 折叠/展开按钮事件
// ============================================

document.querySelectorAll('.bg-section-header').forEach(header => {
    header.addEventListener('click', function() {
        const target = this.getAttribute('data-target');
        const content = document.getElementById(target);
        const collapseBtn = this.querySelector('.btn-collapse-mini');
        
        if (content) {
            content.classList.toggle('collapsed');
            this.classList.toggle('expanded');
        }
    });
});

// 在场景选择时加载 SOP 预览（保持兼容性）
if (typeof loadSopPreview === 'function') {
    const _originalOpenBgModal = openBackgroundModal;
    openBackgroundModal = async function(industry, scene) {
        await _originalOpenBgModal(industry, scene);
        if (scene && scene.id) {
            try {
                await loadSopPreview(scene.id);
            } catch (e) {
                console.error('Load SOP preview failed:', e);
            }
        }
    };
}
