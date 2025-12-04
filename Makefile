# Makefile for blueflame-ai

# 变量定义
PROJECT_NAME = blueflame-ai
PORT = 8123
TMUX_SESSION = $(PROJECT_NAME)
VENV_PATH = .venv

# 默认目标
.PHONY: help
help: ## 显示帮助信息
	@echo "可用命令:"
	@echo "  up          - 使用tmux启动开发环境（推荐）"
	@echo "  down        - 停止tmux会话"
	@echo "  dev         - 本地开发模式启动"
	@echo "  restart     - 重启开发环境"
	@echo "  logs        - 查看服务日志"
	@echo "  shell       - 进入开发shell"
	@echo "  test        - 运行测试"
	@echo "  install     - 安装依赖"
	@echo "  help        - 显示此帮助信息"

# 使用tmux启动开发环境
.PHONY: up
up: ## 使用tmux启动开发环境（推荐）
	@echo "正在启动LangGraph开发环境..."
	@if tmux has-session -t $(TMUX_SESSION) 2>/dev/null; then \
		echo "❌ tmux会话 '$(TMUX_SESSION)' 已存在"; \
		echo "请先运行 'make down' 停止现有会话"; \
	else \
		tmux new-session -d -s $(TMUX_SESSION); \
		tmux send-keys -t $(TMUX_SESSION) "source $(VENV_PATH)/bin/activate" C-m; \
		tmux send-keys -t $(TMUX_SESSION) "export PYTHONPATH=$(PWD)" C-m; \
		tmux send-keys -t $(TMUX_SESSION) "langgraph dev --host 0.0.0.0 --port $(PORT) --no-browser" C-m; \
		echo "✅ LangGraph开发环境已启动！"; \
		echo "🌐 API访问地址: http://localhost:$(PORT)"; \
		echo "📊 Studio访问地址: http://localhost:$(PORT)"; \
		echo "📋 查看日志: make logs"; \
		echo "🛑 停止服务: make down"; \
		echo "💡 进入tmux会话: tmux attach -t $(TMUX_SESSION)"; \
		echo ""; \
		echo "💡 LangGraph开发模式特性："; \
		echo "   - 热重载：代码修改自动重启"; \
		echo "   - 调试支持：内置调试功能"; \
		echo "   - Studio集成：可直接访问Studio UI"; \
	fi

# 停止tmux会话
.PHONY: down
down: ## 停止tmux会话
	@echo "正在停止开发环境..."
	@if tmux has-session -t $(TMUX_SESSION) 2>/dev/null; then \
		tmux kill-session -t $(TMUX_SESSION); \
		echo "✅ 开发环境已停止"; \
	else \
		echo "❌ tmux会话 '$(TMUX_SESSION)' 不存在"; \
	fi

# 本地开发模式启动（前台运行）
.PHONY: dev
dev: ## 本地开发模式启动（前台运行）
	@echo "正在启动本地开发模式..."
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "❌ 虚拟环境不存在，请先运行 'make install'"; \
		exit 1; \
	fi
	source $(VENV_PATH)/bin/activate && \
	export PYTHONPATH=$(PWD) && \
	langgraph dev --host 0.0.0.0 --port $(PORT) --no-browser

# 重启开发环境
.PHONY: restart
restart: down up ## 重启开发环境
	@echo "开发环境已重启"

# 查看服务日志
.PHONY: logs
logs: ## 查看服务日志
	@if tmux has-session -t $(TMUX_SESSION) 2>/dev/null; then \
		tmux attach -t $(TMUX_SESSION); \
	else \
		echo "❌ tmux会话 '$(TMUX_SESSION)' 不存在"; \
		echo "请先运行 'make up' 启动开发环境"; \
	fi

# 进入开发shell
.PHONY: shell
shell: ## 进入开发shell
	@if tmux has-session -t $(TMUX_SESSION) 2>/dev/null; then \
		tmux new-window -t $(TMUX_SESSION); \
	else \
		echo "❌ tmux会话 '$(TMUX_SESSION)' 不存在"; \
		echo "请先运行 'make up' 启动开发环境"; \
	fi

# 安装依赖
.PHONY: install
install: ## 安装项目依赖
	@echo "正在安装项目依赖..."
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "创建虚拟环境..."; \
		python3 -m venv $(VENV_PATH); \
	fi
	@echo "激活虚拟环境并安装依赖..."
	$(VENV_PATH)/bin/pip install --upgrade pip
	$(VENV_PATH)/bin/pip install -e .
	@echo "✅ 依赖安装完成"

# 运行测试
.PHONY: test
test: ## 运行测试
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "❌ 虚拟环境不存在，请先运行 'make install'"; \
		exit 1; \
	fi
	$(VENV_PATH)/bin/python -m pytest

# 查看开发环境状态
.PHONY: status
status: ## 查看开发环境状态
	@echo "服务信息:"
	@echo "  项目名称: $(PROJECT_NAME)"
	@echo "  tmux会话: $(TMUX_SESSION)"
	@echo "  端口: $(PORT)"
	@echo "  访问地址: http://localhost:$(PORT)"
	@if tmux has-session -t $(TMUX_SESSION) 2>/dev/null; then \
		echo "  状态: 运行中"; \
		echo "  会话窗口数: $$(tmux display-message -p '#I' -t $(TMUX_SESSION):)"; \
	else \
		echo "  状态: 未运行"; \
	fi

# 安装开发依赖
.PHONY: install-dev
install-dev: install ## 安装开发依赖
	@echo "正在安装开发依赖..."
	$(VENV_PATH)/bin/pip install pytest pytest-cov black flake8 mypy
	@echo "✅ 开发依赖安装完成"