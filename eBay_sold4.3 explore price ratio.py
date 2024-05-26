import csvimport as cv
import matplotlib.pyplot as plt
import statistics as stats
import math
import copy
import numpy as np
import pandas as pd
from sklearn import tree
from sklearn.model_selection import train_test_split

## IN THIS FILE: TRY TO ANALYZE BASED ON CGC/PSA PRICE RATIO

# NOTE: as of aug 19 2021, there's no good way to be sure that a card labeled as base set 1st edition
# is actually base set 1st edition. many of them are just unlimited (about half, maybe more, are unlimited).
# depending on the analysis, it might be good to exclude these.
# shadowless seems to be quite accurate though.

# also, there are incredibly low numbers for cards from each of the respective base sets.
# consider redoing sold_get so that it filters out the non-base sets first,
# and then considers the rest to just be base set. That will leave a higher sample left.

# note that 'price' for listings that were auctions is an estimated BuyItNow price
# with an algorithm created in eBay_sold_clean.py.

import_filename = "ebay_sold3_cleaned-2021-12-01-16.37.22.csv"

data = cv.importcsv(import_filename,
    typelist = ['s', 's', 's', 's', 'bool',
                's', 's', 's', 's', 's',
                's', 's', 'float', 's', 'i',
                's','s', 's'],
    doBackupCheck = False)

cols = ['title', 'company', 'itemID', 'grade', 'isError', 
        'language', 'set', 'setNum', 'releaseYear', 'releaseMonth', 
        'location', 'country', 'price', 'era', 'dataSetIndex', 
        'endTime', 'PSA9Price', 'PSA9SampleSize']
cols_to_discard = []
items = [{header : 
          data[n][data[0].index(header)] for header in cols if header not in cols_to_discard} 
         for n in range(1,len(data))]
    
input("NOTE: We are currently pre-filtering rows. Not all data is part of the analysis. To turn this off, change it in the code. "
      "Press enter to continue.")
items = [item for item in items if item['dataSetIndex'] == 1]
items = [item for item in items if item['grade'] != '9.5']
print(f"{len(items)} rows remain after filtering.")
    
def era(year):
    if year == '':
        return ''
    if int(year) <= 2005:
        return 'vintage'
    elif int(year) <= 2015:
        return 'semivintage'
    elif int(year) <= 2017:
        return 'evolutions'
    elif int(year) <= 2019:
        return 'semimodern'
    else:
        return 'modern'
cgc_grades = ['0.5', '1', '1.5', '2', '2.5', '3', '3.5', '4', '4.5', '5', 
              '5.5', '6', '6.5', '7', '7.5', '8', '8.5', '9', '9.5', '10', '10 Perfect']

psa_grades = ['1', '1.5', '2', '2.5', '3', '3.5', '4', '4.5', '5', 
              '5.5', '6', '6.5', '7', '7.5', '8', '8.5', '9', '10']

cgc_grade_convert = { 
    # convert CGC grade to approximate PSA grade.
    # grades less than 7 are not yet supported.
    '0.5' : '0',
    '1'   : '0',
    '1.5' : '0',
    '2'   : '0',
    '2.5' : '0',
    '3'   : '0',
    '3.5' : '0',
    '4'   : '0',
    '4.5' : '0',
    '5'   : '5',
    '5.5' : '5',
    '6'   : '6',
    '6.5' : '6',
    '7'   : '7',
    '7.5' : '7',
    '8'   : '8',
    '8.5' : '8',
    '9'   : '9',
    '9.5' : '9',
    '10'  : '10',
    '10 perfect' : '10'
    }
def round_2sigfigs(x): 
    if x >= 10:
        return int(round(x, -int(math.floor(math.log10(x))) + 1) )
    else:
        return round(x, -int(math.floor(math.log10(x))) + 1)
    
    
