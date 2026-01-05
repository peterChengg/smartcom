#!/usr/bin/env python3
"""
Validate development environment configuration for SmartCom.
"""

import os
import sys
import subprocess
from pathlib import Path


def check_dev_files():
    """Check that development files exist."""
    dev_files = [
        "setup_dev.sh",
        "CONTRIBUTING.md", 
        "DEVELOPMENT.md",
        ".github/workflows/ci.yml",
        ".github/workflows/code-quality.yml",
        ".vscode/settings.json",
        ".vscode/launch.json",
        ".vscode/tasks.json",
        ".editorconfig",
        ".pre-commit-config.yaml",
        ".env.example",
        "docs/README.md",
    ]
    
    print("🔍 Checking development files...")
    missing_files = []
    for file_path in dev_files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path}")
        else:
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing development files: {missing_files}")
        return False
    print("✅ All development files exist")
    return True


def check_scripts():
    """Check development scripts."""
    scripts = [
        "scripts/run_tests.sh",
        "scripts/run_lint.sh", 
        "scripts/format_code.sh",
        "scripts/clean.sh",
        "activate_dev.sh",
    ]
    
    print("\n🔍 Checking development scripts...")
    missing_scripts = []
    for script in scripts:
        if Path(script).exists():
            # Check if script is executable
            if os.access(script, os.X_OK):
                print(f"  ✅ {script} (executable)")
            else:
                print(f"  ⚠️  {script} (not executable)")
        else:
            missing_scripts.append(script)
    
    if missing_scripts:
        print(f"❌ Missing scripts: {missing_scripts}")
        return False
    print("✅ All development scripts exist")
    return True


def check_dev_configuration():
    """Check development configuration files."""
    print("\n🔍 Checking development configuration...")
    
    # Check .editorconfig
    if Path(".editorconfig").exists():
        with open(".editorconfig", 'r') as f:
            content = f.read()
            if "root = true" in content and "[*.py]" in content:
                print("  ✅ .editorconfig properly configured")
            else:
                print("  ⚠️  .editorconfig may be incomplete")
    else:
        print("  ❌ .editorconfig missing")
        return False
    
    # Check .vscode settings
    if Path(".vscode/settings.json").exists():
        print("  ✅ VS Code settings configured")
    else:
        print("  ❌ VS Code settings missing")
        return False
    
    # Check pre-commit config
    if Path(".pre-commit-config.yaml").exists():
        print("  ✅ Pre-commit hooks configured")
    else:
        print("  ❌ Pre-commit configuration missing")
        return False
    
    return True


def check_ci_cd():
    """Check CI/CD configuration."""
    print("\n🔍 Checking CI/CD configuration...")
    
    ci_files = [
        ".github/workflows/ci.yml",
        ".github/workflows/code-quality.yml"
    ]
    
    for ci_file in ci_files:
        if Path(ci_file).exists():
            print(f"  ✅ {ci_file}")
        else:
            print(f"  ❌ {ci_file} missing")
            return False
    
    return True


def check_documentation():
    """Check documentation structure."""
    print("\n🔍 Checking documentation structure...")
    
    doc_dirs = [
        "docs/api",
        "docs/user", 
        "docs/developer"
    ]
    
    for doc_dir in doc_dirs:
        if Path(doc_dir).exists():
            print(f"  ✅ {doc_dir}/")
        else:
            print(f"  ❌ {doc_dir}/ missing")
            return False
    
    # Check main documentation files
    if Path("docs/README.md").exists():
        print("  ✅ docs/README.md")
    else:
        print("  ❌ docs/README.md missing")
        return False
    
    return True


def check_dev_tools():
    """Check if development tools are available."""
    print("\n🔍 Checking development tools...")
    
    tools = {
        "python3": "Python 3",
        "pip3": "pip",
        "git": "Git",
    }
    
    missing_tools = []
    for tool, name in tools.items():
        try:
            result = subprocess.run([tool, "--version"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.split()[1] if len(result.stdout.split()) > 1 else "unknown"
                print(f"  ✅ {name} {version}")
            else:
                print(f"  ❌ {name} not working")
                missing_tools.append(tool)
        except FileNotFoundError:
            print(f"  ❌ {name} not found")
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"❌ Missing tools: {missing_tools}")
        return False
    
    return True


def test_setup_script():
    """Test setup script syntax."""
    print("\n🔍 Testing setup script syntax...")
    
    if Path("setup_dev.sh").exists():
        try:
            # Check script syntax
            result = subprocess.run(["bash", "-n", "setup_dev.sh"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("  ✅ setup_dev.sh syntax is valid")
            else:
                print(f"  ❌ setup_dev.sh syntax error: {result.stderr}")
                return False
        except Exception as e:
            print(f"  ❌ Error testing setup script: {e}")
            return False
    else:
        print("  ❌ setup_dev.sh not found")
        return False
    
    return True


def main():
    """Main validation function."""
    print("🚀 SmartCom Development Environment Validation\n")
    
    all_passed = True
    
    # Check all aspects
    if not check_dev_files():
        all_passed = False
        
    if not check_scripts():
        all_passed = False
        
    if not check_dev_configuration():
        all_passed = False
        
    if not check_ci_cd():
        all_passed = False
        
    if not check_documentation():
        all_passed = False
        
    if not check_dev_tools():
        all_passed = False
        
    if not test_setup_script():
        all_passed = False
    
    print(f"\n{'='*60}")
    if all_passed:
        print("🎉 All development environment checks passed! ✅")
        print("Development environment is properly configured.")
        print("\n📋 Next steps:")
        print("   1. Run './setup_dev.sh' to set up the environment")
        print("   2. Run 'source activate_dev.sh' to activate")
        print("   3. Start developing with SmartCom!")
        return 0
    else:
        print("❌ Some development environment checks failed!")
        print("Please fix the issues before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())