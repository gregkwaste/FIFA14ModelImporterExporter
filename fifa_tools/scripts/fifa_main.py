import bpy,imp,os,struct,bmesh,zlib
#fifa_func_path='fifa_tools\\scripts\\fifa_functions.py'
#fifa_func=imp.load_source('fifa_func',fifa_func_path)
fifa_func=imp.load_compiled('fifa_func','fifa_tools\\scripts\\fifa_functions.pyc')
from mathutils import Vector,Euler,Matrix
from math import radians
from subprocess import call
halfpath='fifa_tools\\scripts\\half.py'
#half=imp.load_source('half',halfpath)
half=imp.load_compiled('half','fifa_tools\\scripts\\half.pyc')
comp=half.Float16Compressor()
sig='FIFA 3D Importer/Exporter, made by arti. v0.65. All rights reserved.©'
#General Helper Function Class
helper=fifa_func.general_helper()
tex_helper=fifa_func.texture_helper()

	

#Create Mesh and Object Function
def createmesh(verts,faces,uvs,name,count,id,subname,colors,normal_flag,normals):
	scn=bpy.context.scene
	mesh=bpy.data.meshes.new("mesh"+str(count))
	mesh.from_pydata(verts,[],faces)
	
	
	
	
	for i in range(len(uvs)):
		uvtex=mesh.uv_textures.new(name='map'+str(i))
	for i in range(len(colors)):
		coltex=mesh.vertex_colors.new(name='col'+str(i))
	
		
		
	bm=bmesh.new()
	bm.from_mesh(mesh)
	
	#Create UV MAPS
	for i in range(len(uvs)):
		uvlayer=bm.loops.layers.uv['map'+str(i)]
		for f in bm.faces:
			for l in f.loops:
				l[uvlayer].uv.x=uvs[i][l.vert.index][0]
				l[uvlayer].uv.y=1-uvs[i][l.vert.index][1]
	

	#Create VERTEX COLOR MAPS
	
	for i in range(len(colors)):
		collayer=bm.loops.layers.color['col'+str(i)]
		for f in bm.faces:
				for l in f.loops:
						l[collayer].r=colors[i][l.vert.index][0]
						l[collayer].g=colors[i][l.vert.index][1]
						l[collayer].b=colors[i][l.vert.index][2]
			
	
	
	#Pass Normals
	if normal_flag==True:
		for i in range(len(normals)):
			bm.verts[i].normal=normals[i]
	 

	# Finish up, write the bmesh back to the mesh
	bm.to_mesh(mesh)
	bm.free()  # free and prevent further access
	
	
	#if name.split(sep='_')[0]=='head':
	#	object=bpy.data.objects.new(name+'_'+str(id)+'_'+str(count)+'_'+subname,mesh)
	if name.split(sep='_')[0] in ['stadium','head']:
		object=bpy.data.objects.new(subname,mesh)
	else:
		object=bpy.data.objects.new(name+'_'+str(id)+'_'+str(count),mesh)
	
	object.location=(0,0,0)
	
	#Transformation attributes inherited from bounding boxes
	#if not name=='stadium': 
		#object.scale=Vector((0.1,0.1,0.1))
		#object.rotation_euler=Euler((1.570796251296997, -0.0, 0.0), 'XYZ')
	scn.objects.link(object)
	
	return object.name

	
