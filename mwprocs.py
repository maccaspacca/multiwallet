"""
 Bismuth Multiple Address Wallet (Procedures Module)
 Version 0.0.2 (Test)
 Date 15/02/2018
 Copyright Maccaspacca 2018
 Copyright Hclivess 2016 to 2018
 Author Maccaspacca
"""

import base64, os, sys, getpass, hashlib, sqlite3, time, options
from Crypto import Random
from simplecrypt import encrypt, decrypt
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA

config = options.Get()
config.read()
full_ledger = config.full_ledger_conf
ledger_path = config.ledger_path_conf
hyper_path = config.hyper_path_conf

def generate():

	try:
		# generate key pair and an address
		key = RSA.generate(4096)
		#public_key = key.publickey()

		private_key_readable = key.exportKey().decode("utf-8")
		public_key_readable = key.publickey().exportKey().decode("utf-8")
		address = hashlib.sha224(public_key_readable.encode("utf-8")).hexdigest()  # hashed public key
		
		wlist = sqlite3.connect('wallet.dat')
		wlist.text_factory = str
		w = wlist.cursor()
		w.execute("INSERT INTO wallet VALUES (?,?,?,?)", (str(address),str(private_key_readable),str(public_key_readable),'0'))
		wlist.commit()
		wlist.close()
	
		return True
		
	except:
	
		return False

def checkstart():

	# check if the multiwallet exists - if not then it creates it and a single new address

	if not os.path.exists('wallet.dat'):
		# create empty wallet database
		wlist = sqlite3.connect('wallet.dat')
		wlist.text_factory = str
		w = wlist.cursor()
		w.execute("CREATE TABLE IF NOT EXISTS wallet (address, privkey, pubkey, crypted)")
		wlist.commit()
		wlist.close()
		generate()
		# create empty wallet database

def readcrypt(myaddress): # check encryption status of an address in the wallet

	cwallet = sqlite3.connect('wallet.dat')
	cwallet.text_factory = str
	c = cwallet.cursor()
	c.execute("SELECT crypted FROM wallet WHERE address =?;", (myaddress,))
	iscrypted = c.fetchall()
	cwallet.close()
	
	return iscrypted

def readaddys(): # get list of bismuth addresses in the wallet

	awallet = sqlite3.connect('wallet.dat')
	awallet.text_factory = str
	a = awallet.cursor()
	a.execute("SELECT distinct address FROM wallet;")
	addys = a.fetchall()
	awallet.close()
	
	return addys

def readpub(myaddress): # gets the public key of an address in the wallet

	uwallet = sqlite3.connect('wallet.dat')
	uwallet.text_factory = str
	u = uwallet.cursor()
	u.execute("SELECT pubkey FROM wallet WHERE address = ?;", (myaddress,))
	ukeys = u.fetchone()[0]
	uwallet.close()
	
	return ukeys

def readpriv(myaddress): # gets the private key and encryption status of an address in the wallet

	rwallet = sqlite3.connect('wallet.dat')
	rwallet.text_factory = str
	r = rwallet.cursor()
	r.execute("SELECT privkey,crypted FROM wallet WHERE address = ?;", (myaddress,))
	rkeys = r.fetchone()
	rwallet.close()
	
	return rkeys

def dec_key(address): # decrypts an encrypted private key for an address in the wallet returning the signing key and private key

	password = getpass.getpass()
	encrypted_privkey = readpriv(address)
	decrypted_privkey = (decrypt(password, encrypted_privkey[0]).decode("utf-8"))
	#print(decrypted_privkey)
	key = RSA.importKey(decrypted_privkey)  # for signing
	#print(key)
	
	password = ""
	
	return key, decrypted_privkey

def read(curr_address): # the equivalent of keys.read in the default wallet

	#import keys
	myprivs = readpriv(curr_address)
	my_pk = myprivs[0]
	my_pkc = int(myprivs[1])

	if my_pkc == 1:
		print("Private Key is Encrypted")
		decoded_keys = dec_key(curr_address)
		private_key_readable = decoded_keys[1]
		key = decoded_keys[0]
		#print(private_key_readable)
		#print(key)
	else:
		private_key_readable = my_pk
		key = RSA.importKey(private_key_readable)  # for signing
		#print(private_key_readable)
		#print(key)

	public_key_readable = readpub(curr_address)
	#print(public_key_readable)

	if (len(public_key_readable)) != 271 and (len(public_key_readable)) != 799:
		raise ValueError("Invalid public key length: {}".format(len(public_key_readable)))

	public_key_hashed = base64.b64encode(public_key_readable.encode("utf-8")).decode("utf-8")
	address = hashlib.sha224(public_key_readable.encode("utf-8")).hexdigest()
	# import keys

	return key, private_key_readable, public_key_readable, public_key_hashed, address, my_pkc
	
def writepriv(newkey,myaddress): # writes the encrypted private key to an address in the wallet

	wwallet = sqlite3.connect('wallet.dat')
	wwallet.text_factory = str
	w = wwallet.cursor()
	w.execute("UPDATE wallet SET privkey = ?,crypted = 1 WHERE address = ?;", (newkey,myaddress))
	wwallet.commit()
	wwallet.close()
	
