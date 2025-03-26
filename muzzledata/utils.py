import os
import cv2
from django.conf import settings
import numpy as np
from ultralytics import YOLO
from muzzledata.models import Cow

# Load the pre-trained YOLO model                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
model = YOLO('trained_model_new.pt')

def generate_encoding(image_file, output_folder):
    try:
        if image_file is None:
            print("Failed to decode the image")
            return None

        # Run YOLO model to detect objects 
        results = model(image_file) 

        # Ensure bounding boxes exist
        if not results[0].boxes or len(results[0].boxes) == 0:
            print("No muzzle detected")
            return None

        # Extract the bounding box coordinates
        x1, y1, x2, y2 = map(int, results[0].boxes.xyxy[0].cpu().numpy())

        # Crop the muzzle region
        muzzle_image = image_file[y1:y2, x1:x2]

        # Convert the cropped muzzle region to grayscale for ORB processing
        gray_muzzle = cv2.cvtColor(muzzle_image, cv2.COLOR_BGR2GRAY)

        # Save cropped muzzle image
        output_folder = os.path.join(settings.MEDIA_ROOT, output_folder)
        os.makedirs(output_folder, exist_ok=True)
        cropped_image_path = os.path.join(output_folder, "cropped_muzzle.png")
        cv2.imwrite(cropped_image_path, gray_muzzle)

        print(f"Cropped image saved at: {cropped_image_path}")

        # Generate ORB descriptors for feature matching
        orb = cv2.ORB_create()
        keypoints, descriptors = orb.detectAndCompute(gray_muzzle, None)

        if descriptors is None:
            print("No key features found in muzzle print")
            return None

        return descriptors  # Return ORB descriptors for further processing

    except Exception as e:
        print(f"An error occurred during encoding generation: {e}")
        return None


def verify_encoding(uploaded_encoding):
    # Load all cows from database
    cows = Cow.objects.all()

    # Initialize ORB matcher
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    best_match = None
    max_matches = 0
    match_threshold = 30

    for cow in cows:
        # Convert stored encoding from bytes to numpy array
        stored_encoding = np.frombuffer(cow.cow_encoding, dtype=np.uint8).reshape(-1, 32)

        # Use ORB feature matching
        matches = bf.match(uploaded_encoding, stored_encoding)
        
        strong_matches = [m for m in matches if m.distance < 50] 

        if len(strong_matches) > max_matches and len(strong_matches) > match_threshold:
            max_matches = len(strong_matches)
            best_match = cow

    # If we have a strong match, return the cow
    if best_match:  
        return best_match

    return None  # No match found
