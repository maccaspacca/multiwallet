"""
 Bismuth GUI Multiple Address Wallet
 Version Test 0.11
 Date 24th May 2018
 Copyright Maccaspacca 2018
 Copyright Bismuth Foundation 2016 to 2018
 Author Ian McEvoy (Maccaspacca)
"""

import wx
import wx.html
import wx.lib.agw.hyperlink as hl
import wx.lib.plot as plot
import  wx.lib.newevent
from wx.lib.masked import NumCtrl
import configparser as cp
import time, re, os, sys, hashlib, base64, pyqrcode, requests, json, socks, log, sqlite3
import mwprocs, connections, ticons, bisurl

from datetime import datetime
from operator import itemgetter
from decimal import *
from simplecrypt import encrypt, decrypt
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA

mw_version = "Test 0.11"
mw_copy = "The Bismuth Foundation 2018"
mw_date = "24th May 2018"
mw_author = "Ian McEvoy (Maccaspacca)"
mw_license = "GPL-3.0"

mwprocs.checkstart()

if not os.path.exists('config.dat'):

	# Create text inputs - coded to testnet for test version
	debug_level = "WARNING"
	port = "2829"
	light_ip = "127.0.0.1"
	version = "testnet"
	terminal_output = "no"
	view_all = "True"
	
	f = open('config.dat','w')
	f.write('debug_level={}\n'.format(debug_level))
	f.write('port={}\n'.format(port))
	f.write('light_ip={}\n'.format(light_ip))
	f.write('version={}\n'.format(version))
	f.write('terminal_output={}\n'.format(terminal_output))
	f.write('view_all={}\n'.format(view_all))
	f.close()

with open('config.dat') as ini:
	lines = [line.rstrip('\n') for line in ini]
	for line in lines:
		if "debug_level=" in line:
			debug_level = str(line.split('=')[1])
		if "port=" in line:
			port = str(line.split('=')[1])
		if "light_ip=" in line:
			raw_ip = str(line.split('=')[1])
			light_ip = raw_ip.split(',')
		if "version" in line:
			version = str(line.split('=')[1])
		if "terminal_output=" in line:
			terminal_output = str(line.split('=')[1])
		if "view_all=" in line:
			_view_all = str(line.split('=')[1])
			if _view_all == "False":
				view_all = False
			else:
				view_all = True
			
ini.close()
	
app_log = log.log("multiwallet.log", debug_level, terminal_output)

app_log.warning('Config read completed....')
	
global myversion
global addylist
global s
global mynode
global mytitle

mytitle = "Bismuth Multiwallet"

if "testnet" in version:
	port = 2829
	mytitle = "Bismuth Multiwallet TESTNET"
	light_ip = ["127.0.0.1"]

addylist = mwprocs.readaddys() #reads all addresses from wallet.dat

try:
	for ip in light_ip:

		try:
			s = socks.socksocket()
			s.settimeout(3)

			s.connect((ip, int(port)))
			app_log.warning("Status: Wallet connected to {}".format(ip))

			connections.send(s, "statusget", 10)
			statusget = connections.receive(s, 10)
			myversion = statusget[7]
			print("Node version: {}".format(myversion))
			mynode = ip
			break

		except Exception as e:
			app_log.warning("Status: Cannot connect to {}".format(ip))
			time.sleep(1)

except:
	divvy = wx.App()
	frame = wx.Frame(None, -1, "Connection")
	frame.SetSize(0,0,200,50)
	dlg = wx.MessageDialog(frame, "Wallet cannot connect to the node", "Connection Error", wx.OK | wx.ICON_WARNING)
	dlg.ShowModal()
	dlg.Destroy()
	frame.Destroy()
	divvy.Destroy()
	raise
	
def do_zero(zero_in):
	
	global view_all
	view_all = zero_in
	#if zero_in:
	#	view_all = "true"
	#else:
	#	view_all = "false"
	
def ask(parent, message='', title='', default_value = ''):
	dlg = wx.TextEntryDialog(parent, message, title, default_value)

	if dlg.ShowModal() == wx.ID_OK:
		result = dlg.GetValue()
	else:
		result = "cancel"
	dlg.Destroy()
	return result

(UpdateStatusEvent, EVT_UPDATE_STATUSBAR) = wx.lib.newevent.NewEvent()

a_txt = "Version: {}\nAuthor: {}\nCopyright: {}\nPublished: {}\nLicense: {}".format(mw_version,mw_author,mw_copy,mw_date,mw_license)

w_txt = """1. Select an address from the drop down list.
		2. Click on a transaction in the list to get more information.
		3. Information refreshes every 10 seconds."""

def updatestatus(newstatus,newplace):
	evt = UpdateStatusEvent(msg = newstatus, st_id = int(newplace))
	wx.PostEvent(statusbar,evt)
	
	
def tgetvars(mytemp,mytitle):

	global transis
	transis = []
	tempsis = "<table>"
	tempsis = tempsis + "<tr><td align='right' bgcolor='#DAF7A6'><b>Block:</b></td><td bgcolor='#D0F7C3'>{}</td></tr>".format(mytemp[0])
	tempsis = tempsis + "<tr><td align='right' bgcolor='#DAF7A6'><b>Timestamp:</b></td><td bgcolor='#D0F7C3'>{}</td></tr>".format(mytemp[1])
	tempsis = tempsis + "<tr><td align='right' bgcolor='#DAF7A6'><b>From:</b></td><td bgcolor='#D0F7C3'>{}</td></tr>".format(mytemp[2])
	tempsis = tempsis + "<tr><td align='right' bgcolor='#DAF7A6'><b>To:</b></td><td bgcolor='#D0F7C3'>{}</td></tr>".format(mytemp[3])
	if float(mytemp[4]) !=0:
		tempsis = tempsis + "<tr><td align='right' bgcolor='#DAF7A6'><b>Amount:</b></td><td bgcolor='#D0F7C3'>{}</td></tr>".format(mytemp[4])
	if float(mytemp[5]) !=0:
		tempsis = tempsis + "<tr><td align='right' bgcolor='#DAF7A6'><b>Reward:</b></td><td bgcolor='#D0F7C3'>{}</td></tr>".format(mytemp[5])
	tempsis = tempsis + "<tr><td align='right' bgcolor='#DAF7A6'><b>TXID:</b></td><td bgcolor='#D0F7C3'>{}</td></tr>".format(mytemp[6])
	tempsis = tempsis + "<tr><td align='right' bgcolor='#DAF7A6'><b>Hash:</b></td><td bgcolor='#D0F7C3'>{}</td></tr>".format(mytemp[7])
	tempsis = tempsis + "<tr><td align='right' bgcolor='#DAF7A6'><b>Fee:</b></td><td bgcolor='#D0F7C3'>{}</td></tr>".format(mytemp[8])
	tempsis = tempsis + "<tr><td align='right' bgcolor='#DAF7A6'><b>Openfield:</b></td><td bgcolor='#D0F7C3'>{}</td></tr>".format(mytemp[9])
	tempsis = tempsis + "</table>"
	
	transis.append(tempsis)
	transis.append(mytitle)
	
	return True
	
def send_bis(myaddress,amount_input,recipient_input,openfield_input,keep_input): # sends bismuth from a selected address in the wallet
	
	(key, private_key_readable, public_key_readable, public_key_hashed, address, my_pkc, myseed) = mwprocs.read(myaddress)
	
	if not private_key_readable:
	
		print("Incorrect Password")
		reply = "Incorrect password given"
		mydone = False
		mytxid = "Incorrect password"
		return mydone, reply, mytxid
	
	else:

		try:

			timestamp = '%.2f' % time.time()
			transaction = (str(timestamp), str(myaddress), str(recipient_input), '%.8f' % float(amount_input), str(keep_input), str(openfield_input))  # this is signed
			# print transaction

			h = SHA.new(str(transaction).encode("utf-8"))
			signer = PKCS1_v1_5.new(key)
			signature = signer.sign(h)
			signature_enc = base64.b64encode(signature)
			txid = signature_enc[:56]

			#print("Encoded Signature: %s" % signature_enc.decode("utf-8"))
			#print("Transaction ID: %s" % txid.decode("utf-8"))
			
			mytxid = txid.decode("utf-8")

			verifier = PKCS1_v1_5.new(key)
			
			if verifier.verify(h, signature):
				print("verifier")
				tx_submit = (str(timestamp), str(myaddress), str(recipient_input), '%.8f' % float(amount_input), str(signature_enc.decode("utf-8")), str(public_key_hashed), str(keep_input), str(openfield_input)) #float kept for compatibility
				print(tx_submit)
				connections.send(s, "mpinsert", 10)
				connections.send(s, tx_submit, 10)
				reply = connections.receive(s, 10)
				print(reply)
				mydone = True
				return mydone, reply, mytxid
				# refresh() experimentally disabled
			else:
				print("Invalid signature")
				reply = "Invalid signature"
				mydone = False
				return mydone, reply, mytxid
				# enter transaction end
				
		except:
			print("Oops !")
			reply = "Transaction failed - unknown reason"
			mydone = False
			mytxid = "Transaction failed"
			return mydone, reply, mytxid
			
		
def list_cryptstate(mtype):
	addylist = mwprocs.readaddys() #reads all addresses from wallet.dat
	one_addys = [x[0] for x in addylist]
	list_addys = []
	
	if mtype == 2:
		list_addys = one_addys
	
	else:
		for a in one_addys:
			
			try:

				iscrypted = int(mwprocs.readcrypt(a)[0][0])
				if iscrypted == mtype:
					state = "Yes"
				else:
					state = "No"
				
			except:
				state = "No"

			this_addy = [a,state]
			
			if this_addy[1] == "No":			
				list_addys.append(this_addy[0])
		
	return list_addys
	
def get_my_bal(a):

	try:
		connections.send(s, "balanceget", 10)
	except:
		s.connect((mynode, int(port)))
		connections.send(s, "balanceget", 10)
	
	connections.send(s, a, 10)
	stats_account = connections.receive(s, 10)
	
	return stats_account
	
