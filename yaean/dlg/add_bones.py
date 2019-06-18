import wx
from wx.dataview import TreeListCtrl, TL_CHECKBOX, TL_MULTIPLE


class AddMissingBonesDialog(wx.Dialog):
    def __init__(self, parent, missing_bones, *args, **kw):
        super().__init__(parent, *args, **kw)

        self.SetTitle("Add Missing Bones")
        self.missing_bones = missing_bones

        self.bone_list = TreeListCtrl(self, size=(-1, 250), style=TL_MULTIPLE | TL_CHECKBOX)
        self.bone_list.AppendColumn("Bone")
        root = self.bone_list.GetRootItem()
        for bone in missing_bones:
            item = self.bone_list.AppendItem(root, bone.name, data=bone)
            self.bone_list.CheckItem(item)

        add_button = wx.Button(self, wx.ID_OK, "Add")
        add_button.SetDefault()
        no_add_button = wx.Button(self, wx.ID_CANCEL, "Don't Add")

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(add_button, 0, wx.LEFT | wx.RIGHT, 2)
        button_sizer.Add(no_add_button, 0, wx.LEFT | wx.RIGHT, 5)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self, -1, 'The current EAN is missing the following bones.\n'
                                'Do you want to add them?'), 0, wx.ALL, 10)
        sizer.Add(self.bone_list, 1, wx.ALL | wx.EXPAND, 10)
        sizer.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()

    def GetValues(self):
        missing_bones = []
        item = self.bone_list.GetFirstItem()
        while item.IsOk():
            if self.bone_list.GetCheckedState(item) == wx.CHK_CHECKED:
                missing_bones.append(self.bone_list.GetItemData(item))
            item = self.bone_list.GetNextItem(item)
        return missing_bones

