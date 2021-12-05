import pandas as pd
import seaborn as sns
from datetime import datetime
import math
import base64
import numpy as np 

def give_score(x): 
    score = 0
    if x <= 0.05: 
        score = 5 
    elif x <= 0.2: 
        score = 4
    elif x <=0.3: 
        score = 3 
    elif x <=0.6: 
        score = 2 
    else: 
        score = 1 
    return score 


def segment_customers(rfm_score): 
    segment = ""
    if rfm_score in (434, 435, 443, 444, 445,  453, 454, 455, 533, 534, 535,  543, 544, 553, 554): 
        segment = "Loyal"
    elif rfm_score in (332, 333, 334, 335, 342, 343, 344, 345, 352, 353, 354, 355, 432, 442, 452, 532, 542, 552): 
        segment = "Potential loyal" 
    elif rfm_score in (211, 212, 213, 214, 215, 221, 222, 223, 224, 225, 231, 232, 233, 234, 235, 241, 242, 243, 
                       244, 245, 251, 252, 253, 254, 255, 311, 312, 315, 321, 322, 325, 331, 341, 351): 
        segment = "About to Dump"
    elif rfm_score in (313, 314, 323, 324, 413, 423, 441, 451, 513, 523, 541, 551): 
        segment = "Platonic Friend" 
    elif rfm_score in (113, 123, 124, 125, 133, 134, 135, 143, 144, 145, 153, 154, 155): 
        segment = "Ex Loyal" 
    elif rfm_score in (411, 412, 421, 422, 431, 511, 512, 521, 522, 531): 
        segment = "Apprentice" 
    elif rfm_score in (111, 112, 121, 122, 131, 132, 141, 142, 151, 152): 
        segment = "Breakup" 
    elif rfm_score in (514, 515, 524, 525, 545): 
        segment = "New Passion"
    elif rfm_score in (414, 415, 424, 425, 433): 
        segment = "Flirting" 
    elif rfm_score in (114, 115): 
        segment = "Don Juan" 
    elif rfm_score == 555: 
        segment = "Champions"
    return segment 


def segment_users(shop_data):  
    shop_data['InvoiceDate'] = shop_data['InvoiceDate'].astype('datetime64[ns]')

    # Calculating Recency 
    RecencyDF = shop_data.groupby(['CustomerID'])['InvoiceDate'].max().reset_index()
    RecencyDF.columns = ['ClientID', 'LatestOrderDate']
    RecencyDF['Recency'] = ((shop_data.InvoiceDate.max() - RecencyDF['LatestOrderDate'])/
    np.timedelta64(1, 'h')).astype(int)

    # Calculating Frequency  
    ClientFreq = shop_data[['CustomerID', 'InvoiceDate']].groupby("CustomerID").count().reset_index()
    ClientFreq.columns=['ClientID', 'Frequency'] 

    # Calculating Monetary 
    MonetaryStatisticsDF = shop_data.groupby('CustomerID')['TotalPrice'].aggregate([np.sum])
    MonetaryStatisticsDF = MonetaryStatisticsDF.reset_index()
    MonetaryStatisticsDF.columns = ['ClientID', 'Monetary']

    # Merging RFM 
    clientRFMsDF = pd.merge(RecencyDF, ClientFreq, on='ClientID', how='outer')
    clientRFMsDF = pd.merge(clientRFMsDF, MonetaryStatisticsDF, on='ClientID', how='outer')

    # Ranking (percentile)
    clientRFMsDF["Recency_Rank"]   = clientRFMsDF["Recency"].rank(method='min', ascending=True, pct=True)
    clientRFMsDF["Frequency_Rank"] = clientRFMsDF["Frequency"].rank(ascending=False, pct=True)
    clientRFMsDF["Monetary_Rank"]  = clientRFMsDF["Monetary"].rank(ascending=False, pct=True)

    # Scoring 
    clientRFMsDF['R_Score'] = clientRFMsDF['Recency_Rank'].apply(lambda x: give_score(x))
    clientRFMsDF['F_Score'] = clientRFMsDF['Frequency_Rank'].apply(lambda x: give_score(x))
    clientRFMsDF['M_Score'] = clientRFMsDF['Monetary_Rank'].apply(lambda x: give_score(x))

    # Segmenting Customers 
    clientRFMsDF["RFM_Score"] = clientRFMsDF['R_Score']*100 + clientRFMsDF['F_Score']*10 + clientRFMsDF['M_Score']
    clientRFMsDF["Segment"] = clientRFMsDF['RFM_Score'].apply(lambda x: segment_customers(x))

    segments = ['Champions', 'Loyal', 'Potential loyal', 'Platonic Friend', 
                'Apprentice', 'Flirting', 'About to Dump', 'Breakup', 
                'Don Juan', 'Ex Loyal', 'New Passion']
    segments_share = [] 
    segments_count = [] 
    segments_revenue = [] 
    segments_rides = []

    for segment in segments: 
        seg_share = round(clientRFMsDF[clientRFMsDF.Segment == segment].shape[0] / clientRFMsDF.shape[0] * 100, 2) 
        seg_count = clientRFMsDF[clientRFMsDF.Segment == segment].shape[0]
        seg_revenue = (clientRFMsDF[clientRFMsDF.Segment == segment]['Monetary'].sum()/clientRFMsDF['Monetary'].sum())*100
        seg_rides = (clientRFMsDF[clientRFMsDF.Segment == segment]['Frequency'].sum()/clientRFMsDF['Frequency'].sum())*100

        segments_share.append(seg_share)
        segments_count.append(seg_count)
        segments_revenue.append(seg_revenue)
        segments_rides.append(seg_rides)



    segments_share = {"Segments": segments, 
                      "Count": segments_count, 
                      "Share (%)": segments_share, 
                      "Revenue share (%)":segments_revenue, 
                      "Rides share (%)": segments_rides}

    segmentShareDF = pd.DataFrame(segments_share) 

    return clientRFMsDF, segmentShareDF 