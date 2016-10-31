import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
import re
import os
import json
import sqlite3

EMAIL = ""
PASSWORD = ""

with requests.Session() as r:
    i = 0

    deepSearch = False

    def toggleDeepSearch(status):
        global deepSearch
        deepSearch = status

    def getImages(json_data):
        # Returns True -> Loaded All Images
        # Returns False -> More Images Can Be Loaded
        userID = json_data['items'][0]['user']['id']
        userName = json_data['items'][0]['user']['username']
        for image in json_data['items']:
            imageID = image['id']
            fileName = image['created_time']
            link = image['link']
            url = image['images']['standard_resolution']['url']
            url = url.split('?')[0]
            url = re.sub(r'/s\d{3,}x\d{3,}/', '/', url)
            if(checkImage(imageID)):
                if(not deepSearch):
                    return True
            else:
                downloadImage (userName, fileName, url)
                addImage (userID, imageID, link)
        return False

    def downloadImage(directory, imageTitle, imageLink):
        os.system("aria2c " + imageLink + " --dir='" + directory + "' --out='" + imageTitle + ".jpg'")
        global i
        print (str(i) + " - " + imageLink)
        i += 1

    def checkImage(imageID):
        conn = sqlite3.connect('instagram.db')
        cur = conn.cursor()
        cur.execute('''SELECT * FROM Image WHERE imageID = ?''', (imageID,))
        row = cur.fetchone()
        conn.commit()
        cur.close()
        if row is None:
            return False
        else:
            return True

    def addImage(userID, imageID, link):
        conn = sqlite3.connect('instagram.db')
        cur = conn.cursor()
        cur.execute('''INSERT INTO Image (`userID`, `imageID`, `link`) VALUES (?, ?, ?)''', (userID, imageID, link))
        conn.commit()
        cur.close()

    def getUserNames():
        conn = sqlite3.connect('instagram.db')
        cur = conn.cursor()
        cur.execute('''Select userName FROM User''')
        rows = cur.fetchall()
        conn.commit()
        cur.close()
        return rows

    def showAllUsers():
        conn = sqlite3.connect('instagram.db')
        cur = conn.cursor()
        cur.execute('''Select userName, fullName FROM User''')
        rows = cur.fetchall()
        print ("Users in Database are : ")
        for row in rows:
            print (row[0], "\t", row[1])
        conn.commit()
        cur.close()

    def downloadUserImages(userName = None):
        if (userName is None):
            userNames = getUserNames()
        else:
            userNames = [(userName,)]
        global i
        for user in userNames:
            print ("Download for", user)
            i = 0
            userName = user[0]
            directory = userName
            try:
                os.stat(directory)
            except:
                os.system('mkdir "' + directory + '"')

            BASE_URL = "https://www.instagram.com/" + userName + "/media/?&max_id="
            url = BASE_URL

            json_data = json.loads(r.get(url, cookies = cookies).text)

            doneFlag = getImages(json_data)
            lastID = json_data['items'][-1]['id']

            while(json_data['more_available'] and (not doneFlag)):
                url = BASE_URL + lastID
                json_data = json.loads(r.get(url).text)
                lastID = json_data['items'][-1]['id']
                doneFlag = getImages(json_data)

            print ("Downloaded " + str(i) + " images for " + userName)

    def addUser(userName):
        BASE_URL = "https://www.instagram.com/" + userName + "/media/?&max_id="
        url = BASE_URL

        json_data = json.loads(r.get(url, cookies = cookies).text)
        userID = json_data['items'][0]['user']['id']
        fullName = json_data['items'][0]['user']['full_name']

        conn = sqlite3.connect('instagram.db')
        cur = conn.cursor()
        cur.execute('''INSERT INTO User (`userName`, `userID`, `fullName`) VALUES (?, ?, ?)''', (userName, userID, fullName))
        conn.commit()
        cur.close()

        print ("Added " + userName + " (ID = " + userID + ")")

    def deepSearchDwonloadUser():
        global deepSearch
        deepSearch = True
        showAllUsers()
        print ("\n")
        user = input("Enter username : ")
        downloadUserImages(user)


    r.get("https://www.instagram.com/accounts/login/")
    login_data = {"username" : EMAIL, "password" : PASSWORD}
    cookies = r.cookies.get_dict()
    headers = {'x-csrftoken':r.cookies['csrftoken'], 'origin':'https://www.instagram.com', 'referer':'https://www.instagram.com/accounts/login/'}
    page_data = r.post("https://www.instagram.com/accounts/login/ajax/", data=login_data, cookies = cookies, headers = headers)

    print (page_data.text)

    while True:
        print ("\n\n WELCOME TO INSTAGRAM DOWNLOADER \n\n")
        print ("1. Add a user")
        print ("2. Download data from all users")
        print ("3. Show users")
        print ("4. Enable Deep Search")
        print ("5. Disable Deep Search")
        print ("6. Deep Search Download User")
        print ("7. Exit")
        print ("Deep search :", deepSearch, "\n")
        choice = int(input("Enter your choice:"))
        if(choice == 1):
            userName = input("Enter username : ")
            addUser(userName)
        elif (choice == 2):
            downloadUserImages()
        elif (choice == 3):
            showAllUsers()
        elif (choice == 4):
            toggleDeepSearch(True)
        elif (choice == 5):
            toggleDeepSearch(False)
        elif (choice == 6):
            deepSearchDwonloadUser()
        elif (choice == 7):
            break;
        else:
            print ("Error : Please enter a valid choice")
