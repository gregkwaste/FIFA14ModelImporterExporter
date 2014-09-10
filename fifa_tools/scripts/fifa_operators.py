import bpy,os,webbrowser,imp,math
from builtins import dir as class_dir
from mathutils import Vector,Euler,Matrix
from math import radians
from shutil import copyfile
from xml.dom import minidom




fifa_main_path='fifa_tools\\scripts\\fifa_main.py'
fifa_main=imp.load_source('fifa_main',fifa_main_path)
fifa_func_path='fifa_tools\\scripts\\fifa_functions.py'
fifa_func=imp.load_source('fifa_func',fifa_func_path)


#INIT VARIABLES

f=0
e=0
ddsheader='10'
materials=[]
tex_names=[]
objectcount=0
files=[]
dir='fifa_tools\\'
sig='FIFA 3D Importer/Exporter, made by arti. v0.63. All rights reserved.'


texture_name_dict={0:'diffuseTexture',
			1:'ambientTexture',
			2:'coeffMap',
			3:'normalMap'
}

light_props=[
['sShader',['fGlareSensitivityCenter','fGlareSensitivityEdge','fGlareSensitivityPower','fGlareSizeMultSpread',
'fGlareBloomScale','fGlareBloomSpread','fGlareBloomRate','fGlareRotationRate','fFlareMovementRate','fFlareOffsetScale','fFlareEndScale'],['fVbeamAngle','fVbeamAngleSpread','fVbeamLength','fVbeamLengthSpread']],
'sTexture',
'sTechnique',
['bUseColorRamp',['vColorRamp','vColorRampTimes']],
['bUseSizeRamp',['vSizeRamp','vSizeRampTimes']],
['bUseSizeMult',['fSizeMultX','fSizeMultY']],
['bUseColorMult',['vColorMult','vColorMultSpread']],
'bStretchPerParticle',
'bUseAnimTexture',
'bUseLighting',
'bUseGlareSeed',
'vPivotShift',
'fAngularVelocityAdoption',
'fSizeMean',
'fSizeSpread',
'iEmitRate',
'bInject',
'iType',
'iDepthBuffer',
'iAlign',
'iNoFadeFar',
'iScreenSpace',
'fFadeDistance',
'fZBias',
'fTimeSpeed'
]

group_names=['Pitch',
'MainStadium',
'Alpha3_NoShadowCast',
'Alpha3',
'Alpha2',
'Roof',
'Alpha',
'MainStadium_NoShadowCast',
'AdBoard',
'AdBoard_NoShadowCast',
'EnvironmentSkirt',
'Banner_NoShadowCast',
'Jumbotron',
'SideLineProps',
'TournamentDressing_NoShadowCast',
'StadiumWear_NoShadowCast',
'Sky',
'Weather_NoShadowCast',
]




##OPERATORS
class align_crowd_faces(bpy.types.Operator) :
	bl_idname = "mesh.align_crowd_seats"
	bl_label = "Set"
	bl_description='Click to align crowd seats'
	def invoke(self, context, event) :
		scn=bpy.context.scene
		ob=bpy.context.object
		
		vec_dict={	0:Vector((0,0,0)),
				1:Vector((1,0)),
				2:Vector((0,1)),
				3:Vector((-1,0)),
				4:Vector((0,-1))
		}
		
		
		
		align_vector=vec_dict[int(scn.crowd_align_enum)]
		
		fifa_func.crowd_seat_align(align_vector)
		
		
		return{'FINISHED'}


class crowd_create_seats(bpy.types.Operator):
	bl_idname='mesh.crowd_create_seats'
	bl_label='Create Seats'
	bl_description='Click to create Crowd Seats'
	bl_options={'REGISTER','UNDO'}
	
	crowd_vertical_distance=bpy.props.FloatProperty(name='Vertical Distance',min=2,max=10)
	crowd_horizontal_distance=bpy.props.FloatProperty(name='Horizontal Distance',min=2,max=10)
	crowd_gap_distance=bpy.props.FloatProperty(name='Gap Distance',min=2,max=10)
	crowd_horizontal_seats=bpy.props.IntProperty(name='Seat Number Horizontally',min=2,max=1000)
	crowd_vertical_seats=bpy.props.IntProperty(name='Seat Number Vertically',min=1,max=50)
	
	
	@classmethod
	def poll(cls, context):
		return True
	
	
	def execute(self,context):
		
		fifa_func.crowd_seat_create(self.crowd_vertical_seats,self.crowd_horizontal_seats,self.crowd_vertical_distance,self.crowd_horizontal_distance,self.crowd_gap_distance,context)
		
		return {'FINISHED'}
	
		
class assign_crowd_type(bpy.types.Operator) :
	bl_idname = "mesh.assign_crowd_type"
	bl_label = ""
	bl_description='Click to assign selected vertices to the selected crowd type'
	def invoke(self, context, event) :
		scn=bpy.context.scene
		fifa_func.crowd_groups(scn.crowd_type_enum)
		
		return{'FINISHED'}
				


class colour_assign(bpy.types.Operator) :
	bl_idname = "mesh.color_assign"
	bl_label = "Assign Color"
	def invoke(self, context, event) :
		scn=context.scene
		try:
			scn.vx_color=fifa_func.hex_to_rgb(scn.vx_color_hex)
		except:
			self.report({'ERROR'},'Malformed hex color')
		return{'FINISHED'}

class get_color(bpy.types.Operator):
	bl_idname='mesh.color_get_hex'
	bl_label='Get Color'
	def invoke(self,context,event):
		scn=context.scene
		scn.vx_color_hex=fifa_func.rgb_to_hex((scn.vx_color.r*255,scn.vx_color.g*255,scn.vx_color.b*255))
		return{'FINISHED'}

class assign_color_to_map(bpy.types.Operator):
	bl_idname='mesh.paint_faces'
	bl_label='Paint Faces'
	def invoke(self,context,event):
		scn=context.scene
		object=context.object
		try:
			active_color_layer=object.data.vertex_colors.active.name
		except:
			self.report({'ERROR'},'No active color layer')
			return{'CANCELLED'}
		
		fifa_func.paint_faces(object,scn.vx_color,active_color_layer.name)
		return{'FINISHED'}

class auto_paint(bpy.types.Operator):
	bl_idname='mesh.auto_paint_mesh'
	bl_label='Auto Mesh Paint'
	def invoke(self,context,event):
		scn=context.scene
		object=context.object
		try:
			active_color_layer=object.data.vertex_colors.active.name
		except:
			self.report({'ERROR'},'No active color layer')
			return{'CANCELLED'}
		
		#Context Mode Check
		if context.mode=='EDIT_MESH':
			self.report({'ERROR'},'Should be in Object Mode')
			return{'CANCELLED'}
		
		fifa_func.auto_paint_mesh(object,active_color_layer)
		
		return{'FINISHED'}
