import bpy
import gpu
from bpy.types import PropertyGroup, Operator
from bpy.props import IntProperty,BoolProperty,StringProperty,PointerProperty,CollectionProperty
from bpy.utils import register_class,unregister_class

bl_info = {
    "name" : "ViewSync2",
    "author" : "BlackSpree",
    "description" : "",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "",
    "warning" : "",
    "category" : "Generic"
}

draw_handle = None

def register():
    global draw_handle

    register_class(SetTargetOperator)
    register_class(VIEW3D_PT_view_synchronous)
    register_class(SetTackOperator)
    register_class(ClearTrackOperator)
    draw_handle = bpy.types.SpaceView3D.draw_handler_add(sync_view,(),'WINDOW','POST_VIEW')

def unregister():
    unregister_class(SetTargetOperator)
    unregister_class(VIEW3D_PT_view_synchronous)
    unregister_class(SetTackOperator)
    unregister_class(ClearTrackOperator)
    bpy.types.SpaceView3D.draw_handler_remove(draw_handle,'WINDOW')

C = bpy.context
is_edit = False
target_area = None
target_dict = {}
valid_area = []

# 全局函数
def get_area_info(area):
    '''获取区域信息'''
    win_man = C.window_manager
    for i in range(len(win_man.windows)):
        win = win_man.windows[i]
        for j in range(len(win.screen.areas)):
            if win.screen.areas[j] == area:
                return [i, j]
    return None

def draw_area_info(info, layout):
    '''绘制区域信息到一行'''
    w, a = info
    row = layout.row()
    row.label(text='第'+str(w)+'个窗口')
    row.label(text='第'+str(a)+'个区域')

def try_draw_area_info(area, msg, layout):
    '''尝试绘制区域信息'''
    info = get_area_info(area)
    if not info == None:
        layout.label(text=msg)
        box = layout.box()
        draw_area_info(info, box)

def update_valid_area():
    '''获取所有有效区域'''
    global valid_area

    valid_area.clear()
    win_man = C.window_manager
    for win in win_man.windows:
        for area in win.screen.areas:
            valid_area.append(area)

def sync_view():
    '''每帧运行的函数'''
    global target_dict

    update_valid_area()
    for key in target_dict.keys():
        if not valid_area.__contains__(key):
            del target_dict[key]
            continue
        if not valid_area.__contains__(target_dict[key]):
            del target_dict[key]
            continue
        key.spaces[0].region_3d.view_matrix = target_dict[key].spaces[0].region_3d.view_matrix

class VIEW3D_PT_view_synchronous(bpy.types.Panel):
    '''绘制主面板'''
    bl_label = "视图同步"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "视图跟踪"

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon="RENDER_RESULT")

    def draw(self, context):
        global target_area
        global target_dict

        layout = self.layout
        
        try_draw_area_info(context.area, '当前窗口信息', layout)
        
        if is_edit:
            layout.operator("sync_view.set_target", text='取消设置')
            try_draw_area_info(target_area, '正在为此窗口设置跟踪', layout)
            layout.operator("sync_view.set_track")
        else:
            layout.operator("sync_view.set_target")

        if target_dict.__contains__(context.area):
            try_draw_area_info(target_dict[context.area], '正在跟踪此窗口', layout)
            layout.operator("sync_view.clear_track")


class SetTargetOperator(Operator):
    bl_idname = "sync_view.set_target"
    bl_label = "设置为被跟踪对象"

    def execute(self, context):
        global is_edit
        global target_area

        if not is_edit:
            target_area = context.area
        is_edit = not is_edit

        return {'FINISHED'}


class SetTackOperator(bpy.types.Operator):
    bl_idname = "sync_view.set_track"
    bl_label = "设置跟踪"
    
    @classmethod
    def poll(cls, context):
        global target_area
        global is_edit

        return is_edit and not context.area == target_area

    def execute(self, context):
        global target_dict
        global target_area
        global is_edit

        is_edit = False
        target_dict[context.area] = target_area
        return {'FINISHED'}


class ClearTrackOperator(bpy.types.Operator):
    bl_idname = "sync_view.clear_track"
    bl_label = "清除跟踪"

    @classmethod
    def poll(cls, context):
        global target_dict
        return target_dict.__contains__(context.area)

    def execute(self, context):
        global target_dict
        del target_dict[context.area]
        return {'FINISHED'}
