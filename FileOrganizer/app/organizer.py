"""文件整理核心逻辑"""
import os
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional


# 文件类型分组
FILE_CATEGORIES = {
    "🖼️ 图片": {
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp",
        ".ico", ".tiff", ".tif", ".raw", ".heic", ".heif", ".avif",
    },
    "📄 文档": {
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".txt", ".csv", ".rtf", ".odt", ".ods", ".odp", ".md",
        ".json", ".xml", ".yaml", ".yml", ".ini", ".cfg", ".conf",
    },
    "🎬 视频": {
        ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm",
        ".m4v", ".mpg", ".mpeg", ".3gp", ".ts",
    },
    "🎵 音频": {
        ".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a",
        ".opus", ".aiff", ".ape",
    },
    "📦 压缩包": {
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
        ".tar.gz", ".tar.bz2", ".tar.xz", ".tgz",
    },
    "💻 代码": {
        ".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".h",
        ".ts", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala",
        ".sh", ".bat", ".ps1", ".sql", ".r", ".m", ".vue", ".jsx",
        ".tsx", ".svelte",
    },
    "🔤 字体": {
        ".ttf", ".otf", ".woff", ".woff2", ".eot",
    },
    "🎮 可执行": {
        ".exe", ".msi", ".dll", ".sys", ".app", ".dmg", ".deb", ".rpm",
    },
}


def get_category(ext: str) -> str:
    """根据扩展名获取文件分类"""
    ext_lower = ext.lower()
    for category, extensions in FILE_CATEGORIES.items():
        if ext_lower in extensions:
            return category
    return "📋 其他"


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def safe_move(src: str, dst: str) -> str:
    """安全移动文件，如果目标已存在则自动重命名"""
    dst_path = Path(dst)
    if dst_path.exists():
        stem = dst_path.stem
        suffix = dst_path.suffix
        parent = dst_path.parent
        counter = 1
        while dst_path.exists():
            dst_path = parent / f"{stem}_{counter}{suffix}"
            counter += 1
    shutil.move(src, str(dst_path))
    return str(dst_path)


def scan_directory(directory: str, recursive: bool = True) -> list[dict]:
    """扫描目录，返回文件信息列表"""
    files = []
    try:
        if recursive:
            for root, dirs, filenames in os.walk(directory):
                for name in filenames:
                    filepath = os.path.join(root, name)
                    try:
                        stat = os.stat(filepath)
                        ext = os.path.splitext(name)[1]
                        files.append({
                            "path": filepath,
                            "name": name,
                            "size": stat.st_size,
                            "modified": stat.st_mtime,
                            "ext": ext,
                            "category": get_category(ext),
                        })
                    except (OSError, PermissionError):
                        continue
        else:
            for item in os.listdir(directory):
                filepath = os.path.join(directory, item)
                if os.path.isfile(filepath):
                    try:
                        stat = os.stat(filepath)
                        ext = os.path.splitext(item)[1]
                        files.append({
                            "path": filepath,
                            "name": item,
                            "size": stat.st_size,
                            "modified": stat.st_mtime,
                            "ext": ext,
                            "category": get_category(ext),
                        })
                    except (OSError, PermissionError):
                        continue
    except (OSError, PermissionError):
        pass
    return files


def organize_by_type(directory: str) -> list[dict]:
    """按类型整理文件，返回操作记录"""
    moves = []
    files = scan_directory(directory, recursive=False)
    for f in files:
        category = f["category"]
        target_dir = os.path.join(directory, category)
        target_path = os.path.join(target_dir, f["name"])
        if os.path.dirname(f["path"]) == target_dir:
            continue
        moves.append({
            "src": f["path"],
            "dst": target_path,
            "action": "move",
            "info": f"{f['name']} → {category}/",
        })
    return moves


def execute_type_organization(moves: list[dict]) -> list[dict]:
    """执行按类型整理"""
    results = []
    for m in moves:
        try:
            os.makedirs(os.path.dirname(m["dst"]), exist_ok=True)
            actual_dst = safe_move(m["src"], m["dst"])
            results.append({**m, "dst": actual_dst, "status": "success"})
        except Exception as e:
            results.append({**m, "status": "error", "error": str(e)})
    return results


def organize_by_date(directory: str) -> list[dict]:
    """按日期整理文件，返回操作记录"""
    moves = []
    files = scan_directory(directory, recursive=False)
    for f in files:
        dt = datetime.fromtimestamp(f["modified"])
        year_dir = str(dt.year)
        month_dir = f"{dt.month:02d}"
        target_dir = os.path.join(directory, year_dir, month_dir)
        target_path = os.path.join(target_dir, f["name"])
        if os.path.dirname(f["path"]) == target_dir:
            continue
        moves.append({
            "src": f["path"],
            "dst": target_path,
            "action": "move",
            "info": f"{f['name']} → {year_dir}/{month_dir}/",
        })
    return moves


