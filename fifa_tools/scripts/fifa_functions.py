import struct,os,bpy,imp,bmesh,itertools,zlib,operator
from mathutils import Vector,Euler,Matrix
from math import radians,sqrt,degrees,acos,atan2
from random import randint
from subprocess import call
halfpath='fifa_tools\\scripts\\half.py'
#half=imp.load_source('half',halfpath)
half=imp.load_compiled('half','fifa_tools\\scripts\\half.pyc')
dir='fifa_tools'
comp=half.Float16Compressor()


dict={(12,0):(2,0,0,1,0),  #(CHUNK_LENGTH, VFLAG):   (PREGAP,INNERGAP,POSTGAP,UVCOUNT,VFLAG)
		  (12,1):(2,0,0,1,0),
		  (16,1):(0,0,0,1,1),
		  (20,0):(6,0,0,2,0),
		  (20,1):(0,0,0,2,1),
		  (24,0):(6,0,4,2,0),
		  (24,1):(4,0,0,2,1),
		  (28,0):(6,0,8,2,0),
		  (32,0):(14,0,4,2,0),
		  (32,1):(8,0,4,2,1),
		  (32,2):(14,0,8,1,0),
		  (36,1):(8,0,8,2,1),
		  (40,0):(10,4,12,2,0),
		  (40,1):(2,24,0,2,0),
		  (40,2):(10,4,16,1,0)
		  }


		  
		  
#READ DDS HEADER FILE
def read_dds_header(offset):
	data=[]
	headers=open('fifa_tools\\dds_headers','rb')
	headers.seek(offset+16)
	
	for i in range(128):
		data.append(struct.unpack('<B',headers.read(1))[0])
	
	headers.close() 
	return data

def read_dds_info(f):
	f.seek(12)
	width=struct.unpack('<I',f.read(4))[0]
	height=struct.unpack('<I',f.read(4))[0]
	f.seek(8,1)
	mipmaps=struct.unpack('<H',f.read(2))[0]
	f.seek(54,1)
	type=''
	type=type.join([chr(i) for i in f.read(4)])
	
	return height,width,mipmaps,type


def read_test(f,opts,count):
	#counters
	uvcount=0
	colcount=0
	#lists init
	verts=[]
	uvs=[]
	cols=[]
	cols_0=[]
	cols_1=[]
	cols_2=[]
	uvs_0,uvs_1,uvs_2,uvs_3,uvs_4,uvs_5,uvs_6,uvs_7=[],[],[],[],[],[],[],[]
	bones_i0=[]
	bones_i1=[]
	bones_w=[]
	bones_c=[]
	
	#print(opts)
	for i in range(count):
		uvcount=0
		colcount=0
		for j in opts:
			if j[0][0]=='p':
				if j[4]=='3f32':
					verts.append(read_vertices_1(f))   #READ VERTICES
				elif j[4]=='4f16':
					verts.append(read_vertices_0(f))
			elif j[0][0]=='t':
				if j[4]=='2f32':
					eval('uvs_'+str(j[0][1])+'.append(read_uvs_1(f))')
				elif j[4]=='2f16':
					eval('uvs_'+str(j[0][1])+'.append(read_uvs_0(f))')
				uvcount+=1
			elif j[0][0]=='n':
				colcount+=1
				cols_0.append(read_cols(f))
			elif j[0][0]=='b':
				colcount+=1
				cols_2.append(read_cols(f))
			elif j[0][0]=='g':
				colcount+=1
				cols_1.append(read_cols(f))
			elif j[0][0]=='i':
				if j[4]=='4u8':
					eval('bones_i'+str(j[0][1])+'.append(struct.unpack(\'<4B\',f.read(4)))')
				elif j[4]=='4u16':
					eval('bones_i'+str(j[0][1])+'.append(struct.unpack(\'<4H\',f.read(8)))')
			elif j[0][0]=='w':	
				bones_w.append(struct.unpack('<4B',f.read(4)))
			elif j[0][0]=='c':	
				bones_c.append(struct.unpack('<4B',f.read(4)))
				
		
	#STORE COLORS UVS AND BONES
	for j in range(uvcount):
		eval('uvs.append(uvs_'+str(j)+')')
	for j in range(colcount):
		eval('cols.append(cols_'+str(j)+')')
		
		
	#print(verts)
	return verts,cols,uvs,bones_i0,bones_w   
		
		
	

##READ VERTEX FUNCTIONS 

def read_vertices_1(f):
	vert_tup=struct.unpack('<3f',f.read(12))
	return((vert_tup[0]/100,-vert_tup[2]/100,vert_tup[1]/100)) 

def read_vertices_0(f):
	vx=comp.decompress(struct.unpack('<H',f.read(2))[0])
	vy=comp.decompress(struct.unpack('<H',f.read(2))[0])
	vz=comp.decompress(struct.unpack('<H',f.read(2))[0])
	f.read(2)
	
	hx=struct.unpack('f',struct.pack('I',vx))[0]
	hy=struct.unpack('f',struct.pack('I',vy))[0]
	hz=struct.unpack('f',struct.pack('I',vz))[0]
	return((hx/100,-hz/100,hy/100))  

def read_uvs_1(f):
	return(struct.unpack('<2f',f.read(8)))


def read_uvs_0(f):
	uvx=comp.decompress(struct.unpack('<H',f.read(2))[0])
	uvy=comp.decompress(struct.unpack('<H',f.read(2))[0])
	huvx=struct.unpack('f',struct.pack('I',uvx))[0]
	huvy=struct.unpack('f',struct.pack('I',uvy))[0]
	return((huvx,huvy))

def read_cols(f):
	val=struct.unpack('<I',f.read(4))[0]
	val_0=(val &0x3ff)/1023
	val_1=((val>>10) &0x3ff)/1023
	val_2=((val>>20) &0x3ff)/1023
	return((val_2,val_1,val_0))

	
def mesh_descr_convert(descr):
	opts=[]
	for i in descr:
		opts.append(i[0]+':'+i[4])
	return opts
	

	##READ AND STORE FACE DATA#
