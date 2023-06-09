import struct
import os
import bpy
import imp
import bmesh
import itertools
import zlib
import operator
from mathutils import Vector, Euler, Matrix
from math import radians, sqrt, degrees, acos, atan2
from random import randint

linux_path = '/media/2tb/Blender/blender-2.71-windows64'

# Detect different operating system
if os.name == 'nt':  # windows detected
    prePath = ''
else:
    prePath = linux_path + os.sep

fifa_source_path = os.path.join('fifa_tools', 'scripts', 'source')
fifa_compiled_path = os.path.join('fifa_tools', 'scripts', 'compiled')

try:
    half = imp.load_source('half', prePath + os.path.join(fifa_source_path, 'half.py'))
    print('Loading Source File')
except:
    half = imp.load_compiled('half', prePath + os.path.join(fifa_compiled_path, 'half.pyc'))

dir = 'fifa_tools'
comp = half.Float16Compressor()


dict = {(12, 0): (2, 0, 0, 1, 0),  # (CHUNK_LENGTH, VFLAG):   (PREGAP,INNERGAP,POSTGAP,UVCOUNT,VFLAG)
        (12, 1): (2, 0, 0, 1, 0),
        (16, 1): (0, 0, 0, 1, 1),
        (20, 0): (6, 0, 0, 2, 0),
        (20, 1): (0, 0, 0, 2, 1),
        (24, 0): (6, 0, 4, 2, 0),
        (24, 1): (4, 0, 0, 2, 1),
        (28, 0): (6, 0, 8, 2, 0),
        (32, 0): (14, 0, 4, 2, 0),
        (32, 1): (8, 0, 4, 2, 1),
        (32, 2): (14, 0, 8, 1, 0),
        (36, 1): (8, 0, 8, 2, 1),
        (40, 0): (10, 4, 12, 2, 0),
        (40, 1): (2, 24, 0, 2, 0),
        (40, 2): (10, 4, 16, 1, 0)
        }


class texture_helper:
    # READ DDS HEADER FILE

    @staticmethod
    def read_dds_header(offset):
        data = []
        path = os.path.join(prePath, 'fifa_tools', 'dds_headers')
        headers = open(path, 'rb')
        headers.seek(offset + 16)

        for i in range(128):
            data.append(struct.unpack('<B', headers.read(1))[0])

        headers.close()
        return data

    @staticmethod
    def read_dds_info(data):
        data.seek(12)
        width = struct.unpack('<I', data.read(4))[0]
        height = struct.unpack('<I', data.read(4))[0]
        data.seek(8, 1)
        mipmaps = struct.unpack('<H', data.read(2))[0]
        data.seek(54, 1)
        type = ''
        type = type.join([chr(i) for i in data.read(4)])

        return height, width, mipmaps, type

    @staticmethod
    def get_textures_list(object):
        texture_dict = {}
        textures_list = []
        status = ''
        ambient = None

        try:
            mat = bpy.data.materials[object.material_slots[0].material.name]
            for i in range(10):
                try:
                    texture_name = mat.texture_slots[i].name
                    texture_image = bpy.data.textures[texture_name].image.name
                    texture_path = bpy.data.images[texture_image].filepath
                    texture_alpha = bpy.data.images[texture_image].use_alpha
                    texture_maxsize = max(
                        bpy.data.images[texture_image].size[0], bpy.data.images[texture_image].size[1])

                    # if not texture_name in texture_dict:
                    if i is not 1:
                        textures_list.append(
                            [texture_name, texture_path, texture_alpha, 0, 0, 0, 0, '', texture_maxsize])
                    else:
                        ambient = [texture_name, texture_path, texture_alpha, 0, 0, 0, 0, '', texture_maxsize]
                    # store texture_information indexed in the dictionary
                    texture_dict[texture_name] = len(textures_list)
                except:
                    # Found Empty Texture Slot
                    # print('Empty Texture Slot')
                    pass

        except:
            status = 'material_missing'

        return texture_dict, textures_list, ambient,status