def execute_date_organization(moves: list[dict]) -> list[dict]:
    """执行按日期整理"""
    results = []
    for m in moves:
        try:
            os.makedirs(os.path.dirname(m["dst"]), exist_ok=True)
            actual_dst = safe_move(m["src"], m["dst"])
            results.append({**m, "dst": actual_dst, "status": "success"})
        except Exception as e:
            results.append({**m, "status": "error", "error": str(e)})
    return results


def compute_file_hash(filepath: str, chunk_size: int = 8192) -> str:
    """计算文件 MD5 哈希"""
    h = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                h.update(chunk)
    except (OSError, PermissionError):
        return ""
    return h.hexdigest()


def find_duplicates(directory: str) -> dict[str, list[dict]]:
    """查找重复文件，返回 {hash: [file_info, ...]} 字典"""
    size_map: dict[int, list[dict]] = {}
    files = scan_directory(directory)

    # 先按大小分组
    for f in files:
        size_map.setdefault(f["size"], []).append(f)

    # 只对大小相同的文件计算哈希
    hash_map: dict[str, list[dict]] = {}
    for size, group in size_map.items():
        if len(group) < 2 or size == 0:
            continue
        for f in group:
            h = compute_file_hash(f["path"])
            if h:
                f["hash"] = h
                hash_map.setdefault(h, []).append(f)

    # 只返回有多个文件的哈希组
    return {h: flist for h, flist in hash_map.items() if len(flist) > 1}


def find_empty_folders(directory: str) -> list[str]:
    """查找空文件夹"""
    empty = []
    for root, dirs, files in os.walk(directory):
        # 只检查叶子目录
        if not dirs and not files:
            empty.append(root)
    # 从深到浅排序，方便删除
    empty.sort(key=lambda x: x.count(os.sep), reverse=True)
    return empty


def clean_empty_folders(folders: list[str]) -> list[dict]:
    """清理空文件夹"""
    results = []
    for folder in folders:
        try:
            os.rmdir(folder)
            results.append({"path": folder, "status": "success"})
        except OSError as e:
            results.append({"path": folder, "status": "error", "error": str(e)})
    return results


def find_large_files(directory: str, top_n: int = 20) -> list[dict]:
    """查找最大的 N 个文件"""
    files = scan_directory(directory)
    files.sort(key=lambda x: x["size"], reverse=True)
    return files[:top_n]


def batch_rename_preview(
    directory: str,
    pattern: str,
    prefix: str = "",
    start_num: int = 1,
    separator: str = "_",
) -> list[dict]:
    """批量重命名预览

    pattern: "sequential" | "date" | "custom"
    对于 custom，支持 {n} 编号, {d} 日期, {o} 原名, {e} 扩展名
    """
    files = scan_directory(directory, recursive=False)
    files.sort(key=lambda x: x["name"])
    renames = []

    for i, f in enumerate(files):
        ext = f["ext"]
        stem = Path(f["name"]).stem
        dt = datetime.fromtimestamp(f["modified"])

        if pattern == "sequential":
            num = start_num + i
            new_name = f"{prefix}{separator}{num:03d}{ext}" if prefix else f"{num:03d}{ext}"
        elif pattern == "date":
            date_str = dt.strftime("%Y%m%d")
            new_name = f"{prefix}{separator}{date_str}{ext}" if prefix else f"{stem}{separator}{date_str}{ext}"
        elif pattern == "custom":
            new_name = prefix.replace("{n}", str(start_num + i).zfill(3))
            new_name = new_name.replace("{d}", dt.strftime("%Y%m%d"))
            new_name = new_name.replace("{o}", stem)
            new_name = new_name.replace("{e}", ext)
            if not new_name.endswith(ext):
                new_name += ext
        else:
            new_name = f["name"]

        if new_name != f["name"]:
            new_path = os.path.join(directory, new_name)
            renames.append({
                "old_path": f["path"],
                "new_path": new_path,
                "old_name": f["name"],
                "new_name": new_name,
                "info": f"{f['name']} → {new_name}",
            })

    return renames


def execute_renames(renames: list[dict]) -> list[dict]:
    """执行重命名"""
    results = []
    for r in renames:
        try:
            os.rename(r["old_path"], r["new_path"])
            results.append({**r, "status": "success"})
        except Exception as e:
            results.append({**r, "status": "error", "error": str(e)})
    return results


def undo_moves(results: list[dict]) -> list[dict]:
    """撤销移动/重命名操作"""
    undos = []
    # 反序撤销
    for r in reversed(results):
        if r.get("status") != "success":
            continue
        try:
            src = r.get("dst") or r.get("new_path")
            dst = r.get("src") or r.get("old_path")
            if src and dst and os.path.exists(src):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.move(src, dst)
                undos.append({"path": dst, "status": "undone"})
        except Exception as e:
            undos.append({"path": r.get("src", ""), "status": "error", "error": str(e)})
    return undos


def scan_drives() -> list[str]:
    """扫描可用驱动器"""
    drives = []
    if os.name == "nt":
        import string
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)
    else:
        drives.append("/")
    return drives
