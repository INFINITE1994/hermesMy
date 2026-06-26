#!/usr/bin/env python3
"""WebScraper - 网页抓取工具"""

import sys
import os
import json
import csv
import re
from io import StringIO
from urllib.parse import urljoin, urlparse

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QLineEdit, QPushButton, QTextEdit,
    QTableWidget, QTableWidgetItem, QProgressBar, QFileDialog,
    QStatusBar, QSplitter, QGroupBox, QMessageBox, QComboBox,
    QHeaderView, QAbstractItemView, QScrollArea, QFrame, QGridLayout,
    QSpinBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor, QSyntaxHighlighter, QTextCharFormat, QLinearGradient, QPalette, QIcon

import requests
from bs4 import BeautifulSoup


# ── Theme ────────────────────────────────────────────────────────────
DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #0a0a0a;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
}
QTabWidget::pane {
    border: 1px solid #222244;
    background: #0a0a0a;
    border-radius: 6px;
}
QTabBar::tab {
    background: #111122;
    color: #8888aa;
    padding: 10px 20px;
    border: 1px solid #222244;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #1a1a3a;
    color: #667eea;
    border-bottom: 2px solid #667eea;
}
QGroupBox {
    background: #111122;
    border: 1px solid #222244;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 20px;
    font-weight: bold;
    color: #667eea;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 15px;
    padding: 0 8px;
}
QLineEdit, QTextEdit, QComboBox, QSpinBox {
    background: #0d0d1a;
    border: 1px solid #222244;
    border-radius: 6px;
    padding: 8px 12px;
    color: #e0e0e0;
    selection-background-color: #667eea;
}
QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #667eea;
}
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 24px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7b92ee, stop:1 #8a5fb8);
}
QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5568cc, stop:1 #643b8a);
}
QPushButton:disabled {
    background: #1a1a2e;
    color: #555;
}
QTableWidget {
    background: #0d0d1a;
    alternate-background-color: #111122;
    border: 1px solid #222244;
    border-radius: 6px;
    gridline-color: #1a1a2e;
    color: #e0e0e0;
}
QTableWidget::item:selected {
    background: #667eea;
}
QHeaderView::section {
    background: #111122;
    color: #667eea;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #667eea;
    font-weight: bold;
}
QProgressBar {
    background: #0d0d1a;
    border: 1px solid #222244;
    border-radius: 6px;
    text-align: center;
    color: #e0e0e0;
    height: 20px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    border-radius: 5px;
}
QStatusBar {
    background: #111122;
    color: #8888aa;
    border-top: 1px solid #222244;
}
QScrollBar:vertical {
    background: #0a0a0a;
    width: 8px;
}
QScrollBar::handle:vertical {
    background: #222244;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #667eea;
}
QLabel#titleLabel {
    font-size: 11px;
    color: #667eea;
    font-weight: bold;
}
QLabel#subtitleLabel {
    font-size: 10px;
    color: #6666aa;
}
"""


# ── Syntax Highlighter for HTML ──────────────────────────────────────
class HtmlHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules = []

        tag_fmt = QTextCharFormat()
        tag_fmt.setForeground(QColor("#667eea"))
        self.rules.append((re.compile(r"</?\w+"), tag_fmt))
        self.rules.append((re.compile(r"/>|>"), tag_fmt))

        attr_fmt = QTextCharFormat()
        attr_fmt.setForeground(QColor("#c792ea"))
        self.rules.append((re.compile(r'\b\w+(?==)'), attr_fmt))

        val_fmt = QTextCharFormat()
        val_fmt.setForeground(QColor("#c3e88d"))
        self.rules.append((re.compile(r'"[^"]*"'), val_fmt))
        self.rules.append((re.compile(r"'[^']*'"), val_fmt))

        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(QColor("#546e7a"))
        self.rules.append((re.compile(r"<!--.*?-->", re.DOTALL), comment_fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            for m in pattern.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


# ── Workers ──────────────────────────────────────────────────────────
class FetchWorker(QThread):
    finished = pyqtSignal(str, str)  # html, url
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, url, timeout=15):
        super().__init__()
        self.url = url
        self.timeout = timeout

    def run(self):
        try:
            self.progress.emit(20)
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) WebScraper/1.0"}
            resp = requests.get(self.url, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            self.progress.emit(80)
            self.finished.emit(resp.text, self.url)
            self.progress.emit(100)
        except Exception as e:
            self.error.emit(str(e))


class BatchWorker(QThread):
    finished_one = pyqtSignal(int, str, str, str)  # row, title, status, url
    error_one = pyqtSignal(int, str)
    all_done = pyqtSignal()

    def __init__(self, urls, timeout=15):
        super().__init__()
        self.urls = urls
        self.timeout = timeout

    def run(self):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) WebScraper/1.0"}
        for i, url in enumerate(self.urls):
            try:
                resp = requests.get(url.strip(), headers=headers, timeout=self.timeout)
                resp.raise_for_status()
                resp.encoding = resp.apparent_encoding or "utf-8"
                soup = BeautifulSoup(resp.text, "html.parser")
                title = soup.title.string.strip() if soup.title and soup.title.string else "无标题"
                self.finished_one.emit(i, title, f"{resp.status_code}", url)
            except Exception as e:
                self.error_one.emit(i, str(e))
        self.all_done.emit()


class ImageWorker(QThread):
    image_found = pyqtSignal(str, str)  # src, alt
    finished = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, html, base_url):
        super().__init__()
        self.html = html
        self.base_url = base_url

    def run(self):
        soup = BeautifulSoup(self.html, "html.parser")
        count = 0
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if not src:
                continue
            full = urljoin(self.base_url, src)
            alt = img.get("alt", "")
            self.image_found.emit(full, alt)
            count += 1
        self.finished.emit(count)


# ── Main Window ──────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WebScraper - 网页抓取工具")
        self.setMinimumSize(800, 600)
        self.resize(1100, 750)
        self.current_html = ""
        self.current_url = ""
        self.extracted_links = []
        self.extracted_images = []
        self.extracted_text = ""

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)

        # Header
        header = QHBoxLayout()
        title = QLabel("🕷 WebScraper")
        title.setObjectName("titleLabel")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.addWidget(title)
        subtitle = QLabel("网页抓取工具 v1.0")
        subtitle.setObjectName("subtitleLabel")
        header.addWidget(subtitle)
        header.addStretch()
        layout.addLayout(header)

        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self._build_fetch_tab()
        self._build_links_tab()
        self._build_images_tab()
        self._build_text_tab()
        self._build_batch_tab()
        self._build_html_tab()

        # Status bar
        self.statusBar().showMessage("就绪")

    # ── Fetch Tab ────────────────────────────────────────────────────
    def _build_fetch_tab(self):
        tab = QWidget()
        v = QVBoxLayout(tab)

        grp = QGroupBox("URL 抓取器")
        g = QVBoxLayout(grp)

        row = QHBoxLayout()
        row.addWidget(QLabel("网址:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com")
        self.url_input.returnPressed.connect(self._fetch)
        row.addWidget(self.url_input)
        self.btn_fetch = QPushButton("抓取")
        self.btn_fetch.clicked.connect(self._fetch)
        row.addWidget(self.btn_fetch)
        g.addLayout(row)

        self.fetch_progress = QProgressBar()
        self.fetch_progress.setValue(0)
        g.addWidget(self.fetch_progress)

        self.fetch_result = QTextEdit()
        self.fetch_result.setReadOnly(True)
        self.fetch_result.setPlaceholderText("网页内容将显示在此处...")
        g.addWidget(self.fetch_result)

        btn_row = QHBoxLayout()
        btn_exp_csv = QPushButton("导出 CSV")
        btn_exp_csv.clicked.connect(lambda: self._export("csv"))
        btn_row.addWidget(btn_exp_csv)
        btn_exp_txt = QPushButton("导出 TXT")
        btn_exp_txt.clicked.connect(lambda: self._export("txt"))
        btn_row.addWidget(btn_exp_txt)
        btn_exp_json = QPushButton("导出 JSON")
        btn_exp_json.clicked.connect(lambda: self._export("json"))
        btn_row.addWidget(btn_exp_json)
        btn_row.addStretch()
        g.addLayout(btn_row)

        v.addWidget(grp)
        self.tabs.addTab(tab, "📡 URL 抓取器")

    # ── Links Tab ────────────────────────────────────────────────────
    def _build_links_tab(self):
        tab = QWidget()
        v = QVBoxLayout(tab)

        grp = QGroupBox("链接提取器")
        g = QVBoxLayout(grp)

        row = QHBoxLayout()
        self.btn_links = QPushButton("提取链接")
        self.btn_links.clicked.connect(self._extract_links)
        row.addWidget(self.btn_links)
        row.addWidget(QLabel("当前页面:"))
        self.links_url_label = QLabel("未加载")
        self.links_url_label.setStyleSheet("color: #667eea;")
        row.addWidget(self.links_url_label, 1)
        g.addLayout(row)

        self.links_table = QTableWidget(0, 3)
        self.links_table.setHorizontalHeaderLabels(["序号", "链接文本", "URL"])
        self.links_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.links_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.links_table.setAlternatingRowColors(True)
        g.addWidget(self.links_table)

        btn_row = QHBoxLayout()
        btn = QPushButton("导出 CSV")
        btn.clicked.connect(lambda: self._export_table(self.links_table, "links", "csv"))
        btn_row.addWidget(btn)
        btn = QPushButton("导出 JSON")
        btn.clicked.connect(lambda: self._export_table(self.links_table, "links", "json"))
        btn_row.addWidget(btn)
        btn_row.addStretch()
        g.addLayout(btn_row)

        v.addWidget(grp)
        self.tabs.addTab(tab, "🔗 链接提取器")

    # ── Images Tab ───────────────────────────────────────────────────
    def _build_images_tab(self):
        tab = QWidget()
        v = QVBoxLayout(tab)

        grp = QGroupBox("图片下载器")
        g = QVBoxLayout(grp)

        row = QHBoxLayout()
        self.btn_images = QPushButton("提取图片")
        self.btn_images.clicked.connect(self._extract_images)
        row.addWidget(self.btn_images)
        row.addWidget(QLabel("保存目录:"))
        self.img_dir = QLineEdit()
        self.img_dir.setPlaceholderText("选择图片保存目录...")
        row.addWidget(self.img_dir)
        btn_browse = QPushButton("浏览")
        btn_browse.clicked.connect(self._browse_img_dir)
        row.addWidget(btn_browse)
        g.addLayout(row)

        self.img_table = QTableWidget(0, 3)
        self.img_table.setHorizontalHeaderLabels(["序号", "图片 URL", "Alt 文本"])
        self.img_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.img_table.setAlternatingRowColors(True)
        g.addWidget(self.img_table)

        self.img_count_label = QLabel("共 0 张图片")
        self.img_count_label.setStyleSheet("color: #667eea;")
        g.addWidget(self.img_count_label)

        v.addWidget(grp)
        self.tabs.addTab(tab, "🖼 图片下载器")

    # ── Text Tab ─────────────────────────────────────────────────────
    def _build_text_tab(self):
        tab = QWidget()
        v = QVBoxLayout(tab)

        grp = QGroupBox("文本提取器")
        g = QVBoxLayout(grp)

        row = QHBoxLayout()
        self.btn_text = QPushButton("提取纯文本")
        self.btn_text.clicked.connect(self._extract_text)
        row.addWidget(self.btn_text)
        self.text_stats = QLabel("")
        self.text_stats.setStyleSheet("color: #667eea;")
        row.addWidget(self.text_stats, 1)
        g.addLayout(row)

        self.text_result = QTextEdit()
        self.text_result.setReadOnly(True)
        self.text_result.setPlaceholderText("纯文本将显示在此处...")
        g.addWidget(self.text_result)

        btn_row = QHBoxLayout()
        btn = QPushButton("导出 TXT")
        btn.clicked.connect(lambda: self._export_text("txt"))
        btn_row.addWidget(btn)
        btn = QPushButton("导出 JSON")
        btn.clicked.connect(lambda: self._export_text("json"))
        btn_row.addWidget(btn)
        btn_row.addStretch()
        g.addLayout(btn_row)

        v.addWidget(grp)
        self.tabs.addTab(tab, "📝 文本提取器")

    # ── Batch Tab ────────────────────────────────────────────────────
    def _build_batch_tab(self):
        tab = QWidget()
        v = QVBoxLayout(tab)

        grp = QGroupBox("批量抓取")
        g = QVBoxLayout(grp)

        row = QHBoxLayout()
        row.addWidget(QLabel("URL 列表 (每行一个):"))
        g.addLayout(row)

        self.batch_input = QTextEdit()
        self.batch_input.setMaximumHeight(120)
        self.batch_input.setPlaceholderText("https://example.com\nhttps://google.com\n...")
        g.addWidget(self.batch_input)

        row2 = QHBoxLayout()
        self.btn_batch = QPushButton("开始批量抓取")
        self.btn_batch.clicked.connect(self._batch_fetch)
        row2.addWidget(self.btn_batch)
        self.batch_progress = QProgressBar()
        row2.addWidget(self.batch_progress)
        g.addLayout(row2)

        self.batch_table = QTableWidget(0, 4)
        self.batch_table.setHorizontalHeaderLabels(["序号", "URL", "标题", "状态"])
        self.batch_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.batch_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.batch_table.setAlternatingRowColors(True)
        g.addWidget(self.batch_table)

        v.addWidget(grp)
        self.tabs.addTab(tab, "📦 批量抓取")

    # ── HTML Viewer Tab ──────────────────────────────────────────────
    def _build_html_tab(self):
        tab = QWidget()
        v = QVBoxLayout(tab)

        grp = QGroupBox("HTML 查看器")
        g = QVBoxLayout(grp)

        row = QHBoxLayout()
        self.btn_html = QPushButton("显示当前 HTML")
        self.btn_html.clicked.connect(self._show_html)
        row.addWidget(self.btn_html)
        self.html_stats = QLabel("")
        self.html_stats.setStyleSheet("color: #667eea;")
        row.addWidget(self.html_stats, 1)
        g.addLayout(row)

        self.html_view = QTextEdit()
        self.html_view.setReadOnly(True)
        self.html_view.setFont(QFont("Consolas", 10))
        self.html_view.setPlaceholderText("HTML 源码将显示在此处...")
        self.highlighter = HtmlHighlighter(self.html_view.document())
        g.addWidget(self.html_view)

        v.addWidget(grp)
        self.tabs.addTab(tab, "🔍 HTML 查看器")

    # ── Actions ──────────────────────────────────────────────────────
    def _fetch(self):
        url = self.url_input.text().strip()
        if not url:
            return
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            self.url_input.setText(url)
        self.btn_fetch.setEnabled(False)
        self.statusBar().showMessage(f"正在抓取: {url}")
        self.fetch_progress.setValue(0)

        self.worker = FetchWorker(url)
        self.worker.finished.connect(self._on_fetch_done)
        self.worker.error.connect(self._on_fetch_error)
        self.worker.progress.connect(self.fetch_progress.setValue)
        self.worker.start()

    def _on_fetch_done(self, html, url):
        self.current_html = html
        self.current_url = url
        self.fetch_result.setPlainText(html)
        self.links_url_label.setText(url)
        self.btn_fetch.setEnabled(True)
        self.fetch_progress.setValue(100)
        self.statusBar().showMessage(f"抓取成功: {url} ({len(html)} 字节)")

    def _on_fetch_error(self, msg):
        self.btn_fetch.setEnabled(True)
        self.fetch_progress.setValue(0)
        self.fetch_result.setPlainText(f"错误: {msg}")
        self.statusBar().showMessage(f"抓取失败: {msg}")

    def _extract_links(self):
        if not self.current_html:
            self.statusBar().showMessage("请先抓取一个页面")
            return
        soup = BeautifulSoup(self.current_html, "html.parser")
        self.extracted_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full = urljoin(self.current_url, href)
            text = a.get_text(strip=True) or href
            self.extracted_links.append((text, full))

        self.links_table.setRowCount(len(self.extracted_links))
        for i, (text, url) in enumerate(self.extracted_links):
            self.links_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.links_table.setItem(i, 1, QTableWidgetItem(text[:100]))
            self.links_table.setItem(i, 2, QTableWidgetItem(url))
        self.statusBar().showMessage(f"提取到 {len(self.extracted_links)} 个链接")

    def _extract_images(self):
        if not self.current_html:
            self.statusBar().showMessage("请先抓取一个页面")
            return
        self.img_worker = ImageWorker(self.current_html, self.current_url)
        self.img_worker.image_found.connect(self._on_image_found)
        self.img_worker.finished.connect(self._on_images_done)
        self.extracted_images = []
        self.img_table.setRowCount(0)
        self.img_worker.start()

    def _on_image_found(self, src, alt):
        self.extracted_images.append((src, alt))
        row = self.img_table.rowCount()
        self.img_table.insertRow(row)
        self.img_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self.img_table.setItem(row, 1, QTableWidgetItem(src))
        self.img_table.setItem(row, 2, QTableWidgetItem(alt))

    def _on_images_done(self, count):
        self.img_count_label.setText(f"共 {count} 张图片")
        self.statusBar().showMessage(f"提取到 {count} 张图片")

    def _browse_img_dir(self):
        d = QFileDialog.getExistingDirectory(self, "选择图片保存目录")
        if d:
            self.img_dir.setText(d)

    def _extract_text(self):
        if not self.current_html:
            self.statusBar().showMessage("请先抓取一个页面")
            return
        soup = BeautifulSoup(self.current_html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        lines = [l for l in text.splitlines() if l.strip()]
        self.extracted_text = "\n".join(lines)
        self.text_result.setPlainText(self.extracted_text)
        self.text_stats.setText(f"{len(self.extracted_text)} 字符 | {len(lines)} 行")
        self.statusBar().showMessage("文本提取完成")

    def _show_html(self):
        if not self.current_html:
            self.statusBar().showMessage("请先抓取一个页面")
            return
        self.html_view.setPlainText(self.current_html)
        self.html_stats.setText(f"{len(self.current_html)} 字节")
        self.statusBar().showMessage("HTML 已加载")

    def _batch_fetch(self):
        text = self.batch_input.toPlainText().strip()
        if not text:
            return
        urls = [u.strip() for u in text.splitlines() if u.strip()]
        if not urls:
            return
        self.batch_table.setRowCount(len(urls))
        self.batch_progress.setMaximum(len(urls))
        self.batch_progress.setValue(0)
        self.btn_batch.setEnabled(False)
        self.statusBar().showMessage(f"正在批量抓取 {len(urls)} 个 URL...")

        self.batch_worker = BatchWorker(urls)
        self.batch_worker.finished_one.connect(self._on_batch_one)
        self.batch_worker.error_one.connect(self._on_batch_error)
        self.batch_worker.all_done.connect(self._on_batch_done)
        self.batch_worker.start()

    def _on_batch_one(self, row, title, status, url):
        self.batch_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self.batch_table.setItem(row, 1, QTableWidgetItem(url))
        self.batch_table.setItem(row, 2, QTableWidgetItem(title))
        self.batch_table.setItem(row, 3, QTableWidgetItem(status))
        self.batch_progress.setValue(self.batch_progress.value() + 1)

    def _on_batch_error(self, row, msg):
        self.batch_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self.batch_table.setItem(row, 2, QTableWidgetItem("—"))
        item = QTableWidgetItem(f"错误: {msg[:60]}")
        item.setForeground(QColor("#ff6666"))
        self.batch_table.setItem(row, 3, item)
        self.batch_progress.setValue(self.batch_progress.value() + 1)

    def _on_batch_done(self):
        self.btn_batch.setEnabled(True)
        self.statusBar().showMessage("批量抓取完成")

    # ── Export ───────────────────────────────────────────────────────
    def _export(self, fmt):
        content = self.fetch_result.toPlainText()
        if not content:
            return
        if fmt == "csv":
            path, _ = QFileDialog.getSaveFileName(self, "导出 CSV", "scrape.csv", "CSV (*.csv)")
            if path:
                with open(path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["URL", "内容长度", "内容预览"])
                    writer.writerow([self.current_url, len(content), content[:500]])
        elif fmt == "txt":
            path, _ = QFileDialog.getSaveFileName(self, "导出 TXT", "scrape.txt", "TXT (*.txt)")
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
        elif fmt == "json":
            path, _ = QFileDialog.getSaveFileName(self, "导出 JSON", "scrape.json", "JSON (*.json)")
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({"url": self.current_url, "length": len(content), "content": content}, f, ensure_ascii=False, indent=2)
        self.statusBar().showMessage(f"已导出 {fmt.upper()} 文件")

    def _export_table(self, table, name, fmt):
        if table.rowCount() == 0:
            return
        rows = []
        for i in range(table.rowCount()):
            row = [table.item(i, j).text() if table.item(i, j) else "" for j in range(table.columnCount())]
            rows.append(row)
        headers = [table.horizontalHeaderItem(j).text() for j in range(table.columnCount())]

        if fmt == "csv":
            path, _ = QFileDialog.getSaveFileName(self, "导出 CSV", f"{name}.csv", "CSV (*.csv)")
            if path:
                with open(path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    writer.writerows(rows)
        elif fmt == "json":
            path, _ = QFileDialog.getSaveFileName(self, "导出 JSON", f"{name}.json", "JSON (*.json)")
            if path:
                data = []
                for row in rows:
                    data.append(dict(zip(headers, row)))
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        self.statusBar().showMessage(f"已导出 {fmt.upper()} 文件")

    def _export_text(self, fmt):
        text = self.text_result.toPlainText()
        if not text:
            return
        if fmt == "txt":
            path, _ = QFileDialog.getSaveFileName(self, "导出 TXT", "text.txt", "TXT (*.txt)")
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
        elif fmt == "json":
            path, _ = QFileDialog.getSaveFileName(self, "导出 JSON", "text.json", "JSON (*.json)")
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({"source": self.current_url, "text": text, "chars": len(text)}, f, ensure_ascii=False, indent=2)
        self.statusBar().showMessage(f"已导出 {fmt.upper()} 文件")


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
