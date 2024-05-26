#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 19 17:06:15 2021

@author: ffeist
"""

import requests
import csvimport as cv

import_filename = input("Please enter the input filename, with .csv at the end.")
data = cv.importcsv(import_filename)

headers = data[0]
data = data[1:]
items = {}
for row in data:
    itemIDIndex = 
    items[]
    item = {headers[n]: row[n] for n in range(len(headers))}
    items[item['itemID']] = item

imageurl = ""
imagetype = imageurl.split('.')[-1]
response = requests.get(imageurl)
itemID = 0
index = 0
file = open("images/" + str(itemID) + "/" + str(index) + '.' + str(imagetype))