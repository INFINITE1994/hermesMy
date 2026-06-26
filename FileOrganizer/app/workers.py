"""后台工作线程"""
from PyQt6.QtCore import QThread, pyqtSignal
from app.organizer import (
    organize_by_type, execute_type_organization,
    organize_by_date, execute_date_organization,
    find_duplicates, find_empty_folders, clean_empty_folders,
    find_large_files, batch_rename_preview, execute_renames,
    undo_moves,
)


class BaseWorker(QThread):
    """基础工作线程"""
    progress = pyqtSignal(int, str)  # (percent, message)
    finished_signal = pyqtSignal(object)  # result
    error_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._cancel = False

    def cancel(self):
        self._cancel = True


class OrganizeByTypeWorker(BaseWorker):
    """按类型整理工作线程"""
    def __init__(self, directory: str):
        super().__init__()
        self.directory = directory

    def run(self):
        try:
            self.progress.emit(10, "正在扫描文件...")
            moves = organize_by_type(self.directory)
            if not moves:
                self.finished_signal.emit({"moves": [], "results": []})
                return
            self.progress.emit(30, f"找到 {len(moves)} 个文件需要整理")

            self.progress.emit(50, "正在移动文件...")
            results = execute_type_organization(moves)
            self.progress.emit(100, "整理完成！")
            self.finished_signal.emit({"moves": moves, "results": results})
        except Exception as e:
            self.error_signal.emit(str(e))


class OrganizeByDateWorker(BaseWorker):
    """按日期整理工作线程"""
    def __init__(self, directory: str):
        super().__init__()
        self.directory = directory

    def run(self):
        try:
            self.progress.emit(10, "正在扫描文件...")
            moves = organize_by_date(self.directory)
            if not moves:
                self.finished_signal.emit({"moves": [], "results": []})
                return
            self.progress.emit(30, f"找到 {len(moves)} 个文件需要整理")

            self.progress.emit(50, "正在移动文件...")
            results = execute_date_organization(moves)
            self.progress.emit(100, "整理完成！")
            self.finished_signal.emit({"moves": moves, "results": results})
        except Exception as e:
            self.error_signal.emit(str(e))


class FindDuplicatesWorker(BaseWorker):
    """查找重复文件工作线程"""
    def __init__(self, directory: str):
        super().__init__()
        self.directory = directory

    def run(self):
        try:
            self.progress.emit(10, "正在扫描文件...")
            duplicates = find_duplicates(self.directory)
            self.progress.emit(100, f"扫描完成，找到 {len(duplicates)} 组重复文件")
            self.finished_signal.emit(duplicates)
        except Exception as e:
            self.error_signal.emit(str(e))


class FindEmptyFoldersWorker(BaseWorker):
    """查找空文件夹工作线程"""
    def __init__(self, directory: str):
        super().__init__()
        self.directory = directory

    def run(self):
        try:
            self.progress.emit(50, "正在扫描空文件夹...")
            folders = find_empty_folders(self.directory)
            self.progress.emit(100, f"找到 {len(folders)} 个空文件夹")
            self.finished_signal.emit(folders)
        except Exception as e:
            self.error_signal.emit(str(e))


class CleanEmptyFoldersWorker(BaseWorker):
    """清理空文件夹工作线程"""
    def __init__(self, folders: list[str]):
        super().__init__()
        self.folders = folders

    def run(self):
        try:
            self.progress.emit(50, "正在清理空文件夹...")
            results = clean_empty_folders(self.folders)
            success = sum(1 for r in results if r["status"] == "success")
            self.progress.emit(100, f"清理完成，删除了 {success} 个空文件夹")
            self.finished_signal.emit(results)
        except Exception as e:
            self.error_signal.emit(str(e))


class FindLargeFilesWorker(BaseWorker):
    """查找大文件工作线程"""
    def __init__(self, directory: str, top_n: int):
        super().__init__()
        self.directory = directory
        self.top_n = top_n

    def run(self):
        try:
            self.progress.emit(30, "正在扫描文件大小...")
            files = find_large_files(self.directory, self.top_n)
            self.progress.emit(100, f"扫描完成，显示前 {len(files)} 个最大文件")
            self.finished_signal.emit(files)
        except Exception as e:
            self.error_signal.emit(str(e))


class BatchRenamePreviewWorker(BaseWorker):
    """批量重命名预览工作线程"""
    def __init__(self, directory: str, pattern: str, prefix: str, start_num: int, separator: str):
        super().__init__()
        self.directory = directory
        self.pattern = pattern
        self.prefix = prefix
        self.start_num = start_num
        self.separator = separator

    def run(self):
        try:
            self.progress.emit(50, "正在生成重命名预览...")
            renames = batch_rename_preview(
                self.directory, self.pattern, self.prefix,
                self.start_num, self.separator,
            )
            self.progress.emit(100, f"预览完成，{len(renames)} 个文件将被重命名")
            self.finished_signal.emit(renames)
        except Exception as e:
            self.error_signal.emit(str(e))


class ExecuteRenamesWorker(BaseWorker):
    """执行重命名工作线程"""
    def __init__(self, renames: list[dict]):
        super().__init__()
        self.renames = renames

    def run(self):
        try:
            self.progress.emit(50, "正在重命名文件...")
            results = execute_renames(self.renames)
            success = sum(1 for r in results if r["status"] == "success")
            self.progress.emit(100, f"重命名完成，成功 {success} 个")
            self.finished_signal.emit(results)
        except Exception as e:
            self.error_signal.emit(str(e))


class UndoWorker(BaseWorker):
    """撤销操作工作线程"""
    def __init__(self, results: list[dict]):
        super().__init__()
        self.results = results

    def run(self):
        try:
            self.progress.emit(50, "正在撤销操作...")
            undos = undo_moves(self.results)
            self.progress.emit(100, f"撤销完成")
            self.finished_signal.emit(undos)
        except Exception as e:
            self.error_signal.emit(str(e))
