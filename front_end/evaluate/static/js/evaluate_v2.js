/**
 * 评估报告页面 V2 - JavaScript
 * 功能：数据加载、渲染、交互
 */

// ===================================
// Mock Data (用于预览和测试)
// ===================================
function getMockData() {
    return {
        session_id: '9ae92a74-057e-4c5f-a7c5-927258613f81',
        scene_id: 12,
        scene_name: '汽车销售 - 客户接待场景',
        ai_score: 85,
        ai_summary: '整体表现不错，沟通能力突出，产品知识掌握扎实，但在需求挖掘和异议处理方面还有提升空间。',
        call_duration: 208, // 3分28秒
        created_time: '2024-03-15 14:32:18',
        audio_path: '/audio_file/demo.wav',
        
        // 维度评分结果
        dimension_result: {
            dimension_scores: [
                {
                    dimension_name: '沟通表达',
                    score: 92,
                    weight: 0.25,
                    feedback: '语言表达流畅自然，善于运用开放式问题引导对话，倾听能力强。'
                },
                {
                    dimension_name: '产品知识',
                    score: 88,
                    weight: 0.20,
                    feedback: '对产品参数和特点掌握较好，能够准确回答客户的技术问题。'
                },
                {
                    dimension_name: '需求挖掘',
                    score: 78,
                    weight: 0.20,
                    feedback: '能够识别客户的基本需求，但深层次需求挖掘不够充分，建议多使用追问技巧。'
                },
                {
                    dimension_name: '异议处理',
                    score: 82,
                    weight: 0.20,
                    feedback: '面对客户异议能保持冷静，但处理方式略显直接，建议采用更委婉的方式。'
                },
                {
                    dimension_name: '促成技巧',
                    score: 85,
                    weight: 0.15,
                    feedback: '善于把握成交时机，但促成话术还可以更加自然。'
                }
            ],
            highlights: [
                '开场白亲切自然，快速建立了良好的沟通氛围',
                '产品介绍专业且有针对性，突出了客户关心的卖点',
                '倾听能力强，能够准确捕捉客户的关注点',
                '整体态度积极热情，服务意识强'
            ],
            improvements: [
                '需求挖掘可以更深入，多使用"为什么"、"还有呢"等追问',
                '面对价格异议时，可以先认同再转移，避免直接反驳',
                '促成时机把握不错，但话术可以更加委婉自然',
                '建议增加对竞品的了解，以便更好地进行对比说明'
            ]
        },
        
        // AI建议
        ai_advise: `根据本次训练表现，为您提供以下个性化建议：

【沟通技巧提升】
1. 您的开场白表现优秀，建议继续保持这种亲和力
2. 在对话过程中，可以适当增加一些确认性语句，如"我理解您的意思是..."，让客户感受到被重视

【需求挖掘强化】
1. 当客户表达一个需求时，尝试追问"除了这个，您还有其他考虑吗？"
2. 使用场景化提问，如"您平时主要是上下班用车还是经常跑长途？"
3. 关注客户的情感需求，不仅仅是功能需求

【异议处理优化】
1. 采用"先跟后带"的方式：先认同客户的顾虑，再引导到产品优势
2. 价格异议处理公式：认同感受 → 解释价值 → 提供方案
3. 准备一些成功案例，用故事化的方式化解客户疑虑

【下一步行动建议】
- 建议进行3次"价格异议处理"专项训练
- 学习SPIN销售法，提升需求挖掘能力
- 观看优秀销售案例视频，学习促成技巧`,

        // SOP质检结果
        sop_result: {
            sop_score: 73,  // 百分制总分
            total_score: 225,  // 总可得分数
            actual_score: 165,  // 实际得分
            total_items: 10,
            passed_count: 7,
            failed_count: 3,
            pass_rate: 0.7,
            details: [
                { item_name: '开场问候礼仪', check_type: 'must_do', passed: true, default_score: 30, actual_score: 30, suggestion: '表现优秀，问候语亲切自然' },
                { item_name: '自我介绍', check_type: 'should_do', passed: true, default_score: 15, actual_score: 15, suggestion: '清晰介绍了姓名和职位' },
                { item_name: '需求确认', check_type: 'must_do', passed: true, default_score: 30, actual_score: 30, suggestion: '主动询问了客户的购车需求' },
                { item_name: '产品介绍', check_type: 'must_do', passed: true, default_score: 30, actual_score: 30, suggestion: '针对客户需求进行了产品推荐' },
                { item_name: '竞品对比', check_type: 'should_do', passed: false, default_score: 15, actual_score: 0, suggestion: '未进行竞品对比说明，建议补充' },
                { item_name: '试驾邀请', check_type: 'should_do', passed: true, default_score: 15, actual_score: 15, suggestion: '成功邀请客户试驾' },
                { item_name: '价格说明', check_type: 'must_do', passed: true, default_score: 30, actual_score: 30, suggestion: '清晰说明了价格构成' },
                { item_name: '优惠政策', check_type: 'should_do', passed: false, default_score: 15, actual_score: 0, suggestion: '未主动介绍当前优惠活动' },
                { item_name: '异议处理', check_type: 'should_do', passed: true, default_score: 15, actual_score: 15, suggestion: '对客户异议进行了回应' },
                { item_name: '后续跟进', check_type: 'should_do', passed: false, default_score: 15, actual_score: 0, suggestion: '未明确下次联系时间，建议改进' }
            ],
            summary: '基本流程执行较好，但在竞品对比、优惠政策介绍和后续跟进方面需要加强。'
        },
        
        // 音频分析
        audio_analysis: {
            speaking_rate: '正常',
            speaking_rate_value: 180, // 字/分钟
            emotion: '积极',
            emotion_score: 82,
            pause_frequency: '适中',
            volume_stability: '稳定',
            filler_words_count: 5 // "嗯"、"啊"等
        },
        
        // 对话内容
        word_content: JSON.stringify([
            { role: 'assistant', content: '您好！欢迎光临我们的展厅，我是销售顾问小王。请问今天是来看车的吗？' },
            { role: 'user', content: '是的，我想看看SUV，家用的。' },
            { role: 'assistant', content: '好的，家用SUV是个很好的选择。请问您家里大概几口人呢？平时主要是市区代步还是经常跑长途？' },
            { role: 'user', content: '一家四口，老人孩子都有。主要是市区用，偶尔周末带家人出去玩。' },
            { role: 'assistant', content: '明白了，那空间和舒适性对您来说应该比较重要。我给您推荐我们这款中型SUV，空间非常宽敞，后排坐三个大人都不挤。而且它的悬架调校偏舒适，开起来很稳，老人孩子坐着也不会晕车。' },
            { role: 'user', content: '这车多少钱？' },
            { role: 'assistant', content: '这款车指导价是23.8万，不过我们现在有购置税减半的政策，算下来能省不少。您要不要先坐进去感受一下空间？' },
            { role: 'user', content: '可以，我先看看。' },
            { role: 'assistant', content: '好的，您这边请。您看这个座椅，是真皮的，坐上去特别舒服。后排空间您感受一下，腿部空间很充裕的。' },
            { role: 'user', content: '嗯，空间确实不错。但是这个价格有点超预算了，我原来想的是20万以内。' },
            { role: 'assistant', content: '我理解您的考虑。这样，我可以帮您申请一下优惠，看看能不能再便宜一些。另外我们还有分期方案，首付30%，月供压力也不大。您方便的话，我们可以做个试驾，您实际开一下感受感受？' },
            { role: 'user', content: '好，那就试驾一下吧。' }
        ])
    };
}

