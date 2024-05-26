import csvimport as cv
import re
import csv
import datetime
import statistics as stats
import matplotlib.pyplot as plt
import numpy as np

# to do:
# add in detection of query

import_filepaths = \
[
    "data step 2 - enriched with shoppingapi, completed/ebay_sold_step2_enriched_with_shoppingapi-2021-08-17-07.51.17 - with added sold dates from html.csv",
#    "data step 2 - enriched with shoppingapi, completed/ebay_sold_step2_enriched_with_shoppingapi-2021-11-22-09.32.32 - original pull.csv",
    "data step 2 - enriched with shoppingapi, completed/ebay_sold_step2_enriched_with_shoppingapi-2021-12-06-09.43.12 - combination of all november pulls and pickles so far.csv"
]

columnsToConvert = [
    {
     'columnName': 'titleIsPerfect',
     'newType': 'bool'
    },
    
    {
     'columnName': 'titleError',
     'newType': 'bool'
    },
    
    {
     'columnName': '1stEdition',
     'newType': 'bool'
    },
    
    {
     'columnName': 'shadowless',
     'newType': 'bool'
    },
    
    {
     'columnName': 'hasItemSpecifics',
     'newType': 'bool'
    },
    {
     'columnName': 'itemID',
     'newType': 'int'
    },
]

tables = [cv.importcsv(filepath) for filepath in import_filepaths]
table_header_rows = [t[0] for t in tables]

headers = set([colname for hrow in table_header_rows for colname in hrow])
headers.add('dataSetIndex')
items0 = []


# fill missing values with None when tables are missing columns
for n in range(len(tables)):
    table = tables[n]
    header = table[0]
    missingHeaders = {h for h in headers if h not in header and h!='dataSetIndex'}
    for row in table[1:]:
        item = {header[m] : row[m] for m in range(len(header))}
        dataSetNumber = n
        item['dataSetIndex'] = dataSetNumber
        itemMissingValues = {mh : None for mh in missingHeaders}
        item = {**item, **itemMissingValues}
        items0.append(item)

# convert types of item values
for item in items0:
    for htc in columnsToConvert:
        columnName = htc['columnName']
        newType = htc['newType']
        if newType.lower() in ['b', 'bool']:
            val = item[columnName]
            if val.lower() in ['true', 't', 'yes', 'y', 'on', '1']:
                item[columnName] = True
            elif val.lower() in ['false', 'f', 'yes', 'n', 'off', '0']:
                item[columnName] = False
            else:
                raise Exception(f"Error: Unable to convert string value '{val}' to a boolean. itemID {item['itemID']}, column {columnName}")
        elif newType.lower() in ['i', 'int']:
            item[columnName] = int(item[columnName])
        else:
            raise Exception("Error: Type conversion unsuccessful. Non-recognized type.")


pokemon_sets = []
with open("pokemon sets.csv", "r", encoding="utf-8-sig") as f:
    reader = csv.reader(f, delimiter=",")
    for row in reader:
        pokemon_sets.append(
            {
                'name': row[0],
                 'cardsInSet': row[1],
                 'denominator': row[2],
                 'yearOfRelease': row[3],
                 'monthOfRelease': row[4],
                 'setNumHasLeadingZeroes': True if row[5] == 'TRUE' else False if row[5] == 'FALSE' else ''
            }
        )
pokemon_sets = pokemon_sets[1:]
setnames = [pokeset['name'].lower() for pokeset in pokemon_sets]
setreleases = {pset['name'].lower() : 
               {
                   'year': pset['yearOfRelease'],
                   'month': pset['monthOfRelease']
                }
               for pset in pokemon_sets}
setreleases['base set shadowless'] = {
                   'year': '1999',
                   'month': '1'
                }
