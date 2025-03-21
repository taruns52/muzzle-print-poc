import os
import cv2
from django.conf import settings
import numpy as np
from ultralytics import YOLO
from muzzledata.models import Cow

# Load the pre-trained YOLO model for object detection                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           
model = YOLO('trained_model_new.pt')

def generate_encoding(image_file, output_folder):
    """Generates an encoding (ORB descriptors) for the muzzle in the uploaded image."""

    # Read the image from the uploaded file and convert it to a NumPy array
    image_bytes = image_file.read()
    np_array = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_array, cv2.IMREAD_UNCHANGED)

    if img is None:
        print("Failed to decode the image")
        return None

    # Run the YOLO model on the image to detect objects
    results = model(img)

    # Check if any bounding boxes were detected
    if not results[0].boxes or len(results[0].boxes) == 0:
        print("No muzzle detected")
        return None

    # Extract the bounding box coordinates for the first detected muzzle
    x1, y1, x2, y2 = map(int, results[0].boxes.xyxy[0].cpu().numpy())

    # Crop the region containing the muzzle from the image
    muzzle_image = img[y1:y2, x1:x2]

    # Convert the cropped image to grayscale, as ORB works in grayscale
    gray_muzzle = cv2.cvtColor(muzzle_image, cv2.COLOR_BGR2GRAY)

    # Save cropped muzzle image
    output_folder = os.path.join(settings.MEDIA_ROOT, output_folder)
    os.makedirs(output_folder, exist_ok=True)
    cropped_image_path = os.path.join(output_folder, "cropped_muzzle.png")
    cv2.imwrite(cropped_image_path, gray_muzzle)

    print(f"Cropped image saved at: {cropped_image_path}")

    # Initialize the ORB detector and compute keypoints and descriptors
    orb = cv2.ORB_create()
    keypoints, descriptors = orb.detectAndCompute(gray_muzzle, None)

    if descriptors is None:
        print("No key features found in muzzle print")
        return None

    # Return the ORB descriptors (feature encoding of the muzzle)
    return descriptors


def verify_encoding(uploaded_encoding):
    """Verifies if the uploaded muzzle encoding matches any stored cow encodings."""
    
    # Load all cows from database
    cows = Cow.objects.all()

    # Initialize ORB matcher
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    best_match = None
    max_matches = 0

    # Compare the uploaded encoding with the stored encodings for each cow
    for cow in cows:
        
        # Convert stored encoding from bytes to numpy array
        stored_encoding = np.frombuffer(cow.cow_encoding, dtype=np.uint8).reshape(-1, 32)

        # Perform feature matching between the uploaded encoding and the stored encoding
        matches = bf.match(uploaded_encoding, stored_encoding)

        # Track the cow with the most matching features
        if len(matches) > max_matches:
            max_matches = len(matches)
            best_match = cow

    # If a strong match is found (based on the number of matches), return the matched cow
    if max_matches > 10:
        return best_match

    # No match found; return None
    return None