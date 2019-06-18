import re
import wx


class MultiRenameDialog(wx.Dialog):
    def __init__(self, parent, *args, **kw):
        super().__init__(parent, *args, **kw)
        self.SetTitle("Bulk Rename")
        self.saved_fields = [('', ''), ('', ''), ('', '')]
        self.current_choice = 0

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.radio_box = wx.RadioBox(self, choices=['Replace', 'Add', 'Regex'])
        self.radio_box.Bind(wx.EVT_RADIOBOX, self.on_radio_change)
        sizer.Add(self.radio_box, 0, wx.ALL, 10)

        self.top_label = wx.StaticText(self, -1, 'Replace: ')
        self.top_ctrl = wx.TextCtrl(self, wx.ID_OK, '', size=(300, -1), style=wx.TE_PROCESS_ENTER)
        self.top_ctrl.Bind(wx.EVT_TEXT_ENTER, self.on_close)
        self.top_ctrl.SetFocus()
        self.bot_label = wx.StaticText(self, -1, 'With: ')
        self.bot_ctrl = wx.TextCtrl(self, wx.ID_OK, '', size=(300, -1), style=wx.TE_PROCESS_ENTER)
        self.bot_ctrl.Bind(wx.EVT_TEXT_ENTER, self.on_close)

        grid_sizer = wx.FlexGridSizer(rows=2, cols=2, hgap=10, vgap=10)
        grid_sizer.Add(self.top_label)
        grid_sizer.Add(self.top_ctrl)
        grid_sizer.Add(self.bot_label)
        grid_sizer.Add(self.bot_ctrl)
        sizer.Add(grid_sizer, 0, wx.ALL, 10)

        self.match_case = wx.CheckBox(self, label="Match Case")
        sizer.Add(self.match_case, 0, wx.ALL, 10)

        sizer.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.ALL, 10)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.Button(self, wx.ID_OK, "Ok"), 0, wx.LEFT | wx.RIGHT, 2)
        hsizer.Add(wx.Button(self, wx.ID_CANCEL, "Cancel"), 0, wx.LEFT | wx.RIGHT, 5)
        sizer.Add(hsizer, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, 10)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()
        self.Bind(wx.EVT_BUTTON, self.on_close)

    def GetPattern(self):
        if self.match_case.GetValue():
            flag = 0
        else:
            flag = re.IGNORECASE
        if self.current_choice == 0:
            return re.compile(self.top_ctrl.GetValue(), flag)
        elif self.current_choice == 1:
            return re.compile(r'(.+)')
        else:
            return re.compile(self.top_ctrl.GetValue(), flag)

    def GetReplace(self):
        if self.current_choice == 0:
            return self.bot_ctrl.GetValue()
        elif self.current_choice == 1:
            return r'{}\g<1>{}'.format(self.top_ctrl.GetValue(), self.bot_ctrl.GetValue())
        else:
            return self.bot_ctrl.GetValue()

    def on_radio_change(self, e):
        choice = self.radio_box.GetSelection()
        self.saved_fields[self.current_choice] = (self.top_ctrl.GetValue(), self.bot_ctrl.GetValue())
        self.top_ctrl.SetValue(self.saved_fields[choice][0])
        self.bot_ctrl.SetValue(self.saved_fields[choice][1])
        self.current_choice = choice
        if choice == 0:
            self.top_label.SetLabelText('Replace: ')
            self.bot_label.SetLabelText('With: ')
        elif choice == 1:
            self.top_label.SetLabelText('Prefix: ')
            self.bot_label.SetLabelText('Suffix: ')
        else:
            self.top_label.SetLabelText('Match: ')
            self.bot_label.SetLabelText('Replace: ')

    def on_close(self, e):
        self.EndModal(e.GetId())

