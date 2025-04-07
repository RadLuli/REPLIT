from PIL import Image, ImageEnhance, ImageStat, ImageFilter, ImageOps
from io import BytesIO
import math

# Try to import numpy, with a simple fallback if not available
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    
    # Define a simple array class to mimic basic numpy functionality
    class SimpleArray:
        def __init__(self, data):
            self.data = data
            self.size = len(data) if isinstance(data, list) else 0
            
    # Define simple fallback functions for numpy operations
    def simple_mean(array):
        """Calculate mean without numpy"""
        if not array or len(array) == 0:
            return 0
        return sum(array) / len(array)
    
    def simple_array(img):
        """Create a simple 2D array from PIL Image without numpy"""
        width, height = img.size
        pixels = list(img.getdata())
        if isinstance(pixels[0], tuple):  # RGB image
            arrays = []
            for channel in range(len(pixels[0])):
                channel_pixels = [p[channel] for p in pixels]
                arrays.append(SimpleArray(channel_pixels))
            return arrays
        else:  # Grayscale
            return SimpleArray(pixels)

# Define a function to analyze image without OpenCV and with numpy fallbacks
def analyze_image(image):
    """
    Analyze the uploaded image to extract relevant photographic details using PIL
    
    Args:
        image: A PIL Image
    
    Returns:
        dict: A dictionary containing image analysis results
    """
    # Get image dimensions
    width, height = image.size
    
    # Convert to grayscale for some analyses
    gray = image.convert('L')
    
    # Calculate basic stats using PIL directly
    stat = ImageStat.Stat(image)
    stat_gray = ImageStat.Stat(gray)
    
    # Calculate brightness (0-255)
    brightness = stat_gray.mean[0]
    
    # Calculate contrast using standard deviation
    contrast = stat_gray.stddev[0]
    
    # Calculate sharpness using a simple edge detection method
    edge_image = gray.filter(ImageFilter.FIND_EDGES)
    sharpness = ImageStat.Stat(edge_image).mean[0]
    
    # Calculate exposure - simple version based on histogram
    hist = gray.histogram()
    dark_pixels = sum(hist[:85])
    light_pixels = sum(hist[170:])
    exposure = "balanced"
    if dark_pixels > light_pixels:
        exposure = "underexposed"
    elif dark_pixels < light_pixels:
        exposure = "overexposed"
    
    # Calculate rule of thirds - simple approximation
    third_h, third_v = height // 3, width // 3
    
    # For composition analysis, we'll use a simplified approach that works with or without numpy
    if HAS_NUMPY:
        # Use numpy for more accurate analysis
        gray_np = np.array(gray)
        
        # Extract regions of interest
        center = gray_np[third_h:2*third_h, third_v:2*third_v]
        top_left = gray_np[:third_h, :third_v]
        top_right = gray_np[:third_h, 2*third_v:]
        bottom_left = gray_np[2*third_h:, :third_v]
        bottom_right = gray_np[2*third_h:, 2*third_v:]
        
        # Calculate intensities
        center_intensity = np.mean(center) if center.size > 0 else 0
        corner_intensities = [
            np.mean(top_left) if top_left.size > 0 else 0,
            np.mean(top_right) if top_right.size > 0 else 0,
            np.mean(bottom_left) if bottom_left.size > 0 else 0,
            np.mean(bottom_right) if bottom_right.size > 0 else 0
        ]
        corner_intensity = np.mean(corner_intensities)
        
        # Calculate color statistics for RGB image
        if image.mode == 'RGB':
            # Split into channels
            r, g, b = image.split()
            r_np, g_np, b_np = np.array(r), np.array(g), np.array(b)
            
            # Get average channel values
            avg_r, avg_g, avg_b = np.mean(r_np), np.mean(g_np), np.mean(b_np)
        else:
            avg_r, avg_g, avg_b = 0, 0, 0
            
    else:
        # Fallback method without numpy - use PIL's ImageStat
        # This is less accurate but works without numpy
        
        # Create cropped regions 
        center_crop = gray.crop((third_v, third_h, 2*third_v, 2*third_h))
        top_left_crop = gray.crop((0, 0, third_v, third_h))
        top_right_crop = gray.crop((2*third_v, 0, width, third_h))
        bottom_left_crop = gray.crop((0, 2*third_h, third_v, height))
        bottom_right_crop = gray.crop((2*third_v, 2*third_h, width, height))
        
        # Get intensities using PIL
        center_intensity = ImageStat.Stat(center_crop).mean[0]
        corner_intensities = [
            ImageStat.Stat(top_left_crop).mean[0],
            ImageStat.Stat(top_right_crop).mean[0],
            ImageStat.Stat(bottom_left_crop).mean[0],
            ImageStat.Stat(bottom_right_crop).mean[0]
        ]
        corner_intensity = sum(corner_intensities) / len(corner_intensities)
        
        # Get color info using PIL
        if image.mode == 'RGB':
            r, g, b = image.split()
            avg_r = ImageStat.Stat(r).mean[0]
            avg_g = ImageStat.Stat(g).mean[0]
            avg_b = ImageStat.Stat(b).mean[0]
        else:
            avg_r, avg_g, avg_b = 0, 0, 0
    
    # Simple color balance check
    color_balance = "balanced"
    max_channel = max(avg_r, avg_g, avg_b)
    
    if max_channel == avg_r and avg_r > 1.2 * avg_g and avg_r > 1.2 * avg_b:
        color_balance = "red dominant"
    elif max_channel == avg_g and avg_g > 1.2 * avg_r and avg_g > 1.2 * avg_b:
        color_balance = "green dominant"
    elif max_channel == avg_b and avg_b > 1.2 * avg_r and avg_b > 1.2 * avg_g:
        color_balance = "blue dominant"
    
    # Approximate saturation calculation
    saturation = 0
    try:
        hsv_image = image.convert('HSV')
        h, s, v = hsv_image.split()
        saturation = ImageStat.Stat(s).mean[0]
    except Exception:
        # If HSV conversion fails
        saturation = 0
    
    # Return analysis results
    return {
        "dimensions": f"{width}x{height}",
        "aspect_ratio": round(width / height, 2),
        "brightness": round(brightness, 2),
        "contrast": round(contrast, 2),
        "sharpness": round(sharpness, 2),
        "exposure": exposure,
        "color_balance": color_balance,
        "saturation": round(saturation, 2),
        "composition": "centered" if center_intensity > corner_intensity * 1.2 else "rule of thirds",
        "has_faces": False,  # We can't detect faces reliably without OpenCV
        "number_of_faces": 0,
        "red_channel_avg": round(avg_r, 2),
        "green_channel_avg": round(avg_g, 2),
        "blue_channel_avg": round(avg_b, 2),
    }

