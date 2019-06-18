import wx
from yaean.helpers import POSITION_FLAG, ORIENTATION_FLAG, SCALE_FLAG

FLAGS = [POSITION_FLAG, ORIENTATION_FLAG, SCALE_FLAG]


class RemoveKeyframesDialog(wx.Dialog):
    def __init__(self, parent, *args, **kw):
        super().__init__(parent, *args, **kw)

        self.SetSize((250, 250))
        self.SetTitle("Remove Keyframes from Animation")

        self.checkboxes = []
        self.checkboxes.append(wx.CheckBox(self, -1, 'Position'))
        self.checkboxes.append(wx.CheckBox(self, -1, 'Orientation'))
        self.checkboxes.append(wx.CheckBox(self, -1, 'Scale'))

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(self.checkboxes[0], 0, wx.ALL, 10)
        hsizer.Add(self.checkboxes[1], 0, wx.ALL, 10)
        hsizer.Add(self.checkboxes[2], 0, wx.ALL, 10)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(wx.Button(self, wx.ID_OK, "Ok"), 0, wx.LEFT | wx.RIGHT, 2)
        button_sizer.Add(wx.Button(self, wx.ID_CANCEL, "Cancel"), 0, wx.LEFT | wx.RIGHT, 5)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(hsizer, 0, wx.ALL, 10)
        sizer.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(button_sizer, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, 10)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()

    def GetValues(self):
        return [flag for i, flag in enumerate(FLAGS) if self.checkboxes[i].GetValue()]