// ===================================
// Utility Functions
// ===================================

/**
 * 格式化通话时长
 */
function formatDuration(seconds) {
    if (!seconds) return '--';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}分${secs}秒`;
}

/**
 * 格式化时间
 */
function formatTime(timeStr) {
    if (!timeStr) return '--';
    return timeStr.replace('T', ' ').substring(0, 16);
}

/**
 * 根据分数获取等级类名
 */
function getScoreClass(score) {
    if (score >= 90) return 'excellent';
    if (score >= 80) return 'good';
    if (score >= 70) return 'medium';
    if (score >= 60) return 'poor';
    return 'bad';
}

/**
 * 根据分数获取颜色
 */
function getScoreColor(score) {
    if (score >= 90) return '#10B981';
    if (score >= 80) return '#00D4AA';
    if (score >= 70) return '#F59E0B';
    if (score >= 60) return '#F97316';
    return '#EF4444';
}

/**
 * 根据分数获取等级文字
 */
function getGradeText(score) {
    if (score >= 90) return '优秀';
    if (score >= 80) return '良好';
    if (score >= 70) return '中等';
    if (score >= 60) return '需改进';
    return '不合格';
}

// ===================================
// Data Loading
// ===================================

/**
 * 从API加载报告数据
 */
async function loadReport(sessionId) {
    try {
        showLoading(true);
        
        const response = await fetch(`/evaluate/api/report/${sessionId}`);
        const result = await response.json();
        
        if (!result.success) {
            showError(result.error || '加载失败');
            return;
        }
        
        // 先显示容器再渲染报告，避免 ECharts 在 display:none 容器中初始化导致尺寸为0
        showLoading(false);
        renderReport(result.data);
        
    } catch (error) {
        console.error('加载报告失败:', error);
        showError('网络错误: ' + error.message);
        showLoading(false);
    }
}

/**
 * 显示/隐藏加载状态
 */
function showLoading(show) {
    const loading = document.getElementById('loadingContainer');
    const content = document.querySelector('.report-main');
    
    if (loading) {
        loading.style.display = show ? 'flex' : 'none';
    }
    if (content) {
        content.style.display = show ? 'none' : 'block';
    }
}

/**
 * 显示错误信息
 */
function showError(message) {
    const main = document.querySelector('.report-main');
    if (main) {
        main.innerHTML = `
            <div class="error-container" style="text-align: center; padding: 60px 20px;">
                <div style="font-size: 4rem; margin-bottom: 20px;">😔</div>
                <h2 style="color: var(--text-primary); margin-bottom: 10px;">加载失败</h2>
                <p style="color: var(--text-muted);">${message}</p>
                <a href="/scenes" class="btn btn-primary" style="margin-top: 30px;">返回场景列表</a>
            </div>
        `;
    }
}

// ===================================
// Rendering Functions
// ===================================

/**
 * 渲染完整报告
 */
function renderReport(data) {
    // 基本信息
    renderBasicInfo(data);
    
    // 综合评分
    renderOverallScore(data);
    
    // 雷达图
    renderRadarChart(data);
    
    // 维度详情
    renderDimensions(data);
    
    // SOP质检
    renderSopResults(data);
    
    // 亮点与改进
    renderFeedback(data);
    
    // AI建议
    renderAiAdvice(data);
    
    // 音频分析
    renderAudioAnalysis(data);
    
    // 对话回顾
    renderConversation(data);
}

/**
 * 渲染基本信息
 */
function renderBasicInfo(data) {
    const sceneName = document.getElementById('sceneName');
    const callDuration = document.getElementById('callDuration');
    const createdTime = document.getElementById('createdTime');
    
    // 使用 scene_name 字段，如果没有则使用场景ID
    if (sceneName) {
        sceneName.textContent = data.scene_name || `场景 #${data.scene_id}`;
    }
    if (callDuration) callDuration.textContent = formatDuration(data.call_duration);
    if (createdTime) createdTime.textContent = formatTime(data.created_time);
}

