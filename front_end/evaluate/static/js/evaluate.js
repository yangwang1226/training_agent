document.addEventListener('DOMContentLoaded', function() {
    const tabs = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const pageTitle = document.getElementById('pageTitle');
    
    let radarChart = null;
    let trendChart = null;
    
    const userId = 'default_user';
    
    const tabTitles = {
        'profile': '能力画像',
        'history': '训练历史',
        'assessment': '评估报告',
        'suggestions': '改进建议'
    };
    
    function initTabs() {
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const targetTab = tab.dataset.tab;
                
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                tabContents.forEach(content => {
                    content.classList.remove('active');
                    if (content.id === `${targetTab}-tab`) {
                        content.classList.add('active');
                    }
                });
                
                pageTitle.textContent = tabTitles[targetTab] || '能力画像';
            });
        });
    }
    
    function showToast(message) {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            padding: 15px 30px;
            background: #1B2559;
            color: white;
            border-radius: 10px;
            z-index: 1000;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        `;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    async function loadProfile() {
        try {
            const response = await fetch(`/api/evaluate/profile/${userId}`);
            const data = await response.json();
            
            if (data.success) {
                renderProfile(data.profile);
            } else {
                showToast('加载能力画像失败');
            }
        } catch (error) {
            console.error('Error loading profile:', error);
            showToast('加载失败，请重试');
        }
    }
    
    function renderProfile(profile) {
        document.getElementById('levelLabelText').textContent = profile.level || '入门';
        document.getElementById('levelText').textContent = profile.level || '入门';
        
        const score = profile.overall_score || 0;
        document.getElementById('overallScore').textContent = Math.round(score);
        
        const circumference = 2 * Math.PI * 90;
        const offset = circumference - (score / 100) * circumference;
        const scoreCircle = document.getElementById('scoreCircle');
        scoreCircle.style.strokeDasharray = circumference;
        scoreCircle.style.strokeDashoffset = offset;
        
        document.getElementById('trainingCount').textContent = profile.training_count || 0;
        document.getElementById('totalDuration').textContent = Math.round((profile.total_duration || 0) / 60);
        
        renderRadarChart(profile.dimension_scores);
        
        const strengthsList = document.getElementById('strengthsList');
        const weaknessesList = document.getElementById('weaknessesList');
        
        strengthsList.innerHTML = (profile.strong_points || [])
            .map(p => `<div class="list-item strength"><p>${p}</p></div>`)
            .join('') || '<div class="list-item"><p>暂无数据</p></div>';
        
        weaknessesList.innerHTML = (profile.weak_points || [])
            .map(p => `<div class="list-item weakness"><p>${p}</p></div>`)
            .join('') || '<div class="list-item"><p>暂无数据</p></div>';
    }
    
    function renderRadarChart(scores) {
        const ctx = document.getElementById('radarChart').getContext('2d');
        
        if (radarChart) {
            radarChart.destroy();
        }
        
        const labels = ['沟通技巧', '产品知识', '需求挖掘', '异议处理', '促成技巧'];
        const data = labels.map(label => scores[label] || 0);
        
        radarChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: labels,
                datasets: [{
                    label: '能力得分',
                    data: data,
                    backgroundColor: 'rgba(67, 24, 255, 0.1)',
                    borderColor: 'rgba(67, 24, 255, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(67, 24, 255, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(67, 24, 255, 1)',
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20,
                            font: { size: 10 },
                            color: '#707EAE'
                        },
                        grid: {
                            color: '#E0E5F2'
                        },
                        angleLines: {
                            color: '#E0E5F2'
                        },
                        pointLabels: {
                            font: { size: 12, weight: '500' },
                            color: '#1B2559'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    async function loadHistory() {
        try {
            const response = await fetch(`/api/evaluate/history/${userId}`);
            const data = await response.json();
            
            if (data.success) {
                renderHistory(data.history);
                renderTrendChart(data.history);
                populateSessionSelect(data.history);
            } else {
                showToast('加载训练历史失败');
            }
        } catch (error) {
            console.error('Error loading history:', error);
            showToast('加载失败，请重试');
        }
    }
    
    function renderHistory(history) {
        const container = document.getElementById('historyList');
        
        if (!history || history.length === 0) {
            container.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 40px; color: #707EAE;">暂无训练记录</td></tr>';
            return;
        }
        
        container.innerHTML = history.map(item => {
            const statusClass = item.score >= 80 ? 'high' : item.score >= 60 ? 'medium' : 'low';
            const statusText = item.score >= 80 ? '优秀' : item.score >= 60 ? '良好' : '待提升';
            
            return `
                <tr data-session-id="${item.session_id}">
                    <td>${item.industry} - ${item.role}</td>
                    <td>${item.date}</td>
                    <td>${Math.round(item.duration / 60)} 分钟</td>
                    <td style="font-weight: 700; color: #4318FF;">${item.score}</td>
                    <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                </tr>
            `;
        }).join('');
        
        container.querySelectorAll('tr').forEach(row => {
            row.addEventListener('click', () => {
                const sessionId = row.dataset.sessionId;
                if (sessionId) {
                    loadAssessment(sessionId);
                    
                    tabs.forEach(t => t.classList.remove('active'));
                    document.querySelector('[data-tab="assessment"]').classList.add('active');
                    tabContents.forEach(c => c.classList.remove('active'));
                    document.getElementById('assessment-tab').classList.add('active');
                    pageTitle.textContent = '评估报告';
                }
            });
        });
    }
    
    function renderTrendChart(history) {
        const ctx = document.getElementById('trendChart').getContext('2d');
        
        if (trendChart) {
            trendChart.destroy();
        }
        
        if (!history || history.length === 0) {
            return;
        }
        
        const sortedHistory = [...history].reverse();
        
        trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: sortedHistory.map(h => h.date),
                datasets: [{
                    label: '得分',
                    data: sortedHistory.map(h => h.score),
                    borderColor: 'rgba(67, 24, 255, 1)',
                    backgroundColor: 'rgba(67, 24, 255, 0.1)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: '#F4F7FE' },
                        ticks: { color: '#707EAE' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#707EAE' }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    function populateSessionSelect(history) {
        const select = document.getElementById('sessionSelect');
        
        select.innerHTML = '<option value="">请选择...</option>' +
            history.map(item => `
                <option value="${item.session_id}">
                    ${item.industry} - ${item.role} (${item.date})
                </option>
            `).join('');
    }
    
    async function loadAssessment(sessionId) {
        if (!sessionId) {
            document.getElementById('assessmentReport').style.display = 'none';
            return;
        }
        
        try {
            const response = await fetch(`/api/evaluate/assessment/${sessionId}`);
            const data = await response.json();
            
            if (data.success) {
                renderAssessment(data.assessment);
                document.getElementById('assessmentReport').style.display = 'block';
            } else {
                showToast('加载评估报告失败');
            }
        } catch (error) {
            console.error('Error loading assessment:', error);
            showToast('加载失败，请重试');
        }
    }
    
    function renderAssessment(assessment) {
        document.getElementById('reportTitle').textContent = `${assessment.industry || ''} - ${assessment.role || ''} 评估报告`;
        document.getElementById('reportDate').textContent = assessment.date || '';
        document.getElementById('reportDuration').textContent = `时长: ${Math.round(assessment.duration_seconds / 60)} 分钟`;
        document.getElementById('reportScore').textContent = assessment.overall_score;
        
        const dimensionsContainer = document.getElementById('reportDimensions');
        dimensionsContainer.innerHTML = assessment.dimension_scores.map(dim => {
            const barColor = dim.score >= 80 ? '#05CD99' : 
                            dim.score >= 60 ? '#4318FF' : 
                            dim.score >= 40 ? '#FFB547' : '#EE5D50';
            
            return `
                <div class="dimension-row">
                    <span class="dimension-label">${dim.dimension}</span>
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill" style="width: ${dim.score}%; background: ${barColor};"></div>
                    </div>
                    <span class="dimension-value">${dim.score}</span>
                </div>
                <p style="font-size: 12px; color: #707EAE; margin-bottom: 16px; padding-left: 102px;">${dim.reason}</p>
            `;
        }).join('');
        
        document.getElementById('reportHighlights').innerHTML = 
            assessment.highlights.map(h => `<li style="margin-bottom: 8px;">${h}</li>`).join('');
        
        document.getElementById('reportImprovements').innerHTML = 
            assessment.improvements.map(i => `<li style="margin-bottom: 8px;">${i}</li>`).join('');
        
        document.getElementById('reportGolden').innerHTML = 
            assessment.golden_sentences.map(s => `
                <div style="background: #F8FAFC; padding: 14px 16px; border-radius: 10px; margin-bottom: 10px; border-left: 3px solid #4318FF; font-style: italic; color: #1B2559; font-size: 14px;">
                    "${s}"
                </div>
            `).join('');
        
        document.getElementById('reportMoments').innerHTML = 
            assessment.key_moments.map(m => {
                const badgeClass = m.handling === '较好' ? 'high' : 
                                  m.handling === '一般' ? 'medium' : 'low';
                return `
                    <div style="display: flex; gap: 12px; padding: 14px 16px; background: #F8FAFC; border-radius: 10px; margin-bottom: 10px; align-items: flex-start;">
                        <span class="status-badge ${badgeClass}" style="white-space: nowrap; flex-shrink: 0;">${m.type}</span>
                        <div style="flex: 1;">
                            <p style="color: #1B2559; margin-bottom: 5px; font-size: 14px;">${m.content}</p>
                            ${m.suggestion ? `<p style="font-size: 13px; color: #707EAE;">建议: ${m.suggestion}</p>` : ''}
                        </div>
                    </div>
                `;
            }).join('');
    }
    
    document.getElementById('sessionSelect').addEventListener('change', function() {
        loadAssessment(this.value);
    });
    
    document.getElementById('generateSuggestions').addEventListener('click', async function() {
        const btn = this;
        btn.disabled = true;
        btn.textContent = '生成中...';
        
        try {
            const response = await fetch(`/api/evaluate/suggestions/${userId}`, {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                renderSuggestions(data.suggestions);
                document.getElementById('suggestionsContent').style.display = 'block';
            } else {
                showToast('生成建议失败');
            }
        } catch (error) {
            console.error('Error generating suggestions:', error);
            showToast('生成失败，请重试');
        } finally {
            btn.disabled = false;
            btn.textContent = '生成个性化学习建议';
        }
    });
    
    function renderSuggestions(suggestions) {
        document.getElementById('priorityArea').textContent = suggestions.priority || '暂无';
        
        const learningPathContainer = document.getElementById('learningPath');
        if (suggestions.learning_path && suggestions.learning_path.length > 0) {
            learningPathContainer.innerHTML = suggestions.learning_path.map(step => `
                <div class="suggestion-card">
                    <div class="suggestion-header">
                        <span class="step-circle">${step.step}</span>
                        <span class="suggestion-title">${step.action}</span>
                    </div>
                    <div class="suggestion-body">
                        资源: ${step.resource} · 预计时间: ${step.estimated_time}
                    </div>
                </div>
            `).join('');
        } else {
            learningPathContainer.innerHTML = '<p style="color: #707EAE;">暂无学习路径</p>';
        }
        
        const practiceContainer = document.getElementById('practiceScenarios');
        if (suggestions.practice_scenarios && suggestions.practice_scenarios.length > 0) {
            practiceContainer.innerHTML = suggestions.practice_scenarios
                .map(s => `<span style="display: inline-block; padding: 8px 14px; background: rgba(67, 24, 255, 0.1); border-radius: 20px; font-size: 13px; color: #4318FF; font-weight: 500;">${s}</span>`)
                .join('');
        } else {
            practiceContainer.innerHTML = '<p style="color: #707EAE;">暂无推荐场景</p>';
        }
        
        const keyPointsList = document.getElementById('keyPoints');
        if (suggestions.key_points && suggestions.key_points.length > 0) {
            keyPointsList.innerHTML = suggestions.key_points
                .map(p => `<li style="margin-bottom: 8px;">${p}</li>`)
                .join('');
        } else {
            keyPointsList.innerHTML = '<li>暂无关键要点</li>';
        }
    }
    
    document.getElementById('industryFilter').addEventListener('change', function() {
        const industry = this.value;
        filterHistory(industry);
    });
    
    async function filterHistory(industry) {
        try {
            const url = industry 
                ? `/api/evaluate/history/${userId}?industry=${encodeURIComponent(industry)}`
                : `/api/evaluate/history/${userId}`;
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.success) {
                renderHistory(data.history);
            }
        } catch (error) {
            console.error('Error filtering history:', error);
        }
    }
    
    initTabs();
    loadProfile();
    loadHistory();
});
