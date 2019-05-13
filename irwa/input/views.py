from django.shortcuts import render
from django.http import HttpResponse

from django.http import HttpResponseRedirect
from django.shortcuts import render
from urllib import request
from .forms import GameForm
from input import hw4

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

    urlEbay = "https://www.ebay.com/sch/i.html?_from=R40&_nkw=" + title.replace(" ", "+") + "&LH_BIN=1"
    req = request.urlopen(urlEbay)
    html = req.read()
    ebay_results = hw4.get_video_games_ebay(urlEbay, html, title)

    urlDeepDiscount = "https://www.deepdiscount.com/search?q=" + title.replace(" ", "+")
    req = request.urlopen(urlDeepDiscount)
    html = req.read()
    deepdiscount_results = hw4.get_video_games_deep_discount(urlDeepDiscount, html, title)

    urlNewEgg = "https://www.newegg.com/Product/ProductList.aspx?Submit=ENE&DEPA=0&Order=BESTMATCH&Description=" + title.replace(
        " ", "+")
    req = request.urlopen(urlNewEgg)
    html = req.read()
    newEgg_results = hw4.get_video_games_new_egg(urlNewEgg, html, title)

    urlGameOverGames = "https://gameovervideogames.com/search?type=product&q=" + title.replace(" ", "+")
    req = request.urlopen(urlGameOverGames)
    html = req.read()
    gameOverGame_results = hw4.get_video_games_game_over_games(urlGameOverGames, html, title)

    results = []
    for i in ebay_results:
        results.append(i)
    for i in deepdiscount_results:
        results.append(i)
    for i in newEgg_results:
        results.append(i)
    for i in gameOverGame_results:
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