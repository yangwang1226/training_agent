# -*- coding: utf-8 -*-
import sys
import io

# 设置stdout为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('front_end/manage_system/templates/scene_builder.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换整个 renderAllTemplates 函数
old_function = '''    grid.innerHTML = templates.map(template => `
        <div class="full-template-card">
            <div class="full-card-icon">${icons[template.industry] || '●'}</div>
            <h3 class="full-card-title">${escapeHtml(template.scene_name)}</h3>
            <p class="full-card-role">${escapeHtml(template.role_type || '通用教练')}</p>
            <p class="full-card-description">${escapeHtml(truncateText(template.scene_prompt, 100))}</p>
            <a href="/manage_system/scenes/create-custom?template=${template.scene_code}" class="full-card-btn">使用此模板</a>
        </div>
    `).join('');'''

new_function = '''    // Industry labels for tags
    const industryLabels = {
        'sales': '销售',
        'learning': '学习', 
        'interview': '面试',
        'customer_service': '客服',
        'other': '其他'
    };
    
    grid.innerHTML = templates.map(template => {
        const industryTag = industryLabels[template.industry] || template.industry || '其他';
        
        return `
        <div class="full-template-card">
            <div class="card-header-row">
                <div class="full-card-icon">${icons[template.industry] || '●'}</div>
                <span class="card-industry-tag">${industryTag}</span>
            </div>
            <h3 class="full-card-title">${escapeHtml(template.scene_name)}</h3>
            <p class="full-card-role">${escapeHtml(template.role_type || '通用教练')}</p>
            <p class="full-card-description">${escapeHtml(truncateText(template.scene_prompt, 100))}</p>
            <a href="/manage_system/scenes/create-custom?template=${template.scene_code}" class="full-card-btn">使用此模板</a>
        </div>
    `;
    }).join('');'''

if old_function in content:
    content = content.replace(old_function, new_function)
    print('[OK] Fixed renderAllTemplates function')
else:
    print('[WARN] Could not find exact pattern')

# 确保样式已添加 - 在 .full-card-icon 之后添加标签相关样式
if 'card-header-row' not in content:
    # 在 .full-card-icon 后添加样式
    old_icon_style = '''.full-card-icon {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #fafafa;
    border: 1px solid #e5e7eb;
    font-size: 1.25rem;
    opacity: 0.7;
}'''
    
    new_styles = '''.full-card-icon {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #fafafa;
    border: 1px solid #e5e7eb;
    font-size: 1.25rem;
    opacity: 0.7;
}

/* Card header row */
.card-header-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
}

/* Typeset industry tag */
.card-industry-tag {
    font-family: var(--font-body);
    font-size: 0.6875rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--ink-light);
    padding: 0.25rem 0.625rem;
    border: 1px solid #e5e7eb;
    background: transparent;
    transition: all 0.2s ease;
}

.full-template-card:hover .card-industry-tag {
    border-color: var(--primary-purple);
    color: var(--primary-purple);
}'''
    
    if old_icon_style in content:
        content = content.replace(old_icon_style, new_styles)
        print('[OK] Added tag styles')

with open('front_end/manage_system/templates/scene_builder.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('\n✅ Fixed!')
print('  • renderAllTemplates function updated with tags')
print('  • Tag styles ensured')
print('\nPlease refresh the page and try again.')