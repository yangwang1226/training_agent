// 场景配置页面 JavaScript

// 全局变量
let sceneCode = '';
let currentConfig = {
    sceneName: '',
    sceneDescription: '',
    aiRole: '',
    userRole: '',
    difficulty: '',
    duration: 600,
    openingLine: '',
    fixedQuestions: [],
    relatedQuestions: [],
    sopChecklist: []
};

let originalConfig = null; // 用于恢复默认

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    // 从URL获取场景代码
    const urlParams = new URLSearchParams(window.location.search);
    sceneCode = urlParams.get('scene_code');
    
    if (!sceneCode) {
        alert('缺少场景参数');
        history.back();
        return;
    }
    
    // 加载场景配置
    loadSceneConfig();
    
    // 绑定事件
    initEventListeners();
});

// 加载场景配置
async function loadSceneConfig() {
    try {
        showLoading(true);
        
        const response = await fetch(`/api/preset-scene/config/${sceneCode}`);
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || '加载场景配置失败');
        }
        
        const config = result.data;
        
        // 保存配置
        currentConfig = {
            sceneCode: config.scene_code,
            sceneName: config.scene_name,
            sceneDescription: config.scene_description,
            industryCode: config.industry_code,
            aiRole: config.ai_role,
            userRole: config.user_role,
            difficulty: config.difficulty,
            duration: config.estimated_duration,
            openingLine: config.opening_line || '',
            fixedQuestions: JSON.parse(JSON.stringify(config.fixed_questions || [])),
            relatedQuestions: JSON.parse(JSON.stringify(config.related_questions || [])),
            sopChecklist: JSON.parse(JSON.stringify(config.sop_checklist || []))
        };
        
        // 保存原始配置（用于恢复默认）
        originalConfig = JSON.parse(JSON.stringify(config));
        
        // 调试：打印配置信息
        console.log('加载的场景配置:', currentConfig);
        console.log('固定问题数量:', currentConfig.fixedQuestions.length);
        console.log('关联问题数量:', currentConfig.relatedQuestions.length);
        console.log('SOP质检项数量:', currentConfig.sopChecklist.length);
        if (currentConfig.sopChecklist.length > 0) {
            console.log('第一个SOP质检项:', currentConfig.sopChecklist[0]);
        }
        
        // 渲染页面
        renderPage();
        
    } catch (error) {
        console.error('加载场景配置失败:', error);
        alert('加载场景配置失败：' + error.message);
        history.back();
    } finally {
        showLoading(false);
    }
}

// 渲染页面
function renderPage() {
    // 更新页面标题
    document.getElementById('pageTitle').textContent = `场景配置 - ${currentConfig.sceneName}`;
    document.title = `场景配置 - ${currentConfig.sceneName}`;
    
    // 渲染场景信息
    renderSceneInfo();
    
    // 渲染场景背景
    renderBackground();
    
    // 渲染AI开场白
    renderOpening();
    
    // 渲染固定问题
    renderFixedQuestions();
    
    // 渲染关联问题
    renderRelatedQuestions();
    
    // 渲染SOP质检项
    renderSopChecklist();
}

// 渲染场景信息
function renderSceneInfo() {
    document.getElementById('sceneName').textContent = currentConfig.sceneName;
    document.getElementById('sceneDesc').textContent = currentConfig.sceneDescription;
    document.getElementById('aiRole').textContent = currentConfig.aiRole;
    document.getElementById('userRole').textContent = currentConfig.userRole;
    
    const difficultyMap = { 'easy': '简单', 'medium': '中等', 'hard': '困难' };
    document.getElementById('difficulty').textContent = difficultyMap[currentConfig.difficulty] || '中等';
    document.getElementById('duration').textContent = `约${Math.round(currentConfig.duration / 60)}分钟`;
}

// 渲染场景背景
function renderBackground() {
    const input = document.getElementById('backgroundInput');
    const charCount = document.getElementById('charCount');
    
    input.value = '';
    charCount.textContent = '0';
    
    // 渲染快捷标签（可以根据场景类型定制）
    const quickTags = [
        '30岁女性，首次购车',
        '刚需，预算有限',
        '关注安全性',
        '周末看车'
    ];
    
    const tagsContainer = document.getElementById('quickTags');
    tagsContainer.innerHTML = quickTags.map(tag => 
        `<button class="quick-tag" onclick="fillQuickTag('${tag}')">${tag}</button>`
    ).join('');
    
    // 字符计数
    input.addEventListener('input', function() {
        charCount.textContent = this.value.length;
    });
}

// 填充快捷标签
function fillQuickTag(text) {
    const input = document.getElementById('backgroundInput');
    input.value = text;
    document.getElementById('charCount').textContent = text.length;
    
    // 更新选中状态
    document.querySelectorAll('.quick-tag').forEach(tag => {
        tag.classList.toggle('selected', tag.textContent === text);
    });
}

