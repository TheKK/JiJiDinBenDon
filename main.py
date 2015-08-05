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

from pprint import pprint
import sys
import re
import argparse
import requests
from bs4 import BeautifulSoup

BENDON_SITE = "https://dinbendon.net"

username = "guest"
password = "guest"
username_for_ordering = "I'm a robot from outerspace"

class Menu(object):
    def __init__(self, session, url):
        self.menu_ = {}
        self.payload = {}

        id = session.cookies.get('JSESSIONID')
        orderReq = session.get(url)
        soup = BeautifulSoup(orderReq.text, 'lxml')
        self.menu_['names'] = []
        self.menu_['prices'] = []
        self.menu_['qtyInputs'] = []
        self.menu_['commentInputs'] = []
        self.menu_['userInput'] = soup.find('table', 'lists').find('input')['name']
        self.menu_['urlToPost'] = BENDON_SITE + soup.find('form', id='addOrderItemForm')['action']

        for i in soup.find_all('tr', ['odd', 'even']):
            name = i.find('td', 'productName').div.string
            price = i.find('td', 'variationPrice').string
            qtyInputName = i.find('td', 'qtyColumn').find('input')['name']
            commentInputName = i.find('td', 'commentColumn').find('input')['name']

            # Multiple prices
            if price is None:
                price = ''
                for label in i.find('td', 'variationPrice').find_all('label'):
                    price = price.join(label.string + ' ')

            qtyInput = {
                         "name": qtyInputName,
                         "qty" : ''
                       }

            commentInput = {
                             "name": commentInputName,
                             "comment": ""
                           }

            self.menu_['names'].append(name)
            self.menu_['prices'].append(price)
            self.menu_['qtyInputs'].append(qtyInput)
            self.menu_['commentInputs'].append(commentInput)

    def getItemNameList(self):
        return self.menu_["names"]

    def getItemPriceList(self):
        return self.menu_["prices"]

    def setItemQty(self, itemName, qty):
        if type(qty) is not type(666):
            print(type(qty))
            raise Exception("input qty is not number")

        index = self.menu_["names"].index(itemName)
        self.menu_['qtyInputs'][index]["qty"] = str(qty)

    def setItemComment(self, itemName, comment):
        index = self.menu_["names"].index(itemName)
        self.menu_['commentInputs'][index]["comment"] = str(comment)

    def sendOrder(self, session):
        urlToPost = self.menu_['urlToPost']

        payload = {}
        payload[self.menu_['userInput']] = username_for_ordering
        payload['addOrderItemForm:hf:0'] = ""

        for qtyInput in self.menu_["qtyInputs"]:
            payload[qtyInput["name"]] = str(qtyInput["qty"])

        for commentInput in self.menu_["commentInputs"]:
            payload[commentInput["name"]] = str(commentInput["comment"])

        print(urlToPost)
        for k in payload:
            print(k + ": " + payload[k])
        session.post(urlToPost, data=payload)

def getLoginPostUrl(session):
    return (BENDON_SITE + "/do/?wicket:interface=:0:signInPanel:signInForm::IFormSubmitListener")

def getOrderUrl(session):
    r = session.get(BENDON_SITE + "/do")
    soup = BeautifulSoup(r.text, 'lxml')
    urlsToReturn = []

    for dom in soup.find_all('tr', id=re.compile('inProgressBox_inProgressOrders_\d+')):
        AllA = dom.find_all('a')
        if not len(AllA) == 4:
            continue

        href = AllA[3]['href']
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
    print(urlToPost)
    session.post(urlToPost, data=data)

    return session.cookies.get('INDIVIDUAL_KEY')

def cli(args):
    s = requests.Session()

    login(s)

    r = s.get(BENDON_SITE + "/do")
    soup = BeautifulSoup(r.text, 'lxml')

    for orderUrl in getOrderUrl(s):
        menu = Menu(s, orderUrl)
        item1 = menu.getItemNameList()[0]
        item2 = menu.getItemNameList()[2]
        menu.setItemQty(item1, 3)
        menu.setItemQty(item2, 1)
        menu.setItemComment(item1, "YoYo")
        menu.setItemComment(item2, "GoGo")
        print(item1)
        print(item2)
        menu.sendOrder(s)
        break

if __name__ == "__main__":
    exit(cli(sys.argv[1:]))
