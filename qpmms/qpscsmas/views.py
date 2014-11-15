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
from django.db import connection
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
import socket
import datetime
# from easy_pdf.views import PDFTemplateView


def user_login_required(f):
		def wrap(request, *args, **kwargs):
				print "decorater is calling"
				#this check the session if userid key exist, if not it will redirect to login page
				if 'user' not in request.session.keys():
						return HttpResponseRedirect("/")
				return f(request, *args, **kwargs)
		wrap.__doc__=f.__doc__
		wrap.__name__=f.__name__
		return wrap

def login(request):
	print "login"

	form = UserForm(request.POST)
	content = {}
	content['form'] = form
	content.update(csrf(request))
	if 'user' in request.session.keys():
		return HttpResponseRedirect("/index")

	if request.method == "POST":
		print "post method"
		username = request.POST['userid']
		# password = request.POST['password']
		password = request.POST['password']
		# password = hashpass(in_password)
		user_list = qpusers.objects.filter(user_id=username, password1=password)
		if(user_list):
			userobj = user_list[0]
			s=userlogin(username = userobj.username, userid = userobj.user_id, role = userobj.role, logintime = datetime.datetime.now())
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
	print "Dash board is calling"
	content = {}
	y = connection.cursor()
	y.execute("select count(rfidcardno) from qpscsmas_emp_entry where ip_addr='49.205.74.257'")
	r1 = y.fetchone()[0]
	y.execute("select count(rfidcardno) from qpscsmas_emp_exit where ip_addr='49.205.74.300'")
	r2 = y.fetchone()[0]
	z = r1-r2
	# print "no.of people in halul",z
	y.execute("select count(empid) from qpscsmas_emp_entry where ip_addr='49.205.74.258'")
	r3 = y.fetchone()[0]
	y.execute("select count(empid) from qpscsmas_emp_exit where ip_addr='49.205.74.301'")
	r4= y.fetchone()[0]
	z1 =r3-r4
	# print "no.of people in ps1",z1
	y.execute("select count(empid) from qpscsmas_emp_entry where ip_addr='49.205.74.259'")
	r5 = y.fetchone()[0]
	y.execute("select count(empid) from qpscsmas_emp_exit where ip_addr='49.205.74.302'")
	r6= y.fetchone()[0]
	z2 =r5-r6
	# print "no.of people in ps2",z2
	content.update(csrf(request))
	user = request.session['user']
	# content['halul']=z
	content={'halul':z,'ps1' :z1,'ps2' :z2,'username' :user.username,'email_id':user.email_id}
	return render_to_response('dashboard2.html', content, context_instance=RequestContext(request))
	# content = {}
	# content.update(csrf(request))
	# user = request.session['user']
	# content={'username' :user.username,'email_id':user.email_id}
	# return render_to_response('dashboard2.html', content, context_instance=RequestContext(request))

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
	print "logout"
	print type(request)
	user = request.session['user']
	s=userlogout(username = user.username, userid = user.user_id, role = user.role, logouttime = datetime.datetime.now())            
	s.save()
	session_keys = request.session.keys()
	form = UserForm(request.POST)
	for key in session_keys:
		print "del"
		del request.session[key]
	# content.update(csrf(request))
	return HttpResponseRedirect('/')
	# return render_to_response('login.html', {'form': form}, context_instance=RequestContext(request))
@user_login_required
def registrationAdmin(request):
	# user = request.session['user']
	# content={'username' :user.username,'email_id':user.email_id}
	form = qpusersForm(request.POST or None)
	if form.is_valid():
		save_it = form.save(commit=False)
		save_it.save()
		return HttpResponseRedirect('/adminList')
	return render_to_response("registration_admin.html",locals(),context_instance=RequestContext(request))

@user_login_required
def adminList(request):
	url = '/adminList/'
	a_list = []
	admins = qpusers.objects.all().order_by('-id')
	userobj = request.session['user']
	content = {'username' :userobj.username,'email_id':userobj.email_id,'url':url,'qpusers':admins}
	return render_to_response('masterAdmin/adminList.html',content, context_instance=RequestContext(request))
