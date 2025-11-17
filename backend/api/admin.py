from django.contrib import admin
from .models import DocumentType, LostItem, FoundItem, Match, Notification

@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']
    ordering = ['name']

@admin.register(LostItem)
class LostItemAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'document_type', 'lost_date', 'status', 'user', 'created_at']
    list_filter = ['status', 'document_type', 'lost_date', 'created_at']
    search_fields = ['first_name', 'last_name', 'document_number']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']

@admin.register(FoundItem)
class FoundItemAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'document_type', 'found_date', 'status', 'ocr_confidence', 'user', 'created_at']
    list_filter = ['status', 'document_type', 'found_date', 'created_at']
    search_fields = ['first_name', 'last_name', 'document_number']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at', 'ocr_confidence']

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['lost_item', 'found_item', 'confidence_score', 'status', 'created_at']
    list_filter = ['status', 'confidence_score', 'created_at']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at', 'confidence_score', 'match_criteria']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at'] 