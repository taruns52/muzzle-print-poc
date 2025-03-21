from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import View
from django.contrib import messages
from .models import Cow
from .utils import generate_encoding, verify_encoding
from django.http import HttpResponse

class HomePageView(View):
    def get(self, request):
        return render(request, 'home.html')

class SaveCowDataView(View):
    def post(self, request):
        cow_name = request.POST.get('cow_name')
        cow_image = request.FILES.get('cow_image')

        if not cow_image:
            return HttpResponse("<script>alert('No image uploaded.'); window.location.href='/';</script>")

        muzzle_encoding = generate_encoding(cow_image, 'save_data')

        if muzzle_encoding is None or muzzle_encoding.size == 0:
            return HttpResponse("<script>alert('No muzzle detected in the uploaded image'); window.location.href='/';</script>")

        Cow.objects.create(
            cow_name=cow_name,
            cow_image=cow_image,
            cow_encoding=muzzle_encoding
        )

        return HttpResponse("<script>alert('Cow data successfully saved!'); window.location.href='/';</script>")


class MuzzleVerificationView(View):
    def post(self, request):
        uploaded_image = request.FILES.get('cow_image')

        if not uploaded_image:
            return HttpResponse("<script>alert('No image uploaded.'); window.location.href='/';</script>")

        uploaded_encoding = generate_encoding(uploaded_image, 'verified_data')

        if uploaded_encoding is None or uploaded_encoding.size == 0:
            return HttpResponse("<script>alert('No muzzle detected in the uploaded image.'); window.location.href='/';</script>")

        matching_cow = verify_encoding(uploaded_encoding)

        if matching_cow:
            return HttpResponse(f"<script>alert('Match Found! Cow Name: {matching_cow.cow_name}'); window.location.href='/';</script>")
        else:
            return HttpResponse("<script>alert('No matching muzzle print found in the database.'); window.location.href='/';</script>")
