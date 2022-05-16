"""debate URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from main.views import *
from django.conf.urls.static import static

urlpatterns = [
    path('stonewall@bsq/', admin.site.urls),
    path('', homepage, name="homepage"),
    path('signup/', signup, name="signup"),
    path('signup-coach/', coach_signup, name="coach_signup"),
    path('user/', user, name="user"),
    path('landing/', landing),
    path('school-landing/', school_landing, name="school_landing"),
    path('school-landing/create-tournament/',tournament_cre, name="tournament_cre"),
    path('school-landing/register-for-tournament/<str:s>/',tournament_reg, name="tournament_reg"),
    path('school-landing/<str:s>/delete_tournament/',tournament_del,name="delete tournament"),
    path('school-landing/edit-registered-schools/<str:s>/<str:t>/',remove_school,name="remove school"),
    path('create-school/', school_reg, name="school_reg"),
    path('logout/', log_out, name="log_out"),
    path('school-landing/register-for-tournament/<str:s>/<str:st>/delete/', remove_team),
    path('school-landing/register-for-tournament/<str:s>/<str:st>/delete_judge/', remove_judge),
    path('school-landing/leave/<str:s1>/<str:s>/', leave_tournament),
    path('tournament-landing/<str:s>/',tournament_landing, name="tournament_landing"),
    path('tournament-entries/<str:s>/',tournament_entries, name="tournament_entries"),
    path('tournament-pairings/<str:s>/<str:r>/',tournament_pairings, name="tournament_pairings"),
    path('<str:s>/tournament-administration-base/',tournament_administration_base, name="tournament_admin_base"),
    path('round-info/<str:s>/',judge_round_info, name="judge_round_info"),
    path('round-info/<str:s>/decision-submission/<str:r>/',judge_results_submission, name="judge_results_submission"),
    path('tournament-results/<str:s>/<str:r>/',results, name="results_page"),
    path('team-result/<str:s>/<str:t_name>/',team_result, name="team_result"),
    path('tournament-bracket/<str:s>/',tournament_bracket, name="tournament_bracket"),
    path('info/<str:s>/',student_comments, name="student"),
    path('final-result/<str:s>/', final_result, name="final_result"),
    path('speaker-point-ranking/<str:s>/', speaker_point_ranking, name="speaker_point_ranking"),
    path('verify_email/',sending_email,name="sending_email"),
    path('email_verified/<str:s>/<str:t>/',verification,name="verification"),
    path('contact-information/<str:s>/',contact,name="contact"),
    path('rankings/',rankings,name="rankings"),
    path('school-landing/remove_permanently/<str:t>/<str:s>/',remove_permanently,name="remove permanently"),
    path('school-landing/accept/<str:t>/<str:s>/',accept_roster,name="accept roster"),
    path('inst/',instruction,name="inst"),
    path('blog/',blogs,name="blog"),
    path('blog/<int:s>/',blogs,name="blog_pages"),
    path('blog/post/<int:s>/',posts,name="posts"),
]
