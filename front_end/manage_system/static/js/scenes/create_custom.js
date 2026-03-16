// 自定义场景创建页面 JavaScript

// 表单数据
const formData = {
    sceneDescription: '',
    aiRole: '',
    userRole: ''
};

// DOM 元素
let sceneDescriptionInput;
let aiRoleInput;
let userRoleInput;
let btnNextStep;
let loadingOverlay;

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initElements();
    initEventListeners();
    updateCharCount();
});

// 初始化DOM元素
function initElements() {
    sceneDescriptionInput = document.getElementById('sceneDescription');
    aiRoleInput = document.getElementById('aiRole');
    userRoleInput = document.getElementById('userRole');
    btnNextStep = document.getElementById('btnNextStep');
    loadingOverlay = document.getElementById('loadingOverlay');
}

// 初始化事件监听
function initEventListeners() {
    // 场景描述输入
    sceneDescriptionInput.addEventListener('input', function() {
        formData.sceneDescription = this.value;
        updateCharCount();
        validateForm();
    });

    // AI角色输入
    aiRoleInput.addEventListener('input', function() {
        formData.aiRole = this.value;
        validateForm();
        // 取消快捷标签选中
        document.querySelectorAll('#aiRoleTags .quick-tag').forEach(tag => {
            tag.classList.remove('selected');
        });
    });

    // 用户角色输入
    userRoleInput.addEventListener('input', function() {
        formData.userRole = this.value;
        validateForm();
        // 取消快捷标签选中
        document.querySelectorAll('#userRoleTags .quick-tag').forEach(tag => {
            tag.classList.remove('selected');
        });
    });

    // AI角色快捷标签
    document.querySelectorAll('#aiRoleTags .quick-tag').forEach(tag => {
        tag.addEventListener('click', function() {
            const role = this.getAttribute('data-role');
            aiRoleInput.value = role;
            formData.aiRole = role;
            
            // 切换选中状态
            document.querySelectorAll('#aiRoleTags .quick-tag').forEach(t => {
                t.classList.remove('selected');
            });
            this.classList.add('selected');
            
            validateForm();
        });
    });

    // 用户角色快捷标签
    document.querySelectorAll('#userRoleTags .quick-tag').forEach(tag => {
        tag.addEventListener('click', function() {
            const role = this.getAttribute('data-role');
            userRoleInput.value = role;
            formData.userRole = role;
            
            // 切换选中状态
            document.querySelectorAll('#userRoleTags .quick-tag').forEach(t => {
                t.classList.remove('selected');
            });
            this.classList.add('selected');
            
            validateForm();
        });
    });

    // 下一步按钮
    btnNextStep.addEventListener('click', handleNextStep);
}

// 更新字符计数
function updateCharCount() {
    const length = sceneDescriptionInput.value.length;
    const hint = sceneDescriptionInput.parentElement.querySelector('.form-hint');
    if (hint) {
        hint.textContent = `💡 包含行业、场景、目标等信息，${length}/500字`;
    }
}

// 表单验证
function validateForm() {
    const isValid = formData.sceneDescription.trim() && 
                    formData.aiRole.trim() && 
                    formData.userRole.trim();
    
    btnNextStep.disabled = !isValid;
    return isValid;
}

// 处理下一步
async function handleNextStep() {
    if (!validateForm()) {
        showToast('请填写所有必填项', 'error');
        return;
    }

    // 显示loading
    showLoading();

    try {
        // 调用AI生成接口
        const response = await fetch('/api/scene/generate-custom', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                scene_description: formData.sceneDescription,
                ai_role: formData.aiRole,
                user_role: formData.userRole
            })
        });

        const result = await response.json();

        if (result.success) {
            // 生成成功，跳转到配置页面
            const data = result.data;
            
            // 将数据编码后传递给配置页面
            const encodedData = encodeURIComponent(JSON.stringify(data));
            
            // 延迟跳转，让用户看到完成状态
            setTimeout(() => {
                window.location.href = `/manage_system/scene-config?mode=custom&data=${encodedData}`;
            }, 1000);
        } else {
            hideLoading();
            showToast(result.error || 'AI生成失败，请重试', 'error');
        }
    } catch (error) {
        console.error('生成场景失败:', error);
        hideLoading();
        showToast('网络错误，请重试', 'error');
    }
}

// 显示Loading
function showLoading() {
    loadingOverlay.classList.add('show');
    
    // 模拟进度更新
    let progress = 0;
    const progressBar = document.getElementById('loadingProgressBar');
    
    const steps = [
        { id: 'loadingStep1', delay: 0, progress: 20 },
        { id: 'loadingStep2', delay: 800, progress: 40 },
        { id: 'loadingStep3', delay: 1600, progress: 60 },
        { id: 'loadingStep4', delay: 2400, progress: 80 },
        { id: 'loadingStep5', delay: 3200, progress: 100 }
    ];

    steps.forEach(step => {
        setTimeout(() => {
            // 更新步骤状态
            const stepEl = document.getElementById(step.id);
            if (stepEl) {
                stepEl.classList.remove('active');
                stepEl.classList.add('completed');
                stepEl.querySelector('span:first-child').textContent = '✓';
            }
            
            // 更新下一个步骤
            const nextStepIndex = steps.findIndex(s => s.id === step.id) + 1;
            if (nextStepIndex < steps.length) {
                const nextStepEl = document.getElementById(steps[nextStepIndex].id);
                if (nextStepEl) {
                    nextStepEl.classList.add('active');
                }
            }
            
            // 更新进度条
            progressBar.style.width = step.progress + '%';
        }, step.delay);
    });
}

// 隐藏Loading
function hideLoading() {
    loadingOverlay.classList.remove('show');
    
    // 重置进度
    document.getElementById('loadingProgressBar').style.width = '0%';
    
    // 重置步骤状态
    document.querySelectorAll('.loading-step').forEach((step, index) => {
        step.classList.remove('active', 'completed');
        if (index === 0) {
            step.classList.add('completed');
            step.querySelector('span:first-child').textContent = '✓';
        } else {
            step.querySelector('span:first-child').textContent = '○';
        }
    });
}

// Toast 提示
function showToast(message, type = 'info') {
    // 创建toast元素
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'error' ? '#ef4444' : '#10b981'};
        color: white;
        padding: 16px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 10000;
        animation: slideInRight 0.3s ease;
        max-width: 400px;
    `;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // 3秒后移除
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// 添加CSS动画
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
