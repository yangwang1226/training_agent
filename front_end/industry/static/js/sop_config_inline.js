// ============================================
// SOP 质检项配置 - 内嵌模态框交互逻辑
// ============================================

let currentSopItems = [];
let currentSceneCode = null;
let currentSceneId = null;  // 场景实例ID（从主页面传入）
let pendingSopItems = null;  // 待保存的质检项（缓存在前端，场景生成后保存）

// DOM 元素
const sopConfigModalOverlay = document.getElementById('sopConfigModalOverlay');
const sopConfigClose = document.getElementById('sopConfigClose');
const tabManual = document.getElementById('tabManual');
const tabExtract = document.getElementById('tabExtract');
const panelManual = document.getElementById('panelManual');
const panelExtract = document.getElementById('panelExtract');
const sopItemsList = document.getElementById('sopItemsList');
const btnAddItem = document.getElementById('btnAddItem');
const btnCancelSop = document.getElementById('btnCancelSop');
const btnSaveSop = document.getElementById('btnSaveSop');

// 智能提取相关
const uploadTabAudio = document.getElementById('uploadTabAudio');
const uploadTabText = document.getElementById('uploadTabText');
const uploadSectionAudio = document.getElementById('uploadSectionAudio');
const uploadSectionText = document.getElementById('uploadSectionText');
const audioDropzone = document.getElementById('audioDropzone');
const audioFileInput = document.getElementById('audioFileInput');
const audioFileList = document.getElementById('audioFileList');
const textRecordInput = document.getElementById('textRecordInput');
const textCharCount = document.getElementById('textCharCount');
const btnExtract = document.getElementById('btnExtract');
const extractResult = document.getElementById('extractResult');
const extractResultList = document.getElementById('extractResultList');
const extractResultCount = document.getElementById('extractResultCount');

let uploadedAudioFiles = [];

// ============================================
// 初始化事件监听
// ============================================
function initSopConfigEvents() {
    // 关闭模态框
    sopConfigClose.addEventListener('click', closeSopConfigModal);
    sopConfigModalOverlay.addEventListener('click', (e) => {
        if (e.target === sopConfigModalOverlay) {
            closeSopConfigModal();
        }
    });

    // Tab 切换
    tabManual.addEventListener('click', () => switchTab('manual'));
    tabExtract.addEventListener('click', () => switchTab('extract'));

    // 手工配置
    btnAddItem.addEventListener('click', addNewSopItem);

    // 智能提取 - 上传方式切换
    uploadTabAudio.addEventListener('click', () => switchUploadType('audio'));
    uploadTabText.addEventListener('click', () => switchUploadType('text'));

    // 音频上传
    audioDropzone.addEventListener('click', () => audioFileInput.click());
    audioFileInput.addEventListener('change', handleAudioFileSelect);
    
    // 拖拽上传
    audioDropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        audioDropzone.classList.add('drag-over');
    });
    audioDropzone.addEventListener('dragleave', () => {
        audioDropzone.classList.remove('drag-over');
    });
    audioDropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        audioDropzone.classList.remove('drag-over');
        handleAudioFileDrop(e.dataTransfer.files);
    });

    // 文字输入计数
    textRecordInput.addEventListener('input', () => {
        textCharCount.textContent = textRecordInput.value.length;
    });

    // 智能提取按钮
    btnExtract.addEventListener('click', performSmartExtraction);

    // 底部按钮
    btnCancelSop.addEventListener('click', closeSopConfigModal);
    btnSaveSop.addEventListener('click', saveSopItems);
}

// ============================================
// 打开 SOP 配置模态框
// ============================================
function openSopConfigModal() {
    if (!selectedScene || !selectedScene.id) {
        showToast('请先选择场景', 'error');
        return;
    }

    currentSceneCode = selectedScene.id;
    
    // 优先加载已缓存的质检项，否则从服务器加载
    if (pendingSopItems && pendingSopItems.length > 0) {
        console.log('加载缓存的质检项');
        // 将缓存的质检项转换为内部格式
        currentSopItems = pendingSopItems.map(item => ({
            id: Date.now() + Math.random(),
            name: item.item_name,
            type: item.check_type,
            keywords: item.keywords ? item.keywords.split(',') : [],
            category: item.category || 'greeting'
        }));
        renderSopItems();
    } else {
        // 加载服务器上的质检项（如果有 scene_id）或预设模板
        loadExistingSopItems();
    }

    // 显示模态框
    sopConfigModalOverlay.classList.add('show');
    document.body.style.overflow = 'hidden';
}

