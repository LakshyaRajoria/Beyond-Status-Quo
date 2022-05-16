from django.db import models
from django.contrib.auth.models import User

class Accounts(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    student = models.BooleanField(default=False)
    judge = models.BooleanField(default=False)
    coach = models.BooleanField(default=False)
    school = models.TextField(null=True)
    verified = models.BooleanField(default=False)
    verification_code = models.TextField()
    elo = models.IntegerField(default=1000)

    def __str__(self):
        return "%s" % (self.name)

class School_list(models.Model):
    name = models.CharField(max_length=120)
    street = models.TextField()
    city = models.TextField()
    state = models.TextField()
    pin_code = models.CharField(max_length=6)
    adult_name = models.CharField(max_length=120)
    adult_email = models.EmailField(null=True, blank=True)
    adult_phone = models.CharField(max_length=10)

    def __str__(self):
        return "%s" % (self.name)

class Tournament_list(models.Model):
    name = models.CharField(max_length=150)
    start_date = models.DateField()
    end_date = models.DateField()
    host = models.CharField(max_length=120)
    description = models.TextField()
    n_rounds = models.CharField(max_length=6)
    street = models.TextField()
    city = models.TextField()
    state = models.TextField()
    pin_code = models.CharField(max_length=6)
    min_students = models.CharField(max_length=6, default=2)
    max_students = models.CharField(max_length=6)
    max_teams = models.CharField(max_length=2)
    break_round = models.CharField(max_length=14)
    reg_deadline = models.DateField()
    speaker_point_show = models.BooleanField(default=True)
    only_school_judge = models.BooleanField(default=False)
    private = models.BooleanField(default=False)

    def __str__(self):
        return "%s" % (self.name)

class Tournaments_school(models.Model):

    tournament_name = models.CharField(max_length=150)
    school_name = models.CharField(max_length=120)
    supervisor_name = models.TextField(max_length=150)
    supervisor_number = models.CharField(max_length=10)

    def __str__(self):
        return "%s" % (self.tournament_name)

class Tournaments_team(models.Model):

    tournament_name = models.CharField(max_length=150)
    school_name = models.CharField(max_length=120)
    team_name = models.CharField(max_length=120)

    def __str__(self):
        return "%s" % (self.team_name)

class Tournaments_participant(models.Model):

    tournament_name = models.CharField(max_length=150)
    school_name = models.CharField(max_length=120)
    team_name = models.CharField(max_length=120)
    acc_email = models.EmailField()

    def __str__(self):
        return "%s %s" % (self.tournament_name, self.team_name)

class Result(models.Model):
    tournament_name = models.CharField(max_length=150)
    round_no = models.CharField(max_length=6)
    team1 = models.CharField(max_length=120)
    team2 = models.CharField(max_length=120, null=True, blank=True)
    winner = models.CharField(max_length=120, null=True, blank=True)
    judge = models.CharField(max_length=120, null=True, blank=True)

    def __str__(self):
        return "%s %s" % (self.team1, self.team2)

class Team_statistics(models.Model):
    tournament_name = models.CharField(max_length=150)
    team_name = models.CharField(max_length=120)
    wins = models.CharField(max_length=2, default=0)
    losses = models.CharField(max_length=2, default=0)

    def __str__(self):
        return "%s" % (self.team_name)

class Team_comments(models.Model):
    tournament_name = models.CharField(max_length=150)
    round_no = models.CharField(max_length=6)
    team_name = models.CharField(max_length=120)
    comment = models.TextField(null=True, blank=True)

class Speaker_points(models.Model):
    tournament_name = models.CharField(max_length=150)
    round_no = models.CharField(max_length=6)
    participant = models.EmailField()
    points = models.CharField(max_length=3)

    def __str__(self):
        return "%s" % (self.participant)

class documents(models.Model):
    tournament_name = models.CharField(max_length=150)
    doc_name = models.CharField(max_length=100)
    doc = models.FileField(upload_to='')

    def __str__(self):
        return self.doc_name

class blog(models.Model):
    title = models.CharField(max_length=150)
    author = models.CharField(max_length=120,default="ananymous")
    body = models.TextField()
    date = models.DateField()
    bio = models.TextField(null=True,blank=True,default=None)
    banner = models.FileField(upload_to='',default="banner")
