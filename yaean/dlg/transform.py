import wx
from wx.lib.agw.floatspin import FloatSpin
from pubsub import pub


class TransformDialog(wx.Dialog):
    def __init__(self, parent, name, selected, bone_list, *args, **kw):
        super().__init__(parent, *args, **kw)

        self.selected = selected
        self.SetTitle("Set {} for Animation".format(name))

        grid_sizer = wx.FlexGridSizer(rows=4, cols=2, hgap=10, vgap=10)
        if bone_list:
            self.bone_list = wx.Choice(self, -1, choices=bone_list)
            for i, bone_name in enumerate(bone_list):
                if 'b_c_base' in bone_name.lower():
                    self.bone_list.Select(i)
                    break
            else:
                self.bone_list.Select(0)
            grid_sizer.Add(wx.StaticText(self, -1, 'Bone'), 0, wx.CENTER)
            grid_sizer.Add(self.bone_list, 0, wx.ALIGN_RIGHT)
        else:
            self.bone_list = None

        grid_sizer.Add(wx.StaticText(self, -1, f'X {name}'), 0, wx.CENTER)
        self.ctrl_x = FloatSpin(self, -1, increment=0.01, value=0.0, digits=8, size=(150, -1))
        grid_sizer.Add(self.ctrl_x, 0, wx.ALIGN_RIGHT)

        grid_sizer.Add(wx.StaticText(self, -1, f'Y {name}'), 0, wx.CENTER)
        self.ctrl_y = FloatSpin(self, -1, increment=0.01, value=0.0, digits=8, size=(150, -1))
        grid_sizer.Add(self.ctrl_y, 0, wx.ALIGN_RIGHT)

        grid_sizer.Add(wx.StaticText(self, -1, f'Z {name}'), 0, wx.CENTER)
        self.ctrl_z = FloatSpin(self, -1, increment=0.01, value=0.0, digits=8, size=(150, -1))
        grid_sizer.Add(self.ctrl_z, 0, wx.ALIGN_RIGHT)

        ok_button = wx.Button(self, wx.ID_OK, "Ok")
        ok_button.SetDefault()
        cancel_button = wx.Button(self, wx.ID_CANCEL, "Cancel")

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(grid_sizer, 1, wx.ALL, 10)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(ok_button, 0, wx.LEFT | wx.RIGHT, 2)
        button_sizer.Add(cancel_button, 0, wx.LEFT | wx.RIGHT, 5)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(hsizer, 1, wx.ALL, 10)
        sizer.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)

        self.Bind(wx.EVT_BUTTON, self.on_close)
        self.ctrl_x.SetFocus()
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()

    def on_close(self, e):
        if e.GetId() == wx.ID_OK and self.bone_list and self.bone_list.GetSelection() == wx.NOT_FOUND:
            with wx.MessageDialog(self, " No Bone Selected", "Warning", wx.OK) as dlg:
                dlg.ShowModal()  # Shows it
            return
        e.Skip()

    def GetBoneIndex(self):
        if not self.bone_list:
            return wx.NOT_FOUND
        return self.bone_list.GetSelection()

    def GetValues(self):
        return self.ctrl_x.GetValue(), self.ctrl_y.GetValue(), self.ctrl_z.GetValue()

