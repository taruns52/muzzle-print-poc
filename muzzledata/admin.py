from django.contrib import admin
from .models import Cow

class CowAdmin(admin.ModelAdmin):
    list_display = ('cow_name', 'cow_image') 
    search_fields = ('cow_name',)  
    list_filter = ('cow_name',) 

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

admin.site.register(Cow, CowAdmin)
