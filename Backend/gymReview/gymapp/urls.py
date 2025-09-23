from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'gyms', views.GymViewSet)
router.register(r'reviews', views.ReviewViewSet)
router.register(r'comments', views.CommentViewSet)
router.register(r'photos', views.GymPhotoViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 