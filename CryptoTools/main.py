#!/usr/bin/env python3
"""
CryptoTools - 加密工具箱
一个功能齐全的加密工具桌面应用程序
"""

import sys
import os
import json
import base64
import hashlib
import uuid
import jwt
import secrets
import string
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox, QSpinBox,
    QTabWidget, QGroupBox, QGridLayout, QFileDialog, QMessageBox,
    QCheckBox, QSplitter, QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QFont, QClipboard, QDragEnterEvent, QDropEvent

# 导入加密库
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding, hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
    from cryptography.hazmat.backends import default_backend
    from cryptography import x509
    from cryptography.x509.oid import NameOID, ExtensionOID
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


class StyledButton(QPushButton):
    """样式化按钮"""
    def __init__(self, text: str, primary: bool = True):
        super().__init__(text)
        self.primary = primary
        self.setup_style()
    
    def setup_style(self):
        if self.primary:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #667eea, stop:1 #764ba2);
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #5a6fd6, stop:1 #6a4294);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #4e5fc2, stop:1 #5e3886);
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: #1a1a2e;
                    color: #a0a0a0;
                    border: 1px solid #2a2a3e;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background: #2a2a3e;
                    color: white;
                    border-color: #3a3a4e;
                }
            """)


class StyledLineEdit(QLineEdit):
    """样式化输入框"""
    def __init__(self, placeholder: str = ""):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setStyleSheet("""
            QLineEdit {
                background: #0d0d1a;
                color: #e0e0e0;
                border: 1px solid #2a2a3e;
                padding: 10px 14px;
                border-radius: 6px;
                font-size: 13px;
                selection-background-color: #667eea;
            }
            QLineEdit:focus {
                border-color: #667eea;
            }
        """)


class StyledTextEdit(QTextEdit):
    """样式化文本编辑框"""
    def __init__(self, placeholder: str = ""):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setStyleSheet("""
            QTextEdit {
                background: #0d0d1a;
                color: #e0e0e0;
                border: 1px solid #2a2a3e;
                padding: 10px;
                border-radius: 6px;
                font-size: 13px;
                font-family: Consolas, 'Courier New', monospace;
                selection-background-color: #667eea;
            }
            QTextEdit:focus {
                border-color: #667eea;
            }
        """)


class StyledComboBox(QComboBox):
    """样式化下拉框"""
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QComboBox {
                background: #0d0d1a;
                color: #e0e0e0;
                border: 1px solid #2a2a3e;
                padding: 10px 14px;
                border-radius: 6px;
                font-size: 13px;
                min-width: 120px;
            }
            QComboBox:hover {
                border-color: #667eea;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #a0a0a0;
            }
            QComboBox QAbstractItemView {
                background: #1a1a2e;
                color: #e0e0e0;
                border: 1px solid #2a2a3e;
                selection-background-color: #667eea;
            }
        """)


