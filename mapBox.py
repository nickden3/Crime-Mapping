'''
Created on Jan 4, 2018

@author: nick
'''

import plotly.plotly as py
from plotly.graph_objs import *
import pandas as pd
import plotly.offline
import json
import datetime
import numpy
# mapbox_access_token = 'ADD_YOUR_TOKEN_HERE'



class mapBox(object):
    '''
    classdocs
    '''


    def __init__(self, title):
        '''
        Constructor
        '''
        self.title = title
        
        self.mapbox_access_token = 'pk.eyJ1Ijoibmlja2RlbjMiLCJhIjoiY2piZ3QzemRkMzR0bzJ3bnpvd3NjM24xOCJ9.D4ZE4HMSfjsbk4lsiAqenA'
    
    def readCrimes(self, file, crime):
        self.crime = crime
        
        self.ld = pd.read_csv(file + '.csv')
        
        """['BURGLARY-SECURE PARKING-RES' 'SHOPLIFTING' 'OTHER PROPERTY''VEHICLE THEFT' 'BURGLARY' 'ROBBERY' 'PROPERTY DAMAGE' 'WEAPON' 'ASSAULT'
         'WARRANT ARREST' 'CAR PROWL' 'THREATS' 'NARCOTICS' 'MAIL THEFT'
         'THEFT OF SERVICES' 'HOMICIDE' 'LOST PROPERTY' 'EMBEZZLE' 'BIKE THEFT'
         'TRESPASS' 'STOLEN PROPERTY' 'COUNTERFEIT' 'ANIMAL COMPLAINT' 'ELUDING'
         'FRAUD' 'PICKPOCKET' 'DISTURBANCE' 'VIOLATION OF COURT ORDER'
         'PURSE SNATCH' 'DISPUTE' 'FORGERY' 'ILLEGAL DUMPING' 'TRAFFIC' 'LOITERING'
         'PROSTITUTION' 'OBSTRUCT' 'RECKLESS BURNING' 'FALSE REPORT' 'DUI'
         'RECOVERED PROPERTY' 'FIREWORK' 'INJURY' 'EXTORTION' 'BIAS INCIDENT'
         'ESCAPE' 'LIQUOR VIOLATION' 'PUBLIC NUISANCE' 'FRAUD AND FINANCIAL'
         'STAY OUT OF AREA OF DRUGS' 'DISORDERLY CONDUCT' 'PORNOGRAPHY'
         '[INC - CASE DC USE ONLY]' 'GAMBLE' 'STAY OUT OF AREA OF PROSTITUTION'
         'HARBOR CALLS' 'HARBOR CALLs' 'METRO']"""
        
        self.years = range(2014, 2018)

        #self.ld = self.ld[(self.ld['Summarized Offense Description'] == self.crime) & (self.ld['Year'] == self.year)]
        self.ld = self.ld[self.ld['Year'] > 2013]
        self.ld = [self.ld[(self.ld['Summarized Offense Description'] == self.crime) & (self.ld['Year'] == year)] for year in self.years]
    
    def readMyLocation(self, fileName):
        
        with open(fileName, 'r') as fh:
            raw = json.loads(fh.read())

        self.ld = pd.DataFrame(raw['locations'])
        
        del raw #free up some memory
        self.ld['latitudeE7'] = self.ld['latitudeE7']/float(1e7) 
        self.ld['longitudeE7'] = self.ld['longitudeE7']/float(1e7)
        self.ld['timestampMs'] = self.ld['timestampMs'].map(lambda x: float(x)/1000) #to seconds
        self.ld['datetime'] = self.ld.timestampMs.map(datetime.datetime.fromtimestamp)
        
        
        # Rename fields based on the conversions we just did
        self.ld.rename(columns={'latitudeE7':'Latitude', 'longitudeE7':'Longitude', 'timestampMs':'timestamp'}, inplace=True)
        print(self.ld['Latitude'])
        self.ld['Year'] = self.ld['datetime'].dt.year
        self.ld = self.ld[self.ld.datetime >  datetime.date(2013, 1, 1)]
        self.ld = self.ld[self.ld.accuracy < 100] #Ignore locations with accuracy estimates over 1000m
        self.years = self.ld['Year'].unique()
        print(self.years)
        self.years = numpy.sort(self.years)
        print(self.years)
        self.ld = [self.ld[(self.ld['Year'] == year)] for year in self.years]
        
    def plot(self):
        
        data= []
        i = 0
        for i in range(len(self.years)):
            
            data.append(Scattermapbox(
                lat = self.ld[i]['Latitude'],
                lon = self.ld[i]['Longitude'],
                mode='markers',
                marker=Marker(size=8, opacity = .3),
                text=['Test Map'],
                name = self.years[i]))
            
      
        steps = []
        for i in range(len(data)):
            step = dict(
                method = 'restyle',  
                args = ['visible', [False] * len(data) ],
                label = self.years[i]
            )
            step['args'][1][i] = True # Toggle i'th trace to "visible"
            steps.append(step)
        
        sliders = [ dict(
            active = 10,
            currentvalue = {"prefix": "Year: "},
            pad = {"t": 50},
            steps = steps
        ) ]  
        updatemenus = list([
        dict(active = 0,
        buttons=list([
            dict(
                args=['mapbox.style', 'basic'],
                label='Map',
                method='relayout'
            ),
            dict(
                args=['mapbox.style', 'satellite-streets'],
                label='Satellite',
                method='relayout'
            ),
            dict(
                args=['mapbox.style', 'dark'],
                label='Dark',
                method='relayout'
            )               
        ])
        )])
       
        
        
    
        layout = Layout(
            title = self.title,
            autosize=True,
            hovermode='closest',
            sliders = sliders,
            updatemenus = updatemenus,
            mapbox=dict(
                accesstoken=self.mapbox_access_token,
                bearing=0,
                center=dict(
                    lat=self.ld[-1]['Latitude'].mean(),
                    lon=self.ld[-1]['Longitude'].mean()
                ),
                pitch=0,
                zoom=10,
                style = 'basic'
            ),
        )
        
        
        
        
        
         
      
        
        fig = dict(data=data, layout=layout)
        plotly.offline.plot(fig, filename=self.title + '.html')
     
# test = mapBox()   
# test.readCrimes('Seattle_Police_Department_Police_Report_Incident', 'ASSAULT')
# test.plot()
# 
# test2 = mapBox()
# test2.readCrimes('Seattle_Police_Department_Police_Report_Incident', 'ROBBERY')
# test2.plot()

test3 = mapBox('My Location Data')
test3.readMyLocation('Takeout/Location History/Location History.json')
test3.plot()


        