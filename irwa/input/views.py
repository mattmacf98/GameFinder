from django.http import HttpResponseRedirect
from django.shortcuts import render
from urllib import request
from .forms import GameForm
from input import game_search as gs
import re


def get_game(request):
    if request.method == 'POST':
        form = GameForm(request.POST)

        # check whether form is valid:
        if form.is_valid():
            print(form.cleaned_data['title'])
            title = form.cleaned_data['title']
            request.session['results'] = game_search(title)

            # redirect to a new URL:
            return HttpResponseRedirect('/results/')

    else:
        # Anything but POST request
        form = GameForm()

    return render(request, 'home.html', {'form': form})


def game_search(title):
    title = title.lower()
    title = re.sub(r"[,:\.!\?']", "", title)

    ebay_url = "https://www.ebay.com/sch/i.html?_from=R40&_nkw=" + title.replace(" ", "+") + "&LH_BIN=1"
    req = request.urlopen(ebay_url)
    html = req.read()
    ebay_results = gs.get_games_ebay(ebay_url, html, title)

    dd_url = "https://www.deepdiscount.com/search?q=" + title.replace(" ", "+")
    req = request.urlopen(dd_url)
    html = req.read()
    dd_results = gs.get_games_dd(dd_url, html, title)

    newegg_url = "https://www.newegg.com/Product/ProductList.aspx?Submit=ENE&DEPA=0&Order=BESTMATCH&Description=" \
                 + title.replace(" ", "+")
    req = request.urlopen(newegg_url)
    html = req.read()
    newegg_results = gs.get_games_newegg(newegg_url, html, title)

    gog_url = "https://gameovervideogames.com/search?type=product&q=" + title.replace(" ", "+")
    req = request.urlopen(gog_url)
    html = req.read()
    gog_results = gs.get_games_gog(gog_url, html, title)

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

    return results


def display_results(request):
    if 'results' in request.session:
        results = request.session['results']
        return render(request, 'results.html', {'results': results})
    else:
        return render(request, 'results.html')


def home(request):
    return render(request, 'home.html')