#fifa_rx3_class
class fifa_rx3:
	def __init__(self,path,mode):
		
		self.path   =path
		self.data   =0
		self.offsets =[] #file offset list
		self.mesh_offsets=[]
		self.indices_offsets=[]
		self.offset_list=[]
		self.size   ='' #file size text
		self.count   =0
		self.mesh_count   =0 #total meshes in the file
		self.texture_list=[]
		self.texture_count   =0
		self.mesh_descrs=[]
		self.vxtable	=[]
		self.cols   =[]
		self.colcount=[]
		self.v_bones_i  =[]
		self.v_bones_w  =[]
		self.itable   =[]
		self.ntable   =[]
		self.bboxtable=[]
		self.uvs   =[]
		self.uvcount= []
		self.container_type ='' #file header
		self.endianess  ='' #endianess text
		self.endian='' #endianness identifier
		self.bones=[]
		self.props=[]
		self.prop_list=[]
		self.prop_positions=[]
		self.prop_rotations=[]
		self.prop_count=0
		self.tex_names=[]
		self.sub_names=[]
		self.group_names=[]
		self.group_list=[]
		self.type='' #file model type
		self.group_count=0
		self.materials=[]
		self.material_count=0
		self.material_list=[]
		self.materials_dict={}
		self.object_list=[]
		self.mat_assign_table=[]
		self.id=0 #file id
		self.crowd=[]
		self.collisions=[]
		self.collision_list=[]
		self.init_read(self.path,mode)
		self.name=''

	def init_read(self,path,mode):
		scn=bpy.context.scene
		self.name=path.split(sep='\\')[-1].split(sep='.')[0]
		self.id=self.name.split('_')[1]
		self.type=self.name.split(sep='_')[0]
		
		print('-------------------------------------------------------------------------------')
		print('FILE INITIALIZATION')
		print('FILE PATH: ',self.path)
		print('FILE TYPE: ',self.type)
		print('FILE ID:',self.id)
		
		try:
			if mode:
				self.data=open(self.path,'wb')
			else:
				self.data=open(self.path,'r+b')
			if str(self.data.read(8))[2:-1]=='chunkzip':
				
				t=open('fifa_tools\\'+self.path.split(sep='\\')[-1]+'.decompressed','wb')
				self.data.read(12)
				sec_num=struct.unpack('>I',self.data.read(4))[0]
				self.data.read(8)
				for i in range(sec_num):
					#Uniform the offset
					off=self.data.tell() % 4
					#print('Unzlibing section',i , 'Offset', hex(f.data.tell()),off)
					
					if off:
						self.data.read(4-off)
					
					#find sec length
					sec_found=False
					while sec_found==False:
						sec_len=struct.unpack('>I',self.data.read(4))[0]
						if not sec_len==0:
							sec_found=True
					
					
					self.data.read(4) #Skip 00 00 00 01
					data=self.data.read(sec_len)  #Store part  
					
					try:
						t.write(zlib.decompress(data,-15))
					except zlib.error:
						return 'corrupt_file'
					
				t.close()
				self.data=open(t.name,'r+b')
			
			self.data.seek(8)
			original_size=struct.unpack('<I',self.data.read(4))[0]
			f_size=len(self.data.read())+12
			
			#Clopy Checking
			if not original_size==f_size and path.split(sep='.')[-1]=='rx3' and path.split(sep='\\')[-1].split(sep='_')[0]=='stadium' and scn.game_enum in ['0','1']:
				e=open('fifa_tools\\scripts\\msg','r')
				print(e.read())
				print('                           I SEE WHAT YOU DID THERE')
				e.close()
				return 'file_clopy'
			
			self.data.seek(0)
			return(self)
		
		except IOError as e:
			return 'io_error'
		
		
	def overwrite_geometry_data(self):
		scn=bpy.context.scene
		#file is an already opened file, needs to close
		#READ THE COPIED FILE
		self.file_ident()
		self.read_file_offsets(dir)
		
		print('----------------------------')
		print('SEARCHING FOR '+str(self.type).upper()+' PARTS IN THE SCENE')
		
		progress=0 #store processed parts
		for i in range(len(self.mesh_offsets)):
			try:
				name=self.type+'_'+self.id+'_'+str(i)
				if self.type=='head':
					name=name+'_'+self.sub_names[i]
				object=bpy.data.objects[name]
				progress +=1
				print('PROCESSING PART ',name)
			except KeyError:
				print('PART ',name,' NOT FOUND')
				continue
			
			verts=[]
			uvs=[]
			cols=[]
			indices=[]
			
			opts=self.mesh_descr_convert(self.mesh_descrs[i]) ; print(opts)
			verts,uvs,cols,indices=self.convert_original_mesh_to_data(object) #get new geometry data
			#print('Part Description: ',opts,'\n','Part Vertices: ',len(verts),'\n','Part UV maps: ',e.uvcount[i],'\n','Part Indices: ',len(indices),'\n','Part Color maps: ',e.colcount[i])
			
			self.data.seek(self.mesh_offsets[i][0]+16) #get to geometry data offset
			self.convert_mesh_to_bytes(opts,len(verts),verts,uvs,cols) #write geometry data
			#print(e.data.tell())
			if not scn.trophy_flag:
				self.data.seek(self.indices_offsets[i][0]+16) #get to indices data offset
				self.write_indices(indices) #write indices data
				
			print('----------------------------')
			print('OVERWRITTEN ',str(progress), '/',str(len(self.mesh_offsets)), ' PARTS \n')
		self.data.close()		

	
	def convert_original_mesh_to_data(self,object):
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

	def convert_mesh_to_bytes(self,opts,count,verts,uvs,cols):
		for i in range(count):
			for o in opts:
				if o[0]=='p': #verts
					if o[3:]=='4f16':
						helper.write_half_verts(f,verts[i])
					else:
						self.data.write(struct.pack('<3f',round(verts[i][0],8),round(verts[i][1],8),round(verts[i][2],8)))
				elif o[0]=='n': #col0
					col=(int(cols[0][i][0])<<20) + (int(cols[0][i][1])<<10) + (int(cols[0][i][2]))
					self.data.write(struct.pack('<I',col))
				elif o[0]=='g': #col1
					col=(int(cols[1][i][0])<<20) + (int(cols[1][i][1])<<10) + (int(cols[1][i][2]))
					self.data.write(struct.pack('<I',col))
				elif o[0]=='b': #col2
					col=(int(cols[2][i][0])<<20) + (int(cols[2][i][1])<<10) + (int(cols[2][i][2]))
					self.data.write(struct.pack('<I',col))	
				elif o[0]=='t': #uvs
					huvx=eval('comp.compress(round(uvs[int(o[1])][i][0],8))')
					huvy=eval('comp.compress(round(uvs[int(o[1])][i][1],8))')
					self.data.write(struct.pack('<HH',huvx,huvy))
				elif o[0]=='i': #bone indices
					if o[3:]=='4u8':
						self.data.read(4)
					elif o[3:]=='4u16':
						self.data.read(8)
				elif o[0]=='w': #bone weights
					self.data.read(4)	
		
	def read_file_offsets(self,dir):
		scn=bpy.context.scene
		print('READING FILE OFFSETS...')
		log=open('fifa_tools\\log.txt','w')
		
		
		for offset in self.offsets:
			if offset[0]==3263271920: #MESH DESCRIPTIONS
				self.read_mesh_descr(offset[1])
			elif offset[0]==2047566042: #TEXTURES
				self.read_texture(offset[1],dir)
				self.texture_count+=1
			elif offset[0]==4034198449 and scn.collision_flag: #COLLISIONS
				#print('READING COLLISION OBJECTS')
				self.read_collision(offset[1])
			elif offset[0]==685399266: #PROP POSITIONS
				self.read_prop_positions(offset[1])
			elif offset[0]==1285267122: #PROPS
				self.read_props(offset[1],self.endian)
			elif offset[0]==2116321516: #GROUPS
				log.write('Group Offset: ' + str(offset[1]))
				log.write('\n')
				self.read_group(offset[1])
				self.group_count+=1
			elif offset[0]==230948820: #GROUP NAMES
				self.read_group_names(offset[1])
			elif offset[0]==123459928: #MATERIALS
				#print('CREATING MATERIAL')
				self.create_material(offset[1],self.material_count)
				self.material_count+=1
			elif offset[0]==5798132: #INDICES
				if scn.trophy_flag==True:
					temp=helper.facereadstrip(self.data,offset[1],self.endian)
				else:
					temp=helper.facereadlist(self.data,offset[1],self.endian)
				self.itable.append(temp[0])
				self.indices_offsets.append((offset[1],temp[1]))
			elif offset[0]==3751472158: #BONES
				log.write('Bones Detected')
				self.data.seek(offset[1])
				size=struct.unpack(self.endian+'I',self.data.read(4))[0]
				bc=struct.unpack(self.endian+'I',self.data.read(4))[0]
				self.data.read(8)
				self.bones.append(self.read_bones(bc))
				#round((size-int('B0',16))/16)
			elif offset[0]==5798561 and scn.geometry_flag==True: #MESH DATA
				#print('READING MESH DATA')
				self.data.seek(offset[1])
				self.data.read(4)
				vc=struct.unpack(self.endian+'I',self.data.read(4))[0]
				chunk_length=struct.unpack(self.endian+'I',self.data.read(4))[0]
				self.mesh_offsets.append([offset[1],chunk_length])
				count=len(self.mesh_offsets)-1
				self.data.read(4)
				log.write('Mesh Count: %3d || Vert Count: %5d || Chunk Length: %2d || File Offset: %7d || Of Type: %s' % (self.mesh_count,vc,chunk_length,offset[1],self.type))
				
				temp=self.read_test(self.data,self.mesh_descrs[count],vc)
				
				self.vxtable.append(temp[0])
				self.cols.append(temp[1])
				self.colcount.append(len(temp[1]))
				self.uvs.append(temp[2])
				self.uvcount.append(len(temp[2]))
				self.v_bones_i.append(temp[3])
				self.v_bones_w.append(temp[4])
				self.mesh_count+=1
							
				log.write('\n')
				
				
		print('FILE OFFSETS READ')
		log.close() 	
		#IDENTIFY THE FILE
	def file_ident(self):
		self.container_type,self.endianess,self.endian,self.size,self.offsets,self.count= self.file_ident_func()
	
	def file_ident_func(self):
		print('FILE IDENTIFICATION IN PROGRESS')
		offsets=[]
		name=str(self.data.read(3))[2:-1]
		endian=str(self.data.read(1))[2:-1]
		if endian=='b':
			endian='>'
			endianstr='Big Endian'
		elif endian=='l':
			endian='<'  
			endianstr='Little Endian'
		print('ENDIANNESS DETECTED: ',endianstr)
		
		self.data.read(4)
		filesize=struct.unpack(endian+'I',self.data.read(4))[0]
		sect_num=struct.unpack(endian+'I',self.data.read(4))[0]
		print('DESCRIPTIONS DETECTED: ',sect_num)
		
		#Populate Offset List
		for i in range(0,sect_num):
			offsets.append((struct.unpack(endian+'I',self.data.read(4))[0],struct.unpack(endian+'I',self.data.read(4))[0]))
			self.data.read(8)

		##OFFSET PRINTING
		#for off in offsets:
		#   print(off)
		
		mesh_count=struct.unpack(endian+'I',self.data.read(4))[0]
		print('MESH OBJECTS: ',mesh_count)
		
		return name,endianstr,endian,('Total File Size:',round((filesize/1024),2),'KBs'),offsets,mesh_count
		
	def read_mesh_descr(self,offset):
		self.data.seek(offset)
		self.data.read(4)
		length=struct.unpack(self.endian+'i',self.data.read(4))[0]
		self.data.read(8)
		
		descr_str=''
		list=[]
		temp=[]
		part=''
		
		vflag=0
		uvcount=0
		cols=0
		bones_i=False
		bones_w=False
		
		for i in self.data.read(length):
			
			if i==32 or i==0:
				temp.append(part)
				list.append(temp)
				temp=[]
				part=''
			elif i==58:
				temp.append(part)
				part='' 
			else:
				part=part+chr(i)				   
		
		self.mesh_descrs.append(list)

	def read_test(self,f,opts,count):
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
						verts.append(helper.read_vertices_1(f))   #READ VERTICES
					elif j[4]=='4f16':
						verts.append(helper.read_vertices_0(f))
				elif j[0][0]=='t':
					if j[4]=='2f32':
						eval('uvs_'+str(j[0][1])+'.append(helper.read_uvs_1(f))')
					elif j[4]=='2f16':
						eval('uvs_'+str(j[0][1])+'.append(helper.read_uvs_0(f))')
					uvcount+=1
				elif j[0][0]=='n':
					colcount+=1
					cols_0.append(helper.read_cols(f))
				elif j[0][0]=='b':
					colcount+=1
					cols_2.append(helper.read_cols(f))
				elif j[0][0]=='g':
					colcount+=1
					cols_1.append(helper.read_cols(f))
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
		
	def mesh_descr_convert(self,descr):
		opts=[]
		for i in descr:
			opts.append(i[0]+':'+i[4])
		return opts

	def read_props(self,offset,endian):
		self.data.seek(offset)
		self.data.read(4)
		count=struct.unpack(endian+'i',self.data.read(4))[0]
		self.data.read(8)
		print('READING PROPS', 'COUNT: ',count)
		
		if self.type.endswith('_texture'):
			#Initialize array
			for i in range(count):
				self.tex_names.append('')
			
			for i in range(count):
				self.data.read(4)
				textlen=struct.unpack(endian+'i',self.data.read(4))[0]
				text=''
				for j in range(textlen):
					text=text+chr(struct.unpack(endian+'B',self.data.read(1))[0]) 
				text=text[0:-1] 
				try:
					os.rename('fifa_tools\\texture_'+str(i)+'.dds','fifa_tools\\'+text+'.dds')
					print('Renaming texture_'+str(i)+'.dds to '+text+'.dds')
					self.tex_names[i]=text+'.dds'
				except FileNotFoundError:
					print('Unsupported Image File')
				except FileExistsError:
					print('!!!File Exists!!!')   
					self.tex_names[i]=text+'.dds'
		
		else:
			for i in range(count):
				off=struct.unpack(endian+'I',self.data.read(4))[0]
				textlen=struct.unpack(endian+'I',self.data.read(4))[0]
				text=''
				#text=fifa_func.read_string(self.data)
				for j in range(textlen):
					text=text+chr(struct.unpack(endian+'B',self.data.read(1))[0]) 
				text=text[0:-1] 
				
					
				if off==685399266:
					self.props.append(text)
					self.prop_count+=1  
				elif off==3566041216:
					#print(text,textlen)
					self.sub_names.append(text.split(sep='.')[0].split(sep='_')[0])
				elif off==2047566042:
					self.tex_names.append(text+'.dds')  

	def read_prop_positions(self,offset):
		self.data.seek(offset)
		self.data.read(4)
		temp=struct.unpack('<3f',self.data.read(12))
		rot=struct.unpack('<3f',self.data.read(12))
		self.prop_positions.append((0.01*temp[0],-0.01*temp[2],0.01*temp[1]))
		self.prop_rotations.append((rot[0],rot[1],rot[2]))

	def read_bones(self,count):
		temp=[]
		for k in range(count):
			mat=Matrix()
			mat=mat.to_4x4()
			for i in range(4):
				for j in range(4):
					mat[j][i]=round(struct.unpack('<f',self.data.read(4))[0],8)
			
			
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
			axis, roll = helper.mat3_to_vec_roll(mat.to_3x3())
			#pos = rot*pos
			if k in [2,3,4,324,333]:
				#print('Matrix ID= ',k)
				#print(mat.to_euler())
				#print(mat.to_scale())
				print(sz)
				print(pos)
			temp.append((pos,pos+axis,roll)) #bone.head=pos, #bone.tail=pos+axis, #bone.roll=roll
		return temp		

	#Create Texture Function	
	def read_texture(self,offset,path):
		self.data.seek(offset)
		overall_size=struct.unpack(self.endian+'i',self.data.read(4))[0]
		self.data.read(1)
		identifier=struct.unpack(self.endian+'B',self.data.read(1))[0]
		self.data.read(2)
		width=struct.unpack(self.endian+'h',self.data.read(2))[0]
		height=struct.unpack(self.endian+'h',self.data.read(2))[0]
		self.data.read(2)
		mipmaps=struct.unpack(self.endian+'h',self.data.read(2))[0]
		self.data.read(8)
		size=struct.unpack(self.endian+'i',self.data.read(4))[0]
		self.data.read(4)
		
		if identifier==0:
			data=tex_helper.read_dds_header(0)
			#data[87]=49
			string='DXT1'
		elif identifier==1:
			data=tex_helper.read_dds_header(0)
			data[87]=51
			string='DXT3'
		elif identifier==2:
			data=tex_helper.read_dds_header(144)
			#data[87]=53
			string='DXT5'
		elif identifier==7:
			data=tex_helper.read_dds_header(288)
			#data[86]=49
			#data[87]=48
			string='NVTT'
		else:
			print('NOT RECOGNISABLE IMAGE FILE')
			return  
			
		
		##Assign Changed Values
		data[12]=height.to_bytes(2,'little')[0]
		data[13]=height.to_bytes(2,'little')[1]
		data[16]=width.to_bytes(2,'little')[0]
		data[17]=width.to_bytes(2,'little')[1]
		data[28]=mipmaps.to_bytes(1,'little')[0]	
		
		#log=open('fifa_tools\\log.txt','a')
		#log.write('Writing File: ' +path+'texture_'+str(self.texture_count)+'.dds'+' From File Offset '+str(offset)+ ' Of Type:'+string)
		#log.write('\n')
		
		tf=open('fifa_tools\\'+'texture_'+str(self.texture_count)+'.dds','wb')
		[tf.write(b) for b in [struct.pack('<B',x) for x in data]]
		
		for i in range(mipmaps):
			tf.write(self.data.read(size))
			self.data.read(8)
			size=struct.unpack(self.endian+'i',self.data.read(4))[0]
			self.data.read(4)
			
		
		
		#print(data)
		#log.close()
		tf.close()
	
	def create_material(self,offset,count):
		self.data.seek(offset)
		self.data.read(4)
		tex_num=struct.unpack(self.endian+'i',self.data.read(4))[0]
		self.data.read(8)
		entry=[]
		mat_name=helper.read_string(self.data)+'_'+str(count)
		
		#print(len(self.tex_names))
		for i in range(tex_num):
			texture_type=helper.read_string(self.data)
			#slot=new_mat.texture_slots.add()
			tex_id=struct.unpack('<i',self.data.read(4))[0]
			texture_name=texture_type+'_'+str(tex_id)
			#print(tex_id)
			try:
				entry.append((texture_name,'fifa_tools\\'+self.tex_names[tex_id]))
			except:
				entry.append((texture_name,'fifa_tools\\texture_'+str(tex_id)))
			
		self.materials.append((mat_name,entry))
		
		return {'FINISHED'}
			
	def read_group(self,offset):
		scn=bpy.context.scene
		name='group_'+str(self.group_count)
		#print(name)
		self.data.seek(offset)
		self.data.read(4)
		group_status=struct.unpack(self.endian+'I',self.data.read(4))[0]
		
		if not group_status:
			return
			
		self.data.read(72)
		vec1=Vector((struct.unpack(self.endian+'f',self.data.read(4))[0],struct.unpack(self.endian+'f',self.data.read(4))[0],struct.unpack(self.endian+'f',self.data.read(4))[0]))
		self.data.read(4)
		vec2=Vector((struct.unpack(self.endian+'f',self.data.read(4))[0],struct.unpack(self.endian+'f',self.data.read(4))[0],struct.unpack(self.endian+'f',self.data.read(4))[0]))
		self.data.read(4)
		group_items=struct.unpack(self.endian+'i',self.data.read(4))[0]
		self.data.read(4)
		if scn.geometry_flag:
			helper.create_boundingbox(vec1,vec2,name)
		
		for i in range(group_items):
			ivec1=Vector((struct.unpack(self.endian+'f',self.data.read(4))[0],struct.unpack(self.endian+'f',self.data.read(4))[0],struct.unpack(self.endian+'f',self.data.read(4))[0]))
			self.data.read(4)
			ivec2=Vector((struct.unpack(self.endian+'f',self.data.read(4))[0],struct.unpack(self.endian+'f',self.data.read(4))[0],struct.unpack(self.endian+'f',self.data.read(4))[0]))
			self.data.read(4)
			self.bboxtable.append((ivec1,ivec2))
			part_id=struct.unpack(self.endian+'i',self.data.read(4))[0]
			render_line=struct.unpack(self.endian+'i',self.data.read(4))[0]
			self.mat_assign_table.append((part_id,render_line,self.group_count))
		
	def read_group_names(self,offset):
		self.data.seek(offset)
		self.data.read(16)
		group_name=helper.read_string(self.data)
		#print(group_name)
		self.group_names.append(group_name) 

	def read_collision(self,offset):
		self.data.seek(offset)
		self.data.read(16)
		name=helper.read_string(self.data)
		self.data.read(4)
		triscount=struct.unpack('<I',self.data.read(4))[0]
		indices=[]
		verts=[]
		j=0 #COUNTER FOR INDICES
		for i in range(triscount):
			for k in range(3): #3 VERTICES
				temp=struct.unpack('<3f',self.data.read(12))
				verts.append((temp[0]/100,-temp[2]/100,temp[1]/100))
			# TRIANGLE DEFINITION
			indices.append((j,j+1,j+2))
			j+=3
			
		self.collisions.append((name,verts,indices))

	def write_offsets_to_file(self):
		#Calculate file size
		size=0
		for off in self.offset_list:
			size+=off[2]+16
		#File Header
		self.data.write(struct.pack('<4I',1815304274,4,size+16,len(self.offset_list)))
		for i in self.offset_list:
			self.data.write(struct.pack('<4I',i[0],i[1],i[2],0))

	def write_offset_data_to_file(self,path):
		#Local Variables
		object_count=len(self.object_list)
		texture_count=len(self.texture_list)
		for i in range(len(self.offset_list)):
			self.data.seek(self.offset_list[i][1])
			if self.offset_list[i][0]==582139446:
				self.data.write(struct.pack('<4I',object_count,0,0,0))
				for j in range(object_count):
					if self.object_list[j][1]>65535:
						ind_size=4
					else:
						ind_size=2
					self.data.write(struct.pack('<4I',helper.size_round(self.object_list[j][2]*ind_size+16),self.object_list[j][2],ind_size,0))
			elif self.offset_list[i][0]==3263271920: #mesh description
				id=self.offset_list[i][3]
				self.data.write(struct.pack('<4I',self.offset_list[i][2],len(self.object_list[id][6])+1,0,0))
				s = bytes(self.object_list[id][6], 'utf-8')
				self.data.write(s) 
			elif self.offset_list[i][0]==685399266: # PROP POSITIONS
				id=self.offset_list[i][3]
				self.data.write(struct.pack('<Ifff',self.offset_list[i][2],self.prop_list[id][1][0],self.prop_list[id][1][1],self.prop_list[id][1][2]))
				self.data.write(struct.pack('<fffI',self.prop_list[id][2][0],self.prop_list[id][2][1],self.prop_list[id][2][2],0))
			elif self.offset_list[i][0]==1285267122: #PROPS
				#header
				self.data.write(struct.pack('<4I',self.offset_list[i][2],len(self.prop_list)+len(self.texture_list)+len(self.object_list),0,0))
				#data
				for j in range(len(self.prop_list)):
					self.data.write(struct.pack('<2I',685399266,len(self.prop_list[j][0])+1))
					s = bytes(self.prop_list[j][0], 'utf-8')
					self.data.write(s)
					self.data.write(b'\x00')
				for j in range(len(self.object_list)):
					self.data.write(struct.pack('<2I',3566041216,len(self.object_list[j][0])+1))
					s = bytes(self.object_list[j][0], 'utf-8')
					self.data.write(s)
					self.data.write(b'\x00')
				for j in range(len(self.texture_list)):
					self.data.write(struct.pack('<I',2047566042))
					
					if type(self.texture_list[j])==type(''):
						s = bytes(self.texture_list[j], 'utf-8')
						self.data.write(struct.pack('<I',len(self.texture_list[j])+1))
					
					elif type(self.texture_list[j][0])==type(''):
						#print('textures')
						s = bytes(self.texture_list[j][0], 'utf-8')
						self.data.write(struct.pack('<I',len(self.texture_list[j][0])+1))
					
					self.data.write(s)
					self.data.write(b'\x00')
				
				
				
				
			elif self.offset_list[i][0]==5798132: #INDICES
				id=self.offset_list[i][3]
				#header
				if self.object_list[id][1]>65535:
					ind_size=4
				else:
					ind_size=2
				self.data.write(struct.pack('<4I',helper.size_round(self.object_list[id][2]*ind_size+16),self.object_list[id][2],ind_size,0))  
				#data
				self.write_indices(self.object_list[id][11])
			elif self.offset_list[i][0]==5798561: #VERTICES
				id=self.offset_list[i][3]
				#header
				self.data.write(struct.pack('<4I',self.offset_list[i][2],self.object_list[id][1],self.object_list[id][8],1))
				#data
				self.convert_mesh_to_bytes(self.object_list[id][7],self.object_list[id][1],self.object_list[id][9],self.object_list[id][10],self.object_list[id][4])
			elif self.offset_list[i][0]==3566041216: #80......
				self.data.write(struct.pack('<4I',4,0,0,0))
			elif self.offset_list[i][0]==230948820: #GROUPS
				id=self.offset_list[i][3]
				#print(id,len(group_list))
				#header
				data=self.data.write(struct.pack('<4I',self.offset_list[i][2],1,0,0))	
				#data
				if id>=len(group_list):
					s = bytes('CollisionGeometry', 'utf-8')
					data+=self.data.write(s)
					data+=self.data.write(b'\x00')
					data+=self.data.write(struct.pack('B',id)) 
				else:
					s = bytes(group_list[id][0][5:], 'utf-8')
					self.data.write(s)	
					self.data.write(b'\x00')
					self.data.write(struct.pack('B',id)) 
			elif self.offset_list[i][0]==123459928:
				id=self.offset_list[i][3]
				#material header
				self.data.write(struct.pack('<4I',self.offset_list[i][2],len(materials_dict[materials_list[id]][3]),0,0))
				#data
				#material_name
				#print(materials_dict[materials_list[id]][1])
				s=bytes(materials_dict[materials_list[id]][1],'utf-8')
				self.data.write(s)
				self.data.write(b'\x00')
				#textures
				for j in range(len(materials_dict[materials_list[id]][2])):
					s=bytes(materials_dict[materials_list[id]][3][j],'utf-8')
					self.data.write(s)
					self.data.write(b'\x00')
					#print(self.texture_list.index(materials_dict[materials_list[id]][2][j]))
					self.data.write(struct.pack('I',self.texture_list.index(materials_dict[materials_list[id]][2][j])))
			elif self.offset_list[i][0]==2116321516: #RENDERLINES
				id=self.offset_list[i][3]
				#renderline header
				self.data.write(struct.pack('<4I',self.offset_list[i][2],1,4294967295,0))
				#renderline data
				self.data.write(struct.pack('<4f',1,0,0,0))
				self.data.write(struct.pack('<4f',0,1,0,0))
				self.data.write(struct.pack('<4f',0,0,1,0))
				self.data.write(struct.pack('<4f',0,0,0,1))
				self.data.write(struct.pack('<4f',group_list[id][1][0],group_list[id][1][1],group_list[id][1][2],1))
				self.data.write(struct.pack('<4f',group_list[id][2][0],group_list[id][2][1],group_list[id][2][2],1))
				self.data.write(struct.pack('<2I',group_list[id][3],4294967295))
				object_offset=group_list[id][4]
				for j in range(group_list[id][3]):
					self.data.write(struct.pack('<4f',self.object_list[object_offset+j][5][0][0],self.object_list[object_offset+j][5][0][1],self.object_list[object_offset+j][5][0][2],1))
					self.data.write(struct.pack('<4f',self.object_list[object_offset+j][5][1][0],self.object_list[object_offset+j][5][1][1],self.object_list[object_offset+j][5][1][2],1))
					self.data.write(struct.pack('<2I',object_offset+j,self.object_list[object_offset+j][13]))
			elif self.offset_list[i][0]==4034198449: #COLLISIONS
				id=self.offset_list[i][3]
				self.data.write(struct.pack('4I',self.offset_list[i][2],1,0,0))
				s=bytes(collision_list[id][2],'utf-8')
				self.data.write(s)
				self.data.write(b'\x00')
				self.data.write(struct.pack('I',1))
				self.data.write(struct.pack('I',collision_list[id][0]))
				for i in range(len(collision_list[id][1])):
					self.data.write(struct.pack('<3f',collision_list[id][1][i][0],collision_list[id][1][i][1],collision_list[id][1][i][2]))
				
			elif self.offset_list[i][0]==1808827868:
				self.data.write(struct.pack('<4I',texture_count,0,0,0))
				id=0
				for tex in self.texture_list:
					if tex[7]=='DXT5':
						id=2
					self.data.write(struct.pack('<IBBHHHHH',tex[6],1,id,1,tex[3],tex[4],1,tex[5]))
			elif self.offset_list[i][0]==2047566042:
				id=self.offset_list[i][3]
				#texture writing
				ext_len=len(self.texture_list[id][1].split(sep='\\')[-1].split(sep='.')[-1])
				
				t=open(path+self.texture_list[id][1].split(sep='\\')[-1][0:-1-ext_len]+'.dds','rb')
				
				#Get ready to write
				divider=1
				comp_id=0
				w=self.texture_list[id][3]
				h=self.texture_list[id][4]
				phys_size=w*h
				mipmaps=self.texture_list[id][5]
				if self.texture_list[id][7]=='DXT1':
					divider=2
					multiplier=2
				if self.texture_list[id][7]=='DXT5':
					comp_id=2
					multiplier=4
				t.seek(128)
				
				#Write texture
				#header
				self.data.write(struct.pack('<IBBHHHHH',self.texture_list[id][6],1,comp_id,1,self.texture_list[id][3],self.texture_list[id][4],1,self.texture_list[id][5]))
				#data
				size=phys_size
				for j in range(mipmaps):
					tw=size//(w*multiplier*divider)
					self.data.write(struct.pack('<4I',w*multiplier,tw,w*multiplier*tw,0))
					self.data.write(t.read(tw*w*multiplier))
					#print(tw)
					w=w//2
					size=size//4
				t.close()		

	def write_offsets(self,data_pass):
		#Useful variables:
		object_count=len(self.object_list)
		material_count=len(self.material_list)
		group_count=len(self.group_list)
		prop_count=len(self.prop_list)
		collision_count=len(self.collision_list)
		scn=bpy.context.scene
		
		#offset_list format: IDENTIFIER  OFFSET   SIZE	ID
		if data_pass==0:
			self.offset_list.append([582139446,0,0])
			for i in range(object_count):
				self.offset_list.append([3263271920,0,0,i])
			self.offset_list.append([1285267122,0,0])
			for i in range(object_count):
				self.offset_list.append([5798132,0,0,i])
			
			#HEAD SPECIFIC
			if scn.face_edit_head_flag:
				for i in range(object_count):
					self.offset_list.append([255353250,0,0,i])
			
			for i in range(object_count):
				self.offset_list.append([5798561,0,0,i])
			
			#HEAD SPECIFIC
			if scn.face_edit_head_flag:
				for i in range(object_count):
					self.offset_list.append([3751472158,0,0,i])
			
			for i in range(object_count):
				self.offset_list.append([3566041216,0,0,i])
			
			#STADIUM SPECIFICS
			if scn.stadium_export_flag:
				for i in range(prop_count):
					self.offset_list.append([685399266,0,0,i])
				for i in range(collision_count):
					self.offset_list.append([4034198449,0,0,i])
				for i in range(material_count):
					self.offset_list.append([123459928,0,0,i])
				for i in range(group_count):
					self.offset_list.append([2116321516,0,0,i])
				for i in range(group_count+1):
					self.offset_list.append([230948820,0,0,i])   
		
		elif data_pass==1:
			
			table_size=len(self.offset_list)
			
			for i in range(table_size):
				#Calculating Offsets
				if i==0:
					self.offset_list[i][1]=table_size*16+16
				else:	
					self.offset_list[i][1]=self.offset_list[i-1][1]+self.offset_list[i-1][2]
				
				#Calculating Sizes
				if self.offset_list[i][0]==582139446:
					self.offset_list[i][2]=16+len(self.object_list)*16
				elif self.offset_list[i][0]==1285267122:
					size=16
					for j in range(len(self.prop_list)):
						size+=len(self.prop_list[j][0])+1+8
					for j in range(len(self.object_list)):
						size+=len(self.object_list[j][0])+1+8
					for j in range(len(self.texture_list)):
						size+=len(self.texture_list[j])+1+8
					self.offset_list[i][2]=helper.size_round(size)
				elif self.offset_list[i][0]==3263271920:
					#Local Variables
					id=self.offset_list[i][3]
					self.offset_list[i][2]=helper.size_round(len(self.object_list[id][6])+1+16)
				elif self.offset_list[i][0]==5798132:
					#Local Variables
					id=self.offset_list[i][3]
					if self.object_list[id][1]>65535:
						ind_size=4
					else:
						ind_size=2
					self.offset_list[i][2]=helper.size_round(self.object_list[id][2]*ind_size+16)
				elif self.offset_list[i][0]==5798561:
					#Local Variables
					id=self.offset_list[i][3]
					self.offset_list[i][2]=helper.size_round(16+self.object_list[id][1]*self.object_list[id][8])
				elif self.offset_list[i][0]==3566041216:
					self.offset_list[i][2]=16
				elif self.offset_list[i][0]==4034198449:
					#Local Variables
					id=self.offset_list[i][3]
					self.offset_list[i][2]=helper.size_round(16+len(self.collision_list[id][2])+1+4+self.collision_list[id][0]*3*12)
				elif self.offset_list[i][0]==685399266:
					self.offset_list[i][2]=32
				elif self.offset_list[i][0]==123459928:
					#Local Variables
					id=self.offset_list[i][3]
					self.offset_list[i][2]=materials_dict[self.material_list[id]][4]
				elif self.offset_list[i][0]==230948820:
					#Local Variables
					id=self.offset_list[i][3]
					try:
						self.offset_list[i][2]=helper.size_round(16+len(self.group_list[id][0][5:])+5)
					except IndexError:
						self.offset_list[i][2]=48	
				elif self.offset_list[i][0]==2116321516:
					#Local Variables
					id=self.offset_list[i][3]
					self.offset_list[i][2]=helper.size_round(16+4*16+32+8+self.group_list[id][3]*40)								
									
	def write_indices(self,indices):
		#print('Indices Length: ',indices[0])
		if 3*len(indices)>65535:
			ind_size=4
			format='<III'   
		else:
			ind_size=2
			format='<HHH'

		for entry in indices:
			self.data.write(struct.pack(format,entry[0],entry[1],entry[2]))
					
				