#################################################################################
	
class HtmlWindow(wx.html.HtmlWindow):
    def __init__(self, parent, id, size=(1,1)):
        wx.html.HtmlWindow.__init__(self,parent, id, size=size)
        if "gtk2" in wx.PlatformInfo:
            self.SetStandardFonts()
      

#---------------------------------------------------------------------------

class AboutBoxT(wx.Dialog):
	def __init__(self):
		wx.Dialog.__init__(self, None, -1, transis[1],
			style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|
				wx.TAB_TRAVERSAL)
		hwin = HtmlWindow(self, -1, size=(560,260))
		aboutText = '<p style="color:#08750A";>{}</p>'.format(transis[0])
		hwin.SetPage(aboutText)
		btn = hwin.FindWindowById(wx.ID_OK)
		irep = hwin.GetInternalRepresentation()
		hwin.SetSize((irep.GetWidth()+40, irep.GetHeight()+10))
		self.SetClientSize(hwin.GetSize())
		self.CentreOnParent(wx.BOTH)
		self.SetFocus()
	
#----------------------------------------------------------------------------

class PageOne(wx.Window):
	def __init__(self, parent):
		wx.Window.__init__(self, parent, -1, style = wx.NO_BORDER)
					
		#self.SetBackgroundStyle(wx.BG_STYLE_ERASE)
		
		#self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
		
		self.box1 = wx.BoxSizer(wx.VERTICAL)
		
		self.topbox = wx.BoxSizer(wx.HORIZONTAL) # top box area
		
		self.left_top = wx.BoxSizer(wx.HORIZONTAL) # top left box

		logo = ticons.bismuthlogo.GetBitmap()
		self.image1 = wx.StaticBitmap(self, -1, logo)
		self.left_top.Add(self.image1, 0, wx.ALL|wx.LEFT, 5)
	
		self.right_top = wx.BoxSizer(wx.HORIZONTAL) # top right box
		
		self.b = wx.StaticText(self, -1, "")
		self.SetBackgroundColour("#FFFFFF")
		self.b.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.b.SetForegroundColour("#444995")
		self.b.SetSize(self.b.GetBestSize())
		self.right_top.Add(self.b, 0, wx.ALL|wx.CENTER, 5)
		
		self.topbox.Add(self.left_top, 0, wx.ALL|wx.LEFT, 5)
		self.topbox.Add(self.right_top, 0, wx.ALL|wx.RIGHT, 5)
		
		self.midbox = wx.BoxSizer(wx.VERTICAL)
		
		self.w_text4 = wx.StaticText(self, -1, "Wallet Address List") # list title
		self.w_text4.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.w_text4.SetForegroundColour("#08750A")
		self.w_text4.SetSize(self.w_text4.GetBestSize())
		self.midbox.Add(self.w_text4, 0, wx.ALL|wx.CENTER, 5)
		
		self.list_ctrl1 = wx.ListCtrl(self, size=(800,600),
						 style=wx.LC_REPORT
						 |wx.BORDER_SUNKEN
						 |wx.LC_HRULES
						 |wx.LC_VRULES
						 )

		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.ShowPopup, self.list_ctrl1)
		self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.ShowPopup, self.list_ctrl1)
		self.list_ctrl1.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL))
		self.list_ctrl1.InsertColumn(0, 'item', wx.LIST_FORMAT_LEFT)
		self.list_ctrl1.InsertColumn(1, 'Address', wx.LIST_FORMAT_LEFT)
		self.list_ctrl1.InsertColumn(2, 'Balance', wx.LIST_FORMAT_LEFT)
		self.list_ctrl1.InsertColumn(3, 'Received', wx.LIST_FORMAT_LEFT)
		self.list_ctrl1.InsertColumn(4, 'Spent', wx.LIST_FORMAT_LEFT)
		self.list_ctrl1.InsertColumn(5, 'Mined', wx.LIST_FORMAT_LEFT)
		self.list_ctrl1.InsertColumn(6, 'Fees', wx.LIST_FORMAT_LEFT)
		self.list_ctrl1.InsertColumn(7, 'Encrypted', wx.LIST_FORMAT_LEFT)
		self.list_ctrl1.InsertColumn(8, 'Type', wx.LIST_FORMAT_LEFT)
		
		self.list_ctrl1.SetColumnWidth(0, 0)
		self.list_ctrl1.SetColumnWidth(1, 450)
		self.list_ctrl1.SetColumnWidth(2, 125)
		self.list_ctrl1.SetColumnWidth(3, 0)
		self.list_ctrl1.SetColumnWidth(4, 0)
		self.list_ctrl1.SetColumnWidth(5, 0)
		self.list_ctrl1.SetColumnWidth(6, 0)
		self.list_ctrl1.SetColumnWidth(7, 100)
		self.list_ctrl1.SetColumnWidth(8, 100)
	
		# insert details of each address
		
		self.midbox.Add(self.list_ctrl1, 0, wx.ALL|wx.CENTER, 10)

		self.box1.Add(self.topbox, 0, wx.ALL|wx.LEFT, 10)
		self.box1.Add(self.midbox, 0, wx.ALL|wx.CENTER, 10)

		self.SetSizer(self.box1)
		self.Layout()
		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.update, self.timer)
		self.timer.Start(1 * 500)
		
	def update(self,event):
	
		addylist = mwprocs.readaddys() #reads all addresses from wallet.dat
		self.one_addys = [x[0] for x in addylist]
		list_addys = []
		total_balance = 0
		# print("refresh")
		
		for a in self.one_addys:
			
			try:

				connections.send(s, "balanceget", 10)
				connections.send(s, a, 10)
				stats_account = connections.receive(s, 10)

				#total_balance = total_balance + float(stats_account[0])
				
				balance = '%.8f' % float(stats_account[0])
				credits = '%.8f' % float(stats_account[1])
				debits = '%.8f' % float(stats_account[2])
				rewards = '%.8f' % float(stats_account[4])
				fees = '%.8f' % float(stats_account[3])
				iscrypted = int(mwprocs.readcrypt(a)[0][0])
				ishd = int(mwprocs.readcrypt(a)[0][1])
				if iscrypted == 1:
					state = "Yes"
				elif iscrypted == 0:
					state = "No"
				else:
					state = ""
					
				if ishd == 1:
					hdtype = "HD Seed"
					total_balance = total_balance + float(stats_account[0])
				elif ishd == 2:
					hdtype = "Watch Only"
				else:
					hdtype = "Legacy"
					total_balance = total_balance + float(stats_account[0])
					
				if not view_all:
					if float(balance) > 0:
						this_addy = [a,float(balance),credits,debits,rewards,fees,state,hdtype]
						list_addys.append(this_addy)
				else:
					this_addy = [a,float(balance),credits,debits,rewards,fees,state,hdtype]
					list_addys.append(this_addy)
					
			except:
				balance = "0"
				credits = "0"
				debits = "0"
				rewards = "0"
				fees = "0"
				state = "No"
				hdtype = "None"				
				
				
				if view_all:
				
					this_addy = [a,float(balance),credits,debits,rewards,fees,state,hdtype]
					list_addys.append(this_addy)
			
		list_addys = sorted(list_addys, key=itemgetter(1), reverse=True) # sort by balance
		
		# print(list_addys)
		
		t_balance = '%.8f' % float(total_balance)
		self.b.SetLabel("\nTotal Confirmed Balance: {} BIS".format(t_balance))
		mt = len(list_addys)
		self.list_ctrl1.DeleteAllItems()
		
		for i in range(mt):
		
			if str(list_addys[i][7]) == "HD Seed":
				color_cell = "#e6ffe6" #green
			elif str(list_addys[i][7]) == "Legacy":
				color_cell = "#e6f7ff" #blue
			else:
				color_cell = "#ffe6e6" #red

			index = i
			self.list_ctrl1.InsertItem(index, index) #item
			self.list_ctrl1.SetItem(index, 1, str(list_addys[i][0])) # address
			self.list_ctrl1.SetItem(index, 2, str(list_addys[i][1])) # balance
			self.list_ctrl1.SetItem(index, 3, str(list_addys[i][2])) # received
			self.list_ctrl1.SetItem(index, 4, str(list_addys[i][3])) # spent
			self.list_ctrl1.SetItem(index, 5, str(list_addys[i][4])) # mined
			self.list_ctrl1.SetItem(index, 6, str(list_addys[i][5])) # fees
			self.list_ctrl1.SetItem(index, 7, str(list_addys[i][6])) # encrypted
			self.list_ctrl1.SetItem(index, 8, str(list_addys[i][7])) # wallet type
			self.list_ctrl1.SetItemBackgroundColour(item=index, col=color_cell)
			self.list_ctrl1.SetItemData(index,index)
			
		self.SetSizer(self.box1)
		self.Layout()
		self.timer.Start(30 * 1000)		
		
	def OnAbout(self, event):
		#pass
		for i in range(self.list_ctrl1.GetItemCount()):
			if self.list_ctrl1.IsSelected(i):
				l_event = i
		#l_event = event.GetIndex()
		m = []
		m.append(self.list_ctrl1.GetItem(l_event, 1).GetText())
		m.append(self.list_ctrl1.GetItem(l_event, 2).GetText())
		m.append(self.list_ctrl1.GetItem(l_event, 3).GetText())
		m.append(self.list_ctrl1.GetItem(l_event, 4).GetText())
		m.append(self.list_ctrl1.GetItem(l_event, 5).GetText())
		m.append(self.list_ctrl1.GetItem(l_event, 6).GetText())
		m.append(self.list_ctrl1.GetItem(l_event, 7).GetText())
		m.append(self.list_ctrl1.GetItem(l_event, 8).GetText())
		
		#l_item1 = self.list_ctrl1.GetItem(l_event, 1)
		#getaddress = l_item1.GetText()

		getaddress = "Address: {}\nBalance: {}\nReceived: {}\nSpent: {}\nMined: {}\nFees: {}\nEncrypted: {}\nType: {}".format(m[0],m[1],m[2],m[3],m[4],m[5],m[6],m[7])
		gettitle = "Further Information"

		msgbox = wx.MessageDialog(None,getaddress,gettitle,wx.ICON_INFORMATION)
		msgbox.ShowModal()		

		
	def ShowPopup(self, event):
		menu = wx.Menu()
		menu.Append(1, "Copy Address")
		menu.Append(2, "Get More Information")
		menu.Bind(wx.EVT_MENU, self.CopyItems, id=1)
		menu.Bind(wx.EVT_MENU, self.OnAbout, id=2)
		self.PopupMenu(menu)

	def CopyItems(self, event):
		selectedItems = []
		for i in range(self.list_ctrl1.GetItemCount()):
			if self.list_ctrl1.IsSelected(i):
				selectedItems.append(self.list_ctrl1.GetItemText(i,1))
				print(selectedItems)

		clipdata = wx.TextDataObject()
		clipdata.SetText("\n".join(selectedItems))
		wx.TheClipboard.Open()
		wx.TheClipboard.SetData(clipdata)
		wx.TheClipboard.Close()

		print("Items are on the clipboard")
		
	def OnEraseBackground(self, evt):
		"""
		Add a picture to the background
		"""
		# yanked from ColourDB.py
		dc = evt.GetDC()
		
		if not dc:
			dc = wx.ClientDC(self)
			rect = self.GetUpdateRegion().GetBox()
			dc.SetClippingRect(rect)
		dc.Clear()
		bmp = wx.Bitmap("Bismuth_bg.jpg")
		dc.DrawBitmap(bmp, 0, 0)
		dc.SetBackgroundMode(wx.TRANSPARENT)
		