def identify_set_from_setstring(setstring, language):
    if not setstring:
        return ''
    if language not in ['', 'English']:
        return ''
    if 'promo' in setstring:
        return ''
    special_case_sets_for_setstring = ['base set', 'team rocket', 
                                 'ex ruby & sapphire',  'platinum', 'emerald'
                                 'diamond & pearl',
                                 'heartgold & soulsilver', 'xy base', 'sun & moon', 
                                 'sword & shield',]
    other_sets = [setname for setname in setnames if setname not in special_case_sets_for_setstring]
    for setname in other_sets:
        if setname in setstring:
            return setname
    
    if 'sandstorm' in setstring: return "ex sandstorm"
    if 'team magma v' in setstring: return "ex team magma vs team aqua"
    if 'hidden legends' in setstring: return "ex hidden legends"
    if all(x in setstring for x in ['fire','red','leaf','green']): 
        return "ex firered & leafgreen"
    if 'rocket returns' in setstring: return "ex team rocket returns"
    if 'unseen forces' in setstring: return "ex unseen forces"
    if 'delta species' in setstring: return "ex delta species"
    if 'legend maker' in setstring: return "ex legend maker"
    if 'holon phantoms' in setstring: return "ex holon phantoms"
    if 'crystal guardians' in setstring: return "ex crystal guardians"
    if 'dragon frontiers' in setstring: return "ex dragon frontiers"
    if 'power keepers' in setstring: return "ex power keepers"
    if 'champion' in setstring and 'path' in setstring: return "champion's path"
    
    base_kws = ['ruby', 'diamond', 'pearl', 'dp', 'black', 'b&w'
                        'xy', 'x y', 'x and y', 'x&y', 'x & y', '146', 
                        'sun', 'moon', 's&m' '149', 'sword', 'swsh', '202', 
                        'evolutions', 'like base']
    if any(x in setstring for x in ['xy','x y', 'x&y', 'x & y', 'x and y', 'x + y']) \
        and 'base' in setstring: 
        return "xy base"
    if 'diamond' in setstring and 'pearl' in setstring and 'base' in setstring: 
        return "diamond & pearl"
    if (
        (all(x in setstring for x in ['heart','gold','soul','silver']) or 'hgss' in setstring)
        and all(x not in setstring for x in ['unleashed', 'undaunted','triumphant', 'legends'])
        ):
           return "heartgold & soulsilver"
    if 'black' in setstring and 'white' in setstring and 'base' in setstring: 
        return "black & white"
    if 'sun' in setstring and 'moon' in setstring and 'base' in setstring: 
        # we get quite a few missed cards from each respective base set. 
        # with more time, I could make the filters better.
        return "sun & moon"
    if 'sword' in setstring and 'shield' in setstring and 'base' in setstring:
        return "sword & shield"
    
    if 'base' in setstring and all(x not in setstring for x in base_kws 
                                    + ['set 2', '130', '109', '114']):
        return 'base set'
    if 'team rocket' in setstring:
        return 'team rocket'
    
    return ''

def titlecase(s):
    return re.sub(r"[A-Za-z]+('[A-Za-z]+)?", lambda mo: mo.group(0).capitalize(), s)
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
items = []
bestOfferFiltered = 0
notStandardSizeFiltered = 0
lowPriceFiltered = 0
incorrectYearFiltered = 0
legendaryCollectionFiltered = 0
manuallyFiltered = 0

# cards below this price are excluded.
# The price minimum is date-dependent because the cutoff changed for unreliable data as market fell.
lowPriceLimit1 = 20 # Previously, price limit was 20 for all cards. This was really the PSA cutoff.
lowPriceLimitCGC2 = 3  # 3 for cgc nov 12. 5 for psa nov 12, which I need to cut off later manually.
lowPriceLimitPSA2 = 5  # This is based on looking at the eBay data.

manuallyRemovedItemIDsString = input("Please enter, if you have it, a list of itemIDs to ignore. This is usually "
                       "based on eBay search sorted by low price and manual extraction.\n"
                       "Format is itemID1, itemID2, ..., or just press enter to keep all itemIDs.")
manuallyRemovedItemIDsString.replace(' ', '')
if len(manuallyRemovedItemIDsString) > 0:
    manuallyRemovedItemIDs = [int(iid) for iid in manuallyRemovedItemIDsString.split(',')]
else:
    manuallyRemovedItemIDs = []

