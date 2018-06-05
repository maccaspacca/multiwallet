"""
 Bismuth Multiple Address Wallet (Procedures Module)
 Version RC 1.0
 Date 05/06/2018
 Copyright Maccaspacca 2018
 Copyright Bismuth Foundation 2016 to 2018
 Author Maccaspacca
"""

import base64, os, sys, getpass, hashlib, sqlite3, time, logging, wx, pathlib
from simplecrypt import encrypt, decrypt
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
from Crypto.Protocol.KDF import PBKDF2
from libs.mnemonic import Mnemonic
from libs.rsa_py import rsa_functions
from logging.handlers import RotatingFileHandler

# setup logging
log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
logFile = 'procs.log'
my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=5 * 1024 * 1024, backupCount=2, encoding=None, delay=0)
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.INFO)
app_log = logging.getLogger('root')
app_log.setLevel(logging.INFO)
app_log.addHandler(my_handler)


def imp_seed(mseed,mpass):

	try:
	
		# some predefined variables to keep parity with jimhsu code
		
		#mnemo = Mnemonic('english')
		iterations = 20000
		length = 48
		n = 4096
		cointype = 209 # Provisionally, 209 (atomic weight of bismuth) (see https://github.com/satoshilabs/slips/blob/master/slip-0044.md )
		aid = 1
		addrs = 1

		# key generation

		address = ""
		#pwd_a = mnemo.generate(strength=256)
		pwd_a = mseed

		app_log.info("Imported seed = {}".format(pwd_a))
		passphrase = mpass
		passP = "mnemonic" + passphrase

		master_key = PBKDF2(pwd_a.encode('utf-8'), passP.encode('utf-8'), dkLen=length, count=iterations)
		#print("Master key: " + str(base64.b64encode(master_key)))

		deriv_path = "m/44'/"+ str(cointype) +"'/" + str(aid) + "'/0/" + str(addrs) #HD path

		account_key = PBKDF2(master_key, deriv_path.encode('utf-8'), dkLen=length, count=1)
		#print("Account key: " + str(base64.b64encode(account_key)))

		rsa = rsa_functions.RSAPy(n,account_key)
		key = RSA.construct(rsa.keypair)

		private_key_readable = key.exportKey().decode("utf-8")
		public_key_readable = key.publickey().exportKey().decode("utf-8")
		address = hashlib.sha224(public_key_readable.encode("utf-8")).hexdigest()  # hashed public key
		
		app_log.info('Imported address: {} from seed'.format(address))
		
		wlist = sqlite3.connect('wallet.dat')
		wlist.text_factory = str
		w = wlist.cursor()
		w.execute("INSERT INTO wallet VALUES (?,?,?,?,?,?,?)", (str(address),str(private_key_readable),str(public_key_readable),'0','',pwd_a,'1'))
		wlist.commit()
		wlist.close()
		
		app_log.info('Inserted imported address into wallet.dat')

		return True,address,pwd_a
		
	except:
	
		return False,"",""


def generate():

	from tkinter import Tk
	import tkinter.simpledialog as sdlg
	root = Tk()
	root.withdraw()

	try:
	
		# some predefined variables to keep parity with jimhsu code
		
		create_text = "Your new address is being created from seed\n"\
					"You can enter an optional seed password.\n"\
					"WARNING this is not stored so you will need to remember it !\n"\
					"Click OK when entered or if you want none set"
		
		passphrase = sdlg.askstring("New address creation",create_text, show='*')
		
		mnemo = Mnemonic('english')
		iterations = 20000
		length = 48
		n = 4096
		cointype = 209 # Provisionally, 209 (atomic weight of bismuth) (see https://github.com/satoshilabs/slips/blob/master/slip-0044.md )
		aid = 1
		addrs = 1

		# key generation

		address = ""
		pwd_a = mnemo.generate(strength=256)

		app_log.info("Mnemonic (seed) = {}".format(pwd_a))
		#passphrase = ""
		passP = "mnemonic" + passphrase

		master_key = PBKDF2(pwd_a.encode('utf-8'), passP.encode('utf-8'), dkLen=length, count=iterations)
		#print("Master key: " + str(base64.b64encode(master_key)))

		deriv_path = "m/44'/"+ str(cointype) +"'/" + str(aid) + "'/0/" + str(addrs) #HD path

		account_key = PBKDF2(master_key, deriv_path.encode('utf-8'), dkLen=length, count=1)
		#print("Account key: " + str(base64.b64encode(account_key)))

		rsa = rsa_functions.RSAPy(n,account_key)
		key = RSA.construct(rsa.keypair)

		private_key_readable = key.exportKey().decode("utf-8")
		public_key_readable = key.publickey().exportKey().decode("utf-8")
		address = hashlib.sha224(public_key_readable.encode("utf-8")).hexdigest()  # hashed public key
		
		app_log.info('Generated address: {}'.format(address))
		
		wlist = sqlite3.connect('wallet.dat')
		wlist.text_factory = str
		w = wlist.cursor()
		w.execute("INSERT INTO wallet VALUES (?,?,?,?,?,?,?)", (str(address),str(private_key_readable),str(public_key_readable),'0','',pwd_a,'1'))
		wlist.commit()
		wlist.close()
		
		app_log.info('Inserted new address into wallet.dat')
	
		return True,address,pwd_a
		
	except:
	
		return False,"",""