def facereadlist(f,offset,endian):
	faces=[]	
	f.seek(offset)
	f.read(4)
	indicescount=struct.unpack(endian+'I',f.read(4))[0]
	#CHANGED TO 2BYTE IN ORDER TO MATCH THE 2 ENDIAN TYPES
	indiceslength=struct.unpack(endian+'B',f.read(1))[0]
	f.read(3)
	facecount=int(indicescount/3)
	f.read(4)
	if indiceslength==4:
		string=endian+'III'
	elif indiceslength==2:
		string=endian+'HHH'
	
	for i in range(facecount):
		temp=struct.unpack(string,f.read(indiceslength*3))
		if temp[0]==temp[1] or temp[2]==temp[1] or temp[0]==temp[2]:
			continue
		faces.append((temp[0],temp[1],temp[2]))
		
	#print(faces)   
	return faces,indiceslength

def facereadstrip(f,offset,endian):
	faces=[]	
	f.seek(offset)
	f.read(4)
	indicescount=struct.unpack('<I',f.read(4))[0]
	indiceslength=struct.unpack('<i',f.read(4))[0]
	facecount=indicescount-2
	print(indicescount,facecount)
	f.read(4)
	if indiceslength==4:
		string='<III'
	elif indiceslength==2:
		string='<HHH'
	
	flag=False
	for i in range(facecount):
		back=f.tell()
		temp=struct.unpack(string,f.read(indiceslength*3))  
		if temp[0]==temp[1] or temp[1]==temp[2] or temp[0]==temp[2]:
			flag= not flag  
			f.seek(back+indiceslength)  
			continue
		else:
			if flag==False:
				faces.append((temp[0],temp[1],temp[2]))
			elif flag==True:
				faces.append((temp[2],temp[1],temp[0]))
			
			flag= not flag  
			f.seek(back+indiceslength)
				
	#print(faces)   
	return faces,indiceslength

def convert_mesh_init(object,mode):
	
	scn=bpy.context.scene
	verts=[]
	uvs=[]
	cols=[]
	indices=[]
	collist=[]
	data=object.data
	print('Processing: ',object.name)
	bm=bmesh.new()
	bm.from_mesh(data)
	bm.normal_update()
	
	##STORE TRANSFORMATION
	if mode==0:
		mesh_descr=''
		mesh_descr_short=[]
		
		
		boundbox=object_bbox(object)
		
		#Constructing mesh description
		off=0
		last=0
		chunk_length=0
		mesh_descr='p0:'+'{:02X}'.format(off)+':00:0001:3f32'+' '
		mesh_descr_short.append('p0:3f32')	
		uvlen=len(bm.loops.layers.uv)
		for i in range(len(bm.loops.layers.color)):
			collist.append(bm.loops.layers.color[i].name)
		off+=12
		
		
		if 'col0' in collist:
			mesh_descr+='n0:'+'{:02X}'.format(off)+':00:0001:3s10n'+' '
			mesh_descr_short.append('n0:3s10n')
			off+=4
			
			
		if 'col1' in collist:
			mesh_descr+='g0:'+'{:02X}'.format(off)+':00:0001:3s10n'+' '
			mesh_descr_short.append('g0:3s10n')
			off+=4  
			
		for i in range(uvlen):
			mesh_descr+='t'+str(i)+':'+'{:02X}'.format(off)+':00:0001:2f16'+' '
			mesh_descr_short.append('t'+str(i)+':2f16')
			off+=4
			#last=4
		
		if object.name.split(sep='_')[0] in ['head','hair']:
			mesh_descr+='i0:'+'{:02X}'.format(off)+':00:0001:4u8'+' '
			mesh_descr_short.append('i0:4u8')
			off+=4
			mesh_descr+='w0:'+'{:02X}'.format(off)+':00:0001:4u8'+' '
			mesh_descr_short.append('w0:4u8')
			off+=4
		
		mesh_descr=mesh_descr[0:-1]
		print(mesh_descr_short)
		bm.free()
		
		return collist,boundbox,mesh_descr,mesh_descr_short,off-last  
	
	elif mode==1:
		uvs_0=[]
		uvs_1=[]
		uvs_2=[]
		col_0=[]
		col_1=[]
		col_2=[]
		id=0
		
		#Matrices
		object_matrix_wrld=object.matrix_world
		rot_x_mat=Matrix.Rotation(radians(-90),4,'X')
		if scn.trophy_export_flag:
			scale_mat=Matrix.Scale(100,4)
		else:
			scale_mat=Matrix.Scale(100,4)
		
		#Forced to Use Old Way for N-gons
		
		
		data.update(calc_tessface=True) #convert ngons to tris
		uvcount=len(data.uv_layers)
		colcount=len(data.vertex_colors)
		
		for f in data.tessfaces: 	#indices
			if len(f.vertices)==4:
				indices.append((id,id+1,id+2))
				indices.append((id+3,id,id+2))
				id+=4
			else:
				indices.append((id,id+1,id+2))
				id+=3
			
			
			
			for vert in range(len(f.vertices)):
				co=scale_mat*rot_x_mat*object_matrix_wrld*data.vertices[f.vertices[vert]].co
				verts.append((co[0],co[1],co[2]))
				
				for k in range(uvcount):
					u=eval('data.tessface_uv_textures['+str(k)+'].data['+str(f.index)+'].uv'+str(vert+1)+'[0]')
					v=1-eval('data.tessface_uv_textures['+str(k)+'].data['+str(f.index)+'].uv'+str(vert+1)+'[1]')
					eval('uvs_'+str(k)+'.append((round(u,8),round(v,8)))')
				for k in range(colcount):
					r=eval('data.tessface_vertex_colors['+str(k)+'].data['+str(f.index)+'].color'+str(vert+1)+'[0]*1023')
					g=eval('data.tessface_vertex_colors['+str(k)+'].data['+str(f.index)+'].color'+str(vert+1)+'[1]*1023')
					b=eval('data.tessface_vertex_colors['+str(k)+'].data['+str(f.index)+'].color'+str(vert+1)+'[2]*1023')
					eval('col_'+str(k)+'.append((r,g,b))')
				
		# #New way
		# id=0
		# uvcount=len(bm.loops.layers.uv)
		# colcount=len(bm.loops.layers.color)
		# for f in bm.faces:
			# for l in f.loops:
				# co=scale_mat*rot_x_mat*object_matrix_wrld*l.vert.co
				# verts.append((co[0],co[1],co[2]))
				# #uvs
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
				
				
				
				# #Define a face for each loop
			# if len(f.loops)==4:
				# indices.append((id,id+1,id+2))
				# indices.append((id+3,id,id+2))
				# id+=4
			# elif len(f.loops)==3:
				# indices.append((id,id+1,id+2))
				# id+=3
		# bm.free()
		
		#Gather different maps
		for j in range(uvcount):
			eval('uvs.append(uvs_'+str(j)+')')
		for j in range(colcount):
			eval('cols.append(col_'+str(j)+')')
		
		return len(verts),verts,len(uvs),uvs,len(indices)*3,indices,cols

		