print("Cleaning and transforming data. Please wait...")
for item0 in items0:
    if 'BestOffer' in item0['listingType']:
        # we can't handle this unless slabwatch starts working again
        bestOfferFiltered += 1
        continue
    if any(x in item0['title'] for x in ['carddass', 'cardass', 'carddas', 'topsun',
                                          'sealdass', 'shieldus', 'topps', 'jumbo', 
                                          'pokedex mini', 'top sun', 'sticker', 'stickers',
                                          'lenticular']):
        # skip non-standard size cards as cgc does not grade them at the moment.
        notStandardSizeFiltered += 1
        continue
    price = float(item0['price'])
    if item0['dataSetIndex'] == 0:
        if price < lowPriceLimit1:
            # refine this later. Many low-price items are not actually graded.
            lowPriceFiltered += 1
            continue

    if item0['titleGrade']:
        grade = item0['titleGrade']
    elif item0['grade']:
        grade = item0['grade']
    else:
        grade = ""
    # the next 3 lines only matter for data older than aug 19, when this 
    # check was added to soup-extract-IDs
    grade = grade.strip(".")
    if grade[-2:] == '.0': grade = grade[:-2]
    if grade != '' and not 0 < float(grade) <= 10: grade= ""
    
    # for data older than aug 19 we can remove the grade 10 check. It was included in 
    # ebay_sold_get.py.
    if item0['titleIsPerfect'] and grade == '10':
        grade = grade + ' Perfect'
    
    if not item0['features']: features = []
    elif item0['features'][0] == '[': features = list(item0['features'])
    else: features = [item0['features']]
    
    isError = True if item0['titleError'] or 'Error' in features else False
    is1stEdition = item0['1stEdition'] # "features" can have 1st edition, but idk if i trust it.
    
    if item0['titleLanguage']:
        language = item0['titleLanguage'].title()
    elif not item0['language']:
        language = ''
    else:
        # now try to get language from the ebay property
        en = ['english']
        jp = ['jp', 'jap']
        es = ['spanish', 'espan']
        zh = ['zh', 'chinese']
        nl = ['nl', 'dutch']
        fr = ['fr', 'french', 'francais']
        de = ['de', 'german', 'deutsch']
        it = ['italian', 'italiano']
        ko = ['korean']
        pt = ['portug']
        ru = ['ru']
        langs = []
        titleLangLower = item0['language'].lower()
        if any(x in titleLangLower for x in en): langs.append('English')
        if any(x in titleLangLower for x in jp): langs.append('Japanese')
        if any(x in titleLangLower for x in es): langs.append('Spanish')
        if any(x in titleLangLower for x in zh): langs.append('Chinese')
        if any(x in titleLangLower for x in nl): langs.append('Dutch')
        if any(x in titleLangLower for x in fr): langs.append('French')
        if any(x in titleLangLower for x in de): langs.append('German')
        if any(x in titleLangLower for x in it): langs.append('Italian')
        if any(x in titleLangLower for x in ko): langs.append('Korean')
        if any(x in titleLangLower for x in pt): langs.append('Portuguese')
        if any(x in titleLangLower for x in ru): langs.append('Russian')
        if len(langs) == 1:
            language = langs[0]
        else:
            language = ''
    
    
    if not item0['set'] or item0['set'][0] == '[' or any(x in item0['set'] for x in ['#',';']): 
        item0['set'] = ''
    else: 
        item0['set'] = titlecase(item0['set'])
        
    if item0['titleSet']:
        cardSet = item0['titleSet']
    else:
        cardSet = identify_set_from_setstring(item0['set'], language)
    if cardSet.lower() == 'legendary collection':
        legendaryCollectionFiltered += 1
        continue
    if item0['shadowless'] and not is1stEdition:
        cardSet += ' shadowless'
    if cardSet:
        releaseYear = setreleases[cardSet]['year']
        releaseMonth = setreleases[cardSet]['month']
    else:
        releaseMonth = ''
        try:
            if int(item0['yearManufactured']) < 1995 or int(item0['yearManufactured']) > 2021:
                incorrectYearFiltered += 1
                continue
            else:
                releaseYear = str(int(item0['yearManufactured']))
        except ValueError:
            releaseYear = ''
    if is1stEdition and cardSet:
        if (cardSet == 'base set' 
            and 'machamp' in item0['title'].lower() 
            and 'shadowless' not in item0['title'].lower()):
            cardSetWith1st = cardSet
        else:
            cardSetWith1st = cardSet + ' 1st edition'
    else:
        cardSetWith1st = cardSet
    if cardSet and item0['titleSetNum'] and (cardSet == 'base set shadowless' 
        or pokemon_sets[setnames.index(cardSet)]['setNumHasLeadingZeroes'] == False):
        setNum = item0['titleSetNum'].lstrip('0')
    elif cardSet and item0['titleSetNum'] and \
        pokemon_sets[setnames.index(cardSet)]['setNumHasLeadingZeroes'] == True:
        numDigitsNeeded = len(pokemon_sets[setnames.index(cardSet)]['denominator'])
        diff = numDigitsNeeded - len(item0['titleSetNum'])
        setNum = '0' * diff + item0['titleSetNum']
    else:
        setNum = ''
        
    if int(item0['itemID']) in manuallyRemovedItemIDs:
        manuallyFiltered += 1
        continue
        
    item = dict()
    item['title'] = item0['title']
    item['company'] = item0['companySearched']
    item['listingType'] = item0['listingType']
    item['itemID'] = item0['itemID']
    item['grade'] = grade
    item['isError'] = isError
    item['language'] = language.title()
    item['set'] = cardSetWith1st
    item['setNum'] = setNum
    item['releaseYear'] = releaseYear
    item['releaseMonth'] = releaseMonth
    item['location'] = item0['location']
    item['country'] = item0['country']
    item['price'] = price
    item['era'] = era(releaseYear)
    item['dataSetIndex'] = item0['dataSetIndex']
    item['endTime'] = item0['eBayItemEndTime']
    items.append(item)

