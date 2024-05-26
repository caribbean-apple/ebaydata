import csvimport as cv
import matplotlib.pyplot as plt
import statistics as stats
import math
import copy
import pandas as pd
from sklearn import tree


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
    '4'   : '4',
    '4.5' : '4',
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
    '10 Perfect' : '10'
}
def get_common_grade(item):
    if 'grade' not in item or item['grade'] == '':
        return ''
    grade = item['grade']
    if item['company'] == 'PSA':
        return grade.replace('.5','')
    else:
        return cgc_grade_convert[grade]

def std_error_dollar_market_share(points):
    l = len(points)
    if l == 0:
        return 100000
    avg = sum(points) / l
    prefactor = math.sqrt(l / (l - 1)) if l > 1 else 7
    err =  prefactor * math.sqrt(sum([(p - avg)**2 for p in points]))
    return err

def std_error_item_market_share(nPSA, nCGC):
    n = nCGC + nPSA
    if nCGC == 0:
        return 1/n
    pCGC = nCGC / n
    pPSA = nPSA / n
    prefactor = n/math.sqrt(n-1) if n > 1 else 7
    errorPSA = prefactor * math.sqrt(pCGC * pPSA)
    errorCGC = errorPSA
    itemMarketShareError = 1 / (1 + nPSA/nCGC)**2 * (nPSA/nCGC) * math.sqrt((errorPSA/nPSA)**2 + (errorCGC/nCGC)**2)
    return itemMarketShareError

def round_2sigfigs(x):
    if x >= 10:
        return int(round(x, -int(math.floor(math.log10(x))) + 1) )
    else:
        return round(x, -int(math.floor(math.log10(x))) + 1)
    
    
# pre-filtering rows, if desired:

input("NOTE: We are currently pre-filtering rows. Not all data is part of the analysis. To turn this off, change it in the code. "
      "Press enter to continue.")
items = [item for item in items if item['dataSetIndex'] == 1]
print(f"{len(items)} rows remain after filtering.")
    
########################################################################################################################
########################################################################################################################
# CGC MARKET SHARE (YEAR, GRADE, RATIO, PSA9PRICE, ISERROR)
overallCGCMarketVolume = sum([item['price'] for item in items if item['company'] == 'CGC'])
overallPSAMarketVolume = sum([item['price'] for item in items if item['company'] == 'PSA'])
overallAvgMarketShare = 100 * overallCGCMarketVolume / ( overallCGCMarketVolume + overallPSAMarketVolume)
overallItemMarketShare = 100 * sum([1 for item in items if item['company'] == 'CGC']) / len(items)

# Market Share by Year:
# years = [str(year) for year in range(1995,2022)]
# CGCMarketVolumeByYear = [0 for n in range(len(years))]
# PSAMarketVolumeByYear = [0 for n in range(len(years))]
# CGCPrices = [[] for n in range(len(years))]
# PSAPrices = [[] for n in range(len(years))]
# nSkippedItems = 0
# for item in items:
#     if item['releaseYear'] == '':
#         nSkippedItems += 1
#         continue
#     yearIndex = years.index(item['releaseYear'])
#     if item['company'] == 'PSA':
#         PSAMarketVolumeByYear[yearIndex] += item['price']
#         PSAPrices[yearIndex].append(item['price'])
#     else:
#         CGCMarketVolumeByYear[yearIndex] += item['price']
#         CGCPrices[yearIndex].append(item['price'])
# marketShareByYear = [CGCMarketVolumeByYear[n] / (CGCMarketVolumeByYear[n] + PSAMarketVolumeByYear[n]) 
#                       for n in range(len(CGCMarketVolumeByYear))]
# MVErrorsPSA = [std_error_dollar_market_share(prices) for prices in PSAPrices]
# MVErrorsCGC = [std_error_dollar_market_share(prices) for prices in CGCPrices]
# marketShareErrors = [-1 / (1 + PSAMarketVolumeByYear[n] / CGCMarketVolumeByYear[n])**2 
#                      * math.sqrt((MVErrorsPSA[n]/PSAMarketVolumeByYear[n])**2 + (MVErrorsCGC[n]/CGCMarketVolumeByYear[n])**2) for n in range(len(MVErrorsPSA))]

