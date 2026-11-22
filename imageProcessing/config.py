# Model
MODEL_ID = "microsoft/trocr-base-printed"

# Preprocessing
UPSCALE_MIN_WIDTH = 1200  # narrower images get upscaled

# Gamma thresholds (avg brightness 0-255)
GAMMA_VERY_DARK = 85   # gamma 0.5
GAMMA_DARK = 127  # gamma 0.75
GAMMA_BRIGHT = 180  # gamma 1.5

INVERT_THRESHOLD = 100  # only used when bgr is not passed to preprocess
DENOISE_H = 10

ADAPTIVE_BLOCK_SIZE = 31
ADAPTIVE_C = 10
H_KERNEL_WIDTH = 25
MAX_LINE_HEIGHT_RATIO = 0.20
MIN_REGION_W = 15
MIN_REGION_H = 8
VERTICAL_OVERLAP_THRESH = 0.7
NUM_BEAMS = 3
MAX_NEW_TOKENS = 64
MIN_CROP_PX = 15
MIN_CONFIDENCE = -1.0