// 渲染AI开场白
function renderOpening() {
    document.getElementById('openingInput').value = currentConfig.openingLine;
}
// 渲染固定问题
function renderFixedQuestions() {
    const container = document.getElementById('fixedQuestionList');
    const countEl = document.getElementById('fixedQuestionCount');
    
    countEl.textContent = `共${currentConfig.fixedQuestions.length}个问题`;
    container.innerHTML = '';
    
    currentConfig.fixedQuestions.forEach((q, index) => {
        const item = document.createElement('div');
        item.className = 'question-item';
        item.innerHTML = `
            <div class="question-number">${index + 1}</div>
            <div class="question-content">
                <input type="text" 
                    class="question-input" 
                    value="${escapeHtml(q.question || '')}" 
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
        
        const input = item.querySelector('.question-input');
        input.addEventListener('input', function() {
            currentConfig.fixedQuestions[index].question = this.value;
        });
    });
}

function renderRelatedQuestions() {
    const container = document.getElementById('relatedQuestionList');
    const countEl = document.getElementById('relatedQuestionCount');
    
    countEl.textContent = `共${currentConfig.relatedQuestions.length}个关联问题`;
    container.innerHTML = '';
    
    currentConfig.relatedQuestions.forEach((q, index) => {
        const keywords = Array.isArray(q.trigger_keywords) ? q.trigger_keywords.join('、') : '';
        const item = document.createElement('div');
        item.className = 'related-question-item';
        item.innerHTML = `
            <div class="related-question-header">
                <div class="related-question-title">💰 关联问题 ${index + 1}</div>
                <div class="question-actions">
                    <button class="btn-icon btn-delete" onclick="deleteRelatedQuestion(${index})" title="删除">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                </div>
            </div>
            <div class="related-question-keywords">触发词：${escapeHtml(keywords)}</div>
            <div class="related-question-content">
                <input type="text" 
                    class="question-input" 
                    value="${escapeHtml(q.question || '')}" 
                    data-index="${index}"
                    placeholder="请输入问题">
            </div>
        `;
        container.appendChild(item);
        
        const input = item.querySelector('.question-input');
        input.addEventListener('input', function() {
            currentConfig.relatedQuestions[index].question = this.value;
        });
    });
}

function renderSopChecklist() {
    const container = document.getElementById('sopList');
    const countEl = document.getElementById('sopChecklistCount');
    
    if (!currentConfig.sopChecklist || currentConfig.sopChecklist.length === 0) {
        countEl.textContent = '共0个质检项';
        container.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">暂无质检项</div>';
        return;
    }
    
    // 计算总分
    const totalScore = currentConfig.sopChecklist.reduce((sum, item) => {
        const score = parseInt(item.item_score) || 0;
        return sum + score;
    }, 0);
    
    countEl.textContent = `共${currentConfig.sopChecklist.length}个质检项 (总分: ${totalScore}分)`;
    container.innerHTML = '';
    
    currentConfig.sopChecklist.forEach((item, index) => {
        // 使用 item_name 作为标题
        const title = item.item_name || item.check_point || item.title || `质检项${index + 1}`;
        const description = item.check_criteria || item.description || item.scoring_standard || '';
        const score = item.item_score || 0;
        const checkType = item.check_type || 'must_do';
        const typeText = checkType === 'must_do' ? '必须做' : checkType === 'must_not' ? '禁止做' : '';
        const typeColor = checkType === 'must_do' ? '#e3f2fd' : '#ffebee';
        const typeTextColor = checkType === 'must_do' ? '#1976d2' : '#c62828';
        
        const div = document.createElement('div');
        div.className = 'sop-item';
        div.innerHTML = `
            <div class="sop-checkbox">
                <input type="checkbox" checked disabled>
            </div>
            <div class="sop-content">
                <div class="sop-title">
                    ${index + 1}. ${escapeHtml(title)}
                    ${typeText ? `<span style="margin-left: 8px; padding: 2px 8px; background: ${typeColor}; color: ${typeTextColor}; border-radius: 4px; font-size: 12px;">${typeText}</span>` : ''}
                    <span style="margin-left: 8px; padding: 2px 8px; background: #fff3e0; color: #e65100; border-radius: 4px; font-size: 12px; font-weight: 600;">${score}分</span>
                </div>
                <div class="sop-description">${escapeHtml(description)}</div>
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

function deleteFixedQuestion(index) {
    if (confirm('确定要删除这个问题吗？')) {
        currentConfig.fixedQuestions.splice(index, 1);
        renderFixedQuestions();
    }
}

function deleteRelatedQuestion(index) {
    if (confirm('确定要删除这个关联问题吗？')) {
        currentConfig.relatedQuestions.splice(index, 1);
        renderRelatedQuestions();
    }
}

function deleteSopItem(index) {
    if (confirm('确定要删除这个质检项吗？')) {
        currentConfig.sopChecklist.splice(index, 1);
        renderSopChecklist();
    }
}
function initEventListeners() {
    document.getElementById('btnRestoreOpening').addEventListener('click', restoreOpening);
    document.getElementById('btnRestoreFixed').addEventListener('click', restoreFixed);
    document.getElementById('btnRestoreRelated').addEventListener('click', restoreRelated);
    document.getElementById('btnRestoreSop').addEventListener('click', restoreSop);
    
    document.getElementById('btnAddFixed').addEventListener('click', addFixedQuestion);
    document.getElementById('btnAddRelated').addEventListener('click', addRelatedQuestion);
    document.getElementById('btnAddSop').addEventListener('click', addSopItem);
    
    document.getElementById('btnStartTraining').addEventListener('click', submitAndStart);
    document.getElementById('btnSubmit').addEventListener('click', submitAndStart);
    
    document.querySelectorAll('.section-header.clickable').forEach(header => {
        header.addEventListener('click', function() {
            const target = this.getAttribute('data-target');
            const content = document.getElementById(target);
            if (content) {
                content.classList.toggle('collapsed');
                this.classList.toggle('expanded');
            }
        });
    });
}

function restoreOpening() {
    if (originalConfig) {
        currentConfig.openingLine = originalConfig.opening_line || '';
        document.getElementById('openingInput').value = currentConfig.openingLine;
    }
}

function restoreFixed() {
    if (originalConfig && originalConfig.fixed_questions) {
        currentConfig.fixedQuestions = JSON.parse(JSON.stringify(originalConfig.fixed_questions));
        renderFixedQuestions();
    }
}

function restoreRelated() {
    if (originalConfig && originalConfig.related_questions) {
        currentConfig.relatedQuestions = JSON.parse(JSON.stringify(originalConfig.related_questions));
        renderRelatedQuestions();
    }
}

function restoreSop() {
    if (originalConfig && originalConfig.sop_checklist) {
        currentConfig.sopChecklist = JSON.parse(JSON.stringify(originalConfig.sop_checklist));
        renderSopChecklist();
    }
}

function addFixedQuestion() {
    const newQuestion = {
        order: currentConfig.fixedQuestions.length + 1,
        question: '',
        check_points: [],
        difficulty: 'medium'
    };
    currentConfig.fixedQuestions.push(newQuestion);
    renderFixedQuestions();
}

function addRelatedQuestion() {
    const newQuestion = {
        id: `custom_${Date.now()}`,
        trigger_keywords: [],
        question: '',
        check_points: [],
        difficulty: 'medium'
    };
    currentConfig.relatedQuestions.push(newQuestion);
    renderRelatedQuestions();
}

function addSopItem() {
    const newItem = {
        check_point: '新质检项',
        check_criteria: '请填写质检标准',
        check_type: 'must_do'
    };
    currentConfig.sopChecklist.push(newItem);
    renderSopChecklist();
}

async function submitAndStart() {
    const backgroundInput = document.getElementById('backgroundInput');
    const openingInput = document.getElementById('openingInput');
    
    const background = backgroundInput.value.trim();
    const opening = openingInput.value.trim();
    
    if (!background) {
        alert('请填写场景背景');
        backgroundInput.focus();
        return;
    }
    
    if (!opening) {
        alert('请填写AI开场白');
        openingInput.focus();
        return;
    }
    
    try {
        showLoading(true);
        
        const response = await fetch('/api/scene/generate-from-preset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                scene_code: sceneCode,
                user_background: background,
                opening_line: opening,
                fixed_questions: currentConfig.fixedQuestions,
                related_questions: currentConfig.relatedQuestions,
                sop_checklist: currentConfig.sopChecklist
            })
        });
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || '场景创建失败');
        }
        
        window.location.href = `/realtime?session_id=${result.session_id}`;
        
    } catch (error) {
        console.error('提交失败:', error);
        alert('提交失败：' + error.message);
    } finally {
        showLoading(false);
    }
}

function showLoading(show) {
    const btn1 = document.getElementById('btnStartTraining');
    const btn2 = document.getElementById('btnSubmit');
    
    if (show) {
        btn1.classList.add('loading');
        btn2.classList.add('loading');
        btn1.innerHTML = '<span class="spinner"></span> 正在生成...';
        btn2.innerHTML = '<span class="spinner"></span> 正在生成...';
        btn1.disabled = true;
        btn2.disabled = true;
    } else {
        btn1.classList.remove('loading');
        btn2.classList.remove('loading');
        btn1.innerHTML = '开始训练 <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>';
        btn2.innerHTML = '开始训练 <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>';
        btn1.disabled = false;
        btn2.disabled = false;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
