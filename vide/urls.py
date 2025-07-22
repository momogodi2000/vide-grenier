# vide/urls.py (URL principale)
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
import debug_toolbar


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('backend.urls')),
]

# Add browser reload URLs
urlpatterns += [
    path('__reload__/', include('django_browser_reload.urls')),
]

# Servir les fichiers media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar seulement si disponible
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

# URLs pour PWA
urlpatterns += [
    path('manifest.json', TemplateView.as_view(
        template_name='manifest.json', 
        content_type='application/json'
    ), name='manifest'),
    path('sw.js', TemplateView.as_view(
        template_name='sw.js', 
        content_type='application/javascript'
    ), name='sw'),
    path('offline/', TemplateView.as_view(
        template_name='offline.html'
    ), name='offline'),
]

# Personnalisation admin
admin.site.site_header = "Vidé-Grenier Kamer Administration"
admin.site.site_title = "VGK Admin"
admin.site.index_title = "Panneau d'administration"