class visit_url(bpy.types.Operator) :
	bl_idname = "system.visit_url"
	bl_label = ""
	def invoke(self, context, event) :
		webbrowser.open(url='http://www.soccergaming.com/forums/showthread.php?p=3562558')
		return{'FINISHED'}

class lights_export(bpy.types.Operator):
	bl_idname='mesh.lights_export'
	bl_label='EXPORT LIGHTS'
	
	def invoke(self,context,event):
		object=context.object
		scn=context.scene
		
		#lists for rx3
		textures_list=[]
		offset_list=[]
		
		
		xmlstring=''
		indent=0
		rot_x_mat=Matrix.Rotation(radians(-90),4,'X')
		scale_mat=Matrix.Scale(1000,4)
		
		
		#START PASSING DATA
		xmlstring+='<particleSystem>'+'\n'
		indent+=1
		xmlstring+='    '
		
		xmlstring+='<particleEffect name='+chr(34)+'glares_'+str(scn.file_id)+'_'+scn.stadium_time+chr(34)+'>\n'
		indent+=1
		xmlstring+=indent*'\t'
		
		xmlstring+=fifa_func.write_xml_param('iCullBehavior',0,0)
		
		for ob in scn.objects:
			if ob.name[0:7]=='LIGHTS_':
				textures_list.append([ob.actionrender_props.sTexture.split(sep='.dds')[0]+'.Raster',ob.actionrender_props.sTexture.split(sep='.')[0]+'.Raster.dds',False,0,0,0,0,'',128])
				
				
				
				xmlstring+=indent*'\t'
				xmlstring+='<particleGroup name='+chr(34)+ob.name[7:]+chr(34)+'>\n'
				
				indent+=1
				
				xmlstring+=indent*'\t'
				xmlstring+=fifa_func.write_xml_param('iNumParticlesMax',0,len(ob.children))
				
				
				#EMITBOX PART	
				
				xmlstring+=indent*'\t'
				xmlstring+='<particleAction name='+chr(34)+'ParticleActionEmitBox'+chr(34)+' className='+chr(34)+'ParticleActionEmitBox'+chr(34)+'>\n'
				indent+=1
				
				
							
				for attr in class_dir(ob.emitbox_props):
					
					if attr in light_props:
						xmlstring+=indent*'\t'
						xmlstring+=fifa_func.write_xml_param(attr,0,getattr(ob.emitbox_props,attr))
						
				
				
				
				
				for i in range(len(ob.children)):
					child=ob.children[i]
					if child.type=='LAMP':
						co=child.location
						co=scale_mat*rot_x_mat*co
						xmlstring+=indent*'\t'
						xmlstring+=fifa_func.write_xml_param('vCenter',i,(round(co[0],5),round(co[1],5),round(co[2],5)))
						
				indent-=1
				xmlstring+=indent*'\t'
				xmlstring+='</particleAction>\n'
				
				
				#ACTIONRENDER PART
				
				
				xmlstring+=indent*'\t'
				xmlstring+='<particleAction name='+chr(34)+'ParticleActionRender'+chr(34)+' className='+chr(34)+'ParticleActionRender'+chr(34)+'>\n'
				
				indent+=1
				
				for entry in light_props:
					cl_name=entry.__class__.__name__
					if cl_name=='str':
						try:
							param=fifa_func.write_xml_param(entry,0,getattr(ob.actionrender_props,entry))
							xmlstring+=indent*'\t'
							xmlstring+=param
						except:
							print('Not an ActionRender Property, skipping...')
							
					elif cl_name=='list':
						if entry[0]=='sShader':
							xmlstring+=indent*'\t'
							xmlstring+=fifa_func.write_xml_param(entry[0],0,getattr(ob.actionrender_props,entry[0]))
							val=getattr(ob.actionrender_props,entry[0])
							if val=='lynxVbeam.fx':
								sect=2
							else:
								sect=1	
							
							for subprop in entry[sect]:
								xmlstring+=indent*'\t'
								xmlstring+=fifa_func.write_xml_param(subprop,0,getattr(ob.actionrender_props,subprop))
						else:
							try:
								for subprop in entry[1]:
									xmlstring+=indent*'\t'
									xmlstring+=fifa_func.write_xml_param(subprop,0,getattr(ob.actionrender_props,subprop))
							except:
								print('Not an ActionRender Property, skipping...')
						
				indent-=1
				xmlstring+=indent*'\t'
				xmlstring+='</particleAction>\n'
				
				indent-=1
				xmlstring+=indent*'\t'
				xmlstring+='</particleGroup>\n'
				
		indent-=1
		xmlstring+='    '
		xmlstring+='</particleEffect>\n'
		
		indent-=1
		xmlstring+=indent*'\t'
		xmlstring+='</particleSystem>\n'
		
		
		print('WRITING LNX FILE')		
		f=open(scn.export_path+'glares_'+str(scn.file_id)+'_'+scn.stadium_time+'.lnx','w')
		f.write(xmlstring)
		f.close()
		
		print('WRITING RX3 FILE')		
		
		
		offset_list,textures_list=fifa_func.read_converted_textures(offset_list,textures_list,'fifa_tools\\light_textures\\')
		
		#Calling Writing to file Functions
		f=open(scn.export_path+'glares_'+str(scn.file_id)+'_'+scn.stadium_time+'.rx3','wb')
		
		fifa_func.write_offsets_to_file(f,offset_list)
		fifa_func.write_offset_data_to_file(f,'fifa_tools\\light_textures\\',offset_list,[],[],[],textures_list,[],[],[])
		
		#Signature
		f.seek(offset_list[-1][1])
		f.seek(offset_list[-1][2],1)
		s=bytes(sig,'utf-8')
		f.write(s)
		
		f.close()	
		
		
		
		print(offset_list)
		
		self.report({'INFO'},'Lights Exported Successfully.')
		return{'FINISHED'}		
		
		

