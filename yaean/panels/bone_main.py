from functools import partial
import pickle

import wx
import wx.dataview
from wx.lib.dialogs import MultiMessageDialog
from pubsub import pub

from pyxenoverse.esk.bone import Bone
from yaean.helpers import FILTERS, enable_selected, get_unique_name, rename, get_bone_tree
from yaean.dlg.add_bones import AddMissingBonesDialog
from yaean.dlg.bone_info import BoneInfoDialog
from pyxenoverse.gui.file_drop_target import FileDropTarget


class BoneMainPanel(wx.Panel):
    def __init__(self, parent, root, filetype):
        wx.Panel.__init__(self, parent)
        self.root = root
        self.filetype = filetype
        self.copied_bones = None
        if self.filetype == 'EAN':
            style = wx.dataview.TL_CHECKBOX | wx.dataview.TL_MULTIPLE | wx.dataview.TL_3STATE
        else:
            style = wx.dataview.TL_MULTIPLE

        # Name
        self.name = wx.StaticText(self, -1, '(No file loaded)')
        self.font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.name.SetFont(self.font)

        # Buttons
        self.open = wx.Button(self, wx.ID_OPEN, "Load")
        self.save = wx.Button(self, wx.ID_SAVE, "Save")
        self.edit = wx.Button(self, wx.ID_EDIT, "Edit")

        self.info = wx.Button(self, wx.ID_INFO, "Info")
        self.info.SetToolTip(wx.ToolTip("Get current pyxenoverse info"))
        self.info.Disable()

        self.bone_list = wx.dataview.TreeListCtrl(self, style=style)
        self.bone_list.AppendColumn("Bone")
        self.bone_list.Bind(wx.dataview.EVT_TREELIST_ITEM_CHECKED, self.on_checked)
        self.bone_list.Bind(wx.dataview.EVT_TREELIST_ITEM_CONTEXT_MENU, self.on_right_click)
        self.bone_list.Bind(wx.dataview.EVT_TREELIST_SELECTION_CHANGED, self.on_select)
        self.bone_list.SetDropTarget(FileDropTarget(self, "load_main_file"))

        # Binds
        self.Bind(wx.EVT_BUTTON, self.on_open, id=wx.ID_OPEN)
        self.Bind(wx.EVT_BUTTON, self.on_save, id=wx.ID_SAVE)
        self.Bind(wx.EVT_BUTTON, self.on_right_click, id=wx.ID_EDIT)
        self.Bind(wx.EVT_BUTTON, self.on_info, id=wx.ID_INFO)

        # Select All
        self.rename_id = wx.NewId()
        self.Bind(wx.EVT_MENU, self.toggle_select_all, id=wx.ID_SELECTALL)
        self.Bind(wx.EVT_MENU, self.on_paste, id=wx.ID_PASTE)
        self.Bind(wx.EVT_MENU, self.on_info, id=wx.ID_INFO)
        self.Bind(wx.EVT_MENU, self.on_delete, id=wx.ID_DELETE)
        self.Bind(wx.EVT_MENU, self.on_rename, id=self.rename_id)
        accelerator_table = wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord('a'), wx.ID_SELECTALL),
            (wx.ACCEL_CTRL, ord('i'), wx.ID_INFO),
            (wx.ACCEL_CTRL, ord('v'), wx.ID_PASTE),
            (wx.ACCEL_NORMAL, wx.WXK_DELETE, wx.ID_DELETE),
            (wx.ACCEL_NORMAL, wx.WXK_F2, self.rename_id),
        ])
        self.bone_list.SetAcceleratorTable(accelerator_table)
        pub.subscribe(self.copy_bones, 'copy_bones')

        # Use some sizers to see layout options
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.button_sizer.Add(self.open)
        self.button_sizer.AddSpacer(5)
        self.button_sizer.Add(self.save)
        self.button_sizer.AddSpacer(5)
        self.button_sizer.Add(self.edit)
        self.button_sizer.AddSpacer(5)
        self.button_sizer.Add(self.info)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.name, 0, wx.CENTER)
        self.sizer.Add(self.button_sizer)
        self.sizer.Add(self.bone_list, 1, wx.EXPAND)

        # Layout sizers
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)

    def check_parent(self, bone):
        parent = self.bone_list.GetItemParent(bone)
        while parent.IsOk():
            if self.bone_list.GetCheckedState(parent) == wx.CHK_UNCHECKED:
                return

            if self.bone_list.AreAllChildrenInState(parent, wx.CHK_CHECKED):
                self.bone_list.CheckItem(parent, wx.CHK_CHECKED)
            else:
                self.bone_list.CheckItem(parent, wx.CHK_UNDETERMINED)
            parent = self.bone_list.GetItemParent(parent)

    def get_bone_names_index(self, item):
        current_bone_list = {}
        while item.IsOk():
            bone = self.bone_list.GetItemData(item)
            current_bone_list[bone.name] = item
            current_bone_list.update(self.get_bone_names_index(self.bone_list.GetFirstChild(item)))
            item = self.bone_list.GetNextSibling(item)
        return current_bone_list

    def enable_copy_bones(self, menu_item, selected, single=False):
        if not self.copied_bones:
            menu_item.Enable(False)
            return
        enable_selected(menu_item, selected, single)

    def recalculate_bone_tree(self):
        item = self.bone_list.GetFirstItem()

        # Set index first
        index = 0

        while item.IsOk():
            bone = self.bone_list.GetItemData(item)
            bone.index = index
            self.bone_list.SetItemText(item, "{}: {}".format(bone.index, bone.name))
            item = self.bone_list.GetNextItem(item)
            index += 1

        # Set first pyxenoverse up first
        item = self.bone_list.GetFirstItem()
        bones = []
        while item.IsOk():
            root = self.bone_list.GetRootItem()
            bone = self.bone_list.GetItemData(item)
            parent = self.bone_list.GetItemParent(item)
            child = self.bone_list.GetFirstChild(item)
            sibling = self.bone_list.GetNextSibling(item)

            bone.parent_index = self.bone_list.GetItemData(parent).index if parent != root else 65535
            bone.child_index = self.bone_list.GetItemData(child).index if child.IsOk() else 65535
            bone.sibling_index = self.bone_list.GetItemData(sibling).index if sibling.IsOk() else 65535

            bones.append(bone)

            item = self.bone_list.GetNextItem(item)

        if self.filetype == 'EAN':
            old_length = len(self.root.main['ean'].skeleton.bones)
            self.root.main['ean'].skeleton.bones = bones
        else:
            old_length = len(self.root.main['esk'].bones)
            for bone in bones:
                bone.calculate_transform_matrix_from_skinning_matrix(bones, True)
            self.root.main['esk'].bones = bones

        return old_length, len(bones)

    def on_checked(self, e):
        bone = e.GetItem()
        selection = self.bone_list.GetSelections()
        new_state = wx.CHK_UNCHECKED
        if len(selection) > 1:
            if e.GetOldCheckedState == wx.CHK_UNCHECKED or any(self.bone_list.GetCheckedState(s) == wx.CHK_UNCHECKED for s in selection if s != bone):
                new_state = wx.CHK_CHECKED
            for s in selection:
                self.bone_list.CheckItem(s, new_state)

        if self.bone_list.GetCheckedState(bone) == wx.CHK_CHECKED and not self.bone_list.AreAllChildrenInState(bone, wx.CHK_CHECKED):
            self.bone_list.CheckItem(bone, wx.CHK_UNDETERMINED)

        self.check_parent(bone)

    def add_missing_bones(self):
        missing_bones = self.root.main['ean'].get_bone_difference(self.root.side['ean'])
        if missing_bones:
            with AddMissingBonesDialog(self, missing_bones) as dlg:
                if dlg.ShowModal() != wx.ID_OK:
                    return []
                missing_bones = dlg.GetValues()
        else:
            return []

        # Add bones and add them to the pyxenoverse filter
        bone_indexes = [bone.index for bone in missing_bones]

        # Get Parent bones
        parent_bones = [bone for bone in missing_bones if bone.parent_index not in bone_indexes]

        # Get Bones to copy
        bone_map = {bone.parent_index: get_bone_tree(bone, self.root.side['ean'].skeleton) for bone in parent_bones}

        # Get Root Tree Item
        bone_list = self.root.main['ean_bone_list']
        temp_bone_list = {}
        for index in bone_map:
            if index == 0:
                temp_bone_list[index] = bone_list.GetFirstItem()
            else:
                bone = self.root.main['ean'].skeleton.bones[index]
                item = bone_list.GetFirstItem()
                while item.IsOk():
                    data = bone_list.GetItemData(item)
                    if bone.name == data.name:
                        temp_bone_list[index] = item
                        break
                    item = bone_list.GetNextItem(item)
                else:
                    temp_bone_list[index] = bone_list.GetFirstItem()

        # Copy Bones
        names = []
        for bone in missing_bones:
            new_bone = Bone()
            new_bone.paste(bone)
            item = bone_list.AppendItem(temp_bone_list[bone.parent_index], '', data=new_bone)
            bone_list.Expand(item)
            bone_list.CheckItem(item)

            temp_bone_list[bone.index] = item
            names.append(bone.name)
        self.recalculate_bone_tree()
        return names

    def enable_selected(self, item, single=False):
        selected = self.bone_list.GetSelections()
        if not selected:
            item.Enable(False)
        if single and len(selected) > 1:
            item.Enable(False)

    def on_right_click(self, e):
        selected = self.bone_list.GetSelections()
        menu = wx.Menu()
        info = menu.Append(wx.ID_INFO, "&Info\tCtrl+I", " Edit pyxenoverse information")
        enable_selected(info, selected)
        if self.filetype == 'EAN':
            filter_menu = wx.Menu()
            add_filter_menu = wx.Menu()
            remove_filter_menu = wx.Menu()
            for f in sorted(FILTERS):
                add_bone_filter = add_filter_menu.Append(-1, f, " Select pyxenoverse filter")
                self.Bind(wx.EVT_MENU, partial(self.on_add_filter, bone_filter=f), add_bone_filter)
                remove_bone_filter = remove_filter_menu.Append(-1, f, " Select pyxenoverse filter")
                self.Bind(wx.EVT_MENU, partial(self.on_remove_filter, bone_filter=f), remove_bone_filter)

            filter_menu.AppendSubMenu(add_filter_menu, "&Add")
            filter_menu.AppendSubMenu(remove_filter_menu, "&Remove")
            menu.AppendSubMenu(filter_menu, "&Filters")
            menu.Append(wx.ID_SELECTALL, "Select All\tCtrl+A", " Select all bones")
        delete = menu.Append(wx.ID_DELETE, "&Delete\tDelete", "Delete selected bones")
        enable_selected(delete, selected)
        paste = menu.Append(wx.ID_PASTE, "&Paste\tCtrl+V", "Paste copied bones")
        self.enable_copy_bones(paste, selected)
        rename = menu.Append(self.rename_id, "&Rename\tF2", "Rename selected pyxenoverse")
        enable_selected(rename, selected)

        # Show Menu
        self.PopupMenu(menu)
        menu.Destroy()

    def on_select(self, _):
        if self.bone_list.GetSelections():
            self.info.Enable()
        else:
            self.info.Disable()

    def on_open(self, _):
        pub.sendMessage('open_main_file')

    def on_save(self, _):
        pub.sendMessage('save_' + self.filetype.lower())

    def on_add_filter(self, _, bone_filter):
        bone = self.bone_list.GetFirstItem()
        while bone.IsOk():
            if self.bone_list.GetItemData(bone).name in FILTERS[bone_filter]:
                self.bone_list.CheckItem(bone, wx.CHK_CHECKED)
            self.check_parent(bone)
            bone = self.bone_list.GetNextItem(bone)

    def on_remove_filter(self, _, bone_filter):
        bone = self.bone_list.GetFirstItem()
        while bone.IsOk():
            if self.bone_list.GetItemData(bone).name in FILTERS[bone_filter]:
                self.bone_list.CheckItem(bone, wx.CHK_UNCHECKED)
            self.check_parent(bone)
            bone = self.bone_list.GetNextItem(bone)

    def toggle_select_all(self, _):
        self.bone_list.SelectAll()

    def copy_bones(self, copied_bones):
        self.copied_bones = pickle.dumps(copied_bones)

    def on_delete(self, _):
        selected = self.bone_list.GetSelections()
        if not selected:
            return
        bone = self.bone_list.GetFirstItem()
        while bone.IsOk():
            if bone in selected:
                self.bone_list.DeleteItem(bone)
                bone = self.bone_list.GetFirstItem()
            else:
                bone = self.bone_list.GetNextItem(bone)

        old_len, new_len = self.recalculate_bone_tree()
        if self.filetype == 'EAN':
            self.root.main['ean'].clean_animations()

        self.root.SetStatusText("Deleted {} bones total".format(old_len - new_len))

    def on_paste(self, _):
        selected = self.bone_list.GetSelections()
        if not selected or not self.copied_bones:
            return
        copied_bones = pickle.loads(self.copied_bones)
        if len(selected) > 1:
            with wx.MessageDialog(self, 'Only one pyxenoverse can be selected to paste over', 'Warning') as dlg:
                dlg.ShowModal()
            return
        temp_bone_list = {}
        root = selected[-1]
        root_bone = self.bone_list.GetItemData(root)
        self.bone_list.UnselectAll()
        all_bone_list = self.get_bone_names_index(self.bone_list.GetFirstItem())
        current_bone_list = {root_bone.name: root}
        current_bone_list.update(self.get_bone_names_index(self.bone_list.GetFirstChild(root)))
        changed_bones = ''
        for bone in copied_bones:
            if bone.name in current_bone_list:
                changed_bones += ' * ' + bone.name + '\n'
        if changed_bones:
            msg = "You are about to change multiple bones.  Are you sure you want to do that?"
            with MultiMessageDialog(self, msg, "Warning", changed_bones, wx.YES | wx.NO) as dlg:
                if dlg.ShowModal() != wx.ID_YES:
                    return

        for bone in copied_bones:
            new_bone = Bone()
            new_bone.paste(bone)
            if new_bone.name in current_bone_list:
                item = current_bone_list[new_bone.name]
                self.bone_list.SetItemData(item, new_bone)
            else:
                new_bone = get_unique_name(new_bone, all_bone_list)
                if new_bone.parent_index in temp_bone_list:
                    item = self.bone_list.AppendItem(temp_bone_list[new_bone.parent_index], '', data=new_bone)
                else:
                    item = self.bone_list.AppendItem(root, '', data=new_bone)
            self.bone_list.Select(item)
            self.bone_list.Expand(item)
            self.bone_list.CheckItem(item)
            temp_bone_list[new_bone.index] = item
        self.recalculate_bone_tree()
        self.root.SetStatusText("Pasted {} bones".format(len(copied_bones)))

    def on_rename(self, _):
        def rename_func(item, bone, old_name, new_name):
            self.bone_list.SetItemText(item, '{}: {}'.format(bone.index, bone.name))
            if self.filetype == 'EAN' and self.root.main['ean'] is not None:
                for animation in self.root.main['ean'].animations:
                    for node in animation.nodes:
                        if node.bone_name == old_name:
                            node.bone_name = new_name

        selected = self.bone_list.GetSelections()
        if not selected:
            return
        bones = [self.bone_list.GetItemData(item) for item in selected]
        names = self.get_bone_names_index(self.bone_list.GetFirstItem())
        rename(self.root, 'bones', bones, names, selected, rename_func)

    def on_info(self, _):
        selection = self.bone_list.GetSelections()
        if len(selection) != 1:
            with wx.MessageDialog(self, 'Only one pyxenoverse can be selected for this operation', 'Warning') as dlg:
                dlg.ShowModal()
                return
        bone = self.bone_list.GetItemData(selection[0])
        with BoneInfoDialog(
                self.root, self.filetype, self.name.GetLabel(), bone, False) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.recalculate_bone_tree()
