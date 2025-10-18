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
    path('transactions/<int:transaction_id>/mark-returned/',
         views.mark_returned, name='mark-returned'),
    path('transactions/<int:transaction_id>/confirm-return/',
         views.confirm_return, name='confirm-return'),
    path('transactions/<int:transaction_id>/cancel/',
         views.cancel_request, name='cancel-request'),
    path('transactions/stats/', views.transaction_stats, name='transaction-stats'),
    path('dashboard/', views.user_dashboard, name='user-dashboard'),
]