###IMPORT FILES OPERATOR###
class file_import(bpy.types.Operator) :
	bl_idname = "mesh.fifa_import"
	bl_label = "IMPORT"
	
	def invoke(self, context, event) :
		global f,objectcount,dir,files,tex_names,props
		scn=context.scene
		paths=[]
		paths.append(scn.model_import_path)
		paths.append(scn.hair_import_path)
		
		tex_paths=[]
		tex_paths.append(scn.stadium_texture_import_path)
		tex_paths.append(scn.face_texture_import_path)
		tex_paths.append(scn.hair_texture_import_path)
		tex_paths.append(scn.eyes_texture_import_path)
		
		
		###TEXTURE FILES HANDLING###
		
		for path in tex_paths:
			if path=='':
				continue
			elif not path.split(sep='_')[-1].split(sep='.')[0]=='textures':
				self.report({'ERROR'},'No valid file selected as a texture file')
				return {'CANCELLED'}
			
			f=fifa_main.file_init(path)
			if f=='io_error':
				self.report({'ERROR'},'File Error')
				return {'CANCELLED'}
							
			
			f.type=path.split(sep='\\')[-1].split(sep='_')[0]+'_'+'texture'
			print('File type Detected: ',f.type)
			fifa_main.file_ident(f)
			fifa_main.read_file_offsets(f,dir)
			
			##Reading is enough for Stadium Textures
			if f.type=='stadium_texture':
				continue
			
			
			if scn.create_materials_flag==True:
				if not f.type.split(sep='_')[0]+'_'+str(f.id) in bpy.data.materials:
					#Create Material
					new_mat=bpy.data.materials.new(f.type.split(sep='_')[0]+'_'+str(f.id))
					new_mat.specular_intensity=0
					new_mat.use_shadeless=True
					new_mat.use_transparency=True
					new_mat.alpha=0
					new_mat.specular_alpha=0	
				else:	
					new_mat=bpy.data.materials[f.type.split(sep='_')[0]+'_'+str(f.id)]
					#Clear Texture Slots
					for i in range(5):
						new_mat.texture_slots.clear(i)
					#Add new Ones	
							
				for name in f.tex_names:
					slot=new_mat.texture_slots.add()
					if name in bpy.data.textures:
						new_tex=bpy.data.textures[name]
					else:	
						new_tex=bpy.data.textures.new(name,type='IMAGE')
						new_tex.image=bpy.data.images.load(dir+name)
					
					slot.texture=new_tex
					slot.texture_coords='UV'
					slot.uv_layer='map0'
					slot.blend_type='MIX'
					slot.use_map_color_diffuse=True
					slot.use_map_alpha=True
					slot.alpha_factor=1
					
		###MODEL FILES HANDLING###
		
		for path in paths:
			if not scn.obj_path=='':
				break
			if path=='':
				continue
			
			#INIT FILE
			f=fifa_main.file_init(path)
			if f=='io_error':
				self.report({'ERROR'},'File Error')
				return {'CANCELLED'}
			elif f=='file_clopy':
				self.report({'ERROR'},'Illegal File')
				return {'CANCELLED'}
			
			
			if path.split(sep='_')[-1].split(sep='.')[0]=='textures':
				f.type='texture'
				self.report({'ERROR'},'Texture detected in a Model Path')
				return {'CANCELLED'}
			else:
				f.type=path.split(sep='\\')[-1].split(sep='_')[0]
			
			
			##APPEND FILE TO FILE LIST
			files.append([f,f.type])
			
			print('FILE TYPE DETECTED: ',f.type)
			
			fifa_main.file_ident(f)
			fifa_main.read_file_offsets(f,dir)
			
			#print(f.group_names)
			
			if scn.geometry_flag==True:
				print('PASSING MESHES TO SCENE')
				for i in range(f.mesh_count):
					try:
						sub_name=f.sub_names[i]
					except:
						sub_name='part'+str(i)
					obname=fifa_main.createmesh(f.vxtable[i],f.itable[i],f.uvs[i],f.type,objectcount,f.id,sub_name,f.cols[i],False,[])
					objectcount+=1
					#Create Vertex Groups Based on BONES
					if scn.bone_groups_flag:
						groups={}
						for j in range(len(f.v_bones_i[i])):
							for k in f.v_bones_i[i][j]:
								if not k in groups:
									groups[k]=[]
								else:
									if j in groups[k]:
										continue
									else:
										groups[k].append(j)
						#print(groups)
						for j in groups:
							if not str(j) in bpy.data.objects[obname].vertex_groups:
								bpy.data.objects[obname].vertex_groups.new(str(j))
							bpy.data.objects[obname].vertex_groups[str(j)].add(groups[j],1,'ADD')	
						
					##GROUP PARENTING
				for i in f.mat_assign_table:
					bpy.data.objects[str(f.type)+'_'+str(f.id)+'_'+str(i[0])].parent=bpy.data.objects['group_'+str(i[2])]
					#bpy.data.objects['group_'+str(i[2])].hide=True
					#print(i[1])
				
				#GROUP RENAMING
				for ob in scn.objects:
					if ob.name.split(sep='_')[0]=='group':
						id=int(ob.name.split(sep='_')[1])
						ob.name=f.group_names[id]  
						
			#print(f.materials)
			#print(f.mat_assign_table) 
			#print(f.sub_names)
			#print(len(f.materials))
			#print(f.group_names)
				
			
			###STADIUM MATERIAL IMPORTING
			if scn.materials_flag==True:
				for index in range(len(f.materials)):
					new_mat=bpy.data.materials.new(f.materials[index][0])
					new_mat.use_shadeless=True
					new_mat.specular_intensity=0
					new_mat.use_transparency=True
					new_mat.alpha=0
					new_mat.specular_alpha=0  
					
					for i in f.materials[index][1]:
						slot=new_mat.texture_slots.add()
						#print(i[0],i[1])
						if not i[0] in bpy.data.textures:
							new_tex=bpy.data.textures.new(i[0],type='IMAGE')
							try:
								new_tex.image=bpy.data.images.load(i[1])
							except RuntimeError:
								print('!!!Texture Not Found!!!')
								continue	
							slot.texture=new_tex
						else:
							slot.texture=bpy.data.textures[i[0]]
						
						slot.texture_coords='UV'
						slot.use_map_color_diffuse=True
						slot.use_map_alpha=True
						slot.alpha_factor=1
						
						if i[0].split(sep='_')[0]=='ambientTexture':
							slot.uv_layer='map1'
							slot.blend_type='MULTIPLY'
						else:
							slot.uv_layer='map0'		
							slot.blend_type='MIX'
							
				for i in f.mat_assign_table:
					try:
						#print(f.materials[i[1]][0])
						bpy.data.objects['stadium_'+str(f.id)+'_'+str(i[0])].data.materials.append(bpy.data.materials[f.materials[i[1]][0]])
					except IndexError:
						print('Index Not In Range')
			
			
				
			#BONE IMPORTING SECTION
			if scn.bones_flag==True and len(f.bones)>0:
				ivect=Vector((0,0,1,1))
				count=0
				#testmat=Matrix(((0,1,0,0),(-1,0,0,0),(0,0,1,0),(0,0,0,1)))
				for i in range(len(f.bones)):
					verts=[]
					for j in range(3,len(f.bones[i])):
						#print(matrix)
						temp=f.bones[i][j]*f.bones[i][2]*f.bones[i][1]*f.bones[i][0]
						#print(temp)
						temp=temp*ivect
						verts.append((temp[0],temp[1],temp[2]))
					#print(verts)
					fifa_main.createmesh(verts,[],[],'bones',count,f.id,'',[],False,[])
					count+=1
			
			##PROPS IMPORTING SECTION
			if scn.props_flag==True:
				print('FOUND PROPS: ',len(f.props))
				print('POSITIONS FOUND: ',len(f.prop_positions))
				
				
				for i in range(len(f.props)):
					object_name=fifa_func.create_prop(f.props[i],f.prop_positions[i],f.prop_rotations[i])
				
					if not 'PROPS' in bpy.data.objects:
						bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0,0,0))
						bpy.data.objects['Empty'].name='PROPS'
						bpy.data.objects[object_name].parent=bpy.data.objects['PROPS']
					else:
						
						bpy.data.objects[object_name].parent=bpy.data.objects['PROPS']
						
							
			f.data.close()	
			objectcount=0	
		
			#IMPORT COLLISIONS
			if scn.collision_flag==True:
				collisioncount=0
				for collision in f.collisions:
					obname=fifa_main.createmesh(collision[1],collision[2],[],collision[0],collisioncount,f.id,'',[],False,[])
					bpy.data.objects[obname].scale=Vector((0.001,0.001,0.001))
					collisioncount+=1
			
			


		#IMPORT FACEGEN OBJ
		if not scn.obj_path=='':
			past_ob_list=set(bpy.data.objects)
			bpy.ops.import_scene.obj(filepath=scn.obj_path,axis_forward='-Z', axis_up='Y',use_image_search=True,split_mode='OFF',global_clamp_size=1,use_groups_as_vgroups=True)
			present_ob_list=set(bpy.data.objects)
			
			ob=list(present_ob_list-past_ob_list)[0]
			
			
			
			
			
			
			
			
			
			
			
			
			