def checkstart():

	# check if the multiwallet exists - if not then it creates it and a single new address

	if not os.path.exists('wallet.dat'):
		# create empty wallet database
		wlist = sqlite3.connect('wallet.dat')
		wlist.text_factory = str
		w = wlist.cursor()
		w.execute("CREATE TABLE IF NOT EXISTS wallet (address, privkey, pubkey, crypted, account, seed, hd)")
		wlist.commit()
		wlist.close()
		generate()
		# create empty wallet database and add first address

def readcrypt(myaddress): # check encryption status of an address in the wallet

	cwallet = sqlite3.connect('wallet.dat')
	cwallet.text_factory = str
	c = cwallet.cursor()
	c.execute("SELECT crypted,hd FROM wallet WHERE address =?;", (myaddress,))
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
	r.execute("SELECT privkey,crypted,seed FROM wallet WHERE address = ?;", (myaddress,))
	rkeys = r.fetchone()
	rwallet.close()
	#print(rkeys[2])
	
	return rkeys

def dec_key(address): # decrypts an encrypted private key for an address in the wallet returning the signing key, private key and seed

	try:
		dlgs = wx.PasswordEntryDialog(None, 'Insert password for address:\n{}'.format(address), 'Decrypting things for you....', '', style=wx.TextEntryDialogStyle)
		if dlgs.ShowModal() == wx.ID_OK:
			password = str(dlgs.GetValue())
		else:
			password = ""
		dlgs.Destroy()
		busyDlg = wx.BusyInfo("Busy decrypting {} !".format(address))
		encrypted_privkey = readpriv(address)
		decrypted_privkey = (decrypt(password, encrypted_privkey[0]).decode("utf-8"))
		decrypted_seed = (decrypt(password, encrypted_privkey[2]).decode("utf-8"))
		#print(decrypted_privkey)
		key = RSA.importKey(decrypted_privkey)  # for signing
		#print(key)
	except:
		key = "Incorrect password"
		decrypted_privkey = False
		decrypted_seed = "Incorrect password"
	
	password = None
	busyDlg = None
	
	return key, decrypted_privkey, decrypted_seed

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
		seed = decoded_keys[2]
		#print(private_key_readable)
		#print(key)
	else:
		private_key_readable = my_pk
		key = RSA.importKey(private_key_readable)  # for signing
		seed = myprivs[2]
		#print(private_key_readable)
		#print(key)

	public_key_readable = readpub(curr_address)
	#print(public_key_readable)

	if (len(public_key_readable)) != 271 and (len(public_key_readable)) != 799:
		raise ValueError("Invalid public key length: {}".format(len(public_key_readable)))

	public_key_hashed = base64.b64encode(public_key_readable.encode("utf-8")).decode("utf-8")
	address = hashlib.sha224(public_key_readable.encode("utf-8")).hexdigest()
	# import keys

	return key, private_key_readable, public_key_readable, public_key_hashed, address, my_pkc, seed
	
def writepriv(newkey,myaddress,newseed, mystate): # writes the private key to an address in the wallet

	wwallet = sqlite3.connect('wallet.dat')
	wwallet.text_factory = str
	w = wwallet.cursor()
	w.execute("UPDATE wallet SET privkey = ?,crypted = ?,seed = ? WHERE address = ?;", (newkey,mystate,newseed,myaddress))
	wwallet.commit()
	wwallet.close()
	
