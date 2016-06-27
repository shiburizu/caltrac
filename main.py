from kivy.config import Config
Config.set('graphics','height',672)
Config.set('graphics','width',480)

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from datetime import datetime, date
import sqlite3 as sql
import sys

db = sql.connect('CalTrac.db',detect_types=sql.PARSE_DECLTYPES)
c = db.cursor()
#TODO error checking
c.execute('''CREATE TABLE IF NOT EXISTS user(func TEXT UNIQUE, name TEXT,
 height REAL, weight REAL, age INTEGER, gender TEXT	, rating INTEGER);''')
c.execute('''CREATE TABLE IF NOT EXISTS foods(name TEXT, date DATE, kcal REAL, 
portion REAL);''')

class User(object):

	def getDict(self,i):
		try:
			return str(self.data[i])
		except:
			#we do this so the UI has something to use while setup goes on
			return '1'
		

	def usrProfile(self,gui): #creates a dictionary of user data from SQLite
			self.p = c.execute('SELECT name,height,weight,age,gender,rating FROM user').fetchall()
			try:
				for i in self.p[0]:
					self.p.append(i)
				self.p.pop(0)
				self.p.extend(None for i in range(len(self.p),6))
				print self.p
				
				if None in self.p:
					raise IndexError
				self.data = {'raw':self.p,'name':self.p[0],'height':self.p[1],
				'weight':self.p[2],'age':self.p[3],'gender':self.p[4],'rating':self.p[5]}
				print self.data['gender']
				if self.data['gender'] == 'Male':
					bmr = 88.362 + (13.397*self.data['weight']) + (4.799*self.data['height']) - (5.677*self.data['age'])
				elif self.data['gender'] == 'Female':
					bmr = 447.593 + (9.247*self.data['weight']) + (3.098*self.data['height']) - (4.330*self.data['age'])
				factors = [0,1.2,1.375,1.55,1.725,1.9]

				bmr = bmr*factors[self.data['rating']]
				self.data['bmr'] = bmr

				self.stats = "%s's profile\nGender:%s\nHeight:%s\nWeight:%s\nAge:%s\nRating:%s" % (
				self.data['name'],self.data['gender'],self.data['height'],self.data['weight'],
				self.data['age'],self.data['rating'])
			except IndexError:
				self.p = [None,None,None,None,None,None]
				#Triggers new profile screen in calapp obj
				
	
		
	def updateProfile(self,inp):
		c.execute("INSERT OR REPLACE INTO user(func,name,height,weight,age,gender,rating) VALUES('USER',?,?,?,?,?,?);",
		(inp[0],inp[1],inp[2],inp[3],inp[4],inp[5]))
		db.commit()
		self.usrProfile(CalApp)
		
	def __init__(self,gui):
		self.data = {}

		self.usrProfile(gui)			
		print self.data

class RootTabs(TabbedPanel):
	pass

class RootScreen(Screen):
	foodTable = ObjectProperty(None)
	goalSpn = ObjectProperty(None)
	
	def __init__(self, **kwargs):
		super(RootScreen, self).__init__(**kwargs)
		self.foodTable.bind(minimum_height=self.foodTable.setter('height'))
	
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
	foodInp = ObjectProperty(None)
	kcalInp = ObjectProperty(None)
	portionInp = ObjectProperty(None)
	
	def newFoodIns(self):
		t = date.today()
		try:
			realKcal = float(self.kcalInp.text)*float(self.portionInp.text)
			c.execute("INSERT INTO foods(name,date,kcal,portion) VALUES(?,?,?,?);",
				(self.foodInp.text,t,realKcal,int(self.portionInp.text)))
			db.commit()
			CalApp.updateJournal()
			CalApp.sm.current = 'Root'
		except ValueError:
			invalid = Popup(title='Invalid entries',
				content=Label(text='Check your data and try again.'),
				size_hint=(None, None),size=(250,150))
			invalid.open()

class ProfileScreen(Screen):
	#objects defined in the kv must have a rule
	#e.g. nameInp: nameInp
	#that way None can be replaced by its instance.
	nameInp = ObjectProperty(None)
	heightInp = ObjectProperty(None)
	weightInp = ObjectProperty(None)
	yearsInp = ObjectProperty(None)
	genderInp = ObjectProperty(None)

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
		self.caluser = User(self)

		self.Root = RootScreen()
		self.NewFood = NewFoodScreen()
		self.Profile = ProfileScreen()
		self.Profile2 = Profile2Screen()
		self.sm.add_widget(self.Root)
		self.sm.add_widget(self.NewFood)
		self.sm.add_widget(self.Profile)
		self.sm.add_widget(self.Profile2)
		return self.sm

	def on_start(self):
		if self.caluser.p == [None,None,None,None,None,None]:
			self.SetupProfile()
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
	
	def updateJournal(self):
		l = c.execute("SELECT * FROM foods WHERE date = ?", (date.isoformat(date.today()),)).fetchall()
		self.Root.foodTable.clear_widgets()
		self.Root.foodTable.add_widget(Button(text='Items'))
		self.Root.foodTable.add_widget(Button(text='KCAL'))
		for it in l:
			self.Root.foodTable.add_widget(Label(text='%s - x%s' % (it[0],str(it[3]).replace('.0',''))))
			self.Root.foodTable.add_widget(Label(text=str(it[2]).replace('.0','')))
		t = list(c.execute("SELECT TOTAL(kcal) FROM foods WHERE date = ?",(date.isoformat(date.today()),)).fetchone())
		t = t[0]; t = int(t) 
		self.Root.totalTxt.text = 'Total kcal intake today: %s' % t
		

CalApp = CaltracApp()
CalApp.run()
