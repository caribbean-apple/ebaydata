from ebaysdk.shopping import Connection as shopping
import datetime
import csv
import csvimport as cv
import copy
import ips
import pickle
import time
import random

# This file can get item details for sold listings.
# As input, it needs html files, one for each page of eBay sold results.
# There are (up to) 200 items per page on eBay.
# It uses those pages to extract itemIDs, and then uses the itemIDs to
# get item details for sold listings.
# In my experience, manually saving the .html files takes about 1hr for 50,000 results.

# eBay search query for CGC on nov 12: (taken from bookmarks, unchanged)
# pokemon cgc -(lot,bundle,bundles,mystery) -(gma,sgc,mgc,pca,ksa,cga,ugc,srg,pgc,pgs,mnt,getgraded,ace,dsg) -('get graded',holder) -(proxy,custom,art)
# eBay search query for PSA on nov 12 (taken from bookmarks, removed "or" and "for" from excluded matches in PSA):
# pokemon psa -(cgc,gma,sgc,mgc,pca,ksa,cga,ugc,srg,pgc,pgs,mnt,getgraded,ace,dsg) -(chance,"pack fresh", "never played") -("get graded",candidate,holder,potential,possible,worthy,like,contender,ready,quality) -(proxy,custom,art)

ID_APP = "FelixFei-FelixApp-PRD-27ffb2180-77b6acb3"

if __name__ == "__main__":
    items = dict()
    purposeInt = int(input("Would you like to begin pulling data or continue pulling data by importing a pickle file? Type 0 to begin or 1 to continue: "))
    purpose = "begin" if purposeInt == 0 else "continue"

    if purpose == "begin":
        import_filename = input("Please enter the input filename, with .csv at the end, "
                                + "relative to the base application path: ")
        data = cv.importcsv(import_filename)
        headers = data[0]
        data = data[1:]
        items = dict()
        for row in data:
            item = {headers[n]: row[n] for n in range(len(headers))}
            items[item['itemID']] = item
        numToProcess = len(items)
    if purpose == "continue":
        import_filename = input("Please enter the path of the incomplete pickle items file, with .pickle at the end: ")
        with open(import_filename, 'rb') as pickleFile:
            items = pickle.load(pickleFile)
        itemsPreviouslyCompleted = {itemID: items[itemID] for itemID in items if items[itemID].get('hasItemSpecifics') == True}
        numToProcess = len(itemsPreviouslyCompleted)
        if numToProcess == 0:
            input("ERROR: Previously completed items count is ZERO. Are you sure this is what you want? Enter to continue.")

    input(f"Running shopping api. With {numToProcess} items, this will take {numToProcess//20+1} api calls. The daily call limit for shopping is 2500 calls = 50k items. "
          + "Press enter to continue.")


shopping_api = shopping(appid=ID_APP, config_file = None)
error_messages = []


def try_remove_item(item,lst):
    if lst is None:
        return lst
    try: 
        lst.remove(item)
    except ValueError:
        pass
    return lst

