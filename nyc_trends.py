# -*- coding: utf-8 -*-
# Generate some choropleths showing cv-19 data for NYC's zip codes
# Ben Fried / ben.fried@gmail.com / bf@google.com
# January 2021
# REQUIREMENTS:
# Only tested with python 3.7+
# recent versions of pandas, numpy, plotly
# You may need to run
# pip[3] install -U plotly pandas numpy 


# Data comes from the NYC department of health and is loaded from their github repo at runtime. 
# Outputs HTML files, one for each choropleth -
#    trailingweekaverage.html
#    casesper100k_anim.html
#    testsper100k_anim.html
#    pctpositive_anim.html
#    percent_positive_last_week.html
# Output html files go into the current working directory (.) or into the value of the -o / --output argument

# This started as a jupyter notebook I was using to do some interactive analysis.
# Original file (from which this has diverged significantly) is located at
#    https://colab.research.google.com/drive/1nGpTtx-C3NRthYWSgug7y2gjBNnPFhXf


from pandas.plotting import register_matplotlib_converters
import pandas as pd
import numpy as np
import datetime
import re
import plotly
import plotly.express as px
import json
from packaging import version
import argparse


OUTPUT_DIRECTORY="."

if version.parse(plotly.__version__) < version.parse('4.14'):
  print("Plotly is out of date. Please update")
  #!pip install -U plotly
  exit(1)
  #import plotly

ap = argparse.ArgumentParser()
ap.add_argument('--output', '-o')
args = ap.parse_args()

if args.output != None:
  print("Changing output directory to {}".format(args.output))
  OUTPUT_DIRECTORY=args.output

# This dataset is percent of people tested who tested positive

pp_trends_df = pd.read_csv("https://raw.githubusercontent.com/nychealth/coronavirus-data/master/trends/percentpositive-by-modzcta.csv")

# We know that it's only percent positive info, so remove that from column names.
pp_trends_df = pp_trends_df.rename(columns = lambda x: re.sub('PCTPOS_','',x))

# clean up data, extract last week's info, reshape

# First, convert week ending field to an actual date and make it be the index
pp_trends_df.week_ending = pd.to_datetime(pp_trends_df.week_ending)
pp_trends_df.index = pp_trends_df.week_ending

# Use ```iloc[[-1]]``` to get the last row, which will be last week's data

last_week_series = pp_trends_df.iloc[[-1]]

# Now remove the borough summary fields; for a choropleth we only want the zipcode (well, modzcta) data

last_week_series = last_week_series.iloc[:,7:]
last_week = last_week_series.reset_index().week_ending[0].strftime('%Y-%m-%d')

zip_series = last_week_series.T
zip_series = zip_series.reset_index()
zip_series.columns = ['MODZCTA', 'Percent Positive']

import requests
content = requests.get("https://raw.githubusercontent.com/nychealth/coronavirus-data/master/Geography-resources/MODZCTA_2010_WGS1984.geo.json")
j = json.loads(content.content)

fig = px.choropleth_mapbox(zip_series, geojson=j, locations="MODZCTA", featureidkey='properties.MODZCTA', color="Percent Positive", color_continuous_scale="orrd", 
                           mapbox_style="carto-positron", zoom=10, center={"lat": 40.7, "lon": -73.9}, title="Percent Positive last week",
                           opacity=0.7)

fig.write_html("{}/{}".format(OUTPUT_DIRECTORY, "percent_positive_last_week.html"))


# Percent positivity animation

pp_trends_df = pp_trends_df.iloc[:,7:]
pp_trends_df = pp_trends_df.reset_index()

pp2_df = pp_trends_df.melt(id_vars=['week_ending'], value_vars=pp_trends_df.columns[1:], var_name='MODZCTA', value_name="Percent_Positive")
pp2_df["week"] = pp2_df.week_ending.dt.strftime('%Y-%m-%d')

nfig = px.choropleth_mapbox(pp2_df, geojson=j, locations="MODZCTA", featureidkey='properties.MODZCTA', color="Percent_Positive", color_continuous_scale="orrd", 
                           mapbox_style="carto-positron", zoom=10, center={"lat": 40.7, "lon": -73.9}, animation_frame = "week",
                           opacity=0.7, title="Percent of positive tests by week",range_color=[0,15])