#--------------------------------------------------------
		
class PageTwo(wx.Window):
	def __init__(self, parent):
		wx.Window.__init__(self, parent, -1, style = wx.NO_BORDER)

		self.SetBackgroundColour("#FFFFFF")
		
		self.DoAddys()
		#print(self.alladdys)
		
		self.myaddress = self.alladdys[0] # uses first address if none selected
		
		encrypted = int(mwprocs.readcrypt(self.myaddress)[0][0])
		
		if encrypted == 1:
			unlocked = 0
			self.my_state = "Encrypted"
			self.my_color = '#08750A'
		elif encrypted == 3:
			unlocked = 1
			self.my_state = "Watch Only"
			self.my_color = '#444995'	
		else:
			unlocked = 1
			self.my_state = "Not Encrypted"
			self.my_color = wx.RED		
		
		if not os.path.exists('png/{}_qr.png'.format(self.myaddress)):
			address_qr = pyqrcode.create(self.myaddress)
			address_qr.png('png/{}_qr.png'.format(self.myaddress))
		
		self.box1 = wx.BoxSizer(wx.VERTICAL)
		
		self.selectbox = wx.BoxSizer(wx.HORIZONTAL)
					
		self.cb = wx.StaticText(self, -1, "Select a Bismuth Address:")
		self.cb.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.cb.SetForegroundColour("#444995")
		self.cb.SetSize(self.cb.GetBestSize())
		self.selectbox.Add(self.cb, 0, wx.ALL|wx.CENTER, 5)
		
		self.l = wx.ComboBox(self, -1, size=(-1, -1), choices=self.alladdys, style=wx.CB_READONLY) # address list
		self.Bind(wx.EVT_COMBOBOX, self.OnSelect, self.l)
		self.l.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL))
		self.l.SetForegroundColour(wx.BLACK)
		self.l.SetBackgroundColour(wx.WHITE)
		self.l.SetSize(self.l.GetBestSize())
		self.selectbox.Add(self.l, 0, wx.ALL|wx.CENTER, 5)
		
		self.box1.Add(self.selectbox, 0, wx.ALL|wx.CENTER, 5)
		
		self.topbox1 = wx.BoxSizer(wx.HORIZONTAL) # logo and top text
	
		self.tbleft1 = wx.BoxSizer(wx.VERTICAL) # top text
		
		self.s = wx.StaticText(self, -1, "") # wallet encrypted?
		self.s.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL))
		self.s.SetForegroundColour(self.my_color)
		self.s.SetSize(self.s.GetBestSize())
		self.tbleft1.Add(self.s, 0, wx.ALL|wx.CENTER, 5)
	
		self.t = wx.StaticText(self, -1, "") # address
		self.t.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.t.SetForegroundColour("#444995")
		self.t.SetSize(self.t.GetBestSize())
		self.tbleft1.Add(self.t, 0, wx.ALL|wx.CENTER, 5)

		self.b = wx.StaticText(self, -1, "") # current balance
		self.b.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.b.SetForegroundColour("#444995")
		self.b.SetSize(self.b.GetBestSize())
		self.tbleft1.Add(self.b, 0, wx.ALL|wx.CENTER, 5)
		
		self.d = wx.StaticText(self, -1, "") # wallet summary
		self.d.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL))
		self.d.SetForegroundColour("#444995")
		self.d.SetSize(self.d.GetBestSize())
		self.tbleft1.Add(self.d, 0, wx.ALL|wx.CENTER, 5)
	
		self.topbox1.Add(self.tbleft1, 0, wx.ALL|wx.CENTER, 10)
				
		self.myimage = ticons.bismuthlogo.GetBitmap()
		self.image1 = wx.StaticBitmap(self, wx.ID_ANY, wx.Bitmap(self.myimage))
		self.topbox1.Add(self.image1, 0, wx.ALL|wx.RIGHT, 10)
		
		self.box1.Add(self.topbox1, 0, wx.ALL|wx.CENTER, 10)
		
		self.w_text4 = wx.StaticText(self, -1, "") # list title
		self.w_text4.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.w_text4.SetForegroundColour("#08750A")
		self.w_text4.SetSize(self.w_text4.GetBestSize())
		self.box1.Add(self.w_text4, 0, wx.ALL|wx.CENTER, 5)
		
		self.list_ctrl1 = wx.ListCtrl(self, size=(750,600),
						 style=wx.LC_REPORT
						 |wx.BORDER_SUNKEN
						 )

		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnAbout, self.list_ctrl1)
		self.list_ctrl1.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL))
		self.list_ctrl1.InsertColumn(0, 'Block', wx.LIST_FORMAT_LEFT)
		self.list_ctrl1.InsertColumn(1, 'Date', wx.LIST_FORMAT_LEFT)
		self.list_ctrl1.InsertColumn(2, 'From', wx.LIST_FORMAT_LEFT)
		self.list_ctrl1.InsertColumn(3, 'To', wx.LIST_FORMAT_LEFT)
		self.list_ctrl1.InsertColumn(4, 'Amount', wx.LIST_FORMAT_LEFT)
		self.list_ctrl1.InsertColumn(5, 'Reward', wx.LIST_FORMAT_LEFT)
		self.list_ctrl1.InsertColumn(6, 'txid', wx.LIST_FORMAT_LEFT)
		self.list_ctrl1.InsertColumn(7, 'block_hash', wx.LIST_FORMAT_LEFT)
		self.list_ctrl1.InsertColumn(8, 'fee', wx.LIST_FORMAT_LEFT)
		self.list_ctrl1.InsertColumn(9, 'openfield', wx.LIST_FORMAT_LEFT)
		
		self.list_ctrl1.SetColumnWidth(0, 0)
		self.list_ctrl1.SetColumnWidth(1, 125)
		self.list_ctrl1.SetColumnWidth(2, 200)
		self.list_ctrl1.SetColumnWidth(3, 200)
		self.list_ctrl1.SetColumnWidth(4, 100)
		self.list_ctrl1.SetColumnWidth(5, 100)
		self.list_ctrl1.SetColumnWidth(6, 0)
		self.list_ctrl1.SetColumnWidth(7, 0)
		self.list_ctrl1.SetColumnWidth(8, 0)
		self.list_ctrl1.SetColumnWidth(9, 0)
	
		self.box1.Add(self.list_ctrl1, 0, wx.ALL|wx.CENTER, 10)

		self.SetSizer(self.box1)
		self.Layout()
		self.l.SetValue(self.myaddress)
		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.update, self.timer)
		self.timer.Start(1 * 1000)
		
	def OnSelect(self, event):
		self.myaddress = self.l.GetValue()
		#myaddress = self.myaddress
		self.update(self)
		
	def OnAbout(self, event):
	
		self.timer.Stop()
		l_event = event.GetIndex()

		l_count = self.list_ctrl1.GetColumnCount()
		my_temp = []
		
		for z in range(l_count):
			my_temp.append(self.list_ctrl1.GetItem(l_event, z).GetText())
		
		#print(my_temp)
		gettitle = "Multiwallet | Transaction Details"

		if tgetvars(my_temp,gettitle):
			dlg = AboutBoxT()
			dlg.ShowModal()
			dlg.Destroy()
		
		self.timer.Start()
	
	def update(self, event):
		global latest

		self.timer.Stop()
		
		try:
			self.DoAddys()
			
			self.l.Clear()
			self.l.AppendItems(self.alladdys) 
			self.l.SetValue(self.myaddress)

			encrypted = int(mwprocs.readcrypt(self.myaddress)[0][0])
			
			if encrypted == 1:
				unlocked = 0
				self.my_state = "Encrypted"
				self.my_color = '#08750A'
			elif encrypted == 3:
				unlocked = 1
				self.my_state = "Watch Only"
				self.my_color = '#444995'	
			else:
				unlocked = 1
				self.my_state = "Not Encrypted"
				self.my_color = wx.RED		
			
			if not os.path.exists('png/{}_qr.png'.format(self.myaddress)):
				address_qr = pyqrcode.create(self.myaddress)
				address_qr.png('png/{}_qr.png'.format(self.myaddress))
			
		
			connections.send(s, "blocklast", 10)
			block_get = connections.receive(s, 10)
			#print(block_get)
			
			# check difficulty
			connections.send(s, "diffget", 10)
			diff = connections.receive(s, 10)
			# check difficulty
		
			try:
				latest = str(block_get[0])
				db_timestamp_last = block_get[1]
				time_now = str(time.time())
				last_block_ago = (float(time_now) - float(db_timestamp_last))/60
				last_ago = '%.2f' % last_block_ago
				last_diff = '%.2f' % float(diff[1])
			except:
				latest = 'error check connection'

			statusbar.SetStatusText('Block height: {} found {} mins. ago'.format(latest,last_ago), 0)
			statusbar.SetStatusText('Last difficulty: {}'.format(last_diff), 1)
			
			self.myimage = wx.Image('png/{}_qr.png'.format(self.myaddress), wx.BITMAP_TYPE_ANY)
			self.myimage = self.myimage.Scale(120,120)
			self.image1.SetBitmap(wx.Bitmap(self.myimage))
		
			try:

				connections.send(s, "balanceget", 10)
				connections.send(s, self.myaddress, 10)  # change address here to view other people's transactions
				stats_account = connections.receive(s, 10)

				self.balance = '%.8f' % float(stats_account[0])
				self.credits = '%.8f' % float(stats_account[1])
				self.debits = '%.8f' % float(stats_account[2])
				self.rewards = '%.8f' % float(stats_account[4])
				self.fees = '%.8f' % float(stats_account[3])
				#print('Balance: {}\nCredits: {}\nDebits: {}\nRewards: {}\nFees: {}'.format(self.balance,self.credits,self.debits,self.rewards,self.fees))
			except:
				self.balance = "0"
				self.credits = "0"
				self.debits = "0"
				self.rewards = "0"
				self.fees = "0"
							
			det1 = "Credits: {} | Debits: {} | Rewards: {} | Fees: {}".format(self.credits,self.debits,self.rewards,self.fees)
			
			connections.send(s, "addlistlim", 10)
			connections.send(s, self.myaddress, 10)
			connections.send(s, "20", 10)
			addlist = connections.receive(s, 10)
			t = addlist[:20]  # limit
			
			if len(t) == 0:
				mybacon = []
				#print("No bacon")
			else:
				mt = len(t)
				mybacon = [t[i] for i in range(mt)]
				#print(mybacon[0]['amount'])
			
			t = None
			
			self.s.SetLabel("Wallet Address ({})".format(self.my_state))
			self.t.SetLabel(self.myaddress)
			self.s.SetForegroundColour(self.my_color)
			self.b.SetLabel("Current Balance: {} BIS".format(self.balance))
			self.d.SetLabel(det1)

			self.list_ctrl1.DeleteAllItems()
			
			if not mybacon:
				self.w_text4.SetLabel("No transactions found for this address")
				self.w_text4.SetForegroundColour(wx.RED)
			else:
				self.w_text4.SetLabel("Latest Transactions")
				self.w_text4.SetForegroundColour("#08750A")
				for i in range(mt):
					if i % 2 == 0:
						color_cell = "#FFFFFF"
					else:
						color_cell = "#E8E8E8"
					index = i
					in_time = datetime.fromtimestamp(float(mybacon[i][1])).strftime('%Y-%m-%d %H:%M:%S')
					self.list_ctrl1.InsertItem(index, str(mybacon[i][0]))
					self.list_ctrl1.SetItem(index, 1, in_time) # mybacon[i]['timestamp'])
					self.list_ctrl1.SetItem(index, 2, mybacon[i][2]) # from
					self.list_ctrl1.SetItem(index, 3, mybacon[i][3]) # to
					self.list_ctrl1.SetItem(index, 4, str(mybacon[i][4])) # amount
					self.list_ctrl1.SetItem(index, 5, str(mybacon[i][9])) # reward
					self.list_ctrl1.SetItem(index, 6, str(mybacon[i][5][:56])) # txid
					self.list_ctrl1.SetItem(index, 7, str(mybacon[i][7])) # hash
					self.list_ctrl1.SetItem(index, 8, str(mybacon[i][8])) # fee
					self.list_ctrl1.SetItem(index, 9, str(mybacon[i][11][:1000])) # reward
					self.list_ctrl1.SetItemBackgroundColour(item=index, col=color_cell)
					self.list_ctrl1.SetItemData(index,index)

			self.SetSizer(self.box1)
			self.Layout()
			self.timer.Start(10 * 1000)
		except:
			self.timer.Start(10 * 1000)
		#print("Updated")
		
	def DoAddys(self):
		addylist = mwprocs.readaddys() #reads all addresses from wallet.dat
		#print(len(addylist))
		if view_all or len(addylist) == 1 :
			self.alladdys = sorted([a[0] for a in addylist])
		else:
			self.alladdys = sorted([a[0] for a in addylist if float(get_my_bal(a[0])[0]) > 0])
		#print(self.alladdys)