# fill cards dictionary. Structure is
# cards[cardName][commonGrade][company]['cardList']
print(f"Started with {len(items)} items. Filling dictionary of cards and filtering...")
setnames = {item['set'] for item in items}
cards = dict()
commonGrades = ['5', '6', '7', '8', '9', '10']
numCardsRemovedLackingSetNumOrGrade = 0
numCardsRemovedGradeBelowMinimum = 0
for item in items:
    if not item['set'] or not item['setNum'] or not item['grade']:
        numCardsRemovedLackingSetNumOrGrade += 1
        continue
    cardName = item['set'] + ' #' + item['setNum']
    company = item['company']
    commonGrade = (cgc_grade_convert[item['grade']] if company == 'CGC' 
                   else str(math.floor(float(item['grade']))))
    if commonGrade not in ['5', '6', '7', '8', '9', '10']:
        numCardsRemovedGradeBelowMinimum += 1
        continue
    if cardName not in cards:
        cards[cardName] = \
            {commonGrade: 
                 {company: {'cardList': []} for company in ['PSA', 'CGC']} 
             for commonGrade in ['5', '6', '7', '8', '9', '10']
            }
        cards[cardName][commonGrade][company]['cardList'].append(copy.deepcopy(item))
        
        cards[cardName]['set'] = item['set']
        cards[cardName]['setNum'] = item['setNum']
        cards[cardName]['PSA9Price'] = item['PSA9Price']
    else:
        cards[cardName][commonGrade][company]['cardList'].append(copy.deepcopy(item))
itemsLists = [cards[cardName][grade][company]['cardList']
              for cardName in cards 
              for grade in set(cards[cardName].keys()) & {'5','6','7','8','9','10'}
              for company in ['CGC', 'PSA']]
itemsRemaining = sum([len(il) for il in itemsLists])
print(f"{numCardsRemovedLackingSetNumOrGrade} cards removed because they did not have at least "
      + "one property of set, setNum, or grade")
print(f"{numCardsRemovedGradeBelowMinimum} cards removed because grade was lower than the minimum in our analysis.")
print(f"{itemsRemaining} items remain.")
# - drop low-samplesize cards
# - store summary statistics:
#    cards[cardName]['PSA9Price']
#    cards[cardName]['set']
#    cards[cardName]['releaseYear']
#    cards[cardName]['era']
#    cards[cardName]['cardList']
#    cards[cardName][commonGrade]['minSampleSize']
#    cards[cardName][commonGrade]['priceRatio']
#    cards[cardName][commonGrade][company]['avgPrice']
#    cards[cardName][commonGrade]['cardName']
#    cards[cardName][commonGrade]['commonGrade']
leastMinSampleSize = 4
numMissingPSA9Removed = 0
numCardsRemovedLowSampleSize = 0
for cardName in cards:
    card = cards[cardName]
    for commonGrade in ['5', '6', '7', '8', '9', '10']:
        cards[cardName][commonGrade]['cardName'] = cardName
        cards[cardName][commonGrade]['commonGrade'] = commonGrade
        for company in ['PSA', 'CGC']:
            cardList = cards[cardName][commonGrade][company]['cardList']
            cards[cardName][commonGrade][company]['salesVolume'] = \
                sum([c['price'] for c in cardList])
        cards[cardName][commonGrade]['minSampleSize'] = \
            min(len(cards[cardName][commonGrade]['PSA']['cardList']),
                len(cards[cardName][commonGrade]['CGC']['cardList']))
        
        if cards[cardName][commonGrade]['minSampleSize'] < leastMinSampleSize:
            numCardsRemovedLowSampleSize += len(cards[cardName][commonGrade]['PSA']['cardList']) \
                + len(cards[cardName][commonGrade]['CGC']['cardList'])
            del cards[cardName][commonGrade]
            continue
        if cards[cardName][commonGrade]['PSA']['cardList']:
            PSAprices = [c['price'] for c in cards[cardName][commonGrade]['PSA']['cardList']]
            avgPSAprice = stats.mean(PSAprices)
            cards[cardName][commonGrade]['PSA']['avgPrice'] = avgPSAprice
        else:
            cards[cardName][commonGrade]['PSA']['avgPrice'] = 0
        if cards[cardName][commonGrade]['CGC']['cardList']:
            CGCprices = [c['price'] for c in cards[cardName][commonGrade]['CGC']['cardList']]
            avgCGCprice = stats.mean(CGCprices)
            cards[cardName][commonGrade]['CGC']['avgPrice'] = avgCGCprice
        else:
            cards[cardName][commonGrade]['CGC']['avgPrice'] = 0
        if cards[cardName][commonGrade]['minSampleSize'] >= leastMinSampleSize:
            cards[cardName][commonGrade]['priceRatio'] = avgCGCprice / avgPSAprice
            errAvgCGC = stats.stdev(CGCprices) / (len(CGCprices) - 1)
            errAvgPSA = stats.stdev(PSAprices) / (len(PSAprices) - 1)
            cards[cardName][commonGrade]['priceRatioErr'] = (avgCGCprice / avgPSAprice) \
                * math.sqrt((errAvgCGC/avgCGCprice)**2 + (errAvgPSA/avgPSAprice)**2)
            cards[cardName][commonGrade]['itemMarketShare'] = len(CGCprices) / (len(PSAprices) + len(CGCprices))
        
    
    # properties common to cardName
    cardList = []
    for commonGrade in set(cards[cardName].keys()) & {'5', '6', '7', '8', '9', '10'}:
        for company in set(cards[cardName][commonGrade].keys()) & {'PSA','CGC'}:
            cardList.extend(cards[cardName][commonGrade][company]['cardList'])
    cards[cardName]['cardList']  = cardList
    cardYearCounts = dict()
    for card in cardList:
        year = card['releaseYear']
        if year == '':
            continue
        cardYearCounts[year] = cardYearCounts.setdefault(year, 0) + 1
    if len(cardYearCounts) > 0:
        mostLikelyYear = max(cardYearCounts,key=cardYearCounts.get)
        cards[cardName]['releaseYear'] = mostLikelyYear
        cards[cardName]['era'] = era(mostLikelyYear)
    else:
        cards[cardName]['releaseYear'] = ''
        cards[cardName]['era'] = ''
