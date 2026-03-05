// 场景创建页面 JavaScript

let currentSceneId = null;
let generatedSceneContent = null;
let isSessionInitialized = false;  // 防止重复初始化

// DOM 元素
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const actionBar = document.getElementById('action-bar');
const viewBtn = document.getElementById('view-btn');
const startBtn = document.getElementById('start-btn');
const modal = document.getElementById('content-modal');
const modalBody = document.getElementById('modal-body');
const closeModalBtn = document.getElementById('close-modal');
const closeModalFooterBtn = document.getElementById('close-modal-btn');
const confirmStartBtn = document.getElementById('confirm-start-btn');
const progressSection = document.getElementById('progress-section');
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    // 自动开始对话（只调用一次）
    if (!isSessionInitialized) {
        setTimeout(() => {
            createSceneSession();
        }, 300);
    }
});

function initEventListeners() {
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    viewBtn.addEventListener('click', showGeneratedContent);
    startBtn.addEventListener('click', saveAndStartTraining);
    
    closeModalBtn.addEventListener('click', hideModal);
    closeModalFooterBtn.addEventListener('click', hideModal);
    confirmStartBtn.addEventListener('click', () => {
        hideModal();
        saveAndStartTraining();
    });
}

// 创建场景会话
async function createSceneSession() {
    if (isSessionInitialized) return;  // 防止重复调用
    isSessionInitialized = true;
    
    try {
        const response = await fetch('/api/scene/create', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            addMessage('ai', data.response);
            updateOptions(data.options);
        } else {
            addMessage('ai', '初始化失败，请刷新页面重试。');
        }
    } catch (error) {
        console.error('创建会话失败:', error);
        addMessage('ai', '连接服务器失败，请刷新页面重试。');
    }
}

// 发送消息
async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;
    
    // 添加用户消息
    addMessage('user', message);
    userInput.value = '';
    
    // 禁用输入
    setInputEnabled(false);
    
    try {
        const response = await fetch('/api/scene/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });
        
        const data = await response.json();
        
        if (data.success) {
            addMessage('ai', data.response);
            updateOptions(data.options);
            updateStatus(data.state);
            
            // ✅ 检查对话是否已结束
            if (data.conversation_ended) {
                // 禁用输入框，提示用户点击按钮
                userInput.disabled = true;
                userInput.placeholder = '场景已创建完成，请点击下方按钮开始对练';
                sendBtn.disabled = true;
            }
        } else {
            addMessage('ai', '对话失败：' + data.error);
        }
    } catch (error) {
        console.error('发送消息失败:', error);
        addMessage('ai', '发送消息失败，请重试。');
    } finally {
        setInputEnabled(true);
    }
}

// 简单的 Markdown 渲染
function renderMarkdown(text) {
    if (!text) return '';
    
    let html = text;
    
    // 转义 HTML 特殊字符
    html = html.replace(/&/g, '&amp;')
               .replace(/</g, '&lt;')
               .replace(/>/g, '&gt;');
    
    // 标题 (h1-h4)
    html = html.replace(/^#### (.*$)/gim, '<h4>$1</h4>');
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
    
    // 粗体
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/__(.*?)__/g, '<strong>$1</strong>');
    
    // 斜体
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    html = html.replace(/_(.*?)_/g, '<em>$1</em>');
    
    // 引用
    html = html.replace(/^> (.*$)/gim, '<blockquote>$1</blockquote>');
    
    // 列表项
    html = html.replace(/^\s*[-*+]\s+(.*$)/gim, '<li>$1</li>');
    html = html.replace(/^\s*\d+\.\s+(.*$)/gim, '<li>$1</li>');
    
    // 段落 - 将双换行转换为段落标签
    html = html.replace(/\n\n/g, '</p><p>');
    html = '<p>' + html + '</p>';
    
    // 清理空的段落标签
    html = html.replace(/<p>\s*<\/p>/g, '');
    html = html.replace(/<p>\s*(<h[1-4]>)/g, '$1');
    html = html.replace(/(<\/h[1-4]>)\s*<\/p>/g, '$1');
    html = html.replace(/<p>\s*(<blockquote>)/g, '$1');
    html = html.replace(/(<\/blockquote>)\s*<\/p>/g, '$1');
    
    // 换行 - 将单个换行转换为<br>
    html = html.replace(/\n/g, '<br>');
    
    return html;
}