#GENERAL FIFA FUNCTIONS
		
def write_textures_to_file(textures_list,type):
	scn=bpy.context.scene
	if scn.stadium_export_flag:
		f_name='stadium_'+str(scn.file_id)+'_'+scn.stadium_version+'_textures.rx3'
	elif scn.trophy_export_flag:
		f_name='trophy-ball_'+str(scn.file_id)+'_textures.rx3'
	elif scn.gen_overwriter_flag or scn.face_edit_flag:
		f_name=type+'_'+str(scn.file_id)+'_textures.rx3'
	
	f=fifa_rx3(scn.export_path+f_name,1) #open file
	
	scn=bpy.context.scene
	status=texture_convert(textures_list)
	if status.split(sep=',')[0]=='texture_path_error':
		return 'missing_texture_file'
	#Read converted textures and calculate offsets and texture information
	f.offset_list,f.texture_list=read_converted_textures(f.offset_list,textures_list,'fifa_tools\\')
	
	
	
	#Calling Writing to file Functions
	
	f.write_offsets_to_file()
	f.write_offset_data_to_file('fifa_tools\\')
	
	#Signature
	f.data.seek(f.offset_list[-1][1])
	f.data.seek(f.offset_list[-1][2],1)
	s=bytes(sig,'utf-8')
	f.data.write(s)
	f.data.close()	
	print(f.offset_list)
	return 'success'
		