#	try:
#		bpy.data.objects['Face'].name='head_0'	
#		bpy.data.objects['Eye'].name='head_1'	
#	except KeyError:
#		self.report({'INFO'},'Please Clean up your Scene from other Facegen Faces') 
#
		###IMPORT CROWD FILE
		if not scn.crwd_import_path=='':
			
			#INIT FILE
			f=fifa_main.file_init(scn.crwd_import_path)
			if f.__class__.__name__=='str':
				self.report({'ERROR'},'File Error')
				return {'CANCELLED'}
			
			f.type='crowd'
			print('FILE TYPE DETECTED: ',f.type)
			
			fifa_main.read_crowds(f)	
			f.data.close()
			
			
			crowd_verts=[]
			crowd_faces=[]
			crowd_col=[]
			crowd_types=[]
			core_home=[]
			casual_home=[]
			away=[]
			neutral=[]
			empty=[]
						
			###POPULATE COLOR DICTIONARY
			count=0
			clog=open('clog.txt','w')
			for i in range(len(f.crowd)):
				clog.write(str(f.crowd[i][2]))
				clog.write('\n')
				if f.crowd[i][1]==180:
					print(i,f.crowd[i][1])
				rot_mat=Matrix.Rotation(math.radians(f.crowd[i][1])+math.radians(90.0),4,Vector((0,1,0)))
				rot_mat=rot_mat.to_3x3()
				#original center
				v=Vector((f.crowd[i][0][0],f.crowd[i][0][1],f.crowd[i][0][2]))
				
				
				v1=Vector((10,10,-10))
				v2=Vector((-10,10,-10))
				v3=Vector((-10,-10,10))
				v4=Vector((10,-10,10))
				
				#apply rotation
				v1=rot_mat*v1
				v2=rot_mat*v2
				v3=rot_mat*v3
				v4=rot_mat*v4
				
				#get real positions
				v1=v1+v
				v2=v2+v
				v3=v3+v
				v4=v4+v
				
				crowd_verts.append((v1[0],v1[1],v1[2]))
				crowd_verts.append((v2[0],v2[1],v2[2]))
				crowd_verts.append((v3[0],v3[1],v3[2]))
				crowd_verts.append((v4[0],v4[1],v4[2]))
				crowd_faces.append((count,count+1,count+2,count+3))
				
				
				
				crowd_col.append(f.crowd[i][4])
				crowd_types.append((f.crowd[i][2],f.crowd[i][3],(count,count+1,count+2,count+3)))
				count+=4
				
			clog.close()
			crowd_name=fifa_main.createmesh(crowd_verts,crowd_faces,[],f.type,0,f.id,'crowd',[],False,[])
			fifa_func.crowd_col(crowd_name,crowd_col)
			
			#Getting Crowd Types
			for i in crowd_types:
				if i[1]>=250:
					empty.append(i[2][0])
					empty.append(i[2][1])
					empty.append(i[2][2])
					empty.append(i[2][3])
				elif i[0]<=10:
					core_home.append(i[2][0])
					core_home.append(i[2][1])
					core_home.append(i[2][2])
					core_home.append(i[2][3])
				elif 10<=i[0]<=130:
					casual_home.append(i[2][0])
					casual_home.append(i[2][1])
					casual_home.append(i[2][2])
					casual_home.append(i[2][3])
				elif 131<=i[0]<=180:
					neutral.append(i[2][0])
					neutral.append(i[2][1])
					neutral.append(i[2][2])
					neutral.append(i[2][3])
				elif i[0]>=181:
					away.append(i[2][0])
					away.append(i[2][1])		
					away.append(i[2][2])
					away.append(i[2][3])
							
			
			#Create and populate vertex groups
			bpy.data.objects[crowd_name].vertex_groups.new('Core Home')
			bpy.data.objects[crowd_name].vertex_groups.new('Casual Home')
			bpy.data.objects[crowd_name].vertex_groups.new('Neutral')
			bpy.data.objects[crowd_name].vertex_groups.new('Away')
			bpy.data.objects[crowd_name].vertex_groups.new('Empty')	 
			
			
			bpy.data.objects[crowd_name].vertex_groups['Core Home'].add(core_home,1,'ADD')
			bpy.data.objects[crowd_name].vertex_groups['Casual Home'].add(casual_home,1,'ADD')
			bpy.data.objects[crowd_name].vertex_groups['Neutral'].add(neutral,1,'ADD')
			bpy.data.objects[crowd_name].vertex_groups['Empty'].add(empty,1,'ADD')
			bpy.data.objects[crowd_name].vertex_groups['Away'].add(away,1,'ADD')
			
			bpy.data.objects[crowd_name].scale=Vector((0.001,0.001,0.001))
		
		##IMPORT LNX FILE
		if not scn.lnx_import_path=='':
			
			#INIT FILE
			f=fifa_main.file_init(scn.lnx_import_path)
			if f.__class__.__name__=='str':
				self.report({'ERROR'},'File Error')
				return {'CANCELLED'}
			
			f.type='lights'
			print('FILE TYPE DETECTED: ',f.type)
			
			xmldata=minidom.parse(f.path)
			f.data.close()
			
			#PARTICLE SYSTEM NODE
			system=xmldata.childNodes[0]
			effect=system.childNodes[1]
			for i in range(3,len(effect.childNodes),2):
				name=effect.childNodes[i].attributes['name'].value
				#print(name)
				particlegroup=effect.childNodes[i]
				for j in range(1,len(particlegroup.childNodes),2):
					#print(particlegroup.childNodes[j].tagName)
					if particlegroup.childNodes[j].tagName=='particleAction':
						param=particlegroup.childNodes[j]
						for k in range(1,len(param.childNodes),2):
							try:
								object=param.childNodes[k]
								#print(object.attributes['name'].value)
								if object.attributes['name'].value=='vCenter':
									index=object.attributes['index'].value
									loc=tuple(float(i)/1000 for i in object.attributes['value'].value[1:-1].split(sep=','))
									bpy.ops.object.lamp_add(type='POINT', location=loc)
									bpy.data.objects['Point'].name=name+'_'+index
							except:
								print('Skipping')	
		 
			bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0,0,0))
			bpy.data.objects['Empty'].name='LIGHTS'
			for object in bpy.data.objects:
				if object.type=='LAMP':
					object.parent=bpy.data.objects['LIGHTS']	 
					
			bpy.data.objects['LIGHTS'].rotation_euler=Euler((1.570796251296997, -0.0, 0.0), 'XYZ')
					 
						  
		return {'FINISHED'}


