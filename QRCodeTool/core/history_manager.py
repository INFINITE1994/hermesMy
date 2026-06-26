"""历史记录管理模块"""
import json
import os
from datetime import datetime
from pathlib import Path


class HistoryManager:
    """历史记录管理器"""

    def __init__(self, history_dir: str | None = None):
        if history_dir is None:
            home = Path.home()
            self.history_dir = home / ".qrcodetool" / "history"
        else:
            self.history_dir = Path(history_dir)

        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.history_dir / "history.json"
        self._history = self._load()

    def _load(self) -> list[dict]:
        """加载历史记录"""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def _save(self):
        """保存历史记录"""
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(self._history, f, ensure_ascii=False, indent=2)

    def add(
        self,
        content: str,
        qr_type: str = "text",
        image_path: str = "",
        extra: dict | None = None,
    ) -> dict:
        """添加一条历史记录"""
        record = {
            "id": len(self._history) + 1,
            "content": content,
            "type": qr_type,
            "image_path": image_path,
            "timestamp": datetime.now().isoformat(),
            "extra": extra or {},
        }
        self._history.append(record)
        self._save()
        return record

    def get_all(self) -> list[dict]:
        """获取所有历史记录"""
        return list(reversed(self._history))

    def get_by_id(self, record_id: int) -> dict | None:
        """根据ID获取记录"""
        for record in self._history:
            if record["id"] == record_id:
                return record
        return None

    def delete(self, record_id: int) -> bool:
        """删除一条记录"""
        for i, record in enumerate(self._history):
            if record["id"] == record_id:
                self._history.pop(i)
                self._save()
                return True
        return False

    def clear(self):
        """清空所有记录"""
        self._history.clear()
        self._save()

    def search(self, keyword: str) -> list[dict]:
        """搜索历史记录"""
        keyword_lower = keyword.lower()
        results = []
        for record in reversed(self._history):
            if keyword_lower in record.get("content", "").lower():
                results.append(record)
        return results
