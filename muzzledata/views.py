import base64
from django.core.files.base import ContentFile
import cv2
import numpy as np
from django.shortcuts import render, redirect
from django.views import View
from .models import Cow
from .utils import generate_encoding, verify_encoding
from django.http import HttpResponse

class HomePageView(View):
    def get(self, request):
        return render(request, 'home.html')

class SaveCowDataView(View):
    def get(self, request):
        return render(request, 'upload_cow_data.html')
    
    def post(self, request):
        log_label = "SaveCowData:"
        cow_name = request.POST.get('cow_name')
        cow_image_base64 = request.POST.get('cow_image')  # Base64 string

        if not cow_image_base64:
            print(f"{log_label} No image uploaded.")
            return HttpResponse("<script>alert('No image uploaded.'); window.location.href='/';</script>")

        # Convert Base64 string to OpenCV image
        header, encoded = cow_image_base64.split(",", 1)  # Remove "data:image/jpeg;base64,"
        image_data = base64.b64decode(encoded)  #decoded into binary image data
        nparr = np.frombuffer(image_data, np.uint8)
        cow_image_cv2 = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if cow_image_cv2 is None:
            print(f"{log_label} Error processing image.")
            return HttpResponse("<script>alert('Error processing image.'); window.location.href='/';</script>")

        # Process Image with Your Model
        descriptors, cropped_image = generate_encoding(cow_image_cv2, 'save_data')

        if descriptors is None or len(descriptors) == 0 or cropped_image is None:
            print(f"{log_label} No muzzle detected in the uploaded image")
            return HttpResponse("<script>alert('No muzzle detected in the uploaded image'); window.location.href='/';</script>")

        # Save the image to a file (using ContentFile)
        image_file = ContentFile(cropped_image)
        image_file.name = f"{cow_name}.jpg"

        # Save to Database 
        Cow.objects.create(
            cow_name=cow_name,
            cow_image=image_file, 
            cow_encoding=descriptors
        )

        print(f"{log_label} Cow data successfully saved!")
        return HttpResponse("<script>alert('Cow data successfully saved!'); window.location.href='/';</script>")


class MuzzleVerificationView(View):
    def get(self, request):
        return render(request, 'verify_cow_data.html')

    def post(self, request):
        from django.utils.http import urlencode
        log_label = "VerifyCowData:"
        cow_image_data = request.POST.get('cow_image')

        if not cow_image_data:
            error_message = "No image uploaded."
            print(f"{log_label} Validation Failed: {error_message}")
            query_params = urlencode({'message': error_message})
            return redirect(f"/verification-result/error/Unknown/?{query_params}")

        try:
            image_data = cow_image_data.split(',')[1]  # Strip metadata
            image_bytes = base64.b64decode(image_data)  # Decode base64 to bytes
            nparr = np.frombuffer(image_bytes, np.uint8)
            cow_image_cv2 = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

            if cow_image_cv2 is None:
                raise ValueError("Error in decoding image.")

            descriptors, crooped_image_data = generate_encoding(cow_image_cv2, 'verified_data')

            if descriptors is None or len(descriptors) == 0 or crooped_image_data is None:
                error_message = "No muzzle detected in the uploaded image."
                print(f"{log_label} Validation Failed: {error_message}")
                query_params = urlencode({'message': error_message})
                return redirect(f"/verification-result/error/Unknown/?{query_params}")
            
            matching_cow = verify_encoding(descriptors)
            
            if matching_cow:
                cow_name = matching_cow.cow_name
                cow_image_url = matching_cow.cow_image.url  # Get the image URL

                print(f"{log_label} Match Found Successfully! with cow_name : {cow_name}")
                # Redirect with query parameters
                query_params = urlencode({'cow_image_url': cow_image_url})
                return redirect(f"/verification-result/success/{cow_name}/?{query_params}")
            else:
                error_message = "No matching muzzle print found."
                print(f"{log_label} Validation Failed: {error_message}")
                query_params = urlencode({'message': error_message})
                return redirect(f"/verification-result/error/Unknown/?{query_params}")

        except Exception as e:
            print(f"{log_label} Error: {str(e)}")
            error_message = "An error occurred during processing."
            query_params = urlencode({'message': error_message})
            return redirect(f"/verification-result/error/Unknown/?{query_params}")
            

class VerificationResultView(View):
    def get(self, request, status, cow_name):
        message = request.GET.get('message', '')
        cow_image_url = request.GET.get('cow_image_url', '')

        return render(request, 'verification_result.html', {
            'status': status,
            'message': message,
            'cow_name': cow_name,
            'cow_image_url': cow_image_url
        })