// 添加消息到聊天
function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // 根据角色决定是否渲染 Markdown
    if (role === 'ai') {
        contentDiv.innerHTML = renderMarkdown(content);
    } else {
        contentDiv.textContent = content;
    }
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // 滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 更新选项按钮
function updateOptions(options) {
    // 暂时不实现选项按钮，使用自由输入
}

// 更新状态面板
function updateStatus(state) {
    if (!state) return;
    
    // 更新行业状态
    const industryEl = document.getElementById('status-industry');
    const industryValue = document.getElementById('industry-value');
    if (state.industry) {
        industryEl.classList.add('completed');
        industryEl.classList.remove('in-progress');
        industryValue.textContent = state.industry;
    } else if (state.collected_info?.industry) {
        industryEl.classList.add('in-progress');
    }
    
    // 更新用户角色状态
    const roleEl = document.getElementById('status-role');
    const roleValue = document.getElementById('role-value');
    if (state.role_type) {
        roleEl.classList.add('completed');
        roleEl.classList.remove('in-progress');
        roleValue.textContent = state.role_type;
    }
    
    // 更新 AI 角色状态
    const aiRoleEl = document.getElementById('status-ai-role');
    const aiRoleValue = document.getElementById('ai-role-value');
    if (state.ai_role) {
        aiRoleEl.classList.add('completed');
        aiRoleEl.classList.remove('in-progress');
        aiRoleValue.textContent = state.ai_role;
    } else if (state.collected_info?.ai_role) {
        aiRoleEl.classList.add('in-progress');
    }
    
    // 更新背景信息状态
    const extendedEl = document.getElementById('status-extended');
    const extendedValue = document.getElementById('extended-value');
    if (state.extended_info_sufficient) {
        extendedEl.classList.add('completed');
        extendedEl.classList.remove('in-progress');
        extendedValue.textContent = '已收集足够信息';
    } else {
        const count = Object.keys(state.extended_info || {}).length;
        extendedValue.textContent = `${count} 项信息`;
        if (count > 0) {
            extendedEl.classList.add('in-progress');
        }
    }
}

// 显示操作栏
// ✅ 移除 showActionBar 函数，按钮始终显示
// function showActionBar() {
//     actionBar.style.display = 'block';
// }

// 显示生成进度
function showProgress(show) {
    if (show) {
        progressSection.style.display = 'block';
        progressFill.style.width = '0%';
        progressText.textContent = '正在分析场景信息...';
    } else {
        progressSection.style.display = 'none';
    }
}

// 更新进度
function updateProgress(percent, text) {
    progressFill.style.width = `${percent}%`;
    progressText.textContent = text;
}

// 查看生成的内容 (不保存，只预览)
async function showGeneratedContent() {
    try {
        // 先显示加载状态
        viewBtn.disabled = true;
        viewBtn.textContent = '生成中...';
        
        const response = await fetch('/api/scene/generate', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentSceneId = data.scene_id;
            generatedSceneContent = data.scene_content;
            
            // 显示模态框
            displayContent(generatedSceneContent);
            showModal();
        } else {
            showToast('生成失败：' + data.error, 'error');
        }
    } catch (error) {
        console.error('生成内容失败:', error);
        showToast('生成失败，请重试。', 'error');
    } finally {
        viewBtn.disabled = false;
        viewBtn.textContent = '查看生成的内容';
    }
}

// Toast 提示（使用首页样式）
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: ${type === 'error' ? '#f44336' : '#4caf50'};
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 9999;
        animation: slideDown 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideUp 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// 显示内容
