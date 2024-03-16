#!/usr/bin/env python3

import requests, re, gi, json, os, sys, datetime, subprocess, time

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio

LOG_FILENAME = '~/laserlog/laserlog.log'
CACHE_FILENAME = '~/laserlog/laserlog.cache'

TEXT_INTRO = 'Hoi! Wie ben jij? Wij houden graag bij wie wanneer de lasercutter gebruikt.'
TEXT_NOT_ON_LIST_TITLE = 'Stop!'
TEXT_NOT_ON_LIST_TEXT = '''Als je nog geen persoonlijke instructie gehad hebt,
is het niet de bedoeling dat je de lasercutter gebruikt.

Vraag iemand die wel op de lijst staat of die jou instructie wilt geven.'''

def run(prog):
    global win
    win.close()

    print('Starting %s' % (prog))
    log('%s,%s,%s' % (name, prog, 'start'))

    p = subprocess.Popen([check_path('~/laserlog/start-%s' % (prog))])
    while p.poll() is None:
        time.sleep(0.1)
        while Gtk.events_pending():
            Gtk.main_iteration()

    print('%s done' % (prog))
    log('%s,%s,%s' % (name, 'LaserWeb', 'done'))

    win = LaserLogWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

def check_path(path):
    t = os.path.realpath(os.path.expanduser(path))
    print('"%s" is at "%s"' % (path, t))
    return t

def get_names_from_wiki():
    try:
        print('downloading new list')
        r = requests.get('https://revspace.nl/api.php?action=query&prop=revisions&rvprop=content&rvslots=main&format=json&formatversion=2&redirects&titles=Lasercutter')
        content = r.json()['query']['pages'][0]['revisions'][0]['slots']['main']['content']
        table = re.search(r'= Bevoegde Operators =.+?\}', content, re.S).group(0)
        names = re.findall(r'\|-\n\| ([^|]+) \|\| ([^|]+) \|\| ([^|]+)\n', table)
        json.dump(names, open(CACHE_FILENAME, 'w'))
    except Exception as e:
        print(e)
        print('download failed. attempting cache')
        try:
            names = json.load(open(CACHE_FILENAME))
        except Exception as e:
            print(e)
            print('%s JSON invalid! we\'re done for today' % (CACHE_FILENAME))
            sys.exit(42)

    return names

def log(text):
    fp = open(LOG_FILENAME, 'a')
    fp.write('%s,%s\n' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), text))
    fp.close()
    os.sync()

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

        # Search Entry for filtering
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Jouw naam")

        # Creating the ListStore model
        self.names_store = Gtk.ListStore(str, str, str)
        for software_ref in get_names_from_wiki():
            self.names_store.append(list(software_ref))

        # creating the treeview, making it use the filter as a model, and adding the columns
        # sorting stolen from https://stackoverflow.com/a/19063670/1317735
        self.sorted_model = Gtk.TreeModelSort(model=self.names_store)
        self.sorted_model.set_sort_column_id(0, Gtk.SortType.ASCENDING)
        self.treeview = Gtk.TreeView(model=self.sorted_model)
        self.treeview.set_search_entry(self.search_entry)
        self.treeview.get_selection().connect("changed", self.on_select)
        for i, column_title in enumerate(["Naam"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            column.set_sort_column_id(i)
            self.treeview.append_column(column)

        # creating buttons
        self.not_in_list = Gtk.Button.new_with_mnemonic("Ik sta niet in de l_ijst")
        self.not_in_list.connect("clicked", self.on_not_in_list)

        self.open_wiki = Gtk.Button.new_with_mnemonic("Meer informatie op de wi_ki")
        self.open_wiki.connect("clicked", self.on_wiki)

        self.view_log = Gtk.Button.new_with_mnemonic("Bekijk l_og")
        self.view_log.connect("clicked", self.on_view_log)

        self.not_lasercutting = Gtk.Button.new_with_mnemonic("Ik ga niet l_asercutten")
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
        self.intro_label = Gtk.Label.new(TEXT_INTRO)
        self.grid.attach(self.intro_label, 0, 0, 4, 1)
        self.grid.attach(self.search_entry, 0, 1, 4, 1)
        self.grid.attach(self.scrollable_treelist, 0, 2, 4, 1)
        self.grid.attach(self.not_in_list, 0, 3, 1, 1)
        self.grid.attach(self.not_lasercutting, 0, 4, 1, 1)
        self.grid.attach(self.open_wiki, 1, 3, 1, 1)
        self.grid.attach(self.view_log, 1, 4, 1, 1)
        self.grid.attach(self.start_laserweb, 3, 3, 1, 1)
        self.grid.attach(self.start_lightburn, 3, 4, 1, 1)
        self.scrollable_treelist.add(self.treeview)


    def on_not_in_list(self, widget):
        print("not in list")
        dialog = Gtk.MessageDialog(parent = self, message_type = Gtk.MessageType.ERROR, buttons = Gtk.ButtonsType.OK, text = TEXT_NOT_ON_LIST_TITLE)
        dialog.format_secondary_text(TEXT_NOT_ON_LIST_TEXT)
        dialog.run()
        dialog.destroy()

    def on_not_lasercutting(self, widget):
        print("not lasercutting")
        Gtk.main_quit()

    def on_wiki(self, widget):
        print("Opening wiki")
        os.spawnvp(os.P_NOWAIT, 'xdg-open', ['xdg-open', 'https://revspace.nl/Lasercutter'])

    def on_view_log(self, widget):
        print("opening log")
        os.spawnvp(os.P_NOWAIT, 'xdg-open', ['xdg-open', LOG_FILENAME])

    def on_start_laserweb(self, widget):
        run('laserweb')

    def on_start_lightburn(self, widget):
        run('lightburn')

    def on_select(self, widget):
        global name
        sel = widget.get_selected()
        self.start_laserweb.set_sensitive(False)
        self.start_lightburn.set_sensitive(False)
        if sel[1] is not None:
            self.start_laserweb.set_sensitive(True)
            self.start_lightburn.set_sensitive(True)
            name = sel[0].get_value(sel[1], 0)

LOG_FILENAME = check_path(LOG_FILENAME)
CACHE_FILENAME = check_path(CACHE_FILENAME)

win = LaserLogWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
