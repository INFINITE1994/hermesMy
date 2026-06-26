"""Core scanning engine for CleanMaster."""
import os
import glob
import shutil
import tempfile
import hashlib
import platform

if platform.system() == 'Windows':
    import winreg
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


@dataclass
class ScanResult:
    """Represents a single scan finding."""
    category: str
    path: str
    size: int  # bytes
    description: str
    safe_to_delete: bool = True


@dataclass
class ScanProgress:
    """Progress callback data."""
    current_category: str
    files_scanned: int
    total_size: int


@dataclass
class ScanReport:
    """Full scan report."""
    results: list[ScanResult] = field(default_factory=list)
    total_size: int = 0
    categories: dict[str, int] = field(default_factory=dict)

    def add(self, result: ScanResult):
        self.results.append(result)
        self.total_size += result.size
        self.categories[result.category] = self.categories.get(result.category, 0) + result.size

    def sorted_by_size(self) -> list[ScanResult]:
        return sorted(self.results, key=lambda r: -r.size)


class Scanner:
    """System junk file scanner."""

    def __init__(self):
        self._stop = False
        self.user_profile = os.environ.get("USERPROFILE", "")
        self.local_app = os.environ.get("LOCALAPPDATA", "")
        self.roaming_app = os.environ.get("APPDATA", "")
        self.temp_dir = tempfile.gettempdir()
        self.windows_temp = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Temp")

    def stop(self):
        self._stop = True

    def _get_dir_size(self, path: str) -> int:
        """Get directory size, handling permission errors."""
        total = 0
        try:
            with os.scandir(path) as it:
                for entry in it:
                    if self._stop:
                        return total
                    try:
                        if entry.is_file(follow_symlinks=False):
                            total += entry.stat().st_size
                        elif entry.is_dir(follow_symlinks=False):
                            total += self._get_dir_size(entry.path)
                    except (PermissionError, OSError):
                        pass
        except (PermissionError, OSError):
            pass
        return total

    def _scan_dir_contents(self, path: str, category: str, description: str,
                           report: ScanReport, filter_fn: Callable = None):
        """Scan a directory and add its contents to the report."""
        if not os.path.exists(path):
            return
        try:
            with os.scandir(path) as it:
                for entry in it:
                    if self._stop:
                        return
                    try:
                        if entry.is_file(follow_symlinks=False):
                            if filter_fn and not filter_fn(entry.name):
                                continue
                            size = entry.stat().st_size
                            if size > 0:
                                report.add(ScanResult(
                                    category=category,
                                    path=entry.path,
                                    size=size,
                                    description=description,
                                ))
                        elif entry.is_dir(follow_symlinks=False):
                            dir_size = self._get_dir_size(entry.path)
                            if dir_size > 0:
                                report.add(ScanResult(
                                    category=category,
                                    path=entry.path,
                                    size=dir_size,
                                    description=description,
                                ))
                    except (PermissionError, OSError):
                        pass
        except (PermissionError, OSError):
            pass

    def scan_temp_files(self, report: ScanReport):
        """Scan Windows temp directories."""
        self._scan_dir_contents(self.temp_dir, "临时文件", "系统临时文件", report)
        if self.windows_temp != self.temp_dir:
            self._scan_dir_contents(self.windows_temp, "临时文件", "Windows临时文件", report)

    def scan_browser_cache(self, report: ScanReport):
        """Scan browser cache directories."""
        browsers = {
            "Chrome": os.path.join(self.local_app, "Google", "Chrome", "User Data", "Default", "Cache"),
            "Edge": os.path.join(self.local_app, "Microsoft", "Edge", "User Data", "Default", "Cache"),
            "Firefox": os.path.join(self.roaming_app, "Mozilla", "Firefox", "Profiles"),
        }
        for name, path in browsers.items():
            if os.path.exists(path):
                size = self._get_dir_size(path)
                if size > 0:
                    report.add(ScanResult(
                        category="浏览器缓存",
                        path=path,
                        size=size,
                        description=f"{name}浏览器缓存",
                    ))

    def scan_recycle_bin(self, report: ScanReport):
        """Scan recycle bin size."""
        recycle_paths = [
            os.path.join(os.environ.get("SystemDrive", "C:"), "$RECYCLE.BIN"),
        ]
        for path in recycle_paths:
            if os.path.exists(path):
                size = self._get_dir_size(path)
                if size > 0:
                    report.add(ScanResult(
                        category="回收站",
                        path=path,
                        size=size,
                        description="回收站中的文件",
                    ))

    def scan_crash_dumps(self, report: ScanReport):
        """Scan crash dump files."""
        dump_dir = os.path.join(self.local_app, "CrashDumps")
        self._scan_dir_contents(dump_dir, "崩溃转储", "程序崩溃转储文件", report)

        # Windows error reports
        wer_dir = os.path.join(self.local_app, "Microsoft", "Windows", "WER")
        if os.path.exists(wer_dir):
            size = self._get_dir_size(wer_dir)
            if size > 0:
                report.add(ScanResult(
                    category="崩溃转储",
                    path=wer_dir,
                    size=size,
                    description="Windows错误报告",
                ))

    def scan_windows_update(self, report: ScanReport):
        """Scan Windows Update cache."""
        update_path = os.path.join(os.environ.get("WINDIR", "C:\\Windows"),
                                   "SoftwareDistribution", "Download")
        if os.path.exists(update_path):
            size = self._get_dir_size(update_path)
            if size > 0:
                report.add(ScanResult(
                    category="Windows更新缓存",
                    path=update_path,
                    size=size,
                    description="Windows更新下载缓存",
                ))

    def scan_thumbnail_cache(self, report: ScanReport):
        """Scan thumbnail cache."""
        thumb_dir = os.path.join(self.local_app, "Microsoft", "Windows", "Explorer")
        if os.path.exists(thumb_dir):
            total = 0
            try:
                with os.scandir(thumb_dir) as it:
                    for entry in it:
                        if entry.name.startswith("thumbcache") and entry.is_file():
                            total += entry.stat().st_size
            except (PermissionError, OSError):
                pass
            if total > 0:
                report.add(ScanResult(
                    category="缩略图缓存",
                    path=thumb_dir,
                    size=total,
                    description="文件缩略图缓存",
                ))

    def scan_old_installers(self, report: ScanReport):
        """Scan for old installer cache."""
        installer_path = os.path.join(self.local_app, "Package Cache")
        if os.path.exists(installer_path):
            size = self._get_dir_size(installer_path)
            if size > 0:
                report.add(ScanResult(
                    category="安装包缓存",
                    path=installer_path,
                    size=size,
                    description="旧安装程序缓存",
                    safe_to_delete=False,  # May break some apps
                ))

    def scan_prefetch(self, report: ScanReport):
        """Scan Windows Prefetch files."""
        prefetch = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Prefetch")
        if os.path.exists(prefetch):
            size = self._get_dir_size(prefetch)
            if size > 0:
                report.add(ScanResult(
                    category="预读取文件",
                    path=prefetch,
                    size=size,
                    description="程序预读取缓存",
                ))

    def scan_npm_pip_cache(self, report: ScanReport):
        """Scan npm and pip cache."""
        caches = {
            "npm缓存": os.path.join(self.local_app, "npm-cache"),
            "pip缓存": os.path.join(self.local_app, "pip"),
            "uv缓存": os.path.join(self.local_app, "uv"),
        }
        for name, path in caches.items():
            if os.path.exists(path):
                size = self._get_dir_size(path)
                if size > 0:
                    report.add(ScanResult(
                        category="开发缓存",
                        path=path,
                        size=size,
                        description=name,
                    ))

    def scan_recent_files(self, report: ScanReport):
        """Scan recent file shortcuts."""
        recent = os.path.join(self.roaming_app, "Microsoft", "Windows", "Recent")
        if os.path.exists(recent):
            size = self._get_dir_size(recent)
            if size > 0:
                report.add(ScanResult(
                    category="最近文件记录",
                    path=recent,
                    size=size,
                    description="最近打开文件的快捷方式",
                ))

    def full_scan(self, callback: Callable[[ScanProgress], None] = None) -> ScanReport:
        """Run a full system scan."""
        self._stop = False
        report = ScanReport()

        scanners = [
            ("临时文件", self.scan_temp_files),
            ("浏览器缓存", self.scan_browser_cache),
            ("回收站", self.scan_recycle_bin),
            ("崩溃转储", self.scan_crash_dumps),
            ("Windows更新缓存", self.scan_windows_update),
            ("缩略图缓存", self.scan_thumbnail_cache),
            ("安装包缓存", self.scan_old_installers),
            ("预读取文件", self.scan_prefetch),
            ("开发缓存", self.scan_npm_pip_cache),
            ("最近文件记录", self.scan_recent_files),
        ]

        for i, (name, scanner_fn) in enumerate(scanners):
            if self._stop:
                break
            if callback:
                callback(ScanProgress(
                    current_category=name,
                    files_scanned=i,
                    total_size=report.total_size,
                ))
            scanner_fn(report)

        return report


