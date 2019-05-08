import logging
import re
import sys
from bs4 import BeautifulSoup
from queue import Queue, PriorityQueue
from urllib import parse, request

logging.basicConfig(level=logging.DEBUG, filename='output.log', filemode='w')
visitlog = logging.getLogger('visited')
extractlog = logging.getLogger('extracted')


def parse_links(root, html):
    soup = BeautifulSoup(html, 'html.parser')
    for link in soup.find_all('a'):
        href = link.get('href')
        if href:
            text = link.string
            if not text:
                text = ''
            text = re.sub(r'\s+', ' ', text).strip()
            yield (parse.urljoin(root, link.get('href')), text)


def parse_links_sorted(root, html):
    pq = PriorityQueue()
    soup = BeautifulSoup(request.urlopen(root), features="html.parser")

    root_title = soup.title
    if root_title is not None:
        root_title = root_title.string.strip().replace('\n', '').lower().split()
        root_link_words = re.split(r"\W+", root)
        root_title.extend(root_link_words)
        root_title = set([word.lower() for word in root_title if word.lower() not in stopwords
                          and word not in punctuation and word != ''])
    else:
        root_title = re.split(r"\W+", root)
        root_title = set([word.lower() for word in root_title if word.lower() not in stopwords
                          and word not in punctuation and word != ''])

    res = request.urlopen(root)
    link_text = dict(parse_links(root, res.read()))

    for key in link_text:
        orig_title = link_text[key]

        # if link_text[key] == '':
        #     soup = BeautifulSoup(request.urlopen(key), features="html.parser")
        #     link_text[key] = soup.title.string.strip().replace('\n', '')

        link_words = re.split(r"\W+", key)
        link_words = [word.lower() for word in link_words if word.lower() not in stopwords
                      and word not in punctuation and word != '' and word not in link_text[key].lower()]

        title = str(link_text[key]).split(' ')
        title.extend(link_words)
        link_text[key] = set([word.lower() for word in title if word.lower() not in stopwords
                              and word not in punctuation and word != ''])

        priority = 0
        for word in link_text[key]:
            if word in root_title:
                priority -= 1
        pq.put((priority, (key, orig_title)))

    while not pq.empty():
        next_item = pq.get()
        yield(next_item[1])
        # print(next_item[0], next_item[1])


def read_stopwords(file):
    with open(file) as f:
        return set([x.strip() for x in f.readlines()])


stopwords = read_stopwords('common_words')
punctuation = read_stopwords('punctuation')


def get_links(url):
    res = request.urlopen(url)
    return list(parse_links_sorted(url, res.read()))


def get_nonlocal_links(url):
    """Get a list of links on the page specificed by the url,
    but only keep non-local links and non self-references.
    Return a list of (link, title) pairs, just like get_links()"""

    domain = url[url.index("//")+2:]
    domain = domain[0:domain.index("/")]

    links = get_links(url)
    filtered = []
    for link in links:
        link_text = link[0]
        if domain not in link_text:
            filtered.append(link)
    return filtered


def crawl(root, wanted_content=[], within_domain=True):
    """Crawl the url specified by `root`.
    `wanted_content` is a list of content types to crawl
    `within_domain` specifies whether the crawler should limit itself to the domain of `root`
    """

    queue = Queue()
    queue.put(root)

    visited = []
    extracted = []

    while not queue.empty():
        url = queue.get()
        try:
            req = request.urlopen(url)
            html = req.read()

            visited.append(url)
            visitlog.debug(url)

            information = extract_information(url, html)
            if information is not None:
                for ex in information:
                    extracted.append(ex)
                    extractlog.debug(ex)

            nonLocalLinks = get_nonlocal_links(url)
            for link, title in parse_links(url, html):
                if link in visited:
                    continue

                #ignore self-refrencing links
                selfRef = True
                url_items = url.split('/')
                url_items.reverse()
                if "." in url_items[0]:
                    url_items[0] = url_items[0][0:url_items[0].index(".")]

                if '#' in link:
                    link = link[0: link.index('#')]
                link_items = link.split('/')
                link_items.reverse()
                if "." in link_items[0]:
                    link_items[0] = link_items[0][0:link_items[0].index(".")]
                for i in range(min(len(link_items), len(url_items))):
                    if link_items[i] != url_items[i]:
                        selfRef = False
                        break
                if (selfRef):
                    continue
                
                if within_domain:
                    #print("NON_LOCAL_LINKS: ", nonLocalLinks)
                    #print("LINK", link)
                    if (link,title) not in nonLocalLinks:
                        #print("ADDED")
                        if len(wanted_content) > 0:
                            if request.urlopen(link).headers['Content-Type'] in wanted_content:
                                queue.put(link)
                        else:
                            queue.put(link)
                else:
                    if len(wanted_content) > 0:
                            if request.urlopen(link).headers['Content-Type'] in wanted_content:
                                queue.put(link)
                    else:
                        queue.put(link)

        except Exception as e:
            print(e, url)

    return visited, extracted


def extract_information(address, html):
    """Extract contact information from html, returning a list of (url, category, content) pairs,
    where category is one of PHONE, ADDRESS, EMAIL

    Should we make results a set so it doesn't return duplicates info?
    """

    #print("ADDRESS: ", address)

    #make sure address is html or plain
    addressItems = address.split('/')
    addressItems.reverse()
    page = addressItems[0]

    address_matcher = re.compile(r"([A-Z][a-z]+(\s){1,2})+,(\s)[a-zA-Z]+(\.)*(\s)[0-9]{5}")
    email_matcher = re.compile(r"[a-zA-Z0-9\._]+@[a-zA-Z\.]+\.[a-zA-Z]{2,3}")
    phone_number_matcher = re.compile(r"\({0,1}[0-9]{3}\){0,1}(\-|\s)[0-9]{3}(\-|\s)[0-9]{4}")
    results = []

    # search for emails
    string = str(html).replace("\\xc2\\xa0", " ")
    m = email_matcher.search(string)
    while m is not None:
        results.append((address, "EMAIL", m.group(0)))
        string = string[string.index(m.group(0)) + len(m.group(0)):]
        m = email_matcher.search(string)

    # search for phone numbers
    string = str(html).replace("\\xc2\\xa0", " ")
    m = phone_number_matcher.search(string)
    while m is not None:
        results.append((address, "PHONE", m.group(0)))
        string = string[string.index(m.group(0)) + len(m.group(0)):]
        m = phone_number_matcher.search(string)

    # search for addresses
    string = str(html).replace("\\xc2\\xa0", " ")
    m = address_matcher.search(string)
    while m is not None:
        results.append((address, "ADDRESS", m.group(0)))
        string = string[string.index(m.group(0)) + len(m.group(0)):]
        m = address_matcher.search(string)

    #if results:
        #print(set(results))
    return set(results)


def writelines(filename, data):
    with open(filename, 'w') as fout:
        for d in data:
            print(d, file=fout)


def main():
    site = sys.argv[1]

    links = get_links(site)
    writelines('links.txt', links)

    nonlocal_links = get_nonlocal_links(site)
    writelines('nonlocal.txt', nonlocal_links)

    visited, extracted = crawl(site)
    writelines('visited.txt', visited)
    writelines('extracted.txt', extracted)

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