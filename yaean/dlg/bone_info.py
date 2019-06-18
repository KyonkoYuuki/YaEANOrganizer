import wx
from wx.lib.agw.floatspin import FloatSpin, FS_LEFT, FS_READONLY
from pubsub import pub
from pyquaternion import Quaternion
from yaean.helpers import euler_to_quaternion, quaternion_to_euler


class BoneInfoDialog(wx.Dialog):
    def __init__(self, parent, filetype, filename, bone, read_only, *args, **kw):
        super().__init__(parent, *args, **kw)

        self.filetype = filetype
        self.SetTitle("Bone Info: " + bone.name)
        self.filename = filename
        self.bone = bone
        self.copied_bone_info = parent.copied_bone_info
        self.read_only = read_only

        if read_only:
            style = FS_LEFT | FS_READONLY
        else:
            style = FS_LEFT

        tool_sizer = wx.BoxSizer(wx.HORIZONTAL)
        if self.read_only:
            self.copy_text = wx.StaticText(self, -1, '')
            tool_sizer.Add(self.copy_text, 0, wx.TOP | wx.BOTTOM, 15)
            self.copy_button = wx.Button(self, -1, 'Copy')
            self.copy_button.Bind(wx.EVT_BUTTON, self.on_copy)
            tool_sizer.Add(self.copy_button, 0, wx.ALL, 10)

            if (filename, bone) == self.copied_bone_info:
                self.copy_button.Disable()
                self.copy_text.SetLabelText('Copied!')
        else:
            if self.copied_bone_info:
                label = '{} - {}: {}'.format(
                    self.copied_bone_info[0], self.copied_bone_info[1].index, self.copied_bone_info[1].name)
            else:
                label = ''
            self.paste_text = wx.StaticText(self, -1, label)
            tool_sizer.Add(self.paste_text, 0, wx.TOP | wx.BOTTOM, 15)
            self.paste_button = wx.Button(self, -1, 'Paste')
            self.paste_button.Bind(wx.EVT_BUTTON, self.on_paste)
            tool_sizer.Add(self.paste_button, 0, wx.ALL, 10)
            if not self.copied_bone_info:
                self.paste_button.Disable()

        position = bone.skinning_matrix[0]
        orientation = bone.skinning_matrix[1]
        scale = bone.skinning_matrix[2]

        self.offset_x = FloatSpin(self, -1, value=position[0], digits=8, increment=0.001, size=(150, -1), agwStyle=style)
        self.offset_y = FloatSpin(self, -1, value=position[1], digits=8, increment=0.001, size=(150, -1), agwStyle=style)
        self.offset_z = FloatSpin(self, -1, value=position[2], digits=8, increment=0.001, size=(150, -1), agwStyle=style)

        rot_x, rot_y, rot_z = quaternion_to_euler(Quaternion(orientation[3], orientation[0], orientation[1], orientation[2]))
        self.rotation_x = FloatSpin(self, -1, value=rot_x, digits=8, increment=1.0, size=(150, -1), agwStyle=style)
        self.rotation_y = FloatSpin(self, -1, value=rot_y, digits=8, increment=1.0, size=(150, -1), agwStyle=style)
        self.rotation_z = FloatSpin(self, -1, value=rot_z, digits=8, increment=1.0, size=(150, -1), agwStyle=style)

        self.scale_x = FloatSpin(self, -1, value=scale[0], digits=8, increment=0.01, size=(150, -1), agwStyle=style)
        self.scale_y = FloatSpin(self, -1, value=scale[1], digits=8, increment=0.01, size=(150, -1), agwStyle=style)
        self.scale_z = FloatSpin(self, -1, value=scale[2], digits=8, increment=0.01, size=(150, -1), agwStyle=style)

        position_sizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, 'Position')
        position_grid_sizer = wx.FlexGridSizer(rows=3, cols=2, hgap=5, vgap=20)
        position_grid_sizer.Add(wx.StaticText(self, -1, 'X:'), 0, wx.CENTER)
        position_grid_sizer.Add(self.offset_x, 0, wx.ALIGN_RIGHT)
        position_grid_sizer.Add(wx.StaticText(self, -1, 'Y:'), 0, wx.CENTER)
        position_grid_sizer.Add(self.offset_y, 0, wx.ALIGN_RIGHT)
        position_grid_sizer.Add(wx.StaticText(self, -1, 'Z:'), 0, wx.CENTER)
        position_grid_sizer.Add(self.offset_z, 0, wx.ALIGN_RIGHT)
        position_sizer.Add(position_grid_sizer, 0, wx.ALL, 10)

        orientation_sizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, 'Orientation')
        orientation_grid_sizer = wx.FlexGridSizer(rows=3, cols=2, hgap=5, vgap=20)
        orientation_grid_sizer.Add(wx.StaticText(self, -1, 'X:'), 0, wx.CENTER)
        orientation_grid_sizer.Add(self.rotation_x, 0, wx.ALIGN_RIGHT)
        orientation_grid_sizer.Add(wx.StaticText(self, -1, 'Y:'), 0, wx.CENTER)
        orientation_grid_sizer.Add(self.rotation_y, 0, wx.ALIGN_RIGHT)
        orientation_grid_sizer.Add(wx.StaticText(self, -1, 'Z:'), 0, wx.CENTER)
        orientation_grid_sizer.Add(self.rotation_z, 0, wx.ALIGN_RIGHT)
        orientation_sizer.Add(orientation_grid_sizer, 0, wx.ALL, 10)

        scale_sizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, 'Scale')
        scale_grid_sizer = wx.FlexGridSizer(rows=3, cols=2, hgap=5, vgap=20)
        scale_grid_sizer.Add(wx.StaticText(self, -1, 'X:'), 0, wx.CENTER)
        scale_grid_sizer.Add(self.scale_x, 0, wx.ALIGN_RIGHT)
        scale_grid_sizer.Add(wx.StaticText(self, -1, 'Y:'), 0, wx.CENTER)
        scale_grid_sizer.Add(self.scale_y, 0, wx.ALIGN_RIGHT)
        scale_grid_sizer.Add(wx.StaticText(self, -1, 'Z:'), 0, wx.CENTER)
        scale_grid_sizer.Add(self.scale_z, 0, wx.ALIGN_RIGHT)
        scale_sizer.Add(scale_grid_sizer, 0, wx.ALL, 10)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(self, wx.ID_OK, "Ok")
        ok_button.Bind(wx.EVT_BUTTON, self.on_close)
        ok_button.SetDefault()
        button_sizer.Add(ok_button)
        if not self.read_only:
            cancel_button = wx.Button(self, wx.ID_CANCEL, "Cancel")
            cancel_button.Bind(wx.EVT_BUTTON, self.on_close)
            button_sizer.AddSpacer(10)
            button_sizer.Add(cancel_button)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.AddSpacer(10)
        hsizer.Add(position_sizer, 0, wx.ALL, 10)
        hsizer.Add(orientation_sizer, 0, wx.ALL, 10)
        hsizer.Add(scale_sizer, 0, wx.ALL, 10)
        hsizer.AddSpacer(10)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(tool_sizer, 0, wx.ALIGN_RIGHT, 10)
        sizer.Add(hsizer, 0, wx.EXPAND, 10)
        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, 10)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()

    def on_close(self, e):
        if not self.read_only and e.GetId() == wx.ID_OK:
            q = euler_to_quaternion(self.rotation_x.GetValue(), self.rotation_y.GetValue(), self.rotation_z.GetValue())
            self.bone.skinning_matrix[0][0] = self.offset_x.GetValue()
            self.bone.skinning_matrix[0][1] = self.offset_y.GetValue()
            self.bone.skinning_matrix[0][2] = self.offset_z.GetValue()
            self.bone.skinning_matrix[1][0] = q.x
            self.bone.skinning_matrix[1][1] = q.y
            self.bone.skinning_matrix[1][2] = q.z
            self.bone.skinning_matrix[1][3] = q.w
            self.bone.skinning_matrix[2][0] = self.scale_x.GetValue()
            self.bone.skinning_matrix[2][1] = self.scale_y.GetValue()
            self.bone.skinning_matrix[2][2] = self.scale_z.GetValue()
        e.Skip()

    def on_copy(self, e):
        self.copy_button.Disable()
        self.copy_text.SetLabelText('Copied!')
        self.Layout()
        pub.sendMessage('copy_bone_info', filename=self.filename, bone=self.bone)

    def on_paste(self, e):
        bone = self.copied_bone_info[1]
        position = bone.skinning_matrix[0]
        orientation = bone.skinning_matrix[1]
        scale = bone.skinning_matrix[2]

        self.offset_x.SetValue(position[0])
        self.offset_y.SetValue(position[1])
        self.offset_z.SetValue(position[2])

        rot_x, rot_y, rot_z = quaternion_to_euler(
            Quaternion(orientation[3], orientation[0], orientation[1], orientation[2]))
        self.rotation_x.SetValue(rot_x)
        self.rotation_y.SetValue(rot_y)
        self.rotation_z.SetValue(rot_z)

        self.scale_x.SetValue(scale[0])
        self.scale_y.SetValue(scale[1])
        self.scale_z.SetValue(scale[2])