def convert_original_mesh_to_data(object):
	verts=[];uvs=[];indices=[];cols=[]
	data=object.data
	bm=bmesh.new()
	bm.from_mesh(data)
	uvs_0=[];uvs_1=[];uvs_2=[]
	col_0=[];col_1=[];col_2=[]
	
	uvcount=len(bm.loops.layers.uv)
	colcount=len(bm.loops.layers.color)
	
	rot_x_mat=Matrix.Rotation(radians(90),4,'X')
	scale_mat=Matrix.Scale(100,4)
	
	for vert in bm.verts:
		co=scale_mat*rot_x_mat*object.matrix_world*vert.co
		verts.append((co[0],-co[1],-co[2]))
	 
	for i in range(len(bm.verts)):
		for j in range(uvcount):
			uvlayer=bm.loops.layers.uv[j]
			eval('uvs_'+str(j)+'.append((round(bm.verts[i].link_loops[0][uvlayer].uv.x,8),round(1-bm.verts[i].link_loops[0][uvlayer].uv.y,8)))')
	
	
	
	for i in range(len(bm.verts)):
		for j in range(colcount):
			collayer=bm.loops.layers.color[j]
			vert_data=bm.verts[i].link_loops[0][collayer]
			eval('col_'+str(j)+'.append((vert_data[0]*1023,vert_data[1]*1023,vert_data[2]*1023))')
	
	
	
	for f in bm.faces:
		indices.append((f.verts[0].index,f.verts[1].index,f.verts[2].index))
		
	for j in range(uvcount):
		eval('uvs.append(uvs_'+str(j)+')')
	for j in range(colcount):
		eval('cols.append(col_'+str(j)+')')
	
	bm.free()
	return verts,uvs,cols,indices		
		
def convert_mesh_collisions(object):
	data=object.data
	verts=[]
	
	bm=bmesh.new()
	bm.from_mesh(data)
	
	triscount=0
	
	#Matrices for position convertions
	rot_x_mat=Matrix.Rotation(radians(-90),4,'X')
	scale_mat=Matrix.Scale(1000,4)
	for f in bm.faces:
		if len(f.verts)==4:
			v0=scale_mat*rot_x_mat*object.matrix_world*f.verts[0].co
			v1=scale_mat*rot_x_mat*object.matrix_world*f.verts[1].co
			v2=scale_mat*rot_x_mat*object.matrix_world*f.verts[2].co
			v3=scale_mat*rot_x_mat*object.matrix_world*f.verts[3].co
			
			v0=(v0[0],v0[1],v0[2])
			v1=(v1[0],v1[1],v1[2])
			v2=(v2[0],v2[1],v2[2])
			v3=(v3[0],v3[1],v3[2])
			
			verts.append(v0);verts.append(v1);verts.append(v2)
			verts.append(v3);verts.append(v0);verts.append(v2)
			triscount+=2
		else:
			v0=scale_mat*rot_x_mat*object.matrix_world*f.verts[0].co
			v1=scale_mat*rot_x_mat*object.matrix_world*f.verts[1].co
			v2=scale_mat*rot_x_mat*object.matrix_world*f.verts[2].co
			
			v0=(v0[0],v0[1],v0[2])
			v1=(v1[0],v1[1],v1[2])
			v2=(v2[0],v2[1],v2[2])
			
			verts.append(v0);verts.append(v1);verts.append(v2)
			triscount+=1
	
	return triscount,verts,object.name.split(sep='_')[-1]+'Shape'
		
		
	

def convert_mesh_to_bytes(f,opts,count,verts,uvs,cols):
	for i in range(count):
		for o in opts:
			if o[0]=='p': #verts
				if o[3:]=='4f16':
					write_half_verts(f,verts[i])
				else:
					f.write(struct.pack('<3f',round(verts[i][0],8),round(verts[i][1],8),round(verts[i][2],8)))
			elif o[0]=='n': #col0
				col=(int(cols[0][i][0])<<20) + (int(cols[0][i][1])<<10) + (int(cols[0][i][2]))
				f.write(struct.pack('<I',col))
			elif o[0]=='g': #col1
				col=(int(cols[1][i][0])<<20) + (int(cols[1][i][1])<<10) + (int(cols[1][i][2]))
				f.write(struct.pack('<I',col))
			elif o[0]=='b': #col2
				col=(int(cols[2][i][0])<<20) + (int(cols[2][i][1])<<10) + (int(cols[2][i][2]))
				f.write(struct.pack('<I',col))	
			elif o[0]=='t': #uvs
				huvx=eval('comp.compress(round(uvs[int(o[1])][i][0],8))')
				huvy=eval('comp.compress(round(uvs[int(o[1])][i][1],8))')
				f.write(struct.pack('<HH',huvx,huvy))
			elif o[0]=='i': #bone indices
				if o[3:]=='4u8':
					f.read(4)
				elif o[3:]=='4u16':
					f.read(8)
			elif o[0]=='w': #bone weights
				f.read(4)	
				

def write_half_verts(f,co):
	hvx=comp.compress(round(co[0],8))
	hvy=comp.compress(round(co[1],8))
	hvz=comp.compress(round(co[2],8))
	f.write(struct.pack('<HHHH',hvx,hvy,hvz,0))
				


