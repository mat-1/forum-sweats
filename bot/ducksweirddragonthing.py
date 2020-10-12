import random

def fight(eyes):
	yes = "yes"
	no = "no"
	dragon = ""

	legs = ""
	chest = ""
	boots = ""
	helm = ""
	epicPet = ""
	legPet = ""
	sword = ""

	redo = ""

	lootList = ""

	weight = 0

	fighting = False

	dist = [6, 16, 16, 16, 16, 16, 16]
	dragList = ["superior"]*6+["young"]*16+["old"]*16+["protector"]*16+["unstable"]*16+["strong"]*16+["wise"]*16

	if eyes == 1:
		lootList = ["Leggings"]*4401+["Helmet"]*4402+["Boots"]*4403+["Frags"]*4600
	if eyes == 2:
		lootList = ["Aspect of the Dragons"]*3000+["Chestplate"]*3500+["Leggings"]*3499+["Helmet"]*3498+["Boots"]*3497+["Frags"]*3400
	if eyes == 3:
		lootList = ["Legendary Dragon Pet"]*1+["Epic Dragon Pet"]*5+["Aspect of the Dragons"]*3500+["Chestplate"]*3800+["Leggings"]*3799+["Helmet"]*3798+["Boots"]*3797+["Frags"]*3790
	if eyes == 4:
		lootList = ["Legendary Dragon Pet"]*1+["Epic Dragon Pet"]*5+["Aspect of the Dragons"]*3995+["Chestplate"]*4001+["Leggings"]*4002+["Helmet"]*4001+["Boots"]*4000+["Frags"]*3990
	else:
		return 'Invalid amount of eyes (must be 1-4)'

	if start == yes:
		fighting = True

	while fighting:
		dragon = random.choice(dragList)
		loot = random.choice(lootList)
		print("you got a " + dragon + " dragon!")
		print("your loot was " + loot)
		fighting = False

		redo = input("fight again? ")
		if redo == yes:
			fighting = True

	input("press enter to close")