#---------------------------------------------------------------------------------------------------------------

class PageThree(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		
		self.DoAddys()
		
		self.myaddress = self.alladdys[0] # uses first address if none selected
		self.MyTickState = False
		
		l_text1 = wx.StaticText(self, -1, "Send Bismuth")
		l_text1.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
		l_text1.SetSize(l_text1.GetBestSize())
		
	
		vbox1 = wx.BoxSizer(wx.VERTICAL)
		rbox1 = wx.BoxSizer(wx.VERTICAL)
		rbox2 = wx.BoxSizer(wx.VERTICAL)
		rbox3 = wx.BoxSizer(wx.VERTICAL)
		rbox4 = wx.BoxSizer(wx.VERTICAL)
		rbox5 = wx.BoxSizer(wx.VERTICAL)
		
		l_text2 = wx.StaticText(self, -1, "Send from (select an address):")
		l_text2.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
		l_text2.SetSize(l_text2.GetBestSize())
		
		self.l = wx.ComboBox(self, -1, size=(-1, -1), choices=self.alladdys, style=wx.CB_READONLY) # address list
		self.Bind(wx.EVT_COMBOBOX, self.OnSelect, self.l)
		self.Bind(wx.EVT_COMBOBOX_DROPDOWN, self.OnDrop, self.l)
		self.l.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL))
		self.l.SetForegroundColour(wx.BLACK)
		self.l.SetBackgroundColour(wx.WHITE)
		self.l.SetSize(self.l.GetBestSize())

		rbox1.Add(l_text2, 0, wx.ALL|wx.LEFT, 2)
		rbox1.Add(self.l, 0, wx.ALL|wx.LEFT, 2)		
				
		self.l_text3 = wx.StaticText(self, -1, "Amount to send:")
		self.l_text3.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.l_text3.SetSize(self.l_text3.GetBestSize())
		
		self.lt1 = wx.TextCtrl(self, size=(250, -1), style=wx.TE_PROCESS_ENTER)
		self.lt1.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL))
		
		self.tb1 = wx.CheckBox(self, label = 'Send all?',pos = (10,10))
		self.Bind(wx.EVT_CHECKBOX,self.OnChecked,self.tb1) 
		self.tb1.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.tb1.SetSize(self.tb1.GetBestSize())
		
		rbox2.Add(self.l_text3, 0, wx.ALL|wx.LEFT, 2)
		rbox2.Add(self.lt1, 0, wx.ALL|wx.LEFT, 2)
		rbox2.Add(self.tb1, 0, wx.ALL|wx.LEFT, 2)

		l_text4 = wx.StaticText(self, -1, "Receiving address:")
		l_text4.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
		l_text4.SetSize(l_text4.GetBestSize())
		
		self.lt2 = wx.TextCtrl(self, size=(400, -1), style=wx.TE_PROCESS_ENTER)
		self.lt2.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL))
		
		rbox3.Add(l_text4, 0, wx.ALL|wx.LEFT, 2)
		rbox3.Add(self.lt2, 0, wx.ALL|wx.LEFT, 2)
	
		l_text5 = wx.StaticText(self, -1, "Enter openfield data (message):")
		l_text5.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
		l_text5.SetSize(l_text5.GetBestSize())
		
		self.lt3 = wx.TextCtrl(self, size=(350, 150), style=wx.TE_MULTILINE)
		self.lt3.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL))
		
		rbox4.Add(l_text5, 0, wx.ALL|wx.LEFT, 2)
		rbox4.Add(self.lt3, 0, wx.ALL|wx.LEFT, 2)

		self.l_text6 = wx.StaticText(self, -1, "")
		self.l_text6.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.l_text6.SetSize(self.l_text6.GetBestSize())
		
		rbox5.Add(self.l_text6, 0, wx.ALL|wx.CENTER, 2)
		
		self.buttonbox = wx.BoxSizer(wx.HORIZONTAL)
		
		self.l_submit = wx.Button(self, wx.ID_APPLY, "Send Bismuth")
		#self.l_submit.Bind(wx.EVT_BUTTON, self.OnSubmit)
		
		self.l_import = wx.Button(self, wx.ID_APPLY, "Import URL")
		#self.l_import.Bind(wx.EVT_BUTTON, self.OnImport)
		
		self.l_reset = wx.Button(self, wx.ID_APPLY, "Reset")
		self.l_reset.Bind(wx.EVT_BUTTON, self.reset_me)
		
		self.buttonbox.Add(self.l_submit, 0, wx.ALL|wx.LEFT, 2)
		self.buttonbox.Add(self.l_import, 0, wx.ALL|wx.LEFT, 2)
		self.buttonbox.Add(self.l_reset, 0, wx.ALL|wx.LEFT, 2)
		
		rbox5.Add(self.buttonbox, 0, wx.ALL|wx.LEFT, 2)
		
		vbox2 = wx.BoxSizer(wx.VERTICAL)
		
		self.l_text7 = wx.StaticText(self, -1, "")
		self.l_text7.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.l_text7.SetForegroundColour("#08750A")		
		self.l_text7.SetSize(self.l_text7.GetBestSize())
		
		self.l_text8 = wx.StaticText(self, -1, "")
		self.l_text8.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.l_text8.SetForegroundColour("#08750A")		
		self.l_text8.SetSize(self.l_text8.GetBestSize())
		
		self.l_text9 = wx.StaticText(self, -1, "")
		self.l_text9.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.l_text9.SetForegroundColour("#08750A")		
		self.l_text9.SetSize(self.l_text9.GetBestSize())
		
		vbox1.Add(rbox1, 0, wx.ALL|wx.RIGHT, 2)
		vbox1.Add(rbox2, 0, wx.ALL|wx.RIGHT, 2)
		vbox1.Add(rbox3, 0, wx.ALL|wx.RIGHT, 2)
		vbox1.Add(rbox4, 0, wx.ALL|wx.RIGHT, 2)
		vbox1.Add(rbox5, 0, wx.ALL|wx.RIGHT, 2)

		vbox2.Add(self.l_text7, 0, wx.ALL|wx.CENTER, 2)
		vbox2.Add(self.l_text8, 0, wx.ALL|wx.CENTER, 2)
		vbox2.Add(self.l_text9, 0, wx.ALL|wx.CENTER, 2)		

		box1 = wx.BoxSizer(wx.VERTICAL)
		
		box1.Add(l_text1, 0, wx.ALL|wx.CENTER, 2)
		box1.Add(l_text2, 0, wx.ALL|wx.CENTER, 2)
		box1.Add(vbox1, 0, wx.ALL|wx.CENTER, 2)
		box1.Add(vbox2, 0, wx.ALL|wx.CENTER, 2)

		self.SetSizer(box1)

	def OnSubmit(self, event):
	
		keep_input = 0
		openfield_input = self.lt3.GetValue()
		fee = '%.8f' % float(float(0.01) + (float(len(openfield_input)) / 100000) + int(keep_input))
		address = self.myaddress
		if self.MyTickState:
			amdo = '%.8f' % (Decimal(self.balance) - Decimal(fee))
			print(amdo)
		else:
			amdo = self.lt1.GetValue()
		addo = self.lt2.GetValue()
		openfield_input = self.lt3.GetValue()
	
		try:		
			amdo = Decimal(amdo)
		except:
			self.l_text7.SetForegroundColour(wx.RED)
			self.l_text7.SetLabel("Invalid amount")
			self.Layout()
			return
			
		if float(amdo) < 0:
			self.l_text7.SetForegroundColour(wx.RED)
			self.l_text7.SetLabel("Negative amounts not allowed")
			self.Layout()
			return
			
		#fee = '%.8f' % float(float(0.01) + (float(len(openfield_input)) / 100000) + int(keep_input))
		total_amount = amdo + Decimal(fee)
			
		if amdo + Decimal(fee) > Decimal(self.balance):
			self.l_text7.SetForegroundColour(wx.RED)
			self.l_text7.SetLabel("Not enough funds\n{} BIS fees needed?".format(str(fee)))
			self.Layout()
			return
			
		# Validate address
		if not re.match('[abcdef0123456789]{56}', addo):
			self.l_text8.SetForegroundColour(wx.RED)
			self.l_text8.SetLabel("Bad address format <{}>".format(addo))
			self.Layout()
			return
			
		if len(str(addo)) != 56:
			self.l_text8.SetForegroundColour(wx.RED)
			self.l_text8.SetLabel("Wrong address length")
			self.Layout()
			return
		elif not addo.isalnum():
			self.l_text8.SetForegroundColour(wx.RED)
			self.l_text8.SetLabel("Invalid characters in address")
			self.Layout()
			return
			
		#cryptopia check
		if addo == "edf2d63cdf0b6275ead22c9e6d66aa8ea31dc0ccb367fad2e7c08a25" and len(openfield_input) not in [16,20]:
			self.l_text9.SetForegroundColour(wx.RED)
			self.l_text9.SetLabel("Identification message is missing for Cryptopia, please include it")
			self.Layout()
			return
		# cryptopia check
				
		print(amdo)
		print(addo)
		print(openfield_input)
		self.l_text7.SetLabel("")
		self.l_text8.SetLabel("")
		self.l_text9.SetLabel("")
		
		yesNobox = wx.MessageDialog(None,"Are you sure you wish to send?",'Confirmation Needed',wx.YES_NO)
		yesNoAnswer = yesNobox.ShowModal()
		
		if yesNoAnswer == wx.ID_YES:
			print("Yes")
			self.l_submit.Unbind(wx.EVT_BUTTON)
			self.lt1.SetValue("")
			self.lt2.SetValue("")
			self.lt3.SetValue("")
			s_result = send_bis(address,amdo,addo,openfield_input,keep_input)
			mydone = s_result[0]
			if mydone:
				self.l_text7.SetForegroundColour("#08750A")
				self.l_text7.SetLabel("Transaction complete")
				self.l_text8.SetForegroundColour("#08750A")
				self.l_text8.SetLabel(str(s_result[1][2]))
				app_log.warning(str(s_result[1]))
				self.l_text9.SetForegroundColour("#08750A")
				self.l_text9.SetLabel(str(s_result[2]))
				self.Layout()
			else:
				self.l_text7.SetForegroundColour(wx.RED)
				self.l_text7.SetLabel("Transaction failed")
				self.l_text8.SetForegroundColour(wx.RED)
				self.l_text8.SetLabel(str(s_result[1]))
				app_log.warning(str(s_result[1]))
				self.l_text9.SetForegroundColour(wx.RED)
				self.l_text9.SetLabel(str(s_result[2]))
				self.Layout()
			
		elif yesNoAnswer == wx.ID_NO:
			print("No")
			self.lt1.SetValue("")
			self.lt2.SetValue("")
			self.lt3.SetValue("")
			self.l_text7.SetForegroundColour(wx.RED)
			self.l_text7.SetLabel("Transaction cancelled")
			self.Layout()
			
		else:
			return
		
	def OnSelect(self, event):
		self.myaddress = self.l.GetValue()
		#(key, private_key_readable, public_key_readable, public_key_hashed, address, my_pkc) = mwprocs.read(self.myaddress)
		self.l_submit.Bind(wx.EVT_BUTTON, self.OnSubmit)
		self.l_import.Bind(wx.EVT_BUTTON, self.OnImport)
		self.l_text7.SetLabel("")
		self.l_text8.SetLabel("")
		self.l_text9.SetLabel("")
		self.DoAddys()
		self.l.Clear()
		self.l.AppendItems(self.alladdys)
		self.l.SetValue(self.myaddress)
	
		try:

			connections.send(s, "balanceget", 10)
			connections.send(s, self.myaddress, 10)  # change address here to view other people's transactions
			stats_account = connections.receive(s, 10)

			self.balance = '%.8f' % Decimal(stats_account[0])
			#self.credits = '%.8f' % float(stats_account[1])
			#self.debits = '%.8f' % float(stats_account[2])
			#self.rewards = '%.8f' % float(stats_account[4])
			#self.fees = '%.8f' % float(stats_account[3])
			#print('Balance: {}\nCredits: {}\nDebits: {}\nRewards: {}\nFees: {}'.format(self.balance,self.credits,self.debits,self.rewards,self.fees))
		except:
			self.balance = "0"
			#self.credits = "0"
			#self.debits = "0"
			#self.rewards = "0"
			#self.fees = "0"

		self.l_text3.SetLabel("Amount to send ({} BIS available)".format(self.balance))
		
	def OnDrop(self, event):
		self.DoAddys()
		self.l.SetItems(self.alladdys)
		self.l.SetValue(self.myaddress)
			
	def cleantxt(self):
		self.l_text7.SetLabel("")
		self.l_text7.SetToolTip(wx.ToolTip(""))
		self.l_text8.SetLabel("")
		self.l_text8.SetToolTip(wx.ToolTip(""))

	def DoAddys(self):
		addylist = mwprocs.readaddys() #reads all addresses from wallet.dat
		self.thisalladdys = [a[0] for a in addylist]
		self.alladdys = []

		for z in self.thisalladdys:
		
			try:
				connections.send(s, "balanceget", 10)
			except:
				s.connect((mynode, int(port)))
				connections.send(s, "balanceget", 10)
				
			connections.send(s, z, 10)
			sa = connections.receive(s, 10)

			sabalance = '%.8f' % Decimal(sa[0])
			if Decimal(sabalance) > 0:
				encrypted = int(mwprocs.readcrypt(z)[0][0])
				if encrypted != 3:				
					self.alladdys.append(z)
		#print(self.alladdys)

	def OnImport(self, event):
	
		frame = wx.Frame(None, -1, 'Setup')
		self.myurl = ask(frame, message = 'Paste your url here (bis://..)', title = 'Bismuth Multiwallet', default_value = '')
		#print(self.myurl)
		frame.Destroy()
		if self.myurl == "cancel":
		
			self.l_text6.SetForegroundColour(wx.RED)
			self.l_text6.SetLabel("Import Cancelled")
			self.Layout()
			return
			
		else:
			im_url = bisurl.read_url(app_log, self.myurl)
		
			if im_url[0] == "pay":
				self.l_text6.SetForegroundColour('#08750A')
				self.l_text6.SetLabel("Import Successful")
				self.lt1.SetValue(im_url[2])
				self.lt2.SetValue(im_url[1])
				self.lt3.SetValue(im_url[3])
				self.Layout()
				return
			else:
				self.l_text6.SetForegroundColour(wx.RED)
				self.l_text6.SetLabel("Import Error")
				self.Layout()
				return	
			#print(im_url)
			
	def OnChecked(self,event):
		cb = event.GetEventObject()
		
		self.MyTickState = cb.GetValue()
		
		if self.MyTickState:
			self.lt1.Enable(False)
		else:
			self.lt1.Enable(True)
		#print(self.MyTickState)
		
	def reset_me(self,event):
		self.l_text6.SetForegroundColour(wx.BLACK)
		self.l_text6.SetLabel("")
		self.l_text7.SetForegroundColour(wx.BLACK)
		self.l_text7.SetLabel("")
		self.l_text8.SetForegroundColour(wx.BLACK)
		self.l_text8.SetLabel("")
		self.l_text9.SetForegroundColour(wx.BLACK)
		self.l_text9.SetLabel("")
		self.lt1.SetValue("")
		self.lt1.Enable(True)
		self.tb1.SetValue(False)
		self.lt2.SetValue("")
		self.lt3.SetValue("")
		#self.Layout()