# adjust the price, because BIN price is generally more than auction price.
# create a curve of auctionToBINRatio as a function of price.
# create a dictionary of uItems, which are unique items - meaning one for each unique card (not each sale)

uItems = dict()
for n in range(len(items)):
    item = items[n]
    if any(x not in item for x in ['set', 'setNum', 'company', 'grade']):
        continue
    uName = uniqueName = item['set'] + ' #' + item['setNum'] + ' ' \
        + item['company'] + ' ' + item['grade']
    if uName not in uItems:
        uItems[uName] = {
            'itemList' : [item], 
            'set' : item['set'],
            'setNum' : item['setNum'],
            'company' : item['company'],
            'grade' : item['grade']
            }
    else:
        uItems[uName]['itemList'].append(item)
# remove outlier prices
def dropOutlierPrices(listings):
    # this algorithm isn't good for small samples
    # because the 20th or 80th percentile can be the outlier itself.
    # for example it doesn't work on [168,305,330,1124]
    if len(listings) <= 3:
        outlierIDs = []
        return listings, outlierIDs
    listings.sort(key = lambda lst: lst['price'])
    index20Percentile = round(len(listings)/5)
    index80Percentile = min(round(len(listings) * 4/5), len(listings) - 1)
    distance2080 = listings[index80Percentile]['price'] - listings[index20Percentile]['price']
    lowerBd = listings[index20Percentile]['price'] - 1/3 * distance2080
    upperBd = listings[index80Percentile]['price'] + 1/3 * distance2080
    listingsNew = [lst for lst in listings if lowerBd <= lst['price'] <= upperBd]
    outlierIDs = [lst['itemID'] for lst in listings if lst['price'] < lowerBd or lst['price'] > upperBd]
    return listingsNew, outlierIDs

outlierItemIDs = []
for uName in uItems:
    itemList = uItems[uName]['itemList']
    oldLen = len(itemList)
    itemList, outlierIDs = dropOutlierPrices(itemList)
    uItems[uName]['itemList'] = itemList
    outlierItemIDs.extend(outlierIDs)
numPriceOutliers = len(outlierItemIDs)
items = [item for item in items if item['itemID'] not in outlierItemIDs]


BINprices = []
auctionBINratios = []
sampleSizes = []
for uName in uItems:
    theseBINprices = [item['price'] for item in uItems[uName]['itemList'] 
                 if item['listingType'] == 'BuyItNow']
    theseAuctionPrices = [item['price'] for item in uItems[uName]['itemList'] 
                 if item['listingType'] == 'Auction']
    if not theseBINprices or not theseAuctionPrices:
        continue
    BINprice = stats.mean(theseBINprices)
    auctionBINratio = stats.mean(theseAuctionPrices) / BINprice
    if auctionBINratio > 5 or auctionBINratio < 0.2:
        continue
    BINprices.append(BINprice)
    auctionBINratios.append(auctionBINratio)
    sampleSizes.append(min(len(theseBINprices), len(theseAuctionPrices)))

