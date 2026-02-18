"""配置检查脚本 - 验证配置文件和依赖是否正确"""
import sys
import yaml
from pathlib import Path


def check_config_file(config_path: str = "config.yaml") -> bool:
    """检查配置文件是否存在且格式正确"""
    print("=" * 50)
    print("检查配置文件...")
    print("=" * 50)
    
    if not Path(config_path).exists():
        print(f"❌ 配置文件不存在: {config_path}")
        print("💡 请复制 config.yaml.example 为 config.yaml 并填入配置信息")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print(f"✅ 配置文件存在: {config_path}")
        
        # 检查必需配置项
        required_configs = [
            ('dingtalk', 'app_key'),
            ('dingtalk', 'app_secret'),
            ('feishu', 'app_id'),
            ('feishu', 'app_secret'),
            ('feishu', 'app_token'),
            ('feishu', 'tables', 'main'),
        ]
        
        missing_configs = []
        for keys in required_configs:
            value = config
            path = []
            for key in keys:
                path.append(key)
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    missing_configs.append('.'.join(path))
                    break
        
        if missing_configs:
            print(f"❌ 缺少必需的配置项: {', '.join(missing_configs)}")
            return False
        
        # 检查配置值是否为占位符
        placeholder_values = []
        if config.get('dingtalk', {}).get('app_key') == 'your_dingtalk_app_key':
            placeholder_values.append('dingtalk.app_key')
        if config.get('dingtalk', {}).get('app_secret') == 'your_dingtalk_app_secret':
            placeholder_values.append('dingtalk.app_secret')
        if config.get('feishu', {}).get('app_id') == 'your_feishu_app_id':
            placeholder_values.append('feishu.app_id')
        if config.get('feishu', {}).get('app_secret') == 'your_feishu_app_secret':
            placeholder_values.append('feishu.app_secret')
        if config.get('feishu', {}).get('app_token') == 'your_bitable_app_token':
            placeholder_values.append('feishu.app_token')
        if config.get('feishu', {}).get('tables', {}).get('main') == 'tbl_main_table_id':
            placeholder_values.append('feishu.tables.main')
        
        if placeholder_values:
            print(f"⚠️  以下配置项仍使用占位符，请填写实际值:")
            for item in placeholder_values:
                print(f"   - {item}")
            return False
        
        print("✅ 配置文件格式正确，必需配置项已填写")
        return True
        
    except yaml.YAMLError as e:
        print(f"❌ 配置文件格式错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")
        return False


def check_dependencies() -> bool:
    """检查依赖包是否安装"""
    print("\n" + "=" * 50)
    print("检查依赖包...")
    print("=" * 50)
    
    required_packages = {
        'requests': 'HTTP请求库',
        'yaml': 'YAML配置文件解析',
        'dateutil': '日期时间处理',
        'tenacity': '重试机制'
    }
    
    missing_packages = []
    for package, description in required_packages.items():
        try:
            if package == 'yaml':
                __import__('yaml')
            elif package == 'dateutil':
                __import__('dateutil')
            else:
                __import__(package)
            print(f"✅ {package} - {description}")
        except ImportError:
            print(f"❌ {package} - {description} (未安装)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  缺少依赖包: {', '.join(missing_packages)}")
        print("💡 请运行: pip install -r requirements.txt")
        return False
    
    print("✅ 所有依赖包已安装")
    return True


def check_directories() -> bool:
    """检查必要的目录是否存在"""
    print("\n" + "=" * 50)
    print("检查目录结构...")
    print("=" * 50)
    
    required_dirs = ['logs']
    missing_dirs = []
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            missing_dirs.append(dir_name)
            print(f"❌ 目录不存在: {dir_name}")
        else:
            print(f"✅ 目录存在: {dir_name}")
    
    if missing_dirs:
        print(f"\n💡 正在创建缺失的目录...")
        for dir_name in missing_dirs:
            Path(dir_name).mkdir(parents=True, exist_ok=True)
            print(f"✅ 已创建: {dir_name}")
    
    return True


def check_code_modules() -> bool:
    """检查代码模块是否存在"""
    print("\n" + "=" * 50)
    print("检查代码模块...")
    print("=" * 50)
    
    required_modules = [
        'sync.py',
        'dingtalk_client.py',
        'data_processor.py',
        'checkpoint.py',
        'logger.py'
    ]
    
    missing_modules = []
    for module in required_modules:
        if Path(module).exists():
            print(f"✅ {module}")
        else:
            print(f"❌ {module} (不存在)")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n⚠️  缺少代码模块: {', '.join(missing_modules)}")
        return False
    
    print("✅ 所有代码模块存在")
    return True


def test_imports() -> bool:
    """测试模块导入"""
    print("\n" + "=" * 50)
    print("测试模块导入...")
    print("=" * 50)
    
    modules = [
        ('sync', '主同步程序'),
        ('dingtalk_client', '钉钉客户端'),
        ('data_processor', '数据处理器'),
        ('checkpoint', '检查点管理'),
        ('logger', '日志工具')
    ]
    
    import_errors = []
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"✅ {module_name} - {description}")
        except ImportError as e:
            print(f"❌ {module_name} - {description} (导入失败: {e})")
            import_errors.append(module_name)
        except Exception as e:
            print(f"⚠️  {module_name} - {description} (导入警告: {e})")
    
    if import_errors:
        print(f"\n⚠️  模块导入失败: {', '.join(import_errors)}")
        return False
    
    print("✅ 所有模块可以正常导入")
    return True


def main():
    """主函数"""
    print("\n")
    print("🔍 钉钉审批同步系统 - 配置检查工具")
    print("=" * 50)
    
    all_checks = []
    
    # 检查目录
    all_checks.append(check_directories())
    
    # 检查代码模块
    all_checks.append(check_code_modules())
    
    # 检查依赖
    all_checks.append(check_dependencies())
    
    # 测试导入
    all_checks.append(test_imports())
    
    # 检查配置（最后检查，因为需要先确保依赖安装）
    all_checks.append(check_config_file())
    
    print("\n" + "=" * 50)
    print("检查结果汇总")
    print("=" * 50)
    
    if all(all_checks):
        print("✅ 所有检查通过！系统已就绪")
        print("\n📝 下一步操作:")
        print("   1. 确保已填写 config.yaml 中的实际配置值")
        print("   2. 运行测试: python sync.py --init")
        return 0
    else:
        print("⚠️  部分检查未通过，请根据上述提示修复问题")
        print("\n📝 常见问题:")
        print("   1. 缺少依赖包: pip install -r requirements.txt")
        print("   2. 配置文件未填写: cp config.yaml.example config.yaml 然后编辑")
        return 1


if __name__ == '__main__':
    sys.exit(main())
