# Blueprint 重复注册问题修复

## 🐛 问题描述

**错误信息**:
```
ValueError: The name 'realtime' is already registered for this blueprint. 
Use 'name=' to provide a unique name.
```

**错误位置**: `routes/realtime_routes.py` 第 73 行

**堆栈跟踪**:
```
File "D:\workspace\training_agent\app.py", line 83, in <module>
    register_websocket(app, sock)
File "D:\workspace\training_agent\routes\realtime_routes.py", line 73, in register_websocket
    app.register_blueprint(realtime_bp)
```

## 🔍 问题分析

### 重复注册的原因

1. **第一次注册**: 在 `app.py` 中
   ```python
   app.register_blueprint(realtime_bp)  # 第 80 行
   ```

2. **第二次注册**: 在 `register_websocket` 函数中
   ```python
   def register_websocket(app, sock):
       app.register_blueprint(realtime_bp)  # 第 73 行 - 重复！
   ```

### Flask Blueprint 注册规则

- 每个 blueprint 在 Flask 应用中只能注册一次
- blueprint 的 `name` 参数必须唯一（默认为 `__name__`）
- 重复注册会抛出 `ValueError`

## ✅ 修复方案

### 方案 1: 移除函数内的注册（采用）

**修改 `routes/realtime_routes.py`**:

```python
# 修复前
def register_websocket(app, sock):
    app.register_blueprint(realtime_bp)  # ← 移除这行
    logger.info("Registered realtime blueprint")
    
    @sock.route('/api/realtime/ws/<scene_id>')
    def realtime_ws(ws, scene_id):
        # ...

# 修复后
def register_websocket(sock):
    """注册 WebSocket 路由"""
    logger.info("Registering WebSocket routes")
    
    @sock.route('/api/realtime/ws/<scene_id>')
    def realtime_ws(ws, scene_id):
        # ...
```

**修改 `app.py`**:

```python
# 修复前
register_websocket(app, sock)

# 修复后
register_websocket(sock)
```

### 方案 2: 移除 app.py 中的注册（不采用）

也可以移除 `app.py` 中的注册，只在 `register_websocket` 中注册。但这样不符合 Flask 最佳实践，因为：
- blueprint 的注册应该集中在 `app.py` 中
- 便于统一管理和查看

## 📊 修改文件清单

### 1. routes/realtime_routes.py

**修改内容**:
- ✅ 移除 `app.register_blueprint(realtime_bp)` 
- ✅ 修改函数签名：`register_websocket(sock)` 不再需要 `app` 参数
- ✅ 更新日志信息

**修复前**:
```python
def register_websocket(app, sock):
    app.register_blueprint(realtime_bp)
    logger.info("Registered realtime blueprint")
    
    @sock.route('/api/realtime/ws/<scene_id>')
```

**修复后**:
```python
def register_websocket(sock):
    """注册 WebSocket 路由"""
    logger.info("Registering WebSocket routes")
    
    @sock.route('/api/realtime/ws/<scene_id>')
```

### 2. app.py

**修改内容**:
- ✅ 更新函数调用：`register_websocket(sock)`

**修复前**:
```python
register_websocket(app, sock)
```

**修复后**:
```python
register_websocket(sock)
```

## 🎯 Blueprint 注册流程

### 正确的注册顺序

```python
# app.py

# 1. 创建 Flask 应用
app = Flask(__name__)
app.secret_key = 'your-secret-key'

# 2. 创建 Flask-Sock 实例
sock = Sock(app)

# 3. 注册所有 blueprint（HTTP 路由）
app.register_blueprint(scene_bp)
app.register_blueprint(scene_create_bp)
app.register_blueprint(prompt_bp)
app.register_blueprint(evaluate_bp)
app.register_blueprint(dimension_bp)
app.register_blueprint(progress_bp)
app.register_blueprint(realtime_bp)  # ← 只注册一次

# 4. 注册 WebSocket 路由（使用 sock 对象）
register_progress_websocket(sock)
register_websocket(sock)  # ← 只传入 sock，不再注册 blueprint

# 5. 启动应用
if __name__ == '__main__':
    app.run(debug=True)
```

### WebSocket 路由注册机制

```python
# routes/realtime_routes.py

# 1. 创建 blueprint（定义 HTTP 路由）
realtime_bp = Blueprint('realtime', __name__, ...)

@realtime_bp.route('/<scene_id>')
def index(scene_id):
    # HTTP 路由
    pass

# 2. 注册函数（定义 WebSocket 路由）
def register_websocket(sock):
    @sock.route('/api/realtime/ws/<scene_id>')
    def realtime_ws(ws, scene_id):
        # WebSocket 路由
        pass
```

## ✅ 测试验证

### 1. 启动应用
```bash
python app.py
```

**预期输出**:
```
Loaded .env from: ...
2026-03-05 14:25:00,000 - INFO - Registered realtime blueprint
2026-03-05 14:25:00,001 - INFO - Registering WebSocket routes
2026-03-05 14:25:00,002 - INFO - 评估服务初始化完成，使用模型：qwen3.5-flash
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://0.0.0.0:5000
```

### 2. 访问场景创建页面
```
http://localhost:5000/scene/create/
```

### 3. 完成场景保存并跳转
```
http://localhost:5000/realtime/5
```

### 4. 点击"开始对话"
**预期行为**:
- ✅ 不再报错
- ✅ WebSocket 连接成功
- ✅ 状态显示："已连接 - 正在录音"
- ✅ 可以正常语音对练

### 5. 检查日志
```
INFO - WebSocket connection for scene: 5, provider: qwen
INFO - Registered WebSocket routes
```

## 📝 最佳实践总结

### Blueprint 注册原则

1. **集中注册**: 在 `app.py` 中统一注册所有 blueprint
2. **单一职责**: blueprint 只负责 HTTP 路由
3. **分离关注**: WebSocket 路由通过 `sock` 对象单独注册

### 代码组织

```python
# app.py - 应用入口
- 创建 Flask 应用
- 配置 secret_key
- 创建 Flask-Sock 实例
- 注册所有 blueprint
- 注册 WebSocket 路由
- 启动应用

# routes/xxx.py - 路由模块
- 创建 Blueprint
- 定义 HTTP 路由
- 提供 register_websocket 函数（可选）

# 函数职责清晰
- register_websocket(sock): 只注册 WebSocket 路由
- 不再重复注册 blueprint
```

## 🎉 修复效果

### 修复前
```
❌ ValueError: The name 'realtime' is already registered
❌ 应用无法启动
❌ 无法进行语音对练
```

### 修复后
```
✅ 应用正常启动
✅ WebSocket 连接成功
✅ 可以正常语音对练
✅ 代码结构更清晰
```

## 📚 相关文档

- [Flask Blueprint 文档](https://flask.palletsprojects.com/en/2.3.x/blueprints/)
- [Flask-Sock 文档](https://github.com/nicknisi/flask-sock)
- [WebSocket 修复说明](WEBSOCKET_FIX.md)
- [场景创建使用指南](SCENE_CREATE_GUIDE.md)