def binned_graph(xvals, yvals, weights = [], numBins = 5):
    if not weights:
        weights = [1 for x in xvals]
    pairs = list(zip(xvals,yvals))
    pairs.sort(key = lambda x: x[0])
    xvals = [p[0] for p in pairs]
    yvals = [p[1] for p in pairs]
    
    weightedSampleSize = sum(weights)
    binSize = weightedSampleSize // numBins + 1
    xNew = []
    yNew = []
    iW = 0  # from 0 ... sum(weights)
    i = 0   # from 0 ... len(xvals)
    previousBinFraction = 0
    for iBin in range(numBins):
        # iW = iWeighted is from 0 ... sum(weights)
        maxWIndex = min(binSize * (iBin + 1), weightedSampleSize) - 1
        avgXNumer = 0
        avgYNumer = 0
        denom = 0
        if i > 0:
            avgXNumer += xvals[i-1] * weights [i-1] * (1 - previousBinFraction)
            avgYNumer += yvals[i-1] * weights [i-1] * (1 - previousBinFraction)
            denom += weights[i-1] * (1 - previousBinFraction)
        while iW <= maxWIndex and i < len(xvals):
            if iW + weights[i] > maxWIndex + binSize:
                raise Exception("binned_graph failed because a single point spanned 3 different bins.")
            atEndOfBin = True if iW + weights[i] > maxWIndex else False
            binFraction = (maxWIndex + 1 - iW ) / weights[i] if atEndOfBin else 1
            avgXNumer += xvals[i] * weights [i] * binFraction
            avgYNumer += yvals[i] * weights [i] * binFraction
            denom += weights[i] * binFraction
            iW += weights[i]
            i += 1
            if atEndOfBin:
                previousBinFraction = binFraction
        avgX = avgXNumer / denom
        avgY = avgYNumer / denom
        xNew.append(avgX)
        yNew.append(avgY)
    return xNew, yNew

def binned_graph_with_fixed_ranges(xVals, yVals, rangeIncreaseFactor, rangeMin, minSampleSizePerBin, weights = [],):
    if not weights:
        weights = [1 for x in xVals]
    if not xVals:
        return [], [], []
    xMax = max(xVals)
    xNew = []
    yNew = []
    sampleSizes = []
    while rangeMin < xMax:
        rangeMax = rangeMin * rangeIncreaseFactor
        nVals = [n for n in range(len(xVals)) if rangeMin <= xVals[n] < rangeMax]
        thisBinSampleSize = sum([weights[n] for n in nVals])
        if thisBinSampleSize < minSampleSizePerBin:
            rangeMin = rangeMin * rangeIncreaseFactor
            continue
        xAvg = sum([xVals[n] * weights[n] for n in nVals])/ thisBinSampleSize
        yAvg = sum([yVals[n] * weights[n] for n in nVals])/ thisBinSampleSize
        xNew.append(xAvg)
        yNew.append(yAvg)
        sampleSizes.append(thisBinSampleSize)
        rangeMin = rangeMin * rangeIncreaseFactor
    return xNew, yNew, sampleSizes
BINpricesB, auctionBINratiosB = binned_graph(BINprices, auctionBINratios, 
                                             weights = sampleSizes, numBins = 3)
# plt.scatter(BINpricesB, auctionBINratiosB)
# plt.show()
def linear_interp(x, xvals, yvals):
    if x <= xvals[0]:
        return yvals[0]
    if x >= xvals[-1]:
        return yvals[-1]
    for n in range(1, len(xvals)):
        if x > xvals[n]:
            continue
        # now n is the upper bound
        x1, y1 = xvals[n-1], yvals[n-1]
        x2, y2 = xvals[n],   yvals[n]
        m = (y2 - y1) / (x2 - x1)
        y = y1 + m * (x2 - x1)
        return y

def binAuctionRatio(price):
    return linear_interp(price, BINpricesB, auctionBINratiosB)

# replace prices with estimated BIN price
for item in items:
    if item['listingType'] == 'Auction':
        item['price'] = 1 / binAuctionRatio(price) * item['price']
    del item['listingType']