def read_converted_textures(offset_list,textures_list,path):
	offset_list.append((1808827868,len(textures_list)*16+48,len(textures_list)*16+16))
	
	for k in range(len(textures_list)):
		ext_len=len(textures_list[k][1].split(sep='\\')[-1].split(sep='.')[-1])
		
		t=open(path+textures_list[k][1].split(sep='\\')[-1][0:-ext_len-1]+'.dds','rb')
		textures_list[k][3],textures_list[k][4],textures_list[k][5],textures_list[k][7]=tex_helper.read_dds_info(t) #store width,height,mipmaps,type
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
		
		
		textures_list[k][6]=helper.size_round(size+16) #store size after calculation
		offset_list.append((2047566042,offset_list[-1][1]+offset_list[-1][2],textures_list[k][6],k))
	
	size=16
	for i in range(len(textures_list)):
		size=size+len(textures_list[i][0])+9
	
	offset_list.append((1285267122,offset_list[-1][1]+offset_list[-1][2],helper.size_round(size)))
	
	return offset_list,textures_list
		
def crowd_seat_align(align_vector):
	scn=bpy.context.scene
	ob=bpy.context.object
	bm=bmesh.from_edit_mesh(ob.data)
	
	for f in bm.faces:
		if f.select==True:
			base=helper.face_center(f)
			
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
		
		
		boundbox=helper.object_bbox(object)
		
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
	