// ============================================
// 关闭 SOP 配置模态框
// ============================================
function closeSopConfigModal() {
    sopConfigModalOverlay.classList.remove('show');
    document.body.style.overflow = '';
    
    // 重置状态
    resetExtractPanel();
}

// ============================================
// Tab 切换
// ============================================
function switchTab(tabName) {
    // 切换 Tab 按钮状态
    document.querySelectorAll('.sop-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.sop-config-panel').forEach(panel => {
        panel.classList.remove('active');
    });

    if (tabName === 'manual') {
        tabManual.classList.add('active');
        panelManual.classList.add('active');
    } else {
        tabExtract.classList.add('active');
        panelExtract.classList.add('active');
    }
}

// ============================================
// 手工配置 - 添加新质检项
// ============================================
function addNewSopItem() {
    const newItem = {
        id: Date.now(),
        name: '',
        type: 'must_do',
        keywords: [],
        category: 'greeting'
    };
    currentSopItems.push(newItem);
    renderSopItems();
}

// ============================================
// 渲染质检项列表
// ============================================
function renderSopItems() {
    if (currentSopItems.length === 0) {
        sopItemsList.innerHTML = '<div style="text-align: center; padding: 40px; color: #9CA3AF;">暂无质检项，点击下方按钮添加</div>';
        return;
    }

    sopItemsList.innerHTML = currentSopItems.map((item, index) => `
        <div class="sop-item-card" data-item-id="${item.id}">
            <div class="sop-item-header">
                <span class="sop-item-type-badge ${item.type}">
                    ${item.type === 'must_do' ? '✓ 必须做' : '✗ 禁止做'}
                </span>
                <input 
                    type="text" 
                    class="sop-item-name-input" 
                    placeholder="例如: 30秒内主动问候客户"
                    value="${item.name || ''}"
                    oninput="updateSopItemName(${item.id}, this.value)"
                />
                <div class="sop-item-actions">
                    <button class="sop-item-btn" onclick="toggleSopItemType(${item.id})" title="切换类型">
                        🔄
                    </button>
                    <button class="sop-item-btn delete" onclick="deleteSopItem(${item.id})" title="删除">
                        🗑️
                    </button>
                </div>
            </div>
            <div class="sop-item-keywords">
                ${item.keywords.map(kw => `
                    <span class="sop-keyword-tag">
                        ${kw}
                        <span class="remove" onclick="removeKeyword(${item.id}, '${kw}')">×</span>
                    </span>
                `).join('')}
                <input 
                    type="text" 
                    class="sop-keyword-input" 
                    placeholder="+ 添加关键词"
                    onkeypress="handleKeywordInput(event, ${item.id})"
                />
            </div>
        </div>
    `).join('');
}

// ============================================
// 质检项操作函数
// ============================================
function updateSopItemName(itemId, name) {
    const item = currentSopItems.find(i => i.id === itemId);
    if (item) {
        item.name = name;
    }
}

function toggleSopItemType(itemId) {
    const item = currentSopItems.find(i => i.id === itemId);
    if (item) {
        item.type = item.type === 'must_do' ? 'must_not' : 'must_do';
        renderSopItems();
    }
}

function deleteSopItem(itemId) {
    currentSopItems = currentSopItems.filter(i => i.id !== itemId);
    renderSopItems();
}

function removeKeyword(itemId, keyword) {
    const item = currentSopItems.find(i => i.id === itemId);
    if (item) {
        item.keywords = item.keywords.filter(kw => kw !== keyword);
        renderSopItems();
    }
}

function handleKeywordInput(event, itemId) {
    if (event.key === 'Enter') {
        event.preventDefault();
        const input = event.target;
        const keyword = input.value.trim();
        if (keyword) {
            const item = currentSopItems.find(i => i.id === itemId);
            if (item && !item.keywords.includes(keyword)) {
                item.keywords.push(keyword);
                renderSopItems();
            }
        }
    }
}

