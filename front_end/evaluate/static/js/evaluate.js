document.addEventListener('DOMContentLoaded', function() {
    const tabs = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    let radarChart = null;
    let trendChart = null;
    
    const userId = 'default_user';
    
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
            });
        });
    }
    
    function showToast(message) {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
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
        const levelIcons = {
            '入门': '🌱',
            '进阶': '🌿',
            '熟练': '🌳',
            '专家': '🏆'
        };
        
        document.getElementById('levelBadge').innerHTML = `
            <span class="level-icon">${levelIcons[profile.level] || '🌱'}</span>
            <span class="level-text">${profile.level}</span>
        `;
        
        const score = profile.overall_score || 0;
        document.getElementById('overallScore').textContent = Math.round(score);
        
        const circumference = 2 * Math.PI * 45;
        const offset = circumference - (score / 100) * circumference;
        const scoreCircle = document.getElementById('scoreCircle');
        scoreCircle.style.strokeDashoffset = offset;
        
        document.getElementById('trainingCount').textContent = profile.training_count || 0;
        document.getElementById('totalDuration').textContent = Math.round((profile.total_duration || 0) / 60);
        
        renderDimensionBars(profile.dimension_scores);
        renderRadarChart(profile.dimension_scores);
        
        const strengthsList = document.getElementById('strengthsList');
        const weaknessesList = document.getElementById('weaknessesList');
        
        strengthsList.innerHTML = (profile.strong_points || [])
            .map(p => `<li>${p}</li>`)
            .join('') || '<li>暂无数据</li>';
        
        weaknessesList.innerHTML = (profile.weak_points || [])
            .map(p => `<li>${p}</li>`)
            .join('') || '<li>暂无数据</li>';
    }
    
    function renderDimensionBars(scores) {
        const container = document.getElementById('dimensionBars');
        const dimensions = ['沟通技巧', '产品知识', '需求挖掘', '异议处理', '促成技巧'];
        
        container.innerHTML = dimensions.map(dim => {
            const score = scores[dim] || 0;
            const levelClass = score >= 80 ? 'excellent' : 
                              score >= 60 ? 'good' : 
                              score >= 40 ? 'average' : 'weak';
            
            return `
                <div class="dimension-bar">
                    <span class="dimension-name">${dim}</span>
                    <div class="dimension-progress">
                        <div class="dimension-fill ${levelClass}" style="width: ${score}%"></div>
                    </div>
                    <span class="dimension-score-text">${Math.round(score)}</span>
                </div>
            `;
        }).join('');
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
                    backgroundColor: 'rgba(102, 126, 234, 0.2)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(102, 126, 234, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(102, 126, 234, 1)'
                }]
            },
            options: {
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20
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
            container.innerHTML = '<div class="loading">暂无训练记录</div>';
            return;
        }
        
        container.innerHTML = history.map(item => `
            <div class="history-item" data-session-id="${item.session_id}">
                <div class="history-info">
                    <span class="history-title">${item.industry} - ${item.role}</span>
                    <span class="history-meta">${item.date} · ${Math.round(item.duration / 60)}分钟</span>
                </div>
                <span class="history-score">${item.score}</span>
            </div>
        `).join('');
        
        container.querySelectorAll('.history-item').forEach(item => {
            item.addEventListener('click', () => {
                const sessionId = item.dataset.sessionId;
                loadAssessment(sessionId);
                
                tabs.forEach(t => t.classList.remove('active'));
                document.querySelector('[data-tab="assessment"]').classList.add('active');
                tabContents.forEach(c => c.classList.remove('active'));
                document.getElementById('assessment-tab').classList.add('active');
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
                    borderColor: 'rgba(102, 126, 234, 1)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
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
        document.getElementById('reportScore').textContent = assessment.overall_score;
        document.getElementById('reportDuration').textContent = 
            `时长: ${Math.round(assessment.duration_seconds / 60)}分钟`;
        
        const dimensionsContainer = document.getElementById('reportDimensions');
        dimensionsContainer.innerHTML = assessment.dimension_scores.map(dim => {
            const levelClass = dim.score >= 80 ? 'excellent' : 
                              dim.score >= 60 ? 'good' : 
                              dim.score >= 40 ? 'average' : 'weak';
            const barColor = dim.score >= 80 ? '#28a745' : 
                            dim.score >= 60 ? '#17a2b8' : 
                            dim.score >= 40 ? '#ffc107' : '#dc3545';
            
            return `
                <div class="dimension-item">
                    <div class="dimension-header">
                        <span class="dimension-name-text">${dim.dimension}</span>
                        <span class="dimension-score-badge">${dim.score}分</span>
                    </div>
                    <div class="dimension-bar-container">
                        <div class="dimension-bar-fill" style="width: ${dim.score}%; background: ${barColor}"></div>
                    </div>
                    <p class="dimension-reason">${dim.reason}</p>
                </div>
            `;
        }).join('');
        
        document.getElementById('reportHighlights').innerHTML = 
            assessment.highlights.map(h => `<li>${h}</li>`).join('');
        
        document.getElementById('reportImprovements').innerHTML = 
            assessment.improvements.map(i => `<li>${i}</li>`).join('');
        
        document.getElementById('reportGolden').innerHTML = 
            assessment.golden_sentences.map(s => `<div class="golden-quote">"${s}"</div>`).join('');
        
        document.getElementById('reportMoments').innerHTML = 
            assessment.key_moments.map(m => {
                const badgeClass = m.handling === '较好' ? 'good' : 
                                  m.handling === '一般' ? 'average' : 'poor';
                return `
                    <div class="moment-item">
                        <span class="moment-badge ${badgeClass}">${m.type}</span>
                        <div class="moment-content">
                            <p class="moment-text">${m.content}</p>
                            ${m.suggestion ? `<p class="moment-suggestion">建议: ${m.suggestion}</p>` : ''}
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
                <div class="learning-step">
                    <span class="step-number">${step.step}</span>
                    <div class="step-content">
                        <h5>${step.action}</h5>
                        <p>资源: ${step.resource} · 预计时间: ${step.estimated_time}</p>
                    </div>
                </div>
            `).join('');
        } else {
            learningPathContainer.innerHTML = '<p>暂无学习路径</p>';
        }
        
        const practiceContainer = document.getElementById('practiceScenarios');
        if (suggestions.practice_scenarios && suggestions.practice_scenarios.length > 0) {
            practiceContainer.innerHTML = suggestions.practice_scenarios
                .map(s => `<span class="practice-scenario">${s}</span>`)
                .join('');
        } else {
            practiceContainer.innerHTML = '<p>暂无推荐场景</p>';
        }
        
        const keyPointsList = document.getElementById('keyPoints');
        if (suggestions.key_points && suggestions.key_points.length > 0) {
            keyPointsList.innerHTML = suggestions.key_points
                .map(p => `<li>${p}</li>`)
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
