import wx


class TrimAnimDialog(wx.Dialog):
    def __init__(self, parent, frame_count, *args, **kw):
        super().__init__(parent, *args, **kw)

        self.SetTitle("Trim Animation")

        self.start_frame = wx.SpinCtrl(self, min=0, max=frame_count - 1, initial=0)
        self.end_frame = wx.SpinCtrl(self, min=1, max=frame_count, initial=frame_count)

        self.start_frame.Bind(wx.EVT_SPINCTRL, self.on_set_start_frame)
        self.end_frame.Bind(wx.EVT_SPINCTRL, self.on_set_end_frame)

        self.start_frame.SetFocus()

        ok_button = wx.Button(self, wx.ID_OK, "Ok")
        ok_button.SetDefault()
        cancel_button = wx.Button(self, wx.ID_CANCEL, "Cancel")

        grid_sizer = wx.FlexGridSizer(rows=2, cols=2, hgap=10, vgap=10)
        grid_sizer.Add(wx.StaticText(self, -1, 'Start Frame:'), 0, wx.CENTER)
        grid_sizer.Add(self.start_frame, 0, wx.ALIGN_RIGHT)
        grid_sizer.Add(wx.StaticText(self, -1, 'End Frame:'), 0, wx.CENTER)
        grid_sizer.Add(self.end_frame, 0, wx.ALIGN_RIGHT)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(grid_sizer, 1, wx.ALL, 10)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(ok_button, 0, wx.LEFT | wx.RIGHT, 2)
        button_sizer.Add(cancel_button, 0, wx.LEFT | wx.RIGHT, 5)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(hsizer, 1, wx.ALL, 10)
        sizer.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()

    def on_set_start_frame(self, _):
        self.end_frame.SetMin(self.start_frame.GetValue() + 1)

    def on_set_end_frame(self, _):
        self.start_frame.SetMax(self.end_frame.GetValue() - 1)

    def GetValues(self):
        return self.start_frame.GetValue(), self.end_frame.GetValue()
