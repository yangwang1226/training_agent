document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chatMessages');
    const statusBar = document.getElementById('statusBar');
    const statusText = document.getElementById('statusText');
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const durationEl = document.getElementById('duration');
    const messageCountEl = document.getElementById('messageCount');
    const visualizer = document.getElementById('visualizer');
    const audioCanvas = document.getElementById('audioCanvas');
    const scenarioNameEl = document.getElementById('scenarioName');
    const customerProfileEl = document.getElementById('customerProfile');
    const providerModal = document.getElementById('providerModal');

    let ws = null;
    let isConnected = false;
    let isRecording = false;
    let audioContext = null;
    let audioStream = null;
    let analyser = null;
    let animationId = null;
    let startTime = null;
    let durationInterval = null;
    let messageCount = 0;
    let currentAudioContext = null;
    let audioQueue = [];
    let isPlayingAudio = false;
    let currentAudioSource = null;
    let lastMessageDiv = null;
    let lastMessageRole = null;
    let lastMessageText = '';
    let selectedProvider = null;
    let scenePrompt = '';

    loadSceneInfo();

    async function loadSceneInfo() {
        try {
            const response = await fetch(`/realtime/prompt/${SCENE_ID}`);
            const data = await response.json();
            if (data.success) {
                scenePrompt = data.prompt;
                parseAndDisplaySceneInfo(data.prompt);
                startBtn.disabled = false;
            } else {
                scenarioNameEl.textContent = '加载失败';
                customerProfileEl.textContent = data.error;
            }
        } catch (error) {
            scenarioNameEl.textContent = '加载失败';
            customerProfileEl.textContent = '网络错误';
            console.error('Error:', error);
        }
    }

    function parseAndDisplaySceneInfo(prompt) {
        scenarioNameEl.textContent = SCENE_NAME || '销售实战演练';
        
        const lines = prompt.split('\n');
        let profileInfo = '';
        
        for (const line of lines) {
            if (line.includes('客户') || line.includes('背景') || line.includes('场景')) {
                const cleanLine = line.replace(/^#+\s*/, '').replace(/\*\*/g, '').trim();
                if (cleanLine.length > 0 && cleanLine.length < 100) {
                    profileInfo += cleanLine + '；';
                }
            }
        }
        
        if (profileInfo) {
            customerProfileEl.textContent = profileInfo.slice(0, -1);
        } else {
            customerProfileEl.textContent = 'AI模拟客户，与您进行销售实战演练';
        }
    }

    startBtn.addEventListener('click', showProviderModal);
    stopBtn.addEventListener('click', stopSession);

    document.querySelectorAll('.provider-option').forEach(btn => {
        btn.addEventListener('click', function() {
            selectedProvider = this.dataset.provider;
            providerModal.style.display = 'none';
            startSession();
        });
    });

    function showProviderModal() {
        providerModal.style.display = 'flex';
    }

    async function startSession() {
        try {
            startBtn.disabled = true;
            updateStatus('connecting', '正在连接...');

            audioStream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                } 
            });

            audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
            
            analyser = audioContext.createAnalyser();
            const source = audioContext.createMediaStreamSource(audioStream);
            source.connect(analyser);
            analyser.fftSize = 256;

            const bufferSize = 4096;
            const scriptProcessor = audioContext.createScriptProcessor(bufferSize, 1, 1);
            
            scriptProcessor.onaudioprocess = (event) => {
                if (isRecording && ws && ws.readyState === WebSocket.OPEN) {
                    const inputData = event.inputBuffer.getChannelData(0);
                    const pcmData = float32ToPCM16(inputData);
                    ws.send(pcmData);
                }
            };
            
            const muteGain = audioContext.createGain();
            muteGain.gain.value = 0;
            
            source.connect(scriptProcessor);
            scriptProcessor.connect(muteGain);
            muteGain.connect(audioContext.destination);
            
            window.scriptProcessor = scriptProcessor;
            window.audioSource = source;
            window.muteGain = muteGain;

            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${wsProtocol}//${window.location.host}/api/realtime/ws/${SCENE_ID}?provider=${selectedProvider}`;
            ws = new WebSocket(wsUrl);
            ws.binaryType = 'arraybuffer';

            ws.onopen = () => {
                isConnected = true;
                isRecording = true;
                updateStatus('connected', '已连接 - 正在录音');
                startBtn.style.display = 'none';
                stopBtn.style.display = 'inline-flex';
                visualizer.classList.add('active');
                startDurationTimer();
                drawVisualizer();
                hideWelcomeMessage();
            };

            ws.onmessage = (event) => {
                try {
                    if (typeof event.data === 'string') {
                        const data = JSON.parse(event.data);
                        handleWebSocketMessage(data);
                    } else if (event.data instanceof ArrayBuffer) {
                        playAudio(event.data);
                    }
                } catch (e) {
                    console.error('Message parse error:', e);
                }
            };

            ws.onclose = () => {
                handleDisconnect();
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                updateStatus('error', '连接错误');
                handleDisconnect();
            };

        } catch (error) {
            console.error('Start session error:', error);
            updateStatus('error', '启动失败: ' + error.message);
            startBtn.disabled = false;
        }
    }

    function float32ToPCM16(float32Array) {
        const buffer = new ArrayBuffer(float32Array.length * 2);
        const view = new DataView(buffer);
        for (let i = 0; i < float32Array.length; i++) {
            let s = Math.max(-1, Math.min(1, float32Array[i]));
            view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
        }
        return buffer;
    }

    function stopSession() {
        isRecording = false;
        
        clearAudioQueue();
        
        if (window.scriptProcessor) {
            window.scriptProcessor.disconnect();
            window.scriptProcessor = null;
        }
        
        if (window.audioSource) {
            window.audioSource.disconnect();
            window.audioSource = null;
        }
        
        if (window.muteGain) {
            window.muteGain.disconnect();
            window.muteGain = null;
        }

        if (audioStream) {
            audioStream.getTracks().forEach(track => track.stop());
            audioStream = null;
        }

        if (audioContext) {
            audioContext.close();
            audioContext = null;
        }
        
        if (currentAudioContext) {
            currentAudioContext.close();
            currentAudioContext = null;
        }

        if (ws) {
            ws.close();
        }

        if (animationId) {
            cancelAnimationFrame(animationId);
        }

        handleDisconnect();
    }

    function handleDisconnect() {
        isConnected = false;
        isRecording = false;
        updateStatus('disconnected', '已断开 - 对练结束');
        startBtn.style.display = 'inline-flex';
        stopBtn.style.display = 'none';
        startBtn.disabled = false;
        visualizer.classList.remove('active');
        stopDurationTimer();
    }

    function hideWelcomeMessage() {
        const welcomeContent = chatMessages.querySelector('.welcome-content');
        if (welcomeContent) {
            welcomeContent.style.display = 'none';
        }
    }

    function handleWebSocketMessage(data) {
        switch (data.type) {
            case 'text':
                const role = data.role || 'ai';
                const text = data.text || '';
                const isFinal = data.is_final || false;
                
                if (text.trim()) {
                    if (isFinal) {
                        if (lastMessageDiv && lastMessageRole === role) {
                            lastMessageText += text;
                            lastMessageDiv.querySelector('.message-text').textContent = lastMessageText;
                        } else {
                            addMessage(text.trim(), role);
                            lastMessageText = text;
                            lastMessageRole = role;
                        }
                    } else {
                        if (lastMessageDiv && lastMessageRole === role) {
                            lastMessageText = text;
                            lastMessageDiv.querySelector('.message-text').textContent = text;
                        } else {
                            addMessage(text.trim(), role);
                            lastMessageText = text;
                            lastMessageRole = role;
                        }
                    }
                }
                break;
            case 'audio':
                if (data.audio) {
                    const audioData = base64ToArrayBuffer(data.audio);
                    playAudio(audioData);
                }
                break;
            case 'status':
                updateStatus(data.status, data.message);
                if (data.status === 'speaking') {
                    if (currentAudioSource) {
                        try {
                            currentAudioSource.stop();
                        } catch (e) {}
                        currentAudioSource = null;
                    }
                    audioQueue = [];
                    isPlayingAudio = false;
                    lastMessageDiv = null;
                    lastMessageRole = null;
                    lastMessageText = '';
                }
                break;
            case 'error':
                addMessage('错误: ' + data.message, 'ai');
                break;
        }
    }
    
    function clearAudioQueue() {
        audioQueue = [];
        isPlayingAudio = false;
        
        if (currentAudioSource) {
            try {
                currentAudioSource.stop();
            } catch (e) {}
            currentAudioSource = null;
        }
    }

    function addMessage(text, role) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role === 'user' ? 'user-message' : 'ai-message'}`;
        
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        avatarDiv.textContent = role === 'user' ? '我' : 'AI';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.textContent = text;
        
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = new Date().toLocaleTimeString();
        
        contentDiv.appendChild(textDiv);
        contentDiv.appendChild(timeDiv);
        
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        lastMessageDiv = messageDiv;
        
        messageCount++;
        messageCountEl.textContent = messageCount;
    }

    function updateStatus(status, message) {
        statusBar.className = 'status-indicator ' + status;
        statusText.textContent = message;
    }

    function startDurationTimer() {
        startTime = Date.now();
        durationInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
            const seconds = (elapsed % 60).toString().padStart(2, '0');
            durationEl.textContent = `${minutes}:${seconds}`;
        }, 1000);
    }

    function stopDurationTimer() {
        if (durationInterval) {
            clearInterval(durationInterval);
        }
    }

    function drawVisualizer() {
        if (!analyser || !isConnected) return;

        const canvas = audioCanvas;
        const ctx = canvas.getContext('2d');
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        function draw() {
            if (!isConnected) return;

            animationId = requestAnimationFrame(draw);
            analyser.getByteFrequencyData(dataArray);

            ctx.fillStyle = 'rgba(240, 250, 247, 0.3)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            const barWidth = (canvas.width / bufferLength) * 2.5;
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                const barHeight = (dataArray[i] / 255) * canvas.height;
                
                const gradient = ctx.createLinearGradient(0, canvas.height, 0, 0);
                gradient.addColorStop(0, '#3EB489');
                gradient.addColorStop(1, '#00CED1');
                
                ctx.fillStyle = gradient;
                ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
                x += barWidth + 1;
            }
        }

        draw();
    }

    async function playAudio(audioData) {
        try {
            if (!currentAudioContext) {
                currentAudioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
            }

            if (currentAudioContext.state === 'suspended') {
                await currentAudioContext.resume();
            }
            
            if (audioData.byteLength > 0) {
                try {
                    const wavData = pcmToWav(audioData, 24000, 1, 16);
                    const audioBuffer = await currentAudioContext.decodeAudioData(wavData);
                    
                    if (audioBuffer.duration > 0) {
                        audioQueue.push(audioBuffer);
                        
                        if (!isPlayingAudio) {
                            playNextInQueue();
                        }
                    }
                } catch (e) {
                    console.error('Audio decode error:', e);
                }
            }
        } catch (error) {
            console.error('Play audio error:', error);
        }
    }

    function pcmToWav(pcmData, sampleRate, numChannels, bitsPerSample) {
        const blockAlign = numChannels * (bitsPerSample / 8);
        const byteRate = sampleRate * blockAlign;
        const dataSize = pcmData.byteLength;
        const bufferSize = 44 + dataSize;
        
        const buffer = new ArrayBuffer(bufferSize);
        const view = new DataView(buffer);
        
        writeString(view, 0, 'RIFF');
        view.setUint32(4, 36 + dataSize, true);
        writeString(view, 8, 'WAVE');
        writeString(view, 12, 'fmt ');
        view.setUint32(16, 16, true);
        view.setUint16(20, 1, true);
        view.setUint16(22, numChannels, true);
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, byteRate, true);
        view.setUint16(32, blockAlign, true);
        view.setUint16(34, bitsPerSample, true);
        writeString(view, 36, 'data');
        view.setUint32(40, dataSize, true);
        
        const pcmInt16View = new Int16Array(pcmData);
        const wavInt16View = new Int16Array(buffer, 44, pcmInt16View.length);
        
        for (let i = 0; i < pcmInt16View.length; i++) {
            wavInt16View[i] = pcmInt16View[i];
        }
        
        return buffer;
    }

    function playNextInQueue() {
        if (audioQueue.length === 0) {
            isPlayingAudio = false;
            currentAudioSource = null;
            return;
        }

        isPlayingAudio = true;
        const audioBuffer = audioQueue.shift();
        
        currentAudioSource = currentAudioContext.createBufferSource();
        currentAudioSource.buffer = audioBuffer;
        currentAudioSource.connect(currentAudioContext.destination);
        
        currentAudioSource.start(currentAudioContext.currentTime);
        
        currentAudioSource.onended = () => {
            currentAudioSource = null;
            if (isPlayingAudio) {
                playNextInQueue();
            }
        };
    }

    function writeString(view, offset, string) {
        for (let i = 0; i < string.length; i++) {
            view.setUint8(offset + i, string.charCodeAt(i));
        }
    }

    function base64ToArrayBuffer(base64) {
        const binaryString = atob(base64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        return bytes.buffer;
    }

    window.addEventListener('beforeunload', () => {
        stopSession();
    });
});
