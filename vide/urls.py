from django.conf.urls import handler500
from django.shortcuts import render
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

# Custom 500 error handler
def custom_error_500(request):
    return render(request, 'offline.html', status=500)

handler500 = 'vide.urls.custom_error_500'

# Main URL patterns
urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),
    
    # Authentication URLs
    path('accounts/', include('allauth.urls')),
    
    # Main application URLs
    path('', include('backend.urls')),
    
    # User-type-specific URLs
    path('client/', include('backend.urls_client', namespace='client')),
    path('staff/', include('backend.urls_staff', namespace='staff')),
    path('admin-panel/', include('backend.urls_admin', namespace='admin_panel')),
]

# Browser reload for development
urlpatterns += [
    path('__reload__/', include('django_browser_reload.urls')),
]

# Static and media files for development
if settings.DEBUG:
    # Static and media files for development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Progressive Web App URLs
urlpatterns += [
    # Manifest file
    path('manifest.json', 
         TemplateView.as_view(template_name='manifest.json', content_type='application/json'), 
         name='manifest'),
    
    # Service worker
    path('sw.js', 
         TemplateView.as_view(template_name='sw.js', content_type='application/javascript'), 
         name='sw'),
    
    # Offline page
    path('offline/', 
         TemplateView.as_view(template_name='offline.html'), 
         name='offline'),
]

# Customize admin site
admin.site.site_header = "Vidé-Grenier Kamer Administration"
admin.site.site_title = "VGK Admin"
admin.site.index_title = "Panneau d'administration"