def get_shopping_api_properties(items):
    global error_messages
    # we must query the shopping API 20 items at a time to get more properties
    itemIDsToProcess = [itemID for itemID in list(items.keys()) if items[itemID].get('hasItemSpecifics') != True]
    num_results = len(itemIDsToProcess)
    num_batches = (num_results - 1)//20 + 1
    shopping_response_dicts_debug = []
    temp_debug_invalid_itemid_counter = 0
    timeout_error_count = 0
    chunk_error_count = 0
    for n in range(num_batches):
        lowest_index = 20 * n
        batch_size = 20 if n < num_batches - 1 else num_results - lowest_index
        twenty_item_ids = [itemIDsToProcess[lowest_index + k] for k in range(batch_size)]
        shopping_request = {
            'IncludeSelector': ['Details','Description','ItemSpecifics'],
            'ItemID': twenty_item_ids
            }
        try:
            shopping_response_dict = \
                shopping_api.execute("GetMultipleItems", shopping_request).dict()
        except Exception as e:
            if "Invalid item ID" in str(e):
                print("Found invalid itemID. Exception string:\n", str(e))
                print("Continuing to next value of n. ")
                temp_debug_invalid_itemid_counter += 1
                if temp_debug_invalid_itemid_counter == 1:
                    ips.ips()
                continue
            elif "IP limit" in str(e):
                timenow = datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
                print(f"Reached IP limit at batch with lowest_index = {lowest_index}. Time is {timenow}.")
                pickleOutputFileName = "eBay_sold_step2_items-incomplete-iplimit-" + timenow + ".pickle"
                with open(pickleOutputFileName,'wb') as pickleOutputFile:
                    pickle.dump(items, pickleOutputFile)
                ips.ips()
                continue
            elif "Read timed out" in str(e):
                timenow = datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
                delay = 60
                print(f"Timeout error. Continuing to next batch in {delay} seconds. Time is {timenow}.")
                timeout_error_count += 1
                if timeout_error_count >= 30:
                    print(f"Reached final (30th) timeout at batch with lowest_index = {lowest_index}. Time is {timenow}.")
                    pickleOutputFileName = "eBay_sold_step2_items-incomplete-timeout-" + timenow + ".pickle"
                    with open(pickleOutputFileName,'wb') as pickleOutputFile:
                        pickle.dump(items, pickleOutputFile)
                    ips.ips()
                time.sleep(delay)
                continue
            elif "InvalidChunkLength" in str(e):
                chunk_error_count += 1
                print("Got InvalidChunkLength error. The source of this error is unclear to Felix.")
                print("Waiting 20-60 seconds and trying again.")
                time.sleep(random.uniform(20,60))
                try:
                    shopping_response_dict = \
                shopping_api.execute("GetMultipleItems", shopping_request).dict()
                except Exception as e2:
                    if "InvalidChunkLength" in str(e2):
                        chunk_error_count += 1
                    if chunk_error_count > 0.5 * len(items):
                        print("Got unexpectedly many chunk errors. Opening a terminal.")
                        ips.ips()
                    print("Got an error when trying again. Skipping this batch for now.")
                    continue
            else:
                print(e)
                timenow = datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
                print("Unknown error at time", timenow)
                pickleOutputFileName = "eBay_sold_step2_items-incomplete-unknownError-" + timenow + ".pickle"
                with open(pickleOutputFileName,'wb') as pickleOutputFile:
                    pickle.dump(items, pickleOutputFile)
                ips.ips()
                continue
                # raise e
        srd = shopping_response_dict
        shopping_response_dicts_debug += [srd]
        real_batch_size = 1 if type(srd['Item']) is dict else len(srd['Item'])
        print(f"Retrieving item specifics for the {lowest_index}th result of {num_results}")
        for m in range(lowest_index, lowest_index + real_batch_size):
            inner_index = m%20
            # convert the response into a dict to save all relevant item specifics
            if type(srd['Item']) is dict: #I think this happens if there is only one result in that batch.
                itemSpecificsList = srd['Item'].get('ItemSpecifics')
            else:
                itemSpecificsList = srd['Item'][inner_index].get('ItemSpecifics')
            # account for possibility that the specifics do not exist:
            itemSpecificsList = None \
                if itemSpecificsList is None else itemSpecificsList.get('NameValueList')
            # if there is only one item, itemSpecificsList is now a dict. Change to a list:
            itemSpecificsList = [itemSpecificsList] \
                if type(itemSpecificsList) is dict else itemSpecificsList
            itemSpecificsDict = \
                {itemSpecificsList[k]['Name'] : \
                  itemSpecificsList[k]['Value'] for k in range(len(itemSpecificsList)) \
                } if itemSpecificsList is not None else None
            itemID = twenty_item_ids[inner_index]
            item = items[itemID]
            item['shoppingAPIResponseTimestamp'] = srd.get('Timestamp')
            item['shoppingAPIAck'] = srd.get('Ack')
            item['language'] = itemSpecificsDict.get('Language') \
                if itemSpecificsList is not None else None
            itemSpecificsList = try_remove_item(item['language'], itemSpecificsList)
            item['grade'] = itemSpecificsDict.get('Grade') \
                if itemSpecificsList is not None else None
            itemSpecificsList = try_remove_item(item['grade'], itemSpecificsList)
            item['set'] = itemSpecificsDict.get('Set') \
                if itemSpecificsList is not None else None
            itemSpecificsList = try_remove_item(item['set'], itemSpecificsList)
            item['character'] = itemSpecificsDict.get('Character') \
                if itemSpecificsList is not None else None
            itemSpecificsList = try_remove_item(item['character'], itemSpecificsList)
            if type(item['character']) is str:
                item['character'].replace('é','e')
            item['rarity'] = itemSpecificsDict.get('Rarity') \
                if itemSpecificsList is not None else None
            itemSpecificsList = try_remove_item(item['rarity'], itemSpecificsList)
            item['cardName'] = itemSpecificsDict.get('Card Name') \
                if itemSpecificsList is not None else None
            itemSpecificsList = try_remove_item(item['cardName'], itemSpecificsList)
            item['yearManufactured'] = itemSpecificsDict.get('Year Manufactured') \
                if itemSpecificsList is not None else None
            itemSpecificsList = try_remove_item(item['yearManufactured'], itemSpecificsList)
            item['features'] = itemSpecificsDict.get('Features') \
                if itemSpecificsList is not None else None
            itemSpecificsList = try_remove_item(item['features'], itemSpecificsList)
            item['finish'] = itemSpecificsDict.get('Finish') \
                if itemSpecificsList is not None else None
            itemSpecificsList = try_remove_item(item['finish'], itemSpecificsList)
            item['manufacturer'] = itemSpecificsDict.get('Manufacturer') \
                if itemSpecificsList is not None else None
            itemSpecificsList = try_remove_item(item['manufacturer'], itemSpecificsList)
            item['specialty'] = itemSpecificsDict.get('Specialty') \
                if itemSpecificsList is not None else None
            itemSpecificsList = try_remove_item(item['specialty'], itemSpecificsList)
            item['country/RegionOfManufacture'] = \
                itemSpecificsDict.get('Country/Region of Manufacture') \
                    if itemSpecificsList is not None else None
            itemSpecificsList = try_remove_item(item['country/RegionOfManufacture'], itemSpecificsList)
            item['cardSize'] = itemSpecificsDict.get('Card Size') \
                if itemSpecificsList is not None else None
            itemSpecificsList = try_remove_item(item['cardSize'], itemSpecificsList)
            item['professionalGrader'] = itemSpecificsDict.get('Professional Grader') \
                if itemSpecificsList is not None else None
            itemSpecificsList = try_remove_item(item['professionalGrader'], itemSpecificsList)
            item['cardType'] = itemSpecificsDict.get('Card Type') \
                if itemSpecificsList is not None else None
            itemSpecificsList = try_remove_item(item['cardType'], itemSpecificsList)
            item['hasItemSpecifics'] = True \
                if itemSpecificsList is not None else False
            if type(item['cardType']) is str:
                item['cardType'].replace('é','e')
            # non-itemSpecifics properties:
            # You seem to get a dict if there is only one result in that batch.
            if type(srd['Item']) is dict: 
                itemDetails = srd['Item']
            else:
                itemDetails = srd['Item'][inner_index]
            item['eBayItemEndTime'] = itemDetails.get('EndTime')
            item['viewItemURLForNaturalSearch'] = itemDetails.get('ViewItemURLForNaturalSearch')
            # Be careful, item['listingType'] is already taken since we pulled it from the html.
            # As I recall, the one from the html was more reliable than from the shopping response. But not sure.
            # Could potentially improve / get more valid data by understanding this.
            item['listingTypeFromShoppingAPIResponse'] = itemDetails.get('ListingType')
            item['postalCode'] = None
            item['location'] = itemDetails.get('Location') 
            item['galleryURL'] = itemDetails.get('GalleryURL')
            item['pictureURL'] = itemDetails.get('PictureURL')
            item['primaryCategoryID'] = itemDetails.get('PrimaryCategoryID')
            item['primaryCategoryName'] = itemDetails.get('PrimaryCategoryName')
            item['bidCount'] = itemDetails.get('BidCount')
            price = itemDetails['ConvertedCurrentPrice'].get('value') \
                if itemDetails.get('ConvertedCurrentPrice') is not None else None
            if price is not None:
                price = float(price)
                if price == 0:
                    print(f"ENCOUNTERED AN ITEM WITH PRICE 0. ItemID {item['itemID']}")
                    error_messages += [f"ENCOUNTERED AN ITEM WITH PRICE 0. ItemID {item['itemID']}"]
            else:
                print("Price is None")
                error_messages += [f"Price is None for itemID {item['itemID']}"]
            item['price'] = price
            item['convertedCurrentPrice_currencyID'] = itemDetails['ConvertedCurrentPrice'].get('_currencyID') \
                if itemDetails.get('ConvertedCurrentPrice') is not None else None 
            item['listingStatus'] = itemDetails.get('Completed')
            item['timeLeft'] = itemDetails.get('TimeLeft')
            item['titleFromShoppingAPIResponse'] = itemDetails.get('Title')
            
            item['otherItemSpecificsList'] = itemSpecificsList if itemSpecificsList is not None else None
            item['hitCount'] = itemDetails.get('HitCount')
            item['country'] = itemDetails.get('Country') 
            item['conditionID'] = itemDetails.get('ConditionID')
            item['conditionDisplayName'] = itemDetails.get('conditionDisplayName')
    
    itemProperties = []
    for itemID in items:
        for key in items[itemID]:
            if key not in itemProperties:
                itemProperties += [key]
    
    for itemID in items:
        if 'hasItemSpecifics' not in items[itemID] or items[itemID]['hasItemSpecifics'] is None:
            items[itemID]['hasItemSpecifics'] = False
        for prop in itemProperties:
            if prop not in items[itemID]:
                items[itemID][prop] = None
    return items

