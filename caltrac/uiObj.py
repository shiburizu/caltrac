from kivy.config import Config
Config.set('graphics','width','320')
Config.set('graphics','height','480')
from kivy.core.window import Window
Window.softinput_mode = 'below_target'
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

#kivyMD
from kivymd.theming import ThemeManager
from kivymd.label import MDLabel
from kivymd.list import TwoLineListItem
from kivymd.navigationdrawer import NavigationDrawer
from kivymd.button import MDRaisedButton

#patched KivyMD object
from bottomsheet import MDListBottomSheet

#calTrac modules
from dbObj import *
dbHandler().buildTables()
from userObj import *

Builder.load_file("caltrac/CalMD.kv")

class RootScreen(Screen):
	foodTable = ObjectProperty(None)
	def goalUpdate(self,goal):
		if goal == 'gain':
			self.kcalTxt.text = 'Kcal target: %s' % (int(float(CalApp.caluser.getDict('bmr'))) + 500)
		elif goal == 'maintain':
			self.kcalTxt.text = 'Kcal target: %s' % int(float(CalApp.caluser.getDict('bmr')))
		elif goal == 'lose':
			t = int(float(CalApp.caluser.getDict('bmr'))) - 500
			if t <= 1600:
				self.kcalTxt.text = 'Kcal target: 1600'
			else:
				self.kcalTxt.text = 'Kcal target: %s' % (int(float(CalApp.caluser.getDict('bmr'))) - 500)
	def showGoalsSheet(self):
		bs = MDListBottomSheet()
		bs.add_item("I want to lose weight.", lambda x: CalApp.Root.goalUpdate('lose'))
		bs.add_item("I want to maintain my current weight.", lambda x: CalApp.Root.goalUpdate('maintain'))
		bs.add_item("I want to gain weight.", lambda x: CalApp.Root.goalUpdate('gain'))
		bs.open()
	
	def triggerDummy(self,goal):
		self.goalUpdate(goal)
	
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
				size_hint=(None, None),size=('250dp','150dp'))
			invalid.open()

class ProfileScreen(Screen):
	genderChoice = 'Male'
	def setup2(self):
		try:
			CalApp.inp = [self.nameInp.text.strip(' \t\n\r'),
				float(self.heightInp.text),
				float(self.weightInp.text),int(self.yearsInp.text),
				self.genderChoice]
			CalApp.sm.current='Profile2'

		except (TypeError,ValueError) as e:
			invalid = Popup(title='Invalid entries',
				content=Label(text='Check your data and try again.'),
				size_hint=(None, None),size=('250dp','150dp'))
			invalid.open()
	def openGenderSelect(self):
		bs = MDListBottomSheet()
		bs.add_item("Male", lambda x: CalApp.Profile.changeGender("Male"))
		bs.add_item("Female", lambda x: CalApp.Profile.changeGender("Female"))
		bs.open()
	
	def changeGender(self, gen):
		self.genderChoice = gen
		self.ids['genderInp'].text = self.genderChoice
		

class Profile2Screen(Screen):
	rateChoice = 1
	
	def setup3(self):
		CalApp.inp.append(str(self.rateChoice))
		CalApp.triggerUpdate()
		self.rateChoice = 1
		CalApp.sm.current = 'Root'
	
	def openRateChoice(self):
		bs = MDListBottomSheet()
		bs.add_item("1. Little to no exercise", lambda x: CalApp.Profile2.setChoice(1,"1. Little to no exercise"))
		bs.add_item("2. Light (1-3 days)", lambda x: CalApp.Profile2.setChoice(2,"2. Light (1-3 days)"))
		bs.add_item("3. Moderate (3-5 days)", lambda x: CalApp.Profile2.setChoice(3,"3. Moderate (3-5 days)"))
		bs.add_item("4. Heavy (6-7 days)", lambda x: CalApp.Profile2.setChoice(4,"4. Heavy (6-7 days)"))
		bs.add_item("5. Very heavy (twice per day)", lambda x: CalApp.Profile2.setChoice(5,"5. Very heavy (twice per day)"))
		bs.open()
	def setChoice(self,i,txt):
		self.rateChoice = i
		self.ids['choiceTxt'].text = "Currently selected: %s \n %s" % (i,txt)
	

class DelBtn(TwoLineListItem):
	pass

class SandwichMenu(NavigationDrawer):
	pass
		
class DeleteScreen(Screen):
	deleteTable = ObjectProperty(None)

	def __init__(self, **kwargs):
		super(DeleteScreen, self).__init__(**kwargs)
		self.deleteTable.bind(minimum_height=self.deleteTable.setter('height'))

	def listDelete(self,delta):
		l = c.execute("SELECT rowid, * FROM foods WHERE date = ?", (date.isoformat(date.today() - timedelta(delta)),)).fetchall()
		self.deleteTable.clear_widgets()
		for it in l:
			self.deleteTable.add_widget(DelBtn(text='%s - x%s' % (it[1],str(it[4]).replace('.0','')),
				secondary_text='kcal: %s' % str(it[3]).replace('.0',''),id = str(it[0])))

			
class LangScreen(Screen):
	#options are en and es
	def setLang(self,lang):
		c.execute("INSERT OR REPLACE INTO user(lang) VALUES(?)",(lang,))
		c.commit()

