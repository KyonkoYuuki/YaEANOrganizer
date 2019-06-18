import wx
from wx.lib.dialogs import MultiMessageDialog

import json
import numpy as np
from pyquaternion import Quaternion
import os
import sys

from yaean.dlg.multi_rename import MultiRenameDialog
from yaean.dlg.rename import RenameDialog

CHECK = "\u2714"
POSITION_FLAG = 1792
ORIENTATION_FLAG = 1793
SCALE_FLAG = 1794
TARGET_CAMERA_POSITION_FLAG = 1793
DIRNAME, _ = os.path.split(os.path.abspath(sys.argv[0]))
CONFIG_DIR = os.path.join(DIRNAME, 'config', 'bone_filters')
FILTERS = {}
for path, dirs, files in os.walk(CONFIG_DIR):
    for file in files:
        with open(os.path.join(path, file)) as f:
            FILTERS.update(json.load(f))


def build_anim_list(anim_list_ctrl, ean):
    anim_list_ctrl.DeleteAllItems()
    for i, animation in enumerate(ean.animations):
        anim_list_ctrl.Append((str(i), animation.name, str(animation.frame_count)))


def build_bone_tree(bone_list_ctrl, esk):
    bone_list_ctrl.DeleteAllItems()
    temp_bone_list = []
    for i, bone in enumerate(esk.bones):
        if i == 0:
            item = bone_list_ctrl.AppendItem(
                bone_list_ctrl.GetRootItem(), "{}: {}".format(i, bone.name), data=bone)
        else:
            item = bone_list_ctrl.AppendItem(
                temp_bone_list[bone.parent_index], "{}: {}".format(i, bone.name), data=bone)
        temp_bone_list.append(item)
    item = bone_list_ctrl.GetFirstItem()
    while item.IsOk():
        bone_list_ctrl.Expand(item)
        item = bone_list_ctrl.GetNextItem(item)
    bone_list_ctrl.CheckItemRecursively(bone_list_ctrl.GetRootItem(), wx.CHK_CHECKED)


def get_bone_tree(bone, esk):
    bone_list = [bone]
    if bone.child_index != 65535:
        bone_list.extend(get_bone_tree(esk.bones[bone.child_index], esk))
    if bone.sibling_index != 65535:
        bone_list.extend(get_bone_tree(esk.bones[bone.sibling_index], esk))
    return bone_list


def get_selected_items(list_ctrl):
    index = -1
    while True:
        index = list_ctrl.GetNextSelected(index)
        if index == -1:
            return
        yield index


def enable_selected(item, selected, single=False):
    if not selected:
        item.Enable(False)
    if single and len(selected) > 1:
        item.Enable(False)


def get_unique_name(obj, names):
    while obj.name in names:
        parts = obj.name.rsplit('.', 1)
        if len(parts) == 1:
            obj.name = parts[0] + '.000'
        else:
            try:
                obj.name = '.'.join([parts[0], '{0:03d}'.format(int(parts[1]) + 1)])
            except ValueError:
                obj.name = parts[0] + '.000'
    return obj


def show_rename_dialog(root, obj, names, selected, rename_func):
    with RenameDialog(root, obj.name, names) as dlg:
        if dlg.ShowModal() == wx.ID_OK:
            new_name = dlg.GetValue()
            old_name, obj.name = obj.name, new_name
            rename_func(selected, obj, old_name, new_name)
            root.SetStatusText("Renamed {} to {}".format(old_name, new_name))


def show_multi_rename_dialog(root, obj_type, obj_list, names, selected, rename_func):
    with MultiRenameDialog(root) as dlg:
        if dlg.ShowModal() == wx.ID_OK:
            pattern = dlg.GetPattern()
            repl = dlg.GetReplace()
            changed_bones = ''
            for obj in obj_list:
                new_name = pattern.sub(repl, obj.name)
                if new_name in names and new_name != obj.name:
                    changed_bones += ' * {} (skipping due to naming conflict)\n'.format(obj.name)
                elif new_name == obj.name:
                    changed_bones += ' * {} (no change)\n'.format(obj.name)
                else:
                    changed_bones += ' * {} -> {}\n'.format(obj.name, new_name)
            msg = "You are about to change multiple {}.  Are you sure you want to do that?\n".format(obj_type)
            with MultiMessageDialog(root, msg, "Warning", changed_bones, wx.YES | wx.NO) as warn:
                if warn.ShowModal() != wx.ID_YES:
                    return
            for i, obj in enumerate(obj_list):
                new_name = pattern.sub(repl, obj.name)
                if new_name in names:
                    continue
                old_name, obj.name = obj.name, new_name
                rename_func(selected[i], obj, old_name, new_name)
            root.SetStatusText("Renamed {} {}".format(len(obj_list), obj_type))


def rename(root, obj_type, obj_list, names, selected, rename_func):
    if len(obj_list) == 1:
        show_rename_dialog(root, obj_list[0], names, selected[0], rename_func)
    else:
        show_multi_rename_dialog(root, obj_type, obj_list, names, selected, rename_func)


def euler_to_quaternion(x, y, z):
    rx = np.radians(x)/2
    ry = np.radians(y)/2
    rz = np.radians(z)/2

    qx = np.sin(rx) * np.cos(ry) * np.cos(rz) - np.cos(rx) * np.sin(ry) * np.sin(rz)
    qy = np.cos(rx) * np.sin(ry) * np.cos(rz) + np.sin(rx) * np.cos(ry) * np.sin(rz)
    qz = np.cos(rx) * np.cos(ry) * np.sin(rz) - np.sin(rx) * np.sin(ry) * np.cos(rz)
    qw = np.cos(rx) * np.cos(ry) * np.cos(rz) + np.sin(rx) * np.sin(ry) * np.sin(rz)

    return Quaternion(qw, qx, qy, qz)


def quaternion_to_euler(q):
        t0 = +2.0 * (q.w * q.x + q.y * q.z)
        t1 = +1.0 - 2.0 * (q.x * q.x + q.y * q.y)
        x = np.degrees(np.arctan2(t0, t1))

        t2 = +2.0 * (q.w * q.y - q.z * q.x)
        t2 = +1.0 if t2 > +1.0 else t2
        t2 = -1.0 if t2 < -1.0 else t2
        y = np.degrees(np.arcsin(t2))

        t3 = +2.0 * (q.w * q.z + q.x * q.y)
        t4 = +1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        z = np.degrees(np.arctan2(t3, t4))

        return x, y, z
