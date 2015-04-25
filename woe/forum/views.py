from django.shortcuts import render, redirect
from django.views.generic.edit import FormView
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils.datastructures import SortedDict
from django.contrib.sessions.models import Session
from django.utils import timezone
from . import models
from . import forms

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