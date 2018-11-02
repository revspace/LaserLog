#!/bin/env python3

import requests, re, gi, json, os, sys, datetime

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

LOG_FILENAME = 'laserlog.log'
CACHE_FILENAME = 'laserlog.cache'
CACHE_SECONDS = 600

TEXT_INTRO = 'Hoi! Wie ben jij? Wij houden graag bij wie wanneer de lasercutter gebruikt.'
TEXT_NOT_ON_LIST = '''Als je nog geen persoonlijke instructie gehad hebt, is het niet de bedoeling dat je de lasercutter gebruikt.
Vraag iemand die wel op de lijst staat of hij/zij jou instructie wilt geven.'''


def get_names_from_wiki():
    download = False
    try:
        mtime = os.path.getmtime(CACHE_FILENAME)
        now = datetime.datetime.now().timestamp()
        print('%s is %d seconds old' % (CACHE_FILENAME, now - mtime))
        if (now - mtime) > CACHE_SECONDS:
            print('this is more than %d seconds' % (CACHE_SECONDS))
            download = True
    except FileNotFoundError:
        print('%s does not exist' % (CACHE_FILENAME))
        download = True

    if not download:
        try:
            names = json.load(open(CACHE_FILENAME))
        except json.decoder.JSONDecodeError:
            print('%s JSON invalid' % (CACHE_FILENAME))
            download = True

    if download:
        print('downloading new %s' % (CACHE_FILENAME))

        try:
            r = requests.get('https://revspace.nl/api.php?action=query&prop=revisions&rvprop=content&format=json&formatversion=2&redirects&titles=Lasercutter')
            content = r.json()['query']['pages'][0]['revisions'][0]['content']
            table = re.search(r'= Bevoegde Operators =.+?\}', content, re.S).group(0)
            names = re.findall(r'\|-\n\| ([^|]+) \|\| ([^|]+) \|\| ([^|]+)\n', table)
            json.dump(names, open(CACHE_FILENAME, 'w'))
        except:
            print('download failed. attempting cache (again)')
            try:
                names = json.load(open(CACHE_FILENAME))
            except:
                print('%s JSON invalid! we\'re done for today' % (CACHE_FILENAME))
                sys.exit(42)


    return names

class LaserLogWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="LaserLog")
        self.set_border_width(16)

        # Setting up the self.grid in which the elements are to be positionned
        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_spacing(8)
        self.grid.set_column_spacing(8)
        self.add(self.grid)
        self.set_default_size(600, 600)
        self.name = None

        # Search Entry for filtering
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Jouw naam")

        # Creating the ListStore model
        self.names_store = Gtk.ListStore(str, str, str)
        for software_ref in get_names_from_wiki():
            self.names_store.append(list(software_ref))

        # creating the treeview, making it use the filter as a model, and adding the columns
        self.treeview = Gtk.TreeView.new_with_model(self.names_store)
        self.treeview.set_search_entry(self.search_entry)
        self.treeview.get_selection().connect("changed", self.on_select)
        for i, column_title in enumerate(["Naam", "Geïnstrueerd door", "Ervaring met software"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            self.treeview.append_column(column)

        # creating buttons
        self.not_in_list = Gtk.Button.new_with_mnemonic("Ik sta niet in de _lijst")
        self.not_in_list.connect("clicked", self.on_not_in_list)

        self.open_wiki = Gtk.Button.new_with_mnemonic("Meer _informatie op de wiki")
        self.open_wiki.connect("clicked", self.on_wiki)

        self.not_lasercutting = Gtk.Button.new_with_mnemonic("Ik ga _niet lasercutten")
        self.not_lasercutting.connect("clicked", self.on_not_lasercutting)

        self.start_laserweb = Gtk.Button.new_with_mnemonic("Start Laser_Web")
        self.start_laserweb.connect("clicked", self.on_start_laserweb)
        self.start_laserweb.set_sensitive(False)

        self.start_lightburn = Gtk.Button.new_with_mnemonic("Start Light_Burn")
        self.start_lightburn.connect("clicked", self.on_start_lightburn)
        self.start_lightburn.set_sensitive(False)

        #setting up the layout
        self.scrollable_treelist = Gtk.ScrolledWindow()
        self.scrollable_treelist.set_vexpand(True)
        self.intro_label = Gtk.Label(TEXT_INTRO)
        self.grid.attach(self.intro_label, 0, 0, 3, 1)
        self.grid.attach(self.search_entry, 0, 1, 3, 1)
        self.grid.attach(self.scrollable_treelist, 0, 2, 3, 1)
        self.grid.attach(self.not_in_list, 0, 3, 1, 1)
        self.grid.attach(self.not_lasercutting, 0, 4, 1, 1)
        self.grid.attach(self.start_laserweb, 1, 3, 1, 1)
        self.grid.attach(self.start_lightburn, 1, 4, 1, 1)
        self.grid.attach(self.open_wiki, 2, 3, 1, 1)
        self.scrollable_treelist.add(self.treeview)


    def on_not_in_list(self, widget):
        print("not in list")
        self.not_in_list_label = Gtk.Label(TEXT_NOT_ON_LIST)
        self.grid.attach(self.not_in_list_label, 0, 5, 3, 1)
        self.show_all()

    def on_not_lasercutting(self, widget):
        print("not lasercutting")
        Gtk.main_quit()

    def on_wiki(self, widget):
        print("Opening wiki")
        os.spawnvp(os.P_NOWAIT, 'xdg-open', ['xdg-open', 'https://revspace.nl/Lasercutter'])

    def on_start_laserweb(self, widget):
        print("Starting LaserWeb")
        Gtk.main_quit()
        fp = open(LOG_FILENAME, 'a')
        fp.write('%s,%s,%s\n' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.name, 'LaserWeb'))
        fp.close()
        os.execvp('zenity', ['zenity', '--info', '--text=dummy laserweb'])

    def on_start_lightburn(self, widget):
        print("Starting LightBurn")
        Gtk.main_quit()
        fp = open(LOG_FILENAME, 'a')
        fp.write('%s,%s,%s\n' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.name, 'LightBurn'))
        fp.close()
        os.execvp('zenity', ['zenity', '--info', '--text=dummy lightburn'])

    def on_select(self, widget):
        sel = widget.get_selected()
        self.start_laserweb.set_sensitive(False)
        self.start_lightburn.set_sensitive(False)
        if sel[1] is not None:
            self.name = sel[0].get_value(sel[1], 0)
            prog = sel[0].get_value(sel[1], 2).lower()
            if "laserweb" in prog:
                self.start_laserweb.set_sensitive(True)
            if "lightburn" in prog:
                self.start_lightburn.set_sensitive(True)

win = LaserLogWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
