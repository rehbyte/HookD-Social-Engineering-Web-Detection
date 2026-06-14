"""
Generate a QR code PNG that links to your deployed HookD site.

Usage:
    pip install "qrcode[pil]"
    python make_qr.py https://your-app.onrender.com

Produces: hookd_qr.png  (print it and tape it to the booth)
"""
import sys

try:
    import qrcode
except ImportError:
    sys.exit('Missing dependency. Run:  pip install "qrcode[pil]"')


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python make_qr.py <your-deployed-url>")

    url = sys.argv[1].strip()
    out = sys.argv[2] if len(sys.argv) > 2 else "hookd_qr.png"

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,  # tolerant if slightly smudged
        box_size=12,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    # On-brand colors: green hook on near-black
    img = qr.make_image(fill_color="#c1ff72", back_color="#020d08")
    img.save(out)
    print(f"Saved {out} -> {url}")


if __name__ == "__main__":
    main()