#--------------------------------------------------------------------------------

class PageFour(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)

		self.MyTickState = False
		
		self.SetBackgroundColour("#FFFFFF")
		
		self.DoAddys()
	
		self.myaddress = self.alladdys[0] # uses first address if none selected

		#if not os.path.exists('{}_qr.png'.format(self.myaddress)):
			#address_qr = pyqrcode.create(self.myaddress)
			#address_qr.png('{}_qr.png'.format(self.myaddress))
		
		self.box1 = wx.BoxSizer(wx.VERTICAL)
		
		self.t_text1 = wx.StaticText(self, -1, "Receive Bismuth")
		self.t_text1.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.t_text1.SetSize(self.t_text1.GetBestSize())
		self.box1.Add(self.t_text1, 0, wx.ALL|wx.CENTER, 5)
		
		self.w_text4 = wx.StaticText(self, -1, "Fill in the form and click Request Payment") # list title
		self.w_text4.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.w_text4.SetSize(self.w_text4.GetBestSize())
		self.box1.Add(self.w_text4, 0, wx.ALL|wx.CENTER, 5)
		
		self.newbox = wx.BoxSizer(wx.HORIZONTAL)

		self.tb1 = wx.CheckBox(self, label = 'Generate New Address?',pos = (10,10))
		self.Bind(wx.EVT_CHECKBOX,self.onChecked,self.tb1) 
		self.tb1.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.tb1.SetSize(self.tb1.GetBestSize())
		self.newbox.Add(self.tb1, 0, wx.ALL|wx.CENTER, 5)
		
		self.box1.Add(self.newbox, 0, wx.ALL|wx.CENTER, 5)
		
		self.c_text1 = wx.StaticText(self, -1, "OR")
		self.c_text1.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.c_text1.SetSize(self.c_text1.GetBestSize())
		self.box1.Add(self.c_text1, 0, wx.ALL|wx.CENTER, 5)
		
		self.selectbox = wx.BoxSizer(wx.HORIZONTAL)
					
		self.cb = wx.StaticText(self, -1, "Select a Bismuth Address:")
		self.cb.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.cb.SetSize(self.cb.GetBestSize())
		self.selectbox.Add(self.cb, 0, wx.ALL|wx.CENTER, 5)
		
		self.l = wx.ComboBox(self, -1, size=(-1, -1), choices=self.alladdys, style=wx.CB_READONLY) # address list
		self.Bind(wx.EVT_COMBOBOX, self.OnSelect, self.l)
		self.Bind(wx.EVT_COMBOBOX_DROPDOWN, self.OnDrop, self.l)
		self.l.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL))
		self.l.SetForegroundColour(wx.BLACK)
		self.l.SetBackgroundColour(wx.WHITE)
		self.l.SetSize(self.l.GetBestSize())
		self.selectbox.Add(self.l, 0, wx.ALL|wx.CENTER, 5)
		
		self.box1.Add(self.selectbox, 0, wx.ALL|wx.CENTER, 5)
		
		self.l_text1 = wx.StaticText(self, -1, "Amount (BIS):") 
		self.l_text1.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.l_text1.SetSize(self.l_text1.GetBestSize())
		
		#self.lt1 = wx.TextCtrl(self, size=(250, -1), style=wx.TE_PROCESS_ENTER)
		self.lt1 = wx.lib.masked.NumCtrl(self, pos = (-1,-1), fractionWidth = 8) # for 8 decimal places.
		self.lt1.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL))
		
		self.box1.Add(self.l_text1, 0, wx.ALL|wx.CENTER, 5)
		self.box1.Add(self.lt1, 0, wx.ALL|wx.CENTER, 5)
		
		self.l_text2 = wx.StaticText(self, -1, "Enter openfield data (message):")
		self.l_text2.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.l_text2.SetSize(self.l_text2.GetBestSize())
		
		self.lt2 = wx.TextCtrl(self, size=(400, 75), style=wx.TE_MULTILINE)
		self.lt2.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL))
		
		self.box1.Add(self.l_text2, 0, wx.ALL|wx.CENTER, 5)
		self.box1.Add(self.lt2, 0, wx.ALL|wx.CENTER, 5)
		
		self.buttonbox = wx.BoxSizer(wx.HORIZONTAL)
	
		self.l_submit = wx.Button(self, wx.ID_APPLY, "Request Payment")
		self.l_submit.Bind(wx.EVT_BUTTON, self.OnSubmit)
		
		self.l_reset = wx.Button(self, wx.ID_APPLY, "Reset")
		self.l_reset.Bind(wx.EVT_BUTTON, self.reset_me)
		
		self.buttonbox.Add(self.l_submit, 0, wx.ALL|wx.CENTER, 5)
		self.buttonbox.Add(self.l_reset, 0, wx.ALL|wx.CENTER, 5)
		self.box1.Add(self.buttonbox, 0, wx.ALL|wx.CENTER, 5)
		
		self.l_text3 = wx.StaticText(self, -1, "")
		self.l_text3.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.l_text3.SetSize(self.l_text3.GetBestSize())
		
		self.box1.Add(self.l_text3, 0, wx.ALL|wx.CENTER, 5)
	
		size_h_w = 160
		self.myimage = wx.Bitmap.FromRGBA(size_h_w, size_h_w, green=255, alpha=0)
		self.image1 = wx.StaticBitmap(self, wx.ID_ANY, wx.Bitmap(self.myimage))
		self.box1.Add(self.image1, 0, wx.ALL|wx.CENTER, 5)
		
		self.lt3 = wx.TextCtrl(self, -1, "", size=(650,-1), style=wx.BORDER_NONE|wx.TE_READONLY|wx.TE_MULTILINE)
		self.lt3.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.lt3.SetBackgroundColour("#FFFFFF")
		self.lt3.SetForegroundColour(wx.BLACK)
		
		self.box1.Add(self.lt3, 0, wx.ALL|wx.CENTER, 5)
	
		self.SetSizer(self.box1)
		self.Layout()
		self.l.SetValue(self.myaddress)
				
	def onChecked(self,event):
		cb = event.GetEventObject()
		self.reset_me(event)
		#print(cb.GetLabel(),' is clicked',cb.GetValue())
		
		self.MyTickState = cb.GetValue()
		
		if self.MyTickState:
			self.c_text1.SetLabel("A new address will be created")
			self.cb.SetLabel("")
			self.l.Enable(False)
			self.Layout()
			#print("Ticked")
		else:
			self.c_text1.SetLabel("OR")
			self.cb.SetLabel("Select a Bismuth Address:")
			self.l.Enable(True)
			self.Layout()
			#print("Unticked")
	
	def OnSelect(self, event):
		self.myaddress = self.l.GetValue()
		#myaddress = self.myaddress
		self.reset_me(event)
		
	def OnDrop(self, event):
		self.DoAddys()
		self.l.SetItems(self.alladdys)
		self.l.SetValue(self.myaddress)
	
	def OnSubmit(self,event):
	
		this_fail = True
		
		if self.MyTickState:

			x = mwprocs.generate()
			
			if x[0]:
				print("New address generated and saved")
				print(x[1])
				self.myaddress = str(x[1])
				self.DoAddys()
				self.l.Clear()
				self.l.AppendItems(self.alladdys)
				self.Layout()
				self.l.SetValue(self.myaddress)
				#self.update(self)
			else:
				this_fail = False
				print("New address creation failed")
				
		else:
			self.myaddress = self.l.GetValue()
			
			
		myamount = str(self.lt1.GetValue())
		mymessage = str(self.lt2.GetValue())
		
		receive_str = bisurl.create_url(app_log, "pay", self.myaddress, myamount, mymessage)
		
		if not this_fail:		
			self.l_text3.SetForegroundColour(wx.RED)
			self.l_text3.SetLabel("New address creation failed")
			self.lt3.SetForegroundColour(wx.RED)
			self.lt3.SetValue("Error")
		else:
			self.l_text3.SetForegroundColour(wx.BLACK)
			self.l_text3.SetLabel("Copy the URL string below or scan the QR code")
			self.lt3.SetValue(receive_str)
			receive_qr = pyqrcode.create(receive_str)
			receive_qr_png = receive_qr.png('this_qr.png')
			self.myimage = wx.Image('this_qr.png', wx.BITMAP_TYPE_ANY)
			self.myimage = self.myimage.Scale(160,160)
			self.image1.SetBitmap(wx.Bitmap(self.myimage))
			
		self.Layout()
		#print(receive_str)
		
	def DoAddys(self):
		addylist = mwprocs.readaddys() #reads all addresses from wallet.dat
		self.alladdys = [a[0] for a in addylist if int(mwprocs.readcrypt(a[0])[0][0]) != 3]
		#print(self.alladdys)
		
	def reset_me(self,event):
		self.l_text3.SetForegroundColour(wx.BLACK)
		self.l_text3.SetLabel("")
		self.lt1.SetValue(0)
		self.lt2.SetValue("")
		self.lt3.SetValue("")
		size_h_w = 160
		self.myimage = wx.Bitmap.FromRGBA(size_h_w, size_h_w, green=255, alpha=0)
		#self.image1 = wx.StaticBitmap(self, wx.ID_ANY, wx.Bitmap(self.myimage))
		self.image1.SetBitmap(self.myimage)
		self.Layout()
		
