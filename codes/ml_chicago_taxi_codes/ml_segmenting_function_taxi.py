import pandas as pd
import seaborn as sns
from datetime import datetime
import math
import base64
import numpy as np  

from sklearn.cluster import KMeans 

def segment_users(taxi_data, k_clusters, model_type):   
    taxi_data['Trip Start Timestamp'] = taxi_data['Trip Start Timestamp'].astype('datetime64[ns]')

    # Calculating Recency 
    RecencyDF = taxi_data.groupby(['Taxi ID'])['Trip Start Timestamp'].max().reset_index()
    RecencyDF.columns = ['TaxiID', 'LatestOrderDate']
    RecencyDF['Recency'] = ((taxi_data['Trip Start Timestamp'].max() - RecencyDF['LatestOrderDate'])/
    np.timedelta64(1, 'h')).astype(int)

    RecencyFirstDF = taxi_data.groupby(['Taxi ID'])['Trip Start Timestamp'].min().reset_index()
    RecencyFirstDF.columns = ['TaxiID', 'FirstOrderDate'] 

    RecencyDF = pd.merge(RecencyDF, RecencyFirstDF, on='TaxiID', how='inner')


    # Calculating Frequency  
    ClientFreq = taxi_data[['Taxi ID', 'Trip Start Timestamp']].groupby("Taxi ID").count().reset_index()
    ClientFreq.columns=['TaxiID', 'Frequency'] 

    # Calculating Monetary 
    MonetaryStatisticsDF = taxi_data.groupby('Taxi ID')['Trip Total'].aggregate([np.sum])
    MonetaryStatisticsDF = MonetaryStatisticsDF.reset_index()
    MonetaryStatisticsDF.columns = ['TaxiID', 'Monetary']

    # Merging RFM 
    clientRFMsDF = pd.merge(RecencyDF, ClientFreq, on='TaxiID', how='outer')
    clientRFMsDF = pd.merge(clientRFMsDF, MonetaryStatisticsDF, on='TaxiID', how='outer')

    ## RFAC 
    clientRFMsDF['Recency_RFAC'] = (taxi_data['Trip Start Timestamp'].max() - RecencyDF['LatestOrderDate'])/(taxi_data['Trip Start Timestamp'].max() - RecencyDF['FirstOrderDate'])
    clientRFMsDF['Average_RFAC'] = clientRFMsDF['Monetary']/clientRFMsDF['Frequency']


    ## Clustering 
    if model_type == "RFAC": 
        kmeans = KMeans(n_clusters=k_clusters, random_state=0).fit(clientRFMsDF[['Recency_RFAC', 'Frequency', 'Average_RFAC']]) 
        clientRFMsDF["Segment"] = kmeans.labels_
    else: 
        kmeans = KMeans(n_clusters=k_clusters, random_state=0).fit(clientRFMsDF[['Recency_RFAC', 'Frequency', 'Monetary']]) 
    clientRFMsDF["Segment"] = kmeans.labels_ 

    segments = []
    segments_share = [] 
    segments_count = [] 
    segments_revenue = [] 
    segments_rides = []

    for i in range(0, k_clusters): 
        seg_share = round(clientRFMsDF[clientRFMsDF.Segment == i].shape[0] / clientRFMsDF.shape[0] * 100, 2) 
        seg_count = clientRFMsDF[clientRFMsDF.Segment == i].shape[0]
        seg_revenue = (clientRFMsDF[clientRFMsDF.Segment == i]['Monetary'].sum()/clientRFMsDF['Monetary'].sum())*100
        seg_rides = (clientRFMsDF[clientRFMsDF.Segment == i]['Frequency'].sum()/clientRFMsDF['Frequency'].sum())*100

        segments_share.append(seg_share)
        segments_count.append(seg_count)
        segments_revenue.append(seg_revenue)
        segments_rides.append(seg_rides)

    for j in range(0, k_clusters): 
        segments.append("Group {}".format(j)) 

    segments_share = {"Segments": segments, 
                      "Count": segments_count, 
                      "Share (%)": segments_share, 
                      "Revenue share (%)":segments_revenue, 
                      "Rides share (%)": segments_rides}

    segmentShareDF = pd.DataFrame(segments_share) 

    return clientRFMsDF, segmentShareDF 