def write_head_data(f,verts,uvs,chunk_length):
	
	for i in range(len(verts)):
		#VERT SECTION
		f.write(struct.pack('<fff',round(verts[i][0],8),round(verts[i][1],8),round(verts[i][2],8)))
		f.read(8)
		#UV SECTION
		huvx=comp.compress(round(uvs[i][0],8))
		huvy=comp.compress(round(1-uvs[i][1],8))
		f.write(struct.pack('<HH',huvx,huvy))
		f.read(8)
		
def write_indices(f,indices):
	#print('Indices Length: ',indices[0])
	if 3*len(indices)>65535:
		ind_size=4
		format='<III'   
	else:
		ind_size=2
		format='<HHH'

	for entry in indices:
		f.write(struct.pack(format,entry[0],entry[1],entry[2]))


		
def write_hair_data(f,verts,uvs,chunk_length):
	for i in range(len(verts)):
		#VERT SECTION
		hvx=comp.compress(round(verts[i][0],8))
		hvy=comp.compress(round(verts[i][1],8))
		hvz=comp.compress(round(verts[i][2],8))
		f.write(struct.pack('<HHH',hvx,hvy,hvz))
		f.read(14)
		#UV SECTION
		huvx=comp.compress(round(uvs[i][0],8))
		huvy=comp.compress(round(1-uvs[i][1],8))
		f.write(struct.pack('<HH',huvx,huvy))
		f.read(8)
			   
def write_crowd_file(f,object):
	data=object.data
	bm=bmesh.new()
	bm.from_mesh(data)
	bm.normal_update()
	
	rot_x_mat=Matrix.Rotation(radians(-90),4,'X')
	scale_mat=Matrix.Scale(1000,4)
	
	f.write(struct.pack('<IHI',1146573379,259,len(bm.faces))) #header
	
	for face in bm.faces:
		loc=face.calc_center_median()
		loc=scale_mat*rot_x_mat*object.matrix_world*loc #location
		f.write(struct.pack('<3f',loc[0],loc[1],loc[2]))
		
		f_normal=object.matrix_world*face.normal
		
		#angle=acos(Vector((f_normal[0],f_normal[1],0)).dot(Vector((1,0,0))))
		#angle=round(angle,1)
		
		#print(face.index)
		
		angle=round(degrees(Vector((f_normal[0],f_normal[1])).angle_signed(Vector((1,0)))),0)
		
		
		
		if angle==0:
			if round(degrees(Vector((f_normal[0],f_normal[1],0)).angle(Vector((0,1,0)))),0)==180:
				angle=-180
			if round(degrees(Vector((f_normal[0],f_normal[1],0)).angle(Vector((0,1,0)))),0)==0:
				angle=180
		elif angle==90:
			if round(degrees(Vector((f_normal[0],f_normal[1],0)).angle(Vector((0,1,0)))),0)==180:
				angle=-90
			if round(degrees(Vector((f_normal[0],f_normal[1],0)).angle(Vector((0,1,0)))),0)==0:
				angle=90
		else:
			angle=angle
		
		
		#print(angle)
		f.write(struct.pack('<f',angle))#angle
		#color
		try:
			collayer=bm.loops.layers.color[0]
			color=(face.loops[0][collayer][0]*255,face.loops[0][collayer][1]*255,face.loops[0][collayer][2]*255)
			f.write(struct.pack('<3B',int(color[0]),int(color[1]),int(color[2])))
		except:
			print('exception')
			f.write(struct.pack('<3B',255,255,255))
		
		#home/away attendance
		testvert=face.verts[0].index
		
		
		
		#print(testvert)
		
		try:
			g=object.data.vertices[testvert].groups[0]
			print(g.group)
			if object.vertex_groups[g.group].name=='Core Home':
				f.write(struct.pack('<5B',0,0,randint(10,255),127,51))
			elif object.vertex_groups[g.group].name=='Casual Home':	
				f.write(struct.pack('<5B',randint(10,130),randint(1,2),randint(60,255),127,51))
			elif object.vertex_groups[g.group].name=='Away':
				f.write(struct.pack('<5B',randint(180,255),2,randint(40,125),127,51))
			elif object.vertex_groups[g.group].name=='Neutral':
				f.write(struct.pack('<5B',randint(130,180),2,randint(40,125),127,51))
			else:
				f.write(struct.pack('<5B',0,0,0,127,51)) #Empty	
			
		except:
			print('empty trigger')
			f.write(struct.pack('<5B',0,0,0,127,51)) #Empty
		
		
		f.write(struct.pack('<4f',1,1,0,1)) #Some Values
		
		f.write(struct.pack('<H',0)) #Padding
		

#Blender Transformation Matrix converting functions

def vec_roll_to_mat3(vec, roll):
    target = Vector((0,1,0))
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

def mat3_to_vec_roll(mat):
    vec = mat.col[1]
    vecmat = vec_roll_to_mat3(mat.col[1], 0)
    vecmatinv = vecmat.inverted()
    rollmat = vecmatinv * mat
    roll = atan2(rollmat[0][2], rollmat[2][2])
    return vec, roll



def read_bones(f,count):
	temp=[]
	
	for k in range(count):
		mat=Matrix()
		mat=mat.to_4x4()
		for i in range(4):
			for j in range(4):
				mat[j][i]=round(struct.unpack('<f',f.read(4))[0],8)
		
		
		#pos = mat.to_translation()
		pos=Vector((mat[0][3],mat[1][3],mat[2][3]))
		
		if k in [2,3,4,324,333]:
			print('Matrix ID= ',k)
			#print(mat.to_euler())
			#print(mat.to_scale())
			print(pos)
		
		
		rot = mat.to_euler()
		
		if not rot[0]==0:
			sx=round(rot[0]/abs(rot[0]),1)
		else:
			sx=1.0
		
		if not rot[1]==0:
			sy=round(rot[1]/abs(rot[1]),1)
		else:
			sy=1.0
		
		if not rot[2]==0:
			sz=round(rot[2]/abs(rot[2]),1)
		else:
			sz=1.0
		
		
		#Vector.rotate(pos,rot)
		axis, roll = mat3_to_vec_roll(mat.to_3x3())
		#pos = rot*pos
		if k in [2,3,4,324,333]:
			#print('Matrix ID= ',k)
			#print(mat.to_euler())
			#print(mat.to_scale())
			print(sz)
			print(pos)
		temp.append((pos,pos+axis,roll)) #bone.head=pos, #bone.tail=pos+axis, #bone.roll=roll
	return temp

