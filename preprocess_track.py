import cv2
import numpy as np
import os

# === SETTINGS ===
RAW_DIR = "tracks_raw"
OUT_DIR = "tracks"

os.makedirs(OUT_DIR, exist_ok=True)


def is_red(pixel):
    """
    Detect the actual red racing outline on RacingCircuits maps.
    Eliminates grey pitlane, shadows, labels, etc.
    """
    b, g, r = map(int, pixel)

    # Convert to HSV
    hsv = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2HSV)[0][0]
    h, s, v = hsv

    # Red hue area
    hsv_red = (h < 12 or h > 168) and s > 70 and v > 60

    # RGB dominance filter (avoids grey)
    rgb_red = (r > g + 40) and (r > b + 40)

    return hsv_red and rgb_red


def preprocess_track(filename):
    print(f"🔧 Processing {filename}")

    img = cv2.imread(os.path.join(RAW_DIR, filename))

    if img is None:
        print("❌ Failed to load", filename)
        return

    h, w, _ = img.shape
    print(f"   Original size preserved: {w}x{h}")

    # Create empty mask
    mask = np.zeros((h, w), np.uint8)

    # Detect ONLY red racing outline
    for y in range(h):
        for x in range(w):
            if is_red(img[y, x]):
                mask[y, x] = 255

    # Thin dilation to strengthen but not overpower the track
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)

    # Convert 1-channel mask to 3-channel image
    final_img = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

    out_name = filename.replace(".png", "_clean.png")
    out_path = os.path.join(OUT_DIR, out_name)

    cv2.imwrite(out_path, final_img)

    print(f"   ✅ Saved cleaned track → {out_path}")


if __name__ == "__main__":
    files = [f for f in os.listdir(RAW_DIR) if f.lower().endswith(".png")]

    if not files:
        print(f"❌ No PNG files in {RAW_DIR}/")
        exit()

    for f in files:
        preprocess_track(f)

    print("\n🎉 Done! Cleaned tracks saved in /tracks/")
