from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse
from django.utils.html import escape
from django.utils.translation import gettext as _
from django.views.generic import RedirectView

from parsifal.apps.activities.constants import ActivityTypes
from parsifal.apps.activities.models import Activity
from parsifal.apps.blog.models import Entry


def get_following_feeds(user):
    feeds = []
    try:
        activities = []
        followers = Activity.objects.select_related("to_user__profile", "from_user__profile").filter(
            to_user=user, activity_type=ActivityTypes.FOLLOW
        )
        for follower_user in followers:
            activities.append(follower_user)
        following = Activity.objects.select_related("to_user__profile", "from_user__profile").filter(
            from_user=user, activity_type=ActivityTypes.FOLLOW
        )
        for following_user in following:
            activities.append(following_user)
            initial_activity = Activity.objects.get(
                from_user=user, to_user=following_user.to_user, activity_type=ActivityTypes.FOLLOW
            )
            following_user_activities = Activity.objects.filter(
                from_user=following_user.to_user, activity_type=ActivityTypes.FOLLOW, date__gte=initial_activity.date
            ).exclude(to_user=user)
            for activity in following_user_activities:
                activities.append(activity)
        activities.sort(key=lambda a: a.date, reverse=True)
        for activity in activities:
            if activity.from_user == user:
                activity.message = _('<a href="{0}">You</a> are now following <a href="{1}">{2}</a>').format(
                    reverse("reviews", args=(user.username,)),
                    reverse("reviews", args=(activity.to_user.username,)),
                    escape(activity.to_user.profile.get_screen_name()),
                )
            else:
                is_following = activity.to_user.profile.get_screen_name()
                if activity.to_user == user:
                    is_following = _("you")
                activity.message = _('<a href="{0}">{1}</a> is now following <a href="{2}">{3}</a>').format(
                    reverse("reviews", args=(activity.from_user.username,)),
                    escape(activity.from_user.profile.get_screen_name()),
                    reverse("reviews", args=(activity.to_user.username,)),
                    escape(is_following),
                )
            feeds.append(activity)
    except Exception:
        pass
    return feeds


def home(request):
    if request.user.is_authenticated:
        user_reviews = request.user.profile.get_reviews()
        feeds = get_following_feeds(request.user)
        latest_news = Entry.objects.filter(status=Entry.PUBLISHED).order_by("-start_publication").first()
        return render(
            request,
            "core/home.html",
            {"user_reviews": user_reviews, "feeds": feeds, "latest_news": latest_news},
        )
    return render(request, "core/cover.html")


class LoginRedirectView(LoginRequiredMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse("reviews", kwargs={"username": self.request.user.username})
