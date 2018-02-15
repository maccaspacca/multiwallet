"""
 Bismuth Multiple Address Wallet
 Version 0.0.2 (Test)
 Date 15/02/2018
 Copyright Maccaspacca 2018
 Copyright Hclivess 2016 to 2018
 Author Maccaspacca
"""

import mwprocs

do_bal = True
new_gen = False

mwprocs.checkstart()

while do_bal:
	
	alladdys = mwprocs.readaddys() #reads all addresses from wallet.dat

	print("")
	print("List of addresses found in wallet")
	print("---------------------------------")
	
	i = 0
	for a in alladdys:
		i += 1
		print("{} : {}".format(str(i),a[0]))
		
	print("")
	chadd = input("Please enter the number of the address you wish to use:")

	chnum = int(chadd) - 1

	curr_address = alladdys[chnum][0]
	
	address = curr_address
	
	iscrypted = mwprocs.readcrypt(address)
	my_pkc = int(iscrypted[0][0])

	
	(debit,fees,rewards,credit,balance) = mwprocs.get_stats(address)

	print("Bismuth address: {}".format(address))
	print("Total fees paid: {}".format(fees))
	print("Total rewards mined: {}".format(rewards))
	print("Total tokens received: {}".format(credit))
	print("Total tokens spent: {}".format(debit))
	print("Transaction address balance: {}\n".format(balance))
	
	print("Selected Address: {}".format(address))
	if my_pkc == 1:
		print("Encrypted\n")
	else:
		print("Not Encrypted\n")
	print("What do you wish to do next?")
	print("----------------------------\n")
	print("1. Choose another address")
	print("2. Generate new address")
	if not my_pkc == 1:
		print("3. Encrypt selected address")
	print("4. Send BIS")
	print("5. Finish\n")
	
	next_choice = input("Please enter the number of your choice :")
	
	if int(next_choice) == 1:
		do_bal = True
	elif int(next_choice) == 2:
		do_bal = True

		if mwprocs.generate():
			print("New address generated and saved")
		else:
			print("New address creation failed")

	elif int(next_choice) == 3:
		do_bal = True
		if mwprocs.enc_key(address):
			print("{} has been encrypted".format(address))
		else:
			print("There has been an error - start again")
	elif int(next_choice) == 4:
		do_bal = True
		if mwprocs.send_bis(address):
			print("Bismuth sent as requested")
		else:
			print("Transaction error !!!")
	else:
		do_bal = False