/**
 * 渲染综合评分
 */
function renderOverallScore(data) {
    const score = data.ai_score || 0;
    const grade = getGradeText(score);
    const summary = data.ai_summary || '';
    
    // 分数
    const scoreNumber = document.getElementById('overallScore');
    if (scoreNumber) scoreNumber.textContent = score;
    
    // 等级
    const scoreGrade = document.getElementById('scoreGrade');
    if (scoreGrade) {
        scoreGrade.textContent = grade;
        scoreGrade.className = `score-grade ${getScoreClass(score)}`;
    }
    
    // 摘要
    const scoreSummary = document.getElementById('scoreSummary');
    if (scoreSummary) scoreSummary.textContent = summary;
    
    // 圆环进度
    const scoreProgress = document.getElementById('scoreProgress');
    if (scoreProgress) {
        const circumference = 2 * Math.PI * 54; // r=54
        const offset = circumference - (score / 100) * circumference;
        scoreProgress.style.strokeDashoffset = offset;
        scoreProgress.style.stroke = getScoreColor(score);
    }
}

/**
 * 渲染雷达图
 */
function renderRadarChart(data) {
    const chartDom = document.getElementById('radarChart');
    if (!chartDom) return;
    
    // 即使没有数据也显示空的雷达图
    const myChart = echarts.init(chartDom);
    
    if (!data.dimension_result?.dimension_scores || data.dimension_result.dimension_scores.length === 0) {
        // 显示默认的空雷达图
        const option = {
            radar: {
                indicator: [
                    { name: '暂无数据', max: 100 }
                ],
                shape: 'polygon'
            },
            series: [{
                type: 'radar',
                data: [{
                    value: [0],
                    name: '暂无评分'
                }]
            }]
        };
        myChart.setOption(option);
        window.addEventListener('resize', () => myChart.resize());
        setTimeout(() => { myChart.resize(); }, 100);
        setTimeout(() => { myChart.resize(); }, 500);
        return;
    }
    
    const dimensions = data.dimension_result.dimension_scores;
    const indicators = dimensions.map(d => ({
        name: d.dimension_name,
        max: 100
    }));
    const values = dimensions.map(d => d.score);
    
    const option = {
        tooltip: {
            trigger: 'item'
        },
        radar: {
            indicator: indicators,
            shape: 'polygon',
            splitNumber: 5,
            axisName: {
                color: '#4A5568',
                fontSize: 12
            },
            splitLine: {
                lineStyle: {
                    color: '#E2E8F0'
                }
            },
            splitArea: {
                show: true,
                areaStyle: {
                    color: ['rgba(0, 102, 255, 0.02)', 'rgba(0, 102, 255, 0.04)']
                }
            },
            axisLine: {
                lineStyle: {
                    color: '#E2E8F0'
                }
            }
        },
        series: [{
            type: 'radar',
            data: [{
                value: values,
                name: '能力评分',
                areaStyle: {
                    color: 'rgba(0, 212, 170, 0.3)'
                },
                lineStyle: {
                    color: '#00D4AA',
                    width: 2
                },
                itemStyle: {
                    color: '#00D4AA'
                }
            }]
        }]
    };
    
    myChart.setOption(option);
    
    // 响应式调整
    window.addEventListener('resize', () => myChart.resize());
    
    // 修复首次加载时容器尺寸为0导致图表不显示的问题
    // 延迟执行 resize 确保 DOM 布局完成后图表正确渲染
    setTimeout(() => {
        myChart.resize();
    }, 100);
    setTimeout(() => {
        myChart.resize();
    }, 500);
}

