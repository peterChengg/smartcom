#!/bin/bash
# 提交前自动检查脚本
# 用于确保测试人员遵守开发规范

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 输出函数
print_error() {
    echo -e "${RED}错误: $1${NC}"
}

print_success() {
    echo -e "${GREEN}通过: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}警告: $1${NC}"
}

# 获取最新的提交信息
LATEST_COMMIT_MSG=$(git log -1 --pretty=format:"%s")
echo "检查最新提交信息: $LATEST_COMMIT_MSG"

# 1. 检查提交信息格式
check_commit_message() {
    echo "=== 检查提交信息格式 ==="
    
    # 检查是否包含测试人员标识
    if ! echo "$LATEST_COMMIT_MSG" | grep -q "^\[Test-"; then
        print_error "提交信息必须包含测试人员标识，格式: [Test-姓名] 类型: 描述"
        echo "示例: [Test-张三] test(feature): 添加登录功能的测试用例"
        exit 1
    fi
    
    # 检查提交类型
    if ! echo "$LATEST_COMMIT_MSG" | grep -q "\[Test-.\+\] \(test\|fix\|refactor\|doc\|style\|perf\)\("; then
        print_error "提交类型必须是以下之一: test, fix, refactor, doc, style, perf"
        exit 1
    fi
    
    print_success "提交信息格式正确"
}

# 2. 检查修改的文件权限
check_file_permissions() {
    echo "=== 检查文件修改权限 ==="
    
    # 获取最新提交修改的文件
    modified_files=$(git diff --name-only HEAD~1 HEAD)
    violation_files=()
    
    for file in $modified_files; do
        # 检查是否为禁止测试人员修改的目录
        if [[ $file =~ ^src/main/ ]] && [[ ! $file =~ test ]]; then
            violation_files+=("$file")
        elif [[ $file =~ ^src/core/business/ ]]; then
            violation_files+=("$file")
        elif [[ $file =~ ^src/config/production/ ]]; then
            violation_files+=("$file")
        elif [[ $file =~ ^src/database/ ]] && [[ ! $file =~ test ]]; then
            violation_files+=("$file")
        fi
    done
    
    if [ ${#violation_files[@]} -gt 0 ]; then
        print_error "测试人员禁止修改以下生产代码文件:"
        for file in "${violation_files[@]}"; do
            echo "  - $file"
        done
        echo "允许修改的目录: /tests/, /src/test/, /coverage_reports/, /docs/testing/"
        exit 1
    fi
    
    print_success "文件修改权限检查通过"
}

# 3. 检查测试覆盖率
check_test_coverage() {
    echo "=== 检查测试覆盖率 ==="
    
    # 检查是否有测试文件被修改
    has_test_changes=false
    modified_files=$(git diff --name-only HEAD~1 HEAD)
    
    for file in $modified_files; do
        if [[ $file =~ test ]] || [[ $file =~ spec ]]; then
            has_test_changes=true
            break
        fi
    done
    
    if [ "$has_test_changes" = true ]; then
        echo "检测到测试文件变更，运行覆盖率检查..."
        
        # 运行测试并生成覆盖率报告
        if ! python3 -m pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=80; then
            print_error "测试覆盖率不达标，要求覆盖率 ≥ 80%"
            echo "请检查缺失的测试用例，特别是边界值和异常场景"
            exit 1
        fi
        
        print_success "测试覆盖率达标"
    else
        print_warning "未检测到测试文件变更，跳过覆盖率检查"
    fi
}

# 4. 检查测试用例完整性标记
check_test_case_completeness() {
    echo "=== 检查测试用例完整性 ==="
    
    # 检查新增的测试文件是否包含覆盖率分析注释
    modified_files=$(git diff --name-only HEAD~1 HEAD)
    
    for file in $modified_files; do
        if [[ $file =~ ^tests/.*\.py$ ]] && [[ -f "$file" ]]; then
            # 检查是否包含覆盖分析注释
            if ! grep -q "# Coverage Analysis:" "$file"; then
                print_warning "测试文件 $file 缺少覆盖率分析注释"
                echo "建议在文件开头添加以下注释:"
                echo "# Coverage Analysis:"
                echo "# - [x] Normal flow testing"
                echo "# - [ ] Boundary value testing" 
                echo "# - [ ] Exception handling testing"
                echo "# - [ ] Performance testing"
            fi
        fi
    done
    
    print_success "测试用例完整性检查完成"
}

# 5. 检查代码质量
check_code_quality() {
    echo "=== 检查代码质量 ==="
    
    # 运行 flake8 检查
    if command -v flake8 &> /dev/null; then
        modified_files=$(git diff --name-only HEAD~1 HEAD -- '*.py')
        if [ -n "$modified_files" ]; then
            echo "运行 flake8 代码质量检查..."
            if ! flake8 $modified_files --max-line-length=88 --ignore=E731; then
                print_error "代码质量检查失败，请修复 flake8 报告的问题"
                exit 1
            fi
        fi
    fi
    
    # 运行 black 格式检查
    if command -v black &> /dev/null; then
        modified_files=$(git diff --name-only HEAD~1 HEAD -- '*.py')
        if [ -n "$modified_files" ]; then
            echo "运行 black 格式检查..."
            if ! black --check $modified_files; then
                print_error "代码格式不符合标准，请运行 black 格式化代码"
                exit 1
            fi
        fi
    fi
    
    print_success "代码质量检查通过"
}

# 6. 检查测试文档
check_test_documentation() {
    echo "=== 检查测试文档 ==="
    
    # 检查是否有新增功能但没有对应的测试文档
    if git log -1 --pretty=format:"%s" | grep -q "test(feature):"; then
        print_warning "检测到新增功能测试，建议同时更新测试文档"
        echo "请检查是否需要更新以下文档:"
        echo "  - docs/testing/test-cases.md"
        echo "  - docs/testing/coverage-matrix.md"
    fi
    
    print_success "测试文档检查完成"
}

# 7. 生成检查报告
generate_report() {
    echo "=== 生成检查报告 ==="
    
    REPORT_DIR="quality-reports"
    mkdir -p $REPORT_DIR
    
    REPORT_FILE="$REPORT_DIR/pre-commit-$(date +%Y%m%d-%H%M%S).md"
    
    cat > "$REPORT_FILE" << EOF
# 预提交检查报告

## 检查时间
- **时间**: $(date)
- **提交者**: $(git log -1 --pretty=format:"%an")
- **提交信息**: $(git log -1 --pretty=format:"%s")

## 检查项目
- [x] 提交信息格式
- [x] 文件修改权限
- [x] 测试覆盖率
- [x] 测试用例完整性
- [x] 代码质量
- [x] 测试文档

## 修改的文件
$(git diff --name-only HEAD~1 HEAD | sed 's/^/- /')

## 覆盖率统计
\`\`\`
$(python3 -m pytest tests/ --cov=src --cov-report=term-missing 2>/dev/null || echo "覆盖率统计生成失败")
\`\`\`

## 检查结果
✅ 所有检查通过，提交符合质量标准
EOF
    
    echo "检查报告已保存到: $REPORT_FILE"
}

# 主函数
main() {
    echo "开始预提交质量检查..."
    echo "========================================"
    
    check_commit_message
    check_file_permissions
    check_test_coverage
    check_test_case_completeness
    check_code_quality
    check_test_documentation
    generate_report
    
    echo "========================================"
    print_success "所有检查通过！提交符合质量标准。"
}

# 执行主函数
main