def read_crowd_14(file): #NOT USED
	print('READING CROWD FILE')
	header=file.data.read(4).decode('utf-8')
	if not header=='CRWD':
		print('NOT A VALID CROWD FILE')
		return
	file.data.read(2)
	count=struct.unpack('<H',file.data.read(2))[0]
	print(count)
	
	
	
	for i in range(count):
		file.data.read(2)
		#COORDINATES
		verts=struct.unpack('<3f',file.data.read(12))
		
		#ZROTATION
		zrot=struct.unpack('<f',file.data.read(4))[0]  
		
		#Color
		rawr=struct.unpack('<B',file.data.read(1))[0]   
		rawg=struct.unpack('<B',file.data.read(1))[0]
		rawb=struct.unpack('<B',file.data.read(1))[0]

		r=hex(rawr)[2:]
		g=hex(rawg)[2:]
		b=hex(rawb)[2:]
		color='#'+str(r)+str(g)+str(b)
		
		r=float(rawr/255)
		g=float(rawg/255)
		b=float(rawb/255)
		colorrgb=(r,g,b)
		#print(colorrgb) 
		#print(color)
		#   file.data.read(1)
		
		
		c_status=struct.unpack('<B',file.data.read(1))[0]
		c_attendance=struct.unpack('<B',file.data.read(1))[0]
		#ha=struct.unpack('<3B',file.data.read(3)) #skipping
		#set1=struct.unpack('I',file.data.read(4))
		#set2=struct.unpack('I',file.data.read(4))
		#set3=struct.unpack('I',file.data.read(4))
		#set4=struct.unpack('I',file.data.read(4))
		
		file.crowd.append((verts,zrot,c_status,c_attendance,colorrgb,color,set1,set2,set3,set4))