/**
 * 渲染维度详情
 */
function renderDimensions(data) {
    const container = document.getElementById('dimensionGrid');
    if (!container || !data.dimension_result?.dimension_scores) return;
    
    const dimensions = data.dimension_result.dimension_scores;
    
    container.innerHTML = dimensions.map((dim, index) => {
        const scoreClass = getScoreClass(dim.score);
        return `
            <div class="dimension-card" style="animation-delay: ${index * 0.1}s">
                <div class="dimension-header">
                    <span class="dimension-name">${dim.dimension_name}</span>
                    <span class="dimension-score ${scoreClass}">${dim.score}分</span>
                </div>
                <div class="dimension-progress">
                    <div class="dimension-progress-fill ${scoreClass}" style="width: ${dim.score}%"></div>
                </div>
                <div class="dimension-feedback">${dim.feedback || ''}</div>
            </div>
        `;
    }).join('');
}

/**
 * 渲染SOP质检结果
 */
function renderSopResults(data) {
    const sopSection = document.querySelector('.sop-section');
    if (!data.sop_result) {
        if (sopSection) sopSection.style.display = 'none';
        return;
    }
    
    const sop = data.sop_result;
    
    // 分数
    const sopScore = document.getElementById('sopScore');
    if (sopScore) sopScore.textContent = sop.sop_score || 0;
    
    // 统计
    const sopTotal = document.getElementById('sopTotal');
    const sopPassed = document.getElementById('sopPassed');
    const sopFailed = document.getElementById('sopFailed');
    
    if (sopTotal) sopTotal.textContent = sop.total_items || 0;
    if (sopPassed) sopPassed.textContent = sop.passed_count || 0;
    if (sopFailed) sopFailed.textContent = sop.failed_count || 0;
    
    // 进度条（使用分数百分比）
    const sopProgressFill = document.getElementById('sopProgressFill');
    if (sopProgressFill) {
        const percentage = sop.sop_score || 0;
        sopProgressFill.style.width = `${percentage}%`;
    }
    
    // 详情列表
    const sopDetails = document.getElementById('sopDetails');
    if (sopDetails && sop.details) {
        sopDetails.innerHTML = sop.details.map(item => {
            // 处理多种可能的数据格式
            let itemName = '未知项';
            let suggestion = '';
            let passed = false;
            let defaultScore = 0;
            let actualScore = 0;
            
            if (typeof item === 'string') {
                // 纯字符串格式
                itemName = item;
            } else if (typeof item === 'object') {
                // 对象格式 - 支持多种字段名
                itemName = item.item_name || item.item || item.name || item.check_item || item.title || '未知项';
                suggestion = item.suggestion || item.advice || item.remark || item.feedback || '';
                passed = item.passed === true || item.status === 'passed' || item.result === 'pass';
                defaultScore = item.default_score || 0;
                actualScore = item.actual_score || 0;
            }
            
            // 清理 itemName 中可能的类型标记（如 "(must_do)"）
            itemName = itemName.replace(/\s*\([^)]+\)\s*$/, '');
            
            return `
                <div class="sop-item ${passed ? 'passed' : 'failed'}">
                    <div class="sop-item-icon">
                        ${passed ? '✓' : '✗'}
                    </div>
                    <div class="sop-item-content">
                        <div class="sop-item-name">
                            ${itemName}
                            <span class="sop-item-score">${actualScore}/${defaultScore}分</span>
                        </div>
                        ${suggestion ? `<div class="sop-item-suggestion">${suggestion}</div>` : ''}
                    </div>
                </div>
            `;
        }).join('');
    }
}

