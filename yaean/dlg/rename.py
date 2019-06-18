import wx


class RenameDialog(wx.Dialog):
    def __init__(self, parent, old_name, names, *args, **kw):
        super().__init__(parent, *args, **kw)
        self.name_ctrl = wx.TextCtrl(self, wx.ID_OK, old_name, size=(300, -1), style=wx.TE_PROCESS_ENTER)
        self.name_ctrl.Bind(wx.EVT_TEXT_ENTER, self.on_close)
        self.name_ctrl.SetFocus()
        self.old_name = old_name
        self.names = names
        self.SetTitle("Rename " + old_name)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self, -1, 'Enter new name:'), 0, wx.LEFT | wx.ALL, 10)
        sizer.Add(self.name_ctrl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 15)
        sizer.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.ALL, 10)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.Button(self, wx.ID_OK, "Ok"), 0, wx.LEFT | wx.RIGHT, 2)
        hsizer.Add(wx.Button(self, wx.ID_CANCEL, "Cancel"), 0, wx.LEFT | wx.RIGHT, 5)

        sizer.Add(hsizer, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, 10)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()
        self.Bind(wx.EVT_BUTTON, self.on_close)

    def on_close(self, e):
        if e.GetId() == wx.ID_OK:
            new_name = self.GetValue()
            if new_name in self.names and new_name != self.old_name:
                with wx.MessageDialog(self, '{} already exists, please pick a different name'.format(new_name), 'Warning') as dlg:
                    dlg.ShowModal()
                return
        self.EndModal(e.GetId())

    def GetValue(self):
        return self.name_ctrl.GetValue()