# Helping function class
class general_helper:

    # READ VERTEX FUNCTIONS
    @staticmethod
    def read_vertices_1(f):
        vert_tup = struct.unpack('<3f', f.read(12))
        return((vert_tup[0] / 100, -vert_tup[2] / 100, vert_tup[1] / 100))

    @staticmethod
    def read_vertices_0(f):
        vx = comp.decompress(struct.unpack('<H', f.read(2))[0])
        vy = comp.decompress(struct.unpack('<H', f.read(2))[0])
        vz = comp.decompress(struct.unpack('<H', f.read(2))[0])
        f.read(2)

        hx = struct.unpack('f', struct.pack('I', vx))[0]
        hy = struct.unpack('f', struct.pack('I', vy))[0]
        hz = struct.unpack('f', struct.pack('I', vz))[0]
        return((hx / 100, -hz / 100, hy / 100))

    @staticmethod
    def read_uvs_1(f):
        return(struct.unpack('<2f', f.read(8)))

    @staticmethod
    def read_uvs_0(f):
        uvx = comp.decompress(struct.unpack('<H', f.read(2))[0])
        uvy = comp.decompress(struct.unpack('<H', f.read(2))[0])
        huvx = struct.unpack('f', struct.pack('I', uvx))[0]
        huvy = struct.unpack('f', struct.pack('I', uvy))[0]
        return((huvx, huvy))

    @staticmethod
    def read_cols(f):
        val = struct.unpack('<I', f.read(4))[0]
        val_0 = (val & 0x3ff) / 1023
        val_1 = ((val >> 10) & 0x3ff) / 1023
        val_2 = ((val >> 20) & 0x3ff) / 1023
        return((val_2, val_1, val_0))

    @staticmethod
    def read_cols_testing(f):
        val = struct.unpack('<4B', f.read(4))
        return (val[0], -val[2], val[1])

        ##READ AND STORE FACE DATA#
    @staticmethod
    def facereadlist(f, offset, endian):
        faces = []
        f.seek(offset)
        f.read(4)
        indicescount = struct.unpack(endian + 'I', f.read(4))[0]
        # CHANGED TO 2BYTE IN ORDER TO MATCH THE 2 ENDIAN TYPES
        indiceslength = struct.unpack(endian + 'B', f.read(1))[0]
        f.read(3)
        facecount = int(indicescount / 3)
        f.read(4)
        if indiceslength == 4:
            string = endian + 'III'
        elif indiceslength == 2:
            string = endian + 'HHH'

        for i in range(facecount):
            temp = struct.unpack(string, f.read(indiceslength * 3))
            if temp[0] == temp[1] or temp[2] == temp[1] or temp[0] == temp[2]:
                continue
            faces.append((temp[0], temp[1], temp[2]))

        # print(faces)
        return faces, indiceslength

    @staticmethod
    def facereadstrip(f, offset, endian):
        faces = []
        f.seek(offset)
        f.read(4)
        indicescount = struct.unpack('<I', f.read(4))[0]
        indiceslength = struct.unpack('<i', f.read(4))[0]
        facecount = indicescount - 2
        print(indicescount, facecount)
        f.read(4)
        if indiceslength == 4:
            string = '<III'
        elif indiceslength == 2:
            string = '<HHH'

        flag = False
        for i in range(facecount):
            back = f.tell()
            temp = struct.unpack(string, f.read(indiceslength * 3))
            if temp[0] == temp[1] or temp[1] == temp[2] or temp[0] == temp[2]:
                flag = not flag
                f.seek(back + indiceslength)
                continue
            else:
                if flag is False:
                    faces.append((temp[0], temp[1], temp[2]))
                elif flag is True:
                    faces.append((temp[2], temp[1], temp[0]))

                flag = not flag
                f.seek(back + indiceslength)

        # print(faces)
        return faces, indiceslength

    @staticmethod
    def write_half_verts(f, co):
        hvx = comp.compress(round(co[0], 12))
        hvy = comp.compress(round(co[1], 12))
        hvz = comp.compress(round(co[2], 12))
        f.write(struct.pack('<HHH', hvx, hvy, hvz))
        f.seek(2, 1)

    @staticmethod
    def read_string(f):
        c = ''
        for i in range(128):
            s = struct.unpack('<B', f.read(1))[0]
            if s == 0:
                return c
            c = c + chr(s)

        return {'FINISHED'}

    @staticmethod
    def rgb_to_hex(rgb):
        return '#%02x%02x%02x' % rgb

    @staticmethod
    def hex_to_rgb(hex):
        hex = hex.lstrip('#')
        hlen = len(hex)
        return tuple(int(hex[i:i + int(hlen / 3)], 16) / 255 for i in range(0, hlen, int(hlen / 3)))

    @staticmethod
    def vector_to_matrix(v):
        matrix = Matrix()

        for i in range(len(v)):
            matrix[i][i] = v[i]
        return matrix

    @staticmethod
    def size_round(size):
        rest = size % 16
        eucl = size // 16
        if rest > 0:
            size = eucl * 16 + 16
        return size

    @staticmethod
    def face_center(f):
        cx = 0
        cy = 0
        cz = 0

        for v in f.verts:
            cx = cx + v.co[0]
            cy = cy + v.co[1]
            cz = cz + v.co[2]

        return Vector((cx / len(f.verts), cy / len(f.verts), cz / len(f.verts)))

    @staticmethod
    def vec_roll_to_mat3(vec, roll):
        target = Vector((0, 1, 0))
        nor = vec.normalized()
        axis = target.cross(nor)
        if axis.dot(axis) > 0.000001:
            axis.normalize()
            theta = target.angle(nor)
            bMatrix = Matrix.Rotation(theta, 3, axis)
        else:
            updown = 1 if target.dot(nor) > 0 else -1
            bMatrix = Matrix.Scale(updown, 3)
        rMatrix = Matrix.Rotation(roll, 3, nor)
        mat = rMatrix * bMatrix
        return mat

    # Blender Transformation Matrix converting functions
    @staticmethod
    def mat3_to_vec_roll(mat):
        vec = mat.col[1]
        vecmat = general_helper.vec_roll_to_mat3(mat.col[1], 0)
        vecmatinv = vecmat.inverted()
        rollmat = vecmatinv * mat
        roll = atan2(rollmat[0][2], rollmat[2][2])
        return vec, roll

    @staticmethod
    def create_boundingbox(vec1, vec2, name):
        comb = list(itertools.product(vec1, vec2))
        v1, v2, v3 = comb[0], comb[3], comb[6]
        verts = list(itertools.product(v1, v2, v3))
        faces = [(4, 6, 7), (7, 5, 4), (2, 6, 4), (4, 0, 2), (3, 2, 0), (0, 1, 3),
                 (5, 3, 1), (3, 5, 7), (5, 1, 0), (0, 4, 5), (7, 2, 3), (2, 7, 6)]

        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
        bpy.data.objects['Empty'].scale = Vector((1, 1, 1))
        bpy.data.objects['Empty'].location = (0, 0, 0)
        #bpy.data.objects['Empty'].rotation_euler=Euler((1.570796251296997, -0.0, 0.0), 'XYZ')
        bpy.data.objects['Empty'].rotation_euler = Euler((0, -0.0, 0.0), 'XYZ')
        bpy.data.objects['Empty'].name = name

    @staticmethod
    def create_prop(name, loc, rot):

        bpy.ops.object.empty_add(type='SINGLE_ARROW', location=loc, rotation=(
            rot[0] - radians(90), rot[2], rot[1] + radians(180)))
        ob = bpy.data.objects['Empty']

        try:
            i = 0
            while bpy.data.objects[name + '_' + str(i)]:
                i += 1
        except:
            ob.name = name + '_' + str(i)
            # ob.data.align='CENTER'

        # ob.data.body=name+'_'+str(i)
        ob.scale = Vector((0.1, 0.1, 0.1))
        return ob.name

    @staticmethod
    def object_bbox(object):

        # Matrices
        rot_x_mat = Matrix.Rotation(radians(-90), 4, 'X')
        scale_mat = Matrix.Scale(100, 4)

        # Getters
        getz = operator.itemgetter(2)
        gety = operator.itemgetter(1)
        getx = operator.itemgetter(0)

        bv_list = []
        for j in object.bound_box:
            # Object Matrices
            bbox = Vector()
            bbox[0] = j[0]
            bbox[1] = j[1]
            bbox[2] = j[2]

            object_matrix_wrld = object.matrix_world
            bbox = rot_x_mat * scale_mat * object_matrix_wrld * (bbox)

            bv_list.append((bbox[2], bbox[1], bbox[0]))

        print(bv_list)

        # Returned Vectors
        bbox1 = Vector()
        bbox2 = Vector()

        # get min values
        bbox1[0] = min(bv_list, key=getz)[2]
        bbox1[1] = min(bv_list, key=gety)[1]
        bbox1[2] = min(bv_list, key=getx)[0]

        # get max values
        bbox2[0] = max(bv_list, key=getz)[2]
        bbox2[1] = max(bv_list, key=gety)[1]
        bbox2[2] = max(bv_list, key=getx)[0]

        return bbox1, bbox2

    @staticmethod
    def group_bbox(group):
        mins = [[], [], []]
        maxs = [[], [], []]

        for i in range(len(group.children)):
            vec1, vec2 = general_helper.object_bbox(group.children[i])
            mins[0].append(vec1[0])
            mins[1].append(vec1[1])
            mins[2].append(vec1[2])

            maxs[0].append(vec2[0])
            maxs[1].append(vec2[1])
            maxs[2].append(vec2[2])

        return ((min(mins[0]), min(mins[1]), min(mins[2])), (max(maxs[0]), max(maxs[1]), max(maxs[2])))

    @staticmethod
    def paint_faces(object, color, layer_name):
        bm = bmesh.from_edit_mesh(object.data)
        collayer = bm.loops.layers.color[layer_name]
        for f in bm.faces:
            if f.select:
                for l in f.loops:
                    l[collayer] = color
        bmesh.update_edit_mesh(object.data, True)

    @staticmethod
    def auto_paint_mesh(object):
        scn = bpy.context.scene
        bm = bmesh.new()
        bm.from_mesh(object.data)
        bm.normal_update()
        # base_0=0.498
        # base_1=0.502

        #obj_rotation = object.rotation_euler
        #print(obj_rotation)

        if scn.autopaint_modes == '0':
            collayer = bm.loops.layers.color.new('normalmap')
            for f in bm.faces:
                for l in f.loops:
                    vert = l.vert
                    #rot=Euler((-1.5707963705062866, 0.0, 0.0), 'XYZ')
                    norm = vert.normal
                    # norm.rotate(obj_rotation)
                    #norm.normalize()
                    # norm.rotate(rot)
                    l[collayer].r = general_helper.norm_to_col(
                        round(-norm[1], 3))
                    l[collayer].g = general_helper.norm_to_col(
                        round(norm[2], 3))
                    l[collayer].b = general_helper.norm_to_col(
                        round(norm[0], 3))
        elif scn.autopaint_modes == '1':
            collayer = bm.loops.layers.color.new('fnormalmap')
            for f in bm.faces:
                for l in f.loops:
                    vert = l.vert
                    #rot=Euler((-1.5707963705062866, 0.0, 0.0), 'XYZ')
                    norm = vert.normal
                    # norm.rotate(obj_rotation)
                    norm.normalize()
                    # norm.rotate(rot)
                    l[collayer][0] = general_helper.norm_to_col(
                        round(-norm[0], 3))
                    l[collayer][1] = general_helper.norm_to_col(
                        round(-norm[2] * 0.00068, 3))
                    l[collayer][2] = general_helper.norm_to_col(
                        round(-norm[1], 3))
        elif scn.autopaint_modes == '2':
            try:
                lm = bm.loops.layers.uv[1]
            except:
                print("Missing lightmap layer")
                return
            collayerTangents = bm.loops.layers.color.new('tangents')
            collayerBitangents = bm.loops.layers.color.new('binormals')
            vtanlist = [Vector((0.0, 0.0, 0.0))] * len(bm.verts)
            vbitanlist = [Vector((0.0, 0.0, 0.0))] * len(bm.verts)

            # Calculating tangents
            for i in range(len(bm.faces)):
                f = bm.faces[i]
                l0, l1, l2 = f.loops[0], f.loops[1], f.loops[2]
                v0, v1, v2 = l0.vert.index, l1.vert.index, l2.vert.index
                #print('Working on face: ', i, 'Vertices: ', f.loops[0].vert.index, f.loops[1].vert.index,
                #      f.loops[2].vert.index)

                # Checking first 3 loops/verts
                tangent = general_helper.calc_tangent(l0, l1, l2, lm)
                vtanlist[v0] = (tangent + vtanlist[v0])
                vtanlist[v1] = (tangent + vtanlist[v1])
                vtanlist[v2] = (tangent + vtanlist[v2])

                #print(vtanlist[0], 'first value')
                vbitanlist[v0] = (l0.vert.normal.cross(tangent) + vbitanlist[v0])
                vbitanlist[v1] = (l1.vert.normal.cross(tangent) + vbitanlist[v0])
                vbitanlist[v2] = (l2.vert.normal.cross(tangent) + vbitanlist[v0])

                # if len(f.loops) == 4:
                #    tangent = general_helper.calc_tangent(f.loops[3], f.loops[1], f.loops[2], lm)
                #    vtanlist[f.loops[3].vert.index] += tangent
                #    vtanlist[f.loops[1].vert.index] += tangent
                #    vtanlist[f.loops[2].vert.index] += tangent

                #    vbitanlist[f.loops[3].vert.index] += f.loops[3].vert.normal.cross(tangent)
                #    vbitanlist[f.loops[1].vert.index] += f.loops[1].vert.normal.cross(tangent)
                #    vbitanlist[f.loops[2].vert.index] += f.loops[2].vert.normal.cross(tangent)

            # Passing tangents/bitangents to color maps
            for f in bm.faces:
                for l in f.loops:
                    vert = l.vert
                    tangent = vtanlist[vert.index]
                    #tangent[1] = 500 * tangent[1]
                    #tangent = tangent - vert.normal * \
                    #    (vert.normal.dot(tangent))
                    tangent.normalize()

                    bitangent = vbitanlist[vert.index]
                    bitangent.normalize()
                    # bitangent.normalize()
                    if vert.index == 294:
                        print(tangent)

                    l[collayerTangents][0] = general_helper.norm_to_col(round(tangent[0], 3))
                    l[collayerTangents][1] = general_helper.norm_to_col(round(tangent[2], 3))
                    l[collayerTangents][2] = general_helper.norm_to_col(round(-tangent[1], 3))

                    l[collayerBitangents][0] = general_helper.norm_to_col(round(bitangent[0], 3))
                    l[collayerBitangents][1] = general_helper.norm_to_col(round(bitangent[2], 3))
                    l[collayerBitangents][2] = general_helper.norm_to_col(round(-bitangent[1], 3))

        bm.to_mesh(object.data)
        bm.free()

    @staticmethod
    def calc_tangent(l0, l1, l2, lm):
        delta1 = l1.vert.co - l0.vert.co
        delta2 = l2.vert.co - l0.vert.co
        deltauv1 = l1[lm].uv - l0[lm].uv
        deltauv2 = l2[lm].uv - l0[lm].uv

        r = 1.0 / (deltauv1.x * deltauv2.y - deltauv1.y * deltauv2.x)

        if l0.vert.index == 294 or l1.vert.index == 294 or l2.vert.index == 294:
            print('Real Coords: ', l2.vert.co)
            print(delta1, delta2, deltauv1, deltauv2, r)
        tangent = (delta1 * deltauv2.y - delta2 * deltauv1.y) * r

        return tangent

    @staticmethod
    def norm_to_col(x):
        # converting normal Vector to Color Information
        # Arguments:
        # x:    normal Vector
        # axis: desired axis

        if -1 < x < 0:
            return 0.498*x + 1
        elif 0 <= x <= 1:
            return 0.498*x
        else:
            return 0.502

    @staticmethod
    def crowd_col(ob, col, name):
        me = bpy.data.objects[ob].data
        #coltex = me.vertex_colors.new(name=name)

        bm = bmesh.new()
        bm.from_mesh(me)

        collayer = bm.loops.layers.color.new(name)
        for f in bm.faces:
            for l in f.loops:
                l[collayer].r = col[f.index][0]
                l[collayer].g = col[f.index][1]
                l[collayer].b = col[f.index][2]

        bm.to_mesh(me)
        bm.free()


