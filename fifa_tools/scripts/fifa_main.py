import bpy,imp,os,struct,bmesh,zlib
fifa_func_path='fifa_tools\\scripts\\fifa_functions.py'
fifa_func=imp.load_source('fifa_func',fifa_func_path)
from mathutils import Vector,Euler,Matrix
halfpath='fifa_tools\\scripts\\half.py'
half=imp.load_source('half',halfpath)
comp=half.Float16Compressor()


def read_file_offsets(file,dir):
	print('READING FILE OFFSETS...')
	log=open('fifa_tools\\log.txt','w')
	scn=bpy.context.scene
	
	for offset in file.offsets:
		if offset[0]==3263271920: #MESH DESCRIPTIONS
			read_mesh_descr(file,offset[1])
		elif offset[0]==2047566042: #TEXTURES
			read_texture(file,offset[1],file.endian,dir)
			file.texture_count+=1
		elif offset[0]==4034198449 and scn.collision_flag: #COLLISIONS
			#print('READING COLLISION OBJECTS')
			read_collision(file,offset[1])
		elif offset[0]==685399266: #PROP POSITIONS
			read_prop_positions(file,offset[1])
		elif offset[0]==1285267122: #PROPS
			read_props(file,offset[1],file.endian)
		elif offset[0]==2116321516: #GROUPS
			log.write('Group Offset: ' + str(offset[1]))
			log.write('\n')
			read_group(file,offset[1],file.endian)
			file.group_count+=1
		elif offset[0]==230948820: #GROUP NAMES
			read_group_names(file,offset[1])
		elif offset[0]==123459928: #MATERIALS
			#print('CREATING MATERIAL')
			create_material(file,offset[1],file.material_count)
			file.material_count+=1
		elif offset[0]==5798132: #INDICES
			if scn.trophy_flag==True:
				temp=fifa_func.facereadstrip(file.data,offset[1],file.endian)
				file.itable.append(temp[0])
				file.indices_offsets.append((offset[1],temp[1]))
			else:
				temp=fifa_func.facereadlist(file.data,offset[1],file.endian)
				file.itable.append(temp[0])
				file.indices_offsets.append((offset[1],temp[1]))
		elif offset[0]==3751472158: #BONES
			log.write('Bones Detected')
			file.data.seek(offset[1])
			size=struct.unpack(file.endian+'I',file.data.read(4))[0]
			bc=struct.unpack(file.endian+'I',file.data.read(4))[0]
			file.data.read(8)
			file.bones.append(fifa_func.read_bones(file.data,bc))
			#round((size-int('B0',16))/16)
		elif offset[0]==5798561 and scn.geometry_flag==True: #MESH DATA
			#print('READING MESH DATA')
			file.data.seek(offset[1])
			file.data.read(4)
			vc=struct.unpack(file.endian+'I',file.data.read(4))[0]
			chunk_length=struct.unpack(file.endian+'I',file.data.read(4))[0]
			file.mesh_offsets.append([offset[1],chunk_length])
			count=len(file.mesh_offsets)-1
			file.data.read(4)
			log.write('Mesh Count: %3d || Vert Count: %5d || Chunk Length: %2d || File Offset: %7d || Of Type: %s' % (file.mesh_count,vc,chunk_length,offset[1],file.type))
			
			temp=fifa_func.read_test(file.data,file.mesh_descrs[count],vc)
			
			file.vxtable.append(temp[0])
			file.cols.append(temp[1])
			file.colcount.append(len(temp[1]))
			file.uvs.append(temp[2])
			file.uvcount.append(len(temp[2]))
			file.v_bones_i.append(temp[3])
			file.v_bones_w.append(temp[4])
			file.mesh_count+=1
						

			
			
				
			log.write('\n')
			
			
	print('FILE OFFSETS READ')
	log.close() 



def read_mesh_descr(file,offset):
	file.data.seek(offset)
	file.data.read(4)
	length=struct.unpack(file.endian+'i',file.data.read(4))[0]
	file.data.read(8)
	
	descr_str=''
	list=[]
	temp=[]
	part=''
	
	vflag=0
	uvcount=0
	cols=0
	bones_i=False
	bones_w=False
	
	for i in file.data.read(length):
		
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
	