def determine_if_setnums_have_leading_zeroes(pokemon_sets, items):
    # this is imperfect but gave some indication of which sets have leading zeroes.
    # then the questionable ones were checked manually.
    # it seems that everything after sword and shield base has had leading zeroes in set nums.
    for n in range(len(setnames)):
        setname = setnames[n].lower()
        setNumsFound = [item['setNum'] for item in items if 
                        item['set'] == setname 
                        and item['language'] in ['English', '']
                        and item['setNum'] != '' 
                        and all(x.isnumeric() for x in item['setNum']) 
                        and 1 <= int(item['setNum']) <= 9]
        setNumLengths = {digits : len([sn for sn in setNumsFound if len(sn) == digits]) for digits in [1,2,3,4]}
        setNumDigits = max(setNumLengths, key = setNumLengths.get)
        setNumDigitsCount = setNumLengths[setNumDigits]
        setNumHasLeadingZeroes = True if setNumDigits > 1 \
            and setNumLengths[setNumDigits]/(setNumLengths[1] + setNumDigitsCount) > 0.25 \
            else False
        pokemon_sets[n]['setNumHasLeadingZeroes'] = setNumHasLeadingZeroes
    with open('pokemon sets new.csv', 'w', encoding = 'UTF-8') as csvfile:
        writer = csv.writer(csvfile, lineterminator = '\n')
        writer.writerow(['set name', 'cards in set', 'denominator', 
                          'year of release', 'month of release', 'setNumHasLeadingZeroes'])
        for row in pokemon_sets:
            row = [row[key] for key in pokemon_sets[0].keys()]
            writer.writerow(row)

# Add an estimated PSA 9 price to each row. 
uCards = dict()
for item in items:
    if item['set'] == '' or item['setNum'] == '' or item['grade'] == '':
        continue
    cardName = item['set'] + ' #' + item['setNum']
    if cardName not in uCards:
        uCards[cardName] = {'itemList' : [item]}
    else:
        uCards[cardName]['itemList'].append(item)
# for every company and grade combo besides PSA 9,
# have a list of companyGradePrice and corresponding list of PSA9Ratio
# so that we can then infer stuff.
# Right now we are using binned_graph. But this interpolation doesn't work well
# for all kinds of different price ranges. It might be better to choose price ranges
# first, and then average all samples in each of those ranges. This could be improved
# on later.
PSA9PricePoints = dict()
for company in ['PSA', 'CGC']:
    PSA9PricePoints[company] = dict()
    for grade in ['4', '4.5', '5', '5.5', '6', '6.5', '7', '7.5', '8', '8.5', '9', '9.5', '10', '10 Perfect']:
        PSA9PricePoints[company][grade] = dict()
        if company + grade == 'PSA9' or company + grade  == 'PSA 10 Perfect':
            continue
        companyGradePrices = []
        PSA9Ratios = []
        PSA9Prices = []
        sampleSizes = []
        gradeFloat = float(grade) if grade != '10 Perfect' else 11
        for uCard in uCards:
            theseCompanyGradePrices = [item['price'] for item in uCards[uCard]['itemList'] 
                               if item['company'] == company and item['grade'] == grade]
            thesePSA9Prices = [item['price'] for item in uCards[uCard]['itemList'] 
                               if item['company'] == 'PSA' and item['grade'] == '9']
            if not (theseCompanyGradePrices and thesePSA9Prices):
                continue
            thisCompanyGradePrice = stats.mean(theseCompanyGradePrices)
            thisPSA9Price = stats.mean(thesePSA9Prices)
            sampleSize = min(len(theseCompanyGradePrices), len(thesePSA9Prices))
            if thisCompanyGradePrice / thisPSA9Price > 1:
                if gradeFloat <= 8:
                    continue
            if thisCompanyGradePrice / thisPSA9Price < 1:
                if company == 'PSA' and grade == '10':
                    continue
            companyGradePrices.append(thisCompanyGradePrice)
            PSA9Ratios.append(thisCompanyGradePrice / thisPSA9Price)
            PSA9Prices.append(thisPSA9Price)
            sampleSizes.append(sampleSize)
        companyGradePricesB, PSA9RatiosB, sampleSizesB = binned_graph_with_fixed_ranges(companyGradePrices, PSA9Ratios,
                                                         rangeIncreaseFactor = 2, rangeMin = 20, minSampleSizePerBin = 4, weights = sampleSizes)
        
        PSA9PricePoints[company][grade]['companyGradePricesB'] = companyGradePricesB
        PSA9PricePoints[company][grade]['PSA9RatiosB'] = PSA9RatiosB
        PSA9PricePoints[company][grade]['sampleSizesB'] = sampleSizesB
        if sum(sampleSizesB) < 30:
            print(f"The total sample size for {company} {grade} is less than 50.")
            if '.5' in grade and not (company + grade == 'PSA9.5'):
                flooredGrade = str(int(gradeFloat))
                PSA9PricePoints[company][grade]['companyGradePricesB'] = \
                    PSA9PricePoints[company][flooredGrade]['companyGradePricesB']
                PSA9PricePoints[company][grade]['PSA9RatiosB'] = \
                    [p * 1.15 for p in PSA9PricePoints[company][flooredGrade]['PSA9RatiosB']] # guessed 15% boost for +0.5 grade
                PSA9PricePoints[company][grade]['sampleSizesB'] = sampleSizesB
            
            