/**
 * 渲染亮点与改进建议
 */
function renderFeedback(data) {
    const highlightsList = document.getElementById('highlightsList');
    const improvementsList = document.getElementById('improvementsList');
    
    if (highlightsList && data.dimension_result?.highlights) {
        highlightsList.innerHTML = data.dimension_result.highlights.map(h => 
            `<li>${h}</li>`
        ).join('');
    }
    
    if (improvementsList && data.dimension_result?.improvements) {
        improvementsList.innerHTML = data.dimension_result.improvements.map(i => 
            `<li>${i}</li>`
        ).join('');
    }
}

/**
 * 渲染AI建议
 */
function renderAiAdvice(data) {
    const adviceText = document.getElementById('aiAdviceText');
    if (adviceText && data.ai_advise) {
        adviceText.textContent = data.ai_advise;
    }
}

/**
 * 渲染音频分析
 */
function renderAudioAnalysis(data) {
    const audioSection = document.getElementById('audioSection');
    if (!data.audio_analysis && !data.audio_path) {
        if (audioSection) audioSection.style.display = 'none';
        return;
    }
    
    // 音频播放器
    const audioPlayer = document.getElementById('audioPlayer');
    if (audioPlayer && data.audio_path) {
        audioPlayer.src = data.audio_path;
    }
    
    // 音频指标
    const audioMetrics = document.getElementById('audioMetrics');
    if (audioMetrics && data.audio_analysis) {
        const analysis = data.audio_analysis;
        audioMetrics.innerHTML = `
            <div class="audio-metric">
                <div class="audio-metric-value">${analysis.speaking_rate || '--'}</div>
                <div class="audio-metric-label">语速</div>
            </div>
            <div class="audio-metric">
                <div class="audio-metric-value">${analysis.emotion || '--'}</div>
                <div class="audio-metric-label">情感</div>
            </div>
            <div class="audio-metric">
                <div class="audio-metric-value">${analysis.pause_frequency || '--'}</div>
                <div class="audio-metric-label">停顿频率</div>
            </div>
            <div class="audio-metric">
                <div class="audio-metric-value">${analysis.volume_stability || '--'}</div>
                <div class="audio-metric-label">音量稳定性</div>
            </div>
        `;
    }
}

