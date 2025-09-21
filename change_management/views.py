from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .models import ChangeRequest, Incident, Lead
from .serializers import ChangeRequestSerializer, IncidentSerializer, LeadSerializer
from .models import Role, RoleAssignment, Comment, Activity
from .serializers import RoleSerializer, RoleAssignmentSerializer, CommentSerializer, ActivitySerializer
from .serializers import CommentSerializer, ActivitySerializer
from .models import Comment, Activity
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.contenttypes.models import ContentType
from django.views.generic import ListView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from .models import ChangeRequest



class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated


class HasOperatorRole(permissions.BasePermission):
    """Allow action only if the user has the 'operator' role."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Allow admins/staff as well
        if getattr(request.user, 'is_staff', False) or getattr(request.user, 'is_superuser', False):
            return True
        return RoleAssignment.objects.filter(user=request.user, role__name='operator').exists()


class ChangeRequestViewSet(viewsets.ModelViewSet):
    queryset = ChangeRequest.objects.all().order_by('-created_at')
    serializer_class = ChangeRequestSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['post'], permission_classes=[HasOperatorRole])
    def assign(self, request, pk=None):
        """Assign a user to the ChangeRequest. Only operators or admins may call this action."""
        cr = get_object_or_404(ChangeRequest, pk=pk)
        assignee_id = request.data.get('assignee')
        if not assignee_id:
            return Response({'detail': 'assignee is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            assignee = User.objects.get(pk=assignee_id)
        except Exception:
            return Response({'detail': 'assignee not found'}, status=status.HTTP_400_BAD_REQUEST)

        cr.assignee = assignee
        cr.save()
        Activity.objects.create(actor=request.user, verb='assigned', target=str(cr))
        serializer = self.get_serializer(cr)
        return Response(serializer.data)


class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.all().order_by('-created_at')
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.all().order_by('-created_at')
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAdminUser]


class RoleAssignmentViewSet(viewsets.ModelViewSet):
    queryset = RoleAssignment.objects.all()
    serializer_class = RoleAssignmentSerializer
    permission_classes = [permissions.IsAdminUser]


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().order_by('created_at')
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class ActivityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Activity.objects.all().order_by('-created_at')
    serializer_class = ActivitySerializer
    permission_classes = [permissions.IsAuthenticated]


def cr_detail_view(request, pk):
    cr = get_object_or_404(ChangeRequest, pk=pk)
    # load comments
    ct = ContentType.objects.get_for_model(ChangeRequest)
    comments = Comment.objects.filter(content_type=ct, object_id=cr.id).order_by('created_at')

    if request.method == 'POST' and request.user.is_authenticated:
        text = request.POST.get('text', '').strip()
        if text:
            Comment.objects.create(content_type=ct, object_id=cr.id, author=request.user, text=text)
            Activity.objects.create(actor=request.user, verb='commented', target=str(cr))
            # If request was made via AJAX (XHR), return JSON success so client-side can update without redirect
            if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                return JsonResponse({'status': 'ok'})
            return redirect(request.path)

    return render(request, 'change_management/cr_detail.html', {'cr': cr, 'comments': comments})


class ChangeRequestListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Staff-only paginated list of Change Requests."""
    model = ChangeRequest
    template_name = 'change_management/change_list.html'
    context_object_name = 'change_requests'
    paginate_by = 20

    def test_func(self):
        # Allow staff or users with explicit permission
        user = self.request.user
        return bool(user and (user.is_staff or user.has_perm('change_management.view_changerequest')))

    def get_queryset(self):
        return ChangeRequest.objects.all().order_by('-created_at')