nfig.write_html("{}/{}".format(OUTPUT_DIRECTORY, "pctpositive_anim.html"),auto_play=False)


# Test rate animation

tr_df = pd.read_csv("https://raw.githubusercontent.com/nychealth/coronavirus-data/master/trends/testrate-by-modzcta.csv")

tr_df = tr_df.rename(columns = lambda x: re.sub('TESTRATE_','',x))
tr_df.week_ending = pd.to_datetime(tr_df.week_ending)
tr_df.index = tr_df.week_ending
tr_df = tr_df.iloc[:,7:]

tr_df = tr_df.reset_index()
tr2_df = tr_df.melt(id_vars=['week_ending'], value_vars=tr_df.columns[1:], var_name='MODZCTA', value_name="Tests_per_100k")
tr2_df["week"] = tr2_df.week_ending.dt.strftime('%Y-%m-%d')

nfig2 = px.choropleth_mapbox(tr2_df, geojson=j, locations="MODZCTA", featureidkey='properties.MODZCTA', color="Tests_per_100k", color_continuous_scale="orrd", 
                           mapbox_style="carto-positron", zoom=10, center={"lat": 40.7, "lon": -73.9}, animation_frame = "week",
                           opacity=0.7, title="Tests per hundred thousand people in ZIP Code", range_color=[tr2_df.Tests_per_100k.min(),tr2_df.Tests_per_100k.max()])
nfig2.write_html("{}/{}".format(OUTPUT_DIRECTORY,"testsper100k_anim.html"),auto_play=False)


# cases per 100k population animation

cr_df = pd.read_csv('https://raw.githubusercontent.com/nychealth/coronavirus-data/master/trends/caserate-by-modzcta.csv')

cr_df = cr_df.rename(columns = lambda x: re.sub('CASERATE_','',x))
cr_df.week_ending = pd.to_datetime(cr_df.week_ending)
cr_df.index = cr_df.week_ending
cr_df = cr_df.iloc[:,7:]
cr_df = cr_df.reset_index()
cr2_df = cr_df.melt(id_vars=['week_ending'], value_vars=cr_df.columns[1:], var_name='MODZCTA', value_name="Cases_per_100k")
cr2_df["week"] = cr2_df.week_ending.dt.strftime('%Y-%m-%d')

nfig3 = px.choropleth_mapbox(cr2_df, geojson=j, locations="MODZCTA", featureidkey='properties.MODZCTA', color="Cases_per_100k", color_continuous_scale="orrd", 
                           mapbox_style="carto-positron", zoom=10, center={"lat": 40.7, "lon": -73.9}, animation_frame = "week",
                           opacity=0.7, title="Cases per 100,000 people in the ZIP Code", range_color=[cr2_df.Cases_per_100k.min(),cr2_df.Cases_per_100k.max()])
nfig3.write_html("{}/{}".format(OUTPUT_DIRECTORY, "casesper100k_anim.html"),auto_play=False)


# last 7 days summary info 

latest_df = pd.read_csv("https://raw.githubusercontent.com/nychealth/coronavirus-data/master/latest/last7days-by-modzcta.csv")

latest_df["zipname"] = latest_df.modzcta.astype(str) + ': ' + latest_df.modzcta_name

title="7 day average Covid Testing update for " + latest_df.daterange.iloc[0]

nfig4 = px.choropleth_mapbox(latest_df, geojson=j, locations="modzcta", featureidkey='properties.MODZCTA', color="percentpositivity_7day", color_continuous_scale="orrd", 
                           mapbox_style="carto-positron", zoom=10, center={"lat": 40.7, "lon": -73.9}, 
                           opacity=0.7, title=title, hover_name="zipname",hover_data=["percentpositivity_7day", "people_tested", "people_positive", "median_daily_test_rate"],
                           range_color=[latest_df.percentpositivity_7day.min(),latest_df.percentpositivity_7day.max()])
nfig4.write_html("{}/{}".format(OUTPUT_DIRECTORY, "trailingweekaverage.html"))