class StyledSpinBox(QSpinBox):
    """样式化数字输入框"""
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QSpinBox {
                background: #0d0d1a;
                color: #e0e0e0;
                border: 1px solid #2a2a3e;
                padding: 10px;
                border-radius: 6px;
                font-size: 13px;
            }
            QSpinBox:focus {
                border-color: #667eea;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background: #1a1a2e;
                border: none;
                width: 20px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #2a2a3e;
            }
        """)


class CardWidget(QFrame):
    """卡片式容器"""
    def __init__(self, title: str = ""):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background: #111122;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet("""
                QLabel {
                    color: #ffffff;
                    font-size: 16px;
                    font-weight: bold;
                    background: transparent;
                }
            """)
            self.layout.addWidget(title_label)


class TextEncryptionTab(QWidget):
    """文本加密选项卡"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 算法选择
        algo_group = CardWidget("加密算法")
        algo_layout = QHBoxLayout()
        
        self.algo_combo = StyledComboBox()
        self.algo_combo.addItems(["AES-256-CBC", "DES-CBC", "RSA-2048"])
        algo_layout.addWidget(QLabel("算法:"))
        algo_layout.addWidget(self.algo_combo)
        algo_layout.addStretch()
        
        algo_group.layout.addLayout(algo_layout)
        layout.addWidget(algo_group)
        
        # 密钥输入
        key_group = CardWidget("密钥设置")
        key_layout = QVBoxLayout()
        
        self.key_input = StyledLineEdit("输入密钥 (AES: 32字节, DES: 8字节)")
        key_layout.addWidget(QLabel("密钥:"))
        key_layout.addWidget(self.key_input)
        
        self.iv_input = StyledLineEdit("输入初始向量 (可选，留空自动生成)")
        key_layout.addWidget(QLabel("初始向量 (IV):"))
        key_layout.addWidget(self.iv_input)
        
        key_group.layout.addLayout(key_layout)
        layout.addWidget(key_group)
        
        # 输入文本
        input_group = CardWidget("输入文本")
        self.input_text = StyledTextEdit("在此输入要加密或解密的文本...")
        input_group.layout.addWidget(self.input_text)
        layout.addWidget(input_group)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        encrypt_btn = StyledButton("🔒 加密")
        encrypt_btn.clicked.connect(self.encrypt_text)
        decrypt_btn = StyledButton("🔓 解密")
        decrypt_btn.clicked.connect(self.decrypt_text)
        clear_btn = StyledButton("🗑️ 清除", primary=False)
        clear_btn.clicked.connect(self.clear_all)
        
        btn_layout.addWidget(encrypt_btn)
        btn_layout.addWidget(decrypt_btn)
        btn_layout.addWidget(clear_btn)
        layout.addLayout(btn_layout)
        
        # 输出文本
        output_group = CardWidget("输出结果")
        self.output_text = StyledTextEdit("结果将显示在此处...")
        self.output_text.setReadOnly(True)
        output_group.layout.addWidget(self.output_text)
        
        copy_btn = StyledButton("📋 复制结果", primary=False)
        copy_btn.clicked.connect(self.copy_output)
        output_group.layout.addWidget(copy_btn)
        
        layout.addWidget(output_group)
    
    def encrypt_text(self):
        if not CRYPTO_AVAILABLE:
            QMessageBox.warning(self, "错误", "加密库未安装，请运行: pip install cryptography")
            return
        
        text = self.input_text.toPlainText()
        if not text:
            QMessageBox.warning(self, "警告", "请输入要加密的文本")
            return
        
        key = self.key_input.text()
        iv = self.iv_input.text()
        
        try:
            algo = self.algo_combo.currentText()
            
            if algo == "AES-256-CBC":
                if len(key) < 32:
                    key = key.ljust(32, '\0')
                key = key[:32].encode('utf-8')
                
                if not iv:
                    iv = os.urandom(16)
                else:
                    iv = iv[:16].ljust(16, '\0').encode('utf-8')
                
                cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
                encryptor = cipher.encryptor()
                
                padder = padding.PKCS7(128).padder()
                padded_data = padder.update(text.encode('utf-8')) + padder.finalize()
                
                encrypted = encryptor.update(padded_data) + encryptor.finalize()
                result = base64.b64encode(iv + encrypted).decode('utf-8')
                
            elif algo == "DES-CBC":
                if len(key) < 8:
                    key = key.ljust(8, '\0')
                key = key[:8].encode('utf-8')
                
                if not iv:
                    iv = os.urandom(8)
                else:
                    iv = iv[:8].ljust(8, '\0').encode('utf-8')
                
                cipher = Cipher(algorithms.TripleDES(key.ljust(24, key)), modes.CBC(iv), backend=default_backend())
                encryptor = cipher.encryptor()
                
                padder = padding.PKCS7(64).padder()
                padded_data = padder.update(text.encode('utf-8')) + padder.finalize()
                
                encrypted = encryptor.update(padded_data) + encryptor.finalize()
                result = base64.b64encode(iv + encrypted).decode('utf-8')
                
            elif algo == "RSA-2048":
                private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048,
                    backend=default_backend()
                )
                public_key = private_key.public_key()
                
                encrypted = public_key.encrypt(
                    text.encode('utf-8'),
                    asym_padding.OAEP(
                        mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                
                private_pem = private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
                
                result = f"加密结果 (Base64):\n{base64.b64encode(encrypted).decode('utf-8')}\n\n"
                result += f"私钥 (请妥善保存):\n{private_pem.decode('utf-8')}"
            
            self.output_text.setPlainText(result)
            
        except Exception as e:
            QMessageBox.critical(self, "加密错误", f"加密失败: {str(e)}")
    
    def decrypt_text(self):
        if not CRYPTO_AVAILABLE:
            QMessageBox.warning(self, "错误", "加密库未安装，请运行: pip install cryptography")
            return
        
        text = self.input_text.toPlainText()
        if not text:
            QMessageBox.warning(self, "警告", "请输入要解密的文本")
            return
        
        key = self.key_input.text()
        
        try:
            algo = self.algo_combo.currentText()
            
            if algo == "AES-256-CBC":
                if len(key) < 32:
                    key = key.ljust(32, '\0')
                key = key[:32].encode('utf-8')
                
                encrypted_data = base64.b64decode(text)
                iv = encrypted_data[:16]
                encrypted = encrypted_data[16:]
                
                cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
                decryptor = cipher.decryptor()
                
                decrypted_padded = decryptor.update(encrypted) + decryptor.finalize()
                
                unpadder = padding.PKCS7(128).unpadder()
                result = unpadder.update(decrypted_padded) + unpadder.finalize()
                result = result.decode('utf-8')
                
            elif algo == "DES-CBC":
                if len(key) < 8:
                    key = key.ljust(8, '\0')
                key = key[:8].encode('utf-8')
                
                encrypted_data = base64.b64decode(text)
                iv = encrypted_data[:8]
                encrypted = encrypted_data[8:]
                
                cipher = Cipher(algorithms.TripleDES(key.ljust(24, key)), modes.CBC(iv), backend=default_backend())
                decryptor = cipher.decryptor()
                
                decrypted_padded = decryptor.update(encrypted) + decryptor.finalize()
                
                unpadder = padding.PKCS7(64).unpadder()
                result = unpadder.update(decrypted_padded) + unpadder.finalize()
                result = result.decode('utf-8')
                
            elif algo == "RSA-2048":
                QMessageBox.information(self, "提示", "RSA解密需要私钥，请在密钥框中输入私钥")
                return
            
            self.output_text.setPlainText(result)
            
        except Exception as e:
            QMessageBox.critical(self, "解密错误", f"解密失败: {str(e)}")
    
    def clear_all(self):
        self.input_text.clear()
        self.output_text.clear()
        self.key_input.clear()
        self.iv_input.clear()
    
    def copy_output(self):
        text = self.output_text.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            QMessageBox.information(self, "成功", "已复制到剪贴板")


class FileEncryptionTab(QWidget):
    """文件加密选项卡"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 文件选择
        file_group = CardWidget("文件选择")
        file_layout = QHBoxLayout()
        
        self.file_path = StyledLineEdit("选择要加密/解密的文件...")
        file_layout.addWidget(self.file_path)
        
        browse_btn = StyledButton("📁 浏览", primary=False)
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_btn)
        
        file_group.layout.addLayout(file_layout)
        layout.addWidget(file_group)
        
        # 密钥输入
        key_group = CardWidget("密钥设置")
        self.file_key = StyledLineEdit("输入加密密钥")
        key_group.layout.addWidget(QLabel("密钥:"))
        key_group.layout.addWidget(self.file_key)
        layout.addWidget(key_group)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        encrypt_btn = StyledButton("🔒 加密文件")
        encrypt_btn.clicked.connect(self.encrypt_file)
        decrypt_btn = StyledButton("🔓 解密文件")
        decrypt_btn.clicked.connect(self.decrypt_file)
        
        btn_layout.addWidget(encrypt_btn)
        btn_layout.addWidget(decrypt_btn)
        layout.addLayout(btn_layout)
        
        # 状态
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #a0a0a0; font-size: 13px;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
    
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件")
        if file_path:
            self.file_path.setText(file_path)
    
    def encrypt_file(self):
        if not CRYPTO_AVAILABLE:
            QMessageBox.warning(self, "错误", "加密库未安装")
            return
        
        file_path = self.file_path.text()
        key = self.file_key.text()
        
        if not file_path or not key:
            QMessageBox.warning(self, "警告", "请选择文件并输入密钥")
            return
        
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            key_bytes = key.encode('utf-8')[:32].ljust(32, b'\0')
            iv = os.urandom(16)
            
            cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(data) + padder.finalize()
            
            encrypted = encryptor.update(padded_data) + encryptor.finalize()
            
            output_path = file_path + '.encrypted'
            with open(output_path, 'wb') as f:
                f.write(iv + encrypted)
            
            self.status_label.setText(f"✅ 文件已加密: {output_path}")
            QMessageBox.information(self, "成功", f"文件已加密保存到:\n{output_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加密失败: {str(e)}")
    
    def decrypt_file(self):
        if not CRYPTO_AVAILABLE:
            QMessageBox.warning(self, "错误", "加密库未安装")
            return
        
        file_path = self.file_path.text()
        key = self.file_key.text()
        
        if not file_path or not key:
            QMessageBox.warning(self, "警告", "请选择文件并输入密钥")
            return
        
        try:
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()
            
            key_bytes = key.encode('utf-8')[:32].ljust(32, b'\0')
            iv = encrypted_data[:16]
            encrypted = encrypted_data[16:]
            
            cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            
            decrypted_padded = decryptor.update(encrypted) + decryptor.finalize()
            
            unpadder = padding.PKCS7(128).unpadder()
            data = unpadder.update(decrypted_padded) + unpadder.finalize()
            
            output_path = file_path.replace('.encrypted', '.decrypted')
            with open(output_path, 'wb') as f:
                f.write(data)
            
            self.status_label.setText(f"✅ 文件已解密: {output_path}")
            QMessageBox.information(self, "成功", f"文件已解密保存到:\n{output_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"解密失败: {str(e)}")


class HashCalculatorTab(QWidget):
    """哈希计算器选项卡"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 输入
        input_group = CardWidget("输入")
        self.hash_input = StyledTextEdit("输入要计算哈希的文本...")
        input_group.layout.addWidget(self.hash_input)
        layout.addWidget(input_group)
        
        # 算法选择
        algo_group = CardWidget("哈希算法")
        algo_layout = QHBoxLayout()
        
        self.algo_checks = {}
        algorithms = ["MD5", "SHA1", "SHA256", "SHA512", "BLAKE2b", "BLAKE2s"]
        
        for algo in algorithms:
            cb = QCheckBox(algo)
            cb.setChecked(True)
            cb.setStyleSheet("""
                QCheckBox {
                    color: #e0e0e0;
                    font-size: 13px;
                    spacing: 8px;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border-radius: 4px;
                    border: 1px solid #2a2a3e;
                    background: #0d0d1a;
                }
                QCheckBox::indicator:checked {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #667eea, stop:1 #764ba2);
                    border-color: #667eea;
                }
            """)
            self.algo_checks[algo] = cb
            algo_layout.addWidget(cb)
        
        algo_layout.addStretch()
        algo_group.layout.addLayout(algo_layout)
        layout.addWidget(algo_group)
        
        # 计算按钮
        calc_btn = StyledButton("🔢 计算哈希值")
        calc_btn.clicked.connect(self.calculate_hash)
        layout.addWidget(calc_btn)
        
        # 输出
        output_group = CardWidget("哈希结果")
        self.hash_output = StyledTextEdit()
        self.hash_output.setReadOnly(True)
        output_group.layout.addWidget(self.hash_output)
        
        copy_btn = StyledButton("📋 复制结果", primary=False)
        copy_btn.clicked.connect(self.copy_result)
        output_group.layout.addWidget(copy_btn)
        
        layout.addWidget(output_group)
    
    def calculate_hash(self):
        text = self.hash_input.toPlainText()
        if not text:
            QMessageBox.warning(self, "警告", "请输入文本")
            return
        
        results = []
        data = text.encode('utf-8')
        
        if self.algo_checks["MD5"].isChecked():
            results.append(f"MD5:\n{hashlib.md5(data).hexdigest()}")
        
        if self.algo_checks["SHA1"].isChecked():
            results.append(f"SHA1:\n{hashlib.sha1(data).hexdigest()}")
        
        if self.algo_checks["SHA256"].isChecked():
            results.append(f"SHA256:\n{hashlib.sha256(data).hexdigest()}")
        
        if self.algo_checks["SHA512"].isChecked():
            results.append(f"SHA512:\n{hashlib.sha512(data).hexdigest()}")
        
        if self.algo_checks["BLAKE2b"].isChecked():
            results.append(f"BLAKE2b:\n{hashlib.blake2b(data).hexdigest()}")
        
        if self.algo_checks["BLAKE2s"].isChecked():
            results.append(f"BLAKE2s:\n{hashlib.blake2s(data).hexdigest()}")
        
        self.hash_output.setPlainText("\n\n".join(results))
    
    def copy_result(self):
        text = self.hash_output.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            QMessageBox.information(self, "成功", "已复制到剪贴板")


class PasswordGeneratorTab(QWidget):
    """密码生成器选项卡"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 设置
        settings_group = CardWidget("密码设置")
        settings_layout = QGridLayout()
        
        settings_layout.addWidget(QLabel("密码长度:"), 0, 0)
        self.length_spin = StyledSpinBox()
        self.length_spin.setRange(4, 128)
        self.length_spin.setValue(16)
        settings_layout.addWidget(self.length_spin, 0, 1)
        
        self.upper_check = QCheckBox("大写字母 (A-Z)")
        self.upper_check.setChecked(True)
        self.upper_check.setStyleSheet("color: #e0e0e0;")
        settings_layout.addWidget(self.upper_check, 1, 0)
        
        self.lower_check = QCheckBox("小写字母 (a-z)")
        self.lower_check.setChecked(True)
        self.lower_check.setStyleSheet("color: #e0e0e0;")
        settings_layout.addWidget(self.lower_check, 1, 1)
        
        self.digits_check = QCheckBox("数字 (0-9)")
        self.digits_check.setChecked(True)
        self.digits_check.setStyleSheet("color: #e0e0e0;")
        settings_layout.addWidget(self.digits_check, 2, 0)
        
        self.symbols_check = QCheckBox("特殊字符 (!@#$...)")
        self.symbols_check.setChecked(True)
        self.symbols_check.setStyleSheet("color: #e0e0e0;")
        settings_layout.addWidget(self.symbols_check, 2, 1)
        
        settings_layout.addWidget(QLabel("生成数量:"), 3, 0)
        self.count_spin = StyledSpinBox()
        self.count_spin.setRange(1, 20)
        self.count_spin.setValue(5)
        settings_layout.addWidget(self.count_spin, 3, 1)
        
        settings_group.layout.addLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # 生成按钮
        gen_btn = StyledButton("🎲 生成密码")
        gen_btn.clicked.connect(self.generate_passwords)
        layout.addWidget(gen_btn)
        
        # 输出
        output_group = CardWidget("生成的密码")
        self.password_output = StyledTextEdit()
        self.password_output.setReadOnly(True)
        output_group.layout.addWidget(self.password_output)
        
        copy_btn = StyledButton("📋 复制全部", primary=False)
        copy_btn.clicked.connect(self.copy_passwords)
        output_group.layout.addWidget(copy_btn)
        
        layout.addWidget(output_group)
    
    def generate_passwords(self):
        chars = ""
        if self.upper_check.isChecked():
            chars += string.ascii_uppercase
        if self.lower_check.isChecked():
            chars += string.ascii_lowercase
        if self.digits_check.isChecked():
            chars += string.digits
        if self.symbols_check.isChecked():
            chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        if not chars:
            QMessageBox.warning(self, "警告", "请至少选择一种字符类型")
            return
        
        length = self.length_spin.value()
        count = self.count_spin.value()
        
        passwords = []
        for i in range(count):
            password = ''.join(secrets.choice(chars) for _ in range(length))
            passwords.append(f"{i+1}. {password}")
        
        self.password_output.setPlainText("\n".join(passwords))
    
    def copy_passwords(self):
        text = self.password_output.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            QMessageBox.information(self, "成功", "已复制到剪贴板")


class Base64Tab(QWidget):
    """Base64编码解码选项卡"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 输入
        input_group = CardWidget("输入")
        self.b64_input = StyledTextEdit("输入要编码或解码的文本...")
        input_group.layout.addWidget(self.b64_input)
        layout.addWidget(input_group)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        encode_btn = StyledButton("📝 编码")
        encode_btn.clicked.connect(self.encode_base64)
        decode_btn = StyledButton("📖 解码")
        decode_btn.clicked.connect(self.decode_base64)
        clear_btn = StyledButton("🗑️ 清除", primary=False)
        clear_btn.clicked.connect(lambda: (self.b64_input.clear(), self.b64_output.clear()))
        
        btn_layout.addWidget(encode_btn)
        btn_layout.addWidget(decode_btn)
        btn_layout.addWidget(clear_btn)
        layout.addLayout(btn_layout)
        
        # 输出
        output_group = CardWidget("输出")
        self.b64_output = StyledTextEdit()
        self.b64_output.setReadOnly(True)
        output_group.layout.addWidget(self.b64_output)
        
        copy_btn = StyledButton("📋 复制结果", primary=False)
        copy_btn.clicked.connect(self.copy_result)
        output_group.layout.addWidget(copy_btn)
        
        layout.addWidget(output_group)
    
    def encode_base64(self):
        text = self.b64_input.toPlainText()
        if not text:
            return
        
        try:
            encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
            self.b64_output.setPlainText(encoded)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"编码失败: {str(e)}")
    
    def decode_base64(self):
        text = self.b64_input.toPlainText()
        if not text:
            return
        
        try:
            decoded = base64.b64decode(text).decode('utf-8')
            self.b64_output.setPlainText(decoded)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"解码失败: {str(e)}")
    
    def copy_result(self):
        text = self.b64_output.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            QMessageBox.information(self, "成功", "已复制到剪贴板")


