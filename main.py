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
import os.path
import time
import random
import json
import re
import argparse
import requests
from bs4 import BeautifulSoup

BENDON_SITE = "https://dinbendon.net"

username = "guest"
password = "guest"

"""
Formats
=======

    self.menu_ = {
        "items": [
           { "name": XXX, "price": XXX },
           ...
           ],
        "qtyInputs": [
            { "name": XXX, "qty": XXX }, #name, is the name of input section
            ...
        ],
        "commentInputs": [
            { "name": XXX, "comment": XXX }, #name, is the name of input section
            ...
        ],
        "userInput": XXX,
        "urlToPost": XXX

"""
class Menu(object):
    def __init__(self, session, url):
        self.menu_ = {}
        self.userNameForOrdering = ""

        orderReq = session.get(url)
        soup = BeautifulSoup(orderReq.text, 'lxml')
        self.menu_['items'] = []
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

            item = {
                     "name": name,
                     "price": price
                   }
            qtyInput = {
                         "name": qtyInputName,
                         "qty" : ''
                       }
            commentInput = {
                             "name": commentInputName,
                             "comment": ""
                           }

            self.menu_['items'].append(item)
            self.menu_['qtyInputs'].append(qtyInput)
            self.menu_['commentInputs'].append(commentInput)

    def getItemList(self):
        return self.menu_["items"]

    def setItemQty(self, item, qty):
        if type(qty) is not type(666):
            print(type(qty))
            raise Exception("input qty is not number")

        index = self.menu_["items"].index(item)
        self.menu_['qtyInputs'][index]["qty"] = str(qty)

    def setItemComment(self, item, comment):
        index = self.menu_["items"].index(item)
        self.menu_['commentInputs'][index]["comment"] = str(comment)

    def setNameForOrdering(self, name):
        self.userNameForOrdering = name

    def sendOrder(self, session):
        urlToPost = self.menu_['urlToPost']

        payload = {}
        payload[self.menu_['userInput']] = self.userNameForOrdering
        payload['addOrderItemForm:hf:0'] = ""

        for qtyInput in self.menu_["qtyInputs"]:
            payload[qtyInput["name"]] = str(qtyInput["qty"])

        for commentInput in self.menu_["commentInputs"]:
            payload[commentInput["name"]] = str(commentInput["comment"])

        session.post(urlToPost, data=payload)

class Detail(object):
    def __init__(self, session, url):
        self.detail_ = {}

        orderReq = session.get(url)
        soup = BeautifulSoup(orderReq.text, 'lxml')
        self.detail_["yourOrders"] = []

        # tr here is in the form of:
        #
        # product name / No of items / Unit price / Who order ...
        # AAA          / 1           / 30         / a / b / c ...
        # AAA          / 1           / 30         / a / b / c ...
        #
        for tr in soup.find('table', 'tiles mergeView').find_all('tr'):
            if tr.find('td', 'deletable') is None:
                continue

            productName = tr.find('td', 'mergeKey').div.string
            price = tr.find_all('td')[2].div.string
            numYouOrder = tr.find('span', 'count').string.strip('x')
            nameUsedForOrdering = tr.find('td', 'cell').div.span.a.span.string
            urlToPost = BENDON_SITE + tr.find('td', 'cell').div.span.a['href']

            yourOrder = {
                          "productName": productName,
                          "price": price,
                          "qty": numYouOrder,
                          "nameForOrdering": nameUsedForOrdering,
                          "urlToPostToCancelOrdering": urlToPost
                        }

            self.detail_["yourOrders"].append(yourOrder)

        print(self.detail_["yourOrders"])

    def getOrderingDetails(self):
        return self.detail_["yourOrders"]

    def hasOrderd(self):
        return (len(self.detail_["yourOrders"]) != 0)

    def deleteOrdering(self, session, ordering):
        index = self.detail_["yourOrders"].index(ordering)
        urlToPost = self.detail_["yourOrders"][index]["urlToPostToCancelOrdering"]

        session.post(urlToPost)

