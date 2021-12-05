import streamlit as st

import pandas as pd
import seaborn as sns
from datetime import datetime
import math
import base64
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import plotly.express as px

import ml_segmenting_function_taxi 

def filedownload(df, date_from, date_to, filename):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # strings <-> bytes conversions
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}_{str(date_from)}_{str(date_to)}.csv">Download CSV File</a>'
    return href


st.title('Chicago Taxi - Customer Segmentation') 

st.markdown("""
This app performs customer segmentation for the given data! 
* **🐍 Python libraries:** base64, pandas, streamlit, numpy, matplotlib, seaborn, plotly
* Dataset source: https://data.cityofchicago.org/Transportation/Taxi-Trips-2020/r2u4-wwk3
""")

used_columns = ['Taxi ID', 'Trip Start Timestamp', 'Trip Seconds', 'Trip Miles', 'Fare', 'Tips', 'Trip Total']  
taxi_dataset = pd.read_csv("dataset/Taxi_Trips_-_2020.csv", usecols=used_columns) 
st.write("Total number of drivers: {:,}".format(taxi_dataset['Taxi ID'].nunique()))  

taxi_dataset['Trip Start Timestamp'] = taxi_dataset['Trip Start Timestamp'].astype('datetime64[ns]') 
# taxi_dataset['TotalPrice'] = taxi_dataset['Quantity']*shop_dataset['UnitPrice'] 

date_from = st.date_input("Date From: ", taxi_dataset['Trip Start Timestamp'].min())
date_to   = st.date_input("Date To: "  , taxi_dataset['Trip Start Timestamp'].max())

st.dataframe(taxi_dataset.head(100))

taxi_dataset = taxi_dataset[(taxi_dataset['Trip Start Timestamp'] >= str(date_from)) & (taxi_dataset['Trip Start Timestamp'] <= str(date_to))]

number_of_cluster = st.slider('Enter number of clusters:', 0, 20, 5)

model_type = st.radio("Segmentation model: ", ('RFM', 'RFAC'))

clientRFMsDF, segmentShareDF = ml_segmenting_function_taxi.segment_users(taxi_dataset[:], number_of_cluster, model_type) 

st.header('Statistics of Segmentation')
st.dataframe(segmentShareDF.style.highlight_max(axis=0)) 
st.write("Number of Taxi Drivers: {:,}".format(clientRFMsDF.shape[0]))  

 
fig = px.pie(segmentShareDF, values='Share (%)', names='Segments', title='Customer Segmentation (Pie)')
st.plotly_chart(fig) 

fig_barchart = px.bar(segmentShareDF, x='Count', y='Segments',  title='Customer Segmentation (BarChart)') 
st.plotly_chart(fig_barchart)

for i in range(0, number_of_cluster):
    st.header("Segment: Group {}".format(i)) 
    segmentRides = taxi_dataset[taxi_dataset['Taxi ID'].isin(clientRFMsDF[clientRFMsDF.Segment == i].TaxiID)] 

    st.write("🙎‍♂🙍‍♀️ Number of Customers: {:,} ({}% - Total Customers: {:,})".format(segmentRides['Taxi ID'].nunique(), 
            round(segmentRides['Taxi ID'].nunique()/taxi_dataset['Taxi ID'].nunique()*100,2), taxi_dataset['Taxi ID'].nunique()))

    st.write("🚕 Number of Rides: {:,} ({}% - Total Rides: {:,})".format(segmentRides.shape[0], round(segmentRides.shape[0]/taxi_dataset.shape[0]*100, 2), taxi_dataset.shape[0]))
    st.write("💵 Revenue: {:,} ({}% - Total Revenue: {:,})".format(round(segmentRides['Trip Total'].sum(),2), 
    	round(segmentRides['Trip Total'].sum()/taxi_dataset['Trip Total'].sum()*100, 2), round(taxi_dataset['Trip Total'].sum(), 2)))

    if segmentRides['Trip Total'].mean() > taxi_dataset['Trip Total'].mean(): 
        st.write("💵 Average Trip Cost: ${:,} (Average for all: {:,} 👍)".format(round(segmentRides['Trip Total'].mean(), 2), round(taxi_dataset['Trip Total'].mean(),2))) 
    else: 
        st.write("💵 Average Spending: ${:,} (Average for all: {:,} 👎)".format(round(segmentRides['Trip Total'].mean(), 2), round(taxi_dataset['Trip Total'].mean(),2))) 

    if segmentRides['Trip Miles'].mean() > taxi_dataset['Trip Miles'].mean(): 
        st.write("🏁 Average Trip Miles: {:,} (Average for all: {:,} 👍)".format(round(segmentRides['Trip Miles'].mean(), 2), round(taxi_dataset['Trip Miles'].mean(),2))) 
    else: 
        st.write("🏁 Average Trip Miles: {:,} (Average for all: {:,} 👎)".format(round(segmentRides['Trip Miles'].mean(), 2), round(taxi_dataset['Trip Miles'].mean(),2))) 

    if segmentRides['Tips'].mean() > taxi_dataset['Tips'].mean(): 
        st.write("💰 Average Tips: {:,} (Average for all: {:,} 👍)".format(round(segmentRides['Tips'].mean(), 2), round(taxi_dataset['Tips'].mean(),2))) 
    else: 
        st.write("💰 Average Tips: {:,} (Average for all: {:,} 👎)".format(round(segmentRides['Tips'].mean(), 2), round(taxi_dataset['Tips'].mean(),2))) 

    st.write("🕓 Average Time: {:,} mins (Average for all: {:,} mins)".format(round((segmentRides['Trip Seconds']/60).mean(), 2), round((taxi_dataset['Trip Seconds']/60).mean(),2))) 


    segmentRides.set_index('Trip Start Timestamp',inplace=True) 
    trueDemandsDaily = segmentRides.resample('D').size()
    trueDemandsDaily = trueDemandsDaily.reset_index()
    trueDemandsDaily.columns = ['Date','Demands']
    trueDemandsDaily["Date"] = pd.to_datetime(trueDemandsDaily["Date"])

    fig_daily_demand = px.line(trueDemandsDaily, x="Date", y="Demands", title='Daily Demand') 
    st.plotly_chart(fig_daily_demand) 