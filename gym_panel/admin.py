from django.contrib import admin
from django.utils import timezone

from .models import GymStaffAccess, GymChangeRequest, GymTicketMessage
from gym.models import Sport


@admin.register(GymStaffAccess)
class GymStaffAccessAdmin(admin.ModelAdmin):
    list_display = ("user", "gym", "role", "created_at")
    list_filter = ("role",)


class GymTicketMessageInline(admin.TabularInline):
    model = GymTicketMessage
    extra = 1
    fields = ("sender_role", "message", "created_at")
    readonly_fields = ("created_at",)

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.form.base_fields["sender_role"].initial = "admin"
        return formset


@admin.register(GymChangeRequest)
class GymChangeRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "gym", "request_type", "status", "requested_by", "created_at")
    list_filter = ("request_type", "status")
    readonly_fields = ("gym", "requested_by", "request_type", "payload", "created_at")
    inlines = [GymTicketMessageInline]
    actions = ["approve_requests", "reject_requests"]

    def _apply(self, cr):
        if cr.request_type == "field_edit":
            for field, value in cr.payload.items():
                setattr(cr.gym, field, value)
            cr.gym.save()
        elif cr.request_type == "new_sport":
            sport = Sport.objects.create(
                name=cr.payload["name"],
                category_id=cr.payload["category_id"],
            )
            cr.gym.sports.add(sport)

    def _log(self, cr, sender_role, message, user=None):
        GymTicketMessage.objects.create(
            ticket=cr, sender_role=sender_role, sender=user, message=message
        )

    def approve_requests(self, request, queryset):
        count = 0
        for cr in queryset.filter(status="pending"):
            self._apply(cr)
            cr.status = "approved"
            cr.reviewed_at = timezone.now()
            cr.save()
            self._log(cr, "system", "تیکت تایید و اعمال شد.")
            count += 1
        self.message_user(request, f"{count} تیکت تایید و اعمال شد.")
    approve_requests.short_description = "تایید و اعمال درخواست‌های انتخاب‌شده"

    def reject_requests(self, request, queryset):
        count = 0
        for cr in queryset.filter(status="pending"):
            cr.status = "rejected"
            cr.reviewed_at = timezone.now()
            cr.save()
            reason = cr.admin_note or "بدون ذکر دلیل"
            self._log(cr, "system", f"تیکت رد شد. دلیل: {reason}")
            count += 1
        self.message_user(request, f"{count} تیکت رد شد.")
    reject_requests.short_description = "رد درخواست‌های انتخاب‌شده (دلیل از admin_note خوانده می‌شود)"

    def save_model(self, request, obj, form, change):
        if change:
            old = GymChangeRequest.objects.get(pk=obj.pk)
            if old.status != "approved" and obj.status == "approved":
                self._apply(obj)
                obj.reviewed_at = timezone.now()
                self._log(obj, "system", "تیکت تایید و اعمال شد.")
            elif old.status != "rejected" and obj.status == "rejected":
                obj.reviewed_at = timezone.now()
                reason = obj.admin_note or "بدون ذکر دلیل"
                self._log(obj, "system", f"تیکت رد شد. دلیل: {reason}")
        super().save_model(request, obj, form, change)