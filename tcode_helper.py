import tkinter as tk
from tkinter import ttk
from tkinter import font as tkFont
from tkinter import messagebox
from PIL import Image, ImageTk
import pystray
import keyboard
import json, sys, re
from version import version

class RichText(tk.Text):

	"""
	Campo di testo customizzato per usare stili.
	"""

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		default_font = tkFont.nametofont(self.cget("font"))

		default_size = default_font.cget("size")
		bold_font = tkFont.Font(**default_font.configure())
		italic_font = tkFont.Font(**default_font.configure())
		h1_font = tkFont.Font(**default_font.configure())
		base_font = tkFont.Font(**default_font.configure())

		bold_font.configure(weight="bold", family="Arial")
		italic_font.configure(size=int(default_size*.8), slant="italic", family="Arial")
		base_font.configure(family="Arial")
		h1_font.configure(size=int(default_size*2), weight="bold")

		self.tag_configure("bold", font=bold_font)
		self.tag_configure("italic", font=italic_font)
		self.tag_configure("base", font=base_font)
		self.tag_configure("h1", font=h1_font, spacing3=default_size)


###############################################################################

class Gui():

	# Tiene nota del fatto che il popup informativo sia già stato mostrato
	popup_shown = False

	# File da cui caricare i TCodes
	tcodes_filename = "tcodes.json"

	# File da cui caricare il logo
	logo_filename = "logo.png"

	###########################################################################

	# Inizializzazione finestra
	def __init__(self):

		# Legge lista
		try:
			with open(self.tcodes_filename, "r") as file:
				self.tcodes = json.load(file)
			print(f"Caricato file {self.tcodes_filename}, letti {len(self.tcodes)} elementi.")
		except OSError as e:
			messagebox.showerror(
				"TCode Helper",
				f"Errore durante il caricamento dei tcodes: {str(e)}. Il programma verrà terminato."
			)
			sys.exit()
		except json.decoder.JSONDecodeError as e:
			messagebox.showerror(
				"TCode Helper",
				f"Errore durante l'interpretazione dei tcodes: {str(e)}. Il programma verrà terminato."
			)
			sys.exit()			

		self.window = tk.Tk()
		self.window.title("TCode Helper - " + version)
		self.window.geometry("400x400")

		style = ttk.Style(self.window)
		style.theme_use("xpnative")

		# Nasconde la finestra durante creazione/spostamenti
		self.window.withdraw()

		# Carica logo (per tray e per icona app)
		try:
			self.logo = Image.open(self.logo_filename)
		except OSError as e:
			messagebox.showerror(
				"TCode Helper",
				f"Errore durante il caricamento del logo: {str(e)}. Il programma verrà terminato."
			)
			sys.exit()

		# Imposta icona app
		app_icon = ImageTk.PhotoImage(self.logo)
		self.window.wm_iconphoto(False, app_icon)

		# Menu per icona tray
		self.menu = (
			pystray.MenuItem('Mostra finestra', self.show_window, default=True),
			pystray.MenuItem('Termina applicazione', self.quit_window)
		)

		# Imposta chiamata a withdraw_window in caso di chiusura della finestra
		self.window.protocol('WM_DELETE_WINDOW', self.withdraw_window)

		# Imposta chiamata a withdraw_window in caso di pressione tasto ESC
		self.window.bind('<Escape>', self.withdraw_window)

		# Hotkey globale per apertura finestra
		keyboard.add_hotkey('shift+F12', self.show_window)

		# Creazione componenti UI
		small_info_image=self.logo.resize((12, 12))
		small_info_image_tk = ImageTk.PhotoImage(small_info_image)
		self.info_img = ttk.Button(self.window, image=small_info_image_tk, command=self.popup_about)
		self.info_img.grid(row=0, column=1, sticky="nsew")

		self.search_field = ttk.Entry(self.window, width=50)
		self.search_field.grid(row=0, column=0, sticky="nsew") #columnspan=2
		self.search_field.bind("<KeyRelease>", self._text_callback)
		self.search_field.bind("<Tab>", self.focus_tree)

		columns = ('code', 'descr')
		self.tree = ttk.Treeview(self.window, columns=columns, show='headings') # tree headings
		self.tree.column("#0", minwidth=0, width=20, stretch=tk.NO, anchor=tk.CENTER) 		
		self.tree.column("code", minwidth=0, width=100, stretch=tk.NO) 
		self.tree.heading('code', text='TCode')
		self.tree.heading('descr', text='Descrizione')
		self.tree.grid(row=1, column=0, sticky="nsew")
		self.tree.bind('<<TreeviewSelect>>', self._selected_tcode)
		self.tree.bind("<Tab>", self.focus_search)

		self.list_scrollbar = ttk.Scrollbar(self.window, orient=tk.VERTICAL, command=self.tree.yview)
		self.tree.configure(yscroll=self.list_scrollbar.set)
		self.list_scrollbar.grid(row=1, column=1, sticky="nsew")		

		self.descr_text = RichText(self.window, height=5, borderwidth=5, relief=tk.FLAT, wrap=tk.WORD)
		self.descr_text.grid(row=2, column=0, columnspan=1)

		self.descr_scrollbar = ttk.Scrollbar(self.window, orient=tk.VERTICAL, command=self.descr_text.yview)
		self.descr_text.configure(yscroll=self.descr_scrollbar.set)
		self.descr_scrollbar.grid(row=2, column=1, sticky="nsew")		

		self.window.columnconfigure(0, weight=1)
		self.window.rowconfigure(1, weight=1)

		# Disattiva qualunque azione (compresa modifica) sul campo di testo
		# problema: non consente di tabbare fuori, e blocca callback su esc
		# self.descr_text.bind("<Key>", lambda e: "break")

		# Centra la finestra nello schermo
		self.window.eval('tk::PlaceWindow . center')

		# Mostra la finestra (precedentemente nascosta) al termine di
		# creazione/spostamenti
		self.window.deiconify()

		# Assegna focus a campo di ricerca
		self.window.focus_set()
		self.search_field.focus_set()		

		self.window.mainloop()

	###########################################################################

	def _text_callback(self, event):

		"""
		Callback su inserimento/modifica testo in campo di ricerca.
		"""

		# Verifica che stringa ricerca sia cambiata		
		search = self.search_field.get().upper()
		if (hasattr(self, 'prev_search') and search == self.prev_search):
			return
		self.prev_search = search

		# Identifica parole chiave ricerca
		keywords = [x for x in search.upper().split(' ') if len(x) > 1]
		
		# Inizializza lista per punteggi ai tcodes
		tcodes_points = [[x, 0] for x in self.tcodes]

		# Calcola punteggi 
		# Un punto per ciascuna occorrenza di ciascuna parola chiave nella descrizione
		for keyword in keywords:
			for tcode in tcodes_points:

				pattern = keyword
				text = tcode[0]['keywords'].upper()

				if (re.search("(^| )" + pattern + "( |$)", text)):
					tcode[1] += 2
					print(pattern, tcode)
				elif tcode[0]['keywords'].upper().find(keyword) != -1:
					tcode[1] += 1
		
		# Ordina e ricostruisce lista tcodes con punteggio non nullo
		tcodes_points.sort(key=lambda x: x[1], reverse=True)
		for x in tcodes_points:
			x[0]['score'] = x[1] 
		filtered_list = [x[0] for x in tcodes_points if x[1] > 0]
					
		# Pulisce albero
		for i in self.tree.get_children():
			self.tree.delete(i)
		
		# Aggiunge record in albero
		for item in filtered_list:
			self.tree.insert('', tk.END, values=(item['code'], item['descr']), tags = ('function'))

	###########################################################################

	def focus_tree(self, event):

		"""
		Chiamato per dare il focus all'albero e gestire
		l'evidenziazione di una riga.
		"""

		if (self.tree.get_children()):
			child_id = self.tree.get_children()[0]
			self.tree.focus_set()
			self.tree.focus(child_id)
			self.tree.selection_set(child_id)
		
		return("break")

	###########################################################################

	def focus_search(self, event):

		"""
		Chiamato per dare focus a campo ricerca.
		"""

		self.search_field.focus_set()
		self.search_field.selection_range(0, tk.END)

		return("break")

	###########################################################################

	def _selected_tcode(self, event):

		"""
		Callback alla selezione di un nodo dell'albero.
		"""

		if (len(self.tree.selection()) > 0):

			selected_id = self.tree.selection()[0]
			selected_item = self.tree.item(selected_id)
			selected_tcode = next((x for x in self.tcodes if x['code'] == selected_item['values'][0]), "")

			self.descr_text.delete('1.0', tk.END)
			self.descr_text.insert("end", f"{selected_tcode['code']}\n", "bold")
			self.descr_text.insert("end", f"{selected_tcode['descr']}", "base")
			self.descr_text.insert("end", f"\n\nKeywords ({selected_tcode['score']}): {selected_tcode['keywords']}", "italic")

		return("break")

	###########################################################################

	def quit_window(self):

		"""
		Termina applicazione.
		"""

		self.icon.stop()
		self.window.destroy()
	
	###########################################################################

	def show_window(self):

		"""
		Mostra finestra e nasconde tray icon.
		"""

		if (hasattr(self, 'icon')):
			self.icon.stop()

		self.window.withdraw()
		self.window.deiconify()
		self.window.lift()

		self.search_field.selection_range(0, tk.END)

		# Mette la finestra in primo piano, ma senza
		# lasciarla bloccata lì.
		self.window.attributes("-topmost", True)
		self.window.attributes("-topmost", False)

		self.window.focus_set()
		self.search_field.focus_set()		

	###########################################################################

	def withdraw_window(self, *args):

		"""
		Nasconde finestra e mostra tray icon.
		"""

		self.window.withdraw()
		self.icon = pystray.Icon("TCode Helper", self.logo, "TCode Helper", self.menu)
		self.icon.run(self.show_popup)

	###########################################################################

	def show_popup(self, icon):

		"""
		Mostra popup informativo alla prima riduzione a tray.
		"""

		self.icon.visible = True
		if (not self.popup_shown):
			self.icon.notify("TCode Helper in esecuzione, premere Shift+F12 per richiamare.", "TCode Helper")
			self.popup_shown = True

	###########################################################################

	def popup_about(self):

		"""
		Mostra popup informativo.
		"""

		messagebox.showinfo(
			"TCode Helper",
			"Un simpatico tool per chi non riesce a imparare\n" + 
			"a memoria millemila TCode.\n\n" +
			"In caso di problemi chiedete di Mario."
		)


if __name__ in '__main__':
	Gui()