class Cleaner:
    """File cleanup engine."""

    @staticmethod
    def delete_path(path: str, use_trash: bool = True) -> bool:
        """Delete a file or directory."""
        try:
            if use_trash:
                from send2trash import send2trash
                send2trash(path)
            else:
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    os.remove(path)
            return True
        except Exception:
            return False

    @staticmethod
    def empty_recycle_bin() -> bool:
        """Empty the Windows recycle bin."""
        try:
            import ctypes
            ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
            return True
        except Exception:
            return False


# ═══════════════════════════════════════════════════════════════════════════
# Pro Feature: Large File Finder
# ═══════════════════════════════════════════════════════════════════════════
class LargeFileFinder:
    """Find the largest files on a drive."""

    SKIP_DIRS = {
        '$RECYCLE.BIN', 'System Volume Information', 'Windows',
        '$WinREAgent', 'Recovery', 'PerfLogs',
    }

    def __init__(self):
        self._stop = False

    def stop(self):
        self._stop = True

    def find_large_files(self, drive: str, top_n: int = 20,
                         callback: Callable = None) -> list[dict]:
        """Find the top N largest files on a drive.

        Returns list of dicts: [{'path': str, 'size': int}, ...]
        """
        self._stop = False
        files_found = []

        def _scan(directory):
            if self._stop:
                return
            try:
                with os.scandir(directory) as it:
                    for entry in it:
                        if self._stop:
                            return
                        try:
                            if entry.is_file(follow_symlinks=False):
                                size = entry.stat().st_size
                                files_found.append({
                                    'path': entry.path,
                                    'size': size,
                                })
                                # Keep only top_n to save memory
                                if len(files_found) > top_n * 100:
                                    files_found.sort(key=lambda x: -x['size'])
                                    del files_found[top_n:]
                                if callback:
                                    callback(entry.path, size)
                            elif entry.is_dir(follow_symlinks=False):
                                if entry.name not in self.SKIP_DIRS:
                                    _scan(entry.path)
                        except (PermissionError, OSError):
                            pass
            except (PermissionError, OSError):
                pass

        _scan(drive)
        files_found.sort(key=lambda x: -x['size'])
        return files_found[:top_n]


