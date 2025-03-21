from django.urls import path
from .views import HomePageView, SaveCowDataView, MuzzleVerificationView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('save_cow_data/', SaveCowDataView.as_view(), name='save_cow_data'),
    path('muzzle_verification/', MuzzleVerificationView.as_view(), name='muzzle_verification'),
]
