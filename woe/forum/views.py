from django.shortcuts import render, redirect
from django.views.generic.edit import FormView
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils.datastructures import SortedDict
from django.contrib.sessions.models import Session
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.http import Http404
from django.utils import timezone
from django.http import JsonResponse
from django.utils.html import strip_tags, escape
from . import models
from . import forms
import arrow

class StatusUpdate(View):
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(StatusUpdate, self).dispatch(*args, **kwargs)

    def post(self, request, status):
        if request.POST.get("reply", "false") == "true":
            status = get_object_or_404(models.StatusUpdate, pk=status)
            # TODO - check if a user can reply to statuses
            # TODO - check for ignores
            # TODO - add limit on replies
        
            if len(request.POST.get("text","")) < 1:
                raise Http404("")
             
            status_reply = models.StatusComment(
                status = status,
                author = request.user,
                comment = request.POST.get("text","")
            )
            status_reply.save()
        
            response = {"status": "OK"}
            return JsonResponse(response)
        else:
            status = get_object_or_404(models.StatusUpdate, pk=status)
            status_comments = models.StatusComment.objects.filter(status=status).order_by("created").select_related("author__profile")
            response = {"replies": [], "status": "OK"}
            
            for comment in status_comments:
                response["replies"].append({
                    "pk": comment.pk,
                    "author": comment.author.profile.display_name,
                    "text": escape(comment.comment),
                    "date": arrow.get(comment.created).humanize(),
                    "author_id": comment.author_id,
                    "author_avatar": "" # TODO
                })

            return JsonResponse(response)
    
    def get(self, request, status): # TODO - remove default
        status = get_object_or_404(models.StatusUpdate, pk=status)
        status_comments = models.StatusComment.objects.filter(status=status)
        
        if status.hidden == True and not request.user.is_staff():
            raise Http404("This status has been hidden.")
        
        #TODO - Check if a user was blocked from statuses?
        recent_status_updates = models.StatusUpdate.objects.filter(profile=None).order_by("-created")[:5]
        
        mod = False
        if status.author_id == request.user.pk or request.user.is_staff == True:
            mod = True
        
        context = {
            "recent_status_updates": recent_status_updates,
            "status": status,
            "mod": mod
        }
        
        if request.user.is_authenticated():
            participant, created = models.StatusParticipant.objects.get_or_create(
                    status = status,
                    user = request.user
                )
            if created:
                participant.save()
            context["participant"] = participant
        
        return render(request, "general/status_update.jade", context)

class Index(View):
    def get(self, request):
        
        # Categories
        
        categories = models.Category.objects.all().select_related("parent").order_by("-parent")
        
        category_tree = SortedDict()
        
        for category in categories:
            if category.parent == None:
                category_tree[category.title] = [category]
            else:
                category_tree[category.parent.title].append(category)
        
        # Status updates
        
        status_updates = models.StatusUpdate.objects.filter(profile=None).order_by("-created")[:5]
        
        # Sessions (online users and guests)
        
        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        user_id_list = []
        anonymouse = 0
        
        for session in sessions:
            session_data = session.get_decoded()
            uid = session_data.get("_auth_user_id", False)
            if uid == False:
                anonymouse += 1
            else:
                user_id_list.append(uid)
        
        online_users = models.Profile.objects.filter(user__id__in=user_id_list, hide_login=False)
        
        # Post count
        post_count = models.Post.objects.all().count()
        
        # Member count
        member_count = models.Profile.objects.all().count()
        
        # Newest member    
        newest_member = models.Profile.objects.order_by("-user__id")[:1][0]
        
        context = {
            "categories": category_tree,
            "statuses": status_updates,
            "online_users": online_users,
            "guest_users": anonymouse,
            "all_users": anonymouse+len(online_users),
            "post_count": post_count,
            "member_count": member_count,
            "newest_member": newest_member
        }        
        return render(request, "general/index.jade", context)

@csrf_exempt
def sign_out(request):
    if request.method == "POST":
        logout(request)
        return redirect("/")

class SignInView(FormView):
    template_name = "general/sign_in.jade"
    form_class = forms.SignInForm
    success_url = "/"
    
    def form_valid(self, form):
        login(self.request, form.cleaned_data["authenticated_user"])
        return super(SignInView, self).form_valid(form)

class RegisterView(FormView):
    template_name = "general/registration.jade"
    form_class = forms.RegisterForm
    success_url = "/"
    
    def form_valid(self, form):
        cleaned_data = form.cleaned_data
        u = User.objects.create_user(
            cleaned_data["username"].lower().strip(), 
            cleaned_data["email"], 
            cleaned_data["password"].strip()
        )
        u.save()
        p = models.Profile(
            user = u,
            how_found = cleaned_data["how_did_you_find_us"],
            display_name = cleaned_data["username"].strip()
        )
        p.save()
        # SETUP EMAIL ADDRESS STUFF
        return super(RegisterView, self).form_valid(form)