def enhance_image_brightness(image, factor=1.5):
    """
    Enhance the brightness of an image
    
    Args:
        image: A PIL Image
        factor: Brightness enhancement factor (1.0 means original brightness)
    
    Returns:
        PIL Image: Enhanced image
    """
    enhancer = ImageEnhance.Brightness(image)
    return enhancer.enhance(factor)

def enhance_image_contrast(image, factor=1.5):
    """
    Enhance the contrast of an image
    
    Args:
        image: A PIL Image
        factor: Contrast enhancement factor (1.0 means original contrast)
    
    Returns:
        PIL Image: Enhanced image
    """
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(factor)

def enhance_image_sharpness(image, factor=1.5):
    """
    Enhance the sharpness of an image
    
    Args:
        image: A PIL Image
        factor: Sharpness enhancement factor (1.0 means original sharpness)
    
    Returns:
        PIL Image: Enhanced image
    """
    enhancer = ImageEnhance.Sharpness(image)
    return enhancer.enhance(factor)

def enhance_image_color(image, factor=1.5):
    """
    Enhance the color of an image
    
    Args:
        image: A PIL Image
        factor: Color enhancement factor (1.0 means original color)
    
    Returns:
        PIL Image: Enhanced image
    """
    enhancer = ImageEnhance.Color(image)
    return enhancer.enhance(factor)
