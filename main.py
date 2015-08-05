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
import argparse
import requests
from bs4 import BeautifulSoup

BENDON_SITE = "https://dinbendon.net"

username = ""
password = ""

def getMenu(session, urlLink):
    orderReq = session.get(urlLink)
    soup = BeautifulSoup(orderReq.text, 'lxml')
    menuToReturn = []

    for i in soup.find_all('tr', ['odd', 'even']):
        item = {
                'name': i.find('td', 'productName').div.string,
                'price': i.find('td', 'variationPrice').string
        }
        menuToReturn.append(item)

    return menuToReturn

def cli(args):
    s = requests.Session()

    r = s.get(BENDON_SITE + "/do/login")
    soup = BeautifulSoup(r.text, 'lxml')
    caculate = soup.select('td')[6].text.rstrip('=')
    exec('result= %s' % caculate)

    data = {
            "password":password,
            "rememberMeRow:rememberMe":"on",
            "result":str(result),
            "signInPanel_signInForm:hf:0":"",
            "submit":"login",
            "username":username
    }

    c = s.cookies.get('JSESSIONID')
    url="https://dinbendon.net/do/;jsessionid="+ c +"?wicket:interface=:0:signInPanel:signInForm::IFormSubmitListener"
    r = s.post(url, data=data)

    soup = BeautifulSoup(r.text, 'lxml')
    orderUrl = BENDON_SITE + soup.select('td')[3].select('a')[1]['href']
    menuList = getMenu(s, orderUrl)
    for i in menuList:
        print(i["name"] + ": " + i["price"])


if __name__ == "__main__":
    exit(cli(sys.argv[1:]))