def read_string(f):
	c=''
	for i in range(128):
		s=struct.unpack('<B',f.read(1))[0]
		if s==0:
			return c
		c=c+chr(s)

	return {'FINISHED'}

def create_boundingbox(vec1,vec2,name):
	comb=list(itertools.product(vec1,vec2))
	v1,v2,v3=comb[0],comb[3],comb[6]
	verts=list(itertools.product(v1,v2,v3))
	faces=[(4, 6, 7), (7, 5, 4), (2, 6, 4), (4, 0, 2), (3, 2, 0), (0, 1, 3), (5, 3, 1), (3, 5, 7), (5, 1, 0), (0, 4, 5), (7, 2, 3), (2, 7, 6)]
	
	bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0,0,0))
	bpy.data.objects['Empty'].scale=Vector((1,1,1))
	bpy.data.objects['Empty'].location=(0,0,0)
	#bpy.data.objects['Empty'].rotation_euler=Euler((1.570796251296997, -0.0, 0.0), 'XYZ')
	bpy.data.objects['Empty'].rotation_euler=Euler((0, -0.0, 0.0), 'XYZ')
	bpy.data.objects['Empty'].name=name
	
	
def create_prop(name,loc,rot):
	
	bpy.ops.object.empty_add(type='SINGLE_ARROW', location=loc, rotation=(rot[0]-radians(90), rot[2], rot[1]+radians(180)))
	
	ob=bpy.data.objects['Empty']
	
	try:
		i=0
		while bpy.data.objects[name+'_'+str(i)]:
			i+=1
	except:
		ob.name=name+'_'+str(i)
		#ob.data.align='CENTER'
	
	
	#ob.data.body=name+'_'+str(i)
	ob.scale=Vector((0.1,0.1,0.1))
	return ob.name

def rgb_to_hex(rgb):
	return '#%02x%02x%02x' % rgb

def hex_to_rgb(hex):
	hex=hex.lstrip('#')
	hlen=len(hex)
	return tuple(int(hex[i:i+int(hlen/3)], 16)/255 for i in range(0, hlen, int(hlen/3)))


def crowd_col(ob,col):
	me=bpy.data.objects[ob].data
	coltex=me.vertex_colors.new(name='seat_colors')
	
	bm=bmesh.new()
	bm.from_mesh(me)
	
	collayer=bm.loops.layers.color['seat_colors']
	for f in bm.faces:
		for l in f.loops:
			l[collayer].r=col[f.index][0]
			l[collayer].g=col[f.index][1]
			l[collayer].b=col[f.index][2]
			
	
	bm.to_mesh(me)
	bm.free()
	
	
def chunkzip_decomp(data):
	print('Decompressing File')
	t=open(dir+'\\_decompressed','wb')
	t.write(zlib.decompress(data,-15))
	t.close()
	return t.name

def crowd_seat_align(align_vector):
	scn=bpy.context.scene
	ob=bpy.context.object
	
	bm=bmesh.from_edit_mesh(ob.data)
	
	
	
	
	for f in bm.faces:
		if f.select==True:
			base=face_center(f)
			
			if align_vector==Vector((0,0,0)): #calculate cursor vector
				align_vector=ob.matrix_world.inverted()*(scn.cursor_location-(ob.matrix_world*base))
				align_vector=Vector((align_vector[0],align_vector[1]))
			
			angle=Vector((f.normal[0],f.normal[1])).angle_signed(align_vector) #calculate declining angle
			#print('Angle: ',round(angle),degrees(angle))
			
				
			rot_mat=Matrix.Rotation(round(-angle,2),4,'Z')
			
			for v in f.verts:
				v.co=v.co-base
				v.co=rot_mat*v.co
				v.co=v.co+base
	bm.normal_update()			
	bmesh.update_edit_mesh(ob.data, False)	
			
def crowd_seat_create(v_num,h_num,v_dist,h_dist,gap,context):
	scn=context.scene
	
	
	found_crowd=False
	#Check for crowd object
	if context.mode=='EDIT_MESH':
		ob=context.object
		bm=bmesh.from_edit_mesh(ob.data)
		found_object=ob
		print(found_object)
	else:
		bm=bmesh.new()
		for ob in scn.objects:
			if ob.name=='crowd':
				#ob=bpy.context.object
				found_object=ob
				bm.from_mesh(ob.data)
				found_crowd=True
				break
		
		
	try:
		print(found_object)
	except:
		print('Object not found')
		
	
	print(bm)
	cursor_loc=Vector((scn.cursor_location[0],scn.cursor_location[1],scn.cursor_location[2]))
	for i in range(v_num):
		for j in range(h_num):
			bm.faces.new((bm.verts.new(Vector((cursor_loc[0]+0.01,cursor_loc[1]+0.01,cursor_loc[2]-0.01))),
						bm.verts.new(Vector((cursor_loc[0]-0.01,cursor_loc[1]+0.01,cursor_loc[2]-0.01))),
						bm.verts.new(Vector((cursor_loc[0]-0.01,cursor_loc[1]-0.01,cursor_loc[2]+0.01))),
						bm.verts.new(Vector((cursor_loc[0]+0.01,cursor_loc[1]-0.01,cursor_loc[2]+0.01))))
						)
			
			cursor_loc[0]-=h_dist*0.01
		cursor_loc[0]=scn.cursor_location[0]
		cursor_loc[1]+=gap*0.01
		cursor_loc[2]-=v_dist*0.01
			
	bm.normal_update()
	
	
	
	
	if found_crowd==False and context.mode=='OBJECT':
		me=bpy.data.meshes.new('crowd')
		bm.to_mesh(me)
		ob=bpy.data.objects.new('crowd',me)
		context.scene.objects.link(ob)
	elif found_crowd==True: 
		bm.to_mesh(found_object.data)
	elif context.mode=='EDIT_MESH':
		bmesh.update_edit_mesh(found_object.data)
		
		
	
	
	bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
	
	
		