# ═══════════════════════════════════════════════════════════════════════════
# Pro Feature: Duplicate File Finder
# ═══════════════════════════════════════════════════════════════════════════
class DuplicateFinder:
    """Find duplicate files by MD5 hash."""

    SKIP_DIRS = {
        '$RECYCLE.BIN', 'System Volume Information', 'Windows',
        '$WinREAgent', 'Recovery', 'PerfLogs',
    }

    def __init__(self):
        self._stop = False

    def stop(self):
        self._stop = True

    def _file_hash(self, filepath: str) -> str:
        """Compute MD5 hash of a file."""
        h = hashlib.md5()
        try:
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    h.update(chunk)
            return h.hexdigest()
        except (PermissionError, OSError):
            return ''

    def find_duplicates(self, drive: str,
                        callback: Callable = None) -> dict[str, list[dict]]:
        """Find duplicate files on a drive.

        Returns dict: {hash: [{'path': str, 'size': int}, ...]}
        Only includes entries with 2+ files.
        """
        self._stop = False
        size_map: dict[int, list[str]] = {}  # size -> [paths]
        result: dict[str, list[dict]] = {}   # hash -> [{path, size}]

        # Pass 1: group by size
        def _scan_size(directory):
            if self._stop:
                return
            try:
                with os.scandir(directory) as it:
                    for entry in it:
                        if self._stop:
                            return
                        try:
                            if entry.is_file(follow_symlinks=False):
                                size = entry.stat().st_size
                                if size > 0:
                                    size_map.setdefault(size, []).append(entry.path)
                                if callback:
                                    callback(f"扫描中: {entry.path}", 0)
                            elif entry.is_dir(follow_symlinks=False):
                                if entry.name not in self.SKIP_DIRS:
                                    _scan_size(entry.path)
                        except (PermissionError, OSError):
                            pass
            except (PermissionError, OSError):
                pass

        _scan_size(drive)

        # Pass 2: hash files with same size
        candidates = {s: paths for s, paths in size_map.items() if len(paths) > 1}
        total = sum(len(v) for v in candidates.values())
        done = 0

        for size, paths in candidates.items():
            if self._stop:
                break
            for path in paths:
                if self._stop:
                    break
                h = self._file_hash(path)
                if h:
                    result.setdefault(h, []).append({
                        'path': path,
                        'size': size,
                    })
                done += 1
                if callback:
                    callback(f"计算哈希: {done}/{total}", done)

        # Filter to only groups with 2+ files
        return {h: files for h, files in result.items() if len(files) >= 2}


