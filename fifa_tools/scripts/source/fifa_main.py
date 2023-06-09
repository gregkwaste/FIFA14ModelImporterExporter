import bpy
import imp
import os
import struct
import bmesh
import zlib
import sys
from math import radians, degrees
from io import BytesIO
from shutil import copyfile

from mathutils import Vector, Euler, Matrix
from math import radians, sqrt
from subprocess import call


linux_path = '/media/2tb/Blender/blender-2.71-windows64'

# Detect different operating system
if os.name == 'nt':  # windows detected
    prePath = ''
else:
    prePath = linux_path + os.sep

fifa_source_path = os.path.join('fifa_tools', 'scripts', 'source')
fifa_compiled_path = os.path.join('fifa_tools', 'scripts', 'compiled')

try:
    fifa_func = imp.load_source('fifa_func', prePath + os.path.join(fifa_source_path, 'fifa_functions.py'))
    print('Loading Source File')
except:
    fifa_func = imp.load_compiled('fifa_func', prePath + os.path.join(fifa_compiled_path, 'fifa15_functions.pyc'))

sig = 'FIFA 3D Importer/Exporter, made by arti. v0.66. All rights reserved.©'

# General gh Function Class
from fifa_func import general_helper as gh
from fifa_func import texture_helper as tex_gh
from fifa_func import half
comp = half.Float16Compressor()
# gh=fifa_func.general_gh()


# Classes
class crowdGroup:
    fullNessDict = {'full': 255,
                    'almostFull': 75,
                    'halfFull': 25,
                    'almostEmpty': 10,
                    'empty': 0}
    typeDict = {'hardcoreHome': (0, 0),         # Home strips visible
            'metalcoreHome': (128, 0),      # Home Strips Visible
            'heavyHome': (0, 128),          # no Colours but cheers when home team score
            'popHome': (128, 128),          # no Colours but cheers when home team score
            'folkHome': (255, 128),         # no Colours but cheers when home team score
            'chickenAway': (128, 255),      # Away strips Visible
            'deadAway': (255, 255)}         # Away Strips Visible

    def __init__(self, name):
        # define subgroups
        self.full = []
        self.almostFull = []
        self.halfFull = []
        self.almostEmpty = []
        self.empty = []
        self.name = name

    def passGroupsToObject(self, ob):

        if self.full:
            gname = self.name + '_full'
            ob.vertex_groups.new(gname)
            ob.vertex_groups[gname].add(self.full, 1, 'ADD')
        if self.almostFull:
            gname = self.name + '_almostFull'
            ob.vertex_groups.new(gname)
            ob.vertex_groups[gname].add(self.almostFull, 1, 'ADD')
        if self.halfFull:
            gname = self.name + '_halfFull'
            ob.vertex_groups.new(gname)
            ob.vertex_groups[gname].add(self.halfFull, 1, 'ADD')
        if self.almostEmpty:
            gname = self.name + '_almostEmpty'
            ob.vertex_groups.new(gname)
            ob.vertex_groups[gname].add(self.almostEmpty, 1, 'ADD')
        if self.empty:
            gname = self.name + '_empty'
            ob.vertex_groups.new(gname)
            ob.vertex_groups[gname].add(self.empty, 1, 'ADD')

    def addToGroup(self, value, items):
        if 76 <= value <= 255:
            self.full.extend(items)
        elif 26 <= value <= 75:
            self.almostFull.extend(items)
        elif 11 <= value <= 25:
            self.halfFull.extend(items)
        elif 1 <= value <= 10:
            self.almostEmpty.extend(items)
        else:
            self.empty.extend(items)


# Create Mesh and Object Function
def createmesh(verts, faces, uvs, name, count, id, subname, colors, normal_flag, normals, loc):
    scn = bpy.context.scene
    mesh = bpy.data.meshes.new("mesh" + str(count))
    mesh.from_pydata(verts, [], faces)

    for i in range(len(uvs)):
        uvtex = mesh.uv_textures.new(name='map' + str(i))
    for i in range(len(colors)):
        coltex = mesh.vertex_colors.new(name='col' + str(i))

    bm = bmesh.new()
    bm.from_mesh(mesh)

    # Create UV MAPS
    for i in range(len(uvs)):
        uvlayer = bm.loops.layers.uv['map' + str(i)]
        for f in bm.faces:
            for l in f.loops:
                l[uvlayer].uv.x = uvs[i][l.vert.index][0]
                l[uvlayer].uv.y = 1 - uvs[i][l.vert.index][1]

    # Create VERTEX COLOR MAPS

    for i in range(len(colors)):
        collayer = bm.loops.layers.color['col' + str(i)]
        for f in bm.faces:
            for l in f.loops:
                l[collayer].r, l[collayer].g, l[
                    collayer].b = colors[i][l.vert.index]

    # Pass Normals
    if normal_flag == True:
        for i in range(len(normals)):
            bm.verts[i].normal = normals[i]

    # Finish up, write the bmesh back to the mesh
    bm.to_mesh(mesh)
    bm.free()  # free and prevent further access

    # if name.split(sep='_')[0]=='head':
    #   object=bpy.data.objects.new(name+'_'+str(id)+'_'+str(count)+'_'+subname,mesh)
    if name.split(sep='_')[0] in ['stadium', 'head']:
        object = bpy.data.objects.new(subname, mesh)
    else:
        object = bpy.data.objects.new(
            name + '_' + str(id) + '_' + str(count), mesh)

    object.location = loc

    # Transformation attributes inherited from bounding boxes
    # if not name=='stadium':
        # object.scale=Vector((0.1,0.1,0.1))
        #object.rotation_euler=Euler((1.570796251296997, -0.0, 0.0), 'XYZ')
    scn.objects.link(object)

    return object.name