class texture_export(bpy.types.Operator):
	bl_idname='mesh.texture_export'
	bl_label='EXPORT TEXTURES'
	def invoke(self,context,event):
		scn=bpy.context.scene
		print('Texture Export')
		textures_list=[]
		offset_list=[]
		texture_dict={}
		
		for item in bpy.data.objects:
			if (scn.stadium_export_flag and item.type=='EMPTY' and item.name[0:5]=='stad_') or (scn.trophy_export_flag and item.type=='EMPTY' and item.name=='TROPHY'):
				for child_item in item.children:
					try:
						mat=bpy.data.materials[child_item.material_slots[0].material.name]
						for i in range(3):
							try:
								texture_name=mat.texture_slots[i].name
								texture_image=bpy.data.textures[texture_name].image.name
								texture_path=bpy.data.images[texture_image].filepath
								texture_alpha=bpy.data.images[texture_image].use_alpha
								texture_maxsize=max(bpy.data.images[texture_image].size[0],bpy.data.images[texture_image].size[1])
								
								if not texture_name in texture_dict:
									textures_list.append([texture_name,texture_path,texture_alpha,0,0,0,0,'',texture_maxsize])
									texture_dict[texture_name]=len(textures_list)
								
							except:
								print('Empty Texture Slot')
						
					except:
						self.report('Missing Material')
						return {'CANCELLED'}
						
						
		
		#Convert Textures to DDS
		
		status=fifa_func.texture_convert(self,textures_list)
		if status.split(sep=',')[0]=='texture_path_error':
			self.report({'ERROR'},'Missing '+status.split(sep=',')[1]+' Texture File')
			return {'CANCELLED'}
		
		#Read converted textures and calculate offsets
		
		offset_list,textures_list=fifa_func.read_converted_textures(offset_list,textures_list,'fifa_tools\\')
		
		
		if scn.stadium_export_flag:
			f_name='stadium_'+str(scn.file_id)+'_'+scn.stadium_version+'_textures.rx3'
		elif scn.trophy_export_flag:
			f_name='trophy_'+str(scn.file_id)+'_textures.rx3'
		
		
		#Calling Writing to file Functions
		f=open(scn.export_path+f_name,'wb')
		fifa_func.write_offsets_to_file(f,offset_list)
		fifa_func.write_offset_data_to_file(f,'fifa_tools\\',offset_list,[],[],[],textures_list,[],[],[])
		
		#Signature
		f.seek(offset_list[-1][1])
		f.seek(offset_list[-1][2],1)
		s=bytes(sig,'utf-8')
		f.write(s)
		
		f.close()	
		
		
		
		print(offset_list)
		
		return {'FINISHED'}

		

		
