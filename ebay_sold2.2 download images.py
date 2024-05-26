#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 30 11:47:25 2021

@author: ffeist
"""

import csvimport as cv
import re
import requests
import shutil
import errno
import os
import time
import datetime
import ips

# import a dataset which has already been processed by the shopping api, but not yet cleaned.
import_filepath = "/Users/ffeist/Desktop/Work/CGC Application v2.0/data step 2 - enriched with shoppingapi, completed/ebay_sold_step2_enriched_with_shoppingapi-2022-02-05-12.13.15.csv"
data = cv.importcsv(import_filepath)
input("Have you checked that you are using the intended input file? Enter to continue. ")
input("Reminder: This file can only be run from the base folder of the application. If it's not there, please move it. Enter to continue.")

itemIDIndex = data[0].index("itemID")
pictureURLIndex = data[0].index("pictureURL")
# possible_filetypes = ['.jpg', '.png'] #used for stripping trailing urls. off while that is off. possibly removable.
def convert_liststring_to_list(liststring):
    ls = liststring[1:-1] # get rid of square brackets
    urls = re.split(r"', ", ls)
    urls = [u[1:] for u in urls] # get rid of leading single-quotes
    urls[-1] = urls[-1][:-1] # get rid of trailing single-quote in last entry
    # for n in range(len(urls)): # strip trailing url variables. scrapped because it's hard for google drive files.
    #     u = urls[n]
    #     fileType = ""
    #     for ftype in possible_filetypes:
    #         try:
    #             urlEndIndex = u.lower().index(ftype)
    #             fileType = ftype
    #             break
    #         except ValueError as e:
    #             continue
    #     if fileType == "":
    #         ips.ips()
    #     urls[n] = u[:urlEndIndex + 4]
    return urls
    

items = [
        {'itemID': row[itemIDIndex],
         'pics' : convert_liststring_to_list(row[pictureURLIndex])
        } for row in data[1:]]


errorCount = 0
numItems = len(items)
failed_itemIDs = []
for n in range(len(items)):
    try:
        item = items[n]
        itemID = item['itemID']
        picURLs = item['pics']
        folderpath = 'images/' + itemID
        try:
            os.makedirs(folderpath)
        except OSError as e: 
            if e.errno == errno.EEXIST and os.path.isdir(folderpath):
                print(f"Item n={n} folder exists. Skipping this item.")
                continue
            else: raise e
        print()
        for m in range(len(picURLs)):
            url = picURLs[m]
            
            filepath = folderpath + '/' + itemID + ' pic '+ str(m) + '.jpg'
            
            try:
                timenow = datetime.datetime.now()
                print(f"item {n}/{numItems}: reqesting image for itemID {itemID} at time",timenow.strftime("%H:%M:%S %m/%d/%y"))
                r = requests.get(url, stream = True, timeout = 6)
                
            except Exception as e:
                errorCount += 1
                sleepTime = 5
                print(str(e))
                print(f"Sleeping for {sleepTime} seconds and trying again.")
                time.sleep(sleepTime)
                try:
                    r = requests.get(url, stream = True)
                    pass
                except Exception as e2:
                    print(str(e2))
                    print(f"itemID {itemID} failed after timeout. Skipping.")
                    if itemID not in failed_itemIDs:
                        failed_itemIDs.append(itemID)
                    continue
                
            with open(filepath, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
    except Exception as e:
        print(str(e))
        ips.ips()
        pass
    
print(f"Done. {len(failed_itemIDs)} out of {len(items)} itemIDs failed. They can be found in failed_itemIDs.")