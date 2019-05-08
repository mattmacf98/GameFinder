import re
import sys
from bs4 import BeautifulSoup
from urllib import parse, request

#EBAY
def getInfoFromCard_ebay(listItem, game):
    soup = BeautifulSoup(listItem, 'html.parser')

    string = listItem

    title_matcher = re.compile(r"<h3 class=\"s-item__title\">.{0,20}" + re.escape(game) + r".{0,40}</h3>")
    t = title_matcher.search(string)
    title = ""
    if t is not None:
        #take away the garbage from the title
        title  = t.group(0)
        title = title[0:title.index('</h3>')]
        title = title[title.index('\">')+ 2:]

    price = 0
    price = soup.find('span', {"class": "s-item__price"}).text
    if len(price) > 6:
        #sometimes need to click to see the price :(
        return

    link = ''
    link = soup.find('a', {"class": "s-item__link"})['href']

    if price is not 0 and title is not '' and link is not '':
        return (title, float(price[1:]), link)

def get_video_games_ebay(url, html, game):
    results = []
    soup = BeautifulSoup(html, 'html.parser')
    for listItem in soup.find_all("li", {"class": "s-item"}):
        res = getInfoFromCard_ebay(str(listItem), game)     
        if res is not None:
            results.append(res)
    return results

#GAMESTOP
def getInfoFromCard_gameStop(listItem, game):
    soup = BeautifulSoup(listItem, 'html.parser')

    #get the header for the card whichc contains the link and title
    header = soup.find("h3", {"class":"ats-product-title"})
    header_str = str(header)

    link_soup = BeautifulSoup(header_str, 'html.parser')
    title = link_soup.find('a').text
    title_matcher = re.compile(r"{0,20}" + re.escape(game) + r".{0,40}</h3>")
    if not title_matcher.match(title):
        #if the title does not match the regex, do not include this game in the results
        return

    #now get the link href
    link = link_soup.find('a')['href']

    price = 0
    price = soup.find('p', {"class": "ats-product-price"}).text

    if price is not 0 and title is not '' and link is not '':
        return (title, float(price[1:]), link)

def get_video_games_gameStop(url, html, game):
    results = []
    soup = BeautifulSoup(html, 'html.parser')
    for listItem in soup.find_all("div", {"class": "product"}):
        res = getInfoFromCard_gameStop(str(listItem), game)     
        if res is not None:
            results.append(res)
    return results



if __name__ == '__main__':
    #main()
    game = sys.argv[1]

    urlEbay="https://www.ebay.com/sch/i.html?_from=R40&_nkw=" + game.replace(" ","+") + "&LH_BIN=1"
    req = request.urlopen(urlEbay)
    html = req.read()
    ebay_results = get_video_games_ebay(urlEbay, html, game)

    #urlGameStop = "https://www.gamestop.com/browse?nav=16k-" + game.replace(" ","+")
    #req = request.urlopen(urlGameStop)
    #html =  req.read()
    #gameStop_results = get_video_games_gameStop(urlGameStop, html, game)


    ebay_results.sort(key=lambda x:x[1])
    #gameStop_results.sort(key=lambda x:x[1])

    for i in ebay_results:
        print(i)