class test_file_export(bpy.types.Operator) :
	bl_idname = "mesh.test_fifa_export"
	bl_label = "EXPORT"
	def invoke(self, context, event) :
		scn=bpy.context.scene
		print('Test Exporter')
		offset_list=[]
		object_list=[]
		collision_list=[]
		materials_list=[]
		textures_list=[]
		group_list=[]
		prop_list=[]
		materials_dict={}
		
		
		
		for item in bpy.data.objects:
			if scn.stadium_export_flag and item.type=='EMPTY' and item.name=='PROPS':
				rot_x_mat=Matrix.Rotation(radians(-90),4,'X')
				scale_mat=Matrix.Scale(1000,4)
				for child_item in item.children:
					co=rot_x_mat*scale_mat*child_item.location
					rot=(child_item.rotation_euler[0],child_item.rotation_euler[2],child_item.rotation_euler[1])
					rot=(round(rot[0]+radians(90)),round(rot[1]-radians(180)),round(rot[2]))
					
					
					prop_list.append((child_item.name,(co[0],co[1],co[2]),rot))
			if item.type=='EMPTY' and (item.name[0:5]=='stad_' or item.name=='TROPHY'):
				#Skip if empty
				print(item.name)
				if len(item.children)==0:
					continue
				
				if scn.stadium_export_flag:
					#Populate Group List
					if len(group_list)==0:
						group_object_offset=0
					else:
						group_object_offset=group_list[-1][4]+group_list[-1][3]
					
					group_list.append([item.name,[0,0,0],[0,0,0],len(item.children),group_object_offset])
					#Get Group Bounding Box Values
					
					group_list[-1][1],group_list[-1][2]=fifa_func.group_bbox(item)
				
				
				print('Stadium Group Found: '+str(item.name))
				for child_item in item.children:
					#Initialize Entry for object information storage
					entry=[]
					entry_diffuse=0
					entry_ambient=0
					#Store Name
					entry.append(child_item.name) #0
					#Get Object Data
					entry_collist,entry_boundbox,entry_mesh_descr,entry_mesh_descr_short,entry_chunk_length=fifa_func.convert_mesh(child_item,0)
					entry_vert_length,entry_verts_table,entry_uvlen,entry_uvs_table,entry_ind_length,entry_indices_table,entry_cols=fifa_func.convert_mesh(child_item,1)
					#Append Data to Entry
					entry.append(entry_vert_length) #1
					entry.append(entry_ind_length) #2
					entry.append(entry_uvlen) #3
					entry.append(entry_cols) #4
					entry.append(entry_boundbox) #5
					entry.append(entry_mesh_descr) #6
					entry.append(entry_mesh_descr_short) #7
					entry.append(entry_chunk_length) #8
					entry.append(entry_verts_table) #9
					entry.append(entry_uvs_table) #10
					entry.append(entry_indices_table) #11
					
				
					if scn.stadium_export_flag:	
						#Material and Texture Storing
						try:
							mat_name=child_item.material_slots[0].name
							if not mat_name in materials_dict:
							
							
								#Covert material name
								#Exceptions
								if mat_name=='pitch':
									local_mat_name='pitch'
								elif mat_name=='pitchnoline':
									local_mat_name='pitchnoline'
								elif mat_name=='goalpost':
									local_mat_name='goalpost'
								elif mat_name=='sky':
									local_mat_name='sky'
								elif mat_name=='jumbotron':
									local_mat_name='jumbotron'
								elif mat_name=='adboard':
									local_mat_name='adboard'
								elif mat_name=='crest':
									local_mat_name='crest'
								elif mat_name=='adboarddigital':
									local_mat_name='adboarddigital'
								elif mat_name=='adboarddigitalglow':
									local_mat_name='adboarddigitalglow'
								elif mat_name=='adboardscrolling':
									local_mat_name='adboardscrolling'
								elif mat_name=='banneraway':
									local_mat_name='banneraway'
								elif mat_name=='bannerhome':
									local_mat_name='bannerhome'
								elif mat_name=='sclockhalves':
									local_mat_name='sclockhalves'
								elif mat_name=='sclockminutesones':
									local_mat_name='sclockminutesones'
								elif mat_name=='sclockminutestens':
									local_mat_name='sclockminutestens'
								elif mat_name=='sclocksecondones':
									local_mat_name='sclocksecondones'
								elif mat_name=='sclocksecondtens':
									local_mat_name='sclocksecondtens'
								elif mat_name=='sclockscoreawayones':
									local_mat_name='sclockscoreawayones'
								elif mat_name=='sclockscoreawaytens':
									local_mat_name='sclockscoreawaytens'
								elif mat_name=='sclockscorehomeones':
									local_mat_name='sclockscorehomeones'
								elif mat_name=='sclockscorehometens':
									local_mat_name='sclockscorehometens'
								
								#check alpha or opaque
								else:
									if bpy.data.materials[mat_name].use_transparency:
										local_mat_name='diffusealpha'
									else:
										local_mat_name='diffuseopaque'
								
								local_texture_list=[]
								text_len=0
								#Store 3 first textures
								for i in range(3):
									try:
										local_texture_list.append(bpy.data.materials[mat_name].texture_slots[i].name)
										text_len+=1
									except:
										print('Empty Texture Slot')
									
								#Matchup Textures with the texture name dictionary.
								local_texture_name_list=[]
								for i in range(text_len):
									try:
										local_texture_name_list.append(texture_name_dict[i])
									except:
										print('Empty Texture Slot')
										
								print(local_texture_name_list)
								#Calculate Material Section Size
								size=16+len(local_mat_name)+1
								for i in range(len(local_texture_name_list)):
									size+=len(local_texture_name_list[i])
									size+=5
									
								size=fifa_func.size_round(size)
								#Material and texture Storage
								materials_dict[mat_name]=(mat_name,local_mat_name,local_texture_list,local_texture_name_list,size)
								materials_list.append(mat_name)
								
								for i in range(len(local_texture_list)):
									if not local_texture_list[i] in textures_list:
										textures_list.append(local_texture_list[i])
								#Get object diffuse and ambient texture ids
								try:
									entry_diffuse=textures_list.index(local_texture_list[0])
									#entry_ambient=textures_list.index(local_texture_list[1])
									entry_material=materials_list.index(mat_name)
								except:
									self.report({'ERROR'},'Missing Texture in '+str(child_item.name))
									return {'CANCELLED'}
								
							else:
								try:
									entry_diffuse=textures_list.index(materials_dict[mat_name][2][0])
									#entry_ambient=textures_list.index(materials_dict[mat_name][2][1])
									entry_material=materials_list.index(mat_name)
								except:
									self.report({'ERROR'},'Missing Texture in '+str(child_item.name))
									return {'CANCELLED'}
						except IndexError:
							print('No material in object' +str(child_item.name))
						
					#FINALISE ENTRY ADDITION
					entry.append(entry_diffuse) #12
					#entry.append(entry_ambient) ###
					try:
						entry.append(entry_material) #13
					except:
						entry.append(0)
					
					object_list.append(entry)
			
			#Collision Checkers
			if scn.stadium_export_flag and item.type=='MESH' and item.name[0:14]=='stad_Collision':
				entry=[]
				collision_tris_length,collision_verts_table,collision_part_name=fifa_func.convert_mesh_collisions(item)
				entry.append(collision_tris_length)
				entry.append(collision_verts_table)
				entry.append(collision_part_name)
				collision_list.append(entry)
				
		
		#Adding InitianShading Group to material list
		#if scn.stadium_export_flag:
		#	materials_list.insert(7,'InitialShadinggroup')
		#	materials_dict['InitialShadinggroup']=('InitialShadinggroup','InitialShadinggroup',[],[],48)
		
			
		
		#Populating Offset List
		offset_list=fifa_main.write_offsets(offset_list,0,object_list,materials_list,materials_dict,textures_list,group_list,prop_list,collision_list)	 
		offset_list=fifa_main.write_offsets(offset_list,1,object_list,materials_list,materials_dict,textures_list,group_list,prop_list,collision_list)	 
		
		
		#Printing Debugging Data
		print('Overall Objects Detected:',len(object_list))
		print('Materials Detected:',len(materials_list)) 
		#for i in object_list:
			#print(i[0],i[1],i[2],i[8])
			#print(i[6],i[7])  
		
		#print(materials_dict)
		print(textures_list)
		#print(group_list)
		#print(prop_list)
		
		#Calling Writing to file Functions
		if scn.stadium_export_flag:	
			f=open(scn.export_path+'stadium_'+str(scn.file_id)+'.rx3','wb')
		elif scn.trophy_export_flag:	
			f=open(scn.export_path+'trophy_'+str(scn.file_id)+'.rx3','wb')
				
		
		fifa_func.write_offsets_to_file(f,offset_list)
		fifa_func.write_offset_data_to_file(f,'fifa_tools\\',offset_list,object_list,materials_list,materials_dict,textures_list,group_list,prop_list,collision_list)
		
		#Signature
		f.seek(offset_list[-1][1])
		f.seek(offset_list[-1][2],1)
		s=bytes(sig,'utf-8')
		f.write(s)
		
		f.close()	
		#materials_dict={}
				
		return {'FINISHED'}
