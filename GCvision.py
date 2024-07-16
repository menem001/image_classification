from google.cloud import vision
import logging
import os

# Set Google Cloud credentials environment variable
service_account_path = r"C:\Users\Oracle DB\Desktop\MS_ocr\zeta-ascent-425607-d8-93027003e046.json"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_path

# Ensure the uploads directory exists
os.makedirs('uploads', exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Function to calculate the difference between two colors
def color_difference(color1, color2):
    return abs(color1.red - color2.red) + abs(color1.green - color2.green) + abs(color1.blue - color2.blue)

# Function to determine if colors are significantly different
def are_colors_significantly_different(colors, threshold=100):
    for i in range(len(colors)):
        for j in range(i + 1, len(colors)):
            if color_difference(colors[i].color, colors[j].color) > threshold:
                return True
    return False

# Function to determine the color category of the vehicle
def get_color_category(color):
    logging.debug(f"Analyzing color with RGB ({color.red}, {color.green}, {color.blue})")
    if color.red < 60 and color.green < 60 and color.blue < 60:
        return 'black'
    elif color.red > 200 and color.green > 200 and color.blue > 200:
        return 'white'
    elif abs(color.red - color.green) < 20 and abs(color.red - color.blue) < 20:
        return 'grey'
    elif 160 < color.red < 210 and 160 < color.green < 210 and 160 < color.blue < 210:
        return 'silver'
    elif 210 <= color.red < 240 and 160 <= color.green < 210 and 60 <= color.blue < 100:
        return 'gold'
    elif color.red > 150 and color.green < 100 and color.blue < 100:
        return 'red'
    elif color.red < 100 and color.green > 150 and color.blue < 100:
        return 'green'
    elif color.red < 100 and color.green < 100 and color.blue > 150:
        return 'blue'
    elif color.red > 200 and color.green > 200 and color.blue < 100:
        return 'yellow'
    elif color.red > 150 and color.green < 100 and color.blue > 150:
        return 'purple'
    elif color.red > 150 and color.green > 150 and color.blue < 100:
        return 'orange'
    elif color.red < 100 and color.green > 150 and color.blue > 150:
        return 'cyan'
    elif 128 <= color.red <= 150 and 0 <= color.green < 80 and 0 <= color.blue < 80:
        return 'maroon'
    elif 0 <= color.red < 40 and 0 <= color.green < 80 and 80 <= color.blue <= 150:
        return 'navy'
    elif 100 < color.red < 150 and 80 < color.green < 130 and 30 < color.blue < 80:
        return 'brown'
    else:
        return 'other'

# Function to detect speedometer, vehicle (exterior), and color in an image
def detect_features(image_path):
    try:
        logging.debug(f"Detecting features in image: {image_path}")

        # Initialize Vision API client
        client = vision.ImageAnnotatorClient()

        # Read the image file
        with open(image_path, 'rb') as image_file:
            content = image_file.read()

        # Perform label detection on the image
        image = vision.Image(content=content)
        response = client.label_detection(image=image)
        labels = response.label_annotations

        # Initialize results
        detection_results = {
            "speedometer": False,
            "vehicle_exterior": False,
            "color": None
        }

        # Check for labels and determine if speedometer or vehicle (exterior) are detected
        for label in labels:
            if label.description.lower() == 'speedometer':
                logging.debug("Speedometer detected")
                detection_results["speedometer"] = True
            elif label.description.lower() in ['vehicle', 'car', 'automobile', 'truck', 'bike', 'motorcycle']:
                logging.debug("Vehicle (exterior) detected")
                detection_results["vehicle_exterior"] = True

        # Perform image properties detection to determine color
        response = client.image_properties(image=image)
        props = response.image_properties_annotation
        if props.dominant_colors:
            dominant_colors = props.dominant_colors.colors[:3]  # Analyze the top 3 dominant colors
            if are_colors_significantly_different(dominant_colors):
                # If multiple colors are detected, list them
                detected_colors = [get_color_category(color.color) for color in dominant_colors]
                detection_results["color"] = "multicolored: " + ", ".join(detected_colors)
                logging.debug(f"Multiple colors detected: {detection_results['color']}")
            else:
                # If only one dominant color, classify it
                dominant_color = dominant_colors[0].color
                color_category = get_color_category(dominant_color)
                detection_results["color"] = color_category
                logging.debug(f"Dominant color detected: {detection_results['color']}")

        return detection_results
    except Exception as e:
        logging.error(f"Error in detect_features: {e}")
        return None