# itemCountByYearPSA = [len([1 for item in items if item['releaseYear'] == year and item['company'] == 'PSA']) for year in years]
# itemCountByYearCGC = [len([1 for item in items if item['releaseYear'] == year and item['company'] == 'CGC']) for year in years]
# itemMarketShareByYear = [itemCountByYearCGC[n] / (itemCountByYearCGC[n] + itemCountByYearPSA[n]) for n in range(len(years))] 
# itemMarketShareErrors = [std_error_item_market_share(itemCountByYearPSA[n], itemCountByYearCGC[n]) for n in range(len(itemCountByYearPSA))]

# sampleSize = len(items) - nSkippedItems
# plt.figure(0)
# # plt.axhline(y=overallAvgMarketShare, color='r', linestyle='--')
# plt.axhline(y=overallItemMarketShare, color='r', linestyle='--')
# # plt.errorbar(years, marketShareByYear, yerr=marketShareErrors, c = 'g', fmt='o')
# plt.errorbar(years, itemMarketShareByYear, yerr = itemMarketShareErrors, fmt = 'o')
# plt.title(f"CGC Market Share by Card's Release Year (n={sampleSize})")
# plt.xlabel("Card's Release Year")
# plt.ylabel("CGC Market Share (%)")
# plt.xticks(rotation = -80)
# plt.ylim([0,1])
# plt.show()

# Market Share by Era:
eras = ['vintage', 'semivintage', 'evolutions', 'semimodern', 'modern']
CGCMarketVolumeByEra = [0 for n in range(len(eras))]
PSAMarketVolumeByEra = [0 for n in range(len(eras))]
CGCPrices = [[] for n in range(len(eras))]
PSAPrices = [[] for n in range(len(eras))]
nSkippedItems = 0
for item in items:
    if item['era'] == '':
        nSkippedItems += 1
        continue
    eraIndex = eras.index(item['era'])
    if item['company'] == 'PSA':
        PSAMarketVolumeByEra[eraIndex] += item['price']
        PSAPrices[eraIndex].append(item['price'])
    else:
        CGCMarketVolumeByEra[eraIndex] += item['price']
        CGCPrices[eraIndex].append(item['price'])
marketShareByEra = [100 * CGCMarketVolumeByEra[n] / (CGCMarketVolumeByEra[n] + PSAMarketVolumeByEra[n]) 
                      for n in range(len(CGCMarketVolumeByEra))]
MVErrorsPSA = [std_error_dollar_market_share(prices) for prices in PSAPrices]
MVErrorsCGC = [std_error_dollar_market_share(prices) for prices in CGCPrices]
marketShareErrors = [100 * 1 / (1 + PSAMarketVolumeByEra[n] / CGCMarketVolumeByEra[n])**2 
                     * math.sqrt((MVErrorsPSA[n]/PSAMarketVolumeByEra[n])**2 + (MVErrorsCGC[n]/CGCMarketVolumeByEra[n])**2) for n in range(len(MVErrorsPSA))]

itemCountByEraPSA = [len([1 for item in items if item['era'] == era and item['company'] == 'PSA']) for era in eras]
itemCountByEraCGC = [len([1 for item in items if item['era'] == era and item['company'] == 'CGC']) for era in eras]
itemMarketShareByEra = [100 * itemCountByEraCGC[n] / (itemCountByEraCGC[n] + itemCountByEraPSA[n]) for n in range(len(eras))] 
itemMarketShareErrors = [100 * std_error_item_market_share(itemCountByEraPSA[n], itemCountByEraCGC[n]) for n in range(len(itemCountByEraPSA))]

sampleSize = len(items) - nSkippedItems
plt.figure(0)
# plt.axhline(y=overallAvgMarketShare, color='r', linestyle='--')
plt.axhline(y=overallItemMarketShare, color='r', linestyle='--')
# plt.errorbar(eras, marketShareByEra, yerr=marketShareErrors, c = 'g', fmt='o')
plt.errorbar(eras, itemMarketShareByEra, yerr = itemMarketShareErrors, fmt = 'o', c = 'k')
plt.title(f"CGC Market Share by Card's Release Era (n={sampleSize})")
plt.xlabel("Card's Era")
plt.ylabel("CGC Market Share (%)")
plt.xticks(rotation = -50)
plt.ylim([0,100])
plt.show()