class crowd_export(bpy.types.Operator):
	bl_idname='mesh.crowd_export'
	bl_label='EXPORT CROWD'
	def invoke(self,context,event):
		scn=bpy.context.scene
		crowd_found=False
		
		for i in bpy.data.objects:
			#print(i.name)
			if i.name=='crowd':
				ob=i
				crowd_found=True
				break
			
		if not crowd_found:
			self.report({'ERROR'},'No crowd object found, Nothing exported')
			return {'CANCELLED'}
		
		f=open(scn.export_path+'crowd_'+str(scn.file_id)+'_'+scn.stadium_version+'.dat','wb')
		fifa_func.write_crowd_file(f,ob)
		f.close()
		self.report({'INFO'},'Crowd Exported')
		return {'FINISHED'}
		
				
#VERTEX GROUP SEPARATOR
class ob_group_separator(bpy.types.Operator):
	bl_idname='mesh.ob_vertex_groups_separate'
	bl_label='SPLIT MODEL'
	def invoke(self,context,event):
		scn=bpy.context.scene
		object=context.object
		
		#bpy.ops.object.editmode_toggle()
		if context.mode=='EDIT_MESH':
			fifa_func.object_separate(object)
		else:
			self.report({'ERROR'},'Must be in Object Mode')
			
		
		return {'FINISHED'}
		

		

		
### FILE OVERWRITER ###
class file_overwrite(bpy.types.Operator) :
	bl_idname = "mesh.fifa_overwrite"
	bl_label = "OVERWRITE"
	def invoke(self, context, event) :
		global e
		scn=context.scene
		dict = {'head': 'face', 'eyes': 'eyes'}
		parts_dict={}
		
		
		if scn.hair_export_flag:
			rounds=2
		else:
			rounds=1
		
		
		for i in range(rounds):
			
			#COPY FILE
			if i==1:
				name=scn.hair_import_path.split(sep='\\')[-1]
				copyfile(scn.hair_import_path,scn.export_path+'\\'+name)
			else:
				name=scn.model_import_path.split(sep='\\')[-1]
				copyfile(scn.model_import_path,scn.export_path+'\\'+name)	
			
			#print(name.split(sep='.'))
			file_type=name.split(sep='.')[0].split(sep='_')[0]
			file_id=name.split(sep='.')[0].split(sep='_')[1]
			
			
			
			
			
			e=fifa_main.file(scn.export_path+'\\'+name)
			e.data=open(e.path,'rb+')
			
			#READ THE COPIED FILE
			e.container_type,e.endianess,e.endian,e.size,e.offsets,e.count= fifa_main.file_ident(e.data)
			fifa_main.read_file_offsets(e,dir)
			
			sub_parts=len(e.mesh_offsets)
			
			
			print('WRITING '+str(file_type).upper()+' FILE')
			
			for i in range(sub_parts):
				try:
					if file_type=='head':
						print('Trying to find: ',file_type+'_'+str(file_id)+'_'+str(i)+'_'+e.sub_names[i].split(sep='_')[0])
						object=bpy.data.objects[file_type+'_'+str(file_id)+'_'+str(i)+'_'+e.sub_names[i].split(sep='_')[0]]
						parts_dict[e.sub_names[i].split(sep='_')[0]]=[dict[e.sub_names[i].split(sep='_')[0]],i]
					else:
						print('Trying to find: ',file_type+'_'+str(file_id)+'_'+str(i))
						object=bpy.data.objects[file_type+'_'+str(file_id)+'_'+str(i)]
						parts_dict[file_type]=[file_type,i]
						
				except:
					print('Missing Part')
					continue
				
				verts=[]
				uvs=[]
				cols=[]
				indices=[]
				
				print(e.mesh_offsets)
				print(e.indices_offsets)
				
				
				
				opts=fifa_func.mesh_descr_convert(e.mesh_descrs[i])
				print(opts)
				verts,uvs,cols,indices=fifa_func.convert_original_mesh(object)
				
				print('Part Description: ',opts,'Part Vertices: ',len(verts),'Part UV maps: ',e.uvcount[i],'Part Indices: ',len(indices),'Part Color maps: ',e.colcount[i])
				
				e.data.seek(e.mesh_offsets[i][0]+16)
				
				#fifa_func.write_head_data(e.data,verts,uvs,e.mesh_offsets[head[2]][0])
				fifa_func.convert_mesh_to_bytes(e.data,opts,len(verts),verts,uvs,cols)
				
				
				e.data.seek(e.indices_offsets[i][0]+16)
				fifa_func.write_indices(e.data,indices)
				
				
			e.data.flush()
			e.data.close()	
			print(str(file_type).upper()+' EXPORT SUCCESSFULL')
			print('\n')

		self.report({'INFO'}, 'Models Exported Successfully')
		
		
		#Texture Exporting
		if scn.texture_export_flag:
			print('EXPORTING TEXTURES')
			parts=[]
			
			if scn.model_export_flag:
				parts.append('head')
				parts.append('eyes')
			
			if scn.hair_export_flag:
				parts.append('hair')
				
				
				
				
			for k in range(len(parts)):
				textures_list=[]
				texture_dict={}
				offset_list=[]
				
				if parts[k] in ['head','eyes']:
					name=scn.model_import_path.split(sep='\\')[-1]
				else:
					name=scn.hair_import_path.split(sep='\\')[-1]
				
				file_type=name.split(sep='.')[0].split(sep='_')[0]
				file_id=name.split(sep='.')[0].split(sep='_')[1]
				
				
				
				try:
					if parts[k] in ['head','eyes']:
						object=bpy.data.objects[file_type+'_'+str(file_id)+'_'+str(parts_dict[parts[k]][1])+'_'+parts[k]]
					else:
						object=bpy.data.objects[file_type+'_'+str(file_id)+'_'+str(parts_dict[parts[k]][1])]	
				

					try:
						mat=bpy.data.materials[object.material_slots[0].name]
						
						for i in range(3):
							try:
								texture_name=mat.texture_slots[i].name
								texture_image=bpy.data.textures[texture_name].image.name
								texture_path=bpy.data.images[texture_image].filepath
								texture_alpha=bpy.data.images[texture_image].use_alpha
								texture_maxsize=max(bpy.data.images[texture_image].size[0],bpy.data.images[texture_image].size[1])
								
								if not texture_name in texture_dict:
									textures_list.append([texture_name,texture_path,texture_alpha,0,0,0,0,'',texture_maxsize])
									texture_dict[texture_name]=len(textures_list)
								
							except:
								print('Empty Texture Slot')
					except:
						print('Head Material is Missing')
				except:
					print('Head Part is Missing')
							
				
				#Convert Textures to DDS
				
				status=fifa_func.texture_convert(self,textures_list)
				if status.split(sep=',')[0]=='texture_path_error':
					self.report({'ERROR'},'Missing '+status.split(sep=',')[1]+' Texture File')
					return {'CANCELLED'}
				
				#Read converted textures and calculate offsets
				
				offset_list,textures_list=fifa_func.read_converted_textures(offset_list,textures_list,'fifa_tools\\')
				
				
				#Calling Writing to file Functions
				f=open(scn.export_path+parts_dict[parts[k]][0]+'_'+str(file_id)+'_textures.rx3','wb')
				fifa_func.write_offsets_to_file(f,offset_list)
				fifa_func.write_offset_data_to_file(f,'fifa_tools\\',offset_list,[],[],[],textures_list,[],[],[])
				
				#Signature
				f.seek(offset_list[-1][1])
				f.seek(offset_list[-1][2],1)
				s=bytes(sig,'utf-8')
				f.write(s)
				
				f.close()	
				
				print(offset_list)
		
		
		
		
		return {'FINISHED'}

