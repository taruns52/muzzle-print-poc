import os
import cv2
from django.conf import settings
import numpy as np
from ultralytics import YOLO
from muzzledata.models import Cow

# Load the pre-trained YOLO model                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
model = YOLO('trained_model_new.pt')

def generate_encoding(image_file, output_folder, confidence_threshold=0.7):
    try:
        if image_file is None:
            print("Failed to decode the image")
            return None

        # Run YOLO model to detect objects 
        results = model(image_file) 

        # Ensure bounding boxes exist
        if not results or not results[0].boxes or len(results[0].boxes) == 0:
            print("No muzzle detected")
            return None, None

        boxes = results[0].boxes.xyxy.cpu().numpy()
        confidences = results[0].boxes.conf.cpu().numpy()

        for i, conf in enumerate(confidences):
            if conf >= confidence_threshold:
                x1, y1, x2, y2 = map(int, boxes[i])
                muzzle_image = image_file[y1:y2, x1:x2]

                if muzzle_image.size == 0:
                    continue

                # Save cropped image to bytes
                success, buffer = cv2.imencode(".jpg", muzzle_image)
                cropped_image_bytes = buffer.tobytes() if success else None

                # Generate SIFT descriptors
                gray_muzzle = cv2.cvtColor(muzzle_image, cv2.COLOR_BGR2GRAY)
                sift = cv2.SIFT_create()
                keypoints, descriptors = sift.detectAndCompute(gray_muzzle, None)

                if descriptors is None:
                    return None, None

                return descriptors, cropped_image_bytes

        return None, None

    except Exception as e:
        print(f"An error occurred during encoding generation: {e}")
        return None


def compare_encodings(descriptors1, descriptors2):
    try:
        bf = cv2.BFMatcher()
        matches = bf.knnMatch(descriptors1, descriptors2, k=2)

        good_matches = []

        for m, n in matches:
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)

        return len(good_matches)

    except Exception as e:
        print(f"Error in compare_encodings: {e}")
        return 0
    

def verify_encoding(uploaded_encoding):
    # Load all cows from database
    cows = Cow.objects.filter(cow_encoding__isnull= False)

    best_match = None
    best_score = 0
    threshold = 30

    for entry in cows:
        stored_descriptors = np.frombuffer(entry.cow_encoding, dtype=np.float32)

        if stored_descriptors.size % 128 != 0:
            continue

        stored_descriptors = stored_descriptors.reshape(-1, 128)

        match_score = compare_encodings(uploaded_encoding, stored_descriptors)
        
        if match_score > best_score:
            best_score = match_score
            best_match = entry

        print(f"\n best_score {best_score} best_match {best_match} match_score {match_score}")

    # If we have a strong match, return the cow
    if best_match and best_score >= threshold:
        return best_match

    return None  # No match found