# Market Share by Grade:
commonGrades = [str(grade) for grade in range(4,11)]
CGCMarketVolumeByGrade = [0 for n in range(len(commonGrades))]
PSAMarketVolumeByGrade = [0 for n in range(len(commonGrades))]
CGCPrices = [[] for n in range(len(commonGrades))]
PSAPrices = [[] for n in range(len(commonGrades))]
nSkippedItems = 0
for item in items:
    if item['grade'] == '' or cgc_grade_convert[item['grade']] == '0':
        nSkippedItems += 1
        continue
    grade = get_common_grade(item)
    gradeIndex = commonGrades.index(grade)
    if item['company'] == 'PSA':
        PSAMarketVolumeByGrade[gradeIndex] += item['price']
        PSAPrices[gradeIndex].append(item['price'])
    else:
        CGCMarketVolumeByGrade[gradeIndex] += item['price']
        CGCPrices[gradeIndex].append(item['price'])
marketShareByGrade = [100 * CGCMarketVolumeByGrade[n] / (CGCMarketVolumeByGrade[n] + PSAMarketVolumeByGrade[n]) 
                      for n in range(len(CGCMarketVolumeByGrade))]
MVErrorsPSA = [std_error_dollar_market_share(prices) for prices in PSAPrices]
MVErrorsCGC = [std_error_dollar_market_share(prices) for prices in CGCPrices]
marketShareErrors = [ 100 * 1 / (1 + PSAMarketVolumeByGrade[n] / CGCMarketVolumeByGrade[n])**2 
                     * math.sqrt((MVErrorsPSA[n]/PSAMarketVolumeByGrade[n])**2 + (MVErrorsCGC[n]/CGCMarketVolumeByGrade[n])**2) for n in range(len(MVErrorsPSA))]
sampleSize = len(items) - nSkippedItems

itemCountByGradePSA = [len([1 for item in items if item['grade'] != '' and get_common_grade(item) == grade and item['company'] == 'PSA']) for grade in commonGrades]
itemCountByGradeCGC = [len([1 for item in items if item['grade'] != '' and get_common_grade(item) == grade and item['company'] == 'CGC']) for grade in commonGrades]
itemMarketShareByGrade = [100 * itemCountByGradeCGC[n] / (itemCountByGradeCGC[n] + itemCountByGradePSA[n]) for n in range(len(commonGrades))] 
itemMarketShareErrors = [100 * std_error_item_market_share(itemCountByGradePSA[n], itemCountByGradeCGC[n]) for n in range(len(itemCountByGradePSA))]

plt.figure(1)
# plt.axhline(y=overallAvgMarketShare, color='r', linestyle='--')
plt.axhline(y=overallItemMarketShare, color='r', linestyle='--')
plt.errorbar(commonGrades, itemMarketShareByGrade, yerr=itemMarketShareErrors, c = 'k', fmt='o')
plt.errorbar(commonGrades, marketShareByGrade, yerr=marketShareErrors, c='g', fmt='o')
plt.title(f"CGC Market Share by Card's Grade (n={sampleSize})")
plt.xlabel("Card's Grade (rounded down except CGC9.5 = PSA10)")
plt.ylabel("CGC Market Share (%)")
plt.xticks(rotation = -80)
plt.ylim([0,100])

# Market Share by PSA9Price:
minPrice = 30
maxPrice = 19999.1
f = 5/3
maxExponent = math.ceil(math.log(20000)/math.log(1.5) - 1)
priceRanges = [[round_2sigfigs(minPrice * f**n), round_2sigfigs(minPrice * f**(n+1))] for n in range(maxExponent)]
CGCMarketVolumeByPrice = [0 for n in range(len(priceRanges))]
PSAMarketVolumeByPrice = [0 for n in range(len(priceRanges))]
CGCPrices = [[] for n in range(len(priceRanges))]
PSAPrices = [[] for n in range(len(priceRanges))]
nSkippedItems = 0
for item in items:
    if item['PSA9Price'] == '' or float(item['PSA9Price']) < minPrice:
        nSkippedItems += 1
        continue
    price = float(item['PSA9Price'])
    priceIndex = priceRanges.index([p for p in priceRanges if p[0] <= price < p[1]][0])
    if item['company'] == 'PSA':
        PSAMarketVolumeByPrice[priceIndex] += item['price']
        PSAPrices[priceIndex].append(item['price'])
    else:
        CGCMarketVolumeByPrice[priceIndex] += item['price']
        CGCPrices[priceIndex].append(item['price'])
