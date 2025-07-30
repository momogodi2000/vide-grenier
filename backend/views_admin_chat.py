from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
from .models import User, AdminChat, AdminMessage
from .forms import AdminMessageForm


class AdminChatListView(LoginRequiredMixin, ListView):
    """List of admin chats for all user types"""
    model = AdminChat
    template_name = 'backend/admin_chat/chat_list.html'
    context_object_name = 'chats'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            # Admin/Staff can see all chats
            return AdminChat.objects.all().order_by('-updated_at')
        else:
            # Regular users can only see their own chats
            return AdminChat.objects.filter(user=user).order_by('-updated_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_type'] = self.get_user_type()
        return context

    def get_user_type(self):
        user = self.request.user
        if user.is_superuser:
            return 'admin'
        elif user.is_staff:
            return 'staff'
        else:
            return 'client'


class AdminChatDetailView(LoginRequiredMixin, DetailView):
    """Detail view for admin chat"""
    model = AdminChat
    template_name = 'backend/admin_chat/chat_detail.html'
    context_object_name = 'chat'

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return AdminChat.objects.all()
        else:
            return AdminChat.objects.filter(user=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['messages'] = self.object.messages.all().order_by('created_at')
        context['form'] = AdminMessageForm()
        context['user_type'] = self.get_user_type()
        return context

    def get_user_type(self):
        user = self.request.user
        if user.is_superuser:
            return 'admin'
        elif user.is_staff:
            return 'staff'
        else:
            return 'client'


class AdminChatCreateView(LoginRequiredMixin, CreateView):
    """Create a new admin chat"""
    model = AdminChat
    template_name = 'backend/admin_chat/chat_create.html'
    fields = ['subject', 'category', 'priority']
    success_url = '/admin-chat/'

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.status = 'OPEN'
        response = super().form_valid(form)
        
        # Create initial message
        AdminMessage.objects.create(
            chat=form.instance,
            sender=self.request.user,
            content=self.request.POST.get('initial_message', ''),
            message_type='USER'
        )
        
        messages.success(self.request, 'Chat créé avec succès!')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_type'] = self.get_user_type()
        return context

    def get_user_type(self):
        user = self.request.user
        if user.is_superuser:
            return 'admin'
        elif user.is_staff:
            return 'staff'
        else:
            return 'client'


@login_required
def send_admin_message(request, chat_id):
    """Send a message in admin chat"""
    if request.method == 'POST':
        chat = get_object_or_404(AdminChat, id=chat_id)
        
        # Check permissions
        user = request.user
        if not (user.is_staff or user.is_superuser or chat.user == user):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        content = request.POST.get('content')
        if not content:
            return JsonResponse({'error': 'Message content is required'}, status=400)
        
        # Determine message type
        if user.is_staff or user.is_superuser:
            message_type = 'ADMIN'
        else:
            message_type = 'USER'
        
        # Create message
        message = AdminMessage.objects.create(
            chat=chat,
            sender=user,
            content=content,
            message_type=message_type
        )
        
        # Update chat status
        if message_type == 'USER':
            chat.status = 'WAITING'
        else:
            chat.status = 'RESPONDED'
        chat.updated_at = timezone.now()
        chat.save()
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'sender': message.sender.username,
                'created_at': message.created_at.strftime('%H:%M'),
                'message_type': message.message_type
            }
        })
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def close_admin_chat(request, chat_id):
    """Close an admin chat"""
    if request.method == 'POST':
        chat = get_object_or_404(AdminChat, id=chat_id)
        
        # Check permissions
        user = request.user
        if not (user.is_staff or user.is_superuser or chat.user == user):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        chat.status = 'CLOSED'
        chat.closed_at = timezone.now()
        chat.save()
        
        messages.success(request, 'Chat fermé avec succès!')
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def admin_chat_dashboard(request):
    """Admin chat dashboard for different user types"""
    user = request.user
    
    if user.is_superuser:
        return admin_chat_dashboard_admin(request)
    elif user.is_staff:
        return admin_chat_dashboard_staff(request)
    else:
        return admin_chat_dashboard_client(request)


def admin_chat_dashboard_admin(request):
    """Admin dashboard for superusers"""
    # All chats
    all_chats = AdminChat.objects.all().order_by('-updated_at')
    open_chats = all_chats.filter(status='OPEN')
    waiting_chats = all_chats.filter(status='WAITING')
    closed_chats = all_chats.filter(status='CLOSED')
    
    # Statistics
    stats = {
        'total_chats': all_chats.count(),
        'open_chats': open_chats.count(),
        'waiting_chats': waiting_chats.count(),
        'closed_chats': closed_chats.count(),
        'avg_response_time': calculate_avg_response_time(),
    }
    
    context = {
        'chats': all_chats[:10],
        'open_chats': open_chats[:5],
        'waiting_chats': waiting_chats[:5],
        'stats': stats,
        'user_type': 'admin'
    }
    
    return render(request, 'backend/admin_chat/admin_dashboard.html', context)


def admin_chat_dashboard_staff(request):
    """Staff dashboard for staff members"""
    # Staff can see all chats but with limited actions
    all_chats = AdminChat.objects.all().order_by('-updated_at')
    open_chats = all_chats.filter(status='OPEN')
    waiting_chats = all_chats.filter(status='WAITING')
    
    # Statistics
    stats = {
        'total_chats': all_chats.count(),
        'open_chats': open_chats.count(),
        'waiting_chats': waiting_chats.count(),
        'assigned_chats': all_chats.filter(assigned_to=request.user).count(),
    }
    
    context = {
        'chats': all_chats[:10],
        'open_chats': open_chats[:5],
        'waiting_chats': waiting_chats[:5],
        'stats': stats,
        'user_type': 'staff'
    }
    
    return render(request, 'backend/admin_chat/staff_dashboard.html', context)


def admin_chat_dashboard_client(request):
    """Client dashboard for regular users"""
    # Users can only see their own chats
    user_chats = AdminChat.objects.filter(user=request.user).order_by('-updated_at')
    open_chats = user_chats.filter(status='OPEN')
    waiting_chats = user_chats.filter(status='WAITING')
    closed_chats = user_chats.filter(status='CLOSED')
    
    # Statistics
    stats = {
        'total_chats': user_chats.count(),
        'open_chats': open_chats.count(),
        'waiting_chats': waiting_chats.count(),
        'closed_chats': closed_chats.count(),
    }
    
    context = {
        'chats': user_chats[:10],
        'open_chats': open_chats[:5],
        'waiting_chats': waiting_chats[:5],
        'stats': stats,
        'user_type': 'client'
    }
    
    return render(request, 'backend/admin_chat/client_dashboard.html', context)


def calculate_avg_response_time():
    """Calculate average response time for admin chats"""
    # This is a simplified calculation
    # In a real implementation, you'd track response times more accurately
    return "2h 30m"  # Placeholder 