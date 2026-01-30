# -*- coding: utf-8 -*-
"""
✅ 日期文件名规范化工具（防闪退终极稳定版）
✨ 核心修复：
   • 全局异常捕获 + 强制窗口保持（即使崩溃也不闪退）
   • Windows 控制台编码硬性修复（避免 print 崩溃）
   • 保留原始扩展名大小写（.TXT → .TXT）
   • 每步关键操作日志输出（精准定位失败点）
   • 文件占用/权限问题明确提示
"""
import os
import sys
import re
from pathlib import Path

# =============== 【关键修复1】Windows 控制台编码硬初始化 ===============
if os.name == 'nt':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # 强制设置控制台为 UTF-8 模式（避免中文 print 崩溃）
        kernel32.SetConsoleOutputCP(65001)  # UTF-8
        kernel32.SetConsoleCP(65001)
        # 同时设置 stdout/stderr 编码
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception as e:
        # 即使初始化失败也不中断，用安全方式打印
        pass

# =============== 核心逻辑 ===============
# 精准匹配：年(4位) + [半角/全角点] + 月 + [半角/全角点] + 日 + 任意后续内容
# \uFF0E = 全角点（．），确保字符精准无歧义
DATE_PATTERN = re.compile(r'^(\d{4})([\uFF0E.])(\d{1,2})([\uFF0E.])(\d{1,2})(.*)$', re.UNICODE)

def normalize_filename(filename: str):
    """返回 (需修改, 新文件名, 诊断信息)"""
    if not filename.lower().endswith('.txt'):
        return False, filename, "❌ 非 .txt 文件"
    
    # 保留原始扩展名大小写（.TXT → .TXT）
    stem, ext = os.path.splitext(filename)  # ext 含点且保留原始大小写
    
    match = DATE_PATTERN.match(stem)
    if not match:
        sample = stem[:12]
        codes = ' '.join(f"U+{ord(c):04X}" for c in sample if c)
        return False, filename, f"❌ 无有效日期前缀 | 前12字符码点: {codes}"
    
    year, sep1, month, sep2, day, rest = match.groups()
    new_month, new_day = month.zfill(2), day.zfill(2)
    
    # 仅当需要修改时生成新名
    if month == new_month and day == new_day and sep1 == '.' and sep2 == '.':
        return False, filename, "ℹ️ 已是规范格式"
    
    new_stem = f"{year}.{new_month}.{new_day}{rest}"
    new_name = new_stem + ext  # 保留原始扩展名大小写
    diag = f"✅ 规范化: {month}→{new_month}, {day}→{new_day} | 分隔符 [{repr(sep1)},{repr(sep2)}]→['.','']"
    return True, new_name, diag

def safe_rename(file_path: Path) -> bool:
    try:
        should_rename, new_name, diag = normalize_filename(file_path.name)
        if not should_rename:
            print(f"  {diag} → '{file_path.name}'")
            return False
        
        new_path = file_path.parent / new_name
        
        # 安全检查
        if new_path.exists():
            print(f"⚠️ 跳过（目标已存在）: '{file_path.name}'")
            return False
        
        # 尝试重命名（捕获具体异常）
        file_path.rename(new_path)
        print(f"✅ 重命名成功: '{file_path.name}'")
        print(f"   → '{new_name}'")
        return True
        
    except PermissionError:
        print(f"❌ 权限拒绝: '{file_path.name}'（文件可能被占用/只读）")
    except FileNotFoundError:
        print(f"❌ 文件消失: '{file_path.name}'（可能已被移动）")
    except Exception as e:
        print(f"❌ 重命名失败 '{file_path.name}': {type(e).__name__}")
        print(f"   详情: {str(e)[:150]}")
    return False

def collect_files(input_paths):
    results = []
    for raw in input_paths:
        try:
            p = Path(raw).resolve()
            if not p.exists():
                print(f"⚠️ 路径不存在: {raw}")
                continue
            if p.is_file() and p.suffix.lower() == '.txt':
                results.append(p)
                print(f"📄 添加文件: {p.name}")
            elif p.is_dir():
                found = [f for f in p.rglob("*.txt") if f.is_file()]
                print(f"📁 扫描目录 '{p.name}': 找到 {len(found)} 个 .txt 文件")
                results.extend(found)
            else:
                print(f"⏭️ 跳过: {raw}（非文件/非目录）")
        except Exception as e:
            print(f"❌ 解析路径失败 '{raw}': {e}")
    return results

def wait_exit():
    """强制保持窗口（Windows 专用）"""
    if os.name == 'nt':
        try:
            import msvcrt
            print("\n" + "="*60)
            print("ℹ️ 按任意键退出...")
            msvcrt.getch()
        except:
            input("\nℹ️ 按回车键退出...")

# =============== 主程序（全局异常防护） ===============
def main():
    print("="*60)
    print("📅 日期文件名规范化工具（防闪退终极稳定版）")
    print("="*60)
    
    if len(sys.argv) < 2:
        print("\n💡 使用方法：将 .txt 文件或文件夹直接拖拽到本脚本上")
        print("✨ 特性：")
        print("   • 智能识别半角点(.)和全角点（．）")
        print("   • 月/日自动补零（1→01）")
        print("   • 100% 保留中文标点/空格/扩展名大小写")
        print("   • 崩溃也不闪退，错误信息完整显示")
        wait_exit()
        return
    
    print(f"\n📥 接收 {len(sys.argv)-1} 个拖拽项:")
    for i, p in enumerate(sys.argv[1:], 1):
        print(f"   [{i}] {p}")
    
    print("\n🔍 开始收集 .txt 文件...")
    files = collect_files(sys.argv[1:])
    
    if not files:
        print("\n❌ 未找到任何可处理的 .txt 文件")
        wait_exit()
        return
    
    print(f"\n⚙️ 共需处理 {len(files)} 个文件：")
    print("-"*60)
    
    success = 0
    for i, fp in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] 处理: {fp.name}")
        if safe_rename(fp):
            success += 1
    
    # =============== 结果汇总 ===============
    print("\n" + "="*60)
    print(f"🎉 处理完成 | 成功: {success}/{len(files)}")
    print("="*60)
    
    wait_exit()

# =============== 全局异常防护（防闪退核心） ===============
if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        wait_exit()
    except Exception as e:
        print("\n" + "!"*60)
        print("💥 程序发生严重错误（但窗口已保持）")
        print("!"*60)
        import traceback
        print("\n错误详情:")
        traceback.print_exc()
        print("\n" + "!"*60)
        wait_exit()