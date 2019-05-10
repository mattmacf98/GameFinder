import re
import sys
from bs4 import BeautifulSoup
from urllib import parse, request
import time

#EBAY
def getInfoFromCard_ebay(listItem, game):
    soup = BeautifulSoup(listItem, 'html.parser')

    string = listItem.lower()
    string = re.sub(r"[,.:!?()*'&^%$#@+]","",string)

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

#DEEPDISCOUNT
def getInfoFromCard_deep_discount(listItem, game):
    soup = BeautifulSoup(listItem, 'html.parser')

    #get the header for the card whichc contains the link and title
    header = soup.find("a", {"class":"aec-listlink"})
    header_str = str(header)

    link_soup = BeautifulSoup(header_str, 'html.parser')

    title_sp = link_soup.find('a')
    if title_sp is None:
        return
    title = title_sp.text
    title = title.lower()
    title = re.sub(r"[,.:!?()*&^'%$#@+-_]","",title)
    title_matcher = re.compile(r".{0,20}" + re.escape(game) + r".{0,40}")
    if not title_matcher.match(title) or title.index(game) + len(game) < len(title) - 40:
        #if the title does not match the regex, do not include this game in the results
        return

    #now get the link href
    link = "https://www.deepdiscount.com" + link_soup.find('a')['href']

    price_group = soup.find('div', {"class":"aec-custprice"})
    if price_group is None:
        return

    price = 0
    price_soup = BeautifulSoup(str(price_group), 'html.parser')
    price = price_soup.find('span').text

    if price is not 0 and title is not '' and link is not '':
        return (title, float(price[1:]), link)

def get_video_games_deep_discount(url, html, game):
    results = []
    soup = BeautifulSoup(html, 'html.parser')
    group = soup.find("ul", {"id":"aec-prodgrid"})
    
    li_soup = BeautifulSoup(str(group), 'html.parser')
    for listItem in li_soup.findChildren("li"):
        res = getInfoFromCard_deep_discount(str(listItem), game)     
        if res is not None:
            results.append(res)
    return results

#NEWEGG
def getInfoFromCard_new_egg(listItem, game):
    soup = BeautifulSoup(listItem, 'html.parser')

    #get the header for the card whichc contains the link and title
    header = soup.find("a", {"class":"item-title"})
    title = header.text
    title = title.lower()
    title = re.sub(r"[,.:!?()*&^%'$#@+-_]","",title)
    link = header['href']

    title_matcher = re.compile(r".{0,20}" + re.escape(game) + r".{0,40}")
    if not title_matcher.match(title) or title.index(game) + len(game) < len(title) - 40:
        #if the title does not match the regex, do not include this game in the results
        return

    price_group = soup.find('li', {"class":"price-current"})
    if price_group is None:
        return

    price = 0
    price_soup = BeautifulSoup(str(price_group), 'html.parser')
    price = float(price_soup.find('strong').text)
    price = price + float(price_soup.find('sup').text)

    if price is not 0 and title is not '' and link is not '':
        return (title, price, link)

def get_video_games_new_egg(url, html, game):
    results = []
    soup = BeautifulSoup(html, 'html.parser')
    for listItem in soup.find_all("div", {"class":"item-container"}):
        res = getInfoFromCard_new_egg(str(listItem), game)     
        if res is not None:
            results.append(res)
    return results

#GAMEOVERGAMES
def getInfoFromCard_game_over_games(listItem, game):
    soup = BeautifulSoup(listItem, 'html.parser')

    #get the title and price from the div components
    header = soup.find("div", {"class":"element"})
    title = header['data-alpha']
    title = title.lower()
    title = re.sub(r"[,.:!?()*&^%$'#@+-_]","",title)
    price = header['data-price']
    price = float(price)/100
    

    title_matcher = re.compile(r".{0,20}" + re.escape(game) + r".{0,40}")
    if not title_matcher.match(title) or title.index(game) + len(game) < len(title) - 40:
        #if the title does not match the regex, do not include this game in the results
        return

    link = "https://gameovervideogames.com/" + soup.find('a', {"class":"hoverBorder"})['href']

    if price is not 0 and title is not '' and link is not '':
        return (title, price, link)

def get_video_games_game_over_games(url, html, game):
    results = []
    soup = BeautifulSoup(html, 'html.parser')
    for listItem in soup.find_all("div", {"class":"element"}):
        res = getInfoFromCard_game_over_games(str(listItem), game)     
        if res is not None:
            results.append(res)
    return results


if __name__ == '__main__':
    #main()
    game = sys.argv[1]
    game = game.lower()
    game = re.sub(r"[,.:!?()*&^%$#@'+-_]","",game)

    urlEbay="https://www.ebay.com/sch/i.html?_from=R40&_nkw=" + game.replace(" ","+") + "&LH_BIN=1"
    req = request.urlopen(urlEbay)
    html = req.read()
    ebay_results = get_video_games_ebay(urlEbay, html, game)

    urlDeepDiscount = "https://www.deepdiscount.com/search?q="+game.replace(" ", "+")
    req = request.urlopen(urlDeepDiscount)
    html = req.read()
    deepdiscount_results =  get_video_games_deep_discount(urlDeepDiscount, html, game)

    urlNewEgg = "https://www.newegg.com/Product/ProductList.aspx?Submit=ENE&DEPA=0&Order=BESTMATCH&Description=" + game.replace(" ", "+")
    req = request.urlopen(urlNewEgg)
    html = req.read()
    newEgg_results =  get_video_games_new_egg(urlNewEgg, html, game)

    urlGameOverGames = "https://gameovervideogames.com/search?type=product&q=" + game.replace(" ", "+")
    req = request.urlopen(urlGameOverGames)
    html = req.read()
    gameOverGame_results = get_video_games_game_over_games(urlGameOverGames, html, game)

    
    results = []
    for i in ebay_results:
       results.append(i)
    for i in deepdiscount_results:
       results.append(i)
    for i in newEgg_results:
       results.append(i) 
    for i in gameOverGame_results:
        results.append(i)


    results.sort(key=lambda x:x[1])
    


    for i in results:
      print(i)