def crowd_groups(name):
	scn=bpy.context.scene
	ob=bpy.context.object
	
	bm=bmesh.from_edit_mesh(ob.data)
   
   
	#populate vertex list with selected vertices
	vxlist=[]
	for v in bm.verts:
		if v.select==True:
			vxlist.append(v.index)
	bm.free()
	bpy.ops.object.editmode_toggle()
	 
	if not name in ob.vertex_groups:
		ob.vertex_groups.new(name)
	
	for g in ob.vertex_groups:
		if g.name==name:
			ob.vertex_groups[name].add(vxlist,1,'ADD')
		else:
			ob.vertex_groups[g.name].add(vxlist,1,'SUBTRACT')		  

def write_offsets_to_file(f,offset_list):
	#Calculate file size
	size=0
	for off in offset_list:
		size+=off[2]+16
	
	#File Header
	f.write(struct.pack('<4I',1815304274,4,size+16,len(offset_list)))
	for i in offset_list:
		f.write(struct.pack('<4I',i[0],i[1],i[2],0))
		
	
def group_bbox(group):
	mins=[[],[],[]]
	maxs=[[],[],[]]
	
	for i in range(len(group.children)):
		vec1,vec2=object_bbox(group.children[i])
		mins[0].append(vec1[0])
		mins[1].append(vec1[1])
		mins[2].append(vec1[2])
		
		maxs[0].append(vec2[0])
		maxs[1].append(vec2[1])
		maxs[2].append(vec2[2])
		
		
		
	return ((min(mins[0]),min(mins[1]),min(mins[2])),(max(maxs[0]),max(maxs[1]),max(maxs[2])))
	
def object_bbox(object):
	
	#Matrices
	rot_x_mat=Matrix.Rotation(radians(-90),4,'X')
	scale_mat=Matrix.Scale(1000,4)
	
	#Getters
	getz=operator.itemgetter(2)
	gety=operator.itemgetter(1)
	getx=operator.itemgetter(0)
	
	bv_list=[]
	for j in object.bound_box:
		#Object Matrices
		bbox=Vector()
		bbox[0]=j[0]
		bbox[1]=j[1]
		bbox[2]=j[2]
		
		object_matrix_wrld=object.matrix_world
		bbox=rot_x_mat*scale_mat*object_matrix_wrld*(bbox)
		
		bv_list.append((bbox[2],bbox[1],bbox[0]))
		
	print(bv_list)
	
	#Returned Vectors
	bbox1=Vector()
	bbox2=Vector()
	
	#get min values
	bbox1[0]=min(bv_list,key=getz)[2]
	bbox1[1]=min(bv_list,key=gety)[1]
	bbox1[2]=min(bv_list,key=getx)[0]
	
	#get max values
	bbox2[0]=max(bv_list,key=getz)[2]
	bbox2[1]=max(bv_list,key=gety)[1]
	bbox2[2]=max(bv_list,key=getx)[0]
	
	
	return bbox1,bbox2


def paint_faces(object,color,layer_name):
	bm=bmesh.from_edit_mesh(object.data)
	collayer=bm.loops.layers.color[layer_name]
	for f in bm.faces:
		if f.select==True:
			for l in f.loops:
				l[collayer]=color
	bmesh.update_edit_mesh(object.data, True)
	
def auto_paint_mesh(object,layer_name):
	scn=bpy.context.scene
	bm=bmesh.new()
	bm.from_mesh(object.data)
	bm.normal_update()
	#base_0=0.498
	#base_1=0.502
	
	obj_rotation=object.rotation_euler
	print(obj_rotation)
	collayer=bm.loops.layers.color[layer_name]
	
	for f in bm.faces:
		for l in f.loops:
			vert=l.vert
			
			#rot=Euler((-1.5707963705062866, 0.0, 0.0), 'XYZ')
			norm=vert.normal
			#norm.rotate(obj_rotation)
			norm.normalize()
			
			#norm.rotate(rot)
			
			if scn.autopaint_modes=='0':
				l[collayer][0]=norm_to_col(round(-norm[1],3),0)
				l[collayer][1]=norm_to_col(round(norm[2],3),2)
				l[collayer][2]=norm_to_col(round(norm[0],3),1)
			elif scn.autopaint_modes=='1':
				l[collayer][0]=norm_to_col(round(-norm[0],3),0)
				l[collayer][1]=norm_to_col(round(-norm[2]*0.00068,3),0)
				l[collayer][2]=norm_to_col(round(-norm[1],3),1)
		
	bm.to_mesh(object.data)
	bm.free() 
	

def norm_to_col(x,axis):
    #converting normal Vector to Color Information
	#Arguments:
	#x:	normal Vector
	#axis: desired axis
	
    try:
        angle=Vector((x,0)).angle_signed(Vector((1,0)))
    except:
        angle=0    
    
    if angle<=0:
    
    
        if x==-1:
            return 0.502
        elif  -1<x<0:
            return -0.502*x
        elif 1>=x>=0:
            return 0.498*x
    else:
        if x==-1:
            return 0.502
        elif  -1<x<0:
            return 0.498*x+1
        elif 1>=x>=0:
            return -0.502*x+1   
	
	
	