#   print(list)
#   for i in list:
#   if i[0][0]=='p':
#   if i[4]=='3f32':
#   vflag=1
#   else:
#   vflag=0
#   elif i[0][0] in ['n','g']:
#   cols+=1
#   elif i[0][0]=='t':
#   uvcount+=1
#   elif i[0][0]=='i':
#   bones_i=True
#   elif i[0][0]=='w':
#   bones_w=True			
#   
#   print((vflag,cols,uvcount,bones_i,bones_w))
#   file.mesh_descrs.append((vflag,cols,uvcount,bones_i,bones_w))

	file.mesh_descrs.append(list)
	


def read_group(file,offset,endian):
	scn=bpy.context.scene
	name='group_'+str(file.group_count)
	#print(name)
	file.data.seek(offset)
	file.data.read(4)
	group_status=struct.unpack(endian+'I',file.data.read(4))[0]
	
	if not group_status:
		return
		
	file.data.read(72)
	vec1=Vector((struct.unpack(endian+'f',file.data.read(4))[0],struct.unpack(endian+'f',file.data.read(4))[0],struct.unpack(endian+'f',file.data.read(4))[0]))
	file.data.read(4)
	vec2=Vector((struct.unpack(endian+'f',file.data.read(4))[0],struct.unpack(endian+'f',file.data.read(4))[0],struct.unpack(endian+'f',file.data.read(4))[0]))
	file.data.read(4)
	group_items=struct.unpack(endian+'i',file.data.read(4))[0]
	file.data.read(4)
	if scn.geometry_flag:
		fifa_func.create_boundingbox(vec1,vec2,name)
	
	for i in range(group_items):
		ivec1=Vector((struct.unpack(endian+'f',file.data.read(4))[0],struct.unpack(endian+'f',file.data.read(4))[0],struct.unpack(endian+'f',file.data.read(4))[0]))
		file.data.read(4)
		ivec2=Vector((struct.unpack(endian+'f',file.data.read(4))[0],struct.unpack(endian+'f',file.data.read(4))[0],struct.unpack(endian+'f',file.data.read(4))[0]))
		file.data.read(4)
		file.bboxtable.append((ivec1,ivec2))
		part_id=struct.unpack(endian+'i',file.data.read(4))[0]
		render_line=struct.unpack(endian+'i',file.data.read(4))[0]
		file.mat_assign_table.append((part_id,render_line,file.group_count))
		
	
	
def read_group_names(file,offset):
	file.data.seek(offset)
	file.data.read(16)
	group_name=fifa_func.read_string(file.data)
	print(group_name)
	file.group_names.append(group_name) 

#Create Texture Function	
def read_texture(file,offset,endian,path):
	
	
	file.data.seek(offset)
	overall_size=struct.unpack(endian+'i',file.data.read(4))[0]
	file.data.read(1)
	identifier=struct.unpack(endian+'B',file.data.read(1))[0]
	file.data.read(2)
	width=struct.unpack(endian+'h',file.data.read(2))[0]
	height=struct.unpack(endian+'h',file.data.read(2))[0]
	file.data.read(2)
	mipmaps=struct.unpack(endian+'h',file.data.read(2))[0]
	file.data.read(8)
	size=struct.unpack(endian+'i',file.data.read(4))[0]
	file.data.read(4)
	
	if identifier==0:
		data=fifa_func.read_dds_header(0)
		data[87]=49
		string='DXT1'
	elif identifier==1:
		data=fifa_func.read_dds_header(0)
		data[87]=51
		string='DXT3'
	elif identifier==2:
		data=fifa_func.read_dds_header(144)
		data[87]=53
		string='DXT5'
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
	#log.write('Writing File: ' +path+'texture_'+str(file.texture_count)+'.dds'+' From File Offset '+str(offset)+ ' Of Type:'+string)
	#log.write('\n')
	
	tf=open('fifa_tools\\'+'texture_'+str(file.texture_count)+'.dds','wb')
	[tf.write(b) for b in [struct.pack('<B',x) for x in data]]
	
	for i in range(mipmaps):
		tf.write(file.data.read(size))
		file.data.read(8)
		size=struct.unpack(endian+'i',file.data.read(4))[0]
		file.data.read(4)
		
	
	
	#print(data)
	#log.close()
	tf.close()
	

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
	
	
	if name.split(sep='_')[0]=='head':
		object=bpy.data.objects.new(name+'_'+str(id)+'_'+str(count)+'_'+subname.split(sep='_')[0],mesh)
	else:
		object=bpy.data.objects.new(name+'_'+str(id)+'_'+str(count),mesh)
	
	object.location=(0,0,0)
	
	#Transformation attributes inherited from bounding boxes
	if not name=='stadium': 
		#object.scale=Vector((0.1,0.1,0.1))
		object.rotation_euler=Euler((1.570796251296997, -0.0, 0.0), 'XYZ')
	bpy.context.scene.objects.link(object)
	
	return object.name




