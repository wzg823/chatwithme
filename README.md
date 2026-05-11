# ChatWithMe 项目

小说创作 AI 助手

## 启动方法

### 后端 (FastAPI)

```bash
cd backend
set PYTHONPATH=.
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

或

```bash
cd backend
set PYTHONPATH=.
python -m app.main
```

- 端口: 8000
- API 地址: http://localhost:8000/api

### 前端 (Vue + Vite)

```bash
cd frontend
npm run dev
```

- 端口: 5175 (如被占用则自动切换)
- 访问地址: http://localhost:5175

## 关闭方法

### 停止后端

```bash
# 方式1: 查找进程并结束
netstat -ano | findstr ":8000"
taskkill /PID <进程ID> /F

# 方式2: 直接结束 python 进程
taskkill /IM python.exe /F
```

### 停止前端

```bash
# 查找 node 进程并结束
taskkill /IM node.exe /F
```

或直接关闭运行终端。

## 项目结构

```
CHATWITHME/
├── backend/          # FastAPI 后端
│   └── app/
│       ├── main.py          # 入口
│       ├── routers/          # API 路由
│       │   ├── chat.py
│       │   ├── novels.py
│       │   └── model_configs.py
│       └── models/          # 数据模型
├── frontend/         # Vue 前端
│   └── src/
│       ├── App.vue
│       └── stores/
│           └── chat.ts
└── docs.superpowers/   # 设计文档
```