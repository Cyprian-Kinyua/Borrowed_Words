from django.urls import path
from . import views

urlpatterns = [
    path('transactions/', views.TransactionListView.as_view(),
         name='transaction-list'),
    path('transactions/<int:pk>/', views.TransactionDetailView.as_view(),
         name='transaction-detail'),
    path('transactions/<int:transaction_id>/accept/',
         views.accept_request, name='accept-request'),
    path('transactions/<int:transaction_id>/reject/',
         views.reject_request, name='reject-request'),
]
