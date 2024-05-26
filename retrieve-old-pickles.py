#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec  1 16:21:20 2021

@author: ffeist
"""

import csvimport as cv
import pickle
import copy
import datetime
import ips
import csv
import ebay_sold2_extract_from_shoppingapi

originalDataPath = "data step 2 - enriched with shoppingapi, completed/ebay_sold_step2_enriched_with_shoppingapi-2021-11-22-09.32.32 - original pull.csv"
imageDataPath = "data step 2 - enriched with shoppingapi, completed/ebay_sold_step2_enriched_with_shoppingapi-2021-11-30-08.59.53 - pull2 with images etc but fewer rows.csv"

originalData = cv.importcsv(originalDataPath)
imageData = cv.importcsv(imageDataPath)

# convert originalData to items
hasItemSpecificsIndex = originalData[0].index("hasItemSpecifics")
itemIDIndex = originalData[0].index("itemID")
items1 = {int(row[itemIDIndex]) : 
             {originalData[0][n]:row[n] for n in range(len(row))} 
         for row in originalData[1:]}
for itemID in items1:
    items1[itemID]['hasItemSpecifics'] = True if items1[itemID]['hasItemSpecifics'].lower() in ['true', 't', 'yes', 'y'] else False
    items1[itemID]['itemID'] = int(items1[itemID]['itemID'])

# convert imageData to items
hasItemSpecificsIndex = imageData[0].index("hasItemSpecifics")
itemIDIndex = imageData[0].index("itemID")
items2 = {int(row[itemIDIndex]) : 
             {imageData[0][n]:row[n] for n in range(len(row))} 
         for row in imageData[1:]}
for itemID in items2:
    items2[itemID]['hasItemSpecifics'] = True if items2[itemID]['hasItemSpecifics'].lower() in ['true', 't', 'yes', 'y'] else False
    items2[itemID]['itemID'] = int(items2[itemID]['itemID'])
    
    
picklePath1 = "old pickle files - discard once data from november 12 seems like it's fine/eBay_sold_incomplete_nov22.pickle"
picklePath2 = "/Users/ffeist/Downloads/CGC Application v2.0/old pickle files - discard once data from november 12 seems like it's fine/eBay_sold_step2_items-incomplete-iplimit-2021-11-24-12.40.39.373317.pickle"
picklePath3 = "/Users/ffeist/Downloads/CGC Application v2.0/old pickle files - discard once data from november 12 seems like it's fine/eBayDump2021-11-17-0922.pickle"
picklePath4 = "/Users/ffeist/Downloads/CGC Application v2.0/old pickle files - discard once data from november 12 seems like it's fine/eBayDump2021-11-17-1035 second nonoverlapping batch.pickle"
picklePath5 = "/Users/ffeist/Downloads/CGC Application v2.0/old pickle files - discard once data from november 12 seems like it's fine/eBayDump2021-11-1103 all items in both batches so far.pickle"
picklePaths = [picklePath1, picklePath2, picklePath3, picklePath4, picklePath5]


# first, combine the data from these into one dict of dictionaries.
pItems = [{} for path in picklePaths]
for n in range(len(picklePaths)):
    ppath = picklePaths[n]
    with open(ppath, 'rb') as f:
        itemsAsList = pickle.load(f)
        pItems[n] = {int(itemID) : itemsAsList[itemID] for itemID in itemsAsList}

allItems = copy.deepcopy(pItems)
allItems.append(items1)

items = items2
for n in range(len(allItems)):
    theseItems = allItems[n]
    # merge this into one over-arching items:
    for itemID in theseItems:
        thisItem = theseItems[itemID]
        if itemID not in items:
            items[itemID] = thisItem
            if 'endTime' in items[itemID] and 'url' in items[itemID]['endTime']:
                print("Weird item in items[itemID]")
                ips.ips()
        if itemID in items:
            # merge the items
            for key in thisItem:
                #if key doesn't exist or has values null, "", "nan", then replace items[itemID][key] with thisItem[key]
                # if key == 'endTime' and key in thisItem and "url" in thisItem[key]:
                #     print("Weird endTime in thisItem")
                #     ips.ips()
                # elif key == 'endTime' and key in items[itemID] and "url" in items[itemID][key]:
                #     print("Weird endTime in items[itemID]")
                #     ips.ips()
                if key not in items[itemID]:
                    items[itemID][key] = thisItem[key]
                elif items[itemID] in ['', None, float("nan") ]:
                    items[itemID][key] = thisItem[key]



items2 = ebay_sold2_extract_from_shoppingapi.get_shopping_api_properties(items)
itemsAsList = [items2[itemID] for itemID in items2]

properties = []
for itemID in items2:
    keys = items2[itemID].keys()
    for key in keys:
        if key not in properties:
            properties.append(key)

timenow = datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
outputfilename = 'data step 2 - enriched with shoppingapi, completed/ebay_sold_step2_enriched_with_shoppingapi-' + timenow + '.csv'
print(f"Writing to file {outputfilename}... ")
with open(outputfilename, 'w', encoding='UTF-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames = properties, lineterminator = '\n')
    writer.writeheader() 
    writer.writerows(itemsAsList)
print("done.")