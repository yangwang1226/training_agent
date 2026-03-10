// SOP 质检清单管理页面 JavaScript

// 全局变量
let currentSceneCode = '';
let currentChecklist = [];
let editingIndex = -1; // -1 表示新增，>= 0 表示编辑

// 页面加载完成
document.addEventListener('DOMContentLoaded', function() {
    loadSceneList();
});

// 返回上一页
function goBack() {
    window.history.back();
}

// 加载场景列表
async function loadSceneList() {
    try {
        const response = await fetch('/api/preset-scene/all');
        const data = await response.json();
        
        console.log('API 返回数据:', data); // 调试日志
        
        if (data.success) {
            const select = document.getElementById('sceneSelect');
            select.innerHTML = '<option value="">-- 请选择场景 --</option>';
            
            // 兼容两种返回格式: data.data 或 data.scenes
            const scenes = data.data || data.scenes || [];
            
            // 按行业分组
            const groupedScenes = {};
            scenes.forEach(scene => {
                if (!groupedScenes[scene.industry_code]) {
                    groupedScenes[scene.industry_code] = [];
                }
                groupedScenes[scene.industry_code].push(scene);
            });
            
            // 生成选项
            Object.keys(groupedScenes).forEach(industryCode => {
                const optgroup = document.createElement('optgroup');
                optgroup.label = getIndustryName(industryCode);
                
                groupedScenes[industryCode].forEach(scene => {
                    const option = document.createElement('option');
                    option.value = scene.scene_code;
                    option.textContent = scene.scene_name;
                    optgroup.appendChild(option);
                });
                
                select.appendChild(optgroup);
            });
        } else {
            showToast('加载场景列表失败', 'error');
        }
    } catch (error) {
        console.error('加载场景列表失败:', error);
        showToast('加载场景列表失败', 'error');
    }
}

// 获取行业名称
function getIndustryName(code) {
    const industryMap = {
        'auto_sales': '汽车销售',
        'education': '教育培训',
        'real_estate': '房地产',
        'insurance': '保险',
        'finance': '金融'
    };
    return industryMap[code] || code;
}