#IDENTIFY THE FILE
def file_ident(data):
	print('FILE IDENTIFICATION IN PROGRESS')
	offsets=[]
	name=str(data.read(3))[2:-1]
	endian=str(data.read(1))[2:-1]
	if endian=='b':
		endian='>'
		endianstr='Big Endian'
	elif endian=='l':
		endian='<'  
		endianstr='Little Endian'
	
	data.read(4)
	filesize=struct.unpack(endian+'I',data.read(4))[0]
	sect_num=struct.unpack(endian+'I',data.read(4))[0]
	print('DESCRIPTIONS DETECTED: ',sect_num)
	
	#Populate Offset List
	for i in range(0,sect_num):
		offsets.append((struct.unpack(endian+'I',data.read(4))[0],struct.unpack(endian+'I',data.read(4))[0]))
		data.read(8)

	##OFFSET PRINTING
	#for off in offsets:
	#   print(off)
	
	mesh_count=struct.unpack(endian+'I',data.read(4))[0]
	print('MESH OBJECTS: ',mesh_count)
	
	return name,endianstr,endian,('Total File Size:',round((filesize/1024),2),'KBs'),offsets,mesh_count



def create_material(f,offset,count):
	f.data.seek(offset)
	f.data.read(4)
	tex_num=struct.unpack(f.endian+'i',f.data.read(4))[0]
	f.data.read(8)
	entry=[]
	mat_name=fifa_func.read_string(f.data)+'_'+str(count)
	
	#print(len(f.tex_names))
	for i in range(tex_num):
		texture_type=fifa_func.read_string(f.data)
		#slot=new_mat.texture_slots.add()
		tex_id=struct.unpack('<i',f.data.read(4))[0]
		texture_name=texture_type+'_'+str(tex_id)
		#print(tex_id)
		try:
			entry.append((texture_name,'fifa_tools\\'+f.tex_names[tex_id]))
		except:
			entry.append((texture_name,'fifa_tools\\texture_'+str(tex_id)))
		
	f.materials.append((mat_name,entry))
	
	return {'FINISHED'}


def read_props(file,offset,endian):
	
	file.data.seek(offset)
	file.data.read(4)
	count=struct.unpack(endian+'i',file.data.read(4))[0]
	file.data.read(8)
	
	print('READING PROPS', 'COUNT: ',count)
	
	if file.type.endswith('_texture'):
		for i in range(count):
			file.data.read(4)
			textlen=struct.unpack(endian+'i',file.data.read(4))[0]
			text=''
			for j in range(textlen):
				text=text+chr(struct.unpack(endian+'B',file.data.read(1))[0]) 
			text=text[0:-1] 
			try:
				os.rename('fifa_tools\\texture_'+str(i)+'.dds','fifa_tools\\'+text+'.dds')
				print('Renaming texture_'+str(i)+'.dds to '+text+'.dds')
			except FileExistsError:
			   print('!!!File Exists!!!')   
			
			file.tex_names.append(text+'.dds')  
	else:
		for i in range(count):
			off=struct.unpack(endian+'I',file.data.read(4))[0]
			textlen=struct.unpack(endian+'I',file.data.read(4))[0]
			text=''
			for j in range(textlen):
				text=text+chr(struct.unpack(endian+'B',file.data.read(1))[0]) 
			text=text[0:-1] 
			
				
			if off==685399266:
				file.props.append(text)
				file.prop_count+=1  
			elif off==3566041216:
				file.sub_names.append(text)
			elif off==2047566042:
				file.tex_names.append(text+'.dds')  
		