if sum(PSA9PricePoints['CGC']['10']['sampleSizesB']) < 30:
    PSA9PricePoints['CGC']['10']['companyGradePricesB'] = \
                    PSA9PricePoints['PSA']['10']['companyGradePricesB']
    PSA9PricePoints['CGC']['10']['PSA9RatiosB'] = \
        PSA9PricePoints['PSA']['10']['PSA9RatiosB']
if sum(PSA9PricePoints['CGC']['10 Perfect']['sampleSizesB']) < 30:
    PSA9PricePoints['CGC']['10 Perfect']['companyGradePricesB'] = \
                    PSA9PricePoints['PSA']['10']['companyGradePricesB']
    PSA9PricePoints['CGC']['10 Perfect']['PSA9RatiosB'] = \
        [p * 2 for p in PSA9PricePoints['PSA']['10']['PSA9RatiosB']]
    
PSA9PriceEstimates = dict()
PSA9SampleSize = dict()
for cardName in uCards:
    itemList = uCards[cardName]['itemList']
    PSA9PriceSum = 0
    numPSA9Items = len([item for item in itemList if item['company'] + item['grade'] == 'PSA9'])
    PSA9SampleSize[cardName] = numPSA9Items
    if numPSA9Items > 10:
        PSA9PriceEstimates[cardName] = \
            stats.mean([item['price'] for item in itemList if item['company'] + item['grade'] == 'PSA9'])
        continue
    for item in itemList:
        company = item['company']
        grade = item['grade']
        if company + grade == 'PSA9':
            PSA9PriceSum += 3 * item['price']
            continue
        price = stats.mean([it['price'] for it in itemList if it['grade'] == grade and it['company'] == company])
        if grade not in PSA9PricePoints[company]:
            continue
        pricesForEstimation = PSA9PricePoints[company][grade]['companyGradePricesB']
        ratiosForEstimation = PSA9PricePoints[company][grade]['PSA9RatiosB']
        estimatedRatio = linear_interp(x = price, xvals = pricesForEstimation, yvals = ratiosForEstimation)
        thisPSA9PriceEstimate = price * 1 / estimatedRatio
        PSA9PriceSum += thisPSA9PriceEstimate
    if PSA9PriceSum == 0:
        PSA9PriceEstimates[cardName] = ''
    else:
        PSA9PriceEstimate = PSA9PriceSum / (len(itemList) + 2 * numPSA9Items)
        PSA9PriceEstimates[cardName] = PSA9PriceEstimate

for item in items:
    cardName = item['set'] + ' #' + item['setNum']
    item['PSA9Price'] = PSA9PriceEstimates.get(cardName, '')
    item['PSA9SampleSize'] = PSA9SampleSize.get(cardName, '')
    

# plt.scatter(companyGradePricesB,PSA9RatiosB)
# plt.show()

print("Done filtering.")
print(f"Removed {bestOfferFiltered} items because they could be best offer prices.")
print(f"Removed {notStandardSizeFiltered} items because they are non-standard size cards.")
print(f"Removed {lowPriceFiltered} items because they cost too little (likely not rly graded)")
print(f"Removed {incorrectYearFiltered} items because the production year was not between 1995 and now.")
print(f"Removed {numPriceOutliers} price outliers from data.")
print(f"Removed {legendaryCollectionFiltered} items because they were in legendary collection, and "
      + "reverse holos and non-set cards with the same numeration would require better identification (WIP).")
print(f"Removed {manuallyFiltered} item IDs manually. Probably they were fake listings. "
      f"The remaining of {len(manuallyRemovedItemIDs)} manually entered IDs were filtered out in other steps.")
print(f"In total, {len(items)} items remain out of an initial {len(items0)}")

timenow = datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
outputfilename = 'ebay_sold3_cleaned-' + timenow + '.csv'
properties = list(items[0].keys())

with open(outputfilename, 'w', encoding='UTF-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames = properties, lineterminator = '\n')
    writer.writeheader()
    writer.writerows(items)
print(f"Successfully wrote cleaned data to file {outputfilename}.")
print("Have a nice day.")
