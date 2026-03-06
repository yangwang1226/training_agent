@echo off
echo ================================================
echo   场景智能体重构 - 快速启动脚本
echo ================================================
echo.

echo [1/3] 检查 Python 环境...
python --version
if errorlevel 1 (
    echo 错误：未找到 Python 环境，请先安装 Python 3.8+
    pause
    exit /b 1
)
echo Python 环境检查通过!
echo.

echo [2/3] 检查依赖包...
python -c "import flask, dashscope, langchain_core" 2>nul
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
) else (
    echo 依赖包检查通过!
)
echo.

echo [3/3] 启动 Flask 应用...
echo.
echo ================================================
echo   应用即将启动...
echo   访问地址：http://localhost:5000
echo   场景创建：http://localhost:5000/scene/create/
echo ================================================
echo.
echo 按 Ctrl+C 可停止应用
echo.

python app.py

pause
