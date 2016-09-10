from dbObj import * 

class User(object):
	def getDict(self,i):
		try:
			return str(self.data[i])
		except:
			return '0'
	def usrProfile(self): 
			self.p = c.execute('SELECT name,height,weight,age,gender,rating,pregnancy FROM user').fetchall()
			try:
				for i in self.p[0]:
					self.p.append(i)
				self.p.pop(0)
				self.p.extend(None for i in range(len(self.p),7))
				if None in self.p:
					raise IndexError
				self.data = {'raw':self.p,'name':self.p[0],'height':self.p[1],
				'weight':self.p[2],'age':self.p[3],'gender':self.p[4],'rating':self.p[5],'preg':self.p[6]}
				if self.data['gender'] == 'Male':
					bmr = 88.362 + (13.397*self.data['weight']) + (4.799*self.data['height']) - (5.677*self.data['age'])
				elif self.data['gender'] == 'Female':
					bmr = 447.593 + (9.247*self.data['weight']) + (3.098*self.data['height']) - (4.330*self.data['age'])
				factors = [0,1.2,1.375,1.55,1.725,1.9]
				bmr = bmr*factors[self.data['rating']]
				self.data['bmr'] = bmr
			except IndexError:
				self.p = [None,None,None,None,None,None,None]
				#Triggers new profile screen in calapp obj
	def updateProfile(self,inp):
		c.execute("INSERT OR REPLACE INTO user(func,name,height,weight,age,gender,rating,pregnancy) VALUES('USER',?,?,?,?,?,?,?);",
		(inp[0],inp[1],inp[2],inp[3],inp[4],inp[5],inp[6],))
		db.commit()
		self.usrProfile()
	def __init__(self):
		self.data = {}
		self.usrProfile()			