// 加载场景的质检清单
async function loadSceneChecklist() {
    const sceneCode = document.getElementById('sceneSelect').value;
    
    if (!sceneCode) {
        document.getElementById('checklistEditor').style.display = 'none';
        document.getElementById('emptyState').style.display = 'block';
        return;
    }
    
    currentSceneCode = sceneCode;
    document.getElementById('sceneLoading').style.display = 'inline';
    
    try {
        const response = await fetch(`/api/sop/checklist/${sceneCode}`);
        const data = await response.json();
        
        if (data.success) {
            currentChecklist = data.data.checklist || [];
            
            // 显示场景名称
            const sceneName = document.getElementById('sceneSelect').options[document.getElementById('sceneSelect').selectedIndex].text;
            document.getElementById('currentSceneName').textContent = sceneName;
            
            // 显示编辑器
            document.getElementById('emptyState').style.display = 'none';
            document.getElementById('checklistEditor').style.display = 'block';
            
            // 渲染质检项列表
            renderChecklist();
            
            showToast(data.message);
        } else {
            showToast('加载失败: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('加载质检清单失败:', error);
        showToast('加载失败', 'error');
    } finally {
        document.getElementById('sceneLoading').style.display = 'none';
    }
}

// 渲染质检项列表
function renderChecklist() {
    const container = document.getElementById('checklistItems');
    container.innerHTML = '';
    
    if (currentChecklist.length === 0) {
        container.innerHTML = '<div style="padding: 40px; text-align: center; color: #6c757d;">暂无质检项，点击"添加质检项"开始配置</div>';
        updateStats();
        return;
    }
    
    currentChecklist.forEach((item, index) => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'check-item';
        itemDiv.innerHTML = `
            <div class="item-order">${index + 1}</div>
            <div class="item-name">${escapeHtml(item.item_name)}</div>
            <div class="item-type ${item.check_type === 'must_do' ? 'must-do' : 'must-not'}">
                ${item.check_type === 'must_do' ? '✓ 必须做' : '✗ 禁止做'}
            </div>
            <div class="item-keywords">
                ${item.keywords ? item.keywords.map(kw => `<span class="keyword-tag">${escapeHtml(kw)}</span>`).join('') : '<span style="color: #6c757d; font-size: 13px;">未设置</span>'}
            </div>
            <div class="item-category">${escapeHtml(item.category || '-')}</div>
            <div class="item-actions">
                <button class="btn-edit" onclick="editCheckItem(${index})">编辑</button>
                <button class="btn-delete" onclick="deleteCheckItem(${index})">删除</button>
            </div>
        `;
        container.appendChild(itemDiv);
    });
    
    updateStats();
}

// 更新统计信息
function updateStats() {
    const mustDoCount = currentChecklist.filter(item => item.check_type === 'must_do').length;
    const mustNotCount = currentChecklist.filter(item => item.check_type === 'must_not').length;
    
    document.getElementById('mustDoCount').textContent = mustDoCount;
    document.getElementById('mustNotCount').textContent = mustNotCount;
    document.getElementById('totalCount').textContent = currentChecklist.length;
}

// 添加质检项
function addCheckItem() {
    editingIndex = -1;
    document.getElementById('modalTitle').textContent = '添加质检项';
    
    // 清空表单
    document.getElementById('itemName').value = '';
    document.getElementById('itemKeywords').value = '';
    document.getElementById('itemCategory').value = '';
    document.getElementById('itemDesc').value = '';
    document.querySelector('input[name="checkType"][value="must_do"]').checked = true;
    
    // 显示模态框
    document.getElementById('itemModal').classList.add('active');
}

// 编辑质检项
function editCheckItem(index) {
    editingIndex = index;
    const item = currentChecklist[index];
    
    document.getElementById('modalTitle').textContent = '编辑质检项';
    document.getElementById('itemName').value = item.item_name;
    document.getElementById('itemKeywords').value = item.keywords ? item.keywords.join(',') : '';
    document.getElementById('itemCategory').value = item.category || '';
    document.getElementById('itemDesc').value = item.item_desc || '';
    document.querySelector(`input[name="checkType"][value="${item.check_type}"]`).checked = true;
    
    document.getElementById('itemModal').classList.add('active');
}

// 删除质检项
function deleteCheckItem(index) {
    if (confirm('确定要删除这个质检项吗？')) {
        currentChecklist.splice(index, 1);
        renderChecklist();
        showToast('已删除', 'warning');
    }
}

// 关闭模态框
function closeItemModal() {
    document.getElementById('itemModal').classList.remove('active');
}

// 保存质检项（模态框中的确定按钮）
function saveItem() {
    const name = document.getElementById('itemName').value.trim();
    const keywordsStr = document.getElementById('itemKeywords').value.trim();
    const category = document.getElementById('itemCategory').value.trim();
    const desc = document.getElementById('itemDesc').value.trim();
    const checkType = document.querySelector('input[name="checkType"]:checked').value;
    
    // 验证
    if (!name) {
        showToast('请输入质检项名称', 'error');
        return;
    }
    
    // 解析关键词
    const keywords = keywordsStr ? keywordsStr.split(/[,，]/).map(kw => kw.trim()).filter(kw => kw) : [];
    
    // 构建质检项对象
    const item = {
        item_id: editingIndex >= 0 ? currentChecklist[editingIndex].item_id : `SOP${String(currentChecklist.length + 1).padStart(3, '0')}`,
        item_name: name,
        check_type: checkType,
        keywords: keywords,
        category: category,
        item_desc: desc
    };
    
    // 添加或更新
    if (editingIndex >= 0) {
        currentChecklist[editingIndex] = item;
    } else {
        currentChecklist.push(item);
    }
    
    // 关闭模态框并刷新列表
    closeItemModal();
    renderChecklist();
    showToast(editingIndex >= 0 ? '已更新' : '已添加');
}

// 保存整个清单到服务器
async function saveChecklist() {
    if (!currentSceneCode) {
        showToast('请先选择场景', 'error');
        return;
    }
    
    if (currentChecklist.length === 0) {
        if (!confirm('当前质检项为空，确定要保存空清单吗？')) {
            return;
        }
    }
    
    try {
        const response = await fetch(`/api/sop/checklist/${currentSceneCode}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                checklist: currentChecklist
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('✓ 保存成功');
        } else {
            showToast('保存失败: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('保存失败:', error);
        showToast('保存失败', 'error');
    }
}

// 显示提示消息
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = 'toast active ' + type;
    
    setTimeout(() => {
        toast.classList.remove('active');
    }, 3000);
}

// HTML 转义
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 关闭模态框（点击背景）
document.getElementById('itemModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeItemModal();
    }
});