class JWTDecoderTab(QWidget):
    """JWT解码器选项卡"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 输入
        input_group = CardWidget("输入JWT Token")
        self.jwt_input = StyledTextEdit("粘贴JWT Token (格式: xxxxx.yyyyy.zzzzz)")
        input_group.layout.addWidget(self.jwt_input)
        layout.addWidget(input_group)
        
        # 解码按钮
        decode_btn = StyledButton("🔍 解码JWT")
        decode_btn.clicked.connect(self.decode_jwt)
        layout.addWidget(decode_btn)
        
        # 输出
        output_group = CardWidget("解码结果")
        
        self.header_output = StyledTextEdit()
        self.header_output.setReadOnly(True)
        self.header_output.setPlaceholderText("Header (头部)")
        output_group.layout.addWidget(QLabel("Header (头部):"))
        output_group.layout.addWidget(self.header_output)
        
        self.payload_output = StyledTextEdit()
        self.payload_output.setReadOnly(True)
        self.payload_output.setPlaceholderText("Payload (载荷)")
        output_group.layout.addWidget(QLabel("Payload (载荷):"))
        output_group.layout.addWidget(self.payload_output)
        
        layout.addWidget(output_group)
    
    def decode_jwt(self):
        token = self.jwt_input.toPlainText().strip()
        if not token:
            QMessageBox.warning(self, "警告", "请输入JWT Token")
            return
        
        try:
            # 解码header
            header_b64 = token.split('.')[0]
            # 添加padding
            header_b64 += '=' * (4 - len(header_b64) % 4)
            header = json.loads(base64.b64decode(header_b64))
            self.header_output.setPlainText(json.dumps(header, indent=2, ensure_ascii=False))
            
            # 解码payload
            payload_b64 = token.split('.')[1]
            payload_b64 += '=' * (4 - len(payload_b64) % 4)
            payload = json.loads(base64.b64decode(payload_b64))
            self.payload_output.setPlainText(json.dumps(payload, indent=2, ensure_ascii=False))
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"JWT解码失败: {str(e)}")


class CertificateViewerTab(QWidget):
    """证书查看器选项卡"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 文件选择
        file_group = CardWidget("选择证书文件")
        file_layout = QHBoxLayout()
        
        self.cert_path = StyledLineEdit("选择PEM或DER格式的证书文件...")
        file_layout.addWidget(self.cert_path)
        
        browse_btn = StyledButton("📁 浏览", primary=False)
        browse_btn.clicked.connect(self.browse_cert)
        file_layout.addWidget(browse_btn)
        
        file_group.layout.addLayout(file_layout)
        layout.addWidget(file_group)
        
        # 查看按钮
        view_btn = StyledButton("🔍 查看证书详情")
        view_btn.clicked.connect(self.view_certificate)
        layout.addWidget(view_btn)
        
        # 输出
        output_group = CardWidget("证书详情")
        self.cert_output = StyledTextEdit()
        self.cert_output.setReadOnly(True)
        output_group.layout.addWidget(self.cert_output)
        
        layout.addWidget(output_group)
    
    def browse_cert(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择证书文件", "",
            "证书文件 (*.pem *.crt *.cer *.der);;所有文件 (*)"
        )
        if file_path:
            self.cert_path.setText(file_path)
    
    def view_certificate(self):
        if not CRYPTO_AVAILABLE:
            QMessageBox.warning(self, "错误", "加密库未安装")
            return
        
        cert_path = self.cert_path.text()
        if not cert_path:
            QMessageBox.warning(self, "警告", "请选择证书文件")
            return
        
        try:
            with open(cert_path, 'rb') as f:
                cert_data = f.read()
            
            # 尝试PEM格式
            try:
                cert = x509.load_pem_x509_certificate(cert_data, default_backend())
            except:
                # 尝试DER格式
                cert = x509.load_der_x509_certificate(cert_data, default_backend())
            
            info = []
            info.append(f"主题: {cert.subject.rfc4514_string()}")
            info.append(f"颁发者: {cert.issuer.rfc4514_string()}")
            info.append(f"序列号: {cert.serial_number}")
            info.append(f"生效日期: {cert.not_valid_before_utc}")
            info.append(f"过期日期: {cert.not_valid_after_utc}")
            info.append(f"签名算法: {cert.signature_algorithm_oid._name}")
            
            # 获取SAN
            try:
                san = cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
                dns_names = san.value.get_values_for_type(x509.DNSName)
                if dns_names:
                    info.append(f"DNS名称: {', '.join(dns_names)}")
            except:
                pass
            
            self.cert_output.setPlainText("\n".join(info))
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取证书失败: {str(e)}")


