from django.contrib.auth.models import AbstractUser
from django.db import models
import random
from django.conf import settings
from django.utils.timezone import now

import uuid



class CustomUser(AbstractUser):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    email = models.EmailField(unique=True)
    is_ngo = models.BooleanField(default=False)  # True if the user is an NGO
    contact_number = models.CharField(max_length=15, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def generate_otp(self):
        """Generate and store a 6-digit OTP"""
        self.otp_code = str(random.randint(100000, 999999))
        self.save()
        return self.otp_code


class FundRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reason = models.TextField()
    amount_requested = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount_requested} - {self.status}"



class FundPost(models.Model):
    id = models.BigAutoField(primary_key=True)  # Keep the existing ID
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)  # New UUID field
    
    ngo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'is_ngo': True},
        related_name="ngo_fund_posts",  # Fix conflict
        null=True,  # ✅ Temporarily allow null values
        blank=True  # ✅ Allow empty values
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_fund_posts",  # Fix conflict
        null=True,  # ✅ Temporarily allow null values
        blank=True  # ✅ Allow empty values
    )

    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField()
    target_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    collected_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    image = models.ImageField(upload_to="img/fund_images/", blank=True, null=True)  # Fix path
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.ngo.username}"

 

class Transaction(models.Model):
    donor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="transactions")
    fund_post = models.ForeignKey(FundPost, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=[('UPI', 'UPI'), ('Card', 'Card'), ('Net Banking', 'Net Banking')])
    transaction_id = models.CharField(max_length=100, unique=True)  # Unique transaction reference
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Success', 'Success'), ('Failed', 'Failed')], default='Pending')
    created_at = models.DateTimeField(default=now)



class Donation(models.Model):
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # The user who donates
    fund_post = models.ForeignKey("FundPost", on_delete=models.CASCADE)  # The fundraiser receiving the donation
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Amount donated
    payment_status = models.CharField(max_length=20, choices=[('PENDING', 'Pending'), ('SUCCESS', 'Success'), ('FAILED', 'Failed')], default='PENDING')  # Payment status
    created_at = models.DateTimeField(auto_now_add=True)  # When the donation was made


class NGOVerification(models.Model):
    ngo = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="verification")
    document = models.FileField(upload_to='ngo_documents/')  # Upload NGO certificates
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Verified', 'Verified'), ('Rejected', 'Rejected')], default='Pending')
    verified_at = models.DateTimeField(null=True, blank=True)

class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=now)