def read_prop_positions(file,offset):
	file.data.seek(offset)
	file.data.read(4)
	temp=struct.unpack('<3f',file.data.read(12))
	rot=struct.unpack('<3f',file.data.read(12))
	file.prop_positions.append((0.001*temp[0],-0.001*temp[2],0.001*temp[1]))
	file.prop_rotations.append((rot[0],rot[1],rot[2]))
  
def read_crowds(file):
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
		ha=struct.unpack('<3B',file.data.read(3))
		set1=struct.unpack('I',file.data.read(4))
		set2=struct.unpack('I',file.data.read(4))
		set3=struct.unpack('I',file.data.read(4))
		set4=struct.unpack('I',file.data.read(4))
		
		file.crowd.append((verts,zrot,c_status,c_attendance,colorrgb,color,set1,set2,set3,set4))
		
		
def read_collision(file,offset):
	file.data.seek(offset)
	file.data.read(16)
	name=fifa_func.read_string(file.data)
	file.data.read(4)
	triscount=struct.unpack('<I',file.data.read(4))[0]
	indices=[]
	verts=[]
	j=0 #COUNTER FOR INDICES
	for i in range(triscount):
		#3 VERTICES
		verts.append(struct.unpack('<3f',file.data.read(12)))
		verts.append(struct.unpack('<3f',file.data.read(12)))
		verts.append(struct.unpack('<3f',file.data.read(12)))   
		# TRIANGLE DEFINITION
		indices.append((j,j+1,j+2))
		j+=3
		
	file.collisions.append((name,verts,indices))	

class file:
	def __init__(self,path):
		
		self.path   =path
		self.data   =0
		self.offsets =[]
		self.mesh_offsets=[]
		self.indices_offsets=[]
		self.size   =''
		self.count   =0
		self.mesh_count   =0
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
		self.container_type =''
		self.endianess  =''
		self.endian=''
		self.bones=[]
		self.props=[]
		self.prop_positions=[]
		self.prop_rotations=[]
		self.prop_count=0
		self.tex_names=[]
		self.sub_names=[]
		self.group_names=[]
		self.type=''
		self.group_count=0
		self.materials=[]
		self.material_count=0
		self.mat_assign_table=[]
		self.id=0
		self.crowd=[]
		self.collisions=[]

			

def file_init(path):
	scn=bpy.context.scene
	f=file(path)
	f.id=path.split(sep='\\')[-1].split(sep='_')[1].split(sep='.')[0]
	
	print('-------------------------------------------------------------------------------')
	print('FILE INITIALIZATION')
	print('FILE PATH: ',f.path)
	print('FILE ID:',f.id)
	
	try:
		f.data=open(f.path,'rb')
		if str(f.data.read(8))[2:-1]=='chunkzip':
			
			t=open('fifa_tools\\'+f.path.split(sep='\\')[-1]+'.decompressed','wb')
			f.data.read(12)
			sec_num=struct.unpack('>I',f.data.read(4))[0]
			f.data.read(8)
			for i in range(sec_num):
				#Uniform the offset
				f.data.read(f.data.tell() % 4)
				#unified=False
				# while unified==False:
					# if hex(f.data.tell())[-1] in ['0','4','8','C']:
						# unified=True
					# else:
						# f.data.read(1)
				
				#find sec length
				sec_found=False
				while sec_found==False:
					sec_len=struct.unpack('>I',f.data.read(4))[0]
					if not sec_len==0:
						sec_found=True
				
				f.data.read(4) #Skip 00 00 00 01
				
				data=f.data.read(sec_len)  #Store part  
				t.write(zlib.decompress(data,-15))
				
			t.close()
			f.data=open(t.name,'rb')
			
		f.data.seek(8)
		original_size=struct.unpack('<I',f.data.read(4))[0]
		f_size=len(f.data.read())+12
		
		#Cloppy Checking
		if not original_size==f_size and path.split(sep='.')[-1]=='rx3' and path.split(sep='\\')[-1].split(sep='_')[0]=='stadium' and scn.game_enum=='0':
			e=open('fifa_tools\\scripts\\msg','r')
			print(e.read())
			print('                           I SEE WHAT YOU DID THERE')
			e.close()
			return 'file_clopy'
			
		else:
			f.data.seek(0)
			return(f)
	
	except IOError as e:
		return 'io_error'