@user_login_required
def registerEmp(request):
	content = {}
	data = {}
	if request.method == 'GET':
		if 'eid' in request.GET:
			emp_id = request.GET['eid']
			emp_obj = employee_details.objects.get(id = emp_id)
			content['eid'] = emp_id
			data['first_name'] = emp_obj.first_name
			data['last_name'] = emp_obj.last_name
			data['employee_id'] = emp_obj.employee_id
			data['rfidcardno'] = emp_obj.rfidcardno
			data['gender'] = emp_obj.gender
			data['email_id'] = emp_obj.email_id
			data['contact_no'] = emp_obj.contact_no
			data['date_time'] = emp_obj.date_time
			data['employee_type'] = emp_obj.employee_type
			data['company'] = emp_obj.company
			data['department'] = emp_obj.department
			form = employee_detailsForm(initial=data)
		else:
			form = employee_detailsForm()
		content['form'] = form
	if request.method == "POST":
		print "enter into post"
		if 'eid' in request.POST:
			eid = request.POST['eid']
			if eid:
				emp_form = employee_detailsForm(request.POST or None)
				print emp_form.errors    
				if emp_form.is_valid():
					emp_obj = employee_details.objects.get(id=eid)
					emp_form = employee_detailsForm(request.POST, instance = emp_obj)
					emp_form.save()
					return HttpResponseRedirect('/viewemp/')
			if not eid:
				emp_form = employee_detailsForm(request.POST or None)
				print "enter into else part"
				if emp_form.is_valid():
					save_it = emp_form.save(commit=False)
					save_it.save()
					return HttpResponseRedirect('/viewemp/')
				return render_to_response("registeremp.html",locals(),context_instance=RequestContext(request))
	return render_to_response("registeremp.html",content,context_instance=RequestContext(request))
@user_login_required
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
@user_login_required
def registerCompany(request):

	form = associative_companyForm(request.POST or None)
	if form.is_valid():
		save_it = form.save(commit=False)
		save_it.save()
		return HttpResponseRedirect('/viewcom/')
	return render_to_response("register_company.html",locals(),context_instance=RequestContext(request))
@user_login_required
def viewCompanies(request):
	url = '/viewcom/'
	companies = associative_company.objects.all().order_by('-id')
	# for i in guests:
	#     g_list.append(i.name)
	#     members = member.objects.get(id=i.member_id)
	#     g_list.append(members.first_name_1)
	userobj = request.session['user']
	content = {'username' :userobj.username,'email_id':userobj.email_id,'role' :userobj.role, 'url':url,'companies':companies}
	return render_to_response('viewcom.html',content, context_instance=RequestContext(request))
@user_login_required
def registerDevice(request):
	content = {}
	data = {}
	if request.method == 'GET':
		data['device_id'] = socket.gethostbyname(socket.gethostname())
		data['Installation_Date'] = datetime.datetime.now()
		form = device_infoForm(initial=data)
		content['form'] = form
	if request.method == "POST":
		form = device_infoForm(request.POST or None)
		if form.is_valid():
			save_it = form.save(commit=False)
			save_it.save()
			return HttpResponseRedirect('/viewdev/')
		return render_to_response("register_device.html",locals(),context_instance=RequestContext(request))
	return render_to_response("register_device.html",content,context_instance=RequestContext(request))
@user_login_required
def viewDevice(request):
	url = '/viewdev/'
	devices = device_info.objects.all().order_by('-id')
	userobj = request.session['user']
	content = {'username' :userobj.username,'email_id':userobj.email_id,'url':url,'devices':devices}
	return render_to_response('viewdev.html',content, context_instance=RequestContext(request))
@user_login_required
def mealsConfiguration(request):
	form = device_infoForm(request.POST or None)
	if form.is_valid():
		save_it = form.save(commit=False)
		save_it.save()
	return render_to_response("register_device.html",locals(),context_instance=RequestContext(request))