print(f"{numCardsRemovedLowSampleSize} cards removed because of low sample size per grade.")

flatItemLists = [cards[cardName][commonGrade][company]['cardList'] 
                 for cardName in cards
                 for commonGrade in set(cards[cardName]) & {'5','6','7','8','9','10'}
                 for company in ['PSA', 'CGC']]
flatItems = [item for itemList in flatItemLists for item in itemList]
###########################################################################
############### Prepare CGC/PSA ratio data table ##########################
###########################################################################


ratioData = []
totalCards = 0
for cardName in cards:
    for commonGrade in set(cards[cardName]) & {'5', '6', '7', '8', '9', '10'}:
        row = dict()
        CGCitems = cards[cardName][commonGrade]['CGC']['cardList']
        PSAitems = cards[cardName][commonGrade]['PSA']['cardList']
        totalCards += len(CGCitems) + len(PSAitems)
        row['set'] = cards[cardName]['set']
        row['setNum'] = cards[cardName]['setNum']
        row['grade'] = commonGrade
        row['ratio'] = cards[cardName][commonGrade]['priceRatio']
        row['ratioError'] = cards[cardName][commonGrade]['priceRatioErr']
        row['PSA9Price'] = cards[cardName]['PSA9Price']
        row['year'] = cards[cardName]['releaseYear']
        row['CGCSalesVolume'] = cards[cardName][commonGrade]['CGC']['salesVolume']
        row['PSASalesVolume'] = cards[cardName][commonGrade]['CGC']['salesVolume']
        row['sampleSize'] = cards[cardName][commonGrade]['minSampleSize']
        row['totalSampleSize'] = len(CGCitems) + len(PSAitems)
        row['CGCPrice'] = stats.mean([item['price'] for item in CGCitems])
        row['PSAPrice'] = stats.mean([item['price'] for item in CGCitems])
        row['era'] = cards[cardName]['era']
        row['itemMarketShare'] = cards[cardName][commonGrade].get('itemMarketShare')
        ratioData.append(row)
print(f"{totalCards} cards remain in the sample.")
### WHAT PROPERTIES DO I WANT TO RELATE AT THE END?
# CGC MARKET VOLUME (YEAR, GRADE, RATIO, PSA9PRICE, ISERROR)
avgPriceRatio = np.average([rd['ratio'] for rd in ratioData], 
                           weights = [rd['sampleSize'] for rd in ratioData])
# CGC/PSA Price by era
plt.figure(0)
eraValues = ['vintage', 'semivintage', 'evolutions', 'semimodern', 'modern']
eraValues = [eV for eV in eraValues if any([rd['era'] == eV  for rd in ratioData])]
eraVsRatioY = [np.average([rd['ratio'] for rd in ratioData if rd['era'] == era], 
                            weights = [1/rd['ratioError'] for rd in ratioData if rd['era'] == era])
                 for era in eraValues]
