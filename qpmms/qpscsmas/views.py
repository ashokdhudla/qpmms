from django.shortcuts import render

from django.http import HttpResponse
from models import *
from django.db.models import Q
from django.shortcuts import render_to_response, HttpResponseRedirect
from datetime import *
from forms import *
from django.shortcuts import render, render_to_response, RequestContext, HttpResponseRedirect, HttpResponse
from django.core.context_processors import csrf
from .models import *
from forms import *
from django.template import RequestContext
from django.core.context_processors import csrf
from django.core.paginator import *
import xlrd
from qpmms import *
from django.template.loader import render_to_string
import datetime
import time
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.pagesizes import landscape
from reportlab.platypus import Image
import hashlib
# import datetime
import random
from datetime import datetime, timedelta, date
from django.conf import settings as conf_settings
import os
from django.core.mail import send_mail
from django.template.loader import get_template
from django.template import Context, RequestContext
from django.core.mail import send_mail,  EmailMultiAlternatives
from django.contrib import messages
from apscheduler.schedulers.background import BackgroundScheduler
from django.utils.datastructures import MultiValueDictKeyError

def user_login_required(f):
		def wrap(request, *args, **kwargs):
				#this check the session if userid key exist, if not it will redirect to login page
				if 'user' not in request.session.keys():
						return HttpResponseRedirect("/login")
				return f(request, *args, **kwargs)
		wrap.__doc__=f.__doc__
		wrap.__name__=f.__name__
		return wrap


def login(request):

	form = UserForm(request.POST)
	content = {}
	content['form'] = form

	content.update(csrf(request))

	if request.method == "POST":
		print "post method"
		username = request.POST['userid']
		# password = request.POST['password']
		password = request.POST['password']
		# password = hashpass(in_password)
		user_list = qpusers.objects.filter(user_id=username, password1=password)
		if(user_list):
			userobj = user_list[0]
			s=userlogin(username = userobj.username, userid = userobj.user_id, role = userobj.role, logintime = datetime.now())
			s.save()   
			request.session['user'] = userobj
			# return HttpResponse("This is Admin Home Page")
			return HttpResponseRedirect("/index")
		else:
			content['err_msg'] = 'Invalid username or password'
			# return HttpResponse("Login Failed")
		return render_to_response('login.html', content, context_instance=RequestContext(request))

	return render_to_response('login.html', content, context_instance=RequestContext(request))

@user_login_required
def dashboard(request):
	content = {}
	content.update(csrf(request))
	user = request.session['user']
	content={'username' :user.username,'email_id':user.email_id}
	return render_to_response('dashboard2.html', content, context_instance=RequestContext(request))

@user_login_required
def index(request):
	content = {}
	content.update(csrf(request))
	user = request.session['user']
	content={'username' :user.username,'email_id':user.email_id}
	if str(user.role) == 'Admin' or str(user.role) == 'admin':
		return render_to_response('dashboard2.html', content, context_instance=RequestContext(request))
	if str(user.role) == 'Master Admin' or str(user.role) == 'master admin' or 'Master admin' or 'Master':
		return render_to_response(['madmin_dashboard.html','base.html'], content, context_instance=RequestContext(request))
	else:
		return render_to_response(['login.html','base.html'], content, context_instance=RequestContext(request))
	
def logout(request):
	user = request.session['user']
	s=userlogout(username = user.username, userid = user.user_id, role = user.role, logouttime = datetime.now())            
	s.save()
	session_keys = request.session.keys()
	form = UserForm(request.POST)
	for key in session_keys:
		del request.session[key]
	# content.update(csrf(request))
	return render_to_response('login.html', {'form': form}, context_instance=RequestContext(request))

def registrationAdmin(request):
	# user = request.session['user']
	# content={'username' :user.username,'email_id':user.email_id}
	form = qpusersForm(request.POST or None)
	if form.is_valid():
		save_it = form.save(commit=False)
		save_it.save()
	return render_to_response("registration_admin.html",locals(),context_instance=RequestContext(request))

def adminList(request):
	url = '/adminList/'
	a_list = []
	admins = qpusers.objects.all().order_by('-id')
	userobj = request.session['user']
	content = {'username' :userobj.username,'email_id':userobj.email_id,'url':url,'qpusers':admins}
	return render_to_response('masterAdmin/adminList.html',content, context_instance=RequestContext(request))

def registerEmp(request):
	form = employee_detailsForm(request.POST or None)
	if form.is_valid():
		save_it = form.save(commit=False)
		save_it.save()
	return render_to_response("registeremp.html",locals(),context_instance=RequestContext(request))

