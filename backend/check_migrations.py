import os
import importlib.util

def load_migration_module(file_path):
    """加载迁移模块"""
    module_name = os.path.basename(file_path)[:-3]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def check_migrations():
    """检查迁移版本依赖关系"""
    versions_dir = 'open_webui/migrations/versions'
    
    # 存储所有版本
    versions = {}
    # 存储指向各版本的其他版本
    dependencies = {}
    
    # 加载所有版本信息
    for f in os.listdir(versions_dir):
        if f.endswith('.py') and not f.startswith('__'):
            file_path = os.path.join(versions_dir, f)
            module = load_migration_module(file_path)
            
            revision = module.revision
            down_revision = module.down_revision
            
            # 记录版本
            versions[revision] = {
                'file': f,
                'down_revision': down_revision,
            }
            
            # 记录依赖
            if down_revision:
                if down_revision not in dependencies:
                    dependencies[down_revision] = []
                dependencies[down_revision].append(revision)
    
    # 找到头部版本（没有被其他版本指向的版本）
    heads = []
    for rev in versions:
        if rev not in dependencies:
            heads.append(rev)
    
    # 找到根版本（不指向任何版本的版本）
    roots = []
    for rev, info in versions.items():
        if info['down_revision'] is None:
            roots.append(rev)
    
    print(f"找到 {len(versions)} 个迁移版本")
    print(f"根版本: {roots}")
    print(f"头版本: {heads}")
    
    # 显示所有版本的信息
    print("\n所有版本信息:")
    for rev, info in versions.items():
        print(f"{rev} ({info['file']}) -> {info['down_revision']}")
    
    # 检查头版本到根版本的路径
    if len(heads) > 1:
        print("\n警告: 存在多个头版本，可能需要合并!")
        
        # 分析每个头版本的路径
        for head in heads:
            print(f"\n头版本 {head} 的路径:")
            current = head
            path = [current]
            
            while versions[current]['down_revision'] is not None:
                current = versions[current]['down_revision']
                path.append(current)
            
            path.reverse()
            for i, rev in enumerate(path):
                print(f"  {i+1}. {rev} ({versions[rev]['file']})")

if __name__ == "__main__":
    check_migrations() 