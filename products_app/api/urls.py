from django.urls import path
from . import views

urlpatterns = [
    path('list/',views.product_list, name='product-list'),
    path('list-filter/',views.ProductListFilter.as_view(), name='product-list-filter'),
    path('<int:id>',views.product_details, name='product-details'),
    path('category/',views.CategoryAV.as_view(), name='category'),
    path('category-filter/',views.CategoryFilter.as_view(), name='category-filter'),
    path('category/<int:id>/',views.CategoryDetailAV.as_view(), name='category-details'),
    # path('review/',views.ReviewList.as_view(),name='review-list'),
    # path('review/<int:pk>/', views.ReviewDetail.as_view(), name='review-details'),
    path('<int:pk>/review-create/',views.ReviewCreate.as_view(), name='review-create'),
    path('<int:pk>/review/',views.ReviewList.as_view(), name='stream-detail'),
    path('review/<int:pk>/', views.ReviewDetail.as_view(), name='review-details'),
    path('season-change/',views.SeasonChangeAV.as_view(), name='season-change'),
    path('shipping/', views.OrderListCreateAV.as_view(), name='order-list-create'),
    path('shipping/<int:pk>/', views.OrderDetailAV.as_view(), name='order-detail'),
    path('contact/', views.ContactCreateAV.as_view(), name='contact-create'),
]
