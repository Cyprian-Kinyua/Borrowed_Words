from django.core.management.base import BaseCommand
from django.utils import timezone
from transactions.models import BorrowTransaction
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Check for overdue books and send notifications'

    def handle(self, *args, **options):
        overdue_transactions = BorrowTransaction.objects.filter(
            status='ACCEPTED',
            due_date__lt=timezone.now().date()
        )

        for transaction in overdue_transactions:
            # Send email to borrower
            subject = f'Overdue Book: {transaction.book.title}'
            message = f'''
            Hello {transaction.borrower.username},
            
            The book "{transaction.book.title}" is overdue. 
            It was due on {transaction.due_date}.
            
            Please return the book as soon as possible.
            
            Thank you,
            BorrowedWords Team
            '''

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [transaction.borrower.email],
                fail_silently=True,
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Sent overdue notification for {transaction.book.title}')
            )
