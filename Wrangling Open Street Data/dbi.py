# -*- coding: utf-8 -*- 

import sqlite3,csv,time,codecs

class dbInterface(object):
	'''db operating interface'''

	def __init__(self,path):
		'''connect and get the conn and cursor'''
		self.conn=sqlite3.connect(path)
		self.cu=self.conn.cursor()

	def finish(self):
		'''close the conn'''
		self.conn.close()

	def act_queries_in_afile(self,path):
		'''wait for changes'''	
		with open(path,'r') as f:
			queries=f.readlines()
			for query in queries:
				self.cu.execute(query)
				self.commit()

	def unicode_change(self,this):
		'''change from bytestring to unicode or stay unchanged'''
		if type(this)==str:
			return this.decode('utf-8')
		else:
			return this

	def select_and_repr(self,query):
		for i in self.cu.execute(query).fetchall():
			print i


	def insert_from_csv(self,csv_path,table_name,headers=''):
		count=0
		with codecs.open(csv_path,'rb') as fin:
			dr=csv.DictReader(fin)
			for i in dr:
				try:
					to_db=map(self.unicode_change,i.values())
					self.cu.execute("INSERT INTO %s(%s) VALUES (%s);"%(table_name,','.join(i.keys()),','.join(['?']*len(to_db))),to_db)
				except Exception as e:
					if type(e)==sqlite3.IntegrityError:
						pass
					else:
						print type(e),':',e
						print i.values()
						time.sleep(0.3)
				count+=1
				if count%100000==0:
					print count,'on processing'
					time.sleep(0.5)
				# if count==1000:
				# 	print 'finish it tempera'
				# 	self.select_and_repr('SELECT * FROM nodes LIMIT 10')
				# 	self.select_and_repr('SELECT user,uid FROM nodes LIMIT 10')
				# 	raw_input()
		self.conn.commit()

def create_new_db(dbi):
	schema=['''CREATE TABLE nodes (
		id INTEGER PRIMARY KEY NOT NULL,
		lat REAL,
		lon REAL,
		user TEXT,
		uid INTEGER,
		version INTEGER,
		changeset INTEGER,
		timestamp TEXT
		);'''
		,
		'''CREATE TABLE nodes_tags (
		    id INTEGER,
		    key TEXT,
		    value TEXT,
		    type TEXT,
		    FOREIGN KEY (id) REFERENCES nodes(id)
		);'''
		,
		'''CREATE TABLE ways (
		    id INTEGER PRIMARY KEY NOT NULL,
		    user TEXT,
		    uid INTEGER,
		    version TEXT,
		    changeset INTEGER,
		    timestamp TEXT
		);'''
		,
		'''CREATE TABLE ways_tags (
		    id INTEGER NOT NULL,
		    key TEXT NOT NULL,
		    value TEXT NOT NULL,
		    type TEXT,
		    FOREIGN KEY (id) REFERENCES ways(id)
		);'''
		,
		'''CREATE TABLE ways_nodes (
		    id INTEGER NOT NULL,
		    node_id INTEGER NOT NULL,
		    position INTEGER NOT NULL,
		    FOREIGN KEY (id) REFERENCES ways(id),
		    FOREIGN KEY (node_id) REFERENCES nodes(id)
		);'''
		]
	for q in schema:
		dbi.cu.execute(q)
		dbi.conn.commit()


if __name__=='__main__':
	tl=[(u'manings_labuildings', 2112352),
	(u'schleuss_imports', 1559776),
	(u'Jothirnadh_labuildings', 1316835),
	(u'calfarome_labuilding', 693222),
	(u'nammala_labuildings', 604213),
	(u'Luis36995_labuildings', 596527),
	(u'saikabhi_LA_imports', 570205),
	(u'The Temecula Mapper', 548130),
	(u'planemad_imports', 529421),
	(u'woodpeck_fixbot', 510267)]
	total=18910668+1947075.0
	print 6889243/total

	raw_input()
	print 'start operating'
	PATH_HEADER="F:\Hsiao's studying\Computing\Udacity P3\\"
	table_list=['nodes','nodes_tags','ways','ways_tags','ways_nodes']
	dbi=dbInterface(PATH_HEADER+'mapdata.db')
	#create_new_db(dbi)
	for table in table_list:
		dbi.insert_from_csv(PATH_HEADER+table+'.csv',table)
		print 'keep on going'
	# dbi.conn.commit()
	# for i in dbi.cu.execute('SELECT * FROM nodes LIMIT 0,10').fetchall():
	# 	print i
	dbi.finish()

	# 入库成功！
	pass