// ============================================
// 智能提取 - 上传方式切换
// ============================================
function switchUploadType(type) {
    document.querySelectorAll('.upload-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.upload-section').forEach(section => {
        section.classList.remove('active');
    });

    if (type === 'audio') {
        uploadTabAudio.classList.add('active');
        uploadSectionAudio.classList.add('active');
    } else {
        uploadTabText.classList.add('active');
        uploadSectionText.classList.add('active');
    }
}

// ============================================
// 音频文件处理
// ============================================
function handleAudioFileSelect(event) {
    const files = event.target.files;
    handleAudioFileDrop(files);
}

function handleAudioFileDrop(files) {
    Array.from(files).forEach(file => {
        if (file.type.startsWith('audio/')) {
            if (file.size > 50 * 1024 * 1024) {
                showToast('文件大小不能超过 50MB', 'error');
                return;
            }
            uploadedAudioFiles.push(file);
        } else {
            showToast('请上传音频文件', 'error');
        }
    });
    renderAudioFileList();
}

function renderAudioFileList() {
    if (uploadedAudioFiles.length === 0) {
        audioFileList.innerHTML = '';
        return;
    }

    audioFileList.innerHTML = uploadedAudioFiles.map((file, index) => `
        <div class="upload-file-item">
            <span class="file-icon">🎵</span>
            <div class="file-info">
                <div class="file-name">${file.name}</div>
                <div class="file-size">${formatFileSize(file.size)}</div>
            </div>
            <button class="file-remove" onclick="removeAudioFile(${index})">×</button>
        </div>
    `).join('');
}

function removeAudioFile(index) {
    uploadedAudioFiles.splice(index, 1);
    renderAudioFileList();
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// ============================================
// 智能提取
// ============================================
async function performSmartExtraction() {
    const extractMustDo = document.getElementById('extractMustDo').checked;
    const extractMustNot = document.getElementById('extractMustNot').checked;

    // 检查输入
    const hasAudio = uploadedAudioFiles.length > 0;
    const hasText = textRecordInput.value.trim().length > 0;

    if (!hasAudio && !hasText) {
        showToast('请上传录音文件或输入文字记录', 'error');
        return;
    }

    // 显示加载状态
    btnExtract.classList.add('loading');
    btnExtract.innerHTML = '<span>🤖</span> 正在智能提取...';

    try {
        let extractedItems = [];

        if (hasText) {
            // 文字提取
            const response = await fetch('/api/sop/extract-from-text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    scene_code: currentSceneCode,
                    text_content: textRecordInput.value.trim(),
                    extract_must_do: extractMustDo,
                    extract_must_not: extractMustNot
                })
            });

            const data = await response.json();
            if (data.success) {
                extractedItems = data.items || [];
            } else {
                throw new Error(data.error || '提取失败');
            }
        } else if (hasAudio) {
            // 音频提取 (需要先上传文件)
            const formData = new FormData();
            formData.append('scene_code', currentSceneCode);
            formData.append('extract_must_do', extractMustDo);
            formData.append('extract_must_not', extractMustNot);
            uploadedAudioFiles.forEach(file => {
                formData.append('audio_files', file);
            });

            const response = await fetch('/api/sop/extract-from-audio', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (data.success) {
                extractedItems = data.items || [];
            } else {
                throw new Error(data.error || '提取失败');
            }
        }

        // 显示提取结果
        if (extractedItems.length > 0) {
            renderExtractResult(extractedItems);
            showToast(`成功提取 ${extractedItems.length} 项质检项`, 'success');
        } else {
            showToast('未能提取到质检项，请检查内容', 'warning');
        }
    } catch (error) {
        console.error('智能提取失败:', error);
        showToast('提取失败: ' + error.message, 'error');
    } finally {
        // 恢复按钮状态
        btnExtract.classList.remove('loading');
        btnExtract.innerHTML = '<span>🤖</span> 开始智能提取';
    }
}

// ============================================
// 渲染提取结果
// ============================================
function renderExtractResult(items) {
    extractResultCount.textContent = items.length + ' 项';
    extractResultList.innerHTML = items.map((item, index) => `
        <div class="extract-result-item">
            <input type="checkbox" checked data-item-index="${index}" />
            <div class="extract-result-content">
                <div class="extract-result-name">
                    <span class="sop-item-type-badge ${item.type}">
                        ${item.type === 'must_do' ? '✓ 必须做' : '✗ 禁止做'}
                    </span>
                    ${item.name}
                </div>
                ${item.keywords && item.keywords.length > 0 ? `
                    <div class="extract-result-keywords">
                        ${item.keywords.map(kw => `<span class="extract-keyword">${kw}</span>`).join('')}
                    </div>
                ` : ''}
            </div>
        </div>
    `).join('');

    extractResult.style.display = 'block';

    // 存储提取的项目供后续使用
    extractResult.dataset.items = JSON.stringify(items);
}