# fifa_rx3_class
class fifa_rx3:

    def __init__(self, path, mode):

        self.path = path
        self.data = 0
        self.offsets = []  # file offset list
        self.mesh_offsets = []
        self.indices_offsets = []
        self.offset_list = []
        self.size = ''  # file size text
        self.count = 0
        self.mesh_count = 0  # total meshes in the file
        self.texture_list = []
        self.texture_count = 0
        self.mesh_descrs = []
        self.vxtable = []
        self.cols = []
        self.colcount = []
        self.v_bones_i = []
        self.v_bones_w = []
        self.itable = []
        self.ntable = []
        self.bboxtable = []
        self.uvs = []
        self.uvcount = []
        self.container_type = ''  # file header
        self.endianess = ''  # endianess text
        self.endian = ''  # endianness identifier
        self.bones = []
        self.props = []
        self.prop_list = []
        self.prop_positions = []
        self.prop_rotations = []
        self.prop_count = 0
        self.tex_names = []
        self.sub_names = []
        self.group_names = []
        self.group_list = []
        self.type = ''  # file model type
        self.group_count = 0
        self.materials = []
        self.material_count = 0
        self.material_list = []
        self.material_dict = {}
        self.object_list = []
        self.mat_assign_table = []
        self.id = 0  # file id
        self.crowd = []
        self.collisions = []
        self.collision_list = []
        self.name = ''
        self.code = self.init_read(self.path, mode)
        print(self.code)

    def init_read(self, path, mode):
        scn = bpy.context.scene
        path, filename = os.path.split(path)
        filename, ext = os.path.splitext(filename)
        try:
            self.name = filename
            self.id = self.name.split('_')[1]
            self.type = self.name.split(sep='_')[0]
        except:
            return 'corrupt_filename'

        print(
            '-------------------------------------------------------------------------------')
        print('FILE INITIALIZATION')
        print('FILE PATH: ', self.path)
        print('FILE TYPE: ', self.type)
        print('FILE ID:', self.id)
        print('FILE MODE:', mode)

        try:
            if mode:
                self.data = open(self.path, 'wb')
                return 'new'
            else:
                self.data = open(self.path, 'r+b')
            if str(self.data.read(8))[2:-1] == 'chunkzip':
                t = BytesIO()
                # t=open('fifa_tools\\'+self.path.split(sep='\\')[-1]+'.decompressed','wb')
                self.data.read(12)
                sec_num = struct.unpack('>I', self.data.read(4))[0]
                self.data.read(8)
                for i in range(sec_num):
                    # Uniform the offset
                    off = self.data.tell() % 4
                    # print('Unzlibing section',i , 'Offset', hex(f.data.tell()),off)

                    if off:
                        self.data.read(4 - off)

                    # find sec length
                    sec_found = False
                    while not sec_found:
                        sec_len = struct.unpack('>I', self.data.read(4))[0]
                        if not sec_len == 0:
                            sec_found = True

                    self.data.read(4)  # Skip 00 00 00 01
                    data = self.data.read(sec_len)  # Store part

                    try:
                        t.write(zlib.decompress(data, -15))
                    except zlib.error:
                        return 'corrupt_file'

                # self.data=open(t.name,'r+b')
                self.data = t

            self.data.seek(8)
            original_size = struct.unpack('<I', self.data.read(4))[0]
            f_size = len(self.data.read()) + 12

            # Clopy Checking
            if not original_size == f_size and ext == 'rx3' and self.type == 'stadium' and scn.game_enum in ['0', '2']:
                e = open('fifa_tools\\scripts\\msg', 'r')
                print(e.read())
                print('                           I SEE WHAT YOU DID THERE')
                e.close()
                return 'file_clopy'

            self.data.seek(0)
            return(self)

        except IOError as e:
            return 'io_error'

    def overwrite_geometry_data(self):
        scn = bpy.context.scene
        # file is an already opened file, needs to close
        # READ THE COPIED FILE
        self.file_ident()
        self.read_file_offsets(dir)

        print('----------------------------')
        print(
            'SEARCHING FOR ' + str(self.type).upper() + ' PARTS IN THE SCENE')

        progress = 0  # store processed parts
        for i in range(len(self.mesh_offsets)):
            try:
                name = self.type + '_' + self.id + '_' + str(i)
                if self.type == 'head':
                    name = name + '_' + self.sub_names[i]
                object = bpy.data.objects[name]
                progress += 1
                print('PROCESSING PART ', name)
            except KeyError:
                print('PART ', name, ' NOT FOUND')
                continue

            verts = []
            uvs = []
            cols = []
            indices = []

            opts = self.mesh_descr_convert(self.mesh_descrs[i])
            print(opts)
            verts, uvs, cols, indices = self.convert_original_mesh_to_data(
                object)  # get new geometry data
            #print('Part Description: ',opts,'\n','Part Vertices: ',len(verts),'\n','Part UV maps: ',e.uvcount[i],'\n','Part Indices: ',len(indices),'\n','Part Color maps: ',e.colcount[i])

            # get to geometry data offset
            self.data.seek(self.mesh_offsets[i][0] + 16)
            self.convert_mesh_to_bytes(
                opts, len(verts), verts, uvs, cols)  # write geometry data
            # print(e.data.tell())
            if not scn.trophy_flag:
                # get to indices data offset
                self.data.seek(self.indices_offsets[i][0] + 16)
                self.write_indices(indices)  # write indices data

            print('----------------------------')
            print('OVERWRITTEN ', str(progress), '/',
                  str(len(self.mesh_offsets)), ' PARTS \n')
        self.data.close()

    def convert_original_mesh_to_data(self, object):
        verts = []
        uvs = []
        indices = []
        cols = []
        data = object.data
        bm = bmesh.new()
        bm.from_mesh(data)
        uvs_0 = []
        uvs_1 = []
        uvs_2 = []
        uvs_3 = []
        uvs_4 = []
        uvs_5 = []
        uvs_6 = []
        uvs_7 = []
        col_0 = []
        col_1 = []
        col_2 = []

        uvcount = len(bm.loops.layers.uv)
        colcount = len(bm.loops.layers.color)

        rot_x_mat = Matrix.Rotation(radians(90), 4, 'X')
        scale_mat = Matrix.Scale(100, 4)

        for vert in bm.verts:
            co = scale_mat * rot_x_mat * object.matrix_world * vert.co
            verts.append((co[0], -co[1], -co[2]))

        for i in range(len(bm.verts)):
            for j in range(uvcount):
                uvlayer = bm.loops.layers.uv[j]
                eval(
                    'uvs_' + str(j) + '.append((round(bm.verts[i].link_loops[0][uvlayer].uv.x,8),round(1-bm.verts[i].link_loops[0][uvlayer].uv.y,8)))')

        for i in range(len(bm.verts)):
            for j in range(colcount):
                collayer = bm.loops.layers.color[j]
                vert_data = bm.verts[i].link_loops[0][collayer]
                eval(
                    'col_' + str(j) + '.append((vert_data[0]*1023,vert_data[1]*1023,vert_data[2]*1023))')

        for f in bm.faces:
            indices.append(
                (f.verts[0].index, f.verts[1].index, f.verts[2].index))

        for j in range(uvcount):
            eval('uvs.append(uvs_' + str(j) + ')')
        for j in range(colcount):
            eval('cols.append(col_' + str(j) + ')')

        bm.free()
        return verts, uvs, cols, indices

    def convert_mesh_to_bytes(self, opts, count, verts, uvs, cols):
        for i in range(count):
            for o in opts:
                if o[0] == 'p':  # verts
                    if o[3:] == '4f16':
                        gh.write_half_verts(self.data, verts[i])
                    else:
                        self.data.write(struct.pack(
                            '<3f', round(verts[i][0], 8), round(verts[i][1], 8), round(verts[i][2], 8)))
                elif o[0] == 'n':  # col0
                    col = (
                        int(cols[0][i][0]) << 20) + (int(cols[0][i][1]) << 10) + (int(cols[0][i][2]))
                    self.data.write(struct.pack('<I', col))
                elif o[0] == 'g':  # col1
                    col = (
                        int(cols[1][i][0]) << 20) + (int(cols[1][i][1]) << 10) + (int(cols[1][i][2]))
                    self.data.write(struct.pack('<I', col))
                    # self.data.read(4)
                elif o[0] == 'b':  # col2
                    col = (
                        int(cols[2][i][0]) << 20) + (int(cols[2][i][1]) << 10) + (int(cols[2][i][2]))
                    self.data.write(struct.pack('<I', col))
                elif o[0] == 't':  # uvs
                    huvx = eval('comp.compress(round(uvs[int(o[1])][i][0],8))')
                    huvy = eval('comp.compress(round(uvs[int(o[1])][i][1],8))')
                    self.data.write(struct.pack('<HH', huvx, huvy))
                elif o[0] == 'i':  # bone indices
                    if o[3:] == '4u8':
                        self.data.read(4)
                    elif o[3:] == '4u16':
                        self.data.read(8)
                elif o[0] == 'w':  # bone weights
                    self.data.read(4)

    def read_file_offsets(self, dir):
        scn = bpy.context.scene
        print('READING FILE OFFSETS...')
        log = open('fifa_tools\\log.txt', 'w')

        for offset in self.offsets:
            if offset[0] == 3263271920:  # MESH DESCRIPTIONS
                self.read_mesh_descr(offset[1])
            elif offset[0] == 2047566042:  # TEXTURES
                self.read_texture(offset[1], dir)
                self.texture_count += 1
            elif offset[0] == 4034198449 and scn.collision_flag:  # COLLISIONS
                # print('READING COLLISION OBJECTS')
                self.read_collision(offset[1])
            elif offset[0] == 685399266:  # PROP POSITIONS
                self.read_prop_positions(offset[1])
            elif offset[0] == 1285267122:  # PROPS
                self.read_props(offset[1], self.endian)
            elif offset[0] == 2116321516:  # GROUPS
                log.write('Group Offset: ' + str(offset[1]))
                log.write('\n')
                self.read_group(offset[1])
                self.group_count += 1
            elif offset[0] == 230948820:  # GROUP NAMES
                self.read_group_names(offset[1])
            elif offset[0] == 123459928:  # MATERIALS
                # print('CREATING MATERIAL')
                self.create_material(offset[1], self.material_count)
                self.material_count += 1
            elif offset[0] == 5798132:  # INDICES
                if scn.trophy_flag:
                    temp = gh.facereadstrip(self.data, offset[1], self.endian)
                else:
                    temp = gh.facereadlist(self.data, offset[1], self.endian)
                self.itable.append(temp[0])
                self.indices_offsets.append((offset[1], temp[1]))
            elif offset[0] == 3751472158:  # BONES
                log.write('Bones Detected')
                self.data.seek(offset[1])
                size = struct.unpack(self.endian + 'I', self.data.read(4))[0]
                bc = struct.unpack(self.endian + 'I', self.data.read(4))[0]
                self.data.read(8)
                self.bones.append(self.read_bones(bc))
                # round((size-int('B0',16))/16)
            # MESH DATA
            elif offset[0] == 5798561 and scn.geometry_flag:
                # print('READING MESH DATA')
                self.data.seek(offset[1])
                self.data.read(4)
                vc = struct.unpack(self.endian + 'I', self.data.read(4))[0]
                chunk_length = struct.unpack(
                    self.endian + 'I', self.data.read(4))[0]
                self.mesh_offsets.append([offset[1], chunk_length])
                count = len(self.mesh_offsets) - 1
                self.data.read(4)
                log.write('Mesh Count: %3d || Vert Count: %5d || Chunk Length: %2d || File Offset: %7d || Of Type: %s' % (
                    self.mesh_count, vc, chunk_length, offset[1], self.type))

                temp = self.read_test(self.data, self.mesh_descrs[count], vc)

                self.vxtable.append(temp[0])
                self.cols.append(temp[1])
                self.colcount.append(len(temp[1]))
                self.uvs.append(temp[2])
                self.uvcount.append(len(temp[2]))
                self.v_bones_i.append(temp[3])
                self.v_bones_w.append(temp[4])
                self.mesh_count += 1

                log.write('\n')

        print('FILE OFFSETS READ SUCCESSFULLY')
        log.close()
        # IDENTIFY THE FILE

    def file_ident(self):
        self.container_type, self.endianess, self.endian, self.size, self.offsets, self.count = self.file_ident_func()

    def file_ident_func(self):
        print('FILE IDENTIFICATION IN PROGRESS')
        offsets = []
        name = str(self.data.read(3))[2:-1]
        endian = str(self.data.read(1))[2:-1]
        if endian == 'b':
            endian = '>'
            endianstr = 'Big Endian'
        elif endian == 'l':
            endian = '<'
            endianstr = 'Little Endian'
        print('ENDIANNESS DETECTED: ', endianstr)

        self.data.read(4)
        filesize = struct.unpack(endian + 'I', self.data.read(4))[0]
        sect_num = struct.unpack(endian + 'I', self.data.read(4))[0]
        print('DESCRIPTIONS DETECTED: ', sect_num)

        # Populate Offset List
        for i in range(0, sect_num):
            offsets.append((struct.unpack(endian + 'I', self.data.read(4))
                            [0], struct.unpack(endian + 'I', self.data.read(4))[0]))
            self.data.read(8)

        # OFFSET PRINTING
        # for off in offsets:
        #   print(off)

        mesh_count = struct.unpack(endian + 'I', self.data.read(4))[0]
        print('MESH OBJECTS: ', mesh_count)

        return name, endianstr, endian, ('Total File Size:', round((filesize / 1024), 2), 'KBs'), offsets, mesh_count

    def read_mesh_descr(self, offset):
        self.data.seek(offset)
        self.data.read(4)
        length = struct.unpack(self.endian + 'i', self.data.read(4))[0]
        self.data.read(8)

        descr_str = ''
        list = []
        temp = []
        part = ''

        vflag = 0
        uvcount = 0
        cols = 0
        bones_i = False
        bones_w = False

        for i in self.data.read(length):

            if i == 32 or i == 0:
                temp.append(part)
                list.append(temp)
                temp = []
                part = ''
            elif i == 58:
                temp.append(part)
                part = ''
            else:
                part = part + chr(i)

        self.mesh_descrs.append(list)

    def read_test(self, f, opts, count):
        # counters
        uvcount = 0
        colcount = 0
        # lists init
        verts = []
        uvs = []
        cols = []
        cols_0 = []
        cols_1 = []
        cols_2 = []
        uvs_0, uvs_1, uvs_2, uvs_3, uvs_4, uvs_5, uvs_6, uvs_7 = [
        ], [], [], [], [], [], [], []
        bones_i0 = []
        bones_i1 = []
        bones_w = []
        bones_c = []

        # print(opts)
        for i in range(count):
            uvcount = 0
            colcount = 0
            for j in opts:
                if j[0][0] == 'p':
                    if j[4] == '3f32':
                        verts.append(gh.read_vertices_1(f))  # READ VERTICES
                    elif j[4] == '4f16':
                        verts.append(gh.read_vertices_0(f))
                elif j[0][0] == 't':
                    if j[4] == '2f32':
                        eval(
                            'uvs_' + str(j[0][1]) + '.append(gh.read_uvs_1(f))')
                    elif j[4] == '2f16':
                        eval(
                            'uvs_' + str(j[0][1]) + '.append(gh.read_uvs_0(f))')
                    uvcount += 1
                elif j[0][0] == 'n':
                    colcount += 1
                    cols_0.append(gh.read_cols(f))
                elif j[0][0] == 'b':
                    colcount += 1
                    cols_2.append(gh.read_cols(f))
                elif j[0][0] == 'g':
                    colcount += 1
                    cols_1.append(gh.read_cols(f))
                elif j[0][0] == 'i':
                    if j[4] == '4u8':
                        eval(
                            'bones_i' + str(j[0][1]) + '.append(struct.unpack(\'<4B\',f.read(4)))')
                    elif j[4] == '4u16':
                        eval(
                            'bones_i' + str(j[0][1]) + '.append(struct.unpack(\'<4H\',f.read(8)))')
                elif j[0][0] == 'w':
                    bones_w.append(struct.unpack('<4B', f.read(4)))
                elif j[0][0] == 'c':
                    bones_c.append(struct.unpack('<4B', f.read(4)))

        # STORE COLORS UVS AND BONES
        for j in range(uvcount):
            eval('uvs.append(uvs_' + str(j) + ')')
        for j in range(colcount):
            eval('cols.append(cols_' + str(j) + ')')

        # print(verts)
        return verts, cols, uvs, bones_i0, bones_w

    def mesh_descr_convert(self, descr):
        opts = []
        for i in descr:
            opts.append(i[0] + ':' + i[4])
        return opts

    def read_props(self, offset, endian):
        self.data.seek(offset)
        self.data.read(4)
        count = struct.unpack(endian + 'i', self.data.read(4))[0]
        self.data.read(8)
        print('READING PROPS', 'COUNT: ', count)

        if self.type.endswith('_texture'):
            # Initialize array
            for i in range(count):
                self.tex_names.append('')

            for i in range(count):
                self.data.read(4)
                textlen = struct.unpack(endian + 'i', self.data.read(4))[0]
                text = ''
                for j in range(textlen):
                    text = text + \
                        chr(struct.unpack(endian + 'B', self.data.read(1))[0])
                text = text[0:-1]
                try:
                    path = os.path.join(
                        prePath, 'fifa_tools', 'texture_' + str(i) + '.dds')
                    destpath = os.path.join(
                        prePath, 'fifa_tools', text + '.dds')
                    os.rename(path, destpath)
                    print(
                        'Renaming texture_' + str(i) + '.dds to ' + text + '.dds')
                    self.tex_names[i] = text + '.dds'
                except FileNotFoundError:
                    print('Unsupported Image File')
                except FileExistsError:
                    print('!!!File Exists!!!')
                    self.tex_names[i] = text + '.dds'

        else:
            for i in range(count):
                off = struct.unpack(endian + 'I', self.data.read(4))[0]
                textlen = struct.unpack(endian + 'I', self.data.read(4))[0]
                text = ''
                # text=fifa_func.read_string(self.data)
                for j in range(textlen):
                    text = text + \
                        chr(struct.unpack(endian + 'B', self.data.read(1))[0])
                text = text[0:-1]

                if off == 685399266:
                    self.props.append(text)
                    self.prop_count += 1
                elif off == 3566041216:
                    # print(text,textlen)
                    self.sub_names.append(
                        text.split(sep='.')[0].split(sep='_')[0])
                elif off == 2047566042:
                    self.tex_names.append(text + '.dds')

    def read_prop_positions(self, offset):
        self.data.seek(offset)
        self.data.read(4)
        temp = struct.unpack('<3f', self.data.read(12))
        rot = struct.unpack('<3f', self.data.read(12))
        self.prop_positions.append(
            (0.01 * temp[0], -0.01 * temp[2], 0.01 * temp[1]))
        self.prop_rotations.append((rot[0], rot[1], rot[2]))

    def read_bones(self, count):
        temp = []
        for k in range(count):
            mat = Matrix()
            mat = mat.to_4x4()
            for i in range(4):
                for j in range(4):
                    mat[j][i] = round(
                        struct.unpack('<f', self.data.read(4))[0], 8)

            #pos = mat.to_translation()
            pos = Vector((mat[0][3], mat[1][3], mat[2][3]))

            if k in [2, 3, 4, 324, 333]:
                print('Matrix ID= ', k)
                # print(mat.to_euler())
                # print(mat.to_scale())
                print(pos)

            rot = mat.to_euler()

            if not rot[0] == 0:
                sx = round(rot[0] / abs(rot[0]), 1)
            else:
                sx = 1.0

            if not rot[1] == 0:
                sy = round(rot[1] / abs(rot[1]), 1)
            else:
                sy = 1.0

            if not rot[2] == 0:
                sz = round(rot[2] / abs(rot[2]), 1)
            else:
                sz = 1.0

            # Vector.rotate(pos,rot)
            axis, roll = gh.mat3_to_vec_roll(mat.to_3x3())
            #pos = rot*pos
            if k in [2, 3, 4, 324, 333]:
                #print('Matrix ID= ',k)
                # print(mat.to_euler())
                # print(mat.to_scale())
                print(sz)
                print(pos)
            # bone.head=pos, #bone.tail=pos+axis, #bone.roll=roll
            temp.append((pos, pos + axis, roll))
        return temp

    # Create Texture Function
    def read_texture(self, offset, path):
        print('Seeking to texture offset: ', offset)

        self.data.seek(offset)
        overall_size = struct.unpack(self.endian + 'I', self.data.read(4))[0]
        self.data.read(1)
        identifier = struct.unpack(self.endian + 'B', self.data.read(1))[0]
        self.data.read(2)
        width = struct.unpack(self.endian + 'H', self.data.read(2))[0]
        height = struct.unpack(self.endian + 'H', self.data.read(2))[0]
        self.data.read(2)
        mipmaps = struct.unpack(self.endian + 'H', self.data.read(2))[0]
        print('Texture Information: ', width, height, mipmaps, identifier)

        self.data.read(8)
        size = struct.unpack(self.endian + 'I', self.data.read(4))[0]
        self.data.read(4)

        if identifier == 0:
            data = tex_gh.read_dds_header(0)
            # data[87]=49
            string = 'DXT1'
        elif identifier == 1:
            data = tex_gh.read_dds_header(0)
            data[87] = 51
            string = 'DXT3'
        elif identifier == 2:
            data = tex_gh.read_dds_header(144)
            # data[87]=53
            string = 'DXT5'
        elif identifier == 7:
            data = tex_gh.read_dds_header(288)
            # data[86]=49
            # data[87]=48
            string = 'NVTT'
        else:
            print('NOT RECOGNISABLE IMAGE FILE')
            return

        # Assign Changed Values
        data[12] = height.to_bytes(2, 'little')[0]
        data[13] = height.to_bytes(2, 'little')[1]
        data[16] = width.to_bytes(2, 'little')[0]
        data[17] = width.to_bytes(2, 'little')[1]
        data[28] = mipmaps.to_bytes(1, 'little')[0]

        # log=open('fifa_tools\\log.txt','a')
        #log.write('Writing File: ' +path+'texture_'+str(self.texture_count)+'.dds'+' From File Offset '+str(offset)+ ' Of Type:'+string)
        # log.write('\n')

        path = os.path.join(
            prePath, 'fifa_tools', 'texture_' + str(self.texture_count) + '.dds')
        tf = open(path, 'wb')
        [tf.write(b) for b in [struct.pack('<B', x) for x in data]]

        for i in range(mipmaps):
            print('Mipmap offset: ', self.data.tell(), 'Size: ', size)
            tf.write(self.data.read(size))
            self.data.read(8)
            size = struct.unpack(self.endian + 'I', self.data.read(4))[0]
            self.data.read(4)

        # print(data)
        # log.close()
        tf.close()

    def create_material(self, offset, count):
        self.data.seek(offset)
        self.data.read(4)
        tex_num = struct.unpack(self.endian + 'i', self.data.read(4))[0]
        self.data.read(8)
        entry = []
        mat_name = gh.read_string(self.data) + '_' + str(count)

        # print(len(self.tex_names))
        for i in range(tex_num):
            texture_type = gh.read_string(self.data)
            # slot=new_mat.texture_slots.add()
            tex_id = struct.unpack('<i', self.data.read(4))[0]
            texture_name = texture_type + '_' + str(tex_id)
            # print(tex_id)
            try:
                entry.append(
                    (texture_name, 'fifa_tools\\' + self.tex_names[tex_id]))
            except:
                entry.append(
                    (texture_name, 'fifa_tools\\texture_' + str(tex_id)))

        self.materials.append((mat_name, entry))

        return {'FINISHED'}

    def read_group(self, offset):
        scn = bpy.context.scene
        name = 'group_' + str(self.group_count)
        # print(name)
        self.data.seek(offset)
        self.data.read(4)
        group_status = struct.unpack(self.endian + 'I', self.data.read(4))[0]

        if not group_status:
            return

        self.data.read(72)
        vec1 = Vector((struct.unpack(self.endian + 'f', self.data.read(4))[0], struct.unpack(
            self.endian + 'f', self.data.read(4))[0], struct.unpack(self.endian + 'f', self.data.read(4))[0]))
        self.data.read(4)
        vec2 = Vector((struct.unpack(self.endian + 'f', self.data.read(4))[0], struct.unpack(
            self.endian + 'f', self.data.read(4))[0], struct.unpack(self.endian + 'f', self.data.read(4))[0]))
        self.data.read(4)
        group_items = struct.unpack(self.endian + 'i', self.data.read(4))[0]
        self.data.read(4)
        if scn.geometry_flag:
            gh.create_boundingbox(vec1, vec2, name)

        for i in range(group_items):
            ivec1 = Vector((struct.unpack(self.endian + 'f', self.data.read(4))[0], struct.unpack(
                self.endian + 'f', self.data.read(4))[0], struct.unpack(self.endian + 'f', self.data.read(4))[0]))
            self.data.read(4)
            ivec2 = Vector((struct.unpack(self.endian + 'f', self.data.read(4))[0], struct.unpack(
                self.endian + 'f', self.data.read(4))[0], struct.unpack(self.endian + 'f', self.data.read(4))[0]))
            self.data.read(4)
            self.bboxtable.append((ivec1, ivec2))
            part_id = struct.unpack(self.endian + 'i', self.data.read(4))[0]
            render_line = struct.unpack(
                self.endian + 'i', self.data.read(4))[0]
            self.mat_assign_table.append(
                (part_id, render_line, self.group_count))

    def read_group_names(self, offset):
        self.data.seek(offset)
        self.data.read(16)
        group_name = gh.read_string(self.data)
        # print(group_name)
        self.group_names.append(group_name)

    def read_collision(self, offset):
        self.data.seek(offset)
        self.data.read(16)
        name = gh.read_string(self.data)
        self.data.read(4)
        triscount = struct.unpack('<I', self.data.read(4))[0]
        indices = []
        verts = []
        j = 0  # COUNTER FOR INDICES
        for i in range(triscount):
            for k in range(3):  # 3 VERTICES
                temp = struct.unpack('<3f', self.data.read(12))
                verts.append((temp[0] / 100, -temp[2] / 100, temp[1] / 100))
            # TRIANGLE DEFINITION
            indices.append((j, j + 1, j + 2))
            j += 3

        self.collisions.append((name, verts, indices))

    def write_offsets_to_file(self):
        # Calculate file size
        size = 0
        for off in self.offset_list:
            size += off[2] + 16
        # File Header
        self.data.write(
            struct.pack('<4I', 1815304274, 4, size + 16, len(self.offset_list)))
        for i in self.offset_list:
            self.data.write(struct.pack('<4I', i[0], i[1], i[2], 0))

    def write_offset_data_to_file(self, path):
        # Local Variables
        object_count = len(self.object_list)
        texture_count = len(self.texture_list)
        for i in range(len(self.offset_list)):
            self.data.seek(self.offset_list[i][1])
            if self.offset_list[i][0] == 582139446:
                self.data.write(struct.pack('<4I', object_count, 0, 0, 0))
                for j in range(object_count):
                    if self.object_list[j].vertsCount > 65535:
                        ind_size = 4
                    else:
                        ind_size = 2
                    self.data.write(struct.pack('<4I', gh.size_round(self.object_list[
                                    j].indicesCount * ind_size + 16), self.object_list[j].indicesCount, ind_size, 0))
            elif self.offset_list[i][0] == 3263271920:  # mesh description
                id = self.offset_list[i][3]
                self.data.write(struct.pack(
                    '<4I', self.offset_list[i][2], len(self.object_list[id].meshDescr) + 1, 0, 0))
                s = bytes(self.object_list[id].meshDescr, 'utf-8')
                self.data.write(s)
            elif self.offset_list[i][0] == 685399266:  # PROP POSITIONS
                id = self.offset_list[i][3]
                self.data.write(struct.pack('<Ifff', self.offset_list[i][2], self.prop_list[
                                id][1][0], self.prop_list[id][1][1], self.prop_list[id][1][2]))
                self.data.write(struct.pack('<fffI', self.prop_list[id][2][
                                0], self.prop_list[id][2][1], self.prop_list[id][2][2], 0))
            elif self.offset_list[i][0] == 1285267122:  # PROPS
                # header
                self.data.write(struct.pack('<4I', self.offset_list[i][2], len(
                    self.prop_list) + len(self.texture_list) + len(self.object_list), 0, 0))
                # data
                for j in range(len(self.prop_list)):
                    self.data.write(
                        struct.pack('<2I', 685399266, len(self.prop_list[j][0]) + 1))
                    s = bytes(self.prop_list[j][0], 'utf-8')
                    self.data.write(s)
                    self.data.write(b'\x00')
                for j in range(len(self.object_list)):
                    self.data.write(
                        struct.pack('<2I', 3566041216, len(self.object_list[j].name) + 1))
                    s = bytes(self.object_list[j].name, 'utf-8')
                    self.data.write(s)
                    self.data.write(b'\x00')
                for j in range(len(self.texture_list)):
                    self.data.write(struct.pack('<I', 2047566042))
                    print(self.texture_list[j])
                    if type(self.texture_list[j]) == type(''):
                        s = bytes(self.texture_list[j], 'utf-8')
                        self.data.write(
                            struct.pack('<I', len(self.texture_list[j]) + 1))

                    elif type(self.texture_list[j][0]) == type(''):
                        # print('textures')
                        s = bytes(self.texture_list[j][0], 'utf-8')
                        self.data.write(
                            struct.pack('<I', len(self.texture_list[j][0]) + 1))

                    self.data.write(s)
                    self.data.write(b'\x00')

            elif self.offset_list[i][0] == 5798132:  # INDICES
                id = self.offset_list[i][3]
                # header
                if self.object_list[id].vertsCount > 65535:
                    ind_size = 4
                else:
                    ind_size = 2
                self.data.write(struct.pack('<4I', gh.size_round(self.object_list[
                                id].indicesCount * ind_size + 16), self.object_list[id].indicesCount, ind_size, 0))
                # data
                self.write_indices(self.object_list[id].indices)
            elif self.offset_list[i][0] == 5798561:  # VERTICES
                id = self.offset_list[i][3]
                # header
                self.data.write(struct.pack('<4I', self.offset_list[i][2], self.object_list[
                                id].vertsCount, self.object_list[id].chunkLength, 1))
                # data
                self.convert_mesh_to_bytes(self.object_list[id].meshDescrShort, self.object_list[id].vertsCount, self.object_list[
                                           id].verts, self.object_list[id].uvs, self.object_list[id].colors)
            elif self.offset_list[i][0] == 3566041216:  # 80......
                self.data.write(struct.pack('<4I', 4, 0, 0, 0))
            elif self.offset_list[i][0] == 230948820:  # GROUPS
                id = self.offset_list[i][3]
                # print(id,len(group_list))
                # header
                data = self.data.write(
                    struct.pack('<4I', self.offset_list[i][2], 1, 0, 0))
                # data
                if id >= len(self.group_list):
                    s = bytes('CollisionGeometry', 'utf-8')
                    data += self.data.write(s)
                    data += self.data.write(b'\x00')
                    data += self.data.write(struct.pack('B', id))
                else:
                    s = bytes(self.group_list[id][0][5:], 'utf-8')
                    self.data.write(s)
                    self.data.write(b'\x00')
                    self.data.write(struct.pack('B', id))
            elif self.offset_list[i][0] == 123459928:
                id = self.offset_list[i][3]
                # material header
                self.data.write(struct.pack('<4I', self.offset_list[i][2], len(
                    self.material_dict[self.material_list[id]][3]), 0, 0))
                # data
                # material_name
                # print(material_dict[material_list[id]][1])
                s = bytes(
                    self.material_dict[self.material_list[id]][1], 'utf-8')
                self.data.write(s)
                self.data.write(b'\x00')
                # textures
                for j in range(len(self.material_dict[self.material_list[id]][2])):
                    s = bytes(
                        self.material_dict[self.material_list[id]][3][j], 'utf-8')
                    self.data.write(s)
                    self.data.write(b'\x00')
                    # print(self.texture_list.index(material_dict[material_list[id]][2][j]))
                    self.data.write(struct.pack(
                        'I', self.texture_list.index(self.material_dict[self.material_list[id]][2][j])))
            elif self.offset_list[i][0] == 2116321516:  # RENDERLINES
                id = self.offset_list[i][3]
                # renderline header
                self.data.write(
                    struct.pack('<4I', self.offset_list[i][2], 1, 4294967295, 0))
                # renderline data
                self.data.write(struct.pack('<4f', 1, 0, 0, 0))
                self.data.write(struct.pack('<4f', 0, 1, 0, 0))
                self.data.write(struct.pack('<4f', 0, 0, 1, 0))
                self.data.write(struct.pack('<4f', 0, 0, 0, 1))
                self.data.write(struct.pack('<4f', self.group_list[id][1][
                                0], self.group_list[id][1][1], self.group_list[id][1][2], 1))
                self.data.write(struct.pack('<4f', self.group_list[id][2][
                                0], self.group_list[id][2][1], self.group_list[id][2][2], 1))
                self.data.write(
                    struct.pack('<2I', self.group_list[id][3], 4294967295))
                object_offset = self.group_list[id][4]
                for j in range(self.group_list[id][3]):
                    self.data.write(struct.pack('<4f', self.object_list[object_offset + j].boundBox[0][0], self.object_list[
                                    object_offset + j].boundBox[0][1], self.object_list[object_offset + j].boundBox[0][2], 1))
                    self.data.write(struct.pack('<4f', self.object_list[object_offset + j].boundBox[1][0], self.object_list[
                                    object_offset + j].boundBox[1][1], self.object_list[object_offset + j].boundBox[1][2], 1))
                    self.data.write(struct.pack(
                        '<2I', object_offset + j, self.object_list[object_offset + j].material))
            elif self.offset_list[i][0] == 4034198449:  # COLLISIONS
                id = self.offset_list[i][3]
                self.data.write(
                    struct.pack('4I', self.offset_list[i][2], 1, 0, 0))
                s = bytes(self.collision_list[id][2], 'utf-8')
                self.data.write(s)
                self.data.write(b'\x00')
                self.data.write(struct.pack('I', 1))
                self.data.write(struct.pack('I', self.collision_list[id][0]))
                for i in range(len(self.collision_list[id][1])):
                    self.data.write(struct.pack('<3f', self.collision_list[id][1][i][
                                    0], self.collision_list[id][1][i][1], self.collision_list[id][1][i][2]))

            elif self.offset_list[i][0] == 1808827868:
                self.data.write(struct.pack('<4I', texture_count, 0, 0, 0))
                id = 0
                for tex in self.texture_list:
                    if tex[7] == 'DXT5':
                        id = 2
                    self.data.write(
                        struct.pack('<IBBHHHHH', tex[6], 1, id, 1, tex[3], tex[4], 1, tex[5]))
            elif self.offset_list[i][0] == 2047566042: # TEXTURES
                id = self.offset_list[i][3]
                # texture writing
                ext_len = len(
                    self.texture_list[id][1].split(sep=os.sep)[-1].split(sep='.')[-1])
                # t=open(self.texture_list[id][1].split(sep='\\')[-1][0:-1-ext_len]+'.dds','rb')
                t = open(self.texture_list[id][1], 'rb')

                # Get ready to write
                divider = 1
                comp_id = 0
                w = self.texture_list[id][3]
                h = self.texture_list[id][4]
                phys_size = w * h
                mipmaps = self.texture_list[id][5]
                if self.texture_list[id][7] == 'DXT1':
                    divider = 2
                if self.texture_list[id][7] == 'DXT5':
                    comp_id = 2
                t.seek(128)

                print(
                    'Writing Texture: ', self.texture_list[id][1], w, h, mipmaps)

                # Write texture
                # header
                self.data.write(struct.pack('<IBBHHHHH', self.texture_list[id][6], 1, comp_id, 1, self.texture_list[
                                id][3], self.texture_list[id][4], 1, self.texture_list[id][5]))
                # data
                for j in range(mipmaps):
                    tw = w * h // divider
                    pitch = w * 4 // divider  # calculating texture pitch
                    #print('Writing mipmap: ',j, 'data: ',pitch,tw//pitch,tw,self.data.tell())

                    self.data.write(
                        struct.pack('<4I', pitch, tw // pitch, tw, 0))
                    self.data.write(t.read(tw))
                    # print(tw)
                    w = max(w // 2, 4)
                    h = max(h // 2, 4)
                t.close()

    def write_offsets(self, data_pass):
        # Useful variables:
        object_count = len(self.object_list)
        material_count = len(self.material_list)
        group_count = len(self.group_list)
        prop_count = len(self.prop_list)
        collision_count = len(self.collision_list)
        scn = bpy.context.scene

        # offset_list format: IDENTIFIER  OFFSET   SIZE  ID
        if data_pass == 0:
            self.offset_list.append([582139446, 0, 0])
            for i in range(object_count):
                self.offset_list.append([3263271920, 0, 0, i])
            self.offset_list.append([1285267122, 0, 0])
            for i in range(object_count):
                self.offset_list.append([5798132, 0, 0, i])

            # HEAD SPECIFIC
            if scn.face_edit_head_flag:
                for i in range(object_count):
                    self.offset_list.append([255353250, 0, 0, i])

            for i in range(object_count):
                self.offset_list.append([5798561, 0, 0, i])

            # HEAD SPECIFIC
            if scn.face_edit_head_flag:
                for i in range(object_count):
                    self.offset_list.append([3751472158, 0, 0, i])

            for i in range(object_count):
                self.offset_list.append([3566041216, 0, 0, i])

            # STADIUM SPECIFICS
            if scn.stadium_export_flag:
                for i in range(prop_count):
                    self.offset_list.append([685399266, 0, 0, i])
                for i in range(collision_count):
                    self.offset_list.append([4034198449, 0, 0, i])
                for i in range(material_count):
                    self.offset_list.append([123459928, 0, 0, i])
                for i in range(group_count):
                    self.offset_list.append([2116321516, 0, 0, i])
                for i in range(group_count + 1):
                    self.offset_list.append([230948820, 0, 0, i])

        elif data_pass == 1:

            table_size = len(self.offset_list)

            for i in range(table_size):
                # Calculating Offsets
                if i == 0:
                    self.offset_list[i][1] = table_size * 16 + 16
                else:
                    self.offset_list[i][1] = self.offset_list[
                        i - 1][1] + self.offset_list[i - 1][2]

                # Calculating Sizes
                if self.offset_list[i][0] == 582139446:
                    self.offset_list[i][2] = 16 + len(self.object_list) * 16
                elif self.offset_list[i][0] == 1285267122:
                    size = 16
                    for j in range(len(self.prop_list)):
                        size += len(self.prop_list[j][0]) + 1 + 8
                    for j in range(len(self.object_list)):
                        size += len(self.object_list[j].name) + 1 + 8
                    for j in range(len(self.texture_list)):
                        size += len(self.texture_list[j]) + 1 + 8
                    self.offset_list[i][2] = gh.size_round(size)
                elif self.offset_list[i][0] == 3263271920:
                    # Local Variables
                    id = self.offset_list[i][3]
                    self.offset_list[i][2] = gh.size_round(
                        len(self.object_list[id].meshDescr) + 1 + 16)
                elif self.offset_list[i][0] == 5798132:
                    # Local Variables
                    id = self.offset_list[i][3]
                    if self.object_list[id].vertsCount > 65535:
                        ind_size = 4
                    else:
                        ind_size = 2
                    self.offset_list[i][2] = gh.size_round(
                        self.object_list[id].indicesCount * ind_size + 16)
                elif self.offset_list[i][0] == 5798561:
                    # Local Variables
                    id = self.offset_list[i][3]
                    self.offset_list[i][2] = gh.size_round(
                        16 + self.object_list[id].vertsCount * self.object_list[id].chunkLength)
                elif self.offset_list[i][0] == 3566041216:
                    self.offset_list[i][2] = 16
                elif self.offset_list[i][0] == 4034198449:
                    # Local Variables
                    id = self.offset_list[i][3]
                    self.offset_list[i][2] = gh.size_round(
                        16 + len(self.collision_list[id][2]) + 1 + 4 + self.collision_list[id][0] * 3 * 12)
                elif self.offset_list[i][0] == 685399266:
                    self.offset_list[i][2] = 32
                elif self.offset_list[i][0] == 123459928:
                    # Local Variables
                    id = self.offset_list[i][3]
                    self.offset_list[i][2] = self.material_dict[
                        self.material_list[id]][4]
                elif self.offset_list[i][0] == 230948820:
                    # Local Variables
                    id = self.offset_list[i][3]
                    try:
                        self.offset_list[i][2] = gh.size_round(
                            16 + len(self.group_list[id][0][5:]) + 5)
                    except IndexError:
                        self.offset_list[i][2] = 48
                elif self.offset_list[i][0] == 2116321516:
                    # Local Variables
                    id = self.offset_list[i][3]
                    self.offset_list[i][2] = gh.size_round(
                        16 + 4 * 16 + 32 + 8 + self.group_list[id][3] * 40)

    def write_indices(self, indices):
        # print('Indices Length: ',indices[0])
        if 3 * len(indices) > 65535:
            ind_size = 4
            format = '<III'
        else:
            ind_size = 2
            format = '<HHH'

        for entry in indices:
            self.data.write(struct.pack(format, entry[0], entry[1], entry[2]))


# GENERAL FIFA FUNCTIONS

def write_textures_to_file(textures_list, type, id):
    scn = bpy.context.scene
    if type == 'face':
        f_name = 'face_' + str(id) + '_0_0_0_0_0_0_0_0_textures.rx3'
    elif type == 'eyes':
        f_name = 'eyes_' + str(id) + '_0_textures.rx3'
    elif type == 'hair':
        f_name = 'hair_' + str(id) + '_0_textures.rx3'
    elif type == 'stadium':
        f_name = 'stadium_' + \
            str(id) + '_' + scn.stadium_version + '_textures.rx3'
    else:
        f_name = type + '_' + str(id) + '_textures.rx3'

    f = fifa_rx3(scn.export_path + f_name, 1)  # open file

    scn = bpy.context.scene
    status = texture_convert(textures_list)
    print('Total Number of textures: ', len(textures_list))
    if status.split(sep=',')[0] == 'texture_path_error':
        return 'missing_texture_file'
    # Read converted textures and calculate offsets and texture information
    f.offset_list, f.texture_list = read_converted_textures(
        f.offset_list, textures_list, 'fifa_tools\\')
    # print(f.offset_list)
    [print(i) for i in f.texture_list]

    # Calling Writing to file Functions

    try:
        f.write_offsets_to_file()
        f.write_offset_data_to_file('fifa_tools\\')
    except:
        print(sys.exc_info()[0])
        print('ERROR ON TEXTURE WRITING')
        f.data.close()
        return 'error'
    # Signature
    f.data.seek(f.offset_list[-1][1])
    f.data.seek(f.offset_list[-1][2], 1)
    s = bytes(sig, 'utf-8')
    f.data.write(s)
    f.data.close()
    print(f.offset_list)
    return 'success'


def read_converted_textures(offset_list, textures_list, path):
    offset_list.append(
        (1808827868, len(textures_list) * 16 + 48, len(textures_list) * 16 + 16))

    for k in range(len(textures_list)):
        print('Reading: ',textures_list[k][1])
        ext_len = len(
            textures_list[k][1].split(sep='\\')[-1].split(sep='.')[-1])
        t = open(textures_list[k][1], 'rb')

        width, height, mipmaps, textype = tex_gh.read_dds_info(t)
        textures_list[k][3], textures_list[k][4], textures_list[k][
            5], textures_list[k][7] = width, height, mipmaps, textype
        t.close()
        print(width, height, mipmaps, textype)

        phys_size = width * height
        divider = 1

        if textype == 'DXT1':
            divider = 2

        # Calculate Size
        size = 0
        for i in range(mipmaps):
            size = size + width * height // divider + 16
            width = max(width // 2, 4)
            height = max(height // 2, 4)

        # store size after calculation
        textures_list[k][6] = gh.size_round(size + 16)
        offset_list.append(
            (2047566042, offset_list[-1][1] + offset_list[-1][2], textures_list[k][6], k))

    size = 16
    for i in range(len(textures_list)):
        size = size + len(textures_list[i][0]) + 9

    offset_list.append(
        (1285267122, offset_list[-1][1] + offset_list[-1][2], gh.size_round(size)))

    return offset_list, textures_list


def crowd_seat_align(align_vector):
    scn = bpy.context.scene
    ob = bpy.context.object
    bm = bmesh.from_edit_mesh(ob.data)

    for i in range(len(bm.faces)):
        f=bm.faces[i]
        rotation_vector=align_vector
        if f.select:    
            base = f.calc_center_median()
            if align_vector == 'cursor':  # calculate cursor vector
                rotation_vector=scn.cursor_location - ob.matrix_world * base
                rotation_vector = Vector((rotation_vector.x, rotation_vector.y))
            
            angle = Vector((f.normal[0], f.normal[1])).angle_signed(
                rotation_vector)  # calculate declining angle
            print('Face ID', i, 'Angle: ',round(angle,4),degrees(angle))

            rot_mat = Matrix.Rotation(round(-angle, 8), 4, 'Z')

            for v in f.verts:
                v.co = v.co - base
                v.co = rot_mat * v.co
                v.co = v.co + base
            #f.normal_update()
    bm.normal_update()
    bmesh.update_edit_mesh(ob.data, False)


def crowd_seat_create(v_num, h_num, v_dist, h_dist, gap, context):
    scn = context.scene
    found_crowd = False
    # Check for crowd object
    if context.mode == 'EDIT_MESH':
        ob = context.object
        bm = bmesh.from_edit_mesh(ob.data)
        found_object = ob
        print(found_object)
    else:
        bm = bmesh.new()
        for ob in scn.objects:
            if ob.name == 'crowd':
                # ob=bpy.context.object
                found_object = ob
                bm.from_mesh(ob.data)
                found_crowd = True
                break

    cursor_loc = Vector(
        (scn.cursor_location[0], scn.cursor_location[1], scn.cursor_location[2]))
    val = 0.1
    for i in range(v_num):
        for j in range(h_num):
            bm.faces.new((bm.verts.new(Vector((cursor_loc[0] + val, cursor_loc[1] + val, cursor_loc[2] - val))),
                          bm.verts.new(
                              Vector((cursor_loc[0] - val, cursor_loc[1] + val, cursor_loc[2] - val))),
                          bm.verts.new(
                              Vector((cursor_loc[0] - val, cursor_loc[1] - val, cursor_loc[2] + val))),
                          bm.verts.new(Vector((cursor_loc[0] + val, cursor_loc[1] - val, cursor_loc[2] + val))))
                         )

            cursor_loc[0] -= h_dist * val
        cursor_loc[0] = scn.cursor_location[0]
        cursor_loc[1] += gap * val
        cursor_loc[2] -= v_dist * val

    bm.normal_update()

    if not found_crowd and context.mode == 'OBJECT':
        me = bpy.data.meshes.new('crowd')
        bm.to_mesh(me)
        ob = bpy.data.objects.new('crowd', me)
        context.scene.objects.link(ob)
    elif found_crowd:
        bm.to_mesh(found_object.data)
    elif context.mode == 'EDIT_MESH':
        bmesh.update_edit_mesh(found_object.data)

    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)


def crowd_groups(name):
    scn = bpy.context.scene
    ob = bpy.context.object
    bm = bmesh.from_edit_mesh(ob.data)

    # populate vertex list with selected vertices
    vxlist = []
    for v in bm.verts:
        if v.select == True:
            vxlist.append(v.index)
    bm.free()
    bpy.ops.object.editmode_toggle()

    flag = False
    while not flag:
        if name in ob.vertex_groups:
            name = name[:-1] + str(int(name[-1]) + 1)
        else:
            ob.vertex_groups.new(name)
            flag = True

    for g in ob.vertex_groups:
        if g.name == name:
            ob.vertex_groups[name].add(vxlist, 1, 'ADD')
        else:
            ob.vertex_groups[g.name].add(vxlist, 1, 'SUBTRACT')


def convert_mesh_init(object, mode):
    scn = bpy.context.scene
    verts = []
    norms = []
    uvs = []
    cols = []
    indices = []
    collist = []
    data = object.data
    print('Processing: ', object.name)
    bm = bmesh.new()
    bm.from_mesh(data)
    bm.normal_update()

    # STORE TRANSFORMATION
    if mode == 0:
        mesh_descr = ''
        mesh_descr_short = []

        boundbox = gh.object_bbox(object)

        # Constructing mesh description
        off = 0
        last = 0
        chunk_length = 0
        mesh_descr = 'p0:' + '{:02X}'.format(off) + ':00:0001:3f32' + ' '
        mesh_descr_short.append('p0:3f32')
        uvlen = len(bm.loops.layers.uv)
        for i in range(len(bm.loops.layers.color)):
            collist.append(bm.loops.layers.color[i].name)
        off += 12

        if len(collist) >= 1:
            mesh_descr += 'n0:' + '{:02X}'.format(off) + ':00:0001:3s10n' + ' '
            mesh_descr_short.append('n0:3s10n')
            off += 4

        if len(collist) >= 2:
            mesh_descr += 'g0:' + '{:02X}'.format(off) + ':00:0001:3s10n' + ' '
            mesh_descr_short.append('g0:3s10n')
            off += 4

        for i in range(uvlen):
            mesh_descr += 't' + \
                str(i) + ':' + '{:02X}'.format(off) + ':00:0001:2f16' + ' '
            mesh_descr_short.append('t' + str(i) + ':2f16')
            off += 4
            # last=4

        if object.name.split(sep='_')[0] in ['head', 'hair']:
            mesh_descr += 'i0:' + '{:02X}'.format(off) + ':00:0001:4u8' + ' '
            mesh_descr_short.append('i0:4u8')
            off += 4
            mesh_descr += 'w0:' + '{:02X}'.format(off) + ':00:0001:4u8' + ' '
            mesh_descr_short.append('w0:4u8')
            off += 4

        if len(collist) >= 3:
            mesh_descr += 'b0:' + '{:02X}'.format(off) + ':00:0001:3s10n' + ' '
            mesh_descr_short.append('b0:3s10n')
            off += 4

        mesh_descr = mesh_descr[0:-1]
        print(mesh_descr_short)
        bm.free()

        return collist, boundbox, mesh_descr, mesh_descr_short, off - last

    elif mode == 1:
        uvs_0 = []
        uvs_1 = []
        uvs_2 = []
        col_0 = []
        col_1 = []
        col_2 = []
        id = 0

        # Matrices
        object_matrix_wrld = object.matrix_world
        rot_x_mat = Matrix.Rotation(radians(-90), 4, 'X')
        # if scn.trophy_export_flag:
        scale_mat = Matrix.Scale(100, 4) # Keeping only this scale for FIFA 15
        # else:
        # scale_mat = Matrix.Scale(1000, 4)

        # Forced to Use Old Way for N-gons

        data.update(calc_tessface=True)  # convert ngons to tris
        uvcount = len(data.uv_layers)
        colcount = len(data.vertex_colors)

        for f in data.tessfaces:  # indices
            if len(f.vertices) == 4:
                indices.append((id, id + 1, id + 2))
                indices.append((id + 3, id, id + 2))
                id += 4
            else:
                indices.append((id, id + 1, id + 2))
                id += 3

            for vert in range(len(f.vertices)):
                co = scale_mat * rot_x_mat * object_matrix_wrld * \
                    data.vertices[f.vertices[vert]].co
                norm = scale_mat * rot_x_mat * object_matrix_wrld * \
                    data.vertices[f.vertices[vert]].normal
                verts.append((co[0], co[1], co[2]))
                norms.append((norm[0], norm[1], norm[2]))

                for k in range(uvcount):
                    u = eval(
                        'data.tessface_uv_textures[' + str(k) + '].data[' + str(f.index) + '].uv' + str(vert + 1) + '[0]')
                    v = 1 - \
                        eval(
                            'data.tessface_uv_textures[' + str(k) + '].data[' + str(f.index) + '].uv' + str(vert + 1) + '[1]')
                    eval('uvs_' + str(k) + '.append((round(u,8),round(v,8)))')
                for k in range(colcount):
                    r = eval('data.tessface_vertex_colors[' + str(k) + '].data[' + str(
                        f.index) + '].color' + str(vert + 1) + '[0]*1023')
                    g = eval('data.tessface_vertex_colors[' + str(k) + '].data[' + str(
                        f.index) + '].color' + str(vert + 1) + '[1]*1023')
                    b = eval('data.tessface_vertex_colors[' + str(k) + '].data[' + str(
                        f.index) + '].color' + str(vert + 1) + '[2]*1023')
                    eval('col_' + str(k) + '.append((r,g,b))')

        # New way
        # id=0
        # uvcount=len(bm.loops.layers.uv)
        # colcount=len(bm.loops.layers.color)
        # for f in bm.faces:
            # for l in f.loops:
                # co=scale_mat*rot_x_mat*object_matrix_wrld*l.vert.co
                # verts.append((co[0],co[1],co[2]))
                # uvs
                # for k in range(uvcount):
                    # layer=bm.loops.layers.uv[k]
                    # u=l[layer].uv.x
                    # v=1-l[layer].uv.y
                    # eval('uvs_'+str(k)+'.append((round(u,8),round(v,8)))')
                # for k in range(colcount):
                    # layer=bm.loops.layers.color[k]
                    # r=l[layer].r*1023
                    # g=l[layer].g*1023
                    # b=l[layer].b*1023
                    # eval('col_'+str(k)+'.append((r,g,b))')

                # Define a face for each loop
            # if len(f.loops)==4:
                # indices.append((id,id+1,id+2))
                # indices.append((id+3,id,id+2))
                # id+=4
            # elif len(f.loops)==3:
                # indices.append((id,id+1,id+2))
                # id+=3
        # bm.free()

        # Gather different maps
        for j in range(uvcount):
            eval('uvs.append(uvs_' + str(j) + ')')
        for j in range(colcount):
            eval('cols.append(col_' + str(j) + ')')

        return len(verts), verts, len(uvs), uvs, len(indices) * 3, indices, cols, norms


def read_crowd_14(file):  # NOT USED
    print('READING CROWD FILE')
    header = file.data.read(4).decode('utf-8')
    if not header == 'CRWD':
        print('NOT A VALID CROWD FILE')
        return
    file.data.read(2)
    count = struct.unpack('<H', file.data.read(2))[0]
    print(count)

    for i in range(count):
        file.data.read(2)
        # COORDINATES
        verts = struct.unpack('<3f', file.data.read(12))

        # ZROTATION
        zrot = struct.unpack('<f', file.data.read(4))[0]

        # Color
        rawr = struct.unpack('<B', file.data.read(1))[0]
        rawg = struct.unpack('<B', file.data.read(1))[0]
        rawb = struct.unpack('<B', file.data.read(1))[0]

        r = hex(rawr)[2:]
        g = hex(rawg)[2:]
        b = hex(rawb)[2:]
        color = '#' + str(r) + str(g) + str(b)

        r = float(rawr / 255)
        g = float(rawg / 255)
        b = float(rawb / 255)
        colorrgb = (r, g, b)
        # print(colorrgb)
        # print(color)
        #   file.data.read(1)

        c_status = struct.unpack('<B', file.data.read(1))[0]
        c_attendance = struct.unpack('<B', file.data.read(1))[0]
        # ha=struct.unpack('<3B',file.data.read(3)) #skipping
        # set1=struct.unpack('I',file.data.read(4))
        # set2=struct.unpack('I',file.data.read(4))
        # set3=struct.unpack('I',file.data.read(4))
        # set4=struct.unpack('I',file.data.read(4))

        file.crowd.append(
            (verts, zrot, c_status, c_attendance, colorrgb, color, set1, set2, set3, set4))


def read_crowd_15(file):
    scn = bpy.context.scene
    print('READING CROWD FILE')
    header = file.data.read(4).decode('utf-8')
    if not header == 'CRWD':
        print('NOT A VALID CROWD FILE')
        return
    file.data.read(2)
    count = struct.unpack('<H', file.data.read(2))[0]
    print('Seat Count: ', count)
    t = open('crowd_log.txt', 'w')

    if scn.game_enum == "2":
        skip = 7
    else:
        skip = 19

    for i in range(count):
        file.data.read(2)
        # COORDINATES
        verts = struct.unpack('<3f', file.data.read(12))
        # verts=(verts[0],-verts[2],verts[1])

        # ZROTATION
        zrot = struct.unpack('<f', file.data.read(4))[0]

        # Color
        rawr = struct.unpack('<B', file.data.read(1))[0]
        rawg = struct.unpack('<B', file.data.read(1))[0]
        rawb = struct.unpack('<B', file.data.read(1))[0]

        r = hex(rawr)[2:]
        g = hex(rawg)[2:]
        b = hex(rawb)[2:]
        color = '#' + str(r) + str(g) + str(b)

        r = float(rawr / 255)
        g = float(rawg / 255)
        b = float(rawb / 255)
        colorrgb = (r, g, b)
        # print(colorrgb)
        # print(color)

        # Saving Testing Values
        c_status = struct.unpack('<4B', file.data.read(4))
        # c_attendance=struct.unpack('<B',file.data.read(1))[0]
        t.write(str(c_status) + '       ' + str(file.data.read(skip)) + '\n')
        file.crowd.append((verts, zrot, c_status, colorrgb, color))
    t.close()


def texture_convert(textures_list):
    status = ''
    for tex in textures_list:
        if tex[2]:
            comp = '-dxt5'
        else:
            comp = '-dxt1a'

        if tex[8] >= 2048:
            nmips = 10
        elif tex[8] >= 512:
            nmips = 3
        else:
            nmips = 1

        path, filename = os.path.split(tex[1])
        # print(filename)
        filename, ext = os.path.splitext(filename)

        if ext == '.dds':
            #print('Texture in DDS format')
            pass
        elif os.path.isfile(os.path.join('fifa_tools', filename + '.dds')):
            tex[1] = os.path.join('fifa_tools', filename + '.dds')
            #print('Texture Exists')
            # copyfile(tex[1],os.path.join(prePath,tex[1]))
        else:
            status = call(['./fifa_tools/nvidia_tools/nvdxt.exe', '-file', tex[1], comp, '-nmips', str(
                nmips), '-outdir', './fifa_tools', '-quality_production', '-output', filename + '.dds'])
            tex[1] = os.path.join('fifa_tools', filename + '.dds')

        if status == 4294967294:
            return 'texture_path_error,' + tex[1]

    return str(status)


def convert_mesh_collisions(object):
    data = object.data
    verts = []

    bm = bmesh.new()
    bm.from_mesh(data)

    triscount = 0

    # Matrices for position convertions
    rot_x_mat = Matrix.Rotation(radians(-90), 4, 'X')
    scale_mat = Matrix.Scale(100, 4)
    for f in bm.faces:
        if len(f.verts) == 4:
            v0 = scale_mat * rot_x_mat * object.matrix_world * f.verts[0].co
            v1 = scale_mat * rot_x_mat * object.matrix_world * f.verts[1].co
            v2 = scale_mat * rot_x_mat * object.matrix_world * f.verts[2].co
            v3 = scale_mat * rot_x_mat * object.matrix_world * f.verts[3].co

            v0 = (v0[0], v0[1], v0[2])
            v1 = (v1[0], v1[1], v1[2])
            v2 = (v2[0], v2[1], v2[2])
            v3 = (v3[0], v3[1], v3[2])

            verts.append(v0)
            verts.append(v1)
            verts.append(v2)
            verts.append(v3)
            verts.append(v0)
            verts.append(v2)
            triscount += 2
        else:
            v0 = scale_mat * rot_x_mat * object.matrix_world * f.verts[0].co
            v1 = scale_mat * rot_x_mat * object.matrix_world * f.verts[1].co
            v2 = scale_mat * rot_x_mat * object.matrix_world * f.verts[2].co

            v0 = (v0[0], v0[1], v0[2])
            v1 = (v1[0], v1[1], v1[2])
            v2 = (v2[0], v2[1], v2[2])

            verts.append(v0)
            verts.append(v1)
            verts.append(v2)
            triscount += 1

    return triscount, verts, object.name.split(sep='_')[-1] + 'Shape'


def write_crowd_file(f, object):
    data = object.data
    bm = bmesh.new()
    bm.from_mesh(data)
    bm.normal_update()

    rot_x_mat = Matrix.Rotation(radians(-90), 4, 'X')
    scale_mat = Matrix.Scale(100, 4)

    f.write(struct.pack('<IHI', 1146573379, 261, len(bm.faces)))  # header

    for face in bm.faces:
        loc = face.calc_center_median()
        loc = scale_mat * rot_x_mat * object.matrix_world * loc  # location
        f.write(struct.pack('<3f', loc[0], loc[1], loc[2]))

        f_normal = object.matrix_world * face.normal

        # angle=acos(Vector((f_normal[0],f_normal[1],0)).dot(Vector((1,0,0))))
        # angle=round(angle,1)

        # print(face.index)

        angle = round(
            degrees(Vector((f_normal[0], f_normal[1])).angle_signed(Vector((1, 0)))), 0)

        if angle == 0:
            if round(degrees(Vector((f_normal[0], f_normal[1], 0)).angle(Vector((0, 1, 0)))), 0) == 180:
                angle = -180
            if round(degrees(Vector((f_normal[0], f_normal[1], 0)).angle(Vector((0, 1, 0)))), 0) == 0:
                angle = 180
        elif angle == 90:
            if round(degrees(Vector((f_normal[0], f_normal[1], 0)).angle(Vector((0, 1, 0)))), 0) == 180:
                angle = -90
            if round(degrees(Vector((f_normal[0], f_normal[1], 0)).angle(Vector((0, 1, 0)))), 0) == 0:
                angle = 90
        else:
            angle = angle

        # print(angle)
        f.write(struct.pack('<f', angle))  # angle
        # color
        try:
            collayer = bm.loops.layers.color[0]
            color = (face.loops[0][collayer][
                     0] * 255, face.loops[0][collayer][1] * 255, face.loops[0][collayer][2] * 255)
            f.write(
                struct.pack('<3B', int(color[0]), int(color[1]), int(color[2])))
        except:
            print('Color exception')
            f.write(struct.pack('<3B', 255, 255, 255))

        # home/away attendance
        testvert = face.verts[0].index

        # print(testvert)
        try:
            g = object.data.vertices[testvert].groups[0]
            # print(g.group)
        except:
            f.close()
            print('Unassigned Crowd Vertices')
            return



        gnameParts = object.vertex_groups[g.group].name.split(sep='_')

        try:
            gType = gnameParts[0]
            gFullness = gnameParts[1]
            gTier = int(gnameParts[2])
        except:
            gType = 'deadAway'
            gFullness = 'empty'
            gTier = 1

        #print(list(crowdGroup.typeDict[gType])  +  [gTier, crowdGroup.fullNessDict[gFullness]])
        f.write(struct.pack(
            '<4B', *(list(crowdGroup.typeDict[gType]) + [gTier, crowdGroup.fullNessDict[gFullness]])))

        # f.write(struct.pack('<4f',1,1,0,1)) #Some Values Fifa 14
        f.write(struct.pack('<9B', 0, 0, 0, 0, 0, 0, 0, 0, 0))  # Some Values

        # f.write(struct.pack('<H',0)) #Padding for Fifa 14


def object_separate(ob):

    # Separate vertices

    verts = {}
    for g in ob.vertex_groups:
        verts[g.index] = []

    print(verts)

    for vert in ob.data.vertices:
        try:
            verts[vert.groups[0].group].append(vert.index)
        except:
            print('malakia')

    bm = bmesh.from_edit_mesh(ob.data)
    bpy.context.tool_settings.mesh_select_mode = (True,  False, True)

    for f in bm.faces:
        f.select = False

    for i in range(len(verts) - 1):
        for f in bm.faces:
            for v in f.verts:
                if v.index in verts[i]:
                    v.select = True
                    f.select = True

    bmesh.update_edit_mesh(ob.data, False)

    # bm.to_mesh(ob.data)

    # bpy.ops.mesh.separate(type='SELECTED')

    bm.free()

    print('separating')


def write_xml_param(name, index, prop):
    class_name = prop.__class__.__name__

    if class_name == 'Vector' or class_name == 'bpy_prop_array' or class_name == 'tuple':
        value_repr = '{ '
        for i in range(len(prop)):
            value_repr += str(round(prop[i], 3))
            if i < len(prop) - 1:
                value_repr += ', '

        value_repr += ' }'
    else:
        value_repr = str(prop)
        if value_repr == 'True':
            value_repr = '1'
        elif value_repr == 'False':
            value_repr = '0'

    return '<parameter index=' + chr(34) + str(index) + chr(34) + ' name=' + chr(34) + name + chr(34) + ' value=' + chr(34) + value_repr + chr(34) + ' />\n'
