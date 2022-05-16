from django.contrib import admin
from .models import *
# Register your models here.


class Admin(admin.ModelAdmin):
    pass


admin.site.register(Accounts, Admin)
admin.site.register(School_list, Admin)
admin.site.register(Tournament_list, Admin)
admin.site.register(Tournaments_school, Admin)
admin.site.register(Tournaments_participant, Admin)
admin.site.register(Tournaments_team, Admin)
admin.site.register(Result, Admin)
admin.site.register(Team_statistics, Admin)
admin.site.register(Team_comments, Admin)
admin.site.register(Speaker_points, Admin)
admin.site.register(documents, Admin)
admin.site.register(blog, Admin)