#-----------------------------------------------------------------------

class MainFrame(wx.Frame):
	def __init__(self):
		wx.Frame.__init__(self, None, title=mytitle, pos=(50,50), size=(950,750))
	
		loc = ticons.bismuthicon.GetIcon()
		self.SetIcon(loc)

		menubar = wx.MenuBar()
		
		# File menu

		m_file = wx.Menu()
		
		m_exit = m_file.Append(wx.ID_EXIT, '&Quit', 'Quit application')
		# Add more action menu items here
		#m_file.Append(2, '&Edit Config', 'Edit the config.dat settings')
		
		menubar.Append(m_file, '&File')
		
		# Actions menu
		
		m_act = wx.Menu()
		
		m_add = wx.Menu()
		
		m_add.Append(201, '&Encrypt Address', 'Encrypt an address')
		m_add.Append(202, '&Decrypt Address', 'Decrypt an address')
		m_add.Append(203, '&Generate Address', 'Generate an address')
		m_add.Append(204, '&Delete Address', 'Delete an address')
		m_act.Append(3, 'A&ddresses', m_add)
		
		m_seed = wx.Menu()
		m_seed.Append(205, '&Import Address Seed', 'Import an address from seed')
		m_seed.Append(206, '&View Address Seed', 'View address seed')
		m_seed.Append(207, '&Export Seeds to File', 'Export address seeds to CSV')
		m_seed.Append(208, 'I&mport Seeds from File', 'Import address seeds from CSV')
		m_act.Append(4, '&Seeds', m_seed)
		
		m_imp = wx.Menu()
		m_imp.Append(209, 'Import &Wallet File', 'Import address from wallet.der')
		m_imp.Append(210, 'Import &Privkey File', 'Import address from privkey.der')
		m_imp.Append(211, 'Add &Watch Address', 'Watch a BIS address')		
		m_act.Append(5, '&Legacy Import', m_imp)
			
		menubar.Append(m_act, '&Actions')
		
		# Settings menu
		
		self.m_set = wx.Menu()
		
		self.m_set.AppendCheckItem(302, '&View Zero Balances', 'View addresses with zero balance')
		self.m_set.Check(302,False)
				
		menubar.Append(self.m_set, '&Settings')
		
		# Help menu

		help = wx.Menu()
		
		help.Append(101, '&Transactions', 'Transaction Information')
		help.Append(102, '&About', 'About this Program')
		
		menubar.Append(help, '&Help')

		self.SetMenuBar(menubar)
		
		self.Bind(wx.EVT_MENU, self.OnAbout, id=101)
		self.Bind(wx.EVT_MENU, self.OnAbout, id=102)
		self.Bind(wx.EVT_MENU, self.OnQuit, m_exit)
		self.Bind(wx.EVT_MENU, self.OnEncrypt, id=201)
		self.Bind(wx.EVT_MENU, self.OnDecrypt, id=202)
		self.Bind(wx.EVT_MENU, self.OnGenerate, id=203)
		self.Bind(wx.EVT_MENU, self.OnDelete, id=204)
		self.Bind(wx.EVT_MENU, self.ImpSeed, id=205)
		self.Bind(wx.EVT_MENU, self.ViewSeed, id=206)
		self.Bind(wx.EVT_MENU, self.ExpSeeds, id=207)
		self.Bind(wx.EVT_MENU, self.imp_s_file, id=208)
		self.Bind(wx.EVT_MENU, self.ImpDer, id=209)
		self.Bind(wx.EVT_MENU, self.ImpPriv, id=210)
		self.Bind(wx.EVT_MENU, self.OnWatch, id=211)
		self.Bind(wx.EVT_MENU, self.ViewZero, id=302)
						
		global statusbar
		statusbar = self.CreateStatusBar()
		statusbar.SetFieldsCount(3)
		statusbar.SetStatusWidths([-1, -1, -1])
		statusbar.SetStatusText('', 0)
		statusbar.SetStatusText('', 1)
		
		if "testnet" in version:
			vxtra = " TESTNET"
		else:
			vxtra = ""
		
		if mynode == "127.0.0.1":
			statusbar.SetStatusText('Local Node running version: {}{}'.format(str(myversion),vxtra), 2)
		else:
			statusbar.SetStatusText('Node at {} running version: {}{}'.format(mynode,str(myversion),vxtra), 2)
		
		# Here we create a panel and a notebook on the panel
		p = wx.Panel(self)
		self.nb = wx.Notebook(p)
		
		# create the page windows as children of the notebook
		page1 = PageOne(self.nb)
		page2 = PageTwo(self.nb)
		page3 = PageThree(self.nb)
		page4 = PageFour(self.nb)
				
		# add the pages to the notebook with the label to show on the tab
		self.nb.AddPage(page1, "Overview")
		self.nb.AddPage(page2, "Transactions")
		self.nb.AddPage(page3, "Send")
		self.nb.AddPage(page4, "Receive")

		# finally, put the notebook in a sizer for the panel to manage
		# the layout
		sizer = wx.BoxSizer()
		sizer.Add(self.nb, 1, wx.EXPAND)
		self.CentreOnParent(wx.BOTH)
		p.SetSizer(sizer)

		statusbar.Bind(EVT_UPDATE_STATUSBAR, self.OnStatus)
		statusbar.Bind(wx.EVT_LEFT_DOWN, self.OnClick)

	def OnAbout(self, event):
		global thistitle
		global thisid
		thisid = event.Id
		
		if thisid == 101:
			thistitle = "Transactions Help"
			msgbox = wx.MessageDialog(None,w_txt,thistitle,wx.ICON_INFORMATION)
			msgbox.ShowModal()

		elif thisid == 102:
			thistitle = "About Bismuth Multiwallet"
			msgbox = wx.MessageDialog(None,a_txt,thistitle,wx.ICON_INFORMATION)
			msgbox.ShowModal()

	def updateStatus(self, msg):
		mystatus = msg
		statusbar.SetStatusText(mystatus, 2)

	def OnStatus(self, evt):
		statusbar.SetStatusText(evt.msg, evt.st_id)		


	def OnQuit(self, event):
		self.Close()
		
	def OnClick(self, event):
		pass
		
	def OnEncrypt(self, event):

		choices = list_cryptstate(1)
		#print(choices)
		dlg = wx.SingleChoiceDialog(
				self, "Select address to encrypt", 'Encrypt an address',
				choices, 
				wx.CHOICEDLG_STYLE
				)

		if dlg.ShowModal() == wx.ID_OK:
			addy_sel = dlg.GetStringSelection()

			dlg.Destroy()
		
			if mwprocs.enc_key(addy_sel):
				msgbox = wx.MessageDialog(None,"Address Encrypted","Address Encryption",wx.ICON_INFORMATION)
				msgbox.ShowModal()
			else:
				msgbox = wx.MessageDialog(None,"Encryption failed","Address Encryption",wx.ICON_ERROR)
				msgbox.ShowModal()
		else:
			dlg.Destroy()
			msgbox = wx.MessageDialog(None,"Nothing selected !","Address Encryption",wx.ICON_INFORMATION)
			msgbox.ShowModal()
		
		msgbox.Destroy()
			
	def OnDecrypt(self, event):
		choices = list_cryptstate(0)
		#print(choices)
		dlg = wx.SingleChoiceDialog(
				self, "Select address to decrypt", 'Decrypt an address',
				choices, 
				wx.CHOICEDLG_STYLE
				)

		if dlg.ShowModal() == wx.ID_OK:
			addy_sel = dlg.GetStringSelection()
			busyDlg = wx.BusyInfo("Busy decrypting.......")

			dlg.Destroy()
			
			if mwprocs.dec_all(addy_sel):
				busyDlg = None
				msgbox = wx.MessageDialog(None,"Address Decrypted","Address Decryption",wx.ICON_INFORMATION)
				msgbox.ShowModal()
			else:
				busyDlg = None
				msgbox = wx.MessageDialog(None,"Decryption failed","Address Decryption",wx.ICON_ERROR)
				msgbox.ShowModal()
		else:
			dlg.Destroy()
			msgbox = wx.MessageDialog(None,"Nothing selected !","Address Decryption",wx.ICON_INFORMATION)
			msgbox.ShowModal()
		
		msgbox.Destroy()
			
	def OnGenerate(self,event):
		
		x = mwprocs.generate()
		
		if x[0]:
			#print("New address generated and saved")
			#print(x[1])
			msgbox = wx.TextEntryDialog(None,"Seed for {}".format(x[1]),"New address generated","{}".format(x[2]),style=wx.TE_BESTWRAP|wx.TE_MULTILINE)
			msgbox.ShowModal()
			#print(x)
		else:
			msgbox = wx.MessageDialog(None,"Failed","Address Generation",wx.ICON_ERROR)
			msgbox.ShowModal()
			
		msgbox.Destroy()

	def OnDelete(self,event):
		choices = list_cryptstate(2)
		#print(choices)
		dlg = wx.SingleChoiceDialog(
				self, "Select address to delete", 'Delete an address',
				choices, 
				wx.CHOICEDLG_STYLE
				)

		if dlg.ShowModal() == wx.ID_OK:
			addy_sel = dlg.GetStringSelection()
			
			try:
				connections.send(s, "balanceget", 10)
				connections.send(s, addy_sel, 10)
				sa = connections.receive(s, 10)
			except:
				sa = [0]
			
			#print(sa)

			sabalance = '%.8f' % float(sa[0])
			#sabalance = 0.01
			
			if float(sabalance) > 0:
				msgsure = wx.MessageDialog(None, "WALLET NOT EMPTY ARE YOU SURE?", "Address Deletion", wx.YES_NO | wx.ICON_WARNING)
				result = msgsure.ShowModal() == wx.ID_YES
				msgsure.Destroy()
			else:
				result = True
			
			if result:
				if mwprocs.delete_add(addy_sel):
					msgbox = wx.MessageDialog(None,"Address Deleted","Address Deletion",wx.ICON_INFORMATION)
					msgbox.ShowModal()
				else:
					msgbox = wx.MessageDialog(None,"Deletion Failed","Address Deletion",wx.ICON_ERROR)
					msgbox.ShowModal()
			else:
				msgbox = wx.MessageDialog(None,"Deletion Cancelled","Address Deletion",wx.ICON_ERROR)
				msgbox.ShowModal()
		
		else:
			msgbox = wx.MessageDialog(None,"Nothing selected !","Address Deletion",wx.ICON_INFORMATION)
			msgbox.ShowModal()
			addy_sel = "Nothing"
		
		dlg.Destroy()
		msgbox.Destroy()
		
	def proc_seed(self, myseed, address):
	
		dlgp = wx.TextEntryDialog(None, 'Address: {}\n\n{}\n\nIf you typed a password when the seed was created paste it below and click OK\n\nClick ok or cancel if none'.format(address,myseed),'Seed Import', '')
		
		if dlgp.ShowModal() == wx.ID_OK:
			mypass = str(dlgp.GetValue())
		else:
			mypass = ""
			
		dlgp.Destroy()
		
		x = mwprocs.imp_seed(myseed,mypass)
		
		if x[0]:
			msgbox = wx.MessageDialog(None,"Seed Import Successful","Seed Import",wx.ICON_INFORMATION)
			msgbox.ShowModal()
			return True
		else:
			msgbox = wx.MessageDialog(None,"Failed","Seed Import",wx.ICON_ERROR)
			msgbox.ShowModal()
			return False
		
		
	def ImpSeed(self,event):
	
		dlgs = wx.TextEntryDialog(None, 'Paste or type your 24 word seed here','Seed Import', '')
		
		if dlgs.ShowModal() == wx.ID_OK:
			myseed = str(dlgs.GetValue())
			#print(myseed)
			
			dlgs.Destroy()
			
			#myseed = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
			
			dlgp = wx.TextEntryDialog(None, '1.Paste or type your seed password here\n2. Click ok or cancel if none','Seed Import', '')
			
			if dlgp.ShowModal() == wx.ID_OK:
				mypass = str(dlgp.GetValue())
			else:
				mypass = ""
				
			dlgp.Destroy()
			
			x = mwprocs.imp_seed(myseed,mypass)
			
			if x[0]:
				msgbox = wx.MessageDialog(None,"Seed Import Successful","Seed Import",wx.ICON_INFORMATION)
				msgbox.ShowModal()
			else:
				msgbox = wx.MessageDialog(None,"Failed","Seed Import",wx.ICON_ERROR)
				msgbox.ShowModal()
				
		else:
			msgbox = wx.MessageDialog(None,"Nothing done !","Seed Import",wx.ICON_INFORMATION)
			msgbox.ShowModal()
		
		msgbox.Destroy()
		
	def ViewSeed(self,event):
	
		choices = list_cryptstate(2)
		#print(choices)
		dlg = wx.SingleChoiceDialog(
				self, "Select an address to view it's seed", 'View Address Seed',
				choices, 
				wx.CHOICEDLG_STYLE
				)

		if dlg.ShowModal() == wx.ID_OK:
			addy_sel = dlg.GetStringSelection()
			
			#busyDlg = wx.BusyInfo("Getting address seed.......")
			x = mwprocs.read(addy_sel)
			#busyDlg = None

			msgbox = wx.TextEntryDialog(None,"Seed for {}".format(x[4]),"View Address Seed","{}".format(x[6]),style=wx.TE_BESTWRAP|wx.TE_MULTILINE)
			msgbox.ShowModal()		
			
		else:
			msgbox = wx.MessageDialog(None,"Nothing done !","View Address Seed",wx.ICON_INFORMATION)
			msgbox.ShowModal()			
			
		x = None
		msgbox.Destroy()
		
	def ExpSeeds(self,event):
	
		msgbox = wx.MessageDialog(None,"Please note only addresses with seeds will be saved","Export Seeds",wx.ICON_INFORMATION)
		msgbox.ShowModal()

		s_exp = mwprocs.read_exp()
		
		print(s_exp)
		
	def ImpDer(self,event):
	
		dlgd = wx.FileDialog(None, "Select", "", "","Wallet files (*.der)|*.der")
		
		if dlgd.ShowModal() == wx.ID_OK:
			result = dlgd.GetPath()
		else:
			result = ""
		dlgd.Destroy()
		
		if result == "":
			msgbox = wx.MessageDialog(None,"Nothing done !","Import Wallet.der",wx.ICON_INFORMATION)
			msgbox.ShowModal()
			msgbox.Destroy()
		else:
			with open (result, 'r') as wallet_file:
				wallet_dict = json.load (wallet_file)

			private_key_readable = wallet_dict['Private Key']
			public_key_readable = wallet_dict['Public Key']
			address = wallet_dict['Address']

			try:  # unencrypted
				key = RSA.importKey(private_key_readable)
				crypt = "0"
			except:  # encrypted
				crypt = "1"
				
			new_seed = "traditional key no seed for this address"
	
			try:
				wlist = sqlite3.connect('wallet.dat')
				wlist.text_factory = str
				w = wlist.cursor()
				w.execute("INSERT INTO wallet VALUES (?,?,?,?,?,?,?)", (str(address),str(private_key_readable),str(public_key_readable),crypt,'',new_seed,'0'))
				wlist.commit()
				wlist.close()
			
				app_log.info('Inserted imported address into wallet.dat')
				msgbox = wx.MessageDialog(None,"Wallet Import Successful","Import Wallet.der",wx.ICON_INFORMATION)
				msgbox.ShowModal()
				msgbox.Destroy()
				
			except:
				app_log.warning('Failed to insert imported address into wallet.dat')
				
	def ImpPriv(self,event):
	
		dlgd = wx.FileDialog(None, "Select", "", "","Wallet files (*.der)|*.der")
		new_seed = "traditional key no seed for this address"
		
		if dlgd.ShowModal() == wx.ID_OK:
			result = dlgd.GetPath()
		else:
			result = ""
		dlgd.Destroy()
		
		if result == "":
			msgbox = wx.MessageDialog(None,"Nothing done !","Privkey import.....",wx.ICON_INFORMATION)
			msgbox.ShowModal()
			msgbox.Destroy()
		else:
			try:	
				key = RSA.importKey(open(result).read())
				crypt = "0"
			except:
				dlgp = wx.TextEntryDialog(None, 'Paste or type your wallet password here','Privkey import.....', '')
				
				if dlgp.ShowModal() == wx.ID_OK:
					mypass = str(dlgp.GetValue())
					encrypted_privkey = open(result).read()
					decrypted_privkey = decrypt(password, base64.b64decode(encrypted_privkey))
					key = RSA.importKey(decrypted_privkey)
					crypt = "1"
				else:
					msgbox = wx.MessageDialog(None,"Nothing done !","Privkey import.....",wx.ICON_INFORMATION)
					msgbox.ShowModal()
					msgbox.Destroy()
					return
					pass
				
				dlgp.Destroy()
				
			public_key = key.publickey()
			private_key_readable = key.exportKey().decode("utf-8")
			public_key_readable = key.publickey().exportKey().decode("utf-8")
			address = hashlib.sha224(public_key_readable.encode("utf-8")).hexdigest()  # hashed public key
		
			try:
				wlist = sqlite3.connect('wallet.dat')
				wlist.text_factory = str
				w = wlist.cursor()
				w.execute("INSERT INTO wallet VALUES (?,?,?,?,?,?,?)", (str(address),str(private_key_readable),str(public_key_readable),crypt,'',new_seed,'0'))
				wlist.commit()
				wlist.close()
			
				app_log.info('Inserted imported address into wallet.dat')
				msgbox = wx.MessageDialog(None,"Wallet Import Successful","Import Wallet.der",wx.ICON_INFORMATION)
				msgbox.ShowModal()
				msgbox.Destroy()
				
			except:
				app_log.warning('Failed to insert imported address into wallet.dat')
				
	def imp_s_file(self,event):
	
		dlgi = wx.FileDialog(None, "Select", "", "","Export files (*.txt)|*.*")
		seed_list = []
		if dlgi.ShowModal() == wx.ID_OK:
			result = dlgi.GetPath()
		else:
			result = ""
		dlgi.Destroy()
		
		if result == "":
			msgbox = wx.MessageDialog(None,"Nothing done !","Import Seeds from File",wx.ICON_INFORMATION)
			msgbox.ShowModal()
			msgbox.Destroy()
		else:
			with open (result, 'r') as import_file:
			
				seed_list = [line.rstrip('\n') for line in import_file]
				
				for seed in seed_list:
					this_seed = seed.split(',')
					
					x = self.proc_seed(this_seed[1],this_seed[0])
					#x = mwprocs.write_exp(result)
					print(x)
	
	def ViewZero(self,event):
	
		if self.m_set.IsChecked(302):
			do_zero(True)
			self.m_set.Check(302,True)
		else:
			do_zero(False)
			self.m_set.Check(302,False)
			
	def OnWatch(self,event):
	
		dlgw = wx.TextEntryDialog(None, 'Paste or type BIS address to watch here','Watch address', '')
		
		if dlgw.ShowModal() == wx.ID_OK:
			watch_me = str(dlgw.GetValue())			
			dlgw.Destroy()
			try:
				wlist = sqlite3.connect('wallet.dat')
				wlist.text_factory = str
				w = wlist.cursor()
				w.execute("INSERT INTO wallet VALUES (?,?,?,?,?,?,?)", (str(watch_me),'','','3','','','2'))
				wlist.commit()
				wlist.close()
			
				app_log.info('Inserted watch address into wallet.dat')
				msgbox = wx.MessageDialog(None,"Watch Address Import Successful","Watch address",wx.ICON_INFORMATION)
				msgbox.ShowModal()
				msgbox.Destroy()
				
			except:
				app_log.warning('Failed to insert imported address into wallet.dat')
			
		else:
			msgbox = wx.MessageDialog(None,"Nothing entered !","Watch address",wx.ICON_INFORMATION)
			msgbox.ShowModal()
			msgbox.Destroy()
				
if __name__ == "__main__":

	app = wx.App()
	MainFrame().Show()
	app.MainLoop()