def write_offsets(offset_list,data_pass,object_list,material_list,materials_dict,texture_list,group_list,prop_list,collision_list):
	#Useful variables:
	object_count=len(object_list)
	material_count=len(material_list)
	group_count=len(group_list)
	prop_count=len(prop_list)
	collision_count=len(collision_list)
	scn=bpy.context.scene
	#offset_list format: IDENTIFIER  OFFSET   SIZE	ID
	if data_pass==0:
		offset_list.append([582139446,0,0])
		for i in range(object_count):
			offset_list.append([3263271920,0,0,i])
		offset_list.append([1285267122,0,0])
		for i in range(object_count):
			offset_list.append([5798132,0,0,i])
		
		#HEAD SPECIFIC
		if scn.head_export_flag:
			for i in range(object_count):
				offset_list.append([255353250,0,0,i])
		
		for i in range(object_count):
			offset_list.append([5798561,0,0,i])
		
		#HEAD SPECIFIC
		if scn.head_export_flag:
			for i in range(object_count):
				offset_list.append([3751472158,0,0,i])
		
		for i in range(object_count):
			offset_list.append([3566041216,0,0,i])
		
		#STADIUM SPECIFICS
		if scn.stadium_export_flag:
			for i in range(prop_count):
				offset_list.append([685399266,0,0,i])
			for i in range(collision_count):
				offset_list.append([4034198449,0,0,i])
			for i in range(material_count):
				offset_list.append([123459928,0,0,i])
			for i in range(group_count):
				offset_list.append([2116321516,0,0,i])
			for i in range(group_count+1):
				offset_list.append([230948820,0,0,i])   
	elif data_pass==1:
		
		table_size=len(offset_list)
		
		for i in range(table_size):
			#Calculating Offsets
			if i==0:
				offset_list[i][1]=table_size*16+16
			else:	
				offset_list[i][1]=offset_list[i-1][1]+offset_list[i-1][2]
			
			#Calculating Sizes
			if offset_list[i][0]==582139446:
				offset_list[i][2]=16+len(object_list)*16
			elif offset_list[i][0]==1285267122:
				size=16
				for j in range(len(prop_list)):
					size+=len(prop_list[j][0])+1+8
				for j in range(len(object_list)):
					size+=len(object_list[j][0])+1+8
				for j in range(len(texture_list)):
					size+=len(texture_list[j])+1+8
				offset_list[i][2]=fifa_func.size_round(size)
			elif offset_list[i][0]==3263271920:
				#Local Variables
				id=offset_list[i][3]
				offset_list[i][2]=fifa_func.size_round(len(object_list[id][6])+1+16)
			elif offset_list[i][0]==5798132:
				#Local Variables
				id=offset_list[i][3]
				if object_list[id][1]>65535:
					ind_size=4
				else:
					ind_size=2
				offset_list[i][2]=fifa_func.size_round(object_list[id][2]*ind_size+16)
			elif offset_list[i][0]==5798561:
				#Local Variables
				id=offset_list[i][3]
				offset_list[i][2]=fifa_func.size_round(16+object_list[id][1]*object_list[id][8])
			elif offset_list[i][0]==3566041216:
				offset_list[i][2]=16
			elif offset_list[i][0]==4034198449:
				#Local Variables
				id=offset_list[i][3]
				offset_list[i][2]=fifa_func.size_round(16+len(collision_list[id][2])+1+4+collision_list[id][0]*3*12)
			elif offset_list[i][0]==685399266:
				offset_list[i][2]=32
			elif offset_list[i][0]==123459928:
				#Local Variables
				id=offset_list[i][3]
				offset_list[i][2]=materials_dict[material_list[id]][4]
			elif offset_list[i][0]==230948820:
				#Local Variables
				id=offset_list[i][3]
				try:
					offset_list[i][2]=fifa_func.size_round(16+len(group_list[id][0][5:])+5)
				except IndexError:
					offset_list[i][2]=48	
			elif offset_list[i][0]==2116321516:
				#Local Variables
				id=offset_list[i][3]
				offset_list[i][2]=fifa_func.size_round(16+4*16+32+8+group_list[id][3]*40)								
								
			
	return offset_list			  
			
			
		
		