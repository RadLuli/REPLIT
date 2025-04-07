import numpy as np
from PIL import Image, ImageEnhance, ImageStat, ImageFilter, ImageOps
from io import BytesIO

# Define a function to analyze image without OpenCV
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
    gray_np = np.array(gray)
    
    # Calculate basic stats
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
    color_balance = "balanced"
    saturation = 0
    
    if image.mode == 'RGB':
        # Split into channels
        r, g, b = image.split()
        r_np, g_np, b_np = np.array(r), np.array(g), np.array(b)
        
        # Get average channel values
        avg_r, avg_g, avg_b = np.mean(r_np), np.mean(g_np), np.mean(b_np)
        
        # Simple color balance check
        max_channel = max(avg_r, avg_g, avg_b)
        
        if max_channel == avg_r and avg_r > 1.2 * avg_g and avg_r > 1.2 * avg_b:
            color_balance = "red dominant"
        elif max_channel == avg_g and avg_g > 1.2 * avg_r and avg_g > 1.2 * avg_b:
            color_balance = "green dominant"
        elif max_channel == avg_b and avg_b > 1.2 * avg_r and avg_b > 1.2 * avg_g:
            color_balance = "blue dominant"
        
        # Approximate saturation calculation
        hsv_image = image.convert('HSV')
        h, s, v = hsv_image.split()
        saturation = ImageStat.Stat(s).mean[0]
    else:
        avg_r, avg_g, avg_b = 0, 0, 0
    
    # We'll skip face detection since it requires OpenCV
    # In a production system, you might want to use a different face detection library
    
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