sampleSize = sum([rd['totalSampleSize'] for rd in ratioData if rd['era'] in eraValues])
plt.xticks(rotation = -50)
plt.ylim([0.6,1.1])
plt.axhline(y=avgPriceRatio, color='r', linestyle='--')
plt.scatter(eraValues, eraVsRatioY)
plt.title(f"CGC/PSA Price Ratio by Card's Era (n={sampleSize})")
plt.xlabel("Card's Release Era")
plt.ylabel("CGC/PSA Price Ratio")
plt.show()

# CGC/PSA Price by grade
plt.figure(1)
gradeValues = ['5', '6', '7', '8', '9', '10']
gradeValues = [gr for gr in gradeValues if any(rd['grade'] == gr for rd in ratioData)]
gradeVsRatioY = [np.average([rd['ratio'] for rd in ratioData if rd['grade'] == grade], 
                            weights = [1/rd['ratioError'] for rd in ratioData if rd['grade'] == grade])
                 for grade in gradeValues]
# gradeVsRatioErrs = [math.sqrt(sum([rd['ratioError']**2 for rd in ratioData if rd['grade'] == grade])) 
#                     for grade in gradeValues] # this gives massive errors... seems way to big.
#                                                 # I think the geometric mean isn't right. have to 
#                                                 # consider that it's a sum of ratios? do this last if at all.
plt.ylim([0.6,1.1])
plt.axhline(y=avgPriceRatio, color='r', linestyle='--')
plt.scatter(gradeValues, gradeVsRatioY)
plt.title(f"CGC/PSA Price Ratio by Card's Grade (n={totalCards})")
plt.xlabel("Card's Grade (rounded down except CGC9.5 = PSA10)")
plt.ylabel("CGC/PSA Price Ratio")
plt.show()

# CGC/PSA Price by PSA9 price
plt.figure(2)
minPrice = 30
maxPrice = 40000
f = 5/3
maxExponent = math.ceil(math.log(20000)/math.log(1.5) - 1)
ratioDataPSA9Price = [rd for rd in ratioData if rd['PSA9Price'] != '' and minPrice <= float(rd['PSA9Price']) < maxPrice]
PSA9PriceRanges = [[round(minPrice * f**n), round(minPrice * f**(n+1))] for n in range(maxExponent)]
PSA9PriceRanges = [PR for PR in PSA9PriceRanges if any(PR[0] <= float(rd['PSA9Price']) < PR[1] for rd in ratioDataPSA9Price)]
PSA9PriceVsRatioY = [np.average([rd['ratio'] for rd in ratioDataPSA9Price if PSA9PR[0] <= float(rd['PSA9Price']) < PSA9PR[1]], 
                            weights = [1/rd['ratioError'] for rd in ratioDataPSA9Price if PSA9PR[0] <= float(rd['PSA9Price']) < PSA9PR[1]])
                 for PSA9PR in PSA9PriceRanges]
strPSA9PriceRanges = [str(PSA9PR) for PSA9PR in PSA9PriceRanges]
sampleSize = sum([rd['totalSampleSize'] for rd in ratioDataPSA9Price])
plt.xticks(rotation = -50)
plt.ylim([0.6,1.1])
plt.axhline(y=avgPriceRatio, color='r', linestyle='--')
plt.scatter(strPSA9PriceRanges, PSA9PriceVsRatioY)
plt.title(f"CGC/PSA Price Ratio by PSA 9 Price (n={sampleSize})")
plt.xlabel("Card's PSA 9 Price ($)")
plt.ylabel("CGC/PSA Price Ratio")
plt.show()

# CGC/PSA Price by sale price for a PSA copy
plt.figure(3)
minPrice = 30
maxPrice = 19999.1
f = 5/3
maxExponent = math.ceil(math.log(20000)/math.log(1.5) - 1)
# option 1: generate price ranges exponentially with the above 
PSAPriceRanges = [[round_2sigfigs(minPrice * f**n), round_2sigfigs(minPrice * f**(n+1))] for n in range(maxExponent)]
# option 2: generate price ranges manually
PSAPriceRanges = [[10,20], [20,40], [40,60], [60,80], [80,100], [100,120], [120,140], [140,160]]

PSAPriceRanges = [PR for PR in PSAPriceRanges 
                  if len([rd for rd in ratioData if PR[0] <= rd['PSAPrice'] < PR[1]]) > 1]
