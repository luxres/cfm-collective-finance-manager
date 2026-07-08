import uuid
from datetime import timedelta
import os
import random

from django.db import models
from django.utils import timezone

class UploadSession(models.Model):

    def receipt_upload_path(instance, filename):
        base, ext = os.path.splitext(filename)
        ext = ext.lower()
        ext = ext.lstrip(".") # remove leading dot

        suffix = f"{random.randint(0, 999999):06d}" # 6 random digits

        new_name = f"{suffix}-{base}.{ext}"
        return f"receipts/{new_name}"
    
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    file = models.FileField(upload_to=receipt_upload_path, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(auto_now_add=True)
    uploaded_at = models.DateTimeField(null=True, blank=True)

    def start_timer(self, minutes=5):
        """
        Opens upload window for editing.
        """
        self.activated_at = timezone.now()
        self.save(update_fields=["activated_at"])

    def upload_blocked(self):
        """
        Upload is blocked if:
        - never activated
        - or activation expired (e.g. 5 min window)
        """
        if not self.activated_at:
            return True

        return timezone.now() > self.activated_at + timedelta(minutes=5)

    def can_upload(self):
        return not self.upload_blocked()
    
