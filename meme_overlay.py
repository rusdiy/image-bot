from PIL import Image, ImageDraw, ImageFont, ImageSequence
import requests
import io
import os
from bs4 import BeautifulSoup


DEFAULT_FONT_PATH = "assets/font/impact.ttf"


class MemeTextOverlay:
    def __init__(self, font_path=DEFAULT_FONT_PATH):
        if not os.path.exists(font_path):
            raise FileNotFoundError(f"Font not found: {font_path}")
        self.font_path = font_path

    def tenor_parser(self, url: str):
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(resp.text, 'html.parser')
        meta = soup.find("meta", property="og:image")
        gif_url = meta['content'] if meta else url
        return gif_url

    def apply_to_image(self, image_input: str, text: str):
        """image_input can be a PIL.Image, a URL, or raw bytes."""
        if isinstance(image_input, str) and image_input.startswith("http"):
            if image_input.startswith("https://tenor.com/"):
                image_input = self.tenor_parser(image_input)
            print(f"Downloading image from {image_input}")
            response = requests.get(image_input, stream=True)
            if not response.ok:
                raise ValueError(
                    f"Failed to download image: {response.status_code}"
                )
            image = Image.open(io.BytesIO(response.content))
        elif isinstance(image_input, str) and os.path.exists(image_input):
            image = Image.open(image_input)
        elif isinstance(image_input, bytes):
            image = Image.open(io.BytesIO(image_input))
        elif isinstance(image_input, Image.Image):
            image = image_input
        else:
            raise TypeError("Unsupported image_input type")
        text = text.upper()
        if getattr(image, "is_animated", False):
            return self._process_animated(
                image, text
            )
        else:
            return self._process_static(
                image, text
            )

    def _process_static(self, image: Image.Image, text: str):
        buffer = io.BytesIO()
        is_transparent = (
            image.mode in ("RGBA", "LA") or
            (image.mode == "P" and "transparency" in image.info)
        )
        format = image.format or ""
        frame = image.convert("RGBA" if is_transparent else "RGB")
        frame = self._draw_text(frame, text)
        frame.save(buffer, format=format.upper())
        buffer.seek(0)
        return buffer, f"result.{format.lower()}"

    def _process_animated(self, image: Image.Image, text: str):
        buffer = io.BytesIO()
        frames = []
        duration = image.info.get("duration", 100)
        loop = image.info.get("loop", 0)

        for frame in ImageSequence.Iterator(image):
            is_transparent = (
                image.mode in ("RGBA", "LA") or
                (image.mode == "P" and "transparency" in image.info)
            )
            rgb_frame = frame.convert("RGBA" if is_transparent else "RGB")
            rgb_frame = self._draw_text(rgb_frame, text)
            frames.append(rgb_frame)

        frames[0].save(
            buffer,
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=loop,
            format="GIF",
        )
        buffer.seek(0)
        return buffer, "result.gif"

    def _draw_text(self, image, text, max_lines=2, padding_ratio=0.05):
        draw = ImageDraw.Draw(image)
        width, height = image.size

        font = ImageFont.truetype(self.font_path, size=10)
        padding = int(height * padding_ratio)
        max_width = width - 2 * padding
        max_text_height = height * 0.3

        def wrap_text_by_pixel(text, font, max_width):
            words = text.split()
            lines = []
            line = ""
            for word in words:
                test_line = line + (" " if line else "") + word
                if draw.textlength(test_line, font=font) <= max_width:
                    line = test_line
                else:
                    lines.append(line)
                    line = word
            if line:
                lines.append(line)
            return lines

        def fits(font):
            lines = wrap_text_by_pixel(text, font, max_width)
            if len(lines) > max_lines:
                return False
            line_height = font.getbbox("Ay")[3]
            total_height = len(lines) * line_height + (len(lines) - 1) * 5
            return total_height <= max_text_height

        # Binary search font size
        min_size, max_size = 10, int(height * 0.2)
        while min_size < max_size:
            mid = (min_size + max_size + 1) // 2
            test_font = font.font_variant(size=mid)
            if fits(test_font):
                min_size = mid
            else:
                max_size = mid - 1

        final_font = font.font_variant(size=min_size)
        lines = wrap_text_by_pixel(text, final_font, max_width)

        # Vertical positioning
        line_height = final_font.getbbox("Ay")[3]
        total_text_height = len(lines) * line_height + (len(lines) - 1) * 5
        y = height - padding - total_text_height

        for line in lines:
            text_width = draw.textlength(line, font=final_font)
            x = (width - text_width) // 2
            draw.text(
                (x, y),
                line,
                font=final_font,
                fill="white",
                stroke_fill="black",
                stroke_width=2
            )
            y += line_height + 5

        return image
