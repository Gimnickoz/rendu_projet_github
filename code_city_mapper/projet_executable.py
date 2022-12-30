import folium, io, json, sys, math, random, os
import psycopg2
from folium.plugins import Draw, MousePosition, MeasureControl
from jinja2 import Template
from branca.element import Element
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from datetime import datetime
from PyQt5 import QtGui


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.resize(600, 600)
	    
        main = QWidget()
        self.setCentralWidget(main)
        main.setLayout(QVBoxLayout())
        main.setFocusPolicy(Qt.StrongFocus)

        self.tableWidget = QTableWidget()
        self.tableWidget.doubleClicked.connect(self.table_Click)
        self.rows = []

        self.webView = myWebView()
        controls_fonction = QHBoxLayout()
        controls_panel = QHBoxLayout()
        mysplit = QSplitter(Qt.Vertical)
        mysplit.addWidget(self.tableWidget)
        mysplit.addWidget(self.webView)

        main.layout().addLayout(controls_fonction)
        main.layout().addLayout(controls_panel)
        main.layout().addWidget(mysplit)

        ############################
        #Initialisation de la fonctionnalité des lignes de transport

        self.setWindowIcon(QtGui.QIcon('logo.jpg'))

        self.setWindowTitle("Projet City mapper")

        self.setGeometry(0,0,800,400)

        _label = QLabel('Mode :',self)
        _label.setFixedWidth(55)

        #initialisation des checkBox pour chaque mode de transport
        self.check_boxbus = QCheckBox()
        self.check_boxtram = QCheckBox()
        self.check_boxmetro = QCheckBox()
        self.check_boxtrain = QCheckBox()
        self.check_boxtout = QCheckBox()

        # création texte pour chaque mode de transport
        self.check_boxbus.setText("Bus")
        self.check_boxbus.setFixedWidth(50)
        self.check_boxbus.stateChanged.connect(lambda:self.btnstate(self.check_boxbus))

        self.check_boxtram.setText("Tram")
        self.check_boxtram.setFixedWidth(60)
        self.check_boxtram.stateChanged.connect(lambda:self.btnstate(self.check_boxtram))

        self.check_boxmetro.setText("Metro")
        self.check_boxmetro.setFixedWidth(70)
        self.check_boxmetro.stateChanged.connect(lambda:self.btnstate(self.check_boxmetro))

        self.check_boxtrain.setText("Train")
        self.check_boxtrain.setFixedWidth(70)
        self.check_boxtrain.stateChanged.connect(lambda:self.btnstate(self.check_boxtrain))

        self.check_boxtout.setText("tout")
        self.check_boxtout.setFixedWidth(70)
        self.check_boxtout.stateChanged.connect(lambda:self.btnstate(self.check_boxtout))

        controls_fonction.addWidget(_label)
        controls_fonction.addWidget(self.check_boxbus)
        controls_fonction.addWidget(self.check_boxtram)
        controls_fonction.addWidget(self.check_boxmetro)
        controls_fonction.addWidget(self.check_boxtrain)
        controls_fonction.addWidget(self.check_boxtout)

        _label = QLabel('Ligne', self)
        _label.setFixedSize(40,20)
        self.ligne_box = QComboBox() 
        self.ligne_box.setFixedWidth(100)
        self.ligne_box.setEditable(True)
        self.ligne_box.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.ligne_box.setInsertPolicy(QComboBox.NoInsert)
        controls_fonction.addWidget(_label)
        controls_fonction.addWidget(self.ligne_box)

        self.show_button = QPushButton("Show!")
        self.show_button.setFixedWidth(100)
        self.show_button.clicked.connect(self.button_Show)
        controls_fonction.addWidget(self.show_button)

        ############################

        _label = QLabel('From: ', self)
        _label.setFixedSize(30,20)
        self.from_box = QComboBox() 
        self.from_box.setEditable(True)
        self.from_box.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.from_box.setInsertPolicy(QComboBox.NoInsert)
        controls_panel.addWidget(_label)
        controls_panel.addWidget(self.from_box)

        _label = QLabel('To: ', self)
        _label.setFixedSize(15,15)
        self.to_box = QComboBox() 
        self.to_box.setEditable(True)
        self.to_box.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.to_box.setInsertPolicy(QComboBox.NoInsert)
        controls_panel.addWidget(_label)
        controls_panel.addWidget(self.to_box)

        _label = QLabel('Hops: ', self)
        _label.setFixedSize(20,20)
        self.hop_box = QComboBox() 
        self.hop_box.addItems( ['1', '2', '3'] )
        self.hop_box.setCurrentIndex( 2 )
        controls_panel.addWidget(_label)
        controls_panel.addWidget(self.hop_box)

        # Creation des boutons et assignation des fonctionnalités
        self.go_button = QPushButton("Go!")
        self.go_button.clicked.connect(self.button_Go)
        controls_panel.addWidget(self.go_button)
           
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.button_Clear)
        controls_panel.addWidget(self.clear_button)

        self.sauvegarde_button = QPushButton("SAVE")
        self.sauvegarde_button.clicked.connect(self.button_Sauvegarde)
        controls_panel.addWidget(self.sauvegarde_button)

        self.maptype_box = QComboBox()
        self.maptype_box.addItems(self.webView.maptypes)
        self.maptype_box.currentIndexChanged.connect(self.webView.setMap)
        controls_panel.addWidget(self.maptype_box)
           
        self.connect_DB()

        self.startingpoint = True
                   
        self.show()

    def closeEvent(self,event):
       return event.accept() if QMessageBox.question(
           self, "Fermeture App", "<h3> <font color='red'>Voulez-vous vraiment quitter ?</font></h3>", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes else event.ignore()
           
           
           
    # Connexion à la DB de l'université localement
    def connect_DB(self):
        self.conn = psycopg2.connect(database="l3info_14", user="l3info_14", host="10.11.11.22", password="L3INFO_14")
        self.cursor = self.conn.cursor()

        self.cursor.execute("""with metros(geo_point_2d,nom_long,res_com) as
    (select distinct CONCAT(stations.lat,',',stations.lon) as ma,stations.name,route.route_name
    from stations,route,combined_projet
    where stations.stop_i=combined_projet.from_stop and route.route_i=combined_projet.route_i
    order by stations.name ASC) SELECT distinct nom_long FROM metros ORDER BY nom_long""")
        self.conn.commit()
        rows = self.cursor.fetchall()

        for row in rows : 
            self.from_box.addItem(str(row[0]))
            self.to_box.addItem(str(row[0]))


    # Création d un fichier historique_chemin.txt qui prend la sortie des commandes
    def button_Sauvegarde(self):
        now = datetime.now()
        with open('historique_chemin.txt', 'a') as f:
            f.write(str(now.strftime("Fait le : %d/%m/%Y  à %H:%M:%S")))
            f.write('\n')
            
            i = 0
            for row in self.rows : 
                j = 0
                k = 0 
                for col in row :
                    if j % 3 == 0 : 
                        k = k + 1
                    else : 
                        f.write(self.rows[i][j] + '\t' + '|')
                    j = j + 1
                f.write('\n')
                i = i + 1
            f.write('-------------------------------------------------------------------')
            f.write('\n \n')    

    # affichage des lignes en fonctions de la case cochée            
    def btnstate(self, cnx):
         
         self.from_box.clear()
         self.to_box.clear()
         self.ligne_box.clear()
                    
         if cnx.text() == 'tout':
           if cnx.isChecked() == True:
                checked = self.cursor.execute("""SELECT DISTINCT name FROM combined_projet, stations WHERE stop_I = combined_projet.from_stop ORDER BY name""")
                self.conn.commit()
                rows = self.cursor.fetchall()
                for row in rows : 
                            self.from_box.addItem(str(row[0]))
                            self.to_box.addItem(str(row[0]))
                self.cursor.execute("""SELECT distinct route_name FROM route ORDER BY route_name""")
                self.conn.commit()
                rows = self.cursor.fetchall()
                for row in rows : 
                            self.ligne_box.addItem(str(row[0]))   
         if cnx.text() == "Bus":
            if cnx.isChecked() == True:
                checked = self.cursor.execute("""SELECT DISTINCT name FROM combined_projet, stations WHERE stop_I = combined_projet.from_stop AND route_type = 3 ORDER BY name""")
                self.conn.commit()
                rows = self.cursor.fetchall()
                for row in rows : 
                    self.from_box.addItem(str(row[0]))
                    self.to_box.addItem(str(row[0]))
                self.cursor.execute("""SELECT distinct route_name FROM route where route_type = 3 ORDER BY route_name""")
                self.conn.commit()
                rows = self.cursor.fetchall()
                for row in rows : 
                    self.ligne_box.addItem(str(row[0]))
         if cnx.text() == "Tram":
            if cnx.isChecked() == True:
                checked = self.cursor.execute("""SELECT DISTINCT name FROM combined_projet, stations WHERE stop_I = combined_projet.from_stop AND route_type = 0 ORDER BY name""")
                self.conn.commit()
                rows = self.cursor.fetchall()
                for row in rows : 
                    self.from_box.addItem(str(row[0]))
                    self.to_box.addItem(str(row[0]))
                self.cursor.execute("""SELECT distinct route_name FROM route where route_type = 0 ORDER BY route_name""")
                self.conn.commit()
                rows = self.cursor.fetchall()
                for row in rows : 
                    self.ligne_box.addItem(str(row[0]))
         if cnx.text() == "Metro":
            if cnx.isChecked() == True:
                checked = self.cursor.execute("""SELECT DISTINCT name FROM combined_projet, stations WHERE stop_I = combined_projet.from_stop AND route_type = 1 ORDER BY name""")
                self.conn.commit()
                rows = self.cursor.fetchall()
                for row in rows : 
                    self.from_box.addItem(str(row[0]))
                    self.to_box.addItem(str(row[0]))
                self.cursor.execute("""SELECT distinct route_name FROM route where route_type = 1 ORDER BY route_name""")
                self.conn.commit()
                rows = self.cursor.fetchall()
                for row in rows : 
                    self.ligne_box.addItem(str(row[0]))
         if cnx.text() == "Train":
            if cnx.isChecked() == True:
                checked = self.cursor.execute("""SELECT DISTINCT name FROM combined_projet, stations WHERE stop_I = combined_projet.from_stop AND route_type = 2 ORDER BY name""")
                self.conn.commit()
                rows = self.cursor.fetchall()
                for row in rows : 
                    self.from_box.addItem(str(row[0]))
                    self.to_box.addItem(str(row[0]))
                self.cursor.execute("""SELECT distinct route_name FROM route where route_type = 2 ORDER BY route_name""")
                self.conn.commit()
                rows = self.cursor.fetchall()
                for row in rows : 
                    self.ligne_box.addItem(str(row[0]))


    # affichage du trajet quand on clique sur le tableau
    def table_Click(self):
        k = 0
        prev_lat = 0
        for col in self.rows[self.tableWidget.currentRow()] :
            if (k % 3) == 0:
                lst = col.split(',')
                lat = float(lst[0])
                lon = float(lst[1]) 

                if prev_lat != 0:
                    self.webView.addSegment( prev_lat, prev_lon, lat, lon )
                prev_lat = lat
                prev_lon = lon

                self.webView.addMarker( lat, lon )
            k = k + 1
        

    # fonction principal qui affiche le chemin de _fromstations à _tostations en fonction de _hops
    def button_Go(self):
        self.tableWidget.clearContents()

        _fromstations = str(self.from_box.currentText())
        _tostations = str(self.to_box.currentText())
        _hops = int(self.hop_box.currentText())
        _type = 5

        if self.check_boxbus.isChecked():
            _type = int("3")
        elif self.check_boxtram.isChecked():
            _type = int("0")
        elif self.check_boxmetro.isChecked():
            _type = int("1")
        elif self.check_boxtrain.isChecked():
            _type = int("2")            

        self.rows = []

        if _hops >= 1 :
            if _type == 5 : 
                self.cursor.execute(""f" with metros(geo_point_2d,nom_long,res_com) as (select distinct CONCAT(stations.lat,',',stations.lon) as ma,stations.name,route.route_name   from stations,route,combined_projet   where stations.stop_i=combined_projet.from_stop and route.route_i=combined_projet.route_i   order by stations.name ASC)  select distinct  A.geo_point_2d,A.nom_long, A.res_com,B.geo_point_2d,  B.nom_long from metros as B, metros as A  where A.nom_long = $${_fromstations}$$ AND B.nom_long =$${_tostations}$$ AND A.res_com = B.res_com""")
                self.conn.commit()
                self.rows += self.cursor.fetchall()
            else:
                self.cursor.execute(""f" with metros(geo_point_2d,nom_long,res_com) as (select distinct CONCAT(stations.lat,',',stations.lon) as ma,stations.name,route.route_name   from stations,route,combined_projet   where stations.stop_i=combined_projet.from_stop and route.route_i=combined_projet.route_i and combined_projet.route_type = {_type} and route.route_type = {_type} order by stations.name ASC)  select distinct  A.geo_point_2d,A.nom_long, A.res_com,B.geo_point_2d,  B.nom_long from metros as B, metros as A  where A.nom_long = $${_fromstations}$$ AND B.nom_long =$${_tostations}$$ AND A.res_com = B.res_com""")
                self.conn.commit()
                self.rows += self.cursor.fetchall()    

        if _hops >= 2 :
            if _type == 5: 
                self.cursor.execute(""f" with metros(geo_point_2d,nom_long,res_com) as   (select distinct CONCAT(stations.lat,',',stations.lon) as ma,stations.name,route.route_name  from stations,route,combined_projet   where stations.stop_i=combined_projet.from_stop and route.route_i=combined_projet.route_i   order by stations.name ASC) SELECT distinct A.geo_point_2d,A.nom_long, A.res_com,B.geo_point_2d,  B.nom_long, C.res_com,  D.geo_point_2d,D.nom_long FROM metros as A, metros as B, metros as C, metros as D WHERE A.nom_long =$${_fromstations}$$  AND D.nom_long =$${_tostations}$$ AND A.res_com = B.res_com AND B.nom_long = C.nom_long AND C.res_com = D.res_com AND A.res_com <> C.res_com AND A.nom_long <> B.nom_long AND B.nom_long <> D.nom_long""")
                self.conn.commit()
                self.rows += self.cursor.fetchall()
            else:
                self.cursor.execute(""f" with metros(geo_point_2d,nom_long,res_com) as   (select distinct CONCAT(stations.lat,',',stations.lon) as ma,stations.name,route.route_name  from stations,route,combined_projet   where stations.stop_i=combined_projet.from_stop and route.route_i=combined_projet.route_i and combined_projet.route_type = {_type} and route.route_type = {_type}  order by stations.name ASC) SELECT distinct A.geo_point_2d,A.nom_long, A.res_com,B.geo_point_2d,  B.nom_long, C.res_com,  D.geo_point_2d,D.nom_long FROM metros as A, metros as B, metros as C, metros as D WHERE A.nom_long =$${_fromstations}$$  AND D.nom_long =$${_tostations}$$ AND A.res_com = B.res_com AND B.nom_long = C.nom_long AND C.res_com = D.res_com AND A.res_com <> C.res_com AND A.nom_long <> B.nom_long AND B.nom_long <> D.nom_long""")
                self.conn.commit()
                self.rows += self.cursor.fetchall()   

        if _hops >= 3 : 
            if _type == 5:
                self.cursor.execute(""f" with metros(geo_point_2d,nom_long,res_com) as    (select distinct CONCAT(stations.lat,',',stations.lon) as ma,stations.name,route.route_name    from stations,route,combined_projet where stations.stop_i=combined_projet.from_stop and route.route_i=combined_projet.route_i   order by stations.name ASC) SELECT distinct  A.geo_point_2d,A.nom_long, A.res_com,B1.geo_point_2d,  B2.nom_long, B2.res_com,C2.geo_point_2d,  C2.nom_long, C2.res_com,D.geo_point_2d,  D.nom_long FROM metros as A, metros as B1, metros as B2, metros as C1, metros as C2, metros as D WHERE A.nom_long = $${_fromstations}$$  AND A.res_com = B1.res_com AND B1.nom_long = B2.nom_long AND B2.res_com = C1.res_com AND C1.nom_long = C2.nom_long AND C2.res_com = D.res_com AND D.nom_long =$${_tostations}$$ AND A.res_com <> B2.res_com AND B2.res_com <> C2.res_com AND A.res_com <> C2.res_com AND A.nom_long <> B1.nom_long AND B2.nom_long <> C1.nom_long AND C2.nom_long <> D.nom_long""")
                self.conn.commit()
                self.rows += self.cursor.fetchall()
            else:
                self.cursor.execute(""f" with metros(geo_point_2d,nom_long,res_com) as    (select distinct CONCAT(stations.lat,',',stations.lon) as ma,stations.name,route.route_name    from stations,route,combined_projet where stations.stop_i=combined_projet.from_stop and route.route_i=combined_projet.route_i and combined_projet.route_type = {_type} and route.route_type = {_type}  order by stations.name ASC) SELECT distinct  A.geo_point_2d,A.nom_long, A.res_com,B1.geo_point_2d,  B2.nom_long, B2.res_com,C2.geo_point_2d,  C2.nom_long, C2.res_com,D.geo_point_2d,  D.nom_long FROM metros as A, metros as B1, metros as B2, metros as C1, metros as C2, metros as D WHERE A.nom_long = $${_fromstations}$$  AND A.res_com = B1.res_com AND B1.nom_long = B2.nom_long AND B2.res_com = C1.res_com AND C1.nom_long = C2.nom_long AND C2.res_com = D.res_com AND D.nom_long =$${_tostations}$$ AND A.res_com <> B2.res_com AND B2.res_com <> C2.res_com AND A.res_com <> C2.res_com AND A.nom_long <> B1.nom_long AND B2.nom_long <> C1.nom_long AND C2.nom_long <> D.nom_long""")
                self.conn.commit()
                self.rows += self.cursor.fetchall()    

        if len(self.rows) == 0 : 
            #Ecriture du resultat sur le terminal
            print("AUCUN RESULTAT !!!!!")
            self.tableWidget.setRowCount(0)
            self.tableWidget.setColumnCount(0)
            return

        numrows = len(self.rows)
        numcols = len(self.rows[-1]) - math.floor(len(self.rows[-1]) / 3.0) - 1 
        self.tableWidget.setRowCount(numrows)
        self.tableWidget.setColumnCount(numcols)

        i = 0
        for row in self.rows : 
            j = 0
            k = 0 
            for col in row :
                if j % 3 == 0 : 
                    k = k + 1
                else : 
                    self.tableWidget.setItem(i, j-k, QTableWidgetItem(str(col)))
                j = j + 1
            i = i + 1

        header = self.tableWidget.horizontalHeader()
        j = 0
        while j < numcols : 
            header.setSectionResizeMode(j, QHeaderView.ResizeToContents)
            j = j+1
        
        self.update()	

    # fonction qui reset la fenetre si on clique sur le bouton clear
    def button_Clear(self):
        self.webView.clearMap(self.maptype_box.currentIndex())

        self.ligne_box.clear()
        self.from_box.clear()
        self.to_box.clear()

        if self.check_boxbus.isChecked():
            self.check_boxbus.setChecked(False)
        if self.check_boxmetro.isChecked():
            self.check_boxmetro.setChecked(False)
        if self.check_boxtrain.isChecked():
            self.check_boxtrain.setChecked(False)
        if self.check_boxtram.isChecked():
            self.check_boxtram.setChecked(False)
        if self.check_boxtout.isChecked():
            self.check_boxtout.setChecked(False)    

        self.tableWidget.clear()
        self.startingpoint = True
        
        self.cursor.execute("""with metros(geo_point_2d,nom_long,res_com) as
    (select distinct CONCAT(stations.lat,',',stations.lon) as ma,stations.name,route.route_name
    from stations,route,combined_projet
    where stations.stop_i=combined_projet.from_stop and route.route_i=combined_projet.route_i
    order by stations.name ASC) SELECT distinct nom_long FROM metros ORDER BY nom_long""")
        self.conn.commit()
        rows = self.cursor.fetchall()

        for row in rows : 
            self.from_box.addItem(str(row[0]))
            self.to_box.addItem(str(row[0]))
        self.update()

    # fonction qui determine la stations la plus proche du clic sur la carte
    def mouseClick(self, lat, lng):
        self.webView.addPointMarker(lat, lng)

        print(f"Clicked on: latitude {lat}, longitude {lng}")
        self.cursor.execute(""f"WITH mytable (distance, name) AS (SELECT ( ABS(stations.lat-{lat}) + ABS(stations.lon-{lng}) ), stations.name FROM stations) SELECT A.name FROM mytable as A WHERE A.distance <=  (SELECT min(B.distance) FROM mytable as B)  """)
        self.conn.commit()
        rows = self.cursor.fetchall()
        #print('Closest stations is: ', rows[0][0])
        if self.startingpoint :
            self.from_box.setCurrentIndex(self.from_box.findText(rows[0][0], Qt.MatchFixedString))
        else :
            self.to_box.setCurrentIndex(self.to_box.findText(rows[0][0], Qt.MatchFixedString))
        self.startingpoint = not self.startingpoint

    
    # fonction qui affiche les gares qui utilisent la ligne _ligne 
    def button_Show(self):
        self.tableWidget.clearContents()
        _ligne = str(self.ligne_box.currentText())
        _type = 5
        if self.check_boxbus.isChecked():
            _type = 3
        elif self.check_boxtram.isChecked():
            _type = 0
        elif self.check_boxmetro.isChecked():
            _type = 1
        elif self.check_boxtrain.isChecked():
            _type = 2
        print(_type)
        self.rows = []
        self.cursor.execute(""f" select distinct name, s.lat ,s.lon from route as r, combined_projet as c, stations as s where r.route_name = $${_ligne}$$ and r.route_i=c.route_i and c.from_stop=s.stop_i;""")

        self.conn.commit()
        self.rows += self.cursor.fetchall()
        if len(self.rows) == 0 : 
            self.tableWidget.setRowCount(0)
            self.tableWidget.setColumnCount(0)
            return
        numrows = len(self.rows)
        numcols = 1
        
        self.tableWidget.setRowCount(numrows)
        self.tableWidget.setColumnCount(numcols)
        k = 0
        prev_lat = 0
        for i in range(0, len(self.rows)) :
            print(self.rows[i][0])
            self.tableWidget.setItem(i, 0, QTableWidgetItem(str(self.rows[i][0])))
            lat = self.rows[i][1]
            lon = self.rows[i][2]
            prev_lat = lat
            prev_lon = lon
            self.webView.addMarker( lat, lon )
        header = self.tableWidget.horizontalHeader()
        j = 0
        while j < numcols : 
            header.setSectionResizeMode(j, QHeaderView.ResizeToContents)
            j = j+1
        
        self.update()

class myWebView (QWebEngineView):
    def __init__(self):
        super().__init__()

        self.maptypes = ["OpenStreetMap", "Stamen Terrain", "stamentoner", "cartodbpositron"]
        self.setMap(0)


    def add_customjs(self, map_object):
        my_js = f"""{map_object.get_name()}.on("click",
                 function (e) {{
                    var data = `{{"coordinates": ${{JSON.stringify(e.latlng)}}}}`;
                    console.log(data)}}); """
        e = Element(my_js)
        html = map_object.get_root()
        html.script.get_root().render()
        html.script._children[e.get_name()] = e

        return map_object


    def handleClick(self, msg):
        data = json.loads(msg)
        lat = data['coordinates']['lat']
        lng = data['coordinates']['lng']


        window.mouseClick(lat, lng)


    def addSegment(self, lat1, lng1, lat2, lng2):
        js = Template(
        """
        L.polyline(
            [ [{{latitude1}}, {{longitude1}}], [{{latitude2}}, {{longitude2}}] ], {
                "color": "red",
                "opacity": 1.0,
                "weight": 4,
                "line_cap": "butt"
            }
        ).addTo({{map}});
        """
        ).render(map=self.mymap.get_name(), latitude1=lat1, longitude1=lng1, latitude2=lat2, longitude2=lng2 )

        self.page().runJavaScript(js)


    def addMarker(self, lat, lng):
        js = Template(
        """
        L.marker([{{latitude}}, {{longitude}}] ).addTo({{map}});
        L.circleMarker(
            [{{latitude}}, {{longitude}}], {
                "bubblingMouseEvents": true,
                "color": "#3388ff",
                "popup": "hello",
                "dashArray": null,
                "dashOffset": null,
                "fill": false,
                "fillColor": "#3388ff",
                "fillOpacity": 0.2,
                "fillRule": "evenodd",
                "lineCap": "round",
                "lineJoin": "round",
                "opacity": 1.0,
                "radius": 2,
                "stroke": true,
                "weight": 5
            }
        ).addTo({{map}});
        """
        ).render(map=self.mymap.get_name(), latitude=lat, longitude=lng)
        self.page().runJavaScript(js)


    def addPointMarker(self, lat, lng):
        js = Template(
        """
        L.circleMarker(
            [{{latitude}}, {{longitude}}], {
                "bubblingMouseEvents": true,
                "color": 'green',
                "popup": "hello",
                "dashArray": null,
                "dashOffset": null,
                "fill": false,
                "fillColor": 'green',
                "fillOpacity": 0.2,
                "fillRule": "evenodd",
                "lineCap": "round",
                "lineJoin": "round",
                "opacity": 1.0,
                "radius": 2,
                "stroke": true,
                "weight": 5
            }
        ).addTo({{map}});
        """
        ).render(map=self.mymap.get_name(), latitude=lat, longitude=lng)
        self.page().runJavaScript(js)


    def setMap (self, i):
        self.mymap = folium.Map(location=[48.8619, 2.3519], tiles=self.maptypes[i], zoom_start=12, prefer_canvas=True)

        self.mymap = self.add_customjs(self.mymap)

        page = WebEnginePage(self)
        self.setPage(page)

        data = io.BytesIO()
        self.mymap.save(data, close_file=False)

        self.setHtml(data.getvalue().decode())

    def clearMap(self, index):
        self.setMap(index)



class WebEnginePage(QWebEnginePage):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def javaScriptConsoleMessage(self, level, msg, line, sourceID):
        #print(msg)
        if 'coordinates' in msg:
            self.parent.handleClick(msg)


       
			
if __name__ == '__main__':
    app = QApplication(sys.argv) 
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