@user_login_required
def MealsReports(request):
	content = {}
	bdict = {}
	alist = []
	totallist = []
	br_list = []
	l_list = []
	d_list = []
	final_set_list = []
	sumb = 0
	suml = 0
	sumd = 0
	if request.method == "POST":
		fromdate = request.POST['fromdate']
		todate =  request.POST['todate']
		if fromdate:
			br_obj_list=emp_breakfast.objects.filter(date_time__range=(fromdate, todate))
			l_obj_list = emp_lunch.objects.filter(date_time__range=(fromdate, todate))
			d_obj_list = emp_dinner.objects.filter(date_time__range=(fromdate, todate))
			for br_obj in br_obj_list: 
				br_list.append(br_obj.rfidcardno)
			final_set_list.extend(br_list)
			for l_obj in l_obj_list:
				l_list.append(l_obj.rfidcardno)
			final_set_list.extend(l_list)
			for d_obj in d_obj_list:
				d_list.append(d_obj.rfidcardno)
			final_set_list.extend(d_list)
			if final_set_list:
				for rfid in set(final_set_list):
					adict = {}
					bdict = {}
					bdict['emp_id'] = "Total"
					bdict['emp_name'] = " "
					bdict['com'] = " "
					fbf_count = br_list.count(rfid)
					fl_count  = l_list.count(rfid)
					dd_count  = d_list.count(rfid)
					emp = employee_details.objects.get(rfidcardno = rfid)
					adict['emp_id'] = emp.employee_id
					adict['emp_name'] = emp.first_name
					adict['com'] = emp.company.company_name
					adict['bf_count'] = fbf_count
					sumb += adict['bf_count']
					adict['l_count'] = fl_count
					suml += adict['l_count']
					adict['d_count'] = dd_count
					sumd += adict['d_count']
					alist.append(adict)
					bdict['bf_count'] = sumb
					bdict['l_count'] = suml
					bdict['d_count'] = sumd
		if len(bdict) != 0:
			alist.append(bdict)
			totallist.append(bdict)
		content = {'lists' :alist, 'total_bf' : 'Total BreakFast:' + str(sumb) ,  'total_l': 'Total Lunch :' + str(suml) ,'total_d':'Total Dinner :' +str(sumd)}
	return render_to_response("mealreports.html",content, context_instance=RequestContext(request))


@user_login_required
def priceconfigure(request):
	content = {}
	content.update(csrf(request))
	return render_to_response("priceconfigure.html",content, context_instance=RequestContext(request))

@user_login_required
def mtconfigure(request):
	form = meal_timingForm(request.POST or None)
	if form.is_valid():
		save_it = form.save(commit=False)
		save_it.save()
	return render_to_response("mtconfigure.html",locals(), context_instance=RequestContext(request))

@user_login_required
def detailedmealsreport(request):
	content={}
	list1 = []
	content.update(csrf(request))
	comp_list = []
	comp_list.append('Select')
	cmp_list = associative_company.objects.all()
	for i in cmp_list:
		comp_list.append(i)
	content['comp_list']=comp_list
	cursor = connection.cursor()
	listz = []
	if request.method == "POST":
		comp_name = request.POST['company']
		print comp_name
		if comp_name == 'Select':
			listz = employee_details.objects.all()
		else:
			cursor.execute("select id from qpscsmas_associative_company where company_name = %s",[comp_name])
			comp_id = cursor.fetchone()[0]
			listz = employee_details.objects.filter(company_id = comp_id)
			print comp_id
			sumb = 0
			suml = 0
			sumd = 0
			for i in listz:
			  adict = {}
			  bdict = {}
			  bdict['emp_id'] = "Total"
			  bdict['emp_name'] = " "
			  bdict['com'] = " "
			  cursor.execute("select employee_id,first_name,company_id from qpscsmas_employee_details where rfidcardno = %s",[i.rfidcardno])
			  x = cursor.fetchone()
			  adict['emp_id'] = x[0]
			  adict['emp_name'] = x[1]
			  adict['com'] = associative_company.objects.get(id=x[2])
			  cursor.execute("select count(breakfast_count) from qpscsmas_emp_breakfast where rfidcardno =%s",[i.rfidcardno])
			  adict['bf_count'] = cursor.fetchall()[0][0]
			  sumb += adict['bf_count']
			  cursor.execute("select count(lunch_count) from qpscsmas_emp_lunch where rfidcardno =%s",[i.rfidcardno])
			  adict['l_count'] = cursor.fetchall()[0][0]
			  suml += adict['l_count']
			  cursor.execute("select count(dinner_count) from qpscsmas_emp_dinner where rfidcardno =%s",[i.rfidcardno])
			  adict['d_count'] = cursor.fetchall()[0][0]
			  sumd += adict['d_count']
			  bdict['bf_count'] = sumb
			  bdict['l_count'] = suml
			  bdict['d_count'] = sumd
			  list1.append(adict)
		list1.append(bdict)
		content = { 'lists' : list1 }
	return render_to_response("detailedmealsreport.html",content,context_instance=RequestContext(request))