def employeesList(request):
	url = '/viewemp/'
	employees = employee_details.objects.all()
	# for i in guests:
	#     g_list.append(i.name)
	#     members = member.objects.get(id=i.member_id)
	#     g_list.append(members.first_name_1)
	userobj = request.session['user']
	content = {'username' :userobj.username,'email_id':userobj.email_id,'url':url,'qpusers':employees}
	return render_to_response('viewemp.html',content, context_instance=RequestContext(request))
	# return HttpResponse("Employee List")

def registerCompany(request):

	form = associative_companyForm(request.POST or None)
	if form.is_valid():
		save_it = form.save(commit=False)
		save_it.save()
	return render_to_response("register_company.html",locals(),context_instance=RequestContext(request))

def viewCompanies(request):
	url = '/viewcom/'
	companies = associative_company.objects.all()
	# for i in guests:
	#     g_list.append(i.name)
	#     members = member.objects.get(id=i.member_id)
	#     g_list.append(members.first_name_1)
	userobj = request.session['user']
	content = {'username' :userobj.username,'email_id':userobj.email_id,'role' :userobj.role, 'url':url,'companies':companies}
	return render_to_response('viewcom.html',content, context_instance=RequestContext(request))

def registerDevice(request):
	form = device_infoForm(request.POST or None)
	if form.is_valid():
		save_it = form.save(commit=False)
		save_it.save()
	return render_to_response("register_device.html",locals(),context_instance=RequestContext(request))

def viewDevice(request):
	url = '/viewdev/'
	devices = device_info.objects.all()
	# for i in guests:
	#     g_list.append(i.name)
	#     members = member.objects.get(id=i.member_id)
	#     g_list.append(members.first_name_1)
	userobj = request.session['user']
	content = {'username' :userobj.username,'email_id':userobj.email_id,'url':url,'devices':devices}
	return render_to_response('viewdev.html',content, context_instance=RequestContext(request))

def mealsConfiguration(request):
	form = device_infoForm(request.POST or None)
	if form.is_valid():
		save_it = form.save(commit=False)
		save_it.save()
	return render_to_response("register_device.html",locals(),context_instance=RequestContext(request))
def MealsReports(request):
	content = {}
	alist = []
	blist = []
	if request.method == "POST":
		fromdate = request.POST['fromdate']
		todate =  request.POST['todate']
		employees = employee_details.objects.all()
		for employee in employees:
			# adict = {}
			# atuple = ()
			breakfasts = emp_breakfast.objects.filter(rfidcardno = employee.rfidcardno)
			lunch = emp_lunch.objects.filter(rfidcardno = employee.rfidcardno)
			dinners = emp_dinner.objects.filter(rfidcardno = employee.rfidcardno)
			bf_count = len(breakfasts)
			l_count = len(lunch)
			d_count = len(dinners)
			rfid = employee.rfidcardno
			emp_id =employee.employee_id
			emp_name = employee.first_name
			com = employee.company.company_name 
			blist = employee_details.objects.raw("select a.employee_id,a.first_name, c.breakfast_count, b.lunch_count, d.dinner_count from qpscsmas_employee_details a,qpscsmas_emp_lunch b,qpscsmas_emp_breakfast c, qpscsmas_emp_dinner d where a.rfidcardno = 'rfid' and b.rfidcardno ='rfid' and c.rfidcardno ='rfid' and d.rfidcardno ='rfid'"),
			# adict = {'emp_id' :emp_id,'emp_name',emp_name,'com':com,'bf_count':bf_count,'l_count':l_count,'d_count' :d_count }
			# atuple = (emp_id,emp_name,com,bf_count,l_count,d_count)
			alist.append(blist)
		print alist
		content = {'lists' :alist }
	# return HttpResponse("this is reports")
	return render_to_response("mealreports.html",content, context_instance=RequestContext(request))
def AccommodationReport(request):
	form = emp_accommodationForm(request.POST or None)
 	if form.is_valid():
  		save_it = form.save(commit=False)
  		save_it.save()
 	return render_to_response("accommodation.html",locals(),context_instance=RequestContext(request))
def Acmd_detailreports(request):
 	content = {}
 	content.update(csrf(request))
	return render_to_response("chart.html", content, context_instance=RequestContext(request))

def priceconfigure(request):
	content = {}
	content.update(csrf(request))
	return render_to_response("priceconfigure.html",content, context_instance=RequestContext(request))

def mtconfigure(request):
	form = meal_timingForm(request.POST or None)
	if form.is_valid():
		save_it = form.save(commit=False)
		save_it.save()
	return render_to_response("mtconfigure.html",locals(), context_instance=RequestContext(request))
def detailedmealsreport(request):
	content = {}
	content.update(csrf(request))
	return render_to_response("detailedmealsreport.html",content, context_instance=RequestContext(request))

def custom_404(request):
	return render_to_response("404.html",RequestContext(request))


