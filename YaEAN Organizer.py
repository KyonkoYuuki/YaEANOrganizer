#!/usr/local/bin/python3.6
import os
import sys
import traceback

from pubsub import pub
import wx
from wx.lib.dialogs import MultiMessageDialog

from pyxenoverse.ean import EAN
from pyxenoverse.esk import ESK
from pyxenoverse.gui import create_backup
from yaean.panels.anim_main import AnimMainPanel
from yaean.panels.anim_side import AnimSidePanel
from yaean.panels.bone_main import BoneMainPanel
from yaean.panels.bone_side import BoneSidePanel
from yaean.helpers import build_anim_list, build_bone_tree

VERSION = '0.4.0'


class MainWindow(wx.Frame):
    def __init__(self, parent, title, dirname, filename):
        sys.excepthook = self.exception_hook
        self.copied_animations = None
        self.copied_bones = None
        self.copied_bone_info = None
        self.locale = wx.Locale(wx.LANGUAGE_ENGLISH)

        # A "-1" in the size parameter instructs wxWidgets to use the default size.
        # In this case, we select 200px width and the default height.
        wx.Frame.__init__(self, parent, title=title, size=(1200,800))
        self.statusbar = self.CreateStatusBar() # A Statusbar in the bottom of the window

        # Setting up the menu.
        filemenu= wx.Menu()
        menu_about= filemenu.Append(wx.ID_ABOUT)
        menu_exit = filemenu.Append(wx.ID_EXIT)

        # Creating the menubar.
        menu_bar = wx.MenuBar()
        menu_bar.Append(filemenu,"&File") # Adding the "filemenu" to the MenuBar
        self.SetMenuBar(menu_bar)  # Adding the MenuBar to the Frame content.

        # Publisher
        pub.subscribe(self.open_main_file, 'open_main_file')
        pub.subscribe(self.load_main_file, 'load_main_file')
        pub.subscribe(self.open_side_file, 'open_side_file')
        pub.subscribe(self.load_side_file, 'load_side_file')
        pub.subscribe(self.save_ean, 'save_ean')
        pub.subscribe(self.save_esk, 'save_esk')
        pub.subscribe(self.copy_bone_info, 'copy_bone_info')

        # Events
        self.Bind(wx.EVT_MENU, self.on_exit, menu_exit)
        self.Bind(wx.EVT_MENU, self.on_about, menu_about)

        # Tabs
        self.main_notebook = wx.Notebook(self)

        self.ean_main_notebook = wx.Notebook(self.main_notebook)
        self.ean_main_notebook.SetBackgroundColour(wx.Colour('grey'))
        self.esk_main_notebook = wx.Notebook(self.main_notebook)
        self.main_notebook.AddPage(self.ean_main_notebook, "EAN")
        self.main_notebook.AddPage(self.esk_main_notebook, "ESK")

        self.anim_main_panel = AnimMainPanel(self.ean_main_notebook, self)
        self.bone_main_panel = BoneMainPanel(self.ean_main_notebook, self, "EAN")
        self.ean_main_notebook.AddPage(self.anim_main_panel, "Animation List")
        self.ean_main_notebook.AddPage(self.bone_main_panel, "Bone List")

        self.esk_main_panel = BoneMainPanel(self.esk_main_notebook, self, "ESK")
        self.esk_main_notebook.AddPage(self.esk_main_panel, "Bone List")

        # Other view
        self.side_notebook = wx.Notebook(self)

        self.ean_side_notebook = wx.Notebook(self.side_notebook)
        self.ean_side_notebook.SetBackgroundColour(wx.Colour('grey'))
        self.esk_side_notebook = wx.Notebook(self.side_notebook)
        self.side_notebook.AddPage(self.ean_side_notebook, "EAN")
        self.side_notebook.AddPage(self.esk_side_notebook, "ESK")

        self.anim_side_panel = AnimSidePanel(self.ean_side_notebook, self)
        self.bone_side_panel = BoneSidePanel(self.ean_side_notebook, self, "EAN")
        self.ean_side_notebook.AddPage(self.anim_side_panel, "Animation List")
        self.ean_side_notebook.AddPage(self.bone_side_panel, "Bone List")

        self.esk_side_panel = BoneSidePanel(self.esk_side_notebook, self, "ESK")
        self.esk_side_notebook.AddPage(self.esk_side_panel, "Bone List")

        # Sizer
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.main_notebook, 1, wx.ALL|wx.EXPAND)
        self.sizer.Add(self.side_notebook, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)

        # Lists
        self.main = {
            'dirname': '',
            'ean': None,
            'esk': None,
            'notebook': self.main_notebook,
            'anim_panel': self.anim_main_panel,
            'ean_bone_panel': self.bone_main_panel,
            'esk_bone_panel': self.esk_main_panel,
            'anim_list': self.anim_main_panel.anim_list,
            'ean_bone_list': self.bone_main_panel.bone_list,
            'esk_bone_list': self.esk_main_panel.bone_list
        }

        self.side = {
            'dirname': '',
            'ean': None,
            'esk': None,
            'notebook': self.side_notebook,
            'anim_panel': self.anim_side_panel,
            'ean_bone_panel': self.bone_side_panel,
            'esk_bone_panel': self.esk_side_panel,
            'anim_list': self.anim_side_panel.anim_list,
            'ean_bone_list': self.bone_side_panel.bone_list,
            'esk_bone_list': self.esk_side_panel.bone_list
        }

        self.sizer.Layout()
        self.Show()

        if filename:
            self.load_main_file(dirname, filename)

    def exception_hook(self, e, value, trace):
        with MultiMessageDialog(self, '', 'Error', ''.join(traceback.format_exception(e, value, trace)), wx.OK) as dlg:
            dlg.ShowModal()

    def on_about(self, _):
        # Create a message dialog box
        with wx.MessageDialog(self, " Yet another EAN Organizer v{} by Kyonko Yuuki".format(VERSION),
                              "About YaEAN Organizer", wx.OK) as dlg:
            dlg.ShowModal() # Shows it

    def on_exit(self, _):
        self.Close(True)  # Close the frame.

    def open_file(self, obj):
        with wx.FileDialog(self, "Choose a file", obj['dirname'], "", "*.ean;*.esk", wx.FD_OPEN) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.load_file(dlg.GetDirectory(), dlg.GetFilename(), obj)

    def load_file(self, dirname, filename, obj):
        obj['dirname'] = dirname
        path = os.path.join(obj['dirname'], filename)
        self.statusbar.SetStatusText("Loading...")
        new_ean = EAN()
        new_esk = ESK()
        if new_ean.load(path):
            obj['ean'] = new_ean
            build_anim_list(obj['anim_list'], obj['ean'])
            build_bone_tree(obj['ean_bone_list'], obj['ean'].skeleton)
            obj['anim_panel'].name.SetLabel(filename)
            obj['anim_panel'].Layout()
            obj['ean_bone_panel'].name.SetLabel(filename)
            obj['ean_bone_panel'].Layout()
            obj['notebook'].ChangeSelection(0)
            obj['notebook'].Layout()
            if obj['notebook'] == self.side['notebook']:
                self.copied_animations = None
        elif new_esk.load(path):
            obj['esk'] = new_esk
            build_bone_tree(obj['esk_bone_list'], obj['esk'])
            obj['esk_bone_panel'].name.SetLabel(filename)
            obj['esk_bone_panel'].Layout()
            obj['notebook'].ChangeSelection(1)
            obj['notebook'].Layout()
        else:
            with wx.MessageDialog(self, "{} is not a valid EAN/ESK".format(filename), "Warning") as dlg:
                dlg.ShowModal()
            return

        # TODO: Don't reset everything
        if obj['ean_bone_panel'] == self.side['ean_bone_panel']:
            self.side['ean_bone_panel'].deselect_all()
            self.side['esk_bone_panel'].deselect_all()
            self.main['ean_bone_panel'].copied_bones = None
            self.main['esk_bone_panel'].copied_bones = None
            self.copied_bone_info = None

        self.statusbar.SetStatusText("Loaded {}".format(path))

    def open_main_file(self):
        self.open_file(self.main)

    def load_main_file(self, dirname, filename):
        self.load_file(dirname, filename, self.main)

    def open_side_file(self):
        self.open_file(self.side)

    def load_side_file(self, dirname, filename):
        self.load_file(dirname, filename, self.side)

    def save_file(self, obj, filetype):
        if obj[filetype.lower()] is None:
            with wx.MessageDialog(self, " No {} Loaded".format(filetype), "Warning", wx.OK) as dlg:
                dlg.ShowModal()
            return

        with wx.FileDialog(self, "Choose a file", obj['dirname'], "", "*." + filetype.lower(), wx.FD_SAVE) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetFilename()
                obj['dirname'] = dlg.GetDirectory()
                self.statusbar.SetStatusText("Saving...")
                create_backup(obj['dirname'], filename)
                path = os.path.join(obj['dirname'], filename)
                removed_nodes = obj[filetype.lower()].save(path)
                msg = ''
                if removed_nodes:
                    msg = "The following animation nodes were removed:\n{}".format(
                        '\n'.join([' * ' + node for node in sorted(removed_nodes)]))
                self.statusbar.SetStatusText("Saved {}".format(path))
                with MultiMessageDialog(
                        self, "Saved to {} successfully".format(path), filetype + " Saved", msg, wx.OK) as saved:
                    saved.ShowModal()

    def save_ean(self):
        self.save_file(self.main, "EAN")

    def save_esk(self):
        self.save_file(self.main, "ESK")

    def copy_bone_info(self, filename, bone):
        self.copied_bone_info = filename, bone


if __name__ == '__main__':
    app = wx.App(False)
    dirname = filename = None
    if len(sys.argv) > 1:
        dirname, filename = os.path.split(sys.argv[1])
    frame = MainWindow(None, f"YaEAN Organizer v{VERSION}", dirname, filename)
    app.MainLoop()