// ============================================
// 加载已有质检项
// ============================================
async function loadExistingSopItems() {
    try {
        // 如果有 scene_id，加载场景实例的质检项；否则加载预设模板
        const url = currentSceneId 
            ? `/api/sop/checklist/scene/${currentSceneId}`
            : `/api/sop/checklist/preset/${currentSceneCode}`;
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success && data.data.checklist) {
            currentSopItems = data.data.checklist.map(item => ({
                id: item.id || Date.now() + Math.random(),
                name: item.item_name,
                type: item.check_type,
                keywords: item.keywords ? item.keywords.split(',') : [],
                category: item.category || 'greeting'
            }));
        } else {
            currentSopItems = [];
        }
        
        renderSopItems();
    } catch (error) {
        console.error('加载质检项失败:', error);
        currentSopItems = [];
        renderSopItems();
    }
}

// ============================================
// 保存质检项（前端缓存）
// ============================================
function saveSopItems() {
    // 收集手工配置的项
    let itemsToSave = [...currentSopItems];

    // 如果有提取结果，合并选中的项
    if (extractResult.style.display !== 'none' && extractResult.dataset.items) {
        const extractedItems = JSON.parse(extractResult.dataset.items);
        const checkboxes = extractResult.querySelectorAll('input[type="checkbox"]');
        
        checkboxes.forEach((checkbox, index) => {
            if (checkbox.checked) {
                const item = extractedItems[index];
                itemsToSave.push({
                    id: Date.now() + Math.random(),
                    name: item.name,
                    type: item.type,
                    keywords: item.keywords || [],
                    category: item.category || 'greeting'
                });
            }
        });
    }

    // 验证
    const validItems = itemsToSave.filter(item => item.name && item.name.trim());
    if (validItems.length === 0) {
        showToast('请至少添加一项质检项', 'error');
        return;
    }

    // 暂存到前端（场景生成后再保存到数据库）
    pendingSopItems = validItems.map(item => ({
        item_name: item.name,
        check_type: item.type,
        keywords: item.keywords.join(','),
        category: item.category
    }));
    
    console.log('质检项已暂存:', pendingSopItems);
    showToast(`已暂存 ${validItems.length} 项质检项，生成场景时将自动保存`, 'success');
    
    // 更新预览显示
    updateSopPreviewInBackgroundModal(validItems);
    
    closeSopConfigModal();
}

// 实际保存质检项到服务器（场景生成后调用）
// ============================================
async function saveSopItemsToServer(sceneId, sopItems) {
    try {
        const response = await fetch('/api/sop/save-checklist', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                scene_id: sceneId,
                checklist: sopItems
            })
        });

        const data = await response.json();
        if (data.success) {
            console.log('质检项保存到服务器成功');
            return true;
        } else {
            console.error('保存质检项失败:', data.error);
            return false;
        }
    } catch (error) {
        console.error('保存质检项失败:', error);
        return false;
    }
}

// 更新背景补充弹窗中的 SOP 预览
// ============================================
function updateSopPreviewInBackgroundModal(items) {
    const preview = document.getElementById('bgSopPreview');
    if (!preview) return;
    
    if (!items || items.length === 0) {
        preview.innerHTML = '<div class="bg-sop-empty"><span>暂未配置质检项</span></div>';
        return;
    }
    
    const mustDoCount = items.filter(item => item.type === 'must_do').length;
    const mustNotCount = items.filter(item => item.type === 'must_not').length;
    
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
// 重置提取面板
// ============================================
function resetExtractPanel() {
    uploadedAudioFiles = [];
    renderAudioFileList();
    textRecordInput.value = '';
    textCharCount.textContent = '0';
    extractResult.style.display = 'none';
    extractResult.dataset.items = '';
}

// 清空待保存的质检项缓存
// ============================================
function clearPendingSopItems() {
    pendingSopItems = null;
    console.log('已清空质检项缓存');
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initSopConfigEvents();
});