marketShareByPrice = [100 * CGCMarketVolumeByPrice[n] / (CGCMarketVolumeByPrice[n] + PSAMarketVolumeByPrice[n]) 
                      if CGCMarketVolumeByPrice[n] + PSAMarketVolumeByPrice[n] > 0 else 0
                      for n in range(len(CGCMarketVolumeByPrice))]
indicesToRemove = [n for n in range(len(marketShareByPrice)) if marketShareByPrice[n] == 0]
MVErrorsPSA = [std_error_dollar_market_share(prices) for prices in PSAPrices]
MVErrorsCGC = [std_error_dollar_market_share(prices) for prices in CGCPrices]
marketShareErrors = [100 * 1 / (1 + PSAMarketVolumeByPrice[n] / CGCMarketVolumeByPrice[n])**2 
                     * math.sqrt((MVErrorsPSA[n]/PSAMarketVolumeByPrice[n])**2 
                                 + (MVErrorsCGC[n]/CGCMarketVolumeByPrice[n])**2) 
                     if PSAMarketVolumeByPrice[n] > 0 and CGCMarketVolumeByPrice[n] > 0 else 0.2
                     for n in range(len(MVErrorsPSA))]
MVErrorsPSA = [std_error_dollar_market_share(PSAPrices[n]) for n in range(len(MVErrorsPSA)) if n not in indicesToRemove]
MVErrorsCGC = [std_error_dollar_market_share(CGCPrices[n]) for n in range(len(MVErrorsCGC)) if n not in indicesToRemove]
marketShareByPrice = [marketShareByPrice[n] for n in range(len(marketShareByPrice)) if n not in indicesToRemove]
marketShareErrors = [marketShareErrors[n] for n in range(len(marketShareErrors)) if n not in indicesToRemove]
sampleSize = len(items) - nSkippedItems

itemCountByPSA9PrPSA = [len([1 for item in items if item['PSA9Price'] != '' and priceRange[0] <= float(item['PSA9Price']) < priceRange[1] and item['company'] == 'PSA']) 
                       for priceRange in priceRanges]
itemCountByPSA9PrCGC = [len([1 for item in items if item['PSA9Price'] != '' and priceRange[0] <= float(item['PSA9Price']) < priceRange[1] and item['company'] == 'CGC']) 
                       for priceRange in priceRanges]
itemIndicesToRemove = [n for n in range(len(priceRanges)) if itemCountByPSA9PrPSA[n] == 0]
itemCountByPSA9PrPSA = [itemCountByPSA9PrPSA[n] for n in range(len(priceRanges)) if n not in itemIndicesToRemove]
itemCountByPSA9PrCGC = [itemCountByPSA9PrCGC[n] for n in range(len(priceRanges)) if n not in itemIndicesToRemove]
itemMarketShareByPSA9Pr = [100 * itemCountByPSA9PrCGC[n] / (itemCountByPSA9PrCGC[n] + itemCountByPSA9PrPSA[n]) 
                           for n in range(len(itemCountByPSA9PrCGC))]
itemMarketShareErrors = [100 * std_error_item_market_share(itemCountByPSA9PrPSA[n], itemCountByPSA9PrCGC[n]) for n in range(len(itemCountByPSA9PrPSA))]

plt.figure(2)
strPriceRanges = [str(priceRanges[n]) for n in range(len(priceRanges)) if n not in indicesToRemove]
strItemPriceRanges = [str(priceRanges[n]) for n in range(len(priceRanges)) if n not in itemIndicesToRemove]
# plt.axhline(y=overallAvgMarketShare, color='r', linestyle='--')
plt.axhline(y=overallItemMarketShare, color='r', linestyle='--')
# plt.errorbar(strPriceRanges, marketShareByPrice, yerr=marketShareErrors, fmt='o')
plt.errorbar(strItemPriceRanges, itemMarketShareByPSA9Pr, yerr=itemMarketShareErrors, fmt='o', c='k')
plt.title(f"CGC Market Share by Card's PSA 9 Price (n={sampleSize})")
plt.xlabel("Card's PSA 9 Price")
plt.ylabel("CGC Market Share (%)")
plt.xticks(rotation = -80)
plt.ylim([0,100])
plt.show()

