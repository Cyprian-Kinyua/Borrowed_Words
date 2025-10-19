from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    # API endpoints
    path('', views.TransactionListView.as_view(), name='api-transaction-list'),
    path('<int:pk>/', views.TransactionDetailView.as_view(),
         name='api-transaction-detail'),
    path('<int:transaction_id>/accept/',
         views.api_accept_request, name='api-accept-request'),
    path('<int:transaction_id>/reject/',
         views.api_reject_request, name='api-reject-request'),
    path('<int:transaction_id>/mark-returned/',
         views.api_mark_returned, name='api-mark-returned'),
    path('<int:transaction_id>/confirm-return/',
         views.api_confirm_return, name='api-confirm-return'),
    path('<int:transaction_id>/cancel/',
         views.api_cancel_request, name='api-cancel-request'),
    path('stats/', views.transaction_stats, name='api-transaction-stats'),
    path('dashboard/', views.user_dashboard, name='api-user-dashboard'),
]
