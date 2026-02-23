const state = {
    currentStep: 'position',
    position: '',
    industry: '',
    product: '',
    personality: '',
    interestLevel: '',
    backgroundInfo: ''
};

const stepOrder = ['position', 'industry', 'product', 'personality', 'interest_level', 'background'];

function init() {
    fetch('/api/interactive/init')
        .then(res => res.json())
        .then(data => {
            addMessage(data.message, 'ai');
            renderOptions(data.options.position);
            updateStepIndicator();
        })
        .catch(err => {
            console.error('Init error:', err);
            showToast('初始化失败');
        });
}

function renderOptions(options) {
    const container = document.getElementById('optionContainer');
    container.innerHTML = '';
    
    options.forEach(option => {
        const btn = document.createElement('button');
        btn.className = 'option-btn';
        btn.textContent = option;
        btn.onclick = () => selectOption(option);
        container.appendChild(btn);
    });
    
    document.getElementById('otherInput').classList.remove('show');
}

function selectOption(option) {
    const buttons = document.querySelectorAll('.option-btn');
    buttons.forEach(btn => btn.classList.remove('selected'));
    event.target.classList.add('selected');

    if (option === '其他') {
        showOtherInput();
        return;
    }

    processSelection(option);
}

function showOtherInput() {
    const otherInput = document.getElementById('otherInput');
    otherInput.classList.add('show');
    document.getElementById('otherInputField').focus();
}

function hideOtherInput() {
    const otherInput = document.getElementById('otherInput');
    otherInput.classList.remove('show');
    document.getElementById('otherInputField').value = '';
}

document.getElementById('otherSubmitBtn').onclick = () => {
    const value = document.getElementById('otherInputField').value.trim();
    if (value) {
        processInput(value);
        hideOtherInput();
    }
};

document.getElementById('otherInputField').onkeypress = (e) => {
    if (e.key === 'Enter') {
        document.getElementById('otherSubmitBtn').click();
    }
};

function processSelection(option) {
    addMessage(option, 'user');
    
    fetch('/api/interactive/select', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ step: state.currentStep, value: option })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            updateState(state.currentStep, option);
            
            if (data.show_input) {
                showOtherInput();
            } else if (data.show_background) {
                showBackgroundSection();
            } else {
                state.currentStep = data.next_step;
                setTimeout(() => {
                    addMessage(data.message, 'ai');
                    if (data.options) {
                        renderOptions(data.options);
                    }
                    updateStepIndicator();
                }, 300);
            }
        } else {
            showToast('错误: ' + data.error);
        }
    })
    .catch(err => {
        console.error('Select error:', err);
        showToast('请求失败');
    });
}

function processInput(value) {
    addMessage(value, 'user');
    
    fetch('/api/interactive/input', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ step: state.currentStep + '_input', value: value })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            if (state.currentStep === 'industry') {
                state.industry = value;
            } else if (state.currentStep === 'product') {
                state.product = value;
            }
            
            state.currentStep = data.next_step;
            setTimeout(() => {
                addMessage(data.message, 'ai');
                if (data.options) {
                    renderOptions(data.options);
                }
                updateStepIndicator();
            }, 300);
        } else {
            showToast('错误: ' + data.error);
        }
    })
    .catch(err => {
        console.error('Input error:', err);
        showToast('请求失败');
    });
}

function showBackgroundSection() {
    document.getElementById('interactiveArea').style.display = 'none';
    document.getElementById('backgroundSection').style.display = 'block';
    state.currentStep = 'background';
    updateStepIndicator();
}

function updateState(step, value) {
    switch (step) {
        case 'position':
            state.position = value;
            updateStateDisplay('statePosition', value);
            break;
        case 'industry':
            state.industry = value;
            updateStateDisplay('stateIndustry', value);
            break;
        case 'product':
            state.product = value;
            updateStateDisplay('stateProduct', value);
            break;
        case 'personality':
            state.personality = value;
            updateStateDisplay('statePersonality', value);
            break;
        case 'interest_level':
            state.interestLevel = value;
            updateStateDisplay('stateInterest', value);
            break;
    }
}

function updateStateDisplay(elementId, value) {
    const element = document.querySelector(`#${elementId} .state-value`);
    element.textContent = value;
    element.style.color = '#667eea';
}

function updateStepIndicator() {
    const circles = document.querySelectorAll('.step-circle');
    const lines = document.querySelectorAll('.step-line');
    
    const currentIndex = stepOrder.indexOf(state.currentStep);
    
    circles.forEach((circle, index) => {
        circle.classList.remove('active', 'completed');
        if (index < currentIndex) {
            circle.classList.add('completed');
        } else if (index === currentIndex) {
            circle.classList.add('active');
        }
    });

    lines.forEach((line, index) => {
        line.classList.toggle('completed', index < currentIndex);
    });
}

function addMessage(text, role) {
    const messagesDiv = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role === 'user' ? 'user-message' : 'ai-message'}`;
    
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.textContent = text;
    
    messageDiv.appendChild(textDiv);
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

document.getElementById('autoGenerateBtn').onclick = async () => {
    document.getElementById('loadingArea').classList.add('show');
    
    try {
        const response = await fetch('/api/interactive/generate-background', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(state)
        });
        
        const data = await response.json();
        if (data.success) {
            document.getElementById('backgroundInput').value = data.background;
        } else {
            showToast('生成失败：' + data.error);
        }
    } catch (error) {
        showToast('请求失败：' + error.message);
    } finally {
        document.getElementById('loadingArea').classList.remove('show');
    }
};

document.getElementById('confirmBackgroundBtn').onclick = async () => {
    state.backgroundInfo = document.getElementById('backgroundInput').value;
    
    document.getElementById('loadingArea').classList.add('show');
    
    try {
        const response = await fetch('/api/interactive/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(state)
        });
        
        const data = await response.json();
        if (data.success) {
            document.getElementById('promptResult').textContent = data.prompt;
            document.getElementById('resultModal').style.display = 'flex';
        } else {
            showToast('生成失败：' + data.error);
        }
    } catch (error) {
        showToast('请求失败：' + error.message);
    } finally {
        document.getElementById('loadingArea').classList.remove('show');
    }
};

document.getElementById('closeModal').onclick = () => {
    document.getElementById('resultModal').style.display = 'none';
};

document.getElementById('copyBtn').onclick = () => {
    const text = document.getElementById('promptResult').textContent;
    navigator.clipboard.writeText(text).then(() => {
        showToast('已复制到剪贴板');
    });
};

document.getElementById('saveBtn').onclick = async () => {
    const name = document.getElementById('promptName').value.trim();
    if (!name) {
        showToast('请输入场景名称');
        return;
    }
    
    const prompt = document.getElementById('promptResult').textContent;
    
    try {
        const response = await fetch('/api/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, prompt })
        });
        
        const data = await response.json();
        if (data.success) {
            showToast('保存成功');
            document.getElementById('startRealtimeBtn').onclick = () => {
                window.location.href = `/realtime/${data.scene_id}`;
            };
        } else {
            showToast('保存失败：' + data.error);
        }
    } catch (error) {
        showToast('请求失败：' + error.message);
    }
};

document.getElementById('startRealtimeBtn').onclick = () => {
    const prompt = document.getElementById('promptResult').textContent;
    const name = document.getElementById('promptName').value || '未命名场景';
    
    localStorage.setItem('scenePrompt', prompt);
    localStorage.setItem('sceneName', name);
    
    window.location.href = '/realtime';
};

function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

document.addEventListener('DOMContentLoaded', init);