# Market Share by sale price:
minPrice = 30
maxPrice = 19999.1
f = 5/3
maxExponent = math.ceil(math.log(20000)/math.log(1.5) - 1)
priceRanges = [[round_2sigfigs(minPrice * f**n), round_2sigfigs(minPrice * f**(n+1))] for n in range(maxExponent)]
CGCMarketVolumeByPrice = [0 for n in range(len(priceRanges))]
PSAMarketVolumeByPrice = [0 for n in range(len(priceRanges))]
CGCPrices = [[] for n in range(len(priceRanges))]
PSAPrices = [[] for n in range(len(priceRanges))]
nSkippedItems = 0
for item in items:
    price = item['price']
    if item['price'] < minPrice:
        nSkippedItems += 1
        continue
    priceIndex = priceRanges.index([p for p in priceRanges if p[0] <= price < p[1]][0])
    if item['company'] == 'PSA':
        PSAMarketVolumeByPrice[priceIndex] += item['price']
        PSAPrices[priceIndex].append(item['price'])
    else:
        CGCMarketVolumeByPrice[priceIndex] += item['price']
        CGCPrices[priceIndex].append(item['price'])
marketShareByPrice = [100 * CGCMarketVolumeByPrice[n] / (CGCMarketVolumeByPrice[n] + PSAMarketVolumeByPrice[n]) 
                      if CGCMarketVolumeByPrice[n] + PSAMarketVolumeByPrice[n] > 0 else 0
                      for n in range(len(CGCMarketVolumeByPrice))]
indicesToRemove = [n for n in range(len(marketShareByPrice)) if marketShareByPrice[n] == 0]
MVErrorsPSA = [std_error_dollar_market_share(prices) for prices in PSAPrices]
MVErrorsCGC = [std_error_dollar_market_share(prices) for prices in CGCPrices]
marketShareErrors = [100 * 1 / (1 + PSAMarketVolumeByPrice[n] / CGCMarketVolumeByPrice[n])**2 
                     * math.sqrt((MVErrorsPSA[n]/PSAMarketVolumeByPrice[n])**2 
                                 + (MVErrorsCGC[n]/CGCMarketVolumeByPrice[n])**2) 
                     if PSAMarketVolumeByPrice[n] > 0 and CGCMarketVolumeByPrice[n] > 0 else 0.2
                     for n in range(len(MVErrorsPSA))]
MVErrorsPSA = [std_error_dollar_market_share(PSAPrices[n]) for n in range(len(MVErrorsPSA)) if n not in indicesToRemove]
MVErrorsCGC = [std_error_dollar_market_share(CGCPrices[n]) for n in range(len(MVErrorsCGC)) if n not in indicesToRemove]
marketShareByPrice = [marketShareByPrice[n] for n in range(len(marketShareByPrice)) if n not in indicesToRemove]
marketShareErrors = [marketShareErrors[n] for n in range(len(marketShareErrors)) if n not in indicesToRemove]
strPriceRanges = [str(priceRanges[n]) for n in range(len(priceRanges)) if n not in indicesToRemove]
sampleSize = len(items) - nSkippedItems

itemCountBySalePrPSA = [len([1 for item in items if item['price'] != '' and priceRange[0] <= float(item['price']) < priceRange[1] and item['company'] == 'PSA']) 
                       for priceRange in priceRanges]
itemCountBySalePrCGC = [len([1 for item in items if item['price'] != '' and priceRange[0] <= float(item['price']) < priceRange[1] and item['company'] == 'CGC']) 
                       for priceRange in priceRanges]
itemIndicesToRemove = [n for n in range(len(priceRanges)) if itemCountBySalePrPSA[n] == 0]
itemCountBySalePrPSA = [itemCountBySalePrPSA[n] for n in range(len(priceRanges)) if n not in itemIndicesToRemove]
itemCountBySalePrCGC = [itemCountBySalePrCGC[n] for n in range(len(priceRanges)) if n not in itemIndicesToRemove]
itemMarketShareBySalePr = [100 * itemCountBySalePrCGC[n] / (itemCountBySalePrCGC[n] + itemCountBySalePrPSA[n]) 
                           for n in range(len(itemCountBySalePrCGC))]