# @user_login_required
def MealsInvoice(request):
	content={}
	list1 = []
	content.update(csrf(request))
	comp_list = []
	comp_list.append('Select')
	cmp_list = associative_company.objects.all()
	for i in cmp_list:
		comp_list.append(i)
	content['comp_list']=comp_list
	cursor = connection.cursor()
	listz = []
	if request.method == "POST":
		comp_name = request.POST['company']
		print comp_name
		if comp_name == 'Select':
			listz = employee_details.objects.all()
		else:
			cursor.execute("select id from qpscsmas_associative_company where company_name = %s",[comp_name])
			comp_id = cursor.fetchone()[0]
			listz = employee_details.objects.filter(company_id = comp_id)
			print comp_id
			sumb = 0
			suml = 0
			sumd = 0
			for i in listz:
			  adict = {}
			  bdict = {}
			  bdict['emp_id'] = "Total"
			  bdict['emp_name'] = " "
			  bdict['com'] = " "
			  cursor.execute("select employee_id,first_name,company_id from qpscsmas_employee_details where rfidcardno = %s",[i.rfidcardno])
			  x = cursor.fetchone()
			  adict['emp_id'] = x[0]
			  adict['emp_name'] = x[1]
			  adict['com'] = associative_company.objects.get(id=x[2])
			  cursor.execute("select count(breakfast_count) from qpscsmas_emp_breakfast where rfidcardno =%s",[i.rfidcardno])
			  adict['bf_count'] = cursor.fetchall()[0][0]
			  sumb += adict['bf_count']
			  cursor.execute("select count(lunch_count) from qpscsmas_emp_lunch where rfidcardno =%s",[i.rfidcardno])
			  adict['l_count'] = cursor.fetchall()[0][0]
			  suml += adict['l_count']
			  cursor.execute("select count(dinner_count) from qpscsmas_emp_dinner where rfidcardno =%s",[i.rfidcardno])
			  adict['d_count'] = cursor.fetchall()[0][0]
			  sumd += adict['d_count']
			  bdict['bf_count'] = sumb
			  bdict['l_count'] = suml
			  bdict['d_count'] = sumd
			  list1.append(adict)
		list1.append(bdict)
		content = { 'lists' : list1 }
	return render_to_response("mealsinvoice.html",content,context_instance=RequestContext(request))

@user_login_required
def custom_404(request):
	return render_to_response("404.html",RequestContext(request))

@user_login_required
def printpdf(request):
	# Create the HttpResponse object with the appropriate PDF headers.
	response = HttpResponse(content_type='application/pdf')
	response['Content-Disposition'] = 'attachment; filename="somefilename.pdf"'

	# Create the PDF object, using the response object as its "file."
	p = canvas.Canvas(response)

	# Draw things on the PDF. Here's where the PDF generation happens.
	# See the ReportLab documentation for the full list of functionality.
	p.drawString(100, 100, "Hello world.")

	# Close the PDF object cleanly, and we're done.
	p.showPage()
	p.save()
	return response

@user_login_required
def AccommodationReport(request):
	content={}
	alist = []
	adict = {}
	bdict = {}
	list10 =[]
	list11 =[]
	if request.method == "POST":
		employeeid= request.POST.get("empid")
		fromdate= request.POST.get("fromdate")
		todate= request.POST.get("todate")
		print "idddddddddddd",employeeid
		# list1 = emp_entry.objects.filter(empid=employeeid,date_time__range=(fromdate, todate)).order_by('-empid')
		list1 = emp_entry.objects.filter(empid=employeeid,date_time__range=(fromdate,todate))
		list2 = emp_exit.objects.filter(empid=employeeid,date_time__range=(fromdate,todate))
		#print "listtttttttttttttt", list1,list2
	# try:
	# 	return self.activity_set.all().order_by('-empid')[0:1].get()
	# except Activity.DoesNotExist:
	# 	return None
	# 	activity_set__when__lte=timezone.now()
	# 	x = emp_entry.objects.all.annotate(date_time=Max('activity_set__when__lte'))
	# 	y = emp_exit.objects.all.annotate(date_time=Max('activity_set__when__lte'))
		#list5 = emp_entry.objects.filter(empid=employeeid)
		if list2:
			list3 = list2[0].empid
		else:
			list3 = []
		list4 = list1[0].empid
		print list4
		# list3 = list1[0].date_time
		# list9 =list1[0].device_location
		# list8 = emp_exit.objects.filter(empid=employeeid,date_time__gte=list1[0].date_time)
		# listn = list8[0].device_location
		if list4 != list3:
			for i in list1:
				adict['empid'] =  i.empid
				adict['device_location']  = i.device_location
				adict['date_time'] = i.date_time
			list10 = i.device_location
			print list10
			alist.append(adict)
		else:
			for i in list1:
				adict['empid'] =  i.empid
				adict['device_location']  = i.device_location
				adict['date_time'] = i.date_time
			alist.append(adict)
			for j in list2:
				bdict['empid'] = j.empid
				bdict['device_location']  = j.device_location
				bdict['date_time'] = j.date_time
			list11 = j.device_location
			print list11
			alist.append(bdict)
		content = {'lists' : alist,'latest' : list10,'latest1' : list11}#,'latest':listn,'latest1':list9}
	content.update(csrf(request))
	return render_to_response("accommodation.html",content,context_instance=RequestContext(request))

