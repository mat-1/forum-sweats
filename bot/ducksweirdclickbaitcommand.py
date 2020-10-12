import random

gaming = "1"
contacting = "2"
challenge = "3"

cap = "4"
nocap = "5"

themeList = [gaming, contacting, challenge]
yes = "yes"
no = "no"
repeat = ""
generating = False
capsList = [True, False]


def generate():
	theme = random.choice(themeList)
	gaming1caps = random.choice(capsList)
	gaming2caps = random.choice(capsList)
	gaming3caps = random.choice(capsList)
	gaming4caps = random.choice(capsList)

	contact1caps = random.choice(capsList)
	contact2caps = random.choice(capsList)
	contact3caps = random.choice(capsList)
	contact4caps = random.choice(capsList)

	challenge1caps = random.choice(capsList)
	challenge2caps = random.choice(capsList)
	challenge3caps = random.choice(capsList)
	challenge4caps = random.choice(capsList)

	if theme == gaming:
		gamingList1 = ["beating", "winning against", "I got killed by", "I won with", "I won against"]
		gamingList2 = ["the best player ever", "a famous youtuber", "the president", "an asian gamer"]
		gamingList3 = ["in Minecraft!", "in Overwatch!", "in Call of Duty!", "in Roblox!", "in Fortnite!"]
		gamingList4 = ["(intense)", "(ultra gamer)", "(so close)", "(omg)", "(pro)"]

		gaming1 = random.choice(gamingList1)
		if gaming1caps:
			gaming1 = gaming1.upper()
		gaming2 = random.choice(gamingList2)
		if gaming2caps:
			gaming2 = gaming2.upper()
		gaming3 = random.choice(gamingList3)
		if gaming3caps:
			gaming3 = gaming3.upper()
		gaming4 = random.choice(gamingList4)
		if gaming4caps:
			gaming4 = gaming4.upper()

		return f'{gaming1} {gaming2} {gaming3} {gaming4}'

	if theme == contacting:
		contactList1 = ["calling", "meeting", "inviting over"]
		contactList2 = ["Elmo", "Barney", "Santa Claus", "Pennywise", "Thanos", "Scooby Doo", "Shrek"]
		contactList3 = ["at 3AM!", "at midnight!", "at 1AM!", "at night!"]
		contactList4 = ["(scary)", "(omg he came)", "(intense)", "(cops called)", "(don't try this at home)", "(crazy)"]

		contact1 = random.choice(contactList1)
		if contact1caps:
			contact1 = contact1.upper()
		contact2 = random.choice(contactList2)
		if contact2caps:
			contact2 = contact2.upper()
		contact3 = random.choice(contactList3)
		if contact3caps:
			contact3 = contact3.upper()
		contact4 = random.choice(contactList4)
		if contact4caps:
			contact4 = contact4.upper()

		return f'{contact1} {contact2} {contact3} {contact4}'

	if theme == challenge:
		challengeList1 = ["buying", "selling", "eating", "stealing"]
		challengeList2 = ["everything in the store", "all of my parent's belongings", "everything I can hold", "everything green", "everything orange", "everything blue", "everything red"]
		challengeList3 = ["- challenge", "- super hard challenge", "- expensive challenge", "- impossible challenge"]

		challenge1 = random.choice(challengeList1)
		if challenge1caps:
			challenge1 = challenge1.upper()
		challenge2 = random.choice(challengeList2)
		if challenge2caps:
			challenge2 = challenge2.upper()
		challenge3 = random.choice(challengeList3)
		if challenge3caps:
			challenge3 = challenge3.upper()

		return f'{challenge1} {challenge2} {challenge3}'
