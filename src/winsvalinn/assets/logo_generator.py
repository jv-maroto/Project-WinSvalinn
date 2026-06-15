"""
Logo Generator - WinSvalinn
Generates the app logo and icon programmatically using Pillow.
Based on Svalinn — the Norse shield that protects the world from the sun's fire.
"""

import math
import os

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = None


def create_logo(output_dir="assets", size=256):
    """Generate the WinSvalinn logo."""
    if not Image:
        print("Pillow not installed, skipping logo generation")
        return None

    os.makedirs(output_dir, exist_ok=True)

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2, size // 2
    r = size // 2 - 10

    # ── Background: dark circle with fiery outer glow ──
    # Outer fire glow (orange/red gradient rings)
    fire_colors = [
        (255, 100, 20, 15),  # outermost - deep orange
        (255, 120, 30, 25),
        (255, 140, 40, 35),
        (255, 160, 50, 45),
        (255, 80, 10, 55),  # red-fire
        (200, 60, 10, 40),
    ]
    for i, color in enumerate(fire_colors):
        offset = (len(fire_colors) - i) * 4
        draw.ellipse(
            [cx - r - offset, cy - r - offset, cx + r + offset, cy + r + offset], fill=color
        )

    # Solar rays emanating outward (8 rays)
    ray_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ray_draw = ImageDraw.Draw(ray_layer)
    num_rays = 12
    for i in range(num_rays):
        angle = (2 * math.pi * i) / num_rays
        inner_r = r - 5
        outer_r = r + 15
        # Thin triangle ray
        tip_x = cx + outer_r * math.cos(angle)
        tip_y = cy + outer_r * math.sin(angle)
        spread = math.pi / (num_rays * 2)
        left_x = cx + inner_r * math.cos(angle - spread)
        left_y = cy + inner_r * math.sin(angle - spread)
        right_x = cx + inner_r * math.cos(angle + spread)
        right_y = cy + inner_r * math.sin(angle + spread)

        alpha = 120 if i % 2 == 0 else 70
        ray_draw.polygon(
            [(tip_x, tip_y), (left_x, left_y), (right_x, right_y)], fill=(255, 140, 30, alpha)
        )
    img = Image.alpha_composite(img, ray_layer)
    draw = ImageDraw.Draw(img)

    # Dark background circle (the protected world)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(13, 17, 23, 255))

    # Subtle accent ring (blue-cyan digital feel)
    ring_color = (88, 166, 255, 200)
    draw.ellipse([cx - r + 2, cy - r + 2, cx + r - 2, cy + r - 2], outline=ring_color, width=3)

    # Inner dark area
    inner_r = r - 14
    draw.ellipse([cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r], fill=(18, 22, 30, 255))

    # ── Svalinn Shield ──
    shield_w = int(size * 0.34)
    shield_h = int(size * 0.42)
    shield_top = cy - shield_h // 2 - 4

    # Shield outline (bright accent)
    shield_points = [
        (cx, shield_top),  # top center
        (cx + shield_w, shield_top + shield_h * 0.22),  # right shoulder
        (cx + shield_w * 0.92, shield_top + shield_h * 0.65),  # right lower
        (cx, shield_top + shield_h),  # bottom point
        (cx - shield_w * 0.92, shield_top + shield_h * 0.65),  # left lower
        (cx - shield_w, shield_top + shield_h * 0.22),  # left shoulder
    ]

    # Shield glow
    draw.polygon(shield_points, fill=(88, 166, 255, 30), outline=(88, 166, 255, 180))

    # Shield body with gradient effect (dark steel)
    inset = 4
    shield_inner = [
        (cx, shield_top + inset),
        (cx + shield_w - inset, shield_top + shield_h * 0.22 + inset // 2),
        (cx + (shield_w - inset) * 0.92, shield_top + shield_h * 0.65),
        (cx, shield_top + shield_h - inset),
        (cx - (shield_w - inset) * 0.92, shield_top + shield_h * 0.65),
        (cx - shield_w + inset, shield_top + shield_h * 0.22 + inset // 2),
    ]
    draw.polygon(shield_inner, fill=(25, 35, 50, 240), outline=(88, 166, 255, 255))

    # ── Shield center decoration: Norse-inspired cross/knot ──
    # Vertical line through shield center
    line_color = (88, 166, 255, 180)
    mid_y_top = shield_top + int(shield_h * 0.18)
    mid_y_bot = shield_top + int(shield_h * 0.85)
    draw.line([(cx, mid_y_top), (cx, mid_y_bot)], fill=line_color, width=2)

    # Horizontal line
    mid_y = cy + 2
    hleft = cx - int(shield_w * 0.65)
    hright = cx + int(shield_w * 0.65)
    draw.line([(hleft, mid_y), (hright, mid_y)], fill=line_color, width=2)

    # Small diamond at center (shield boss)
    boss_size = int(size * 0.045)
    boss_y = mid_y
    draw.polygon(
        [
            (cx, boss_y - boss_size),
            (cx + boss_size, boss_y),
            (cx, boss_y + boss_size),
            (cx - boss_size, boss_y),
        ],
        fill=(88, 166, 255, 220),
        outline=(130, 200, 255, 255),
    )

    # ── Fire blocking effect: small flame wisps at shield edges ──
    flame_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    flame_draw = ImageDraw.Draw(flame_layer)

    # Small flame accents at shield shoulders (fire being blocked)
    flame_positions = [
        (cx + shield_w + 2, shield_top + shield_h * 0.22, -1),  # right
        (cx - shield_w - 2, shield_top + shield_h * 0.22, 1),  # left
        (cx + shield_w * 0.5, shield_top - 3, 0),  # top-right
        (cx - shield_w * 0.5, shield_top - 3, 0),  # top-left
    ]

    for fx, fy, direction in flame_positions:
        flame_h = int(size * 0.06)
        flame_w = int(size * 0.025)
        points = [
            (fx, fy),
            (fx + flame_w * direction if direction != 0 else fx + flame_w, fy - flame_h * 0.6),
            (fx, fy - flame_h),
            (fx - flame_w * direction if direction != 0 else fx - flame_w, fy - flame_h * 0.6),
        ]
        flame_draw.polygon(points, fill=(255, 120, 20, 100))
        # Inner bright core
        small_h = int(flame_h * 0.5)
        small_w = int(flame_w * 0.5)
        inner_points = [
            (fx, fy),
            (fx + small_w, fy - small_h * 0.6),
            (fx, fy - small_h),
            (fx - small_w, fy - small_h * 0.6),
        ]
        flame_draw.polygon(inner_points, fill=(255, 200, 80, 130))

    img = Image.alpha_composite(img, flame_layer)
    draw = ImageDraw.Draw(img)

    # ── Windows-inspired 4-pane in upper half of shield ──
    pane_size = int(size * 0.04)
    pane_gap = int(size * 0.012)
    pane_cx = cx
    pane_cy = cy - int(shield_h * 0.15)

    pane_color = (88, 166, 255, 160)
    # Top-left
    draw.rectangle(
        [
            pane_cx - pane_size - pane_gap // 2,
            pane_cy - pane_size - pane_gap // 2,
            pane_cx - pane_gap // 2,
            pane_cy - pane_gap // 2,
        ],
        fill=pane_color,
    )
    # Top-right
    draw.rectangle(
        [
            pane_cx + pane_gap // 2,
            pane_cy - pane_size - pane_gap // 2,
            pane_cx + pane_size + pane_gap // 2,
            pane_cy - pane_gap // 2,
        ],
        fill=pane_color,
    )
    # Bottom-left
    draw.rectangle(
        [
            pane_cx - pane_size - pane_gap // 2,
            pane_cy + pane_gap // 2,
            pane_cx - pane_gap // 2,
            pane_cy + pane_size + pane_gap // 2,
        ],
        fill=pane_color,
    )
    # Bottom-right
    draw.rectangle(
        [
            pane_cx + pane_gap // 2,
            pane_cy + pane_gap // 2,
            pane_cx + pane_size + pane_gap // 2,
            pane_cy + pane_size + pane_gap // 2,
        ],
        fill=pane_color,
    )

    # ── Performance speed lines at bottom-right ──
    for i, offset in enumerate([-10, 0, 10]):
        y = cy + int(shield_h * 0.3) + offset
        x_start = cx + inner_r - 22
        x_end = cx + inner_r - 6
        alpha = 180 - i * 40
        draw.line([(x_start, y), (x_end, y)], fill=(88, 166, 255, alpha), width=2)

    # Save PNG
    png_path = os.path.join(output_dir, "logo.png")
    img.save(png_path, "PNG")

    # Generate multiple sizes for ICO
    ico_sizes = [16, 24, 32, 48, 64, 128, 256]
    ico_images = []
    for s in ico_sizes:
        resized = img.resize((s, s), Image.LANCZOS)
        ico_images.append(resized)

    ico_path = os.path.join(output_dir, "icon.ico")
    ico_images[0].save(
        ico_path, format="ICO", sizes=[(s, s) for s in ico_sizes], append_images=ico_images[1:]
    )

    # Small logo for sidebar (40x40)
    small = img.resize((40, 40), Image.LANCZOS)
    small_path = os.path.join(output_dir, "logo_small.png")
    small.save(small_path, "PNG")

    # Splash logo (400x400)
    splash = img.resize((400, 400), Image.LANCZOS)
    splash_path = os.path.join(output_dir, "logo_splash.png")
    splash.save(splash_path, "PNG")

    print(f"Logo generated: {png_path}")
    print(f"Icon generated: {ico_path}")

    return ico_path


def get_icon_path():
    """Get the path to the icon file, generate if needed."""
    base = os.path.dirname(os.path.abspath(__file__))
    ico_path = os.path.join(base, "icon.ico")
    if not os.path.exists(ico_path):
        create_logo(base)
    return ico_path


def get_logo_path(variant="logo.png"):
    """Get path to a logo variant."""
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, variant)
    if not os.path.exists(path):
        create_logo(base)
    return path


if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    create_logo(base)
    print("Done!")
