"""QR码扫描识别模块"""
import os
from PIL import Image


class QRScanner:
    """QR码扫描器"""

    @staticmethod
    def scan_from_file(file_path: str) -> list[str]:
        """从图片文件识别QR码"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        results = []

        # 方法1: 使用 pyzbar (如果可用)
        try:
            from pyzbar.pyzbar import decode
            img = Image.open(file_path)
            decoded = decode(img)
            for item in decoded:
                if item.type == 'QRCODE':
                    results.append(item.data.decode('utf-8', errors='replace'))
            if results:
                return results
        except ImportError:
            pass

        # 方法2: 使用 opencv
        try:
            import cv2
            img = cv2.imread(file_path)
            if img is not None:
                detector = cv2.QRCodeDetector()
                data, points, _ = detector.detectAndDecode(img)
                if data:
                    results.append(data)

                # 尝试多QR码检测
                try:
                    retval, decoded_info, points, _ = detector.detectAndDecodeMulti(img)
                    if retval:
                        for info in decoded_info:
                            if info and info not in results:
                                results.append(info)
                except Exception:
                    pass
        except Exception:
            pass

        if not results:
            raise ValueError("未能识别到二维码，请确保图片包含有效的二维码")

        return results

    @staticmethod
    def scan_from_image(image: Image.Image) -> list[str]:
        """从PIL图片对象识别QR码"""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            image.save(tmp.name)
            tmp_path = tmp.name

        try:
            return QRScanner.scan_from_file(tmp_path)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
