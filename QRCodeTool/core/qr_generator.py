"""QR码生成器核心模块"""
import os
import io
import qrcode
from PIL import Image, ImageDraw


class QRGenerator:
    """QR码生成器"""

    @staticmethod
    def generate(
        data: str,
        fg_color: str = "#ffffff",
        bg_color: str = "#000000",
        size: int = 10,
        border: int = 4,
        logo_path: str | None = None,
        box_size: int = 10,
    ) -> Image.Image:
        """生成QR码图片"""
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=box_size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color=fg_color, back_color=bg_color).convert("RGB")

        # 缩放到指定尺寸
        if size != 10:
            target = size * 100
            img = img.resize((target, target), Image.Resampling.LANCZOS)

        # 嵌入Logo
        if logo_path and os.path.exists(logo_path):
            img = QRGenerator._embed_logo(img, logo_path)

        return img

    @staticmethod
    def _embed_logo(qr_img: Image.Image, logo_path: str) -> Image.Image:
        """在QR码中心嵌入Logo"""
        try:
            logo = Image.open(logo_path).convert("RGBA")
            qr_w, qr_h = qr_img.size
            logo_size = min(qr_w, qr_h) // 4
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

            # 创建圆形遮罩
            mask = Image.new("L", (logo_size, logo_size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse([0, 0, logo_size - 1, logo_size - 1], fill=255)

            # 白色背景圆形
            bg = Image.new("RGBA", (logo_size, logo_size), (255, 255, 255, 255))
            bg_mask = Image.new("RGBA", (logo_size, logo_size), (255, 255, 255, 0))
            bg_draw = ImageDraw.Draw(bg_mask)
            bg_draw.ellipse([0, 0, logo_size - 1, logo_size - 1], fill=(255, 255, 255, 255))

            # 粘贴logo
            pos = ((qr_w - logo_size) // 2, (qr_h - logo_size) // 2)
            qr_img = qr_img.convert("RGBA")
            qr_img.paste(bg, pos, bg_mask)
            qr_img.paste(logo, pos, mask)

            return qr_img.convert("RGB")
        except Exception:
            return qr_img

    @staticmethod
    def generate_wifi(ssid: str, password: str, security: str = "WPA", hidden: bool = False) -> str:
        """生成WiFi配置字符串"""
        hidden_str = "true" if hidden else "false"
        return f"WIFI:T:{security};S:{ssid};P:{password};H:{hidden_str};;"

    @staticmethod
    def generate_vcard(
        name: str,
        phone: str = "",
        email: str = "",
        org: str = "",
        title: str = "",
        url: str = "",
    ) -> str:
        """生成vCard字符串"""
        lines = [
            "BEGIN:VCARD",
            "VERSION:3.0",
            f"FN:{name}",
        ]
        if phone:
            lines.append(f"TEL:{phone}")
        if email:
            lines.append(f"EMAIL:{email}")
        if org:
            lines.append(f"ORG:{org}")
        if title:
            lines.append(f"TITLE:{title}")
        if url:
            lines.append(f"URL:{url}")
        lines.append("END:VCARD")
        return "\r\n".join(lines)

    @staticmethod
    def generate_svg(
        data: str,
        fg_color: str = "#ffffff",
        bg_color: str = "#000000",
        box_size: int = 10,
        border: int = 4,
    ) -> str:
        """生成SVG格式QR码"""
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=box_size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)

        matrix = qr.get_matrix()
        rows = len(matrix)
        cols = len(matrix[0]) if rows > 0 else 0
        size = rows * box_size

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">',
            f'  <rect width="{size}" height="{size}" fill="{bg_color}"/>',
        ]

        for r in range(rows):
            for c in range(cols):
                if matrix[r][c]:
                    x = c * box_size
                    y = r * box_size
                    svg_parts.append(f'  <rect x="{x}" y="{y}" width="{box_size}" height="{box_size}" fill="{fg_color}"/>')

        svg_parts.append("</svg>")
        return "\n".join(svg_parts)