def write_offset_data_to_file(f,path,offset_list,object_list,materials_list,materials_dict,textures_list,group_list,prop_list,collision_list):
	#Local Variables
	object_count=len(object_list)
	texture_count=len(textures_list)
	for i in range(len(offset_list)):
		f.seek(offset_list[i][1])
		if offset_list[i][0]==582139446:
			f.write(struct.pack('<4I',object_count,0,0,0))
			for j in range(object_count):
				if object_list[j][1]>65535:
					ind_size=4
				else:
					ind_size=2
				f.write(struct.pack('<4I',size_round(object_list[j][2]*ind_size+16),object_list[j][2],ind_size,0))
		elif offset_list[i][0]==3263271920: #mesh description
			id=offset_list[i][3]
			f.write(struct.pack('<4I',offset_list[i][2],len(object_list[id][6])+1,0,0))
			s = bytes(object_list[id][6], 'utf-8')
			f.write(s) 
		elif offset_list[i][0]==685399266: # PROP POSITIONS
			id=offset_list[i][3]
			f.write(struct.pack('<Ifff',offset_list[i][2],prop_list[id][1][0],prop_list[id][1][1],prop_list[id][1][2]))
			f.write(struct.pack('<fffI',prop_list[id][2][0],prop_list[id][2][1],prop_list[id][2][2],0))
		elif offset_list[i][0]==1285267122: #PROPS
			#header
			f.write(struct.pack('<4I',offset_list[i][2],len(prop_list)+len(textures_list)+len(object_list),0,0))
			#data
			for j in range(len(prop_list)):
				f.write(struct.pack('<2I',685399266,len(prop_list[j][0])+1))
				s = bytes(prop_list[j][0], 'utf-8')
				f.write(s)
				f.write(b'\x00')
			for j in range(len(object_list)):
				f.write(struct.pack('<2I',3566041216,len(object_list[j][0])+1))
				s = bytes(object_list[j][0], 'utf-8')
				f.write(s)
				f.write(b'\x00')
			for j in range(len(textures_list)):
				f.write(struct.pack('<I',2047566042))
				
				if type(textures_list[j])==type(''):
					s = bytes(textures_list[j], 'utf-8')
					f.write(struct.pack('<I',len(textures_list[j])+1))
				
				elif type(textures_list[j][0])==type(''):
					#print('textures')
					s = bytes(textures_list[j][0], 'utf-8')
					f.write(struct.pack('<I',len(textures_list[j][0])+1))
				
				f.write(s)
				f.write(b'\x00')
			
			
			
			
		elif offset_list[i][0]==5798132: #INDICES
			id=offset_list[i][3]
			#header
			if object_list[id][1]>65535:
				ind_size=4
			else:
				ind_size=2
			f.write(struct.pack('<4I',size_round(object_list[id][2]*ind_size+16),object_list[id][2],ind_size,0))  
			#data
			write_indices(f,object_list[id][11])
		elif offset_list[i][0]==5798561: #VERTICES
			id=offset_list[i][3]
			#header
			f.write(struct.pack('<4I',offset_list[i][2],object_list[id][1],object_list[id][8],1))
			#data
			convert_mesh_to_bytes(f,object_list[id][7],object_list[id][1],object_list[id][9],object_list[id][10],object_list[id][4])
		elif offset_list[i][0]==3566041216: #80......
			f.write(struct.pack('<4I',4,0,0,0))
		elif offset_list[i][0]==230948820: #GROUPS
			id=offset_list[i][3]
			#print(id,len(group_list))
			#header
			data=f.write(struct.pack('<4I',offset_list[i][2],1,0,0))	
			#data
			if id>=len(group_list):
				s = bytes('CollisionGeometry', 'utf-8')
				data+=f.write(s)
				data+=f.write(b'\x00')
				data+=f.write(struct.pack('B',id)) 
			else:
				s = bytes(group_list[id][0][5:], 'utf-8')
				f.write(s)	
				f.write(b'\x00')
				f.write(struct.pack('B',id)) 
		elif offset_list[i][0]==123459928:
			id=offset_list[i][3]
			#material header
			f.write(struct.pack('<4I',offset_list[i][2],len(materials_dict[materials_list[id]][3]),0,0))
			#data
			#material_name
			#print(materials_dict[materials_list[id]][1])
			s=bytes(materials_dict[materials_list[id]][1],'utf-8')
			f.write(s)
			f.write(b'\x00')
			#textures
			for j in range(len(materials_dict[materials_list[id]][2])):
				s=bytes(materials_dict[materials_list[id]][3][j],'utf-8')
				f.write(s)
				f.write(b'\x00')
				#print(textures_list.index(materials_dict[materials_list[id]][2][j]))
				f.write(struct.pack('I',textures_list.index(materials_dict[materials_list[id]][2][j])))
		elif offset_list[i][0]==2116321516: #RENDERLINES
			id=offset_list[i][3]
			#renderline header
			f.write(struct.pack('<4I',offset_list[i][2],1,4294967295,0))
			#renderline data
			f.write(struct.pack('<4f',1,0,0,0))
			f.write(struct.pack('<4f',0,1,0,0))
			f.write(struct.pack('<4f',0,0,1,0))
			f.write(struct.pack('<4f',0,0,0,1))
			f.write(struct.pack('<4f',group_list[id][1][0],group_list[id][1][1],group_list[id][1][2],1))
			f.write(struct.pack('<4f',group_list[id][2][0],group_list[id][2][1],group_list[id][2][2],1))
			f.write(struct.pack('<2I',group_list[id][3],4294967295))
			object_offset=group_list[id][4]
			for j in range(group_list[id][3]):
				f.write(struct.pack('<4f',object_list[object_offset+j][5][0][0],object_list[object_offset+j][5][0][1],object_list[object_offset+j][5][0][2],1))
				f.write(struct.pack('<4f',object_list[object_offset+j][5][1][0],object_list[object_offset+j][5][1][1],object_list[object_offset+j][5][1][2],1))
				f.write(struct.pack('<2I',object_offset+j,object_list[object_offset+j][13]))
		elif offset_list[i][0]==4034198449: #COLLISIONS
			id=offset_list[i][3]
			f.write(struct.pack('4I',offset_list[i][2],1,0,0))
			s=bytes(collision_list[id][2],'utf-8')
			f.write(s)
			f.write(b'\x00')
			f.write(struct.pack('I',1))
			f.write(struct.pack('I',collision_list[id][0]))
			for i in range(len(collision_list[id][1])):
				f.write(struct.pack('<3f',collision_list[id][1][i][0],collision_list[id][1][i][1],collision_list[id][1][i][2]))
			
		elif offset_list[i][0]==1808827868:
			f.write(struct.pack('<4I',texture_count,0,0,0))
			id=0
			for tex in textures_list:
				if tex[7]=='DXT5':
					id=2
				f.write(struct.pack('<IBBHHHHH',tex[6],1,id,1,tex[3],tex[4],1,tex[5]))
		elif offset_list[i][0]==2047566042:
			id=offset_list[i][3]
			#texture writing
			ext_len=len(textures_list[id][1].split(sep='\\')[-1].split(sep='.')[-1])
			
			t=open(path+textures_list[id][1].split(sep='\\')[-1][0:-1-ext_len]+'.dds','rb')
			
			#Get ready to write
			divider=1
			comp_id=0
			w=textures_list[id][3]
			h=textures_list[id][4]
			phys_size=w*h
			mipmaps=textures_list[id][5]
			if textures_list[id][7]=='DXT1':
				divider=2
				multiplier=2
			if textures_list[id][7]=='DXT5':
				comp_id=2
				multiplier=4
			t.seek(128)
			
			#Write texture
			#header
			f.write(struct.pack('<IBBHHHHH',textures_list[id][6],1,comp_id,1,textures_list[id][3],textures_list[id][4],1,textures_list[id][5]))
			#data
			size=phys_size
			for j in range(mipmaps):
				tw=size//(w*multiplier*divider)
				f.write(struct.pack('<4I',w*multiplier,tw,w*multiplier*tw,0))
				f.write(t.read(tw*w*multiplier))
				#print(tw)
				w=w//2
				size=size//4
			t.close()
			