# def AccommodationReport(request):
#     list1 = emp_entry.objects.all
#     return render_to_response("accommodation.html",locals(),context_instance=RequestContext(request))

@user_login_required
def Acmd_detailreports(request):
	content = {}
	alist = []
	bh_list = []
	bh1 =[]
	bh2 =[]
	# collector = defaultdict(dict)
	cdict ={}
	list3= []
	if request.method == "POST":
		fromdate = request.POST.get('fromdate')
		todate =  request.POST.get('todate')
		if fromdate:
			list1 = emp_entry.objects.filter(date_time__range=(fromdate, todate))
			list2 = emp_exit.objects.filter(date_time__range=(fromdate,todate))
			# list3 = emp_entry.objects.all()
			# list4 = emp_exit.objects.all()
			my_list =zip(list1,list2)
			print "valuessssssssssssssss",my_list
			for i,j in my_list:
				adict={}
				adict['empid']=i.empid
				adict['status']=i.device_location
				adict['status1']=j.device_location
				adict['timeforentry']=i.date_time
				adict['timeforexit']=j.date_time
				adict['rfidcardno']=i.rfidcardno
				alist.append(adict)
			print "myyyyyyyyyyy",alist
				# for i in set(list1):
				# 	adict = {}
				# 	adict['empid']=i.empid
				# 	adict['ip_addr']=i.ip_addr
				# 	adict['status']=i.device_location
				# 	adict['timeforentry']=i.date_time
				# 	adict['rfidcardno']=i.rfidcardno
				# 	alist.append(adict)
				# # 	print adict
				# for j in set(list2):
				# 	bdict = {}
				# 	bdict['empid']=j.empid
				# 	bdict['ip_addr1']=j.ip_addr
				# 	bdict['status1']=j.device_location
				# 	bdict['timeforexit']=j.date_time
				# 	bdict['rfidcardno1']=j.rfidcardno
				# # z =zip(adict,bdict)
				# # print "okkkkkkkkkkkkk",z
				# 	alist.append(bdict)
				#z=cdict(adict+bdict)
			# for collectible in chain(adict, bdict):
			# 	collector[collectible['rfidcardno']].update(collectible.iteritems())
			# 	list_c = list(collector.itervalues())
			# if list1:
			# 	list0 = emp_entry.objects.all()#.values_list('rfidcardno')
			# 	bh2 = emp_exit.objects.all()#.values_list('rfidcardno')
			# 	# for rfidcardno in list1:
			# 	# 	bh_list.append(rfidcardno.rfidcardno)
			# 	for bh1 in list0:
			# 		adict['empid'] = bh1.empid
			# 		print bh1.empid
			# 		adict['ip_addr'] = bh1.ip_addr
			# 		print bh1.ip_addr
			# 	if bh2[0].ip_addr==[]:
			# 		adict['ip_addr1'] = []
			# 	else:
			# 		adict['ip_addr1'] =bh2[0].ip_addr
			# 		adict['status'] = bh1.device_location
			# 	if bh2[0].device_location==[]:
			# 		adict['status1'] = []
			# 	else:
			# 		adict['status1'] = bh2[0].device_location
			# 		adict['timeforentry']=bh1.date_time
			# 	if bh2[0].date_time==[]:
			# 		adict['timeforexit']=[]
			# 	else:
			# 		adict['timeforexit']=bh2[0].date_time
			# 		adict['rfidcardno'] =bh1.rfidcardno
			# 		alist.append(adict)
			content = {'lists' : alist}
		content.update(csrf(request))
	return render_to_response("accommodation1.html", content, context_instance=RequestContext(request))

# class HelloPDFView(PDFTemplateView):
#     template_name = "mealreports.html"