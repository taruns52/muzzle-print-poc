from django.urls import path
from .views import HomePageView, SaveCowDataView, MuzzleVerificationView, VerificationResultView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('upload_cow_data/', SaveCowDataView.as_view(), name='upload_cow_data'),
    path('verify_cow_data/', MuzzleVerificationView.as_view(), name='verify_cow_data'),
    path('verification-result/<str:status>/<str:cow_name>/', VerificationResultView.as_view(), name='verification_result'),
]
