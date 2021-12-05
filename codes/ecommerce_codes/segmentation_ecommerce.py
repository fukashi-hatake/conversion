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

import segmenting_function_ecommerce 

def filedownload(df, date_from, date_to, filename):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # strings <-> bytes conversions
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}_{str(date_from)}_{str(date_to)}.csv">Download CSV File</a>'
    return href


st.title('E-commerce Customer Segmentation') 

st.markdown("""
This app performs customer segmentation for the given data! 
* **🐍 Python libraries:** base64, pandas, streamlit, numpy, matplotlib, seaborn, plotly
* Dataset source: https://www.kaggle.com/carrie1/ecommerce-data 
""")


shop_dataset = pd.read_csv("dataset/e-commerce.csv") 
st.write("Total number of transactions: {:,}".format(shop_dataset.shape[0]))   

shop_dataset['InvoiceDate'] = shop_dataset['InvoiceDate'].astype('datetime64[ns]') 
shop_dataset['TotalPrice'] = shop_dataset['Quantity']*shop_dataset['UnitPrice'] 

date_from = st.date_input("Date From: ", shop_dataset['InvoiceDate'].min())
date_to   = st.date_input("Date To: "  , shop_dataset['InvoiceDate'].max())

# st.dataframe(shop_dataset.head(100))

shop_dataset = shop_dataset[(shop_dataset.InvoiceDate >= str(date_from)) & (shop_dataset.InvoiceDate <= str(date_to))]

clientRFMsDF, segmentShareDF = segmenting_function_ecommerce.segment_users(shop_dataset[:]) 

st.header('Statistics of Segmentation')
st.dataframe(segmentShareDF.style.highlight_max(axis=0)) 
st.write("Number of Customers: {:,}".format(clientRFMsDF.shape[0]))  

customer_segments = ['Champions', 'Loyal', 'Potential loyal', 'Platonic Friend', 
                        'Apprentice', 'Flirting', 'About to Dump', 'Breakup', 
                        'Don Juan', 'Ex Loyal', 'New Passion']

selected_segments = st.sidebar.multiselect('Segments', customer_segments, customer_segments)

df_selected_segments = clientRFMsDF[clientRFMsDF.Segment.isin(selected_segments)]

st.header('Customers from Selected Segments(s)')
st.write('Data Dimension: ' + str(df_selected_segments.shape[0]) + ' rows (= number of clients) and ' + str(df_selected_segments.shape[1]) + ' columns.')
st.dataframe(df_selected_segments)
st.markdown(filedownload(df_selected_segments, date_from, date_to, "customer_segments"), unsafe_allow_html=True)
 
fig = px.pie(segmentShareDF, values='Share (%)', names='Segments', title='Customer Segmentation (Pie)')
st.plotly_chart(fig) 

fig_barchart = px.bar(segmentShareDF, x='Count', y='Segments',  title='Customer Segmentation (BarChart)') 
st.plotly_chart(fig_barchart)

for segment in selected_segments:  
    st.header("Segment: {}".format(segment))    
    segmentPurchases = shop_dataset[shop_dataset.CustomerID.isin(df_selected_segments[df_selected_segments.Segment == segment].ClientID)] 

    st.write("🙎‍♂🙍‍♀️ Number of Customers: {:,} ({}% - Total Customers: {:,})".format(segmentPurchases.CustomerID.nunique(), 
            round(segmentPurchases.CustomerID.nunique()/shop_dataset.CustomerID.nunique()*100,2), shop_dataset.CustomerID.nunique()))

    st.write("🛒 Number of Purchases: {:,} ({}% - Total Purchases: {:,})".format(segmentPurchases.shape[0], round(segmentPurchases.shape[0]/shop_dataset.shape[0]*100, 2), shop_dataset.shape[0]))
    st.write("💵 Revenue: {:,} ({}% - Total Revenue: {:,})".format(round(segmentPurchases.TotalPrice.sum(),2), 
    	round(segmentPurchases.TotalPrice.sum()/shop_dataset.TotalPrice.sum()*100, 2), shop_dataset.TotalPrice.sum()))

    if segmentPurchases.TotalPrice.mean() > shop_dataset.TotalPrice.mean(): 
        st.write("💵 Average Spending: ${:,} (Average for all: {:,} 👍)".format(round(segmentPurchases.TotalPrice.mean(), 2), round(shop_dataset.TotalPrice.mean(),2))) 
    else: 
        st.write("💵 Average Spending: ${:,} (Average for all: {:,} 👎)".format(round(segmentPurchases.TotalPrice.mean(), 2), round(shop_dataset.TotalPrice.mean(),2))) 

    if segmentPurchases.Quantity.mean() > shop_dataset.Quantity.mean(): 
        st.write("🛒 Average Purchase Quantity: {:,} (Average for all: {:,} 👍)".format(round(segmentPurchases.Quantity.mean(), 2), round(shop_dataset.Quantity.mean(),2))) 
    else: 
        st.write("🛒 Average Purchase Quantity: {:,} (Average for all: {:,} 👎)".format(round(segmentPurchases.Quantity.mean(), 2), round(shop_dataset.Quantity.mean(),2))) 