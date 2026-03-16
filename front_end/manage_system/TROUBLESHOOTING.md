# 🔧 故障排查指南

## 快速检查清单

### 1. 检查应用是否正常启动

```bash
# 启动应用
python app.py

# 应该看到类似输出：
# * Running on http://127.0.0.1:5000
# * Debug mode: on/off
```

### 2. 检查路由是否注册

访问以下URL，确认每个都能正常访问：

- ✅ 主页: `http://localhost:5000/manage_system/`
- ✅ 场景管理: `http://localhost:5000/manage_system/scenes`
- ✅ API测试: `http://localhost:5000/manage_system/api/scenes`

### 3. 检查静态资源

在浏览器开发者工具（F12）-> Network 标签中，确认以下资源加载成功：

- CSS: `/manage_system/static/css/scenes.css`
- JS: `/manage_system/static/js/scenes.js`

如果显示 404，检查文件路径是否正确。

### 4. 检查数据库

```bash
# 查看场景表数据
sqlite3 ai_coach.db "SELECT id, scene_name, status FROM scenes WHERE deleted_at IS NULL LIMIT 5;"
```

## 常见错误及解决方案

### 错误 1: 页面显示空白

**症状**: 访问 `/manage_system/scenes` 显示空白页面

**排查步骤**:
1. 打开浏览器控制台（F12）
2. 查看 Console 标签是否有 JavaScript 错误
3. 查看 Network 标签，API 请求是否成功

**解决方案**:
```javascript
// 在 scenes.js 中添加调试日志
console.log('Scenes page loaded');

async function loadScenes() {
    console.log('Loading scenes...');
    try {
        const response = await fetch('/manage_system/api/scenes');
        console.log('Response:', response);
        const data = await response.json();
        console.log('Data:', data);
    } catch (error) {
        console.error('Error:', error);
    }
}
```

### 错误 2: API 返回 500 错误

**症状**: 浏览器控制台显示 500 Internal Server Error

**排查步骤**:
1. 查看后端控制台的错误日志
2. 检查数据库连接是否正常

**解决方案**:
```bash
# 检查数据库文件是否存在
ls -l ai_coach.db

# 检查数据库是否可读写
sqlite3 ai_coach.db "SELECT 1;"
```

### 错误 3: 静态资源 404

**症状**: CSS 或 JS 文件加载失败

**解决方案**:
```python
# 在 manage_routes.py 中检查静态文件路由
@manage_bp.route('/static/<path:filename>')
def manage_static(filename):
    static_dir = Path(__file__).parent.parent / 'front_end' / 'manage_system' / 'static'
    print(f"Static file requested: {filename}")
    print(f"Static dir: {static_dir}")
    print(f"File exists: {(static_dir / filename).exists()}")
    return send_from_directory(static_dir, filename)
```

### 错误 4: 场景列表不显示

**症状**: 页面加载成功，但场景列表为空

**排查步骤**:
1. 检查 API 是否返回数据
2. 检查前端 JavaScript 是否正确处理数据

**测试 API**:
```bash
# 使用 curl 测试 API
curl http://localhost:5000/manage_system/api/scenes

# 或使用 Python
python -c "import requests; print(requests.get('http://localhost:5000/manage_system/api/scenes').json())"
```

### 错误 5: 点击按钮无反应

**症状**: 创建场景、删除等按钮点击后无反应

**解决方案**:
```javascript
// 检查函数是否定义
console.log('createScene function:', typeof createScene);
console.log('deleteScene function:', typeof deleteScene);

// 检查事件绑定
document.querySelector('.btn-primary').addEventListener('click', function() {
    console.log('Button clicked!');
    createScene();
});
```

## 完整测试脚本

创建 `test_manage_system.py`:

```python
#!/usr/bin/env python3
"""后台管理系统测试脚本"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_page_access():
    """测试页面访问"""
    print("\n=== 测试 1: 页面访问 ===")
    
    pages = {
        "仪表盘": "/manage_system/",
        "场景管理": "/manage_system/scenes"
    }
    
    for name, path in pages.items():
        try:
            response = requests.get(f"{BASE_URL}{path}")
            status = "✓" if response.status_code == 200 else "✗"
            print(f"{status} {name}: {response.status_code}")
        except Exception as e:
            print(f"✗ {name}: {e}")

def test_api_scenes():
    """测试场景列表 API"""
    print("\n=== 测试 2: 场景列表 API ===")
    
    try:
        response = requests.get(f"{BASE_URL}/manage_system/api/scenes")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"返回数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if data.get('success'):
                scenes = data.get('data', [])
                print(f"✓ 场景数量: {len(scenes)}")
                
                if scenes:
                    print(f"✓ 第一个场景: {scenes[0].get('scene_name')}")
            else:
                print(f"✗ API 返回失败: {data.get('message')}")
        else:
            print(f"✗ HTTP 错误: {response.status_code}")
            print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"✗ 请求异常: {e}")

def test_api_stats():
    """测试统计 API"""
    print("\n=== 测试 3: 统计 API ===")
    
    try:
        response = requests.get(f"{BASE_URL}/manage_system/api/stats/overview")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"统计数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"✗ HTTP 错误: {response.status_code}")
    except Exception as e:
        print(f"✗ 请求异常: {e}")

def test_static_files():
    """测试静态文件"""
    print("\n=== 测试 4: 静态文件 ===")
    
    files = [
        "/manage_system/static/css/scenes.css",
        "/manage_system/static/js/scenes.js",
        "/manage_system/static/css/common.css",
        "/manage_system/static/js/common.js"
    ]
    
    for file in files:
        try:
            response = requests.get(f"{BASE_URL}{file}")
            status = "✓" if response.status_code == 200 else "✗"
            print(f"{status} {file}: {response.status_code}")
        except Exception as e:
            print(f"✗ {file}: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("AI教练后台管理系统 - 测试脚本")
    print("=" * 60)
    
    test_page_access()
    test_api_scenes()
    test_api_stats()
    test_static_files()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
```

## 使用方法

```bash
# 1. 确保应用正在运行
python app.py

# 2. 在另一个终端运行测试
python test_manage_system.py
```

## 日志调试

在 `manage_routes.py` 中添加详细日志：

```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@manage_bp.route('/api/scenes', methods=['GET'])
def get_scenes_api():
    logger.info("接收到场景列表请求")
    try:
        scenes = list_scenes()
        logger.info(f"查询到 {len(scenes)} 个场景")
        logger.debug(f"场景数据: {scenes}")
        
        return jsonify({
            'success': True,
            'data': scenes
        })
    except Exception as e:
        logger.error(f"获取场景列表失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
```

## 性能检查

```javascript
// 在 scenes.js 中添加性能监控
console.time('loadScenes');
await loadScenes();
console.timeEnd('loadScenes');

console.time('renderTable');
renderScenesTable(scenes);
console.timeEnd('renderTable');
```

## 数据验证

```python
# 验证数据库中的场景数据
import sqlite3

conn = sqlite3.connect('ai_coach.db')
cursor = conn.cursor()

# 检查场景总数
cursor.execute("SELECT COUNT(*) FROM scenes WHERE deleted_at IS NULL")
print(f"总场景数: {cursor.fetchone()[0]}")

# 检查各状态场景数
for status in [0, 1, 2]:
    cursor.execute("SELECT COUNT(*) FROM scenes WHERE status = ? AND deleted_at IS NULL", (status,))
    count = cursor.fetchone()[0]
    status_name = {0: '草稿', 1: '预设', 2: '自定义'}[status]
    print(f"{status_name}场景数: {count}")

conn.close()
```

## 需要帮助？

如果以上方法都无法解决问题，请提供：

1. **错误日志**: 完整的后端控制台输出
2. **浏览器控制台**: Console 和 Network 标签的截图
3. **环境信息**: Python 版本、操作系统、浏览器版本
4. **复现步骤**: 详细的操作步骤

然后联系技术支持或提交 Issue。
```