def enc_key(address): # encrypts the private key for an address in the wallet

	goodpass = False
	
	x = 0
	while x < 3:
		input_password1 = getpass.getpass()
		print("Thanks, confirm password")
		input_password2 = getpass.getpass()
		
		if input_password1 == input_password2:
			privkey_not = readpriv(address)
			#print("{}......".format(str(privkey_not[0])))
			ciphertext = encrypt(input_password1, str(privkey_not[0]))
			writepriv(ciphertext,address)
			goodpass = True
			x = 3
		else:
			print("passwords do not match - try again\n")
			x +=1
	
	input_password1 = ""
	input_password2 = ""
	
	if goodpass:
		return True
	else:
		return False
		
def get_stats(address): # gets the financial statistics for an address in the wallet.

	mempool = sqlite3.connect('mempool.db')
	mempool.text_factory = str
	m = mempool.cursor()

	# include mempool fees
	m.execute("SELECT count(amount), sum(amount) FROM transactions WHERE address = ?;", (address,))
	result = m.fetchall()[0]
	if result[1] != None:
		debit_mempool = float('%.8f' % (float(result[1]) + float(result[1]) * 0.001 + int(result[0]) * 0.01))
	else:
		debit_mempool = 0
	# include mempool fees

	if full_ledger == 1:
		conn = sqlite3.connect(ledger_path)
	else:
		conn = sqlite3.connect(hyper_path)

	conn.text_factory = str
	c = conn.cursor()
	c.execute("SELECT sum(amount) FROM transactions WHERE recipient = ?;", (address,))
	credit = c.fetchone()[0]
	c.execute("SELECT sum(amount) FROM transactions WHERE address = ?;", (address,))
	debit = c.fetchone()[0]
	c.execute("SELECT sum(fee) FROM transactions WHERE address = ?;", (address,))
	fees = c.fetchone()[0]
	c.execute("SELECT sum(reward) FROM transactions WHERE address = ?;", (address,))
	rewards = c.fetchone()[0]
	c.execute("SELECT MAX(block_height) FROM transactions")
	bl_height = c.fetchone()[0]

	debit = 0 if debit is None else float('%.8f' % debit)
	fees = 0 if fees is None else float('%.8f' % fees)
	rewards = 0 if rewards is None else float('%.8f' % rewards)
	credit = 0 if credit is None else float('%.8f' % credit)

	balance = '%.8f' % (credit - debit - fees + rewards - debit_mempool)
	
	return debit,fees,rewards,credit,balance

def send_bis(myaddress): # sends bismuth from a selected address in the wallet
	
	(key, private_key_readable, public_key_readable, public_key_hashed, address, my_pkc) = read(myaddress)
	(debit,fees,rewards,credit,balance) = get_stats(myaddress)
	
	amount_input = input("Amount to send: ")

	recipient_input = input("Recipient address: ")

	keep_input = 0

	openfield_input = input("Enter openfield data (message): ")
	
	fee = '%.8f' % float(0.01 + (float(len(openfield_input)) / 100000) + int(keep_input))  # 0.01 dust
	print("Fee: %s" % fee)

	confirm = input("Confirm (y/n): ")

	if confirm != 'y':
		print("Transaction cancelled, user confirmation failed")
		exit(1)

	# hardfork fee display
	try:
		float(amount_input)
		is_float = 1
	except ValueError:
		is_float = 0
		exit(1)

	if len(str(recipient_input)) != 56:
		print("Wrong address length")
		return False
	else:
		timestamp = '%.2f' % time.time()
		transaction = (str(timestamp), str(address), str(recipient_input), '%.8f' % float(amount_input), str(keep_input), str(openfield_input))  # this is signed
		# print transaction

		h = SHA.new(str(transaction).encode("utf-8"))
		signer = PKCS1_v1_5.new(key)
		signature = signer.sign(h)
		signature_enc = base64.b64encode(signature)
		txid = signature_enc[:56]

		print("Encoded Signature: %s" % signature_enc.decode("utf-8"))
		print("Transaction ID: %s" % txid.decode("utf-8"))

		verifier = PKCS1_v1_5.new(key)

		if verifier.verify(h, signature):
			if float(amount_input) < 0:
				print("Signature OK, but cannot use negative amounts")
				return False

			elif float(amount_input) + float(fee) > float(balance):
				print("Mempool: Sending more than owned")
				return False

			else:
				print("The signature is valid, proceeding to save transaction to mempool")
				mempool = sqlite3.connect('mempool.db')
				mempool.text_factory = str
				m = mempool.cursor()
				m.execute("INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?)", (str(timestamp), str(address), str(recipient_input), '%.8f' % float(amount_input), str(signature_enc.decode("utf-8")), str(public_key_hashed), str(keep_input), str(openfield_input)))
				mempool.commit()  # Save (commit) the changes
				mempool.close()
				print("Mempool updated with a received transaction")
				return True
				# refresh() experimentally disabled
		else:
			print("Invalid signature")
			return False
			# enter transaction end
