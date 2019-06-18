import wx
import wx.dataview
from pubsub import pub

from yaean.dlg.bone_info import BoneInfoDialog
from yaean.helpers import CHECK
from pyxenoverse.gui.file_drop_target import FileDropTarget


class BoneSidePanel(wx.Panel):
    def __init__(self, parent, root, filetype):
        wx.Panel.__init__(self, parent)
        self.root = root
        self.filetype = filetype
        self.selected = []

        # Name
        self.name = wx.StaticText(self, -1, '(No file loaded)')
        self.font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.name.SetFont(self.font)

        # Buttons
        self.load = wx.Button(self, wx.ID_OPEN, "Load")
        self.copy = wx.Button(self, wx.ID_COPY, "Copy")
        self.info = wx.Button(self, wx.ID_INFO, "Info")

        self.copy.Disable()
        self.info.Disable()

        # Children
        self.check_box = wx.CheckBox(self, -1, "Select child bones?")
        self.check_box.SetValue(wx.CHK_CHECKED)

        self.bone_list = wx.dataview.TreeListCtrl(self)

        self.bone_list.AppendColumn("Bone")
        self.bone_list.AppendColumn("Selected", width=80)
        self.bone_list.Bind(wx.dataview.EVT_TREELIST_ITEM_CONTEXT_MENU, self.on_right_click)
        self.bone_list.Bind(wx.dataview.EVT_TREELIST_SELECTION_CHANGED, self.on_select)
        self.bone_list.SetDropTarget(FileDropTarget(self, "load_side_file"))

        self.Bind(wx.EVT_BUTTON, self.on_open, id=wx.ID_OPEN)
        self.Bind(wx.EVT_BUTTON, self.on_copy, id=wx.ID_COPY)
        self.Bind(wx.EVT_BUTTON, self.on_info, id=wx.ID_INFO)

        self.Bind(wx.EVT_MENU, self.on_copy, id=wx.ID_COPY)
        self.Bind(wx.EVT_MENU, self.on_info, id=wx.ID_INFO)
        accelerator_table = wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord('c'), wx.ID_COPY),
            (wx.ACCEL_CTRL, ord('i'), wx.ID_INFO)
        ])
        self.bone_list.SetAcceleratorTable(accelerator_table)

        # Use some sizers to see layout options
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.button_sizer.Add(self.load)
        self.button_sizer.AddSpacer(5)
        self.button_sizer.Add(self.copy)
        self.button_sizer.AddSpacer(5)
        self.button_sizer.Add(self.info)
        self.button_sizer.AddSpacer(10)
        self.button_sizer.Add(self.check_box)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.name, 0, wx.CENTER)
        self.sizer.Add(self.button_sizer)
        self.sizer.Add(self.bone_list, 1, wx.EXPAND)

        pub.subscribe(self.deselect_all, 'deselect_bones')

        # Layout sizers
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)

    def on_open(self, _):
        self.copy.Disable()
        self.selected = []
        pub.sendMessage('open_side_file')

    def on_copy(self, _):
        self.on_select(None)
        self.root.side['ean_bone_panel'].deselect_all()
        self.root.side['esk_bone_panel'].deselect_all()
        bone = self.bone_list.GetFirstItem()
        copied_bones = []
        while bone.IsOk():
            if bone in self.selected:
                self.bone_list.SetItemText(bone, 1, CHECK)
                copied_bones.append(self.bone_list.GetItemData(bone))
            bone = self.bone_list.GetNextItem(bone)

        copied_bones.sort(key=lambda bone: bone.index)
        pub.sendMessage('copy_bones', copied_bones=copied_bones)
        self.root.SetStatusText("Copied {} pyxenoverse(s)".format(len(copied_bones)))

    def get_children(self, bone):
        while bone.IsOk():
            self.selected.append(bone)
            self.get_children(self.bone_list.GetFirstChild(bone))
            bone = self.bone_list.GetNextSibling(bone)

    def deselect_all(self):
        bone = self.bone_list.GetFirstItem()
        while bone.IsOk():
            self.bone_list.SetItemText(bone, 1, '')
            bone = self.bone_list.GetNextItem(bone)

    def on_select(self, _):
        selection = self.bone_list.GetSelection()
        self.selected = [selection]
        if selection and self.check_box.GetValue():
            self.get_children(self.bone_list.GetFirstChild(selection))

        if self.selected:
            self.copy.Enable()
            self.info.Enable()
        else:
            self.copy.Disable()
            self.info.Disable()

    def on_info(self, _):
        selection = self.bone_list.GetSelections()
        if len(selection) != 1:
            with wx.MessageDialog(self, 'Only one pyxenoverse can be selected for this operation', 'Warning') as dlg:
                dlg.ShowModal()
                return
        bone = self.bone_list.GetItemData(selection[0])
        with BoneInfoDialog(
                self.root, self.filetype, self.name.GetLabel(), bone, True) as dlg:
            dlg.ShowModal()

    def on_right_click(self, _):
        menu = wx.Menu()
        menu.Append(wx.ID_INFO, "&Info\tCtrl+I", " Bone info")
        menu.Append(wx.ID_COPY, "&Copy\tCtrl+C", " Copy pyxenoverse(s)")
        self.PopupMenu(menu)
        menu.Destroy()
