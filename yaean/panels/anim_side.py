import wx
from pubsub import pub

from yaean.helpers import get_selected_items, CHECK
from pyxenoverse.gui.file_drop_target import FileDropTarget


class AnimSidePanel(wx.Panel):
    def __init__(self, parent, root):
        wx.Panel.__init__(self, parent)
        self.root = root

        # Name
        self.name = wx.StaticText(self, -1, '(No file loaded)')
        self.font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.name.SetFont(self.font)

        # Load button
        self.load = wx.Button(self, wx.ID_OPEN, "Load")
        self.copy = wx.Button(self, wx.ID_COPY, "Copy")
        self.copy.Disable()

        # Anim List
        self.anim_list = wx.ListCtrl(self, style=wx.LC_REPORT)
        self.anim_list.InsertColumn(0, "#", width=30)
        self.anim_list.InsertColumn(1, "Animation", width=200)
        self.anim_list.InsertColumn(2, "Frames", width=50)
        self.anim_list.InsertColumn(3, "Copied", width=60)
        self.anim_list.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_right_click)
        self.anim_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select)
        self.anim_list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_select)
        self.anim_list.SetDropTarget(FileDropTarget(self, "load_side_file"))

        # Bind
        self.Bind(wx.EVT_BUTTON, self.on_open, id=wx.ID_OPEN)
        self.Bind(wx.EVT_BUTTON, self.on_copy, id=wx.ID_COPY)

        # Select All
        self.Bind(wx.EVT_MENU, self.select_all, id=wx.ID_SELECTALL)
        self.Bind(wx.EVT_MENU, self.on_copy, id=wx.ID_COPY)
        accelerator_table = wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord('a'), wx.ID_SELECTALL),
            (wx.ACCEL_CTRL, ord('c'), wx.ID_COPY),
        ])
        self.anim_list.SetAcceleratorTable(accelerator_table)

        # Button Sizer
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.button_sizer.Add(self.load)
        self.button_sizer.AddSpacer(5)
        self.button_sizer.Add(self.copy)

        # Use some sizers to see layout options
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.name, 0, wx.CENTER)
        self.sizer.Add(self.button_sizer)
        self.sizer.Add(self.anim_list, 1, wx.EXPAND | wx.ALL)

        # Layout sizers
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)

    def select_all(self, _):
        for i in range(self.anim_list.GetItemCount()):
            self.anim_list.Select(i)

    def on_select(self, _):
        selected = list(get_selected_items(self.anim_list))
        if selected:
            self.copy.Enable()
        else:
            self.copy.Disable()

    def on_right_click(self, _):
        menu = wx.Menu()
        menu.Append(wx.ID_SELECTALL, "&Select All\tCtrl+A", " Select all animations")
        menu.Append(wx.ID_COPY, "&Copy\tCtrl+C", " Copy selected animation")
        self.PopupMenu(menu)
        menu.Destroy()

    def on_open(self, _):
        self.copy.Disable()
        pub.sendMessage('open_side_file')

    def on_copy(self, _):
        selected = list(get_selected_items(self.anim_list))
        if not selected:
            return
        copied_animations = [self.root.side['ean'].animations[i] for i in selected]
        for i in range(self.anim_list.GetItemCount()):
            if i in selected:
                self.anim_list.SetItem(i, 3, CHECK)
            else:
                self.anim_list.SetItem(i, 3, '')
        pub.sendMessage('copy_animation', copied_animations=copied_animations)
        self.root.SetStatusText("Copied {} animation(s)".format(len(copied_animations)))