class CaltracApp(App):
	def __init__(self, **kwargs):
		super(CaltracApp, self).__init__(**kwargs)
		self.sm = ScreenManager()
		self.inp = []
		self.theme_cls = ThemeManager()
		self.theme_cls.theme_style = 'Dark'
		self.theme_cls.primary_palette = 'Green'
		self.theme_cls.accent_palette = 'Pink'
		self.nav_drawer = ObjectProperty()

	def build(self):
		self.caluser = User()
		self.dayDelta = 0
		self.nav_drawer = SandwichMenu()
		self.Root = RootScreen()
		self.NewFood = NewFoodScreen()
		self.Profile = ProfileScreen()
		self.Profile2 = Profile2Screen()
		self.DeleteScreen = DeleteScreen()
		self.LangScreen = LangScreen()
		self.sm.add_widget(self.Root)
		self.sm.add_widget(self.NewFood)
		self.sm.add_widget(self.Profile)
		self.sm.add_widget(self.Profile2)
		self.sm.add_widget(self.DeleteScreen)
		self.sm.add_widget(self.LangScreen)
		return self.sm

	def on_start(self):
		if self.caluser.p == [None,None,None,None,None,None]:
			self.SetupProfile() #todo transition to setlang
		self.updateJournal()
	
	def on_pause(self):
		return True
	
	def on_resume(self):
		pass
		
	def deltaUpdate(self,val):
		self.dayDelta += val
		self.updateJournal(self.dayDelta)
	
	def deltaReset(self):
		self.dayDelta = 0
		self.updateJournal()
	
	def selectLang(self):
		self.sm.current= 'SetLang'

	def SetupProfile(self,lang=""): #todo
		#lc.execute("INSERT OR REPLACE INTO user(lang) VALUES (?)", (lang,))
		self.Profile.ids['profileToolbar'].left_action_items = []
		self.sm.current = 'Profile'
	
	def triggerUpdate(self):
		self.caluser.updateProfile(self.inp)
		self.Root.toolbar.title = "CalTrac - %s" % date.isoformat(date.today())
		self.Root.nameLbl.text = 'About ' + self.caluser.getDict('name')
		self.Root.heightLbl.text = 'Height: ' + self.caluser.getDict('height')
		self.Root.weightLbl.text = 'Weight: ' + self.caluser.getDict('weight')
		self.Root.ageLbl.text = 'Age: ' + self.caluser.getDict('age')
		self.Root.genderLbl.text = 'Gender: ' + self.caluser.getDict('gender')
		self.Root.ratingLbl.text = 'Rating: ' + self.caluser.getDict('rating')
		self.Root.kcalTxt.text = 'Kcal target: ' + str(int(float(self.caluser.getDict('bmr'))))
		self.nav_drawer.ids['nameBtn'].text = self.caluser.getDict('name')
		self.Profile.ids['profileToolbar'].left_action_items = [['arrow-left', lambda x: self.changeScreens('Root')]]
	def DeleteItems(self,delta):
		self.DeleteScreen.listDelete(delta)
		self.sm.current = 'DeleteFood'
	
	def updateJournal(self,delta=0):
		l = c.execute("SELECT * FROM foods WHERE date = ?", (date.isoformat(date.today()-timedelta(delta)),)).fetchall()
		stats = []
		self.Root.foodTable.clear_widgets()
		for it in l:
			self.Root.foodTable.add_widget(TwoLineListItem(text='%s - x%s' % (it[0],str(it[3]).replace('.0','')),secondary_text="%s kcal" % str(it[2]).replace('.0','')))
			stats.append(it[2])
		self.Root.toolbar.title = "CalTrac - %s" % date.isoformat(date.today() - timedelta(delta))
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
		weekGraph = Graph(xlabel='Days', ylabel='Calories',
			x_ticks_major=1, y_ticks_major=1000, y_ticks_minor=500,
			y_grid_label=True, x_grid_label=True,
			x_grid=False, y_grid=True, xmin=1, xmax=7, ymin=0, ymax=5000)
		weekplot = MeshStemPlot(color=[1, 0, 0, 1])
		for i in xrange(1,8):
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
			x_ticks_major=7,x_ticks_minor=1, y_ticks_major=1000, y_ticks_minor=500,
			y_grid_label=True, x_grid_label=True,
			x_grid=True, y_grid=True, xmin=1, xmax=30, ymin=0, ymax=5000)
		monthplot = SmoothLinePlot(color=[1, 0, 0, 1])
		for i in xrange(1,31):
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
			avg = 'No data.'
		total = sum(total)
		self.Root.monthTotalTxt.text = "Total calories: %s" % total
		self.Root.monthAvgTxt.text = "Average per day: %s" % avg
		self.Root.monthLenTxt.text = "Total items: %s" % sum(items)
		monthplot.points = [(x[0],x[1]) for x in pointlist]
		monthGraph.add_plot(monthplot)
		self.Root.monthGraphLayout.clear_widgets()
		self.Root.monthGraphLayout.add_widget(monthGraph)
		t = int(list(c.execute("SELECT TOTAL(kcal) FROM foods WHERE date = ?",(date.isoformat(date.today()-timedelta(delta)),)).fetchone())[0])
		self.Root.totalTxt.text = 'Kcal intake: %s' % t
	def deleteEntry(self,i):
		date = list(c.execute("SELECT * FROM foods WHERE rowid = ?",(i,)).fetchone())[1]
		c.execute("DELETE FROM calendar WHERE date = ?",(date,))
		c.execute("DELETE FROM foods WHERE rowid = ?", (i,))
		db.commit()
		self.updateJournal(self.dayDelta)
		self.sm.current = 'Root'
	def getLocalTxt(self,lang,txt):
		return unicode(list(lc.execute("SELECT %s FROM dictionary WHERE id = ?" % lang,(txt,)).fetchone())[0])
		#todo replace with dictionary func
	def changeScreens(self,screen):
		self.sm.current = screen
	
CalApp = CaltracApp()