class UUIDGeneratorTab(QWidget):
    """UUID生成器选项卡"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 设置
        settings_group = CardWidget("UUID设置")
        settings_layout = QHBoxLayout()
        
        settings_layout.addWidget(QLabel("UUID版本:"))
        self.version_combo = StyledComboBox()
        self.version_combo.addItems(["UUID v1 (基于时间)", "UUID v4 (随机)"])
        settings_layout.addWidget(self.version_combo)
        
        settings_layout.addWidget(QLabel("生成数量:"))
        self.count_spin = StyledSpinBox()
        self.count_spin.setRange(1, 50)
        self.count_spin.setValue(5)
        settings_layout.addWidget(self.count_spin)
        
        settings_layout.addStretch()
        settings_group.layout.addLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # 格式选项
        format_group = CardWidget("格式选项")
        format_layout = QHBoxLayout()
        
        self.upper_check = QCheckBox("大写")
        self.upper_check.setStyleSheet("color: #e0e0e0;")
        format_layout.addWidget(self.upper_check)
        
        self.no_dash_check = QCheckBox("无连字符")
        self.no_dash_check.setStyleSheet("color: #e0e0e0;")
        format_layout.addWidget(self.no_dash_check)
        
        self.braces_check = QCheckBox("花括号包围")
        self.braces_check.setStyleSheet("color: #e0e0e0;")
        format_layout.addWidget(self.braces_check)
        
        format_layout.addStretch()
        format_group.layout.addLayout(format_layout)
        layout.addWidget(format_group)
        
        # 生成按钮
        gen_btn = StyledButton("🎲 生成UUID")
        gen_btn.clicked.connect(self.generate_uuids)
        layout.addWidget(gen_btn)
        
        # 输出
        output_group = CardWidget("生成的UUID")
        self.uuid_output = StyledTextEdit()
        self.uuid_output.setReadOnly(True)
        output_group.layout.addWidget(self.uuid_output)
        
        copy_btn = StyledButton("📋 复制全部", primary=False)
        copy_btn.clicked.connect(self.copy_uuids)
        output_group.layout.addWidget(copy_btn)
        
        layout.addWidget(output_group)
    
    def generate_uuids(self):
        count = self.count_spin.value()
        version = self.version_combo.currentIndex()
        
        uuids = []
        for i in range(count):
            if version == 0:
                u = uuid.uuid1()
            else:
                u = uuid.uuid4()
            
            u_str = str(u)
            
            if self.upper_check.isChecked():
                u_str = u_str.upper()
            
            if self.no_dash_check.isChecked():
                u_str = u_str.replace('-', '')
            
            if self.braces_check.isChecked():
                u_str = f"{{{u_str}}}"
            
            uuids.append(f"{i+1}. {u_str}")
        
        self.uuid_output.setPlainText("\n".join(uuids))
    
    def copy_uuids(self):
        text = self.uuid_output.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            QMessageBox.information(self, "成功", "已复制到剪贴板")


class CryptoTools(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CryptoTools - 加密工具箱")
        self.setMinimumSize(900, 700)
        self.setup_ui()
        self.apply_dark_theme()
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题栏
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                padding: 20px;
            }
        """)
        header_layout = QVBoxLayout(header)
        
        title = QLabel("🔐 CryptoTools")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 28px;
                font-weight: bold;
                background: transparent;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("加密工具箱 - 安全、高效、易用")
        subtitle.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 14px;
                background: transparent;
            }
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        
        main_layout.addWidget(header)
        
        # 选项卡
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: #0a0a0a;
            }
            QTabBar::tab {
                background: #1a1a2e;
                color: #a0a0a0;
                padding: 12px 24px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background: #0a0a0a;
                color: #ffffff;
                border-bottom: 2px solid #667eea;
            }
            QTabBar::tab:hover {
                background: #2a2a3e;
                color: #ffffff;
            }
        """)
        
        # 添加选项卡
        self.tabs.addTab(TextEncryptionTab(), "🔒 文本加密")
        self.tabs.addTab(FileEncryptionTab(), "📁 文件加密")
        self.tabs.addTab(HashCalculatorTab(), "🔢 哈希计算")
        self.tabs.addTab(PasswordGeneratorTab(), "🔑 密码生成")
        self.tabs.addTab(Base64Tab(), "📝 Base64")
        self.tabs.addTab(JWTDecoderTab(), "🔍 JWT解码")
        self.tabs.addTab(CertificateViewerTab(), "📜 证书查看")
        self.tabs.addTab(UUIDGeneratorTab(), "🆔 UUID生成")
        
        main_layout.addWidget(self.tabs)
        
        # 底部状态栏
        footer = QFrame()
        footer.setStyleSheet("""
            QFrame {
                background: #111122;
                padding: 10px;
            }
        """)
        footer_layout = QHBoxLayout(footer)
        
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("color: #666666; font-size: 12px; background: transparent;")
        
        crypto_status = QLabel("✅ 加密库已加载" if CRYPTO_AVAILABLE else "⚠️ 加密库未安装")
        crypto_status.setStyleSheet("color: #a0a0a0; font-size: 12px; background: transparent;")
        
        footer_layout.addWidget(version_label)
        footer_layout.addStretch()
        footer_layout.addWidget(crypto_status)
        
        main_layout.addWidget(footer)
    
    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background: #0a0a0a;
            }
            QWidget {
                background: #0a0a0a;
                color: #e0e0e0;
                font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #e0e0e0;
            }
            QScrollArea {
                border: none;
                background: #0a0a0a;
            }
            QScrollBar:vertical {
                background: #0a0a0a;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #2a2a3e;
                min-height: 30px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #3a3a4e;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QScrollBar:horizontal {
                background: #0a0a0a;
                height: 10px;
                margin: 0;
            }
            QScrollBar::handle:horizontal {
                background: #2a2a3e;
                min-width: 30px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #3a3a4e;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0;
            }
        """)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = CryptoTools()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
