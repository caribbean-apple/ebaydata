#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 19 08:44:48 2021

@author: ffeist
"""

from bs4 import BeautifulSoup
import os
import datetime
import csv
import re
import math
import ips

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

# ***the names of the folders matter! Whether they contain 'cgc sold' or 'psa sold' determines 
# the grading company which was searched for.***
# I also recommend padding zeroes on all of the folder and filenames so that they are processed in order.
# Later to-do: make these sort better so that zero padding is not necessary.
input("Reminder before running: You might want to download a few pages of results for each search, sorted by lowest price, so later manually exclude certain itemIDs. "
      "Press enter to continue. ")

folder_of_folders = "data step 0.1 - raw html files/2022.02.01.2022 pull 2 - missing folder"

input("Pulling data from folder:\n" + folder_of_folders + "\n Is this the correct date?? If so, press enter to confirm.")
folders = os.listdir(folder_of_folders)
folder_paths = [folder_of_folders + "/" + f for f in folders if f[:3] in ['psa', 'cgc']] # these folder names should contain the eBay html files to extract from
# folders = ["cgc sold html"]
html_filepaths = [] 
for folder in folder_paths:
    for filename in os.listdir(folder):
        if filename[-5:] == ".html":
            html_filepaths.append(folder + "/" + filename)
html_filepaths.sort()
print(f"Total number of files to parse: {len(html_filepaths)}")

# check that the pokemon sets file is here:
pokemon_sets_filename = "pokemon sets.csv"
if pokemon_sets_filename not in os.listdir():
    print("Need to add the file", pokemon_sets_filename, "to this folder to run the program. Please fix! Exiting.")
    raise Exception("Invalid folder contents. Need to add the file " + pokemon_sets_filename 
                    + " to this folder to run the program. Please fix and then restart!")

# this will hold itemID, url, title, and listing type of all items in all html files in all folders
items = dict()
numDuplicates = 0

num_api_calls_upper_bound = math.floor(len(html_filepaths)*200*6/100)
print("Getting item properties requires at most and approximately "
          f"{num_api_calls_upper_bound} api calls. Running extract_from_html alone does not call the API. ")
for webpage in html_filepaths:
    print("Parsing", webpage)
    soup = BeautifulSoup(open(webpage,encoding='UTF-8'), features = 'lxml')
    results_soup = soup.find(
        lambda tag: 
            'ul' in tag.name and
            'class' in tag.attrs and
            'srp-results' in tag['class']
    )
    items_soup = results_soup.find_all(
        lambda tag:
            tag.name == 'li' and
            'class' in tag.attrs and
            's-item' in tag['class']
    )
    try:
        queryHolder_soup = soup.find(
            lambda tag:
                tag.name == 'h1' and
                'class' in tag.attrs and
                'srp-controls__count-heading' in tag['class']
        )
        query_soup = queryHolder_soup.find(
            lambda tag:
                tag.name == 'span' and
                'class' in tag.attrs and 
                'BOLD' in tag['class'] and not
                tag.get_text().replace(",","").strip().isdigit()
        )
        query_text = query_soup.get_text()
        previous_query_text = query_text
        previous_company = 'CGC' if 'cgc sold' in webpage else 'PSA' if 'psa sold' in webpage else None
    except AttributeError as e:
        company = 'CGC' if 'cgc sold' in webpage else 'PSA' if 'psa sold' in webpage else None
        if company == previous_company:
            query_text = previous_query_text
            print("Got error finding eBay query in html. Since company is same as in the last working query search, we will use the same query text.")
        else:
            raise e
    
    for n in range(len(items_soup)):
        item_soup = items_soup[n]
        itemWrapper_soup = item_soup.find(
            lambda tag: 
                tag.name == 'div' and 
                'class' in tag.attrs and
                's-item__wrapper' in tag['class']
        )
        itemInfo_soup = itemWrapper_soup.find(
            lambda tag:
                tag.name == 'div' and
                'class' in tag.attrs and
                's-item__info' in tag['class']
        )
        itemLink_soup = itemInfo_soup.find(
            lambda tag:
                tag.name == 'a' and
                'class' in tag.attrs and
                's-item__link' in tag['class']
        )
        itemTitle_soup = itemLink_soup.find(
            lambda tag:
                tag.name == 'h3' and
                'class' in tag.attrs and
                's-item__title' in tag['class']
        )
        itemDetails_soup = itemInfo_soup.find(
            lambda tag:
                tag.name == 'div' and
                'class' in tag.attrs and
                's-item__details' in tag['class']
        )
        itemSoldDate_soup = itemInfo_soup.find(
            lambda tag:
                tag.name == 'span' and
                'class' in tag.attrs and
                'POSITIVE' in tag['class']
        )
        item = dict()
        item['url'] = itemLink_soup['href']
        item['title'] = itemTitle_soup.get_text()
        item['queryFromHtml'] = query_text
        rawDate = itemSoldDate_soup.get_text()
        rawDate = rawDate.replace("Sold ", "")
        rawDate = rawDate.strip(" ")
        formattedDate = datetime.datetime.strptime(rawDate, '%b %d, %Y')
        item['htmlSoldDate'] = formattedDate.strftime("%Y-%m-%d")
        if type(item['htmlSoldDate']) is not str:
            ips.ips()
        itemDetailsString = str(itemDetails_soup).lower()
        if 'cgc' in webpage:
            item['companySearched'] = 'CGC'
        elif 'psa' in webpage:
            item['companySearched'] = 'PSA'
        else:
            raise Exception("Search cannot be attributed to CGC or PSA.")
        if "best offer accepted" in itemDetailsString:
            item['listingType'] = "BestOfferAccepted"
        elif "or best offer" in itemDetailsString:
            item['listingType'] = "BuyItNowOrBestOffer"
        elif "buy it now" in itemDetailsString:
            item['listingType'] = "BuyItNow"
        elif "bids" in itemDetailsString:
            item['listingType'] = "Auction"
        else:
            raise Exception("Unable to extract listing type.")
        itemID = int(item['url'][25:37])
        item['itemID'] = itemID
        if itemID in items:
            numDuplicates += 1
        else:
            items[itemID] = item
print(f"Done extracting from html files. {numDuplicates} duplicates were found.")
# sanity check
print("Sanity checking resulting item list...")
# more sanity checks that could be added:
# - something preventing ebay's fake pages, ...
for itemID in items:
    item = items[itemID]
    if itemID < 1e11:
        raise Exception(f"Item has invalid itemID. It is {itemID}.")
    if not ("title" in item and "url" in item and "listingType" in item):
        raise Exception(f"Missing an item property for itemID == {itemID}")
    for key in item:
        if len(str(item[key]) ) < 3:
            raise Exception(f"Item Property too short for itemID == {itemID}")
print("All items passed sanity checks.")


filtered_itemIDs = []

def extract_properties_from_titles(items):
    # first, pull properties from the item title.
    companyMatcher = re.compile(
        r"psa|cgc|bgs|gma|sgc|mgc|pca|ksa|cga|ugc|srg|pgc|pgs|mnt|getgraded|ace|dsg")
    bannedWordsBeforeCompany = ['potential', 'possible', 'likely', 
                                'like', 'not', 'approx', 'almost', 
                                'approx.', 'maybe']
    pokemon_sets = []
    with open(pokemon_sets_filename, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=",")
        for row in reader:
            pokemon_sets += [row]
    setnames = [pokeset[0].lower() for pokeset in pokemon_sets]
    throwaway_itemIDs = []
    for itemID in items:
        item = items[itemID]
        title_lower = item['title'].lower()
        # extract properties from the item title...
        # extract all valid grading companies from the title:
        found_companies = companyMatcher.findall(title_lower)
        for comp in found_companies:
            foundBannedWord = False
            for bannedWord in bannedWordsBeforeCompany:
                if re.search(bannedWord + " " + comp, title_lower):
                    foundBannedWord = True
                    break
            if foundBannedWord:
                found_companies.remove(comp)
        # extract the corresponding grades
        comps_and_grades = {comp : "-1" for comp in found_companies }
        num_companies = len(comps_and_grades)
        for n in range(num_companies):
            # find the grade corresponding to each company if possible
            comp = found_companies[n]
            comp_start_index = title_lower.find(comp)
            comp_end_index = comp_start_index + len(comp)
            if comp_end_index == len(title_lower) - 1:
                comps_and_grades[comp] = "-1"
                continue
            title_after_comp = title_lower[comp_end_index + 1:]
            # remove singly-parenthesized text
            paren_start_index = title_after_comp.find("(")
            paren_end_index = title_after_comp.find(")")
            paren_text = ""
            if paren_start_index >= 0 and paren_end_index >= 0:
                paren_text = title_after_comp[paren_start_index:paren_end_index + 1]
            # only consider text up to the next company name
            next_comp_start_index = \
                title_after_comp.find(found_companies[n + 1]) \
                    if n < num_companies - 1 else float('inf')
            title_after_comp = \
                title_after_comp[:min(next_comp_start_index, len(title_after_comp))]
            # identify first possible grade in remaining text
            grade_search = re.search(
            r"(?:10|[0-9]\.5|[1-9]|10\.0|[1-9]\.0),?.?-? |(?:10|[0-9]\.5|[1-9]|10\.0|[1-9]\.0).?$", 
            title_after_comp)
            if not grade_search:
                # for now, we only allow for titles where the grade appears AFTER the company.
                # this is not a big constraint as a percentage of search results.
                # it could be expanded later by allowing for weird grade locations, like
                # "charizard grade 8.5 near mint cgc"
                comps_and_grades[comp] = "-1"
                continue
            possible_grade = ''.join(c for c in grade_search[0] if c.isdigit() or c == '.')
            possible_grade = possible_grade.strip(".")
            if possible_grade[-2:] == '.0':
                possible_grade = possible_grade[:-2]
            if not 0 < float(possible_grade) <= 10:
                comps_and_grades[comp] = "-1"
                continue
            
            grade_end_index = grade_search.end() # gives index of char after end of match
            text_after_grade = title_after_comp[grade_end_index :]
            banned_match = re.findall(
                r"(?:^ ?/ ?[0-9])|(?:^ ?candidate)|(?:^ ?worthy)|(?:^ ?contender)|(?:^ ?or)|(?:^ ?quality)|(?:^ ?regrade)|(?:^ ?\?)",
                text_after_grade)
            if banned_match:
                comps_and_grades[comp] = "-1"
                continue
            # lastly, only allow for certain words between company name and grade
            text_before_grade = title_after_comp[:grade_search.start()]
            # get rid of parenthesized text between company and grade,
            # e.g. for cases like "CGC (PSA BGS) 9"
            paren_start_index = text_before_grade.find("(")
            paren_end_index = text_before_grade.find(")")
            if paren_start_index >= 0 and paren_end_index >= 0:
                slice1 = text_before_grade[:paren_start_index]
                slice2 = (text_before_grade[paren_end_index + 1:] 
                    if paren_end_index < len(text_before_grade) - 1
                    else "")
                text_before_grade = slice1 + slice2
            
            text_before_grade = ''.join(c for c in text_before_grade if c.isalpha())
            allowed_pre_grade_text = [
                'moderatelyplayed', 'authentic', 'authenticated', 'perfect', 'pristine', 'beautiful', 'excellent', 'nearmint', 
                'verygood', 'graded', 'grade', 'black', 'label', 'gemmt', 'mint', 'very', 'fair', 
                'played', 'strong', 'poor', 'good', 'gem', 'exc', 'ex', 'mp', 'nm', 'mt', 'vf', 
                'fn', 'fr', 'vg', 'fa', 'lp', 'hp', 'pr', 'g', 'm'
                ]
            for s in allowed_pre_grade_text:
                text_before_grade = text_before_grade.replace(s, "")
            if len(text_before_grade) > 0:
                comps_and_grades[comp] = "-1"
                continue
            comps_and_grades[comp] = possible_grade.strip()
        
        company_searched = item['companySearched'].lower()
        if 'cgc' in company_searched:
            if "qualified" in title_lower:
                throwaway_itemIDs.append(itemID)
                continue
            elif 'cgc' not in comps_and_grades or comps_and_grades.get('cgc') == "-1":
                throwaway_itemIDs.append(itemID)
                continue
        elif 'psa' in company_searched:
            if 'psa' not in comps_and_grades or comps_and_grades.get('psa') == "-1":
                throwaway_itemIDs.append(itemID)
                continue
            if 'bgs' in comps_and_grades \
                and ('bgs' not in paren_text or 'psa' in paren_text) \
                and (
                    (comps_and_grades['bgs'] != "-1" and 'bgs' not in paren_text) or 
                    ('psa' in paren_text and 'bgs' not in paren_text) or
                    found_companies.index('bgs') < found_companies.index('psa') or
                    ('bgs' not in paren_text and 'psa' in paren_text)):
                throwaway_itemIDs.append(itemID)
                continue
        # at this point we can assume that company_searched is the actual grading company
        item['titleGradingCompany'] = company_searched
        item['titleGrade'] = comps_and_grades[company_searched]
        item['titleIsPerfect'] = True if company_searched == 'cgc' and '10' in item['titleGrade'] \
            and title_lower.find('perfect') > title_lower.find('cgc') else False
        item['titleError'] = True if ("error" in title_lower or "misprint" in title_lower) \
            and not ("computer" in title_lower) else False
        
        # now get title language
        en = [' english']
        jp = [' jp', ' jap']
        es = [' es ', ' spanish', ' espan']
        zh = [' zh ', ' chinese']
        nl = [' nl ', ' dutch']
        fr = [' fr ', ' french', ' francais']
        de = [' de ', ' german', ' deutsch']
        it = [' italian', ' italiano']
        ko = [' korean']
        pt = [' portug']
        ru = [' ru ', ' russia']
        langs = []
        if any(x in title_lower for x in en): langs.append('English')
        if any(x in title_lower for x in jp): langs.append('Japanese')
        if any(x in title_lower for x in es): langs.append('Spanish')
        if any(x in title_lower for x in zh): langs.append('Chinese')
        if any(x in title_lower for x in nl): langs.append('Dutch')
        if any(x in title_lower for x in fr): langs.append('French')
        if any(x in title_lower for x in de): langs.append('German')
        if any(x in title_lower for x in it): langs.append('Italian')
        if any(x in title_lower for x in ko): langs.append('Korean')
        if any(x in title_lower for x in pt): langs.append('Portuguese')
        if any(x in title_lower for x in ru): langs.append('Russian')
        if len(langs) == 1:
            item['titleLanguage'] = langs[0]
        else:
            item['titleLanguage'] = None
        
        # now try to identify the set from the title.
        # this could be much improved with a database of all cards from every set.
        # then, to double check the set, it could be double checked that the card 
        # number in the title corresponds to the name of the card in the title.
        # This would verify the set. Cards could also be at times uniquely identified
        # by only the card number, with the card name to double check.
        
        # currently, set_ids only finds traditionally numbered cards.
        # it is missing stuff like "sv" and "sl" and whatnot.
        # these would be easier to implement with a database list of all
        # cards and their codes.
        set_ids = re.findall("[0-9]{1,3}[a-zA-Z]? ?/ ?[0-9]{2,3}", title_lower)
        numerators = [set_id[:set_id.index('/')].strip() for set_id in set_ids]
        denominators = [set_id[set_id.index('/') + 1:].strip() for set_id in set_ids]
        tl = title_lower
        if 'promo' in title_lower or item['titleLanguage'] not in ['english', None]:
            # dont identify sets promos or other languages yet. only do main set english cards.
            item['titleSet'] = None
            item['titleSetNum'] = None
            item['titleSetDenom'] = None
        else:
            base_kws = ['ruby', 'diamond', 'pearl', 'dp', 'black', 'b&w'
                        'xy', 'x y', 'x and y', 'x&y', 'x & y', '146', 
                        'sun', 'moon', 's&m' '149', 'sword', 'swsh', '202', 
                        'evolutions', 'like base', 'expedition','165']
            
            # these are sets whose names could be found in titles of other sets.
            # check for them first, then check only for other sets.
            special_case_sets = ['base set', 'base set 2', 'fossil', 'team rocket', 
                                 'ex ruby & sapphire', 'ex dragon', 'ex deoxys', 'ex emerald', 
                                 'diamond & pearl', 'platinum', 'arceus', 
                                 'heartgold & soulsilver',  'xy base', 'sun & moon', 
                                 'team up', 'sword & shield', 'shining fates']
            set_matches = []
            if 'base' in tl and ('102' in denominators 
                                     or all(x not in tl for x in base_kws 
                                            + ['set 2', '130', '109', '114'])):
                set_matches.append('base set')
            elif 'fossil' in tl and (
                    '62' in denominators 
                    or (
                    all(x not in tl for x in ['claw', 'root', 'rare fossil', 'researcher', 
                                              'jaw', 'sail', 'unidentified', 'map', 'dome', 'kit', 
                                              'excavation', 'helix', 'holon', 'armor', 'shieldon', 
                                              'anorith', 'excavator', 'skull', 'cover', 'plume', 
                                              'lileep', '91', '85', '111', '92', '124'])
                    and not [y for y in re.findall(r"[1-2][0-9]{3}", tl) if y != '1999']
                    )):
                set_matches.append('fossil')
            elif 'team rocket' in tl and ('82' in denominators or '2000' in tl):
                set_matches.append('team rocket')
            elif (
                'base set 2' in tl and all(x not in tl for x in base_kws)
                and (len(set_ids) == 0 or tl.index('base set 2') + 9 != tl.index(set_ids[0]))
                ):
                set_matches.append('base set 2')
            elif (
                ' dragon ' in tl 
                and (('ex' in tl and len(denominators) == 0) or '97' in denominators) 
                and all(x not in tl for x in 
                        ['frontiers', '101', '2006', 'roaring', 'skies', '108', 'exalted', '124'])
                ):
                set_matches.append('ex dragon')
            elif 'platinum' in tl and (
                    '127' in denominators
                    or (all(x not in tl for x in ['rising rivals', 'victors', 'arceus'])
                    and len([x for x in denominators if x != '127']) == 0)
                    ):
                set_matches.append('platinum')
            elif 'arceus' in tl and '99' in denominators:
                set_matches.append('arceus')
            elif 'deoxys' in tl and '107' in denominators:
                set_matches.append('ex deoxys')
            elif 'emerald' in tl and 'ex' in tl and 'break' not in tl:
                set_matches.append('ex emerald')
            elif any(x in tl for x in ['xy','x y', 'x&y', 'x & y', 'x and y', 'x + y']) \
                and ('base' in tl or '146' in denominators): 
                set_matches.append("xy base")
            elif 'diamond' in tl and 'pearl' in tl and ('base' in tl or '130' in denominators): 
                set_matches.append("diamond & pearl")
            elif (
                (all(x in tl for x in ['heart','gold','soul','silver']) or 'hgss' in tl)
                and (
                    '123' in denominators 
                    or len(denominators) == 0 and all(x not in tl for x in ['unleashed', 'undaunted', 
                                                                            'triumphant', 'legends']))
                ):
                   set_matches.append("heartgold & soulsilver")
            if 'black' in tl and 'white' in tl and ('base' in tl or '114' in denominators): 
                set_matches.append("black & white")
            if 'sun' in tl and 'moon' in tl and ('base' in tl or '149' in denominators): 
                # we get quite a few missed cards from each respective base set. 
                # with more time, I could make the filters better.
                set_matches.append("sun & moon")
            if 'team up' in tl and (
                    '181' in denominators
                    or ('promo' not in tl and not re.findall(r"sm ?[0-9]{1,3}", tl))
                    ):
                set_matches.append("team up")
            if 'hidden fates' in tl and ('072' not in denominators or 'shining fates' not in tl):
                set_matches.append("hidden fates")
            if 'sword' in tl and 'shield' in tl and ('base' in tl or '202' in denominators):
                set_matches.append("sword & shield")
            if 'shining fates' in tl and ('072' in denominators or 'hidden' not in tl):
                set_matches.append("shining fates")
            
            if len(set_matches) == 0:
                set_matches += [setnames[n] for n in range(len(setnames)) 
                                if setnames[n] in title_lower 
                                and setnames[n] not in special_case_sets]
    
            if len(set_matches) == 0:
                # consider some sets which are not in special_case_sets but might not be found 
                # by the simple title search.
                if 'sandstorm' in tl: set_matches.append("ex sandstorm")
                if 'team magma v' in tl: set_matches.append("ex team magma vs team aqua")
                if 'hidden legends' in tl: set_matches.append("ex hidden legends")
                if all(x in tl for x in ['fire','red','leaf','green']): 
                    set_matches.append("ex firered & leafgreen")
                if 'rocket returns' in tl: set_matches.append("ex team rocket returns")
                if 'unseen forces' in tl: set_matches.append("ex unseen forces")
                if 'delta species' in tl: set_matches.append("ex delta species")
                if 'legend maker' in tl: set_matches.append("ex legend maker")
                if 'holon phantoms' in tl: set_matches.append("ex holon phantoms")
                if 'crystal guardians' in tl: set_matches.append("ex crystal guardians")
                if 'dragon frontiers' in tl: set_matches.append("ex dragon frontiers")
                if 'power keepers' in tl: set_matches.append("ex power keepers")
                if 'champion' in tl and 'path' in tl: set_matches.append("champion's path")
            unownSpecialCase = False
            if len(set_matches) == 1:
                # unown special case
                if len(set_ids) == 0 and 'ex unseen forces' in set_matches:
                    unown_setid = re.findall(r"[a-zA-Z] ?/ ?28", tl)
                    if unown_setid:
                        uset_id = unown_setid[0]
                        unumerator = uset_id[:uset_id.index('/')].strip().upper()
                        set_ids.append(uset_id)
                        numerators.append(unumerator)
                        denominators.append('28')
                        unownSpecialCase = True
                        
                if len(set_ids) == 0:
                    item['titleSet'] = set_matches[0]
                    # Maybe this regex could be expanded on to include more possibilities
                    set_numerator = re.findall(r"(?:#|No.?) ?[0-9]{1,3}", tl)
                    if set_numerator:
                        set_numerator = ''.join(x for x in set_numerator[0] if x.isnumeric())
                        # we could expand this to "if setnumerator_index != grade_index else None"  
                        # if we save the location of the grade in the string when we extract it.
                        # This would remove some errors.
                        item['titleSetNum'] = set_numerator
                    else:
                        item['titleSetNum'] = None
                    item['titleSetDenom'] = None
                # check that denominator matches title set index if found.
                
                elif len(set_ids) == 1:
                    numerator = numerators[0]
                    denominator = denominators[0]
                    set_index = setnames.index(set_matches[0])
                    # excel removes leading zeroes when csv files are opened,
                    # so we have to allow for pokemon_sets not to include them...
                    unpadded_denom = denominator.strip("0")
                    if (pokemon_sets[set_index][2] not in [denominator, unpadded_denom] 
                        and not unownSpecialCase):
                        item['titleSet'] = None
                        item['titleSetNum'] = None
                        item['titleSetDenom'] = None
                    else:
                        item['titleSet'] = set_matches[0]
                        item['titleSetNum'] = numerator
                        item['titleSetDenom'] = denominator
                else:
                    # seems like more than one card in listing
                    throwaway_itemIDs.append(itemID)
                    continue
            else:
                item['titleSet'] = None
                item['titleSetNum'] = None
                item['titleSetDenom'] = None
            
        first_edition = re.findall('(?:1st|first) ed', tl)
        if len(first_edition) > 0:
            item['1stEdition'] = True
            if item['titleSet'] is not None:
                set_index = setnames.index(item['titleSet'])
                year = int(pokemon_sets[set_index][3])
                month = int(pokemon_sets[set_index][4])
                if year > 2002 or year == 2002 and month > 2 or item['titleSet'] == 'base set 2':
                    item['1stEdition'] = False
        else:
            item['1stEdition'] = False
        item['shadowless'] = True if 'shadowless' in tl and item['titleSet'] == "base set" else False
        
        
    global filtered_itemIDs
    filtered_itemIDs += throwaway_itemIDs
    for itemID in throwaway_itemIDs:
        del items[itemID]
    return items

items = extract_properties_from_titles(items)
timenow = datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
outputfilepath = 'data step 1 - pulled from html, completed/ebay_sold_step1_from_html_only-' + timenow + '.csv'
print(f"Writing to file {outputfilepath}... ")
first_item = next(iter(items.values()))
properties = list(first_item.keys())
itemIDs = list(items.keys())
failed_items = dict()
for itemID in itemIDs:
    for p in properties:
        if p not in items[itemID]:
            failed_items[itemID] = items[itemID]
            del items[itemID]
            break
itemIDs = list(items.keys())
print(f"{numDuplicates} duplicates were found while extracting itemIDs from html.")
print(f"{len(filtered_itemIDs)} itemIDs were filtered during title parsing.",
      "They can be found in filtered_itemIDs.")
print(f"{len(failed_items)} out of {len(items)} items were missing properties and were removed.",
      "They can be found in failed_items.")
itemsAsList = [items[itemID] for itemID in itemIDs]
with open(outputfilepath, 'w', encoding='UTF-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames = properties, lineterminator = '\n')
    writer.writeheader() 
    writer.writerows(itemsAsList)
    