from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, HttpResponseRedirect, get_object_or_404, redirect
from django.contrib.auth.models import User
from .models import *
import random
from random import randint
import datetime
from django.contrib import messages
from django.core.mail import EmailMessage
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.template.loader import render_to_string
import os
import xlwt
from django.http import HttpResponse, FileResponse
from itertools import islice

def blogs(request,s=1):

    context={"older":s+1,"newer":s-1}
    posts = [x for x in blog.objects.all()]

    if s > len(posts)//5+1:
        return HttpResponseRedirect ("/blog/"+str(len(posts)//5+1)+"/")

    try:
        temp = [posts[(s-1)*5+1],posts[(s-1)*5+2],posts[(s-1)*5+3],posts[(s-1)*5+4],posts[(s-1)*5+5]]
    except:
        temp = []
        for x in range(1,len(posts)%5+1):
            temp.append(posts[-x])

    posts = temp

    if s*5 > len(posts):
        context['older'] = False
    if s == 1:
        context['newer'] = False

    posts.reverse()
    context.update({"posts":posts})
    return render (request,"blog/homepage.html", context)

def posts(request,s):
    s = str(s)
    try:
        post = blog.objects.all().filter(id=s)[0]
    except:
        return HttpResponseRedirect('/blog/')

    all_posts = [x.id for x in blog.objects.all().filter()]

    temp = [all_posts[-1],all_posts[-1]-1,all_posts[-1]-2]
    temp = [ele for ele in temp if ele > 0]

    latest = []
    for x in temp:
        try:
            latest.append(blog.objects.get(id=x))
        except:
            pass

    if int(s)+1 in all_posts:
        next_post = blog.objects.get(id=int(s)+1)
    else:
        next_post = None

    if int(s)-1 in all_posts:
        prev_post =  blog.objects.get(id=int(s)-1)
    else:
        prev_post = None

    if post.banner == "banner":
        temp = None
    else:
        temp = post.banner.url

    context={
        "title":post.title,
        "author":post.author,
        "body":post.body.split('\n'),
        "date":post.date,
        "latest":latest,
        "next":next_post,
        "prev":prev_post,
        "bio":post.bio,
        "banner":temp,
    }

    return render (request, "blog/post.html",context)

def instruction(request):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf = open(os.path.join(BASE_DIR, 'static')+'/Instructions.pdf', 'rb')
    return FileResponse(pdf, content_type='application/pdf')

def sending_email(request):
    if request.user.is_authenticated:
        if Accounts.objects.all().filter(email=request.user)[0].verified == True:
            return HttpResponseRedirect('/')
    else:
        return HttpResponseRedirect('/')

    template = render_to_string('email_template.html',{"user":Accounts.objects.all().filter(email=request.user)[0]})

    email = EmailMessage(
        'CONFIRM YOUR EMAIL - BEYOND STATUS QUO',
        template,
        settings.EMAIL_HOST_USER,
        [request.user],
    )

    email.fail_silently = False
    email.send()
    return HttpResponseRedirect('/')

def verification(request,s, t):
    user = Accounts.objects.all().filter(email=t)[0]
    if user.verified == True:
        return HttpResponseRedirect('/')

    def send(user):
        template = render_to_string('email_verified.html',{"user":user.name})

        email = EmailMessage(
            'EMAIL CONFIRMED - BEYOND STATUS QUO',
            template,
            settings.EMAIL_HOST_USER,
            [user.email],
        )

        email.fail_silently = False
        email.send()

    if str(s) == str(user.verification_code):
        user.verified = True
        user.save()
        send(user)

    return render(request,'verification_alert.html',{"verified":user.verified})

def homepage(request):

    tournaments =  [x for x in Tournament_list.objects.all()]
    y = []
    p=[]
    for x in tournaments:
        if x.reg_deadline < datetime.date.today():
            y.append(x)
        if x.private == True:
            p.append(x)

    for x in p:
        tournaments.remove(x)
    tournaments.sort(key=lambda x: x.reg_deadline)
    tournaments.reverse()
    temp=tournaments[:]
    tournaments= []
    for x in range(len(temp)):
        tournaments.append([(x+1),temp[x]])
    f_10 = []
    for i in range(10):
        try:
            f_10.append(tournaments[0])
            tournaments.remove(tournaments[0])
        except:
            break
    mobile = request.user_agent.is_mobile

    context = {
        "action":request.POST.get('action'),
        "email":request.POST.get('email'),
        "password":request.POST.get('psw'),
        "f_10":f_10,
        "object_list": tournaments,
        "login":False,
        "mobile":mobile,
        "school_verified":True,
    }

    #----------login authentication---------
    message = ""
    if context["action"] == "sub":
        user =  authenticate(request,username=context["email"], password=context["password"])
        if user is None:
            message = "Wrong Username or Password"
            context.update({"message":message})
        else:
            login(request,user)
            return HttpResponseRedirect ('/')
    #----------end of login authentication----------
    if request.user.is_authenticated:
        if str(request.user) == "team@beyondstatusquo.in":
            context.update({"user":"admin", "verified":True})
        else:
            context.update({ "user": Accounts.objects.all().filter(email=request.user)[0].name, "verified":True})
            if Accounts.objects.all().filter(email=request.user)[0].verified == False:
                context.update ({"verified":False})
            if Accounts.objects.all().filter(email=request.user)[0].coach == True:
                if Accounts.objects.all().filter(email=request.user)[0].school == None:
                    obj = get_object_or_404(Accounts, email=request.user)
                    obj.delete()
                    u = User.objects.get(username=request.user)
                    u.delete()
                    return HttpResponseRedirect('/')
                elif Accounts.objects.all().filter(email=request.user)[0].school.split()[-1] == "__notverified__":
                    context['school_verified'] = False

        context['login'] = True
    return render(request,'homepage.html',context)

def log_out(request):
    logout(request)
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/')

def landing(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/')

    if Accounts.objects.all().filter(email=request.user)[0].coach == True:
        return HttpResponseRedirect('/')

    email = request.user
    tournaments_judged = []
    future_tournaments = []
    today = datetime.date.today()
    for x in Tournaments_participant.objects.all().filter(acc_email=email):
        tournament_info = Tournament_list.objects.all().filter(name=x.tournament_name)[0]
        if today < tournament_info.start_date:
            future_tournaments.append([x.tournament_name, tournament_info.start_date, tournament_info.end_date])
        else:
            tournaments_judged.append([x.tournament_name, tournament_info.start_date, tournament_info.end_date])

    action = request.POST.get('action')
    if action == "sub":
        school = request.POST.get('school')
        person = Accounts.objects.all().filter(email=request.user)[0]
        person.school = school +" _notaccepted_"
        person.save()
        return HttpResponseRedirect('/user/')

    schools = [x.name for x in School_list.objects.all()]
    schools = sorted(schools)
    context= {
        "tournaments_judged":tournaments_judged,
        "future_tournaments":future_tournaments,
        "user": Accounts.objects.all().filter(email=request.user)[0],
        "schools":schools,
    }

    return render(request, 'landing_page.html', context)

def student_comments(request, s):
    user = request.user
    #validation for user
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/')

    if Accounts.objects.all().filter(email=user)[0].student == False:
        return HttpResponseRedirect('/')

    team = Tournaments_participant.objects.all().filter(tournament_name=s, acc_email=user)[0].team_name
    comments = Team_comments.objects.all().filter(tournament_name=s, team_name=team)

    info = []
    for x in comments:
        for y in Result.objects.all().filter(tournament_name=s, round_no=x.round_no):
            if y.team1 == team:
                info.append([y.round_no, team, y.team2, y.judge, x.comment])
            elif y.team2 == team:
                info.append([y.round_no, team, y.team1, y.judge, x.comment])

    break_list = {1:"Finals", 2:"Semi-Finals", 4:"Quarter-Finals", 8:"Octo-Finals"}
    bround = int(Tournament_list.objects.get(name=s).break_round)

    break_dict = {}
    c = 1
    while bround > 1:
        break_dict.update({"B"+str(c):break_list[bround]})
        bround //= 2
        c += 1
        if  bround == 1:
            break
    break_dict.update({"B"+str(c):"Finals"})
    for i in range(len(info)):
        if info[i][0] in break_dict:
            info[i][0] = break_dict[info[i][0]]

    user = Accounts.objects.all().filter(email=user)[0].name
    context = {
        "tournament_name":s,
        "user_name":user,
        "info":info,
        }
    return render (request, 'student_comments.html',context)

def judge_round_info(request, s):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/')

    if Accounts.objects.all().filter(email=request.user)[0].judge == False:
        return HttpResponseRedirect('/')

    pairs_query = Result.objects.all().filter(tournament_name=s, judge=Accounts.objects.all().filter(email=request.user)[0].name)

    break_list = {1:"Finals", 2:"Semi-Finals", 4:"Quarter-Finals", 8:"Octo-Finals"}
    bround = int(Tournament_list.objects.get(name=s).break_round)

    break_dict = {}
    c = 1
    while bround > 1:
        break_dict.update({"B"+str(c):break_list[bround]})
        bround //= 2
        c += 1
        if bround == 1:
            break
    break_dict.update({"B"+str(c):"Finals"})
    pairs = []
    rounds = []
    for x in pairs_query:
        message = True
        pairing = Result.objects.all().filter(tournament_name= s, round_no= x.round_no, judge=Accounts.objects.all().filter(email=request.user)[0].name)[0]
        if pairing.winner != "" and pairing.winner != None:
            message = False

        pairs.append([x.round_no, x.team1, x.team2, message])
        rounds.append(x.round_no)

    rounds = sorted(rounds)
    pairs = sorted(pairs,key=lambda x: x[0])

    for i in range(len(pairs)):
        if pairs[i][0] in break_dict:
            pairs[i].append(pairs[i][0])
            pairs[i][0] = (break_dict[pairs[i][0]])
            rounds[i] = break_dict[rounds[i]]

    context = {
        "pairs":pairs,
        "rounds":rounds,
        "user":Accounts.objects.all().filter(email=request.user)[0].name,
        "message": message,
    }

    return render(request, 'judge_round_info.html', context)

def judge_results_submission(request, s, r):

    def elo_calcualtion(team1, team2, winner): #parameters must be the team names
        team1x = [x.acc_email for x in Tournaments_participant.objects.all().filter(tournament_name=s,team_name=team1)]
        team1x = [Accounts.objects.get(email=x) for x in team1x]

        elo_team1 = [i.elo for i in team1x]
        elo_team1 = sum(elo_team1)/len(elo_team1) #average elo rating of team1

        team2x = [x.acc_email for x in Tournaments_participant.objects.all().filter(tournament_name=s,team_name=team2)]
        team2x = [Accounts.objects.get(email=x) for x in team2x]

        elo_team2 = [i.elo for i in team2x]
        elo_team2 = sum(elo_team2)/len(elo_team2) #average elo rating of team2

        if elo_team2 > elo_team1:# team1 needs to be the one with higher elo rating
            temp = elo_team1
            elo_team1 = elo_team2
            elo_team2 = temp

            temp2 = team1
            team1 = team2
            team2 = temp2

        factor_difference = elo_team1/elo_team2

#------------------------------------lakshya ka kaam------------------------------------------------------
        all_participants_refr = Tournaments_participant.objects.all().filter(tournament_name=s)
        all_participants_elos = []
        for a in all_participants_refr:
            all_participants_elos.append(Accounts.objects.all().filter(email=a.acc_email)[0].elo)
        avg_elos = sum(all_participants_elos) / len(all_participants_elos)

        if avg_elos >= 3000: # difficulty = 10
            t_diff_multiplier = 2
        if avg_elos >= 2500 and avg_elos <= 2800: #difficulty 9,8
            t_diff_multiplier = 1.75
        if avg_elos >= 1500 and avg_elos <= 2500 :# difficulty 7,6,5
            t_diff_multiplier = 1.5
        if avg_elos >= 1300 and avg_elos <= 1500 :# difficulty 4
            t_diff_multiplier = 1.25
        if avg_elos >= 1100 and avg_elos <= 1300:#  difficulty 3
            t_diff_multiplier = 1.1
        if avg_elos <= 1100: # 2,1
            t_diff_multiplier = 1



#up till here all multipliers are calculated, so now only points need to be added to the elos.
#--------------------------------------------------------------------------------------------------------------

        if team1 == winner:
            point = factor_difference * 40 * t_diff_multiplier
        else:
            point = 1/factor_difference * 40 * t_diff_multiplier

        if r[0] == "B":
            start_br = int(Tournament_list.objects.all().filter(name=s)[0].break_round)
            break_round_value = int(r[1])
            ct = 1
            while start_br != 1:
                ct += 1
                start_br = start_br/2
            multiplier = []
            a = 2
            for i in range (ct):
                multiplier.append(a)
                a -= 0.25
            multiplier.reverse()
            b_multiplier = multiplier[int(r[1])-1]

            point *= b_multiplier

        # adding/deducting points to teams
        for x in team1x:# team won
            print (x.email,x.name)
            x.elo += int(point)
            x.save()
        for y in team2x:#team lost
            print (y.email,y.name)
            y.elo -= int(point)
            y.save()


    if Accounts.objects.all().filter(email=request.user)[0].judge == False:
        return HttpResponseRedirect('/')

    pairing = Result.objects.all().filter(tournament_name= s, round_no= r, judge=Accounts.objects.all().filter(email=request.user)[0].name)[0]
    if pairing.winner != None:
        return HttpResponseRedirect('/round-info/'+s+'/')

    message = ""

    team1_p = Tournaments_participant.objects.all().filter(tournament_name= s, team_name=pairing.team1)
    team2_p = Tournaments_participant.objects.all().filter(tournament_name= s, team_name=pairing.team2)

    team1_participants = []
    for x in team1_p:
        team1_participants.append(Accounts.objects.all().filter(email=x.acc_email)[0].name)

    team2_participants = []
    for x in team2_p:
        team2_participants.append(Accounts.objects.all().filter(email=x.acc_email)[0].name)

    participants = []
    if len(team1_participants)>len(team2_participants):
        for i in range(len(team1_participants)-len(team2_participants)):
            team2_participants.append("")
    elif len(team2_participants)>len(team1_participants):
        for i in range(len(team2_participants)-len(team1_participants)):
            team1_participants.append("")
    for i in range(len(team1_participants)):
        participants.append([team1_participants[i],team2_participants[i]])

    context = {
        "user":Accounts.objects.all().filter(email=request.user)[0].name,
        "first_team_name": pairing.team1,
        "second_team_name": pairing.team2,
        "participants":participants,
        "message": message,
        }

    action = request.POST.get('action')
    if action == "sub":
        winner = request.POST.get('winner')

        if winner == "" or winner == None:
            message = "You haven't decided the winner"
            context.update({"message":message})
        else:
            obj = Result.objects.get(tournament_name= s, round_no= r, judge=Accounts.objects.all().filter(email=request.user)[0].name)
            obj.winner = winner
            obj.save()

            if r[0] != "B":
                obj = Team_statistics.objects.get(tournament_name= s, team_name= winner)
                obj.wins = str(int(obj.wins) + 1)
                obj.save()

                if pairing.team1 == winner:
                    obj = Team_statistics.objects.get(tournament_name= s, team_name= pairing.team2)
                else:
                    obj = Team_statistics.objects.get(tournament_name= s, team_name= pairing.team1)
                obj.losses = str(int(obj.losses) + 1)
                obj.save()

            Team_comments.objects.create(tournament_name=s, round_no=r,
                team_name= pairing.team1, comment= request.POST.get('team1')) # Team1 comments
            Team_comments.objects.create(tournament_name=s, round_no=r,
                team_name= pairing.team2, comment= request.POST.get('team2')) #Team2 comments
            for i in range(len(participants)):
                if participants[i][0] != "":
                    Speaker_points.objects.create(tournament_name=s, round_no=r,
                        participant= Accounts.objects.all().filter(name = participants[i][0])[0].email,
                         points= request.POST.get(participants[i][0])) #team1 member
                if participants[i][1] != "":
                    Speaker_points.objects.create(tournament_name=s, round_no=r,
                        participant= Accounts.objects.all().filter(name = participants[i][1])[0].email,
                         points= request.POST.get(participants[i][1])) #team2 member
            elo_calcualtion(pairing.team1,pairing.team2,winner)
            return HttpResponseRedirect('../../')

    return render(request, 'judge_results_submission.html', context)


def rankings(request):
    response = HttpResponse(content_type='application/ms-excel')

    response['Content-Disposition'] = 'attachment; filename=' + "rankings.xls"
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Rankings')
    # Sheet header, first row
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    columns = ['Name', 'School Name', 'Points']
    #columns = ['Organization Name', 'Description', 'Start Time', 'End Time', ]
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()
    rows = Accounts.objects.all().values_list('name', 'school', 'elo').filter(student=True,verified=True)

    rows_2 = []
    for a in rows:
        a = list(a)
        a = tuple(a)
        rows_2.append(a)
    rows_2.sort(key = lambda x: x[2])
    rows_2.reverse()
    for row in rows_2:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    wb.save(response)
    return response


def user(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/')
    elif Accounts.objects.all().filter(email=request.user)[0].student == True or Accounts.objects.all().filter(email=request.user)[0].judge == True:
        return redirect('../landing/')
    elif Accounts.objects.all().filter(email=request.user)[0].coach == True and Accounts.objects.all().filter(email=request.user)[0].school != None:
        if Accounts.objects.all().filter(email=request.user)[0].verified == False:
            return HttpResponseRedirect('/verify_email/')
        else:
            return redirect('../school-landing/')
    elif Accounts.objects.all().filter(email=request.user)[0].coach == True and Accounts.objects.all().filter(email=request.user)[0].school == None:
        obj = get_object_or_404(Accounts, email=request.user)
        obj.delete()
        return HttpResponseRedirect('/')



def signup(request):
    context = {
        "action":request.POST.get('action'),
        "email":request.POST.get('email'),
        "name":request.POST.get('name'),
        "school":request.POST.get('school'),
        "role":request.POST.get('role'),
        "psw":request.POST.get('psw'),
        "psw-repeat":request.POST.get('psw-repeat'),
        "queryset":[x.school for x in Accounts.objects.all().filter(coach=True, verified=True)], #.filter()
        "message":None,
    }

    temp = context['queryset']
    for x in temp:
        y = x.split()
        if y[-1] == "__notverified__":
            temp.remove(x)
    context['queryset'] = temp

    if context["action"] == "sub":
        condition = True
        if User.objects.filter(username=context['email']).exists():
            condition = False
            context['message'] = "Email already exists"
        elif context['psw'] == context['psw-repeat']:
            code = str(randint (10000000, 99999999))
            if context['message'] == None:
                if context["role"] == "judge":
                    Accounts.objects.create(name=(context["name"]),email=context["email"],school=context["school"]+" _notaccepted_",judge=True, verification_code=code)
                elif context["role"] == "student":
                    Accounts.objects.create(name=(context["name"]),email=context["email"],school=context["school"]+" _notaccepted_",student=True, verification_code=code)
                user = User.objects.create_user(context['email'],'',context['psw']) #stores user account info
                user.save()
                login(request,user)
                return HttpResponseRedirect('/verify_email/')
        else:
            context['message'] = "Input passwords do not match"

    return render(request,'g_signup.html',context)

def coach_signup(request):
    context = {
        "action":request.POST.get('action'),
        "email":request.POST.get('email'),
        "name":request.POST.get('name'),
        "psw":request.POST.get('psw'),
        "psw-repeat":request.POST.get('psw-repeat'),
        "message":None,
    }

    if context["action"] == "sub":
        condition = True
        if User.objects.filter(username=context['email']).exists():
            condition = False
            context['message'] = "Email already exists"
        elif context['psw'] == context['psw-repeat']:
            Accounts.objects.create(name=(context["name"]),email=context["email"],school=None,coach=True)
            user = User.objects.create_user(context['email'],'',context['psw']) #stores user account info
            user.save()
            login(request,user)
            return HttpResponseRedirect('/create-school/')
        else:
            context['message'] = "Input passwords do not match"
    return render(request,'coach_signup.html', context)

def school_reg(request):
    if not request.user.is_authenticated or Accounts.objects.all().filter(email=request.user)[0].coach == False:
       return HttpResponseRedirect ('/')

    def send_email(name, email, school):
        template = render_to_string('new_coach.html',{"name":name,"email":email,"school":school})

        email = EmailMessage(
            'New coach registered',
            template,
            settings.EMAIL_HOST_USER,
            ["team@beyondstatusquo.in"],
        )
        email.fail_silently = False
        email.send()

    context = {}

    school = request.POST.get('school/team_name')
    street = request.POST.get('street_name')
    city = request.POST.get('city_name')
    state = request.POST.get('state_name')
    pincode = request.POST.get('pincode')
    name = request.POST.get('name')
    email = request.POST.get('email')
    phone = request.POST.get('phone')
    action = request.POST.get('action')
    if action == "sub":
        if len(School_list.objects.all().filter(name=school)) != 0:
            message = "School name already exists"
            context.update({"message":message})
        else:
            School_list.objects.create(name=school + " __notverified__",street=street,city=city,state=state,pin_code=pincode,adult_name=name,adult_email=email,adult_phone=phone)
            coach = Accounts.objects.get(email=request.user)
            coach.school = school + " __notverified__"
            coach.verification_code = str(randint (10000000, 99999999))
            coach.save()
            send_email(coach.name,request.user,school)
            return HttpResponseRedirect('/user/')
    return render (request,'school_creation.html', context)

def school_landing(request):
    if not request.user.is_authenticated:
       return HttpResponseRedirect ('/')

    if Accounts.objects.all().filter(email=request.user)[0].coach == False or Accounts.objects.all().filter(email=request.user)[0].school.split()[-1] == "__notverified__":
        return HttpResponseRedirect('/')

    school = Accounts.objects.all().filter(email=request.user)[0].school
    student = Accounts.objects.all().filter(school=school,student=True)
    judge = Accounts.objects.all().filter(school=school,judge=True)
    students = []
    judges = []
    for x in student:
        students.append(x)
    for x in judge:
        judges.append(x)

    rt= Tournaments_school.objects.all().filter(school_name=school)
    all_t =  Tournament_list.objects.all()

    ar=[] #already registered
    ot= [] #other tournaments

    Person_validate = Accounts.objects.all().filter(email=request.user)[0]
    for e1 in all_t:
        c =False
        for e in rt:
            if e1.name == e.tournament_name:
                if Person_validate.coach == True and Person_validate.school == Tournament_list.objects.all().filter(name=e1.name)[0].host:
                    ar.append([Tournament_list.objects.all().filter(name=e1.name)[0],True])
                else:
                    ar.append([Tournament_list.objects.all().filter(name=e1.name)[0],False])
                c = True
        if c==False:
            ot.append(Tournament_list.objects.all().filter(name=e1.name)[0])

    y = []
    for x in ar:
        if x[0].end_date < datetime.date.today():
            ar.remove(x)
    for z in y:
        ar.remove(z)

    for x in ar:
        if x[0].host == school and x[0].start_date > datetime.date.today():
            x.append(True)
            temp = [x.school_name for x in Tournaments_school.objects.all().filter(tournament_name=x[0].name)]
            temp.remove(school)
            x.append(temp)
        else:
            x.append(False)
            x.append(None)
        if x[0].reg_deadline > datetime.date.today():
            x.append(True)
        else:
            if len(Result.objects.all().filter(tournament_name= x[0].name, round_no= "1")) < 1 and Accounts.objects.all().filter(email=request.user)[0].school == x[0].host and x[0].only_school_judge == True:
                x.append(True)
            else:
                x.append(False)
    y = []
    for x in ot:
        if x.reg_deadline < datetime.date.today():
            y.append(x)
        if x.private == True and Person_validate.school != Tournament_list.objects.all().filter(name=x.name)[0].host:
            y.append(x)
    for z in y:
        ot.remove(z)

    requests = [x for x in Accounts.objects.all().filter(school=school + " _notaccepted_")]
    for x in requests:
        if x.verified == False:
            requests.remove(x)

    context= {
        "user": Accounts.objects.all().filter(email=request.user)[0],
        "object_list":ot,
        "object_list1":ar,
        "school_name":school,
        "student":students,
        "judge":judges,
        "requests":requests,
        "mobile":request.user_agent.is_mobile,
    }
    return render (request,'school_landing_page.html', context)

def accept_roster(request, t, s):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/')

    user = Accounts.objects.all().filter(email=request.user)[0]
    if user.coach == False or user.school+" _notaccepted_" != t:
        return HttpResponseRedirect('/')

    person = Accounts.objects.all().filter(email=s)[0]
    temp = person.school.split()
    temp.remove("_notaccepted_")
    temp = " ".join(temp)
    person.school = temp
    person.save()
    return HttpResponseRedirect('/school-landing/')

def remove_permanently(request, t, s):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/')

    user = Accounts.objects.all().filter(email=request.user)[0]
    if user.coach == True:
        if user.school == t or user.school+" _notaccepted_" == t:
            person = Accounts.objects.all().filter(email=s)[0]
            person.school = ""
            person.save()
            return HttpResponseRedirect('/school-landing/')
    else:
        return HttpResponseRedirect('/')

def contact(request,s):

    if not request.user.is_authenticated:
        return HttpResponseRedirect('/')

    school = [x.school_name for x in Tournaments_school.objects.all().filter(tournament_name=s)]
    if Accounts.objects.all().filter(email=request.user)[0].coach == False or Accounts.objects.all().filter(email=request.user)[0].school not in school:
        return HttpResponseRedirect('/')

    contacts = [x for x in Tournaments_school.objects.all().filter(tournament_name=s)]
    response = HttpResponse(content_type='application/ms-excel')

    response['Content-Disposition'] = 'attachment; filename=' + s + " "  + "contacts.xls"
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Contacts')
    # Sheet header, first row
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    columns = ['School', 'Supervisor Name', 'Supervisor Number' ]
    #columns = ['Organization Name', 'Description', 'Start Time', 'End Time', ]
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()
    rows = Tournaments_school.objects.all().filter(tournament_name=s).values_list('school_name', 'supervisor_name', 'supervisor_number')
    rows_2 = []
    for a in rows:
        a = list(a)
        a = tuple(a)
        rows_2.append(a)
    for row in rows_2:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    wb.save(response)
    return response


def remove_school(request,s,t):

    if not request.user.is_authenticated:
        return HttpResponseRedirect('/')

    if Accounts.objects.all().filter(email=request.user)[0].coach == False or Accounts.objects.all().filter(email=request.user)[0].school != Tournament_list.objects.all().filter(name=s)[0].host:
        return HttpResponseRedirect('/')

    Tournaments_school.objects.all().filter(tournament_name=s,school_name=t).delete()
    for x in Tournaments_team.objects.all().filter(tournament_name=s,school_name=t):
        Team_statistics.objects.all().filter(tournament_name=s, team_name=x.team_name).delete()
    Tournaments_team.objects.all().filter(tournament_name=s,school_name=t).delete()
    Tournaments_participant.objects.all().filter(tournament_name=s,school_name=t).delete()

    return HttpResponseRedirect('/school-landing/')

def tournament_cre(request):
    if not request.user.is_authenticated or Accounts.objects.all().filter(email=request.user)[0].coach == False:
       return HttpResponseRedirect ('/')

    context = {
        "user": Accounts.objects.all().filter(email=request.user)[0].name,
        "message":None,
        "mobile":request.user_agent.is_mobile,
        "speaker_point_available":request.POST.get('speaker_point_available'),
    }

    name= request.POST.get('tournament_name')
    start_date= request.POST.get('start-date')
    end_date= request.POST.get('end-date')
    host = Accounts.objects.all().filter(email=request.user)[0].school
    description= request.POST.get('tournament_description')
    street_name = request.POST.get('street_name')
    city= request.POST.get('tournament_city')
    tournament_state = request.POST.get('tournament_state')
    tournament_pin = request.POST.get('tournament_pin')
    action = request.POST.get('action')
    min_students = request.POST.get('min_students')
    max_students = request.POST.get('max_students')
    max_teams = request.POST.get('max_teams')
    n_rounds = request.POST.get('num_rounds')
    break_rounds = request.POST.get('break_rounds')
    reg_deadline = request.POST.get('reg_deadline')
    only_school = request.POST.get('school_judge')
    private = request.POST.get('private_bool')
    online = request.POST.get('online_bool')
    if private == "on":
        private = True
    elif private == None:
        private = False

    if only_school == "on":
        only_school = True
    elif only_school == None:
        only_school = False

    today = datetime.datetime.now()
    if action == "sub":
        if len(Tournament_list.objects.all().filter(name=name)) != 0:
            context['message'] = "Tournament name already exists"
        elif datetime.datetime.strptime(reg_deadline, '%Y-%m-%d') < today:
            context['message'] = "Registration deadline date has passed"
        elif datetime.datetime.strptime(reg_deadline, '%Y-%m-%d') > datetime.datetime.strptime(start_date, '%Y-%m-%d'):
            context['message'] = "Registration deadline date cannot be later than the start date"
        elif datetime.datetime.strptime(reg_deadline, '%Y-%m-%d') > datetime.datetime.strptime(end_date, '%Y-%m-%d'):
            context['message'] = "Registration deadline date cannot be later than end date"
        elif datetime.datetime.strptime(start_date, '%Y-%m-%d') > datetime.datetime.strptime(end_date, '%Y-%m-%d'):
            context['message'] = "Tournament cannot start after it ends!"
        else:
            if online != "t":
                Tournament_list.objects.create(name=name, start_date=start_date, end_date=end_date,
                                                host=host, description=description, n_rounds=n_rounds,
                                                street=street_name, city=city, state=tournament_state,
                                                pin_code=tournament_pin, min_students=min_students,
                                                max_students=max_students, max_teams=max_teams,
                                                break_round=break_rounds, reg_deadline=reg_deadline,
                                                speaker_point_show=context["speaker_point_available"], only_school_judge=only_school, private=private)
            else:
                Tournament_list.objects.create(name=name, start_date=start_date, end_date=end_date,
                                                host=host, description=description, n_rounds=n_rounds,
                                                street="Online", city="Online", state="Online",
                                                pin_code="Online", min_students=min_students,
                                                max_students=max_students, max_teams=max_teams,
                                                break_round=break_rounds, reg_deadline=reg_deadline,
                                                speaker_point_show=context["speaker_point_available"], only_school_judge=only_school, private=private)


        #if context["speaker_point_available"] == "Yes":
            #context.update({"stats":stats})
                #elif context["speaker_point_available"] == "No":
                 #   context.update({"stats":stats})
            # myfile = request.FILES.getlist('myfile')
            # for x in myfile:
                # documents.objects.create(tournament_name=name,doc_name=x.name,doc=x)
            return HttpResponseRedirect('/school-landing/')
    return render (request,'tournament_creation.html', context)

def tournament_reg(request, s):

    school = Accounts.objects.all().filter(email=request.user)[0].school
    if not request.user.is_authenticated or Accounts.objects.all().filter(email=request.user)[0].coach == False:
       return HttpResponseRedirect ('/')

    action = request.POST.get('action')
    student_number = [num+1 for num in range(int(Tournament_list.objects.all().filter(name=s)[0].max_students))]


    student_team = []
    multiple_entry=False
    team_name = ""
    already_exists = []
    pick_judge = False

    judge_already_exists_value = ""
    judge_already_exists = False

    number_of_judges = len(Tournaments_participant.objects.all().filter(tournament_name=s, school_name=school,team_name="N/A"))
    number_of_teams = len(Tournaments_team.objects.all().filter(tournament_name=s, school_name=school))
    message = None

    only_school = Tournament_list.objects.all().filter(name=s)[0].only_school_judge
    if Accounts.objects.all().filter(email=request.user)[0].school == Tournament_list.objects.all().filter(name=s)[0].host:
        only_school = False

    try:
        judge_ = request.POST.get('judge_picked')
        if action == "sub_judge" and judge_ != "Choose...":
            if len(Tournaments_participant.objects.all().filter(acc_email=Accounts.objects.all().filter(name=judge_)[0].email, tournament_name=s)) == 0:
                Tournaments_participant.objects.create(tournament_name=s,school_name=school, team_name = "N/A", acc_email=Accounts.objects.all().filter(name=judge_)[0].email)
            elif len(Tournaments_participant.objects.all().filter(acc_email=Accounts.objects.all().filter(name=judge_)[0].email)) != 0:
                judge_already_exists_value = judge_
                judge_already_exists = True
            if len(Tournaments_school.objects.all().filter(tournament_name=s, school_name=school)) == 0:
                temp = School_list.objects.all().filter(name=school)[0]
                Tournaments_school.objects.create(tournament_name=s,school_name=school, supervisor_name=temp.adult_name, supervisor_number=temp.adult_phone)

        if action == "sub_judge" and judge_ == "Choose...":
            pick_judge = True

        if len(Tournaments_team.objects.all().filter(tournament_name=s, school_name=school)) < int(Tournament_list.objects.all().filter(name=s)[0].max_teams):
            for x in student_number:
                student_team.append(request.POST.get('student_picked' + str(x)))

            student_emails = []
            for a in student_team:
                if a != "Choose...":
                    student_emails.append(Accounts.objects.all().filter(name=a)[0].email)
            student_og = student_team
            student_team = student_emails

            check1 = set(student_team)
            if len(check1) == len(student_team):
                last_names = ""
                for a in student_team:
                    name = Accounts.objects.all().filter(email=a)[0].name.split()
                    last_names = last_names + name[-1][0]
                team_name = school+ " " +last_names
                teams = [x.team_name for x in Tournaments_team.objects.all().filter(tournament_name=s, school_name=school)]

                c = 0
                temp = team_name
                while temp in teams:
                    temp = team_name + str(c)
                    c += 1
                team_name = temp

                if len(Tournaments_school.objects.all().filter(tournament_name=s, school_name=school)) == 0:
                    temp = School_list.objects.all().filter(name=school)[0]
                    Tournaments_school.objects.create(tournament_name=s,school_name=school, supervisor_name=temp.adult_name, supervisor_number=temp.adult_phone)

                choose_num = 0
                for g in student_og:
                    if g == "Choose...":
                        choose_num += 1

                if action == "sub_student" and choose_num < (int(Tournament_list.objects.all().filter(name=s)[0].max_students)-int(Tournament_list.objects.all().filter(name=s)[0].min_students)+1):
                    if number_of_teams >= number_of_judges*2+1 and only_school == False:
                        message = "You need a judge for every two teams"

                    if message == None:
                        already_exists = []
                        for y in student_team:
                            if len(Tournaments_participant.objects.all().filter(acc_email=y, tournament_name=s)) != 0:
                                already_exists.append(Accounts.objects.all().filter(email=y)[0].name)

                        if len(already_exists) == 0:
                            for y in student_team:
                                Tournaments_participant.objects.create(tournament_name=s,school_name=school, team_name = team_name, acc_email=y)
                            if len(Tournaments_team.objects.all().filter(tournament_name=s, team_name= team_name)) == 0:
                                Tournaments_team.objects.create(tournament_name=s,school_name=school,team_name= team_name)
                                Team_statistics.objects.create(tournament_name=s, team_name= team_name)
                elif action == "sub_student":
                    message = "You selected less than the minimum students allowed in a team"
            else:
                multiple_entry = True
        else:
            message = "You have the maximum number of teams allowed for one school."
    except:
        pass

    student = Accounts.objects.all().filter(school=school,student=True)
    judge = Accounts.objects.all().filter(school=school,judge=True)
    students = []
    judges = []
    unverified_accounts = []

    for x in Accounts.objects.all().filter(school=school, verified=False):
        unverified_accounts.append(x.name)

    for x in student:
        if x.name not in unverified_accounts:
            students.append(x.name)
    for x in judge:
        if x.name not in unverified_accounts:
            judges.append(x.name)

    l = [num+1 for num in range(int(Tournament_list.objects.all().filter(name=s)[0].max_students))]

    tournament_teams = Tournaments_team.objects.all().filter(tournament_name=s, school_name=school)
    chosen_judges = Tournaments_participant.objects.all().filter(tournament_name=s, school_name=school,team_name="N/A")
    list = []
    for x in tournament_teams:
        tournament_participants=Tournaments_participant.objects.all().filter(tournament_name=s, school_name=school, team_name=x.team_name)
        members = ""
        for y in tournament_participants:
            members = members + Accounts.objects.all().filter(email=y.acc_email)[0].name + ", "
        members = members[:-2]
        list.append([x.team_name, members, "Students"])

    for j in chosen_judges:
        list.append(["N/A", Accounts.objects.all().filter(email=j.acc_email)[0].name, "Judge"])

    context = {
        "user": Accounts.objects.all().filter(email=request.user)[0].name,
        "students":sorted(students),
        "judges":sorted(judges),
        "list":list,
        "l": l,
        "multiple_entry":multiple_entry,
        "team_name":team_name,
        "already_exists":already_exists,
        "tournament_teams":tournament_teams,
        "pick_judge":pick_judge,
        "judge_already_exists": judge_already_exists,
        "judge_already_exists_value": judge_already_exists_value,
        "message":message,
        "only_school_judge":only_school,
    }
    return render (request,'tournament_registration.html',context)

def tournament_del(request, s):

    try:
        if not request.user.is_authenticated or Accounts.objects.all().filter(email=request.user)[0].coach == False or Accounts.objects.all().filter(email=request.user)[0].school != Tournament_list.objects.all().filter(name=s)[0].host:
            return HttpResponseRedirect ('/')
    except:
        return HttpResponseRedirect ('/')

    school = Accounts.objects.all().filter(email=request.user)[0].school
    get_object_or_404(Tournament_list, name=s, host=school).delete()
    Tournaments_participant.objects.all().filter(tournament_name=s).delete()
    Tournaments_team.objects.all().filter(tournament_name=s).delete()
    Tournaments_school.objects.all().filter(tournament_name=s).delete()
    Result.objects.all().filter(tournament_name=s).delete()
    Team_statistics.objects.all().filter(tournament_name=s).delete()
    Speaker_points.objects.all().filter(tournament_name=s).delete()
    Team_comments.objects.all().filter(tournament_name=s).delete()
    # documents.objects.all().filter(tournament_name=s).delete()
    return HttpResponseRedirect('/school-landing/')

def remove_team(request, s, st):

    obj = get_object_or_404(Tournaments_team, tournament_name=s, team_name=st)
    obj.delete()
    obj = get_object_or_404(Team_statistics, tournament_name=s, team_name=st)
    obj.delete()

    participant_list = Tournaments_participant.objects.all().filter(team_name=st, tournament_name=s)

    for i in participant_list:
        obj = get_object_or_404(Tournaments_participant, acc_email=i.acc_email, tournament_name=s)
        obj.delete()
    return redirect('../../')

def remove_judge(request, s, st):
    obj = get_object_or_404(Tournaments_participant, acc_email=Accounts.objects.all().filter(name=st)[0].email, tournament_name=s)
    obj.delete()

    return redirect('../../')

def leave_tournament(request, s1, s):
    obj = get_object_or_404(Tournaments_school, school_name=s1, tournament_name=s)
    obj.delete()

    l = Tournaments_participant.objects.all().filter(tournament_name=s, school_name=s1)

    for a in l:
        a.delete()

    return redirect('../../../')

def tournament_landing(request, s):

    # files = [[x.doc_name, x.doc.url] for x in documents.objects.all().filter(tournament_name=s)]
    files = []
    user = None
    host = False
    try:
        tournament = Tournament_list.objects.all().filter(name=s)[0]
    except:
        return HttpResponseRedirect('/')


    if request.user.is_authenticated:
        user = Accounts.objects.all().filter(email=request.user)[0]
        if user.coach == True and user.school == tournament.host:
            host = True
            user = user.name

    description = tournament.description
    description = description.split('\n')

    action = request.POST.get('action')
    if action == "sub":
        description = request.POST.get('tournament_description')
        tournament.description = description
        tournament.save()
        return HttpResponseRedirect('/tournament-landing/'+s+'/')

    context = {
        "tournament": s,
        "description": description,
        "l": [x+1 for x in range(int(tournament.n_rounds))],
        "files":files,
        "user":user,
        "host":host,
        "show_speaker_points": tournament.speaker_point_show,
    }
    print (tournament.speaker_point_show)
    return render(request, 'tournament_landing_page.html', context)

def tournament_entries(request, s):
    l = [x for x in range(1,int(Tournament_list.objects.all().filter(name=s)[0].n_rounds)+1)]

    schools_qset = Tournaments_school.objects.all().filter(tournament_name=s)
    schools = []
    for i in schools_qset:
        schools.append(i.school_name)

    #judges
    judges = []
    for x in Tournaments_participant.objects.all().filter(tournament_name=s, team_name="N/A"):
        judges.append([x.school_name, Accounts.objects.all().filter(email=x.acc_email)[0].name])

    temp = []
    for i in schools:
        c = 0
        while c<len(judges):
            if judges[c][0] == i:
                temp.append(judges[c])
            c += 1
    judges = temp

    condition1 = False
    judges2 = []
    if len(judges)>9:
        condition1 = True
        for i in range(int(len(judges)/2)):
            judges2.append(judges[i])
            judges[i] = 0

        while 0 in judges:
            judges.remove(0)

    #teams
    teams = []
    for x in Tournaments_team.objects.all().filter(tournament_name=s):
        students = ""
        for i in Tournaments_participant.objects.all().filter(tournament_name=s, team_name=x.team_name, school_name=x.school_name):
            students += Accounts.objects.all().filter(email=i.acc_email)[0].name + ", "
        students=students[:-2]
        teams.append([x.school_name, x.team_name, students])

    temp = []
    for i in schools:
        c = 0
        while c<len(teams):
            if teams[c][0] == i:
                temp.append(teams[c])
            c += 1
    teams = temp

    condition = False
    teams2 = []
    if len(teams)>9:
        condition = True
        for i in range(int(len(teams)/2)):
            teams2.append(teams[i])
            teams[i] = 0

        while 0 in teams:
            teams.remove(0)

    user = None
    if request.user.is_authenticated:
        user = Accounts.objects.all().filter(email=request.user)[0].name

    tournament = Tournament_list.objects.all().filter(name=s)[0]

    context = {
        "s": s,
        "teams": teams,
        "teams2": teams2,
        "condition": condition,
        "condition1": condition1,
        "judges": judges,
        "judges2":judges2,
        "l": l,
        "user":user,
        "show_speaker_points": tournament.speaker_point_show,
    }
    return render(request,'tournament_entries_page.html',context)


def tournament_administration_base(request, s):

    #------------------------------------------------preliminary pairings--------------------------------------------------------------------

    Tournament = Tournament_list.objects.all().filter(name=s)[0]
    if Tournament.start_date > datetime.date.today():
        return HttpResponseRedirect('/school-landing/')

    n = Tournament.n_rounds #number of rounds
    l = [i for i in range(1,int(n)+1)] #count

    action = request.POST.get('action') #value of button pressed

    message1 = ""
    message5 = ""
    message6 = ""
    error_message = ""
    mess = None


    break_round = Tournament.break_round
    break_list = {1:1, 2:2, 4:3, 8:4}
    l2 = [i+1 for i in range(break_list[int(break_round)])]


    # bround = int(break_round)
    # break_dict = {}
    # c = 1
    # while bround > 1:
    #     break_dict.update({c:break_list[bround]})
    #     bround //= 2
    #     c += 1
    #     if bround == 1:
    #         break
    # break_dict.update({c:"Finals"})
    # print (break_dict)
    # for i in range(len(l2)):
    #     l2[i] = break_dict[l2[i]]

    teams_qset = Tournaments_team.objects.all().filter(tournament_name=s)
    teams = []
    for f in teams_qset:
        teams.append(f)
    x = int(len(teams)/2)
    schools = [ [] for i in range(len(Tournaments_school.objects.all().filter(tournament_name=s)))]

    if len(Tournaments_participant.objects.all().filter(tournament_name=s, team_name = "N/A")) < x:
            mess = "Available judges are not sufficient"
    else:
        for i in range(1, int(n)+1):

            if action == str(i) and len(Result.objects.all().filter(tournament_name=s,round_no=i)) == 0:

                if i == 1 or len(Result.objects.all().filter(tournament_name=s,round_no=str(int(i)-1))) != 0 and Result.objects.all().filter(tournament_name=s,round_no=str(int(i)-1))[0].winner != "" and Result.objects.all().filter(tournament_name=s,round_no=i-1)[0].winner != None:
                    #------you may be able to remove this------------
                    teams = [f for f in Tournaments_team.objects.all().filter(tournament_name=s)]
                    x = int(len(teams))/2  # number of pairs
                    # -----------------------------------------------

                    schools = [ [] for x in range(len(Tournaments_school.objects.all().filter(tournament_name=s)))]
                    c = 0
                    count = []
                    for sc in Tournaments_school.objects.all().filter(tournament_name=s):

                        for f in teams:
                            if f.school_name == sc.school_name:
                                schools[c].append(f.team_name)
                        count.append(c)
                        c += 1

                    schools.sort(key=len)

                    while schools[0] == []:
                        schools.remove(schools[0])
                        count.remove(count[-1])

                    if Tournament.private == False:
                        majority = schools[-1]
                        if len(schools[-1]) == len(schools[-2]):
                            majority = []
                        else:
                            MajorityIndex = schools.index(majority)
                            count.remove(MajorityIndex)
                    else:
                        majority = []

                    bye = ""

                    # ------------------- for bye (this is ok)---------------------------------------
                    if x != int(x):
                        if len(majority)>0:
                            con = 0
                            while con < 30:
                                cond = True
                                bye = random.choice(majority)
                                rec = Result.objects.all().filter(tournament_name= s, team1= bye)
                                for xi in rec:
                                    if xi.team2 == None:
                                        cond = False
                                if cond == True:
                                    con = 30
                                con += 1

                            ind = schools.index(majority)
                            majority.remove(bye)
                        else:
                            con = 0
                            while con < 50:
                                cond = True
                                ran_school= random.choice(schools)
                                bye = random.choice(ran_school)
                                rec = Result.objects.all().filter(tournament_name= s, team1= bye)
                                for xi in rec:
                                    if xi.team2 == None:
                                        cond = False
                                if cond == True:
                                    con = 50
                                con += 1
                            ind = schools.index(ran_school)
                            schools[ind].remove(bye)
                            if len(schools[ind])<1:
                                schools.remove(ran_school)
                                count.remove(count[-1])
                        Result.objects.create(tournament_name= s, round_no= i, team1= bye, winner= bye)
                        print(bye)

                        obj = Team_statistics.objects.get(tournament_name= s, team_name= bye)
                        obj.wins = str(int(obj.wins) + 1)
                        obj.save()

                    #-------------------------------------------------------------------------------

                    if i > 1 and len(teams) > 10:  #new pairing system
                        team_profiles = [[x.team_name, int(x.wins)-int(x.losses)] for x in Team_statistics.objects.all().filter(tournament_name=s)]
                        for ix in team_profiles:
                            if ix[0] == bye:
                                team_profiles.remove(ix)
                        team_profiles.sort(key = lambda x: x[1])
                        team_profiles.reverse()
                        print (team_profiles)
                        pairings = [[team_profiles[count][0],team_profiles[int(x)+count][0]] for count in range (int(x))]
                    # it ends here
                    else:
                    #traditional way
                        x = int(x)
                        pairings = []
                        if Tournament.private == False:
                            for k in range(x): #for every pair
                                schools.sort(key=len)

                                while schools[0] == []:
                                    schools.remove(schools[0])
                                    count.remove(count[-1])

                                if majority == []:
                                    if len(schools[-1]) > len(schools[-2]):
                                        majority = schools[-1]
                                        count.remove(schools.index(majority))
                                else:
                                    if schools[-1] != majority:
                                        if len(schools[-1]) > len(majority):
                                            majority = schools[-1]
                                        else:
                                            count.append(count[-1]+1)
                                            majority = []
                                    elif len(schools[-2]) == len(majority):
                                        count.append(count[-1]+1)
                                        majority = []

                                temp_count = count[:]

                                if len(majority)>0:
                                    team1 = random.choice(majority)
                                    majority.remove(team1)
                                else:
                                    chosen_school_index = random.choice(temp_count)
                                    del temp_count[temp_count[chosen_school_index]]
                                    team1 = random.choice(schools[chosen_school_index])
                                    schools[chosen_school_index].remove(team1)

                                # for team 2\
                                chosen_school_index1 = random.choice(temp_count)
                                team2 = random.choice(schools[chosen_school_index1])
                                cu = 0
                                while len(Result.objects.all().filter(tournament_name= s, team1= team1, team2= team2)) != 0 or len(Result.objects.all().filter(tournament_name= s, team1= team2, team2= team1)) != 0:
                                    chosen_school_index1 = random.choice(temp_count)
                                    team2 = random.choice(schools[chosen_school_index1])
                                    cu += 1
                                    if cu == 49:
                                        message1 = "Insufficient students so some pairings may overlap"
                                        break
                                schools[chosen_school_index1].remove(team2)
                                pairings.append([team1, team2])

                        else:
                            for k in range(x): #for every pair
                                print("private")
                                team1 = random.choice(teams)
                                teams.remove(team1)
                                team1 = team1.team_name
                                team2 = random.choice(teams)
                                cu = 0
                                while len(Result.objects.all().filter(tournament_name= s, team1= team1, team2= team2)) != 0 or len(Result.objects.all().filter(tournament_name= s, team1= team2, team2= team1)) != 0:
                                    team2 = random.choice(teams)
                                    cu += 1
                                    if cu == 49:
                                        message1 = "Insufficient students so some pairings may overlap"
                                        break
                                teams.remove(team2)
                                team2 = team2.team_name
                                pairings.append([team1, team2])

                    judges_qset = Tournaments_participant.objects.all().filter(tournament_name=s, team_name="N/A")
                    judges = []
                    for f in judges_qset:
                        judges.append(f)

                    for k in pairings:
                        mess = None
                        judge = ""

                        if Tournament.only_school_judge == True or len(schools) == 2 or Tournament.private == True:
                            judge = random.choice(judges)
                        else:
                            for ju in judges:
                                if ju.school_name != Tournaments_team.objects.all().filter(tournament_name=s, team_name= k[0])[0].school_name and ju.school_name != Tournaments_team.objects.all().filter(tournament_name=s, team_name= k[1])[0].school_name:
                                    judge = ju
                                    break
                        if judge == "":
                            mess = "Insuffient Judges"
                            break
                        else:
                            Result.objects.create(tournament_name= s, round_no= i,team1= k[0],
                            team2= k[1], judge= Accounts.objects.all().filter(email = judge.acc_email)[0].name)
                            judges.remove(judge)
                else:
                    message1 = "All decisions for the past rounds have not been made yet"


            elif action == str(i) and len(Result.objects.all().filter(tournament_name=s,round_no=i)) != 0:
                message1 = "Pairings have been created already"

        #---------------------------------------------------------------------------------------------------------------------------------


        message5=""
        message6=""
        if action == "B"+str(1) and len(Result.objects.all().filter(tournament_name=s,round_no="B"+str(1))) == 0:

            judges_qset = Tournaments_participant.objects.all().filter(tournament_name=s, team_name="N/A")
            judges = []
            for f in judges_qset:
                judges.append(f)

            break_round_2 = int(break_round)*2
            team_stats = Team_statistics.objects.all().filter(tournament_name=s)
            teams = []

            for x in team_stats:
                teams.append([x.wins,x.team_name])

            teams = sorted(teams,key=lambda x: x[0])
            teams.reverse()
            #after descending sort
            selected_teams = []
            i = 0
            while i <= len(teams)-2:
                if teams[i][0] != teams[i+1][0]:
                    selected_teams.append(teams[i][1])
                else:
                    same_wins = []
                    while teams[i][0] == teams[i+1][0]:
                        same_wins.append(teams[i][1])
                        i += 1
                        if len(teams)-1 <= i:
                            break
                    same_wins.append(teams[i][1])
                    average_speaker_points = []

                    remaing_needed = break_round_2-len(selected_teams)
                    if len(same_wins) < remaing_needed:
                        for x in same_wins:
                            selected_teams.append(x)
                    else:
                        for x in same_wins:
                            participants_qset = Tournaments_participant.objects.all().filter(tournament_name=s, team_name=x)
                            speaker_points = 0
                            for y in participants_qset:
                                speaker_points_per_round = Speaker_points.objects.all().filter(tournament_name=s, participant=y.acc_email)
                                for z in speaker_points_per_round:
                                    speaker_points += float(z.points)

                            num_r = int(Team_statistics.objects.all().filter(tournament_name=s, team_name=x)[0].wins) + int(Team_statistics.objects.all().filter(tournament_name=s, team_name=x)[0].losses)
                            av_sp = speaker_points/num_r
                            average_speaker_points.append([av_sp,x])

                        average_speaker_points = sorted(average_speaker_points,key=lambda x: x[0])
                        average_speaker_points.reverse()
                        c= 0
                        while c<remaing_needed:
                            selected_teams.append(average_speaker_points[c][1])
                            c += 1

                if len(selected_teams) == break_round_2:
                    break
                i += 1

            selected = selected_teams

            for i in range(int(break_round)):
                team1 = random.choice(selected)
                selected.remove(team1)
                team2 = random.choice(selected)
                selected.remove(team2)

                judge = ""

                # if Tournament.only_school_judge == True or len(schools) == 2 or Tournament.private == True:
                judge = random.choice(judges)
                # else:
                #     for ju in judges:
                #         if ju.school_name != Tournaments_team.objects.all().filter(tournament_name=s, team_name= k[0])[0].school_name and ju.school_name != Tournaments_team.objects.all().filter(tournament_name=s, team_name= k[1])[0].school_name:
                #             judge = ju
                #             break
                # if judge == "":
                #     mess = "Insuffient Judges"
                #     break
                # else:
                Result.objects.create(tournament_name= s, round_no= "B"+str(1),team1= team1,
                    team2= team2, judge= Accounts.objects.all().filter(email = judge.acc_email)[0].name)
                judges.remove(judge)

        elif action == "B"+str(i) and len(Result.objects.all().filter(tournament_name=s,round_no="B"+str(1))) != 0:
            message6 = "Pairings have been created already"

        error_message = ""
        for i in range(2, int(break_round)+1):
            if action == "B"+str(i) and len(Result.objects.all().filter(tournament_name=s,round_no="B"+str(i))) == 0:
                judges_qset = Tournaments_participant.objects.all().filter(tournament_name=s, team_name="N/A")
                judges = []
                for f in judges_qset:
                    judges.append(f)

                P_Round_Result = Result.objects.all().filter(tournament_name=s,round_no="B"+str(i-1))
                winners = []
                for x in P_Round_Result:
                    winners.append(x.winner)

                pairs = []
                for j in range (len(winners)//2):
                    team1 = winners[0]
                    winners.remove(team1)
                    team2 = winners[0]
                    winners.remove(team2)

                    judge = ""

                    # if Tournament.only_school_judge == True or len(schools) == 2 or Tournament.private == True:
                    judge = random.choice(judges)
                    # else:
                    #     for ju in judges:
                    #         if ju.school_name != Tournaments_team.objects.all().filter(tournament_name=s, team_name= k[0])[0].school_name and ju.school_name != Tournaments_team.objects.all().filter(tournament_name=s, team_name= k[1])[0].school_name:
                    #             judge = ju
                    #             break
                    # if judge == "":
                    #     mess = "Insuffient Judges"
                    #     break
                    # else:
                    Result.objects.create(tournament_name=s, round_no="B"+str(i), team1=team1, team2=team2, judge=Accounts.objects.all().filter(email = judge.acc_email)[0].name)
                    judges.remove(judge)
            elif action == "B"+str(i) and len(Result.objects.all().filter(tournament_name=s,round_no="B"+str(i))) != 0:
                error_message = "Pairings have been created already"

    context = {
        "message1":message1,
        "message5":message5,
        "message6":message6,
        "error_message":error_message,
        "mess":mess,
        "l": l,
        "l2":l2,
        "user": Accounts.objects.all().filter(email=request.user)[0].name,
        "started":True,
    }


    return render(request, "tournament_administration_base.html", context)




def tournament_pairings(request, s, r):
    debates = Result.objects.all().filter(tournament_name=s, round_no=r)
    pairings = []
    bye_teams = []
    for debate in debates:
        if debate.team1 and debate.team2:
            pairings.append([(debate.team1),(debate.team2),(debate.judge)])
        else:
            if not(debate.team1):
                bye_teams.append(debate.team2)
            if not(debate.team2):
                bye_teams.append(debate.team1)

    n_rounds = Tournament_list.objects.all().filter(name=s)[0].n_rounds

    l = []

    for x in range(int(n_rounds)):
        l.append(x+1)

    user = None
    if request.user.is_authenticated:
        user = Accounts.objects.all().filter(email=request.user)[0].name

    tournament = Tournament_list.objects.all().filter(name=s)[0]
    context = {
        "s": s,
        "l": l,
        "r": r,
        "pairings": pairings,
        "bye_teams": bye_teams,
        "user":user,
        "show_speaker_points": tournament.speaker_point_show,
    }

    return render(request, "tournament_pairings.html", context)



def results(request, s, r):
    #s ==> tournament_name
    #r ==> round number
    results1 = Result.objects.all().filter(tournament_name=s, round_no=r)

    bye_teams = ""
    results = []
    for result in results1:
        winner = ""
        if result.winner:
            if result.winner == result.team1:
                winner = "Team 1"
            elif result.winner == result.team2:
                winner = "Team 2"
            results.append([result.team1, result.team2, result.judge, winner])
        elif not result.team2:
            bye_teams = result.team1

    #o = Result.objects.all().filter(tournament_name=s, round_no=r)

    n_rounds = Tournament_list.objects.all().filter(name=s)[0].n_rounds

    l = []

    for x in range(int(n_rounds)):
        l.append(x+1)

    user = None
    if request.user.is_authenticated:
        user = Accounts.objects.all().filter(email=request.user)[0].name

    context = {
        "l": l,
        "s": s,
        "results": results,
        "r": r,
        "user":user,
        "bye_teams": bye_teams,
        "show_speaker_points": Tournament_list.objects.all().filter(name=s)[0].speaker_point_show,
     }

    return render(request, "tournament_results.html", context)


def team_result(request,s,t_name):

    team_p = Tournaments_participant.objects.all().filter(tournament_name= s, team_name=t_name)
    tournament_team_data = []
    for x in team_p:
        tournament_team_data.append(Speaker_points.objects.all().filter(tournament_name=s, participant=Accounts.objects.all().filter(email=x.acc_email)[0].email)) #round number
    #for each participant, this array stores all the instances(querysets) in that tournament where their name occurs
    #need to see what happens in the case of a bye
    indivisual_speaker_points = {}
    for member in tournament_team_data:
        for each_round in member:
            member_name = Accounts.objects.all().filter(email=each_round.participant)[0].name
            if member_name not in indivisual_speaker_points:
                indivisual_speaker_points[member_name] = [[each_round.round_no, each_round.points]]
            elif member_name in indivisual_speaker_points:
                 indivisual_speaker_points[member_name] = indivisual_speaker_points[member_name] + [[each_round.round_no, each_round.points]]

    temp = []
    for x in indivisual_speaker_points:
        temp.append([x,indivisual_speaker_points[x]])
    indivisual_speaker_points = temp

    team_round_info1 = []
    try:
        team_rounds1 = Result.objects.all().filter(tournament_name=s, team1=t_name)

        for a in team_rounds1:
            if not(a.team2):
                team_round_info1.append([a.round_no, "Bye", "W", a.judge])
            elif not(a.team1):
                team_round_info1.append([a.round_no, "Bye", "W", a.judge])
            else:
                if a.winner == t_name:
                    team_round_info1.append([a.round_no, a.team2, "W", a.judge])
                else:
                    team_round_info1.append([a.round_no, a.team2, "L", a.judge])

    except:
        pass

    team_round_info2 = []
    try:
        team_rounds2 = Result.objects.all().filter(tournament_name=s, team2=t_name)
        for a in team_rounds2:
            if not(a.team2):
                team_round_info2.append([a.round_no, "Bye", "W", a.judge])
            elif not(a.team1):
                team_round_info2.append([a.round_no, "Bye", "W", a.judge])
            else:
                if a.winner == t_name:
                    team_round_info2.append([a.round_no, a.team1, "W", a.judge])
                else:
                    team_round_info2.append([a.round_no, a.team1, "L", a.judge])

    except:
        pass

    if team_round_info1 and team_round_info2:
        team_round_info = team_round_info1 + team_round_info2
        team_round_info.sort(key = lambda team_round_info: team_round_info[0])
        context = {"team_result": team_round_info}
    elif team_round_info1:
        context = {"team_result": team_round_info1}
    elif team_round_info2:
        context = {"team_result": team_round_info2}

    context.update({
        "indivisual_speaker_points": indivisual_speaker_points,
        "show_speaker_points": Tournament_list.objects.all().filter(name=s)[0].speaker_point_show,
        })

    return render(request, "team_result.html", context)

def tournament_bracket(request, s):
    break_rounds = Tournament_list.objects.all().filter(name=s)[0].break_round
    #1 ==> B1, #2 ==> B2, #4 ==> B3, #8 ==> B4
    all_round_results = Result.objects.all().filter(tournament_name=s)
    break_round_results = {}

    break_round_no = ''
    if int(break_rounds) == 8:
        break_round_no = "B4"
    elif int(break_rounds) == 4:
        break_round_no = "B3"
    elif int(break_rounds) == 2:
        break_round_no = "B2"
    elif int(break_rounds) == 1:
        break_round_no = "B1"

    winner = Result.objects.all().filter(tournament_name=s, round_no=break_round_no)
    if len(winner) == 0:
        winner = None
    else:
        winner = winner[0].winner

    for i in range(1,int(break_rounds)+1):
       break_round_results['B'+str(i)] = []

    for break_round in all_round_results:
        if str(break_round.round_no)[0] == 'B':
            break_round_results[break_round.round_no] = break_round_results[break_round.round_no] + [[break_round.team1, break_round.team2, break_round.judge]]

    temp = []
    for x in break_round_results:
        if break_round_results[x] != []:
            temp.append([x,break_round_results[x]])
        else:
            temp.append([x,None])
    break_round_results = temp

    #counter = [i for i in range ()]
    context = {
        's':s,
        "break_round": break_rounds,
        "break_round_results": break_round_results,
        "winner":winner,
        # "counter":
    }

    return render(request, "tournament_bracket.html", context)

def final_result(request, s):
    user = None
    if request.user.is_authenticated:
        user = Accounts.objects.all().filter(email=request.user)[0].name

    context = {
        "s":s,
        "l": [x+1 for x in range(int(Tournament_list.objects.all().filter(name=s)[0].n_rounds))],
        "user":user,
        "show_speaker_points": Tournament_list.objects.all().filter(name=s)[0].speaker_point_show,
    }

    stats_qset = Team_statistics.objects.all().filter(tournament_name= s)
    stats = []

    for x in stats_qset:
        stats.append([x.team_name, x.wins, x.losses])

    stats = sorted(stats,key=lambda x: x[1])
    stats.reverse()
    context.update({"stats":stats})

    return render(request, "tournament_final_result.html", context)



def speaker_point_ranking(request, s):

    user = None
    if request.user.is_authenticated:
        user = Accounts.objects.all().filter(email=request.user)[0].name
    context = {
        "user":user,
        "s":s,
        "l":[x+1 for x in range(int(Tournament_list.objects.all().filter(name=s)[0].n_rounds))],
    }
    message = ""

    last_round = Tournament_list.objects.all().filter(name=s)[0].n_rounds
    last_r = Result.objects.all().filter(tournament_name=s, round_no=last_round)
    if len(last_r)>0:
        for i in last_r:
            if i.winner == None or i.winner =="":
                message = "Not all results are out yet"

        if message == "":
            participants_qset1 = Tournaments_participant.objects.all().filter(tournament_name=s)
            participants_qset = []
            for i in participants_qset1:
                if i.team_name != "N/A":
                    participants_qset.append(i)

            average_speaker_points = []
            zero_p = []

            for y in participants_qset:
                speaker_points = 0

                speaker_points_per_round_qset = Speaker_points.objects.all().filter(tournament_name=s, participant=y.acc_email)
                speaker_points_per_round = []
                num_r = 0
                for i in speaker_points_per_round_qset:
                    if i.round_no[0] != "B":
                        speaker_points += float(i.points)
                        num_r += 1

                  #for loop in the last_round variable which gives the number of prelim rounds in that tournament
                speaker_points_per_round_this_participant = []
                try:
                    for k in range(1, int(last_round)+1):
                        speaker_points_per_round_this_participant.append(Speaker_points.objects.all().filter(tournament_name=s, participant=y.acc_email, round_no=k)[0].points)
                #to seperate the speaker points of each debater and have in the format like [[4,5,6], [7,8,9]] need the following line
                except:
                    pass

                if num_r>0:
                    av_sp = speaker_points/num_r
                    av_sp = '%s' % float('%.3g' % av_sp)
                    average_speaker_points.append([Accounts.objects.all().filter(email=y.acc_email)[0].name, y.team_name, Accounts.objects.all().filter(email=y.acc_email)[0].school,speaker_points_per_round_this_participant, float(av_sp)])
                else:
                    zero_p.append(Accounts.objects.all().filter(email=y.acc_email)[0].name)

            if len(average_speaker_points) > 0:
                average_speaker_points = sorted(average_speaker_points, key= lambda x: x[4])
                average_speaker_points.reverse()
                context.update({"ranking":average_speaker_points})
            context.update({"zero_p":zero_p,"num_rounds":[q+1 for q in range (num_r)]})

    else:
        message = "Not all results are out yet"

    context.update({"message":message})

    return render(request, "best_speaker.html", context)

