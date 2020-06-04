import pickle

import wx
from wx.lib.dialogs import MultiMessageDialog
from pubsub import pub
from pyquaternion import Quaternion

from pyxenoverse.ean.animation import Animation
from pyxenoverse.ean.keyframed_animation import KeyframedAnimation
from pyxenoverse.ean.keyframe import Keyframe

from yaean.dlg.remove_keyframes import RemoveKeyframesDialog
from yaean.dlg.trim_anim import TrimAnimDialog
from yaean.dlg.transform import TransformDialog
from pyxenoverse.gui.file_drop_target import FileDropTarget
from yaean.helpers import (
    enable_selected, get_selected_items, get_unique_name, rename, euler_to_quaternion,
    POSITION_FLAG, ORIENTATION_FLAG, SCALE_FLAG, TARGET_CAMERA_POSITION_FLAG
)


class AnimMainPanel(wx.Panel):
    def __init__(self, parent, root):
        wx.Panel.__init__(self, parent)
        self.parent = parent.GetParent().GetParent()
        self.root = root
        self.copied_animations = None

        self.is_camera = False

        # Name
        self.name = wx.StaticText(self, -1, '(No file loaded)')
        self.font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.name.SetFont(self.font)

        # Buttons
        self.open = wx.Button(self, wx.ID_OPEN, "Load")
        self.save = wx.Button(self, wx.ID_SAVE, "Save")
        self.edit = wx.Button(self, wx.ID_EDIT, "Edit")

        # AnimList
        self.anim_list = wx.ListCtrl(self, style=wx.LC_REPORT)
        self.anim_list.InsertColumn(0, "#", width=30)
        self.anim_list.InsertColumn(1, "Animation", width=200)
        self.anim_list.InsertColumn(2, "Frames", width=50)
        self.anim_list.SetDropTarget(FileDropTarget(self, "load_main_file"))
        self.anim_list.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_right_click)

        # Bind
        self.Bind(wx.EVT_BUTTON, self.on_open, id=wx.ID_OPEN)
        self.Bind(wx.EVT_BUTTON, self.on_save, id=wx.ID_SAVE)
        self.Bind(wx.EVT_BUTTON, self.on_right_click, id=wx.ID_EDIT)

        # Select All
        self.insert_id = wx.NewId()
        self.append_id = wx.NewId()
        self.rename_id = wx.NewId()
        self.duration_id = wx.NewId()
        self.offset_id = wx.NewId()
        self.rotation_id = wx.NewId()
        self.scale_id = wx.NewId()
        self.trim_anim_id = wx.NewId()
        self.mirror_anim_id = wx.NewId()
        self.reverse_anim_id = wx.NewId()
        self.remove_keyframes_id = wx.NewId()
        self.target_camera_offset_id = wx.NewId()
        self.Bind(wx.EVT_MENU, self.on_open, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.on_save, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.select_all, id=wx.ID_SELECTALL)
        self.Bind(wx.EVT_MENU, self.on_delete, id=wx.ID_DELETE)
        self.Bind(wx.EVT_MENU, self.on_insert, id=self.insert_id)
        self.Bind(wx.EVT_MENU, self.on_append, id=self.append_id)
        self.Bind(wx.EVT_MENU, self.on_paste, id=wx.ID_PASTE)
        self.Bind(wx.EVT_MENU, self.on_rename, id=self.rename_id)
        self.Bind(wx.EVT_MENU, self.on_set_duration, id=self.duration_id)
        self.Bind(wx.EVT_MENU, self.on_set_offset, id=self.offset_id)
        self.Bind(wx.EVT_MENU, self.on_set_rotation, id=self.rotation_id)
        self.Bind(wx.EVT_MENU, self.on_set_scale, id=self.scale_id)
        self.Bind(wx.EVT_MENU, self.on_trim_anim, id=self.trim_anim_id)
        self.Bind(wx.EVT_MENU, self.on_mirror_anim, id=self.mirror_anim_id)
        self.Bind(wx.EVT_MENU, self.on_reverse_anim, id=self.reverse_anim_id)
        self.Bind(wx.EVT_MENU, self.on_remove_keyframes, id=self.remove_keyframes_id)
        self.Bind(wx.EVT_MENU, self.on_set_target_camera_offset, id=self.target_camera_offset_id)
        accelerator_table = wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord('a'), wx.ID_SELECTALL),
            (wx.ACCEL_CTRL, ord('v'), wx.ID_PASTE),
            (wx.ACCEL_NORMAL, wx.WXK_DELETE, wx.ID_DELETE),
            (wx.ACCEL_NORMAL, wx.WXK_F2, self.rename_id)
        ])
        self.anim_list.SetAcceleratorTable(accelerator_table)
        pub.subscribe(self.copy_animation, 'copy_animation')

        # Button Sizer
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.button_sizer.Add(self.open)
        self.button_sizer.AddSpacer(5)
        self.button_sizer.Add(self.save)
        self.button_sizer.AddSpacer(5)
        self.button_sizer.Add(self.edit)

        # Use some sizers to see layout options
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.name, 0, wx.CENTER)
        self.sizer.Add(self.button_sizer)
        self.sizer.Add(self.anim_list, 1, wx.EXPAND)

        # Layout sizers
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)

    def on_open(self, _):
        pub.sendMessage('open_main_file')

    def on_save(self, _):
        pub.sendMessage('save_ean')

    def copy_animation(self, copied_animations):
        self.copied_animations = pickle.dumps(copied_animations)

    def select_all(self, _):
        for i in range(self.anim_list.GetItemCount()):
            self.anim_list.Select(i)

    def enable_copy_animation(self, menu_item, selected, single=False):
        if not self.copied_animations:
            menu_item.Enable(False)
            return
        enable_selected(menu_item, selected, single)

    def on_right_click(self, _):
        selected = list(get_selected_items(self.anim_list))
        menu = wx.Menu()
        menu.Append(wx.ID_SELECTALL, "&Select All\tCtrl+A", " Select all animations")
        delete = menu.Append(wx.ID_DELETE, "&Delete\tDelete", " Delete selected animation(s)")
        enable_selected(delete, selected)
        insert = menu.Append(self.insert_id, "&Insert", " Insert copied animation")
        self.enable_copy_animation(insert, selected)
        append = menu.Append(self.append_id, "&Append", " Append copied animation")
        self.enable_copy_animation(append, selected)
        paste = menu.Append(wx.ID_PASTE, "&Paste\tCtrl+V", " Paste copied animation")
        self.enable_copy_animation(paste, selected)
        rename = menu.Append(self.rename_id, "&Rename\tF2", " Rename selected animation")
        enable_selected(rename, selected)
        menu.AppendSeparator()
        set_duration = menu.Append(self.duration_id, "Set &Duration", " Set duration on selected animation")
        enable_selected(set_duration, selected)
        offset = menu.Append(self.offset_id, "Set O&ffset", " Change offset of bones in an animation")
        enable_selected(offset, selected)
        rotation = menu.Append(self.rotation_id, "Set R&otation", " Change animation rotation")
        enable_selected(rotation, selected)
        scale = menu.Append(self.scale_id, "Set &Scale", " Change scale of bones in an animation")
        enable_selected(scale, selected)
        menu.AppendSeparator()
        trim_anim = menu.Append(self.trim_anim_id, "&Trim Animation", " Trim off frames from an animation")
        enable_selected(trim_anim, selected, True)
        mirror_anim = menu.Append(self.mirror_anim_id, "&Mirror Animation", " Mirror animation L/R")
        enable_selected(mirror_anim, selected)
        reverse_anim = menu.Append(self.reverse_anim_id, "Re&verse Animation", " Reverse animation")
        enable_selected(reverse_anim, selected)
        remove_keyframes = menu.Append(self.remove_keyframes_id,
                                       "Remove &Keyframes", " Removes keyframe data of bones from an animation")
        enable_selected(remove_keyframes, selected)
        menu.AppendSeparator()
        target_camera_offset = menu.Append(self.target_camera_offset_id, "Set Target &Camera Offset",
                                           " Change offset of target camera (for cam.ean files)")
        enable_selected(target_camera_offset, selected)

        self.PopupMenu(menu)
        menu.Destroy()

    def reindex(self):
        for i in range(self.anim_list.GetItemCount()):
            self.anim_list.SetItem(i, 0, str(i))

    def get_bones(self):
        bones = []
        bone_list = self.root.main['ean_bone_list']
        item = bone_list.GetFirstItem()
        while item.IsOk():
            bones.append(bone_list.GetItemText(item))
            item = bone_list.GetNextItem(item)
        return bones

    def add_animation(self, append):
        selected = list(get_selected_items(self.anim_list))
        if not selected or not self.copied_animations:
            return
        copied_animations = pickle.loads(self.copied_animations)

        for i in selected:
            self.anim_list.Select(i, 0)

        index = selected[0]
        if append:
            index = selected[-1] + 1

        names = [animation.name for animation in self.root.main['ean'].animations]
        for i, copied_animation in enumerate(copied_animations):
            dst_index = index + i
            animation = Animation(self.root.main['ean'])
            animation.paste(copied_animation)
            animation = get_unique_name(animation, names)
            self.root.main['ean'].animations.insert(dst_index, animation)
            self.anim_list.InsertItem(dst_index, str(dst_index))
            self.anim_list.SetItem(dst_index, 1, animation.name)
            self.anim_list.SetItem(dst_index, 2, str(animation.frame_count))
            self.anim_list.Select(dst_index)
        self.reindex()
        self.root.SetStatusText("Added {} animation(s)".format(len(copied_animations)))

    def on_append(self, _):
        self.add_animation(True)

    def on_insert(self, _):
        self.add_animation(False)

    def on_delete(self, _):
        selected = list(get_selected_items(self.anim_list))
        if not selected:
            return
        self.root.SetStatusText("Deleting...")
        for i in reversed(selected):
            self.root.main['ean'].remove_animation(i)
            self.anim_list.DeleteItem(i)
        self.reindex()
        self.root.SetStatusText("Deleted {} animation(s)".format(len(selected)))

    def on_paste(self, _):
        selected = list(get_selected_items(self.anim_list))
        if not self.copied_animations or not selected:
            return
        copied_animations = pickle.loads(self.copied_animations)
        bone_list = self.root.main['ean_bone_list']

        # Expand/truncate selection
        selected = selected[:len(copied_animations)]
        difference = len(copied_animations) - len(selected)
        if difference:
            last_index = selected[-1]
            selected.extend(list(range(last_index+1, last_index + difference + 1)))
        for i in range(self.anim_list.GetItemCount()):
            self.anim_list.Select(i, i in selected)

        bone_filters = set()
        item = bone_list.GetFirstItem()
        while item.IsOk():
            if bone_list.GetCheckedState(item) != wx.CHK_UNCHECKED:
                bone_filters.add(bone_list.GetItemData(item).name)
            item = bone_list.GetNextItem(item)

        # Warn if multiple animations are being copied
        if len(copied_animations) > 1:
            changed_animations = ''
            for i, animation in enumerate(copied_animations):
                changed_animations += ' * '
                dst_index = selected[i]
                if dst_index < len(self.root.main['ean'].animations):
                    changed_animations += self.root.main['ean'].animations[dst_index].name
                changed_animations += ' -> {}\n'.format(animation.name)
            with wx.MessageDialog(
                    self, "You are about to change multiple animations. Are you sure you want to do that?\n"
                          + changed_animations, "Warning", wx.YES | wx.NO) as dlg:
                if dlg.ShowModal() != wx.ID_YES:
                    return

        skipped_nodes = set()

        # Add missing bones
        bone_filters.update(self.root.main['ean_bone_panel'].add_missing_bones())

        # Do the copying
        names = [animation.name for animation in self.root.main['ean'].animations]
        for i, copied_animation in enumerate(copied_animations):
            dst_index = selected[i]
            if dst_index < len(self.root.main['ean'].animations):
                animation = self.root.main['ean'].animations[dst_index]
                skipped_nodes.update(animation.paste(copied_animation, bone_filters, True))
            else:
                animation = Animation(self.root.main['ean'])
                animation.frame_float_size = copied_animation.frame_float_size
                skipped_nodes.update(animation.paste(copied_animation))
                animation = get_unique_name(animation, names)
                self.root.main['ean'].animations.append(animation)
                self.anim_list.InsertItem(dst_index, str(dst_index))
                self.anim_list.SetItem(dst_index, 1, animation.name)
            self.anim_list.SetItem(dst_index, 2, str(animation.frame_count))
            self.anim_list.Select(dst_index)
        self.reindex()
        pasted_msg = "Pasted {} animation(s)".format(len(copied_animations))
        self.root.SetStatusText(pasted_msg)

        msg = ''
        if skipped_nodes:
            skipped_list = '\n'.join([' * ' + node for node in sorted(skipped_nodes)])
            msg = 'The following animation nodes were skipped:\n' + skipped_list
        with MultiMessageDialog(self, pasted_msg, "Warning", msg, wx.OK) as dlg:
            dlg.ShowModal()

    def on_rename(self, _):
        def rename_func(item, animation, old_name, new_name):
            self.anim_list.SetItem(item, 1, new_name)

        selected = list(get_selected_items(self.anim_list))
        if not selected:
            return
        animations = [self.root.main['ean'].animations[i] for i in selected]
        names = [animation.name for animation in self.root.main['ean'].animations]
        rename(self.root, 'animations', animations, names, selected, rename_func)

    def on_set_duration(self, _):
        selected = list(get_selected_items(self.anim_list))
        if not selected:
            return
        animations = [self.root.main['ean'].animations[i] for i in selected]
        old_duration = animations[0].frame_count

        with wx.TextEntryDialog(self, 'Enter new duration in frames (60 frames = 1.0s):', 'Set Duration') as dlg:
            dlg.SetValue(str(old_duration))
            if dlg.ShowModal() == wx.ID_OK:
                new_duration = int(dlg.GetValue())
                for i, animation in enumerate(animations):
                    animation.set_duration(target_duration=new_duration)
                    self.anim_list.SetItem(selected[i], 2, str(new_duration))
                if len(animations) > 1:
                    self.root.SetStatusText("Set duration for {} animations to {} ({:.2f}s)".format(
                        len(animations), new_duration, new_duration / 60.0))
                else:
                    self.root.SetStatusText("Set {} duration to {} ({:.2f}s)".format(
                        animations[0].name, new_duration, new_duration / 60.0))

    def transform(self, selected, bone_index, flag, found_func, w, x, y, z):
        animations = [self.root.main['ean'].animations[i] for i in selected]
        msg = ''
        animations_changed = len(selected)
        for animation in animations:
            for node in animation.nodes:
                if node.bone_index == bone_index:
                    for keyframed_animation in node.keyframed_animations:
                        if keyframed_animation.flag == flag:
                            for keyframe in keyframed_animation.keyframes:
                                found_func(keyframe, w, x, y, z)
                            break
                    else:
                        keyframed_animation = KeyframedAnimation()
                        keyframed_animation.flag = flag
                        keyframed_animation.keyframes.append(Keyframe(0, w, x, y, z))
                        keyframed_animation.keyframes.append(Keyframe(animation.frame_count - 1, w, x, y, z))
                        node.keyframed_animations.append(keyframed_animation)
                    break
            else:
                msg += ' * {}\n'.format(animation.name)
                animations_changed -= 1
        if msg:
            with MultiMessageDialog(self, 'Skipped animations:', "Warning", msg, wx.OK) as dlg:
                dlg.ShowModal()
        self.root.SetStatusText("Edited {} animation(s)".format(len(selected)))

    def on_set_offset(self, _):
        def offset_func(keyframe, _, x, y, z):
            keyframe.x += x
            keyframe.y += y
            keyframe.z += z
        selected = list(get_selected_items(self.anim_list))
        if not selected:
            return
        with TransformDialog(self, 'Offset', selected, self.get_bones()) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.transform(selected, dlg.GetBoneIndex(), POSITION_FLAG, offset_func, 1, *dlg.GetValues())

    def on_set_scale(self, _):
        def scale_func(keyframe, _, x, y, z):
            keyframe.x += x
            keyframe.y += y
            keyframe.z += z
        selected = list(get_selected_items(self.anim_list))
        if not selected:
            return
        with TransformDialog(self, 'Scale', selected, self.get_bones()) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.transform(selected, dlg.GetBoneIndex(), SCALE_FLAG, scale_func, 1, *dlg.GetValues())

    def on_set_rotation(self, _):
        def rotate_func(keyframe, w, x, y, z):
            rq = Quaternion(w, x, y, z)
            kq = Quaternion(keyframe.w, keyframe.x, keyframe.y, keyframe.z)
            keyframe.w, keyframe.x, keyframe.y, keyframe.z = kq * rq
        selected = list(get_selected_items(self.anim_list))
        if not selected:
            return
        with TransformDialog(self, 'Rotation', selected, self.get_bones()) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.transform(
                    selected, dlg.GetBoneIndex(), ORIENTATION_FLAG, rotate_func, *euler_to_quaternion(*dlg.GetValues()))

    def on_set_target_camera_offset(self, _):
        selected = list(get_selected_items(self.anim_list))
        if not selected:
            return
        with TransformDialog(self, 'Target Camera Offset', selected, None) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                offset_x, offset_y, offset_z = dlg.GetValues()
                animations = [self.root.main['ean'].animations[i] for i in selected]
                changed = 0
                for animation in animations:
                    for node in animation.nodes:
                        for keyframed_animation in node.keyframed_animations:
                            if keyframed_animation.flag != TARGET_CAMERA_POSITION_FLAG:
                                continue
                            changed += 1
                            for keyframe in keyframed_animation.keyframes:
                                keyframe.x = keyframe.x + offset_x
                                keyframe.y = keyframe.y + offset_y
                                keyframe.z = keyframe.z + offset_z
                self.root.SetStatusText("Edited {} Target Camera Position".format(changed))

    def on_remove_keyframes(self, _):
        selected = list(get_selected_items(self.anim_list))
        if not selected:
            return
        frame_count = None
        if len(selected) == 1:
            frame_count = int(self.anim_list.GetItem(selected[0], 2).GetText())
        with RemoveKeyframesDialog(self, frame_count) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                flags, start_frame, end_frame = dlg.GetValues()
                animations = [self.root.main['ean'].animations[i] for i in selected]
                bone_filters = []
                item = self.root.main['ean_bone_list'].GetFirstItem()
                while item.IsOk():
                    if self.root.main['ean_bone_list'].GetCheckedState(item) != wx.CHK_UNCHECKED:
                        bone_filters.append(self.root.main['ean_bone_list'].GetItemData(item).index)
                    item = self.root.main['ean_bone_list'].GetNextItem(item)

                removed_keyframed_animations = 0
                for animation in animations:
                    for node in animation.nodes:
                        if node.bone_index not in bone_filters:
                            continue
                        keyframed_animations = []
                        for keyframed_animation in node.keyframed_animations:
                            if keyframed_animation.flag not in flags:
                                keyframed_animations.append(keyframed_animation)
                            else:
                                if not frame_count or (start_frame == 0 and end_frame == frame_count):
                                    removed_keyframed_animations += 1
                                else:
                                    new_keyframes = []
                                    for keyframe in keyframed_animation.keyframes:
                                        if keyframe.frame < start_frame or keyframe.frame >= end_frame:
                                            new_keyframes.append(keyframe)
                                    keyframed_animation.keyframes = new_keyframes
                                    keyframed_animations.append(keyframed_animation)

                        node.keyframed_animations = keyframed_animations

                self.root.SetStatusText("Removed {} keyframed animation(s) from {} animation(s)".format(
                    removed_keyframed_animations, len(animations)))

    def on_trim_anim(self, _):
        selected = list(get_selected_items(self.anim_list))
        if not selected:
            return
        self.anim_list.Select(selected[0])
        frame_count = int(self.anim_list.GetItem(selected[0], 2).GetText())
        animation = self.root.main['ean'].animations[selected[0]]
        with TrimAnimDialog(self, frame_count, selected[0]) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                start_frame, end_frame = dlg.GetValues()
                animation.set_duration(start_frame=start_frame, end_frame=end_frame)
                self.anim_list.SetItem(selected[0], 2, str(animation.frame_count))
                self.root.SetStatusText("Changed animation to start from frame {} and end on frame {}".format(
                    start_frame, end_frame))

    def on_mirror_anim(self, _):
        selected = list(get_selected_items(self.anim_list))
        if not selected:
            return
        animations = [self.root.main['ean'].animations[i] for i in selected]
        animations_changed = len(animations)

        exclude_base = False
        with wx.MessageDialog(self, 'Exclude b_C_Base?', 'Mirror Animation', wx.YES | wx.NO) as dlg:
            if dlg.ShowModal() == wx.ID_YES:
                exclude_base = True

        # Swap left and right
        for animation in animations:
            for node in animation.nodes:
                bone_name_parts = node.bone_name.split('_')

                # Swap left and right animations first
                if bone_name_parts[1] == 'R':
                    bone_name_parts[1] = 'L'
                    node.bone_name = '_'.join(bone_name_parts)
                elif bone_name_parts[1] == 'L':
                    bone_name_parts[1] = 'R'
                    node.bone_name = '_'.join(bone_name_parts)
                if node.bone_index == -1:
                    with wx.MessageDialog(self, "Cannot mirror. Couldn't find matching L/R bones", "Error") as dlg:
                        dlg.ShowModal()
                    return

        # Then we can go and do the math
        for animation in animations:
            for node in animation.nodes:
                if exclude_base and node.bone_name == 'b_C_Base':
                    continue
                for keyframed_animation in node.keyframed_animations:
                    if keyframed_animation.flag == POSITION_FLAG:
                        for keyframe in keyframed_animation.keyframes:
                            keyframe.x *= -1.0
                    elif keyframed_animation.flag == ORIENTATION_FLAG:
                        for keyframe in keyframed_animation.keyframes:
                            keyframe.y *= -1.0
                            keyframe.z *= -1.0

        self.root.SetStatusText(f"Mirrored {animations_changed} animations")

    def on_reverse_anim(self, _):
        selected = list(get_selected_items(self.anim_list))
        if not selected:
            return
        animations = [self.root.main['ean'].animations[i] for i in selected]
        animations_changed = len(animations)

        for animation in animations:
            for node in animation.nodes:
                for keyframed_animation in node.keyframed_animations:
                    # In case we run into some keyframes created by old programs
                    last_frame = keyframed_animation.keyframes[-1].frame
                    keyframed_animation.keyframes.reverse()
                    for keyframe in keyframed_animation.keyframes:
                        keyframe.frame = last_frame - keyframe.frame

        self.root.SetStatusText(f"Reversed {animations_changed} animations")