def read_crowd_15(file):
	scn=bpy.context.scene
	print('READING CROWD FILE')
	header=file.data.read(4).decode('utf-8')
	if not header=='CRWD':
		print('NOT A VALID CROWD FILE')
		return
	file.data.read(2)
	count=struct.unpack('<H',file.data.read(2))[0]
	print(count)
	t=open('crowd_log.txt','w')
	
	if scn.game_enum=="2":
		skip=9
	else:
		skip=19
		
	for i in range(count):
		file.data.read(2)
		#COORDINATES
		verts=struct.unpack('<3f',file.data.read(12))
		#verts=(verts[0],-verts[2],verts[1])
		
		#ZROTATION
		zrot=struct.unpack('<f',file.data.read(4))[0]  
		
		#Color
		rawr=struct.unpack('<B',file.data.read(1))[0]   
		rawg=struct.unpack('<B',file.data.read(1))[0]
		rawb=struct.unpack('<B',file.data.read(1))[0]

		r=hex(rawr)[2:]
		g=hex(rawg)[2:]
		b=hex(rawb)[2:]
		color='#'+str(r)+str(g)+str(b)
		
		r=float(rawr/255)
		g=float(rawg/255)
		b=float(rawb/255)
		colorrgb=(r,g,b)
		#print(colorrgb) 
		#print(color)
		#   file.data.read(1)
		
		
		c_status=struct.unpack('<B',file.data.read(1))[0]
		c_attendance=struct.unpack('<B',file.data.read(1))[0]
		t.write(str(c_status)+'       '+str(file.data.read(skip))+'\n')
		file.crowd.append((verts,zrot,c_status,c_attendance,colorrgb,color))
	t.close()

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
	
	