class BenDonSession(object):
    def __init__(self):
        self.session = requests.Session()

    def login(self, username, password):
        r = self.session.get(BENDON_SITE + "/do/login")
        soup = BeautifulSoup(r.text, 'lxml')
        urlToPost = BENDON_SITE + soup.find('form', id='signInPanel_signInForm')['action']

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

        self.session.post(urlToPost, data=data)

        return self.session.cookies.get('INDIVIDUAL_KEY')

    def getInProgressOrderings(self):
        r = self.session.get(BENDON_SITE + "/do")
        soup = BeautifulSoup(r.text, 'lxml')
        urlsToReturn = []

        for dom in soup.find_all('tr', id=re.compile('inProgressBox_inProgressOrders_\d+')):
            AllA = dom.find_all('a')
            if not len(AllA) == 4:
                continue

            creator = AllA[2].find_all('span')[0].string
            shopName = AllA[2].find_all('span')[1].string
            count = AllA[0].find('span').string
            detailUrl = BENDON_SITE + AllA[2]['href']
            orderUrl = BENDON_SITE + AllA[3]['href']

            inProgressOrdering = {
                                   "creator": creator,
                                   "shopName": shopName,
                                   "count": count,
                                   "detailUrl": detailUrl,
                                   "orderUrl": orderUrl
                                 }

            urlsToReturn.append(inProgressOrdering)

        return urlsToReturn

    def loadCookies(self, filePath):
        cookieDict = {}
        with open(filePath, "r") as fp:
            cookieDict = json.load(fp)
        self.session.cookies = requests.utils.cookiejar_from_dict(cookieDict)

    def saveCookies(self, filePath):
        cookieDict = requests.utils.dict_from_cookiejar(self.session.cookies)
        with open(filePath, "w") as fp:
            fp.write(json.dumps(cookieDict))

def cli(args):
    benDon = BenDonSession()
    cookieFilePath = "cookie"

    if os.path.isfile(cookieFilePath):
        benDon.loadCookies(cookieFilePath)

    benDon.login(username, password)

    # TODO Make ordering another class
    orderings =  benDon.getInProgressOrderings()
    if len(orderings) is 0:
        print("There's no in progress ordering, please check it later")
        return 0

    command = raw_input("What to do? [d]etail, [o]rder, [q]uit: ")

    if command == "o":
        # Choose which ordering to order
        for i in range(0, len(orderings)):
            ordering = orderings[i]
            creator = ordering["creator"]
            shopName = ordering["shopName"]
            count = ordering["count"]

            print("[%d] %s create %s, now %s people has ordered"
                  % (i, creator, shopName, count))

        chosenOrdering = int(raw_input('which to order?'))

        # Choose which item you want for lunch
        menu = Menu(benDon.session, orderings[chosenOrdering]["orderUrl"])
        items = menu.getItemList()
        itemCount = len(items)

        for i in range(0, itemCount):
            item = items[i]

            print("[%d] %s\tprice: %s" % (i, item["name"], item["price"]))

        choosenItem = int(raw_input('which to order? '))
        orderQty = int(raw_input('quantity to order? '))
        orderComment = raw_input('any comment? (default is nothing) ')
        username_for_ordering = ""
        while username_for_ordering is "":
            username_for_ordering = raw_input("name for ordering? ")

        # Give me your personal information for free
        itemToOrder = items[choosenItem]
        menu.setNameForOrdering(username_for_ordering)
        menu.setItemQty(itemToOrder, orderQty)
        menu.setItemComment(itemToOrder, orderComment)
        menu.sendOrder(benDon.session)

        print("You have ordered \'%s\' from \'%s\' as \'%s\'!"
              % (itemToOrder["name"], orderings[chosenOrdering]["shopName"], username_for_ordering))

    elif command == "d":
        # Choose which ordering to check
        for i in range(0, len(orderings)):
            ordering = orderings[i]

            creator = ordering["creator"]
            shopName = ordering["shopName"]
            count = ordering["count"]

            print("[%d] %s create %s, now %s people has ordered"
                  % (i, creator, shopName, count))

        chosenOrdering = int(raw_input('which order to check? '))

        detail = Detail(benDon.session, orderings[chosenOrdering]["detailUrl"])
        orderingDetails = detail.getOrderingDetails()

        for i in range(0, len(orderingDetails)):
            orderingDetail = orderingDetails[i]

            productName = orderingDetail["productName"]
            price = orderingDetail["price"]
            qty = orderingDetail["qty"]
            nameForOrdering = orderingDetail["nameForOrdering"]

            print("[%d] %s %s$ x%s: %s"
                  % (i, productName, price, qty, nameForOrdering))

        command = raw_input("Now what? [c]ancel order, [q]uit ")

        if command == "c":
            whichToCancel = int(raw_input("Which one to cancel? "))

            detail.deleteOrdering(benDon.session, orderingDetails[whichToCancel])

            print("Canceled, bye!")

    benDon.saveCookies(cookieFilePath)

    return 0

if __name__ == "__main__":
    exit(cli(sys.argv[1:]))