# ═══════════════════════════════════════════════════════════════════════════
# Pro Feature: Startup Manager
# ═══════════════════════════════════════════════════════════════════════════
class StartupManager:
    """Manage Windows startup programs via registry."""

    @staticmethod
    def _get_registry_paths():
        """Get registry paths (lazy init for non-Windows)."""
        return [
            (winreg.HKEY_CURRENT_USER,
             r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE,
             r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_CURRENT_USER,
             r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
            (winreg.HKEY_LOCAL_MACHINE,
             r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
        ]

    @staticmethod
    def _get_disabled_paths():
        """Get disabled registry paths (lazy init for non-Windows)."""
        return [
            (winreg.HKEY_CURRENT_USER,
             r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"),
            (winreg.HKEY_LOCAL_MACHINE,
             r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"),
        ]

    @staticmethod
    def get_startup_programs() -> list[dict]:
        """Get list of all startup programs.

        Returns list of dicts with keys:
        - name: program name
        - command: command line
        - location: 'HKCU' or 'HKLM'
        - enabled: bool
        - hive: registry hive handle
        - reg_path: registry path
        """
        if platform.system() != 'Windows':
            return []

        programs = []

        for hive, path in StartupManager._get_registry_paths():
            hive_name = "HKCU" if hive == winreg.HKEY_CURRENT_USER else "HKLM"
            try:
                key = winreg.OpenKey(hive, path, 0,
                                     winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        programs.append({
                            'name': name,
                            'command': value,
                            'location': hive_name,
                            'enabled': True,
                            'hive': hive,
                            'reg_path': path,
                        })
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except (FileNotFoundError, OSError):
                pass

        # Check disabled status
        for hive, base_path in StartupManager._get_disabled_paths():
            try:
                key = winreg.OpenKey(hive, base_path, 0,
                                     winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
                i = 0
                while True:
                    try:
                        name, value, vtype = winreg.EnumValue(key, i)
                        # The value is binary; first 4 bytes indicate status
                        # 02,00,00,00 = enabled; 03,00,00,00 = disabled
                        is_disabled = (isinstance(value, bytes) and len(value) >= 4
                                       and value[0] == 0x03)
                        for prog in programs:
                            if prog['name'] == name:
                                prog['enabled'] = not is_disabled
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except (FileNotFoundError, OSError):
                pass

        return programs

    @staticmethod
    def disable_startup(name: str, hive, reg_path: str) -> bool:
        """Disable a startup program by writing to StartupApproved."""
        if platform.system() != 'Windows':
            return False
        return StartupManager._set_startup_status(name, hive, reg_path, enable=False)

    @staticmethod
    def enable_startup(name: str, hive, reg_path: str) -> bool:
        """Enable a startup program by writing to StartupApproved."""
        if platform.system() != 'Windows':
            return False
        return StartupManager._set_startup_status(name, hive, reg_path, enable=True)

    @staticmethod
    def _set_startup_status(name: str, hive, reg_path: str, enable: bool) -> bool:
        """Set startup enabled/disabled status via StartupApproved key."""
        # Map Run path to StartupApproved path
        if 'RunOnce' in reg_path:
            return False  # RunOnce entries can't be toggled

        approved_path = reg_path.replace('\\Run', '\\Explorer\\StartupApproved\\Run')
        try:
            key = winreg.OpenKey(hive, approved_path, 0,
                                 winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY)
        except (FileNotFoundError, OSError):
            try:
                key = winreg.CreateKeyEx(hive, approved_path, 0,
                                         winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY)
            except OSError:
                return False

        try:
            if enable:
                value = b'\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            else:
                value = b'\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            winreg.SetValueEx(key, name, 0, winreg.REG_BINARY, value)
            winreg.CloseKey(key)
            return True
        except OSError:
            try:
                winreg.CloseKey(key)
            except Exception:
                pass
            return False

    @staticmethod
    def remove_startup(name: str, hive, reg_path: str) -> bool:
        """Remove a startup entry entirely."""
        if platform.system() != 'Windows':
            return False
        try:
            key = winreg.OpenKey(hive, reg_path, 0,
                                 winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY)
            winreg.DeleteValue(key, name)
            winreg.CloseKey(key)
            return True
        except (FileNotFoundError, OSError):
            return False


# ═══════════════════════════════════════════════════════════════════════════
# Pro Feature: Disk Usage Analyzer
# ═══════════════════════════════════════════════════════════════════════════
class DiskUsageAnalyzer:
    """Analyze disk usage by folder."""

    SKIP_DIRS = {
        '$RECYCLE.BIN', 'System Volume Information',
        '$WinREAgent', 'Recovery', 'PerfLogs',
    }

    def __init__(self):
        self._stop = False

    def stop(self):
        self._stop = True

    def analyze(self, path: str, depth: int = 1,
                callback: Callable = None) -> list[dict]:
        """Analyze disk usage under a path.

        Returns list of dicts: [{'name': str, 'path': str, 'size': int, 'children': list}]
        sorted by size descending.
        """
        self._stop = False
        result = self._analyze_dir(path, depth, callback)
        return result

    def _analyze_dir(self, directory: str, depth: int,
                     callback: Callable = None) -> list[dict]:
        """Recursively analyze directory."""
        if self._stop or depth < 0:
            return []

        entries = []
        try:
            with os.scandir(directory) as it:
                for entry in it:
                    if self._stop:
                        break
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            if entry.name in self.SKIP_DIRS:
                                continue
                            size = self._dir_size(entry.path)
                            children = self._analyze_dir(entry.path, depth - 1) if depth > 0 else []
                            entries.append({
                                'name': entry.name,
                                'path': entry.path,
                                'size': size,
                                'children': children,
                            })
                            if callback:
                                callback(entry.path, size)
                        elif entry.is_file(follow_symlinks=False):
                            size = entry.stat().st_size
                            if size > 0:
                                entries.append({
                                    'name': entry.name,
                                    'path': entry.path,
                                    'size': size,
                                    'children': [],
                                })
                    except (PermissionError, OSError):
                        pass
        except (PermissionError, OSError):
            pass

        entries.sort(key=lambda x: -x['size'])
        return entries

    def _dir_size(self, path: str) -> int:
        """Get total size of a directory."""
        total = 0
        try:
            with os.scandir(path) as it:
                for entry in it:
                    if self._stop:
                        return total
                    try:
                        if entry.is_file(follow_symlinks=False):
                            total += entry.stat().st_size
                        elif entry.is_dir(follow_symlinks=False):
                            if entry.name not in self.SKIP_DIRS:
                                total += self._dir_size(entry.path)
                    except (PermissionError, OSError):
                        pass
        except (PermissionError, OSError):
            pass
        return total


def get_available_drives() -> list[str]:
    """Get list of available drive letters."""
    drives = []
    for letter in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            drives.append(drive)
    return drives