/**
 * 渲染对话回顾
 */
function renderConversation(data) {
    const messagesContainer = document.getElementById('conversationMessages');
    if (!messagesContainer || !data.word_content) return;
    
    let messages = [];
    let rawText = data.word_content;
    
    try {
        // 尝试解析为JSON
        messages = typeof rawText === 'string' ? JSON.parse(rawText) : rawText;
    } catch (e) {
        // 如果不是JSON，可能是纯文本格式，需要解析
        // 格式: [11:40:09] 用户: 喂喂。
        if (typeof rawText === 'string') {
            const lines = rawText.split('\n').filter(line => line.trim());
            messages = lines.map(line => {
                // 匹配格式: [时间] 角色: 内容
                const match = line.match(/\[([^\]]+)\]\s*([^:：]+)[:：]\s*(.+)/);
                if (match) {
                    const [, time, role, content] = match;
                    return {
                        role: role.trim().includes('用户') || role.trim().includes('User') ? 'user' : 'assistant',
                        content: content.trim(),
                        time: time.trim()
                    };
                }
                return null;
            }).filter(msg => msg !== null);
            
            // 如果解析失败，直接显示原文本
            if (messages.length === 0) {
                messagesContainer.innerHTML = `<pre style="white-space: pre-wrap; padding: 20px; background: var(--bg-muted); border-radius: var(--radius-md); line-height: 1.8;">${rawText}</pre>`;
                return;
            }
        } else {
            return;
        }
    }
    
    if (!Array.isArray(messages)) return;
    
    messagesContainer.innerHTML = messages.map(msg => {
        // 支持多种角色字段名
        const role = msg.role || msg.speaker || 'unknown';
        const isUser = role === 'user' || role === 'User' || role.includes('用户');
        const content = msg.content || msg.text || msg.message || '';
        
        return `
            <div class="message ${isUser ? 'user' : 'ai'}">
                <div class="message-avatar">
                    ${isUser ? '👤' : '🤖'}
                </div>
                <div class="message-bubble">
                    ${content}
                </div>
            </div>
        `;
    }).join('');
}

// ===================================
// Interaction Handlers
// ===================================

/**
 * 切换AI建议展开/收起
 */
function toggleAdvice() {
    const content = document.getElementById('adviceContent');
    const toggle = document.getElementById('adviceToggle');
    
    if (content && toggle) {
        content.classList.toggle('expanded');
        toggle.classList.toggle('expanded');
    }
}

/**
 * 切换对话回顾展开/收起
 */
function toggleConversation() {
    const content = document.getElementById('conversationContent');
    const toggle = document.getElementById('conversationToggle');
    
    if (content && toggle) {
        content.classList.toggle('expanded');
        toggle.classList.toggle('expanded');
    }
}

// ===================================
// Initialization
// ===================================

// 页面加载完成后自动初始化一些交互
document.addEventListener('DOMContentLoaded', () => {
    // 默认展开AI建议
    const adviceContent = document.getElementById('adviceContent');
    const adviceToggle = document.getElementById('adviceToggle');
    if (adviceContent && adviceToggle) {
        adviceContent.classList.add('expanded');
        adviceToggle.classList.add('expanded');
    }
});