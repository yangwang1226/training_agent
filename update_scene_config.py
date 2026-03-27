import os

html_content = """{% extends "layout.html" %}

{% block title %}场景配置 - AI教练后台管理系统{% endblock %}

{% block breadcrumb %}
<span class="breadcrumb-item"><a href="/manage_system/">首页</a></span>
<span class="breadcrumb-separator">/</span>
<span class="breadcrumb-item"><a href="/manage_system/builder">构建器</a></span>
<span class="breadcrumb-separator">/</span>
<span class="breadcrumb-item active">场景配置 (新版草稿)</span>
{% endblock %}

{% block extra_css %}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {
    --ink-black: #1a1a1a;
    --ink-gray: #4a4a4a;
    --ink-light: #767676;
    --paper-white: #ffffff;
    --bg-subtle: #f9fafb;
    --border-light: #e5e7eb;
    --primary-purple: #6366f1;
    --primary-purple-light: #e0e7ff;
    --accent-orange: #f97316;
    --danger-red: #ef4444;
    --success-green: #10b981;
}

body {
    font-family: 'Plus Jakarta Sans', sans-serif;
    background-color: var(--bg-subtle);
}

.config-header {
    background: var(--paper-white);
    padding: 1.5rem 2rem;
    border-bottom: 1px solid var(--border-light);
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: -2rem -2rem 2rem -2rem;
}

.scene-summary {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.scene-summary-icon {
    font-size: 2.5rem;
    background: var(--bg-subtle);
    padding: 0.5rem;
    border-radius: 12px;
}

.scene-summary-info h1 {
    margin: 0 0 0.5rem 0;
    font-size: 1.5rem;
    color: var(--ink-black);
}

.scene-tags {
    display: flex;
    gap: 0.5rem;
}

.badge {
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    background: var(--bg-subtle);
    color: var(--ink-gray);
    border: 1px solid var(--border-light);
}

.badge.primary { background: var(--primary-purple-light); color: var(--primary-purple); border-color: transparent; }
.badge.warning { background: #ffedd5; color: var(--accent-orange); border-color: transparent; }

.header-actions {
    display: flex;
    gap: 1rem;
}

.btn {
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    border: none;
    transition: all 0.2s;
    font-size: 0.875rem;
}

.btn-outline {
    background: white;
    border: 1px solid var(--border-light);
    color: var(--ink-gray);
}
.btn-outline:hover { background: var(--bg-subtle); }

.btn-primary {
    background: var(--primary-purple);
    color: white;
}
.btn-primary:hover { background: #4f46e5; }

.config-container {
    max-width: 800px;
    margin: 0 auto;
    padding-bottom: 4rem;
}

.section-card {
    background: var(--paper-white);
    border-radius: 16px;
    border: 1px solid var(--border-light);
    margin-bottom: 1.5rem;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.section-header {
    padding: 1.5rem;
    border-bottom: 1px solid var(--border-light);
    background: #fafafa;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.section-header h2 {
    margin: 0;
    font-size: 1.125rem;
    color: var(--ink-black);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.section-header p {
    margin: 0.25rem 0 0 1.75rem;
    font-size: 0.875rem;
    color: var(--ink-light);
}

.section-body {
    padding: 1.5rem;
}

.form-group {
    margin-bottom: 1.5rem;
}
.form-group:last-child { margin-bottom: 0; }

.form-label {
    display: block;
    font-weight: 600;
    margin-bottom: 0.5rem;
    color: var(--ink-black);
}

.form-control {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid var(--border-light);
    border-radius: 8px;
    font-family: inherit;
    font-size: 0.875rem;
    color: var(--ink-black);
    transition: border-color 0.2s;
}
.form-control:focus {
    outline: none;
    border-color: var(--primary-purple);
    box-shadow: 0 0 0 3px var(--primary-purple-light);
}
textarea.form-control { resize: vertical; min-height: 100px; }

.chip-group {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
    flex-wrap: wrap;
}
.chip {
    padding: 0.35rem 0.75rem;
    background: var(--bg-subtle);
    border: 1px solid var(--border-light);
    border-radius: 6px;
    font-size: 0.75rem;
    color: var(--ink-gray);
    cursor: pointer;
    transition: all 0.2s;
}
.chip:hover {
    background: var(--primary-purple-light);
    color: var(--primary-purple);
    border-color: var(--primary-purple-light);
}

/* 列表项样式 (SOP 和 异议) */
.dynamic-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}
.list-item {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    background: var(--bg-subtle);
    padding: 0.75rem;
    border-radius: 8px;
    border: 1px solid transparent;
}
.list-item:hover {
    border-color: var(--border-light);
    background: white;
}
.list-item-number {
    width: 24px;
    height: 24px;
    background: var(--ink-black);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: bold;
    flex-shrink: 0;
    margin-top: 0.25rem;
}
.list-item-content {
    flex: 1;
}
.list-item-input {
    width: 100%;
    background: transparent;
    border: none;
    font-size: 0.875rem;
    color: var(--ink-black);
    outline: none;
    resize: none;
}
.btn-icon {
    background: transparent;
    border: none;
    color: var(--ink-light);
    cursor: pointer;
    padding: 0.25rem;
    border-radius: 4px;
}
.btn-icon:hover {
    color: var(--danger-red);
    background: #fee2e2;
}
.btn-add {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--primary-purple);
    background: transparent;
    border: 1px dashed var(--primary-purple);
    padding: 0.75rem;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
    font-size: 0.875rem;
    width: 100%;
    justify-content: center;
    margin-top: 0.75rem;
    transition: all 0.2s;
}
.btn-add:hover {
    background: var(--primary-purple-light);
    border-style: solid;
}

/* 高级设置折叠 */
.collapsible-header {
    cursor: pointer;
    user-select: none;
}
.collapsible-header:hover {
    background: #f3f4f6;
}
.collapsible-content {
    display: none;
}
.collapsible-content.open {
    display: block;
}
.toggle-icon {
    transition: transform 0.3s;
}
.open .toggle-icon {
    transform: rotate(180deg);
}

.radio-group {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}
.radio-label {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    font-size: 0.875rem;
    color: var(--ink-gray);
    cursor: pointer;
}
.radio-label input[type="radio"] {
    margin-top: 0.25rem;
}

.hint-text {
    font-size: 0.75rem;
    color: var(--ink-light);
    margin-top: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.25rem;
}
</style>
{% endblock %}

{% block content %}
<div class="config-page">
    
    <!-- 顶部状态栏 -->
    <header class="config-header">
        <div class="scene-summary">
            <div class="scene-summary-icon">🚗</div>
            <div class="scene-summary-info">
                <h1>汽车首次邀约到店</h1>
                <div class="scene-tags">
                    <span class="badge primary">🎯 销售转化</span>
                    <span class="badge">⏱️ 约10分钟</span>
                    <span class="badge warning">⭐ 中等难度</span>
                </div>
            </div>
        </div>
        <div class="header-actions">
            <button class="btn btn-outline" onclick="history.back()">取消修改</button>
            <button class="btn btn-outline">保存草稿</button>
            <button class="btn btn-primary" onclick="startTraining()">开始训练 ▶</button>
        </div>
    </header>

    <main class="config-container">
        
        <!-- ================= 核心设定 (必填) ================= -->
        <div class="section-card">
            <div class="section-header">
                <div>
                    <h2>📌 核心设定 <span class="badge" style="background:#fee2e2;color:#ef4444;border:none;">必填</span></h2>
                    <p>定义这场沟通的背景和你的目标</p>
                </div>
            </div>
            
            <div class="section-body">
                <!-- 场景背景 -->
                <div class="form-group">
                    <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 0.5rem;">
                        <label class="form-label" style="margin:0;">1. 📝 场景背景与人物设定</label>
                        <div class="chip-group" style="margin:0;">
                            <button class="chip" onclick="applyTemplate('female')">👱‍♀️ 模板: 30岁女白领/20万预算</button>
                            <button class="chip" onclick="applyTemplate('family')">👨‍👩‍👧 模板: 二胎家庭/注重空间</button>
                        </div>
                    </div>
                    <textarea id="backgroundInput" class="form-control" rows="4">客户是30岁女性白领，预算20万左右，关注安全性和外观，周末带家人来看车。
这是她第一次购车，对汽车参数不太了解，更看重服务体验和试驾感受。</textarea>
                    <div class="hint-text">💡 提示：描述越生动，AI扮演的客户就越真实。（建议包含：客户画像、当前痛点、核心诉求）</div>
                </div>

                <!-- 考核目标 -->
                <div class="form-group" style="margin-top: 2rem;">
                    <label class="form-label">2. 🎯 考核目标 (SOP质检项)</label>
                    <div class="dynamic-list" id="sopList">
                        <!-- JS 动态渲染 -->
                    </div>
                    <button class="btn-add" onclick="addSopItem()">+ 添加考核目标</button>
                    <div class="hint-text">💡 提示：系统将根据这些目标，在对话结束后为你的表现打分。</div>
                </div>
            </div>
        </div>

        <!-- ================= 实战挑战 (选填) ================= -->
        <div class="section-card">
            <div class="section-header">
                <div>
                    <h2>⚔️ 实战挑战 <span class="badge">选填</span></h2>
                    <p>给这场练习增加一点真实的“麻烦”</p>
                </div>
            </div>
            
            <div class="section-body">
                <div class="form-group">
                    <label class="form-label">🛡️ 客户异议预设</label>
                    <p style="font-size:0.875rem; color:var(--ink-gray); margin-bottom:1rem;">客户会在对话中见机行事，抛出以下难题考验你：</p>
                    
                    <div class="dynamic-list" id="objectionList">
                        <!-- JS 动态渲染 -->
                    </div>
                    <button class="btn-add" onclick="addObjectionItem()">+ 添加客户异议</button>
                    <div class="hint-text">💡 提示：不需要设置复杂的触发条件，AI会在合适的时机自然地提出这些质疑。</div>
                </div>
            </div>
        </div>

        <!-- ================= 对话控制 (高级设置/折叠) ================= -->
        <div class="section-card">
            <div class="section-header collapsible-header" onclick="toggleAdvanced()">
                <div>
                    <h2>⚙️ 对话控制 (高级设置) <span class="badge">选填</span></h2>
                    <p>掌控开场白与对话结束的节奏</p>
                </div>
                <svg class="toggle-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
            </div>
            
            <div class="section-body collapsible-content" id="advancedContent">
                <!-- AI 开场白 -->
                <div class="form-group">
                    <label class="form-label">🎤 AI 开场白</label>
                    <input type="text" class="form-control" value="您好，我随便看看，你们这款SUV现在有什么优惠吗？" placeholder="如果不填，将由 AI 自动根据背景生成开场白">
                    <div class="hint-text">💡 第一句话由 AI 模拟客户先开口。</div>
                </div>

                <!-- 结束条件 -->
                <div class="form-group" style="margin-top: 1.5rem;">
                    <label class="form-label">🛑 对话结束条件</label>
                    <div class="radio-group">
                        <label class="radio-label">
                            <input type="radio" name="endCondition" value="manual">
                            <span>仅允许用户手动点击结束对话</span>
                        </label>
                        <label class="radio-label">
                            <input type="radio" name="endCondition" value="ai_auto" checked>
                            <div>
                                <span>允许 AI 主动结束对话（推荐）</span>
                                <input type="text" class="form-control" style="margin-top:0.5rem;" value="当用户成功加上微信并约好试驾时间后，或者客户明确表示完全没兴趣要离开时。">
                            </div>
                        </label>
                    </div>
                </div>
            </div>
        </div>

    </main>
</div>
{% endblock %}

{% block extra_js %}
<script>
// Mock Data 初始化
const mockSops = [
    "[必做] 热情接待并主动询问购车预算和用途",
    "[必做] 针对女性客户，重点介绍车辆的安全配置和高颜值外观",
    "[加分] 成功邀约客户登记试驾"
];

const mockObjections = [
    "隔壁那款车只要18万，你们这太贵了。",
    "我老公说这牌子保值率不行，我还在犹豫。"
];

document.addEventListener('DOMContentLoaded', () => {
    renderList('sopList', mockSops, '例如：主动破冰并递交名片...');
    renderList('objectionList', mockObjections, '例如：我觉得你们的贷款利息太高了...');
});

// 渲染列表通用函数
function renderList(containerId, items, placeholder) {
    const container = document.getElementById(containerId);
    container.innerHTML = items.map((item, index) => `
        <div class="list-item">
            <div class="list-item-number">${index + 1}</div>
            <div class="list-item-content">
                <input type="text" class="list-item-input" value="${item}" placeholder="${placeholder}">
            </div>
            <button class="btn-icon" onclick="removeItem(this, '${containerId}')" title="删除">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
            </button>
        </div>
    `).join('');
}

// 添加项
function addSopItem() {
    const container = document.getElementById('sopList');
    const index = container.children.length + 1;
    container.insertAdjacentHTML('beforeend', `
        <div class="list-item">
            <div class="list-item-number">${index}</div>
            <div class="list-item-content">
                <input type="text" class="list-item-input" placeholder="例如：主动破冰并递交名片...">
            </div>
            <button class="btn-icon" onclick="removeItem(this, 'sopList')" title="删除">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
        </div>
    `);
    updateNumbers('sopList');
}

function addObjectionItem() {
    const container = document.getElementById('objectionList');
    const index = container.children.length + 1;
    container.insertAdjacentHTML('beforeend', `
        <div class="list-item">
            <div class="list-item-number">${index}</div>
            <div class="list-item-content">
                <input type="text" class="list-item-input" placeholder="例如：我觉得你们的贷款利息太高了...">
            </div>
            <button class="btn-icon" onclick="removeItem(this, 'objectionList')" title="删除">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
        </div>
    `);
    updateNumbers('objectionList');
}

// 删除项并重新编号
function removeItem(btn, containerId) {
    btn.closest('.list-item').remove();
    updateNumbers(containerId);
}

function updateNumbers(containerId) {
    const items = document.getElementById(containerId).querySelectorAll('.list-item-number');
    items.forEach((item, index) => {
        item.textContent = index + 1;
    });
}

// 快速应用模板
function applyTemplate(type) {
    const bgInput = document.getElementById('backgroundInput');
    if (type === 'female') {
        bgInput.value = "客户是30岁女性白领，预算20万左右，关注安全性和外观，周末带家人来看车。\n这是她第一次购车，对汽车参数不太了解，更看重服务体验和试驾感受。";
    } else if (type === 'family') {
        bgInput.value = "客户是35岁二胎奶爸，预算25万左右，旧车是一台小轿车打算置换。\n核心诉求是空间大、后排舒适，打算买MPV或中大型SUV，对油耗有一定要求。";
    }
    
    // 简单动画提示
    bgInput.style.backgroundColor = 'var(--primary-purple-light)';
    setTimeout(() => { bgInput.style.backgroundColor = 'transparent'; }, 500);
}

// 折叠高级设置
function toggleAdvanced() {
    const content = document.getElementById('advancedContent');
    const header = document.querySelector('.collapsible-header');
    content.classList.toggle('open');
    header.classList.toggle('open');
}

// 模拟开始训练
function startTraining() {
    const btn = document.querySelector('.btn-primary');
    btn.innerHTML = '正在初始化剧本...';
    btn.style.opacity = '0.7';
    setTimeout(() => {
        alert('假装跳转到了训练页面！\n配置已打包传给大模型。');
        btn.innerHTML = '开始训练 ▶';
        btn.style.opacity = '1';
    }, 1000);
}
</script>
{% endblock %}
"""

filepath = 'front_end/manage_system/templates/scenes/scene_config.html'
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(html_content)
print(f'Successfully overwrote {filepath}')