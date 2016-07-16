from kivy.config import Config
Config.set('graphics','height',672)
Config.set('graphics','width',480)

from kivy.app import App
from kivy.lang import Builder
from graphing import * #modded Kivy.Graph module
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from datetime import datetime, date, timedelta
import sqlite3 as sql

#calTrac modules
from dbObj import *
dbHandler().buildTables()
from userObj import *

Builder.load_file("caltrac/Cal.kv")

class RootTabs(TabbedPanel):
	pass

class RootScreen(Screen):
	foodTable = ObjectProperty(None)

	def __init__(self, **kwargs):
		super(RootScreen, self).__init__(**kwargs)
		self.foodTable.bind(minimum_height=self.foodTable.setter('height'))
		self.dateLbl.text = date.isoformat(date.today())
	def goalUpdate(self,goal):
		if goal == 'gain':
			self.kcalTxt.text = 'Daily Kcal Recommendation: %s' % (int(float(CalApp.caluser.getDict('bmr'))) + 500)
		elif goal == 'maintain':
			self.kcalTxt.text = 'Daily Kcal Recommendation: %s' % int(float(CalApp.caluser.getDict('bmr')))
		elif goal == 'lose':
			t = int(float(CalApp.caluser.getDict('bmr'))) - 500
			if t <= 1600:
				self.kcalTxt.text = 'Daily Kcal Recommendation: 1600'
			else:
				self.kcalTxt.text = 'Daily Kcal Recommendation: %s' % (int(float(CalApp.caluser.getDict('bmr'))) - 500)
	
class NewFoodScreen(Screen):

	
	def newFoodIns(self,delta):
		t = date.today() - timedelta(delta)
		try:
			realKcal = float(self.kcalInp.text)*float(self.portionInp.text)
			c.execute("INSERT INTO foods(name,date,kcal,portion) VALUES(?,?,?,?);",
				(self.foodInp.text,t,realKcal,int(self.portionInp.text)))
			db.commit()
			CalApp.updateJournal(delta)
			CalApp.sm.current = 'Root'
		except ValueError:
			invalid = Popup(title='Invalid entries',
				content=Label(text='Check your data and try again.'),
				size_hint=(None, None),size=(250,150))
			invalid.open()

class ProfileScreen(Screen):

	def setup2(self):
		try:
			CalApp.inp = [self.nameInp.text.strip(' \t\n\r'),
				float(self.heightInp.text),
				float(self.weightInp.text),int(self.yearsInp.text),
				str(self.genderInp.text)]
			print CalApp.inp
			CalApp.sm.current='Profile2'

		except (TypeError,ValueError) as e:
			invalid = Popup(title='Invalid entries',
				content=Label(text='Check your data and try again.'),
				size_hint=(None, None),size=(250,150))
			invalid.open()

class Profile2Screen(Screen):
	rateSpn = ObjectProperty(None)
	
	def setup3(self):
		CalApp.inp.append(str(self.rateSpn.text))
		CalApp.triggerUpdate()
		CalApp.sm.current = 'Root'

class DelBtn(Button):
	pass
		
class DeleteScreen(Screen):
	deleteTable = ObjectProperty(None)

	def __init__(self, **kwargs):
		super(DeleteScreen, self).__init__(**kwargs)
		self.deleteTable.bind(minimum_height=self.deleteTable.setter('height'))

	def listDelete(self,delta):
		l = c.execute("SELECT rowid, * FROM foods WHERE date = ?", (date.isoformat(date.today() - timedelta(delta)),)).fetchall()

		#list items in delete list with buttons
		#give each button an id 
		#when pressed search the local list for row number with that id.
		self.deleteTable.clear_widgets()
		for it in l:
			self.deleteTable.add_widget(DelBtn(text='%s - x%s    kcal: %s' % (it[1],str(it[4]).replace('.0',''),str(it[3]).replace('.0','')),
			id = str(it[0])))