PSAPriceVsRatioY = [np.average([rd['ratio'] for rd in ratioData if PSAPR[0] <= rd['PSAPrice'] < PSAPR[1]], 
                            weights = [1/rd['ratioError'] for rd in ratioData if PSAPR[0] <= rd['PSAPrice'] < PSAPR[1]])
                 for PSAPR in PSAPriceRanges]
strPSAPriceUppers = ['< ' + str(PSAPriceRanges[n][1]) for n in range(len(PSAPriceRanges))]
sampleSize = sum([rd['totalSampleSize'] for rd in ratioData if minPrice <= rd['PSAPrice'] < maxPrice])
plt.xticks(rotation = -50)
plt.ylim([0.6,1.25])
plt.axhline(y=avgPriceRatio, color='r', linestyle='--')
plt.scatter(strPSAPriceUppers, PSAPriceVsRatioY)
plt.title(f"CGC/PSA Price Ratio by Sale Price (n={sampleSize})")
plt.xlabel("Card's Sale Price ($)")
plt.ylabel("CGC/PSA Price Ratio")
plt.show()

# # CGC/PSA Price by item market share
# plt.figure(4)
# minIMS = 0
# maxIMS = 1
# step = 0.1
# numSteps = int(maxIMS / step)
# ratioDataIMS = [rd for rd in ratioData if rd['itemMarketShare'] is not None]
# IMSRanges = [[round(minIMS + step * n,2), round(minIMS + step * (n+1),2)] for n in range(numSteps)]
# IMSRanges = [IMSR for IMSR in IMSRanges if any(IMSR[0] <= rd['itemMarketShare'] < IMSR[1] for rd in ratioDataIMS)]
# IMSVsRatioY = [np.average([rd['ratio'] for rd in ratioDataIMS if IMSR[0] <= rd['itemMarketShare'] < IMSR[1]], 
#                             weights = [rd['sampleSize'] for rd in ratioDataIMS if IMSR[0] <= rd['itemMarketShare'] < IMSR[1]])
#                  for IMSR in IMSRanges]
# strIMSRanges = [str(IMSR) for IMSR in IMSRanges]
# sampleSize = sum([rd['totalSampleSize'] for rd in ratioDataIMS])
# plt.xticks(rotation = -50)
# plt.ylim([0.6,1.1])
# plt.axhline(y=avgPriceRatio, color='r', linestyle='--')
# plt.scatter(strIMSRanges, IMSVsRatioY)
# plt.title(f"CGC/PSA Price Ratio by CGC item market share (n={sampleSize})")
# plt.xlabel("Card's CGC market share")
# plt.ylabel("CGC/PSA Price Ratio")
# plt.show()



# check typical CGC 9.5 to PSA 10 ratio
# numerator = 0
# denominator = 0
# numeratorModern = 0
# denominatorModern = 0
# numerator95to9 = 0
# denominator95to9 = 0
# for cardName in cards:
#     cgc95s = [item['price'] for item in cards[cardName]['cardList'] if item['grade'] == '9.5']
#     psa10s = [item['price'] for item in cards[cardName]['cardList'] if item['grade'] == '10' and item['company'] == 'PSA']
#     if len(cgc95s) > 0 and len(psa10s) > 0:
#         ratio = stats.mean(cgc95s)/stats.mean(psa10s)
#         minSampleSize = min(len(cgc95s),len(psa10s))
#         numerator += ratio * minSampleSize
#         denominator += minSampleSize
#         if cards[cardName]['era'] == 'modern':
#             numeratorModern += ratio * minSampleSize
#             denominatorModern += minSampleSize
#     psa9s = [item['price'] for item in cards[cardName]['cardList'] if item['grade'] == '9' and item['company'] == 'PSA']
#     if len(psa9s) > 0 and len(cgc95s) > 0:
#         ratio = stats.mean(cgc95s)/stats.mean(psa9s)
#         minSampleSize = min(len(cgc95s),len(psa9s))
#         numerator95to9 += ratio * minSampleSize
#         denominator95to9 += minSampleSize    
# avg95to10ratio = numerator / denominator
# avg95to10ratioModern = numeratorModern / denominatorModern
# avg95to9ratio = numerator95to9 / denominator95to9
# print("avg cgc 9.5 to psa 10 ratio is", avg95to10ratio)
# print("avg cgc 9.5 to psa 10 ratio in modern is", avg95to10ratioModern)
# print("avg cgc 9.5 to psa 9 ratio is", avg95to9ratio)