##TEXTURE FUNCTIONS


def texture_convert(textures_list):
	status=''
	for tex in textures_list:
		if tex[2]:
			comp='-dxt5'
		else:
			comp='-dxt1a'
		
		if tex[8]>=2048:
			nmips=10
		elif tex[8]>=512:
			nmips=3
		else:
			nmips=1
		
		
		if tex[1].split(sep='.')[-1]=='.dds':
			copyfile(tex[1],'./fifa_tools'+tex[1].split(sep='\\')[-1].split(sep='.')[0]+'.dds')
		else:	
			status=call(['./fifa_tools/nvidia_tools/nvdxt.exe','-file',tex[1],comp,'-nmips',str(nmips),'-outdir','./fifa_tools','-quality_production','-output',tex[1].split(sep='\\')[-1].split(sep='.')[0]+'.dds'])
		
		if status==4294967294:
			return 'texture_path_error,'+tex[1]
	
	
	return str(status)
			

def read_converted_textures(offset_list,textures_list,path):
	offset_list.append((1808827868,len(textures_list)*16+48,len(textures_list)*16+16))
	
	for k in range(len(textures_list)):
		ext_len=len(textures_list[k][1].split(sep='\\')[-1].split(sep='.')[-1])
		
		t=open(path+textures_list[k][1].split(sep='\\')[-1][0:-ext_len-1]+'.dds','rb')
		textures_list[k][3],textures_list[k][4],textures_list[k][5],textures_list[k][7]=read_dds_info(t) #store width,height,mipmaps,type
		t.close()
		print(textures_list[k][3],textures_list[k][4],textures_list[k][5],textures_list[k][7])
		
		phys_size=textures_list[k][3]*textures_list[k][4]
		divider=1
		
		size=0
		w=textures_list[k][3]
		h=textures_list[k][4]
		if textures_list[k][7]=='DXT1':
			divider=2
		
		#Calculate Size
		for i in range(textures_list[k][5]):
			size=size+w*h//divider+16
			w=w//2
			h=h//2
		
		
		textures_list[k][6]=size_round(size+16) #store size after calculation
		offset_list.append((2047566042,offset_list[-1][1]+offset_list[-1][2],textures_list[k][6],k))
	
	size=16
	for i in range(len(textures_list)):
		size=size+len(textures_list[i][0])+9
	
	offset_list.append((1285267122,offset_list[-1][1]+offset_list[-1][2],size_round(size)))
	
	return offset_list,textures_list
		
		

def object_separate(ob):
	
	#Separate vertices
	
	verts={}
	for g in ob.vertex_groups:
		verts[g.index]=[]

	print(verts)
	
	
	for vert in ob.data.vertices:
		try:
			verts[vert.groups[0].group].append(vert.index)
		except:
			print('malakia')
	
	
	
	bm=bmesh.from_edit_mesh(ob.data)
	bpy.context.tool_settings.mesh_select_mode = (True,  False, True)
	
	 
	for f in bm.faces:
		f.select=False
	
	for i in range(len(verts)-1):
		for f in bm.faces:
			for v in f.verts:
				if v.index in verts[i]:
					v.select=True
					f.select=True
			
	bmesh.update_edit_mesh(ob.data, False)
	
	#bm.to_mesh(ob.data)
	
	
	#bpy.ops.mesh.separate(type='SELECTED')
	
	bm.free()
	
	print('separating')
		
	
		
			
			
def vector_to_matrix(v):
	matrix=Matrix()
	
	for i in range(len(v)):
		matrix[i][i]=v[i]
		
	return matrix


def face_center(f):
	cx=0
	cy=0
	cz=0
	
	for v in f.verts:
		cx=cx+v.co[0]
		cy=cy+v.co[1]
		cz=cz+v.co[2]
		
	return Vector((cx/len(f.verts),cy/len(f.verts),cz/len(f.verts)))

def write_xml_param(name,index,prop):
	class_name=prop.__class__.__name__
	
	if class_name=='Vector' or class_name=='bpy_prop_array' or class_name=='tuple':
		value_repr='{ '
		for i in range(len(prop)):
			value_repr+=str(round(prop[i],3))
			if i<len(prop)-1:
				value_repr+=', '
			
		value_repr+=' }'	
	else:
		value_repr=str(prop)
		if value_repr=='True':
			value_repr='1'
		elif value_repr=='False':
			value_repr='0'
	
	return '<parameter name='+chr(34)+name+chr(34)+' index='+chr(34)+str(index)+chr(34)+' value='+chr(34)+value_repr+chr(34) +' />\n'
	
	

	
def size_round(size):
	rest=size % 16
	eucl=size // 16
	if rest>0:
		size=eucl*16+16
	return size 