def enc_key(address): # encrypts the private key and seed string for an address in the wallet

	goodpass = False
	x = 0
	
	while x < 3:
	
		try:
		
			dlgs = wx.PasswordEntryDialog(None, 'Try {} of 3 - Please enter encryption password:'.format(str(x+1)), 'Password Input', '', style=wx.TextEntryDialogStyle)
			if dlgs.ShowModal() == wx.ID_OK:
				input_password1 = str(dlgs.GetValue())
			else:
				input_password1 = "x"
			dlgs = wx.PasswordEntryDialog(None, 'Try {} of 3 - Please confirm the password:'.format(str(x+1)), 'Password Input', '', style=wx.TextEntryDialogStyle)
			if dlgs.ShowModal() == wx.ID_OK:
				input_password2 = str(dlgs.GetValue())
			else:
				input_password2 = "y"
			
			dlgs.Destroy()
		
			if input_password1 == input_password2:
				busyDlg = wx.BusyInfo("Busy encrypting {} !".format(address))
				privkey_not = readpriv(address)
				ciphertext = encrypt(input_password1, str(privkey_not[0]))
				if str(privkey_not[2]) == " ":
					seedtext = "traditional key no seed for this address"
				else:
					seedtext = encrypt(input_password1, str(privkey_not[2]))
				writepriv(ciphertext,address,seedtext,"1")
				goodpass = True
				x = 3
			else:
				msgbox = wx.MessageDialog(None,"Passwords Do Not Match !!!","Encrypting address",wx.ICON_ERROR)
				msgbox.ShowModal()
				msgbox.Destroy()
				x +=1
			
			busyDlg = None
				
		except:
			x +=1
			
	input_password1 = ""
	input_password2 = ""
	
	if goodpass:
		return True
	else:
		return False
		
def dec_all(address): # decrypts the private key and seed string for an address in the wallet

	goodpass = False
	
	x = 0
	while x < 3:
	
		try:
		
			dlgs = wx.PasswordEntryDialog(None, 'Try {} of 3 - Please enter your decryption password:'.format(str(x+1)), 'Password Input', '', style=wx.TextEntryDialogStyle)
			if dlgs.ShowModal() == wx.ID_OK:
				password = str(dlgs.GetValue())
			else:
				password = "x"
		
			busyDlg = wx.BusyInfo("Busy decrypting.......")
			encrypted_privkey = readpriv(address)
			decrypted_privkey = (decrypt(password, encrypted_privkey[0]).decode("utf-8"))
			decrypted_seed = (decrypt(password, encrypted_privkey[2]).decode("utf-8"))
			busyDlg = None
				
			writepriv(decrypted_privkey,address,decrypted_seed,"0")
			goodpass = True
			x = 3

		except:
			busyDlg = None
			x +=1
			goodpass = False
			
	password = ""
	
	if goodpass:
		return True
	else:
		return False
		
def delete_add(myaddress):

	good_delete = False
	
	try:
		dwallet = sqlite3.connect('wallet.dat')
		dwallet.text_factory = str
		d = dwallet.cursor()
		d.execute("DELETE FROM wallet WHERE address = ?;", (myaddress,))
		dwallet.commit()
		dwallet.close()
		good_delete = True
	except:
		good_delete = False
		
	if good_delete:
		return True
	else:
		return False
		
def read_exp():

	ewallet = sqlite3.connect('wallet.dat')
	ewallet.text_factory = str
	e = ewallet.cursor()
	e.execute("SELECT address,crypted,seed,hd FROM wallet;")
	s_exp = e.fetchall()
	ewallet.close()
	
	timestamp = '%.0f' % time.time()
	pathlib.Path('export').mkdir(parents=True, exist_ok=True)
	filepath = "export/expseed_{}.txt".format(timestamp)
	
	try:
		with open(filepath, 'w') as file_handler:
			for ex in s_exp:
			
				if ex[3] == "1":
					t_write = True
					if ex[1] == "0":
						ex_seed = ex[2]
					else:
						ex_temp = dec_key(ex[0])
						ex_seed = ex_temp[2]
				else:
					t_write = False
							
				if t_write:
					ex_write = "{},{}".format(str(ex[0]),ex_seed)
					file_handler.write("{}\n".format(ex_write))
		
		return True,filepath
	
	except:
		return False,"error"
		