class CaltracApp(App):
	ratingText = '''How would you describe the amount of exercise you do?
1. Little to no exercise
2. Light exercise(1-3 days per week)
3. Moderate exercise(3-5 days per week)
4. Heavy exercise(6-7 days per week)
5. Very heavy exercise(twice per day, extra heavy workouts)'''
	sm = ScreenManager()
	inp = []
	
	def __init__(self, **kwargs):
		super(CaltracApp, self).__init__(**kwargs)

	def build(self):
		self.caluser = User()
		self.dayDelta = 0

		self.Root = RootScreen()
		self.NewFood = NewFoodScreen()
		self.Profile = ProfileScreen()
		self.Profile2 = Profile2Screen()
		self.DeleteScreen = DeleteScreen()
		self.sm.add_widget(self.Root)
		self.sm.add_widget(self.NewFood)
		self.sm.add_widget(self.Profile)
		self.sm.add_widget(self.Profile2)
		self.sm.add_widget(self.DeleteScreen)
		return self.sm

	def on_start(self):
		if self.caluser.p == [None,None,None,None,None,None]:
			self.SetupProfile()
		self.updateJournal()
		
	def deltaUpdate(self,val):
		self.dayDelta += val
		self.updateJournal(self.dayDelta)
	
	def deltaReset(self):
		self.dayDelta = 0
		self.updateJournal()

	def SetupProfile(self):
		self.sm.current = 'Profile'
	
	def triggerUpdate(self):
		self.caluser.updateProfile(self.inp)
		print self.inp
		self.Root.userPnl.text = self.caluser.getDict('name')
		self.Root.nameLbl.text = 'About ' + self.caluser.getDict('name')
		self.Root.heightLbl.text = 'Height: ' + self.caluser.getDict('height')
		self.Root.weightLbl.text = 'Weight: ' + self.caluser.getDict('weight')
		self.Root.ageLbl.text = 'Age: ' + self.caluser.getDict('age')
		self.Root.genderLbl.text = 'Gender: ' + self.caluser.getDict('gender')
		self.Root.ratingLbl.text = 'Rating: ' + self.caluser.getDict('rating')
		self.Root.kcalTxt.text = 'Daily Kcal Recommendation: ' + str(int(float(self.caluser.getDict('bmr'))))
	
	def DeleteItems(self,delta):
		self.DeleteScreen.listDelete(delta)
		self.sm.current = 'DeleteFood'
	
	def updateJournal(self,delta=0):
		l = c.execute("SELECT * FROM foods WHERE date = ?", (date.isoformat(date.today()-timedelta(delta)),)).fetchall()
		stats = []
		self.Root.foodTable.clear_widgets()
		self.Root.foodTable.add_widget(Button(text='Items'))
		self.Root.foodTable.add_widget(Button(text='KCAL'))
		for it in l:
			self.Root.foodTable.add_widget(Label(text='%s - x%s' % (it[0],str(it[3]).replace('.0',''))))
			self.Root.foodTable.add_widget(Label(text=str(it[2]).replace('.0','')))
			stats.append(it[2])
		
		self.Root.dateLbl.text = date.isoformat(date.today() - timedelta(delta))
		if delta != 0:
			self.Root.tmrwBtn.disabled = False
		else:
			self.Root.tmrwBtn.disabled = True
		try:
			c.execute("INSERT OR REPLACE INTO calendar(date,total,avg,len) VALUES(?,?,?,?)",
				(date.isoformat(date.today()-timedelta(delta)),sum(stats),sum(stats)/len(stats),len(stats),))
		except:
			pass
		db.commit()
		#retrieve weekly
		total = []; avg = []; items = []; pointlist = [] # lists to use 
		#the following graph works through a workaround for an open issue with Kivy's Graph module. 
		#https://github.com/kivy-garden/garden.graph/issues/7 follow this.
		
		weekGraph = Graph(xlabel='Days', ylabel='Calories',
			x_ticks_major=1, y_ticks_major=1000, y_ticks_minor=500,
			y_grid_label=True, x_grid_label=True,
			x_grid=False, y_grid=True, xmin=0, xmax=7, ymin=0, ymax=5000)

		weekplot = MeshStemPlot(color=[1, 0, 0, 1])
		for i in xrange(8):
			try:
				total.append(c.execute("SELECT total FROM calendar WHERE date = ?",(date.isoformat(date.today()- timedelta(i)),)).fetchall()[0][0])
				avg.append(c.execute("SELECT avg FROM calendar WHERE date = ?",(date.isoformat(date.today()- timedelta(i)),)).fetchall()[0][0])
				items.append(c.execute("SELECT len FROM calendar WHERE date = ?",(date.isoformat(date.today()- timedelta(i)),)).fetchall()[0][0])
				pointlist.append((i,float(c.execute("SELECT total FROM calendar WHERE date = ?",(date.isoformat(date.today()- timedelta(i)),)).fetchall()[0][0])))
			except:
				total.append(0)
				avg.append(0)
				pointlist.append((i,0))
		try:
			avg = sum(avg)/len(items)
		except:
			avg = 'No data.'
		total = sum(total)
		self.Root.weekTotalTxt.text = "Total calories: %s" % total
		self.Root.weekAvgTxt.text = "Average per day: %s" % avg
		self.Root.weekLenTxt.text = "Total items: %s" % sum(items)
		weekplot.points = [(x[0],x[1]) for x in pointlist]
		weekGraph.add_plot(weekplot)
		self.Root.weekGraphLayout.clear_widgets()
		self.Root.weekGraphLayout.add_widget(weekGraph)
		
		#monthly
		total = []; avg = []; items = []; pointlist = []; # reset lists 
		monthGraph = Graph(xlabel='Days', ylabel='Calories',
			x_ticks_major=5,x_ticks_minor=1, y_ticks_major=1000, y_ticks_minor=500,
			y_grid_label=True, x_grid_label=True,
			x_grid=True, y_grid=True, xmin=0, xmax=30, ymin=0, ymax=5000)
			
		monthplot = SmoothLinePlot(color=[1, 0, 0, 1])

		for i in xrange(31):
			try:
				total.append(c.execute("SELECT total FROM calendar WHERE date = ?",(date.isoformat(date.today()- timedelta(i)),)).fetchall()[0][0])
				avg.append(c.execute("SELECT avg FROM calendar WHERE date = ?",(date.isoformat(date.today()- timedelta(i)),)).fetchall()[0][0])
				items.append(c.execute("SELECT len FROM calendar WHERE date = ?",(date.isoformat(date.today()- timedelta(i)),)).fetchall()[0][0])
				pointlist.append((i,float(c.execute("SELECT total FROM calendar WHERE date = ?",(date.isoformat(date.today()- timedelta(i)),)).fetchall()[0][0])))			
			except:
				total.append(0)
				avg.append(0)
				#if it cant it means nothing could be found
				pointlist.append((i,0))
		try:
			avg = sum(avg)/len(items)
		except:
			acg = 'No data.'
		total = sum(total)
		self.Root.monthTotalTxt.text = "Total calories: %s" % total
		self.Root.monthAvgTxt.text = "Average per day: %s" % avg
		self.Root.monthLenTxt.text = "Total items: %s" % sum(items)
		monthplot.points = [(x[0],x[1]) for x in pointlist]
		monthGraph.add_plot(monthplot)
		self.Root.monthGraphLayout.clear_widgets()
		self.Root.monthGraphLayout.add_widget(monthGraph)

		
		t = int(list(c.execute("SELECT TOTAL(kcal) FROM foods WHERE date = ?",(date.isoformat(date.today()-timedelta(delta)),)).fetchone())[0])
		self.Root.totalTxt.text = 'Total kcal intake today: %s' % t
	
	def deleteEntry(self,i):
		c.execute("DELETE FROM foods WHERE rowid = ?", (i,))
		db.commit()
		self.updateJournal(self.dayDelta)
		self.sm.current = 'Root'

CalApp = CaltracApp()

