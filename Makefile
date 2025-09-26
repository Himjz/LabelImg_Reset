# 基础配置
PROJECT_NAME := labelimg
PYTHON := python3.13
POETRY := poetry
SRC_DIR := src/labelimg
TEST_DIR := tests
DIST_DIR := dist

# 默认目标
.DEFAULT_GOAL := help

# 帮助信息
help:  ## 显示帮助信息
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# 环境管理
env:  ## 创建并配置虚拟环境
	$(POETRY) env use $(PYTHON)
	$(POETRY) install --no-root

update:  ## 更新依赖到最新兼容版本
	$(POETRY) update

clean-env:  ## 清理虚拟环境
	$(POETRY) env remove $(PYTHON)
	rm -rf .venv

# 开发工具
format:  ## 使用black和isort格式化代码
	$(POETRY) run black $(SRC_DIR) $(TEST_DIR)
	$(POETRY) run isort $(SRC_DIR) $(TEST_DIR)

lint:  ## 使用ruff和mypy检查代码
	$(POETRY) run ruff check $(SRC_DIR) $(TEST_DIR)
	$(POETRY) run mypy $(SRC_DIR)

check: format lint  ## 运行所有代码检查和格式化

# 测试
test:  ## 运行所有测试
	$(POETRY) run pytest $(TEST_DIR)

test-cov:  ## 运行测试并生成覆盖率报告
	$(POETRY) run pytest $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=html

# 构建与打包
build: check test  ## 构建项目分发包
	$(POETRY) build --format=wheel
	$(POETRY) build --format=sdist

install:  ## 本地安装项目
	$(POETRY) install

# 运行应用
run:  ## 直接运行应用
	$(POETRY) run labelimg

# 清理构建产物
clean:  ## 清理构建和测试产物
	rm -rf $(DIST_DIR)
	rm -rf build
	rm -rf *.egg-info
	rm -rf .coverage
	rm -rf htmlcov
	find . -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -exec rm -f {} +
	find . -name "*.pyo" -exec rm -f {} +

# 发布到PyPI
publish: build  ## 发布包到PyPI
	$(POETRY) publish

# 生成资源文件
resources:  ## 编译Qt资源文件
	$(POETRY) run pyside6-rcc $(SRC_DIR)/resources/resources.qrc -o $(SRC_DIR)/resources/resources_rc.py

.PHONY: help env update clean-env format lint check test test-cov build install run clean publish resources
