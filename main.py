#!/usr/bin/env python2

# JiJiDinBenDon
# Copyright (C) 2015 TheKK <thumbd03803@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

import sys
import re
import argparse
import requests
from bs4 import BeautifulSoup

BENDON_SITE = "https://dinbendon.net"

username = ""
password = ""
username_for_order = ""

def getLoginPostUrl(session):
    id = session.cookies.get('JSESSIONID')
    return (BENDON_SITE + "/do/;jsessionid=" + id +
            "?wicket:interface=:0:signInPanel:signInForm::IFormSubmitListener")

def getOrderUrl(session):
    r = session.get(BENDON_SITE + "/do")
    soup = BeautifulSoup(r.text, 'lxml')
    urlsToReturn = []

    for dom in soup.find_all('tr', id=re.compile('inProgressBox_inProgressOrders_\d+')):
        AllA = dom.find_all('a')
        if not len(AllA) == 4:
            continue

        href = AllA[3]['href']
        print(href)
        urlsToReturn.append(BENDON_SITE + href)

    return urlsToReturn

def login(session):
    r = session.get(BENDON_SITE + "/do/login")
    soup = BeautifulSoup(r.text, 'lxml')

    # Since cpacha here is the form of '1+49=', we can easily get result
    capcha = soup.select('td')[6].text.rstrip('=')
    exec('result = %s' % capcha)

    data = {
            "username":username,
            "password":password,
            "result":str(result),
            "submit":"login",
            "rememberMeRow:rememberMe":"on",
            "signInPanel_signInForm:hf:0":""
    }

    urlToPost = getLoginPostUrl(session)
    session.post(urlToPost, data=data)

    return session.cookies.get('INDIVIDUAL_KEY')

def getMenu(session, urlLink):
    orderReq = session.get(urlLink)
    soup = BeautifulSoup(orderReq.text, 'lxml')
    menuToReturn = []

    for i in soup.find_all('tr', ['odd', 'even']):
        name = i.find('td', 'productName').div.string
        price = i.find('td', 'variationPrice').string

        # Multiple prices
        if price is None:
            price = ''
            for label in i.find('td', 'variationPrice').find_all('label'):
                price = price.join(label.string + ' ')

        item = {
                'name': name,
                'price': price
        }
        menuToReturn.append(item)

    return menuToReturn

def cli(args):
    s = requests.Session()

    login(s)

    r = s.get(BENDON_SITE + "/do")
    soup = BeautifulSoup(r.text, 'lxml')

    for orderUrl in getOrderUrl(s):
        menu = getMenu(s, orderUrl)
        for item in menu:
            print(item["name"] + ": " + item['price'])

if __name__ == "__main__":
    exit(cli(sys.argv[1:]))
