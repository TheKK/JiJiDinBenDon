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
import argparse
import notify2
import jijidinbendon as BenDon

username = "guest"
password = "guest"

def interactiveMode (args):
    benDon = BenDon.BenDonSession()
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
        for i in range(0, 5):
            ordering = orderings[i]
            creator = ordering["creator"]
            shopName = ordering["shopName"]
            count = ordering["count"]

            print("[%d] %s create %s, now %s people has ordered"
                  % (i, creator, shopName, count))

        chosenOrdering = int(raw_input('which to order?'))

        # Choose which item you want for lunch
        menu = BenDon.Menu(benDon.session, orderings[chosenOrdering]["orderUrl"])
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

        detail = BenDon.Detail(benDon.session, orderings[chosenOrdering]["detailUrl"])
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

def commandMode(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true',
                        help='check if all lunchs are ordered')
    parser.add_argument('-r', action='store_true',
                        help='randomly order any possilbe lunch')
    parser.add_argument('-c', default="",
                        help='ordering comment')
    parser.add_argument('-n', default="BenDonRobot",
                        help='ordering name')
    parser.add_argument('-p', action='store_true',
                        help='show popup message')
    args = parser.parse_args(args)

    benDon = BenDon.BenDonSession()
    cookieFilePath = "cookie"
    retVal = 0
    comment = args.c
    name = args.n

    if os.path.isfile(cookieFilePath):
        benDon.loadCookies(cookieFilePath)

    benDon.login(username, password)

    if args.check:
        for ordering in benDon.getInProgressOrderings():
            detail = BenDon.Detail(benDon.session, ordering["detailUrl"])
            if len(detail.getOrderingDetails()) == 0:
                retVal = 1
    elif args.r:
        for ordering in benDon.getInProgressOrderings():
            menu = BenDon.Menu(benDon.session, ordering["orderUrl"])
            items = menu.getItemList()
            numItem = len(items)
            itemToOrder = items[random.randrange(0, numItem)]

            # variation price
            if itemToOrder["priceInput"] is not "":
                priceToOrder = random.randrange(0, len(itemToOrder["price"]))
                menu.setVariationPrice(itemToOrder, priceToOrder)

            menu.setNameForOrdering(name)
            menu.setItemQty(itemToOrder, 1)
            menu.setItemComment(itemToOrder, comment)
            menu.sendOrder(benDon.session)

            msg = ("You have ordered \'%s\' from \'%s\' as \'%s\'!"
                  % (itemToOrder["name"], ordering["shopName"], name))

            notify2.init("JiJiDinBenDon")
            n = notify2.Notification("Lunch ordered!!", msg, "weather-storm")
            n.show()

    benDon.saveCookies(cookieFilePath)

    return retVal

def printGlobalHelp():
    print("Avaliable command:")
    print("  interactive")
    print("  command")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        printGlobalHelp()
        exit(1)
    modeName = sys.argv[1]

    if modeName == "interactive":
        modeToRun = interactiveMode
    elif modeName == "command":
        modeToRun = commandMode
    else:
        printGlobalHelp()
        exit(1)

    exit(modeToRun(sys.argv[2:]))
