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
    const promptName = document.getElementById('promptName');
    const saveBtn = document.getElementById('saveBtn');
    const toast = document.getElementById('toast');
    const startRealtimeBtn = document.getElementById('startRealtimeBtn');

    let currentPrompt = '';
    let currentSceneId = '';

    function addMessage(content, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'assistant-message'}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = isUser ? '我' : 'AI';
        
        const text = document.createElement('div');
        text.className = 'message-text';
        
        if (!isUser) {
            text.innerHTML = formatMessage(content);
        } else {
            text.textContent = content;
        }
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(text);
        chatMessages.appendChild(messageDiv);
        
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function formatMessage(content) {
        let formatted = content;
        
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        const lines = formatted.split('\n');
        let result = [];
        let inList = false;
        let listItems = [];
        
        for (let line of lines) {
            const numberedMatch = line.match(/^(\d+)[.、．]\s*(.*)$/);
            const bulletMatch = line.match(/^[-•·]\s*(.*)$/);
            
            if (numberedMatch) {
                if (!inList) {
                    inList = true;
                    listItems = [];
                }
                listItems.push(`<li class="numbered-item"><span class="item-number">${numberedMatch[1]}.</span> ${formatInline(numberedMatch[2])}</li>`);
            } else if (bulletMatch) {
                if (!inList) {
                    inList = true;
                    listItems = [];
                }
                listItems.push(`<li class="bullet-item">• ${formatInline(bulletMatch[1])}</li>`);
            } else {
                if (inList && listItems.length > 0) {
                    result.push('<ul class="formatted-list">' + listItems.join('') + '</ul>');
                    listItems = [];
                    inList = false;
                }
                if (line.trim()) {
                    result.push(`<p>${formatInline(line)}</p>`);
                }
            }
        }
        
        if (inList && listItems.length > 0) {
            result.push('<ul class="formatted-list">' + listItems.join('') + '</ul>');
        }
        
        return result.join('');
    }

    function formatInline(text) {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
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
            
            // 显示选项按钮
            if (data.options && data.options.length > 0) {
                showOptions(data.options, data.multi_select);
            }
            
            // 显示维度确认面板
            if (data.show_dimensions && data.dimensions) {
                showDimensionsPanel(data.dimensions);
            }
            
            // 维度确认后显示生成按钮
            if (data.dimensions_confirmed) {
                document.getElementById('actionButtons').style.display = 'flex';
            }
            
            // 检测信息收集完成的消息，显示生成按钮
            if (data.response && (data.response.includes('开始生成') || data.response.includes('信息已收集完成'))) {
                document.getElementById('actionButtons').style.display = 'flex';
            }

        } catch (error) {
            removeLoadingMessage();
            addMessage('抱歉，发生了错误，请重试。');
            console.error('Error:', error);
        }

        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.focus();
    }

    function showDimensionsPanel(dimensions) {
        const panel = document.createElement('div');
        panel.className = 'dimensions-panel';
        panel.id = 'dimensionsPanel';
        
        let html = '<h4>考核维度确认</h4><div class="dimensions-list">';
        for (let i = 0; i < dimensions.length; i++) {
            const dim = dimensions[i];
            html += `<div class="dimension-item">
                <div class="dimension-name">${i + 1}. ${dim.dimension_name}</div>
                <div class="dimension-weight">权重: ${(dim.weight * 100).toFixed(0)}%</div>
                <div class="dimension-criteria">`;
            for (const [key, value] of Object.entries(dim.sub_criteria || {})) {
                html += `<div class="criterion"><span class="criterion-key">${key}:</span> ${value}</div>`;
            }
            html += '</div></div>';
        }
        html += '</div>';
        
        panel.innerHTML = html;
        
        const buttonsDiv = document.createElement('div');
        buttonsDiv.className = 'dimensions-buttons';
        
        const confirmBtn = document.createElement('button');
        confirmBtn.className = 'btn btn-success';
        confirmBtn.textContent = '确认维度';
        confirmBtn.onclick = () => {
            sendMessage('确认，继续');
            panel.remove();
        };
        
        const regenerateBtn = document.createElement('button');
        regenerateBtn.className = 'btn btn-warning';
        regenerateBtn.textContent = '重新生成';
        regenerateBtn.onclick = () => {
            sendMessage('重新生成');
            panel.remove();
        };
        
        buttonsDiv.appendChild(confirmBtn);
        buttonsDiv.appendChild(regenerateBtn);
        panel.appendChild(buttonsDiv);
        
        chatMessages.appendChild(panel);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    let progressWebSocket = null;
    let progressMessageElement = null;

    function connectProgressWebSocket() {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/api/progress/ws`;
        
        progressWebSocket = new WebSocket(wsUrl);
        
        progressWebSocket.onopen = () => {
            console.log('Progress WebSocket connected');
        };
        
        progressWebSocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'progress') {
                    updateProgressMessage(data.message, data.step);
                }
            } catch (error) {
                console.error('Error parsing progress message:', error);
            }
        };
        
        progressWebSocket.onclose = () => {
            console.log('Progress WebSocket closed');
        };
        
        progressWebSocket.onerror = (error) => {
            console.error('Progress WebSocket error:', error);
        };
    }

    function updateProgressMessage(message, step) {
        if (!progressMessageElement) {
            progressMessageElement = document.createElement('div');
            progressMessageElement.className = 'assistant-message';
            progressMessageElement.style.opacity = '0.8';
            progressMessageElement.innerHTML = `
                <div class="message-content">
                    <div class="progress-indicator">
                        <div class="progress-bar" style="width: ${step}%"></div>
                    </div>
                    <p>${message}</p>
                </div>
            `;
            chatMessages.appendChild(progressMessageElement);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        } else {
            progressMessageElement.innerHTML = `
                <div class="message-content">
                    <div class="progress-indicator">
                        <div class="progress-bar" style="width: ${step}%"></div>
                    </div>
                    <p>${message}</p>
                </div>
            `;
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    function clearProgressMessage() {
        if (progressMessageElement) {
            progressMessageElement.remove();
            progressMessageElement = null;
        }
    }

    async function generatePrompt() {
        generateBtn.disabled = true;
        generateBtn.textContent = '生成中...';
        userInput.disabled = true;
        sendBtn.disabled = true;

        // 确保WebSocket连接
        if (!progressWebSocket || progressWebSocket.readyState !== WebSocket.OPEN) {
            connectProgressWebSocket();
        }

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

            clearProgressMessage();

            if (data.success) {
                currentPrompt = data.full_prompt;
                promptResult.textContent = data.full_prompt;
                promptName.value = '';
                resultModal.style.display = 'flex';
            } else {
                addMessage('生成失败: ' + (data.error || '未知错误'));
            }

        } catch (error) {
            clearProgressMessage();
            
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

    // 页面加载时连接WebSocket
    window.addEventListener('load', connectProgressWebSocket);

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
            
            // 显示选项按钮
            if (data.options && data.options.length > 0) {
                showOptions(data.options);
            }

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
            
            // 显示选项按钮
            if (data.options && data.options.length > 0) {
                showOptions(data.options);
            }

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

    function showToast(message, type = 'success') {
        toast.textContent = message;
        toast.className = `toast show ${type}`;
        setTimeout(() => {
            toast.className = 'toast';
        }, 3000);
    }

    function showOptions(options, multiSelect = false) {
        const optionsContainer = document.createElement('div');
        optionsContainer.className = 'options-container';
        
        if (multiSelect) {
            // 多选模式
            const selectedOptions = [];
            
            options.forEach(option => {
                const button = document.createElement('button');
                button.className = 'option-button';
                button.textContent = option;
                button.onclick = () => {
                    button.classList.toggle('selected');
                    if (selectedOptions.includes(option)) {
                        selectedOptions.splice(selectedOptions.indexOf(option), 1);
                    } else {
                        selectedOptions.push(option);
                    }
                };
                optionsContainer.appendChild(button);
            });
            
            // 添加确认按钮
            const confirmBtn = document.createElement('button');
            confirmBtn.className = 'btn btn-success';
            confirmBtn.textContent = '确认选择';
            confirmBtn.style.marginTop = '10px';
            confirmBtn.onclick = () => {
                if (selectedOptions.length === 0) {
                    showToast('请至少选择一个选项', 'error');
                    return;
                }
                sendMessage(selectedOptions.join(', '));
                optionsContainer.remove();
            };
            optionsContainer.appendChild(confirmBtn);
        } else {
            // 单选模式
            options.forEach(option => {
                const button = document.createElement('button');
                button.className = 'option-button';
                button.textContent = option;
                button.onclick = () => {
                    sendMessage(option);
                    optionsContainer.remove();
                };
                optionsContainer.appendChild(button);
            });
        }
        
        chatMessages.appendChild(optionsContainer);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function savePrompt() {
        const name = promptName.value.trim();
        
        if (!name) {
            showToast('请输入场景名称', 'error');
            return;
        }
        
        if (!currentPrompt) {
            showToast('没有可保存的提示词', 'error');
            return;
        }

        saveBtn.disabled = true;
        saveBtn.textContent = '保存中...';

        try {
            const response = await fetch('/api/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    name: name,
                    prompt: currentPrompt 
                })
            });

            const data = await response.json();

            if (data.success) {
                showToast('场景保存成功！', 'success');
                promptName.value = '';
                currentSceneId = data.scene_id;
                startRealtimeBtn.style.display = 'inline-block';
            } else {
                showToast('保存失败: ' + (data.error || '未知错误'), 'error');
            }

        } catch (error) {
            showToast('保存失败，请重试', 'error');
            console.error('Error:', error);
        }

        saveBtn.textContent = '保存场景';
        saveBtn.disabled = false;
    }

    saveBtn.addEventListener('click', savePrompt);

    promptName.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            savePrompt();
        }
    });

    startRealtimeBtn.addEventListener('click', () => {
        if (currentSceneId) {
            window.location.href = `/realtime/${currentSceneId}`;
        }
    });

    initConversation();
});
