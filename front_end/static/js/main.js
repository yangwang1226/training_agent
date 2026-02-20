document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chatMessages');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const generateBtn = document.getElementById('generateBtn');
    const resetBtn = document.getElementById('resetBtn');
    const resultModal = document.getElementById('resultModal');
    const closeModal = document.getElementById('closeModal');
    const copyBtn = document.getElementById('copyBtn');
    const promptResult = document.getElementById('promptResult');

    let isReady = false;

    function addMessage(content, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'assistant-message'}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = isUser ? '我' : 'AI';
        
        const text = document.createElement('div');
        text.className = 'message-text';
        text.textContent = content;
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(text);
        chatMessages.appendChild(messageDiv);
        
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function addLoadingMessage() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant-message loading';
        messageDiv.id = 'loadingMessage';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = 'AI';
        
        const text = document.createElement('div');
        text.className = 'message-text';
        text.innerHTML = '<span class="loading-dots">正在思考...</span>';
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(text);
        chatMessages.appendChild(messageDiv);
        
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function removeLoadingMessage() {
        const loadingMessage = document.getElementById('loadingMessage');
        if (loadingMessage) {
            loadingMessage.remove();
        }
    }

    function updateState(state) {
        const industryEl = document.querySelector('#stateIndustry .state-value');
        const roleEl = document.querySelector('#stateRole .state-value');
        const intentEl = document.querySelector('#stateIntent .state-value');
        const questionsEl = document.querySelector('#stateQuestions .state-value');

        industryEl.textContent = state.industry || '未收集';
        industryEl.className = `state-value ${state.collected_info.industry ? 'collected' : ''}`;

        roleEl.textContent = state.role_type || '未收集';
        roleEl.className = `state-value ${state.collected_info.role ? 'collected' : ''}`;

        intentEl.textContent = state.purchase_intent || '未收集';
        intentEl.className = `state-value ${state.collected_info.intent ? 'collected' : ''}`;

        if (state.custom_questions && state.custom_questions.length > 0) {
            questionsEl.textContent = state.custom_questions.join(', ');
            questionsEl.className = 'state-value collected';
        } else {
            questionsEl.textContent = '自动生成';
            questionsEl.className = `state-value ${state.collected_info.questions ? 'collected' : ''}`;
        }

        updateExtendedInfo(state);
    }

    function updateExtendedInfo(state) {
        const extendedStatusEl = document.getElementById('extendedStatus');
        const extendedInfoListEl = document.getElementById('extendedInfoList');
        
        const basicInfoComplete = state.collected_info.industry && 
                                   state.collected_info.role && 
                                   state.collected_info.intent && 
                                   state.collected_info.questions;
        
        if (!basicInfoComplete) {
            extendedStatusEl.textContent = '';
            extendedStatusEl.className = 'extended-status';
            extendedInfoListEl.innerHTML = '<p class="no-extended-info">基础信息收集完成后，将根据行业特点收集延展信息</p>';
            return;
        }
        
        if (state.extended_info_sufficient) {
            extendedStatusEl.textContent = '✓ 已完成';
            extendedStatusEl.className = 'extended-status completed';
        } else {
            extendedStatusEl.textContent = '收集中...';
            extendedStatusEl.className = 'extended-status collecting';
        }
        
        if (state.extended_info && Object.keys(state.extended_info).length > 0) {
            let html = '';
            for (const [key, value] of Object.entries(state.extended_info)) {
                html += `<div class="extended-item">
                    <span class="extended-label">${key}：</span>
                    <span class="extended-value">${value}</span>
                </div>`;
            }
            extendedInfoListEl.innerHTML = html;
        } else {
            extendedInfoListEl.innerHTML = '<p class="no-extended-info">正在收集延展信息...</p>';
        }
    }

    async function sendMessage(message) {
        if (!message.trim()) return;

        addMessage(message, true);
        userInput.value = '';
        userInput.disabled = true;
        sendBtn.disabled = true;

        addLoadingMessage();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();
            
            removeLoadingMessage();
            addMessage(data.response);
            
            isReady = data.is_ready;
            generateBtn.disabled = !isReady;
            
            updateState(data.state);

        } catch (error) {
            removeLoadingMessage();
            addMessage('抱歉，发生了错误，请重试。');
            console.error('Error:', error);
        }

        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.focus();
    }

    async function generatePrompt() {
        generateBtn.disabled = true;
        generateBtn.textContent = '生成中...';
        userInput.disabled = true;
        sendBtn.disabled = true;

        addMessage('正在生成提示词，请稍候（可能需要10-30秒）...', false);

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 120000);
            
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);

            const data = await response.json();

            const lastMessage = chatMessages.lastElementChild;
            if (lastMessage && lastMessage.classList.contains('assistant-message')) {
                lastMessage.remove();
            }

            if (data.success) {
                promptResult.textContent = data.full_prompt;
                resultModal.style.display = 'flex';
            } else {
                addMessage('生成失败: ' + (data.error || '未知错误'));
            }

        } catch (error) {
            const lastMessage = chatMessages.lastElementChild;
            if (lastMessage && lastMessage.classList.contains('assistant-message')) {
                lastMessage.remove();
            }
            
            if (error.name === 'AbortError') {
                addMessage('生成超时，请重试。');
            } else {
                addMessage('生成失败，请重试。');
            }
            console.error('Error:', error);
        }

        generateBtn.textContent = '开始生成';
        generateBtn.disabled = false;
        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.focus();
    }

    async function resetConversation() {
        userInput.disabled = true;
        sendBtn.disabled = true;
        generateBtn.disabled = true;

        chatMessages.innerHTML = '';
        addLoadingMessage();

        try {
            const response = await fetch('/api/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();
            
            removeLoadingMessage();
            addMessage(data.response);
            
            isReady = data.is_ready;
            updateState(data.state);

        } catch (error) {
            removeLoadingMessage();
            addMessage('重置失败，请刷新页面。');
            console.error('Error:', error);
        }

        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.focus();
    }

    async function initConversation() {
        addLoadingMessage();

        try {
            const response = await fetch('/api/init');
            const data = await response.json();
            
            removeLoadingMessage();
            addMessage(data.response);
            
            isReady = data.is_ready;
            updateState(data.state);

        } catch (error) {
            removeLoadingMessage();
            addMessage('初始化失败，请刷新页面。');
            console.error('Error:', error);
        }

        userInput.focus();
    }

    sendBtn.addEventListener('click', () => {
        sendMessage(userInput.value);
    });

    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage(userInput.value);
        }
    });

    generateBtn.addEventListener('click', generatePrompt);
    resetBtn.addEventListener('click', resetConversation);

    closeModal.addEventListener('click', () => {
        resultModal.style.display = 'none';
    });

    resultModal.addEventListener('click', (e) => {
        if (e.target === resultModal) {
            resultModal.style.display = 'none';
        }
    });

    copyBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(promptResult.textContent).then(() => {
            copyBtn.textContent = '已复制!';
            setTimeout(() => {
                copyBtn.textContent = '复制到剪贴板';
            }, 2000);
        });
    });

    initConversation();
});
