## By Shiqing Yu
## sqyu@uw.edu
from __future__ import print_function
import urllib2
from bs4 import BeautifulSoup
import re
import json
import datetime
import time

class COL:
        RED = "\033[91m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        BLUE = "\033[94m"
        PURPLE = "\033[95m"
        END = "\033[0m"
        BOLD = "\033[1m"
        UL = "\033[4m"

MAJORS = ["stat", "math"]
SCHOOLS = [["chicago", "uchi", "cmu", "carnegie", "cornell", "duke", "harvard", "stanford", "ucb", "berkeley", "umich", "university of michigan", "unc", "university of north carolina", "chapel hill", "uw", "university of washington"], 
["brown", "columbia", "mit", "massachusetts institute of technology"]]
BLACKLIST = ["fin", "uwm", "madison", "missouri"]
year = 15 #e.g. 15, 16, 17
max = 3 # Max number of pages to search in 1p3a
keywords_cafe = ["statistics", "stats", "stat", "math*"] # Keywords to seach in the grad cafe
maxes = [2,1,1,1] # Max number of pages to search for each keyword in the grad cafe

def check(school, major):
        school = school.lower()
        major = major.lower()
        if not all([not bl in school + major for bl in BLACKLIST]):
                return False
        found = False
        #if all(not maj in major for maj in MAJORS):
        #        return False
        try:
                m = next(i for (i, maj) in enumerate(MAJORS) if maj in major)
        except StopIteration:
                return False
        if all(not sch in school for sch in SCHOOLS[m]):
                return False
        return True

def getHTML(URL):
	"""
	get raw html from given URL
	"""
	req = urllib2.Request(URL,headers={'User-Agent':'Mozilla/50.0'})
	con = urllib2.urlopen(req)
	html = con.read()
	con.close()
	return html

def parse(html):
	"""
	parse raw html, return cleaned results.
	"""
	# html = open("./test/page3-test.html").read() # TODO: change it to getHTML() when test is done succesfully.
	soup = BeautifulSoup(html)
	pattern = re.compile(r"normalthread_\d+") # pattern of every post in the collection page
	raw_results = soup.findAll("tbody", {"id": pattern})
	cleaned_results = []
	for i in raw_results:
                try:
                        post_id = i["id"].split("_")[1]
                        # block: class = by
                        block_by = i.find("td", {"class": "by"})
                        user = block_by.cite.a.text
                        user_id = re.match(r".*uid-(\d+)\.html", block_by.cite.a["href"]).group(1)
                        # block: class = new
                        block_new = i.find("th", {"class": "new"})
                        season = block_new.span.u.find("font", {"color": "#666"}).text[1:] # 2014Fall, 2015Spring, etc.
                        if season != str(year) + "Fall":
                                continue
                        school = block_new.span.u.find("font", {"color": "#00B2E8"}).text # Stanford, Harvard, etc.
                        major = re.match(r".*\]\[(.*)@", block_new.span.text).group(1).split("@")[0] # an alternative to code above
                        if not check(school, major):
                                continue
                        title = block_new.find("a", {"class": "s xst"}).text

                        degree = block_new.span.u.find("font", {"color": "blue"}).text # MS or PhD
                        result = block_new.span.u.find("font", {"color": "black"}).text[:-1] # Offer, AD, WaitingList or REJ
                        notice_date = block_new.span.find("font", {"color": "brown"}).text # eg. 2014-12-15, 2014-11-30
                        TOEFL = block_new.span.find("font", {"color": "cornflowerblue"}).text[3:]
                        GRE = block_new.span.findAll("font", {"color": "brown"})[1].text[3:] # eg. V 164 Q 170 AW 3.0, 153+168+3.5 
                        GPA = block_new.span.find("font", {"color": "darkcyan"}).text[1:-1] # eg. 3.88/4.0 1/108
                        undergrad_school = block_new.span.find("font", {"color": "purple"}).text
                        dic = {"post_id": post_id, "user": user, "user_id": user_id, "title": title, "season": season, "degree": degree, "result": result, "school": school, "major": major, "notice_date": notice_date, "TOEFL": TOEFL, "GRE": GRE, "GPA": GPA, "undergrad_school": undergrad_school}
                except:
                        continue
		cleaned_results.append(dic)
        return cleaned_results

def parse2(html):
	"""
	parse raw html, return cleaned results.
	"""
	# html = open("./test/page3-test.html").read() # TODO: change it to getHTML() when test is done succesfully.
	soup = BeautifulSoup(html)
	pattern = re.compile(r"row\d+") # pattern of every post in the collection page
	raw_results = soup.findAll("tr", {"class": pattern})
	cleaned_results = []
        for i in raw_results:
                all = i.findAll("td")
                institution = all[0].text # e.g. University of Michigan
                dm = all[1].text.split(", ")
                major = ", ".join(dm[0:len(dm) - 1]) # e.g. Statistics
                if not check(institution, major):
                        continue
                ds = dm[len(dm) - 1].split(" (") # e.g. ['Statistics', 'PhD (F15)']
                #assert(len(ds) == 2) # for debugging purpose only
                degree = ds[0] # e.g. PhD
                season = ds[1].replace(')', '') # e.g. F15
                if season != "F" + str(year):
                        continue
                extinfo = i.findAll("a", {"class": "extinfo"})
                if len(extinfo):
                        extinfo = extinfo[0].text.replace("GRE", " GRE")[:-1] + "\n"
                else:
                        extinfo = ""
                result = all[2].text.split(" via ")[0] # e.g. Accepted
                via = re.compile(r"via[ ]?\S* ").search(all[2].text).group(0) # e.g. via E-mail
                date = re.compile(r"\d{1,2} \w{3} \d{4}").search(all[2].text).group(0)
                status = all[3].text # A, U, I, O, ?
                note = all[5].text.replace("\n", " ").replace("\r", " ") # e.g. Yay!
                if note:
                        note += "\n"
                dic = {"school": institution, "major": major, "degree": degree, "season": season, "extinfo": extinfo, "result": result, "via": via, "date": date, "status": status, "note": note}     
                cleaned_results.append(dic)
	return cleaned_results

def formulateresult(result):
        if "AD" in result or result == "Offer":
                return COL.BOLD + COL.GREEN + result + COL.END
        elif result == "Rej":
                return COL.BOLD + COL.RED + result + COL.END
        else:
                return COL.BOLD + COL.BLUE + result + COL.END

def formulateresult2(result):
        if result == "Accepted":
                return COL.BOLD + COL.GREEN + result + COL.END
        elif result == "Rejected":
                return COL.BOLD + COL.RED + result + COL.END
        else:
                return COL.BOLD + COL.BLUE + result + COL.END

def _print(results):
	"""
	print crawled data
	"""
        for i in results:
                print(", ".join([COL.UL + COL.BOLD + i["school"] + COL.END, COL.BOLD + i["degree"] + " in " + i["major"] + COL.END, formulateresult(i["result"]), i["notice_date"]]) + "\n" + i["title"] + "\n" + ", ".join(filter(None, [i["TOEFL"], i["GRE"], i["GPA"], i["undergrad_school"]])) + "\n")

def _print2(results):
	"""
	print crawled data
	"""
        for i in results:
                print(", ".join([COL.UL + COL.BOLD + i["school"] + COL.END, COL.BOLD + i["degree"] + " in " + i["major"] + COL.END, formulateresult2(i["result"]), i["date"], i["status"]]) + "\n" + i["extinfo"] + i["note"])

def main():
        lastresults = lastresults2 = []
        while True:
                print("----------- 1point3acres -----------\n")
                max = 3
                results = []
                results2 = []
                for i in range(1, max + 1):
                        URL = "http://www.1point3acres.com/bbs/forum.php?mod=forumdisplay&fid=82&orderby=dateline&filter=author&page=%d" % i
                        html = getHTML(URL)
                        results = results + parse(html)
                results = sorted(results, key = lambda dic : dic["notice_date"], reverse = True)
                if results == []:
                        print("No results found.\n")
                if results != lastresults:
                        _print(results)
                        if lastresults != []:
                                print(COL.RED + COL.BOLD + "NEW " * 200 + COL.END)
                                break
                        lastresults = results
                print("--------- The grad cafe ---------\n")
                for m, str in enumerate(keywords_cafe):
                        for i in range(1, maxes[m] + 1):
                                URL = "http://thegradcafe.com/survey/index.php?q=%s&t=a&o=&p=%d" % (str, i)
                                html = getHTML(URL)
                                results2 = results2 + parse2(html)
                if results2 == []:
                        print("No results found.\n")
                else:
                        results2 = sorted(results2, key = lambda dic : datetime.datetime.strptime(dic["date"], "%d %b %Y").strftime("%Y-%m-%d"), reverse = True)
                        if results2[0] != lastresults2:
                                _print2(results2)
                                if lastresults2 != []:
                                        print(COL.RED + COL.BOLD + "NEW " * 200 + COL.END)
                                        break
                                lastresults2 = results2[0]
                time.sleep(600)

if __name__ == "__main__":
	main()
