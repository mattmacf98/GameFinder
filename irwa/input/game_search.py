import re
import sys
from bs4 import BeautifulSoup
from urllib import request


# EBay
def get_ebay_info(list_item, game):
    soup = BeautifulSoup(list_item, 'html.parser')

    string = list_item.lower()
    string = re.sub(r"[,:\.!\?']", "", string)

    title_matcher = re.compile(r"<h3 class=\"s-item__title\">.{0,20}" + re.escape(game) + r".{0,40}</h3>")
    t = title_matcher.search(string)

    if t is not None:
        # take away the garbage from the title
        title = t.group(0)
        title = title[0:title.index('</h3>')]
        title = title[title.index('\">') + 2:]
    else:
        return

    if soup.find('span', {"class": "s-item__price"}) is None:
        return
    price = soup.find('span', {"class": "s-item__price"}).text
    if len(price) > 6:
        # sometimes need to click to see the price :(
        return

    if soup.find('a', {"class": "s-item__link"}) is None:
        return
    link = soup.find('a', {"class": "s-item__link"})['href']

    if price is not 0 and title is not '' and link is not '':
        return title, float(price[1:]), link


def get_games_ebay(url, html, game):
    results = []
    soup = BeautifulSoup(html, 'html.parser')
    for listItem in soup.find_all("li", {"class": "s-item"}):
        res = get_ebay_info(str(listItem), game)
        if res is not None:
            results.append(res)
    return results


# DeepDiscount
def get_info_dd(list_item, game):
    soup = BeautifulSoup(list_item, 'html.parser')

    # get the header for the card whichc contains the link and title
    header = soup.find("a", {"class": "aec-listlink"})
    header_str = str(header)

    link_soup = BeautifulSoup(header_str, 'html.parser')

    title_sp = link_soup.find('a')
    if title_sp is None:
        return
    title = title_sp.text
    title = title.lower()
    title = re.sub(r"[,:\.!\?']", "", title)
    title_matcher = re.compile(r".{0,20}" + re.escape(game) + r".{0,40}")
    if not title_matcher.match(title) or title.index(game) + len(game) < len(title) - 40:
        # if the title does not match the regex, do not include this game in the results
        return

    # now get the link href
    if link_soup.find('a') is None:
        return
    link = "https://www.deepdiscount.com" + link_soup.find('a')['href']

    price_group = soup.find('div', {"class": "aec-custprice"})
    if price_group is None:
        return

    price_soup = BeautifulSoup(str(price_group), 'html.parser')
    if price_soup.find('span') is None:
        return
    price = price_soup.find('span').text

    if price is not 0 and title is not '' and link is not '':
        return title, float(price[1:]), link


def get_games_dd(url, html, game):
    results = []
    soup = BeautifulSoup(html, 'html.parser')
    group = soup.find("ul", {"id": "aec-prodgrid"})

    li_soup = BeautifulSoup(str(group), 'html.parser')
    for listItem in li_soup.findChildren("li"):
        res = get_info_dd(str(listItem), game)
        if res is not None:
            results.append(res)
    return results


# NewEgg
def get_info_newegg(list_item, game):
    soup = BeautifulSoup(list_item, 'html.parser')

    # get the header for the card whichc contains the link and title
    header = soup.find("a", {"class": "item-title"})
    if header is None:
        return
    title = header.text
    title = title.lower()
    title = re.sub(r"[,:\.!\?']", "", title)
    link = header['href']

    title_matcher = re.compile(r".{0,20}" + re.escape(game) + r".{0,40}")
    if not title_matcher.match(title) or title.index(game) + len(game) < len(title) - 40:
        # if the title does not match the regex, do not include this game in the results
        return

    price_group = soup.find('li', {"class": "price-current"})
    if price_group is None:
        return

    price_soup = BeautifulSoup(str(price_group), 'html.parser')
    if price_soup.find('strong') is None or price_soup.find('sup') is None:
        return
    price = float(price_soup.find('strong').text)
    price = price + float(price_soup.find('sup').text)

    if price is not 0 and title is not '' and link is not '':
        return title, price, link


def get_games_newegg(url, html, game):
    results = []
    soup = BeautifulSoup(html, 'html.parser')
    for listItem in soup.find_all("div", {"class": "item-container"}):
        res = get_info_newegg(str(listItem), game)
        if res is not None:
            results.append(res)
    return results


# GameOverGames
def get_info_gog(list_item, game):
    soup = BeautifulSoup(list_item, 'html.parser')

    # get the title and price from the div components
    header = soup.find("div", {"class": "element"})
    if header is None:
        return
    title = header['data-alpha']
    title = title.lower()
    title = re.sub(r"[,:\.!\?']", "", title)
    price = header['data-price']
    price = float(price) / 100

    title_matcher = re.compile(r".{0,20}" + re.escape(game) + r".{0,40}")
    if not title_matcher.match(title) or title.index(game) + len(game) < len(title) - 40:
        # if the title does not match the regex, do not include this game in the results
        return

    if soup.find('a', {"class": "hoverBorder"}) is None:
        return
    link = "https://gameovervideogames.com/" + soup.find('a', {"class": "hoverBorder"})['href']

    if price is not 0 and title is not '' and link is not '':
        return title, price, link


def get_games_gog(url, html, game):
    results = []
    soup = BeautifulSoup(html, 'html.parser')
    for listItem in soup.find_all("div", {"class": "element"}):
        res = get_info_gog(str(listItem), game)
        if res is not None:
            results.append(res)
    return results


if __name__ == '__main__':
    # main()
    game = sys.argv[1]
    game = game.lower()
    game = re.sub(r"[,:\.!\?']", "", game)

    ebay_url = "https://www.ebay.com/sch/i.html?_from=R40&_nkw=" + game.replace(" ", "+") + "&LH_BIN=1"
    req = request.urlopen(ebay_url)
    html = req.read()
    ebay_results = get_games_ebay(ebay_url, html, game)

    dd_url = "https://www.deepdiscount.com/search?q=" + game.replace(" ", "+")
    req = request.urlopen(dd_url)
    html = req.read()
    dd_results = get_games_dd(dd_url, html, game)

    newegg_url = "https://www.newegg.com/Product/ProductList.aspx?Submit=ENE&DEPA=0&Order=BESTMATCH&Description=" \
                 + game.replace(" ", "+")
    req = request.urlopen(newegg_url)
    html = req.read()
    newegg_results = get_games_newegg(newegg_url, html, game)

    gog_url = "https://gameovervideogames.com/search?type=product&q=" + game.replace(" ", "+")
    req = request.urlopen(gog_url)
    html = req.read()
    gog_results = get_games_gog(gog_url, html, game)

    results = []
    for i in ebay_results:
        results.append(i)
    for i in dd_results:
        results.append(i)
    for i in newegg_results:
        results.append(i)
    for i in gog_results:
        results.append(i)

    results.sort(key=lambda x: x[1])

    for i in results:
        print(i)
