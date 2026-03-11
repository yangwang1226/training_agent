#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
部署检查脚本
验证 SOP 配置功能的所有文件是否正确部署
"""

import os
import sys
import io

# 设置标准输出编码为 UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ANSI 颜色代码
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓{RESET} {text}")

def print_error(text):
    print(f"{RED}✗{RESET} {text}")

def print_warning(text):
    print(f"{YELLOW}⚠{RESET} {text}")

def check_file_exists(filepath, description):
    """检查文件是否存在"""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print_success(f"{description}: {filepath} ({size} bytes)")
        return True
    else:
        print_error(f"{description}: {filepath} 不存在")
        return False

def check_file_content(filepath, search_text, description):
    """检查文件内容是否包含特定文本"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if search_text in content:
                print_success(f"{description}: 在 {filepath} 中找到")
                return True
            else:
                print_error(f"{description}: 在 {filepath} 中未找到")
                return False
    except Exception as e:
        print_error(f"{description}: 读取 {filepath} 失败 - {e}")
        return False

def main():
    print_header("SOP 配置功能部署检查")
    
    all_checks_passed = True
    
    # 1. 检查 HTML 模板
    print_header("1. 检查 HTML 模板文件")
    
    html_path = 'front_end/industry/templates/index.html'
    if check_file_exists(html_path, "主模板文件"):
        # 检查 CSS 引用
        check_file_content(html_path, 'sop_config_inline.css', "CSS 引用")
        # 检查 JS 引用
        check_file_content(html_path, 'sop_config_inline.js', "JS 引用")
        # 检查 SOP 配置模态框
        check_file_content(html_path, 'sop-config-modal-overlay', "SOP 配置模态框")
        # 检查是否有错误的字符
        if check_file_content(html_path, "'n", "检查是否有错误字符"):
            print_error("发现错误字符 'n，请检查模板")
            all_checks_passed = False
    else:
        all_checks_passed = False
    
    # 检查备份
    backup_path = 'front_end/industry/templates/index_backup.html'
    if os.path.exists(backup_path):
        print_success(f"备份文件存在: {backup_path}")
    else:
        print_warning("备份文件不存在，建议创建备份")
    
    # 2. 检查 CSS 文件
    print_header("2. 检查 CSS 样式文件")
    
    css_files = [
        ('front_end/industry/static/css/industry.css', '主样式文件'),
        ('front_end/industry/static/css/sop_config_inline.css', 'SOP 配置样式')
    ]
    
    for css_path, description in css_files:
        if not check_file_exists(css_path, description):
            all_checks_passed = False
    
    # 检查 SOP CSS 内容
    sop_css = 'front_end/industry/static/css/sop_config_inline.css'
    if os.path.exists(sop_css):
        check_file_content(sop_css, '.sop-config-modal', "模态框样式")
        check_file_content(sop_css, '.sop-tab', "Tab 样式")
        check_file_content(sop_css, '.extract-upload-area', "上传区域样式")
    
    # 3. 检查 JS 文件
    print_header("3. 检查 JavaScript 文件")
    
    js_files = [
        ('front_end/industry/static/js/industry.js', '主 JS 文件'),
        ('front_end/industry/static/js/sop_config_inline.js', 'SOP 配置 JS')
    ]
    
    for js_path, description in js_files:
        if not check_file_exists(js_path, description):
            all_checks_passed = False
    
    # 检查 industry.js 修复
    industry_js = 'front_end/industry/static/js/industry.js'
    if os.path.exists(industry_js):
        check_file_content(industry_js, 'openBackgroundModal', "函数定义")
        check_file_content(industry_js, 'loadSopPreview', "SOP 预览加载函数")
        check_file_content(industry_js, "getElementById('bgSopBtnConfig')", "SOP 按钮事件")
    
    # 检查 sop_config_inline.js 内容
    sop_js = 'front_end/industry/static/js/sop_config_inline.js'
    if os.path.exists(sop_js):
        check_file_content(sop_js, 'openSopConfigModal', "打开模态框函数")
        check_file_content(sop_js, 'performSmartExtraction', "智能提取函数")
        check_file_content(sop_js, 'saveSopItems', "保存函数")
    
    # 4. 检查后端 API
    print_header("4. 检查后端 API 路由")
    
    routes_path = 'routes/sop_routes.py'
    if check_file_exists(routes_path, "SOP 路由文件"):
        check_file_content(routes_path, '/save-checklist', "保存质检项接口")
        check_file_content(routes_path, '/extract-from-text', "文字提取接口")
        check_file_content(routes_path, '/extract-from-audio', "音频提取接口")
    else:
        all_checks_passed = False
    
    # 5. 检查数据库 DAO
    print_header("5. 检查数据库访问层")
    
    dao_path = 'database/sop_dao.py'
    if check_file_exists(dao_path, "SOP DAO 文件"):
        check_file_content(dao_path, 'get_scene_sop_checklist', "获取质检项函数")
        check_file_content(dao_path, 'update_scene_sop_checklist', "更新质检项函数")
    else:
        print_warning("DAO 文件不存在，可能需要创建")
    
    # 6. 检查文档
    print_header("6. 检查文档文件")
    
    docs = [
        ('SOP_CONFIG_REDESIGN.md', '设计方案文档'),
        ('IMPLEMENTATION_CHECKLIST.md', '实施检查清单'),
    ]
    
    for doc_path, description in docs:
        check_file_exists(doc_path, description)
    
    # 7. 检查测试文件
    print_header("7. 检查测试文件")
    
    test_files = [
        ('test_sop_integration.py', 'API 集成测试'),
        ('front_end/industry/static/test_sop_modal.html', '前端模态框测试')
    ]
    
    for test_path, description in test_files:
        check_file_exists(test_path, description)
    
    # 总结
    print_header("部署检查总结")
    
    if all_checks_passed:
        print_success("✅ 所有关键文件检查通过！")
        print("\n下一步操作：")
        print("1. 启动服务器: python app.py")
        print("2. 访问测试页面: http://localhost:5000/industry/static/test_sop_modal.html")
        print("3. 运行 API 测试: python test_sop_integration.py")
        print("4. 访问主页面: http://localhost:5000/industry/")
        return 0
    else:
        print_error("❌ 部分检查未通过，请检查上述错误")
        return 1

if __name__ == '__main__':
    sys.exit(main())