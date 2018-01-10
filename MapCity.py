'''
Created on Nov 20, 2017

@author: Nick
'''
import fiona
import numpy as np
import pandas as pd
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon
from shapely.prepared import prep
from matplotlib.collections import PatchCollection
from descartes import PolygonPatch
from math import sin, cos, sqrt, atan2, radians
import matplotlib.pyplot as plt
import datetime

class MapCity(object):
    '''
    classdocs
    '''


    def __init__(self, shapefile):
        '''
        Constructor
        '''
        
        self.processShapeFile(shapefile)
        
    
    def processShapeFile(self, shapefile):
        
        shp = fiona.open(shapefile+'.shp')
        self.coords = shp.bounds
        shp.close()
        self.w, self.h = self.coords[2] - self.coords[0], self.coords[3] - self.coords[1] 
        extra = .01 
        self.m = Basemap(projection='tmerc', ellps='WGS84',lon_0=np.mean([self.coords[0], self.coords[2]]),
                    lat_0=np.mean([self.coords[1], self.coords[3]]),llcrnrlon=self.coords[0] - extra * self.w,
                    llcrnrlat=self.coords[1] - (extra * self.h), urcrnrlon=self.coords[2] + extra * self.w,
                    urcrnrlat=self.coords[3] + (extra * self.h),resolution='i',  suppress_ticks=True)
        
        self.m.readshapefile(shapefile, name='seattle', drawbounds=False, color='none', zorder=2)
        
        self.df_map = pd.DataFrame({
            'poly': [Polygon(hood_points) for hood_points in self.m.seattle],
            'name': [hood['S_HOOD'] for hood in self.m.seattle_info]
        })
        self.hood_polygons = prep(MultiPolygon(list(self.df_map['poly'].values)))
        
    def addDataSet(self, fileName, fileType):
        if (fileType == 'json'):
            import json
            with open(fileName + '.json', 'r') as fh:
                raw = json.loads(fh.read())

            self.ld = pd.DataFrame(raw['locations'])
            
            del raw #free up some memory
            self.ld['latitudeE7'] = self.ld['latitudeE7']/float(1e7) 
            self.ld['longitudeE7'] = self.ld['longitudeE7']/float(1e7)
            self.ld['timestampMs'] = self.ld['timestampMs'].map(lambda x: float(x)/1000) #to seconds
            self.ld['datetime'] = self.ld.timestampMs.map(datetime.datetime.fromtimestamp)
            
            
            # Rename fields based on the conversions we just did
            self.ld.rename(columns={'latitudeE7':'latitude', 'longitudeE7':'longitude', 'timestampMs':'timestamp'}, inplace=True)
            self.ld = self.ld[self.ld.datetime >  datetime.date(2013, 1, 1)]
            self.ld = self.ld[self.ld.accuracy < 100] #Ignore locations with accuracy estimates over 1000m
            self.mapped_points = [Point(self.m(mapped_x, mapped_y)) for mapped_x, mapped_y in zip(self.ld['longitude'], self.ld['latitude'])]

            self.ld.reset_index(drop=True, inplace=True)
            
        elif(fileType == 'csv'):
            self.ld = pd.read_csv(fileName + '.csv')
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
            self.ld.rename(columns={'Latitude':'latitude', 'Longitude':'longitude'},inplace=True)
            self.ld = self.ld[(self.ld['Summarized Offense Description'] == 'MAIL THEFT') & (self.ld['Year'] == 2015)]
            self.mapped_points = [Point(self.m(mapped_x, mapped_y)) for mapped_x, mapped_y in zip(self.ld['longitude'], self.ld['latitude'])]
            
        all_points = MultiPoint(self.mapped_points)
        self.city_points = [point for point in all_points if self.hood_polygons.contains(point)]
        self.hoodCount()
      
    def num_of_contained_points(self, apolygon, city_points):
        numPointsinPoly = [point for point in city_points if prep(apolygon).contains(point)]
        return len(numPointsinPoly)
            
    def hoodCount(self):
        self.df_map['hood_count'] = self.df_map['poly'].apply(self.num_of_contained_points, args=(self.city_points,)) 

    def calcDistance(self,lat1,lon1,lat2,lon2):