if __name__ == "__main__":
    # get item properties from api (takes a while for 2500 calls)
    items = get_shopping_api_properties(items)
    
    # try again for failed items
    items = get_shopping_api_properties(items)
    
    # one last time
    items = get_shopping_api_properties(items)
    
    
    try:
        itemProperties = []
        for itemID in items:
            for key in items[itemID]:
                if key not in itemProperties:
                    itemProperties += [key]
        # 'hasItemSpecifics is not True' is a superficial criterion for a failed API call. Could improve later.
        failed_items = {itemID : items[itemID] for itemID in items if items[itemID]['hasItemSpecifics'] is not True}
        print(f"{len(failed_items)} out of {len(items)} items failed to return from API.",
              "They can be found in failed_items.")
        timenow = datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
        outputfilename = 'data step 2 - enriched with shoppingapi, completed/ebay_sold_step2_enriched_with_shoppingapi-' + timenow + '.csv'
        print(f"Writing to file {outputfilename}... ")
        itemsAsList = list(items.values())
        with open(outputfilename, 'w', encoding='UTF-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames = itemProperties, lineterminator = '\n')
            writer.writeheader() 
            writer.writerows(itemsAsList)
        
        ans = input("Done outputting csv. To print all error messages now, press 1: ")
    
        if ans == "1":
            for msg in error_messages:
                print(msg)
                print()
            if len(error_messages) == 0:
                print("No error messages. Congratulations.")
    except Exception as e:
        ips.ips()