function displayContent(content) {
    if (!content) return;
    
    let html = '';
    
    // 背景信息
    if (content.background_info) {
        html += '<h3>📍 场景背景</h3>';
        html += `<p>${content.background_info.replace(/\n/g, '<br>')}</p>`;
    }
    
    // 主问题列表
    if (content.main_questions && content.main_questions.length > 0) {
        html += '<h3>❓ 主问题列表</h3>';
        html += '<ol>';
        content.main_questions.forEach(q => {
            html += `<li>${q.question}</li>`;
        });
        html += '</ol>';
    }
    
    // 关联问题分组
    if (content.trigger_groups && content.trigger_groups.length > 0) {
        html += '<h3>🔗 关联问题分组</h3>';
        content.trigger_groups.forEach(group => {
            html += `<h4>${group.group_name}</h4>`;
            html += `<p><strong>触发关键词:</strong> ${group.trigger_keywords.join(', ')}</p>`;
            html += '<ul>';
            group.questions.forEach(q => {
                html += `<li>${q.question}</li>`;
            });
            html += '</ul>';
        });
    }
    
    // 考核维度
    if (content.dimensions && content.dimensions.length > 0) {
        html += '<h3>📊 考核维度</h3>';
        content.dimensions.forEach(dim => {
            html += `<h4>${dim.dimension_name} (权重：${(dim.weight * 100).toFixed(0)}%)</h4>`;
            html += '<ul>';
            for (const [criterion, desc] of Object.entries(dim.sub_criteria || {})) {
                html += `<li><strong>${criterion}:</strong> ${desc}</li>`;
            }
            html += '</ul>';
        });
    }
    
    // 情绪画像
    if (content.emotion_profile) {
        html += '<h3>😊 情绪画像</h3>';
        html += `<p><strong>情绪类型:</strong> ${content.emotion_profile.emotion_type}</p>`;
        html += `<p><strong>情绪描述:</strong> ${content.emotion_profile.emotion_description}</p>`;
        html += `<p><strong>说话风格:</strong> ${content.emotion_profile.speaking_style}</p>`;
        html += `<p><strong>沟通态度:</strong> ${content.emotion_profile.attitude}</p>`;
    }
    
    modalBody.innerHTML = html;
}

// 保存并开始对练
async function saveAndStartTraining() {
    try {
        // 禁用按钮，防止重复点击
        startBtn.disabled = true;
        startBtn.textContent = '保存中...';
        
        if (!currentSceneId) {
            // 如果还没有生成，先调用生成接口保存场景
            const response = await fetch('/api/scene/generate', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                currentSceneId = data.scene_id;
                generatedSceneContent = data.scene_content;
                console.log('场景保存成功:', currentSceneId);
                
                // 显示成功提示
                showToast('场景保存成功！正在跳转到对练页面...', 'success');
                
                // 延迟跳转，让用户看到提示
                setTimeout(() => {
                    window.location.href = `/realtime/${currentSceneId}`;
                }, 1000);
            } else {
                showToast('保存失败：' + data.error, 'error');
                startBtn.disabled = false;
                startBtn.textContent = '开始对练';
                return;
            }
        } else {
            // 已经生成过了，直接跳转
            showToast('正在跳转到对练页面...', 'success');
            setTimeout(() => {
                window.location.href = `/realtime/${currentSceneId}`;
            }, 500);
        }
    } catch (error) {
        console.error('保存场景失败:', error);
        showToast('保存失败，请重试', 'error');
        startBtn.disabled = false;
        startBtn.textContent = '开始对练';
    }
}

// 模态框控制
function showModal() {
    modal.classList.add('show');
}

function hideModal() {
    modal.classList.remove('show');
}

// 启用/禁用输入
function setInputEnabled(enabled) {
    userInput.disabled = !enabled;
    sendBtn.disabled = !enabled;
    if (enabled) {
        userInput.focus();
    }
}

// 点击模态框外部关闭
modal.addEventListener('click', (e) => {
    if (e.target === modal) {
        hideModal();
    }
});