# approximate radius of earth in km
        R = 6373.0       
        lat1 = radians(lat1)
        lon1 = radians(lon1)
        lat2 = radians(lat2)
        lon2 = radians(lon2)        
        dlon = lon2 - lon1
        dlat = lat2 - lat1       
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))       
        distance = R * c
        return distance
    
    def changeToDateTime(self):
        self.ld['datetime'] = [datetime.datetime.strptime(time, '%m/%d/%Y %I:%M:%S %p') for time in self.ld['Occurred Date or Date Range Start']]
        
        self.ld['low_datetime'] = [time - datetime.timedelta(minutes=30) for time in self.ld['datetime']]
        self.ld['high_datetime'] = [time + datetime.timedelta(minutes=30) for time in self.ld['datetime']]
    def scatterPlot(self):
        
        plt.clf()
        fig = plt.figure()
        ax = fig.add_subplot(111, axisbg='w', frame_on=False)
        dev = self.m.scatter([geom.x for geom in self.city_points],[geom.y for geom in self.city_points],5, marker='o', lw=.25,
              facecolor='#33ccff', edgecolor='w',alpha=0.9, antialiased=True,label='Crime Incident Locations', zorder=3)
        
        self.df_map['patches'] = self.df_map['poly'].map(lambda x: PolygonPatch(x,fc='#555555',ec='#787878', lw=.25, alpha=.9,zorder=4))
        ax.add_collection(PatchCollection(self.df_map['patches'].values, match_original=True))
        self.m.drawmapscale(self.coords[0] + 0.08, self.coords[1] + 0.015,self.coords[0], self.coords[1],10.,barstyle='fancy', labelstyle='simple',
                       fillcolor1='w', fillcolor2='#555555',fontcolor='#555555',zorder=5)
        
        plt.title("Crime Incident Locations, Seattle")
        plt.tight_layout()
        # this will set the image width to 722px at 100dpi
        fig.set_size_inches(7.22, 5.25)
        plt.savefig('seattle_crimes.png', dpi=100, alpha=True)
        plt.show()
        
        
    def plotHexBin(self, color, title):
        
        figwidth = 16
        fig = plt.figure(figsize=(figwidth, figwidth*self.h/self.w), facecolor='#878585')
        ax = fig.add_subplot(111, frame_on=False)

# draw neighborhood patches from polygons
        self.df_map['patches'] = self.df_map['poly'].map(lambda x: PolygonPatch(
            x, fc='#555555', ec='#555555', lw=1, alpha=1, zorder=0))
        # plot neighborhoods by adding the PatchCollection to the axes instance
        ax.add_collection(PatchCollection(self.df_map['patches'].values, match_original=True))
        
        # the mincnt argument only shows cells with a value >= 1
        # The number of hexbins you want in the x-direction
        numhexbins = 50
        hx = self.m.hexbin(
            np.array([geom.x for geom in self.city_points]),
            np.array([geom.y for geom in self.city_points]),
            gridsize=(numhexbins, int(numhexbins*self.h/self.w)), #critical to get regular hexagon, must stretch to map dimensions
            bins='log', mincnt=1, edgecolor='none', alpha=1.,
            cmap=plt.get_cmap(color))
        
        # Draw the patches again, but this time just their borders (to achieve borders over the hexbins)
        self.df_map['patches'] = self.df_map['poly'].map(lambda x: PolygonPatch(
            x, fc='none', ec='#FFFF99', lw=1, alpha=1, zorder=1))
        ax.add_collection(PatchCollection(self.df_map['patches'].values, match_original=True))
        
        # Draw a map scale
        self.m.drawmapscale(((self.coords[0] + self.coords[2])/ 2 + .01), self.coords[1],
            self.coords[0], self.coords[1], 4.,
            units='mi', barstyle='fancy', labelstyle='simple',
            fillcolor1='w', fillcolor2='#555555', fontcolor='#555555',
            zorder=5, fontsize = 18)
        
        ax.set_title(title, fontsize = 30)
        
        
        plt.savefig(color + '.png', dpi=300, frameon=False, bbox_inches='tight', facecolor='#dedede')
        plt.show()
       
# test = MapCity('Neighborhoods/WGS84/Neighborhoods')
# test.calcDistance(47.655789, -122.348186, 47.654058, -122.352195)
# test.addDataSet('Takeout/Location History/Location History','json')
# test.plotHexBin('Reds', 'My Location Data Across Seattle')   
# 
# crimeVar = 'ASSAULT'   
# test1 = MapCity('Neighborhoods/WGS84/Neighborhoods')
# test1.addDataSet('Seattle_Police_Department_Police_Report_Incident','csv')
# test1.plotHexBin('Blues', crimeVar + ' Incidents Across Seattle in 2015')  