itemMarketShareErrors = [100 * std_error_item_market_share(itemCountBySalePrPSA[n], itemCountBySalePrCGC[n]) for n in range(len(itemCountBySalePrPSA))]
# itemCountByPSA9PrPSA = [len([1 for item in items if item['PSA9Price'] != '' and priceRange[0] <= float(item['PSA9Price']) < priceRange[1] and item['company'] == 'PSA']) 
#                        for priceRange in priceRanges]
# itemCountByPSA9PrCGC = [len([1 for item in items if item['PSA9Price'] != '' and priceRange[0] <= float(item['PSA9Price']) < priceRange[1] and item['company'] == 'CGC']) 
#                        for priceRange in priceRanges]
# itemIndicesToRemove = [n for n in range(len(priceRanges)) if itemCountByPSA9PrPSA[n] == 0]
# itemCountByPSA9PrPSA = [itemCountByPSA9PrPSA[n] for n in range(len(priceRanges)) if n not in itemIndicesToRemove]
# itemCountByPSA9PrCGC = [itemCountByPSA9PrCGC[n] for n in range(len(priceRanges)) if n not in itemIndicesToRemove]
# itemMarketShareByPSA9Pr = [itemCountByPSA9PrCGC[n] / (itemCountByPSA9PrCGC[n] + itemCountByPSA9PrPSA[n]) 
#                            for n in range(len(itemCountByPSA9PrCGC))]
# itemMarketShareErrors = [std_error_item_market_share(itemCountBySalePrPSA[n], itemCountBySalePrCGC[n]) for n in range(len(itemCitemCountBySalePrountBySalePrPSA))]


strItemPriceRanges = [str(priceRanges[n]) for n in range(len(priceRanges)) if n not in itemIndicesToRemove]
strItemPriceUppers = ['< ' + str(priceRanges[n][1]) for n in range(len(priceRanges)) if n not in itemIndicesToRemove]
plt.figure(2)
# plt.axhline(y=overallAvgMarketShare, color='r', linestyle='--')
plt.axhline(y=overallItemMarketShare, color='r', linestyle='--')
# plt.errorbar(strPriceRanges, marketShareByPrice, yerr=marketShareErrors, fmt='o')
plt.errorbar(strItemPriceUppers, itemMarketShareBySalePr, yerr=itemMarketShareErrors, fmt='o', c = 'k')
plt.title(f"CGC Market Share by Sale Price (n={sampleSize})")
plt.xlabel("Card's Sale Price ($)")
plt.ylabel("CGC Market Share (%)")
plt.xticks(rotation = -60)
plt.ylim([0,100])
plt.show()

# overall Stats:
print("Overall market share by item is", round(overallItemMarketShare,2), "%")
cgcDollars = sum([item['price'] for item in items if item['company'] == 'CGC'])
allDollars = sum([item['price'] for item in items])
print("Overall market share by the dollar is", round(100*cgcDollars/allDollars,2), "%")
print()

# isError:
errorMarketVolumeCGC = sum([item['price'] for item in items if item['isError'] and item['company'] == 'CGC'])
errorMarketShare = 100 * errorMarketVolumeCGC / sum([item['price'] for item in items if item['isError']])
errorItemMarketShare = 100 * len([1 for item in items if item['isError'] and item['company'] == 'CGC']) \
    / len([1 for item in items if item['isError']])
print("Error market share by the dollar is", errorMarketShare, "=", round(100 * (errorMarketShare/overallAvgMarketShare - 1),2), 
      "% more than average.")
print("Error market share by item is", errorItemMarketShare, "=", round(100 * (errorItemMarketShare/overallItemMarketShare - 1),2), 
      "% more than average.")
print()
# japanese:
jpMarketVolumePSA = sum([item['price'] for item in items if item['language'] == 'Japanese' and item['company'] == 'PSA'])
jpMarketVolumeCGC = sum([item['price'] for item in items if item['language'] == 'Japanese' and item['company'] == 'CGC'])
jpItemMarketShare = 100 * len([1 for item in items if item['language'] == 'Japanese' and item['company'] == 'CGC']) \
    / len([item for item in items if item['language'] == 'Japanese'])
jpMarketShare = 100 * jpMarketVolumeCGC / (jpMarketVolumeCGC + jpMarketVolumePSA)
print("Japanese market share by the dollar is", jpMarketShare, "=", round(100 * (jpMarketShare/overallAvgMarketShare - 1),2), 
      "% more than average.")
print("Japanese market share by item is", jpItemMarketShare, "=", round(100 * (jpItemMarketShare/overallItemMarketShare - 1),2), 
      "% more than average.")