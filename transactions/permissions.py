from rest_framework import permissions


class IsTransactionParticipant(permissions.BasePermission):
    """
    Only allow participants (borrower or lender) to view the transaction.
    """

    def has_object_permission(self, request, view, obj):
        return obj.borrower == request.user or obj.lender == request.user


class IsBorrower(permissions.BasePermission):
    """
    Only allow the borrower to perform action.
    """

    def has_object_permission(self, request, view, obj):
        return obj.borrower == request.user


class IsLender(permissions.BasePermission):
    """
    Only allow the lender to perform action.
    """

    def has_object_permission(self, request, view, obj):
        return obj.lender == request.user