class group_add(bpy.types.Operator):
	bl_idname = "system.add_stad_groups"
	bl_label = "Add Groups"

	
	def invoke(self, context,event):
		for name in group_names:
			if not 'stad_'+name in bpy.data.objects:
				bpy.ops.object.empty_add(type='PLAIN_AXES',location=(0,0,0))
				ob=bpy.data.objects['Empty']
				ob.name='stad_'+name
		return {'FINISHED'}


### FIX RELATIVE PATH OPERATOR###
class fix_relative_paths(bpy.types.Operator) :
	bl_idname = "system.fix_relative_paths"
	bl_label = "Fix Settings"
	bl_description = 'Fixes Relative Path Option in User Preferences'
	def invoke(self, context, event) :
		bpy.context.user_preferences.filepaths.use_relative_paths=False
		bpy.context.scene.game_settings.material_mode='GLSL'
		return {'FINISHED'}

### DELETE ALL DDS FILES FROM TEMP DIRECTORY###
class clear_temp_directory(bpy.types.Operator) :
	bl_idname = "system.clean_temp_dir"
	bl_label = "Clean Up"
	bl_description = 'Delete all textures from fifa_tools folder'
	def invoke(self, context, event) :
		files=os.listdir('fifa_tools')
		count=0
		for f in files:
			if f.endswith('.dds') or f.endswith('.decompressed'):
				count+=1
				os.remove('fifa_tools\\'+f)
				print('Deleting '+f)
				
		
		self.report({'INFO'},str(count)+' Textures Removed')
		return {'FINISHED'}

### ADD PROP
class add_prop(bpy.types.Operator):
	bl_idname = "system.add_prop"
	bl_label = "Add Prop"
	bl_description = 'Adds Selected Prop to Curosr Location in the scene'
	def invoke(self,context,event):
		scn=context.scene
		fifa_func.create_prop(scn.prop_enum,scn.cursor_location,(0,0,0))
		return {'FINISHED'}

###REMOVE UNUSED MESHES FROM THE SCENE###
class remove_meshes(bpy.types.Operator):
	bl_idname = "mesh.remove_meshes"
	bl_label = "Remove Unused Meshes"
	bl_description = 'Remove Unused Meshes'
	def invoke(self, context, event):
		count=0
		for m in bpy.data.meshes:
			if m.users==0:
				bpy.data.meshes.remove(m)
				count+=1
		temp=count
		
		count=0
		for m in bpy.data.curves:
			if m.users==0:
				bpy.data.curves.remove(m)
				count+=1
		lcount=0
		for m in bpy.data.lamps:
			if m.users==0:
				bpy.data.lamps.remove(m)
				count+=1
		
		self.report({'INFO'},str(temp)+' Unused Meshes Removed And '+str(count)+' Unused Curves Removed '+str(lcount)+' Unused Lamps Removed')	
		return {'FINISHED'}

###CLEAN ALL THE FILE PATHS IN THE SCRIPT###
class clean_paths(bpy.types.Operator):
	bl_idname = "mesh.clean_paths"
	bl_label = "Clean Paths"
	bl_description = 'Clear all Script Paths'
	def invoke(self, context, event):
		scn=bpy.context.scene
		
		scn.model_import_path=''
		scn.hair_import_path=''
		scn.stadium_texture_import_path=''
		scn.face_texture_import_path=''
		scn.hair_texture_import_path=''
		scn.eyes_texture_import_path=''
		scn.lnx_import_path=''
		scn.crwd_import_path=''
		scn.export_path=''
		
		self.report({'INFO'},'Paths Cleared')	
		return {'FINISHED'}

class hide_props(bpy.types.Operator):
	bl_idname="mesh.hide_props"
	bl_label='Hide/Show Props'
	bl_description='Toggles Prop visibility'
	def invoke(self,context,event):
	   for object in bpy.data.objects:
		   if object.parent==bpy.data.objects['PROPS']:
			   object.hide= not object.hide
		   self.report({'INFO'},'Props View Toggled')
	   return {'FINISHED'}
	   



### ASSIGN MATERIALS TO OBJECTS###
class assign_materials(bpy.types.Operator):
	bl_idname = "mesh.assign_materials"
	bl_label = "Assign Created Materials"
	bl_description = 'Try to assign Face/Hair/Eyes Materials to Scene Objects'
	bl_options ={'UNDO'}
	def invoke(self, context, event):
		dict = {'head': 'face', 'eyes': 'eyes'}
		
		
		for obj in bpy.context.scene.objects:
			if obj.type in ['LAMP','CAMERA','EMPTY']:
				continue
			
			
			ident=obj.name.split(sep='_')[-1]
			
			if ident in dict:
				try:
					for j in obj.data.materials:
						obj.data.materials.pop(0, update_data=True)
					print(ident)
					obj.data.materials.append(bpy.data.materials[dict[ident]+'_'+obj.name.split(sep='_')[1]])
				except KeyError:
					self.report({'ERROR'},'Missing '+ident.title()+' Material')
			else:
				try:
					for j in obj.data.materials:
						obj.data.materials.pop(0, update_data=True)
					obj.data.materials.append(bpy.data.materials[obj.name.split(sep='_')[0]+'_'+obj.name.split(sep='_')[1]])
				except KeyError:
					self.report({'ERROR'},'Missing '+obj.name.split(sep='_')[0].title()+' Material')
		self.report({'INFO'},'Materials Assigned Successfully')	  
		
		return {'FINISHED'}





def register():
	bpy.utils.register_module(__name__)
	pass

def unregister():
	bpy.utils.unregister_module(__name__)
	pass

if __name__ == "__main__":
	register()