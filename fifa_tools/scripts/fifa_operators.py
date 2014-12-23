import bpy,os,webbrowser,imp,math,sys,struct
from builtins import dir as class_dir
from mathutils import Vector,Euler,Matrix
from math import radians
from shutil import copyfile
from xml.dom import minidom

linux_path='/media/2tb/Blender/blender-2.71-windows64'

#Detect different operating system
if os.name=='nt': #windows detected
	prePath='' 
else:
	prePath=linux_path+os.sep

fifa_main_path='fifa_tools'+os.sep+'scripts'+os.sep+'fifa_main.py'
fifa_main=imp.load_source('fifa_main',prePath+fifa_main_path)
#fifa_main=imp.load_compiled('fifa_main','fifa_tools\\scripts\\fifa_main.pyc')
fifa_func_path='fifa_tools'+os.sep+'scripts'+os.sep+'fifa_functions.py'
fifa_func=imp.load_source('fifa_func',prePath+fifa_func_path)
#fifa_func=imp.load_compiled('fifa_func','fifa_tools\\scripts\\fifa_functions.pyc')
from fifa_func import general_helper as gh
from fifa_func import texture_helper as tex_gh
from fifa_main import sig

#INIT VARIABLES
f=0
e=0
ddsheader='10'
materials=[]
tex_names=[]
objectcount=0
files=[]
dir='fifa_tools\\'
dir=os.path.realpath(dir)

texture_slotType_dict={0:'diffuseTexture',
			1:'ambientTexture',
			2:'coeffMap',
			3:'normalMap',
			4:'cubicEnvMap',
			5:'incandescenceMap',
			6:'alphamask',
			7:'noiseTexture',
			8:'pitchLinesMap',
			9:'diffuseTexture'			
}

light_props=[['sShader',['fGlareSensitivityCenter','fGlareSensitivityEdge','fGlareSensitivityPower','fGlareSizeMultSpread','fGlareBloomScale','fGlareBloomSpread','fGlareBloomRate','fGlareRotationRate','fFlareMovementRate','fFlareOffsetScale','fFlareEndScale'],['fVbeamAngle','fVbeamAngleSpread','fVbeamLength','fVbeamLengthSpread']],
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
'SidelineProps',
'TournamentDressing_NoShadowCast',
'StadiumWear_NoShadowCast',
'Sky',
'Weather_NoShadowCast',
]
group_names_15=group_names+[
'CrowdNet',
'Default',
'Pitch_NoShadowCast',
'TournamentDressing',
'Exterior',
'Exterior_NoShadowCast',
'Exterior_ShadowAlpha',
'Roof_NoShadowCast',
'Roof_ShadowAlpha',
]

standard_materials = ['adboard', 'adboarddigital', 'adboarddigitalglow', 'adboarddigitalwide', 'adboardgeneric', 'adboardscrolling', 'adboardsingledigital', 'adboardsingledigitalglow', 'banneraway',
 'bannergroup', 'bannerhome', 'concrete', 'concreteshadow', 'crest', 'diffusealpha', 'diffuseopaque', 'diffusesimple', 'diffusewet', 'envmetal', 'genericad', 'glass',
 'homeprimary', 'homesecondary', 'initialshadinggroup', 'jumbotron', 'metalbare', 'metalpainted', 'pitch', 'pitchnoline', 'rubbershadow', 'sclockhalves', 'sclockminutesones',
 'sclockminutestens', 'sclockscoreawayones', 'sclockscoreawaytens', 'sclockscorehomeones', 'sclockscorehometens', 'sclocksecondsones', 'sclocksecondstens', 'sclocktimeanalog',
  'simpleglow', 'sky', 'snowplie', 'tournament']

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
		
		fifa_main.crowd_seat_align(align_vector)
		
		
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
		
		fifa_main.crowd_seat_create(self.crowd_vertical_seats,self.crowd_horizontal_seats,self.crowd_vertical_distance,self.crowd_horizontal_distance,self.crowd_gap_distance,context)
		
		return {'FINISHED'}
	
		
class assign_crowd_type(bpy.types.Operator) :
	bl_idname = "mesh.assign_crowd_type"
	bl_label = ""
	bl_description='Click to assign selected vertices to the selected crowd type'
	def invoke(self, context, event) :
		scn=bpy.context.scene
		fifa_main.crowd_groups(scn.crowd_type_enum)
		
		return{'FINISHED'}

class colour_assign(bpy.types.Operator) :
	bl_idname = "mesh.color_assign"
	bl_label = "Assign Color"
	def invoke(self, context, event) :
		scn=context.scene
		try:
			scn.vx_color=gh.hex_to_rgb(scn.vx_color_hex)
		except:
			self.report({'ERROR'},'Malformed hex color')
		return{'FINISHED'}

class get_color(bpy.types.Operator):
	bl_idname='mesh.color_get_hex'
	bl_label='Get Color'
	def invoke(self,context,event):
		scn=context.scene
		scn.vx_color_hex=gh.rgb_to_hex((scn.vx_color.r*255,scn.vx_color.g*255,scn.vx_color.b*255))
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
		
		gh.paint_faces(object,scn.vx_color,active_color_layer)
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
		
		gh.auto_paint_mesh(object,active_color_layer)
		
		return{'FINISHED'}


class visit_url(bpy.types.Operator) :
	bl_idname = "system.visit_url"
	bl_label = ""
	def invoke(self, context, event) :
		webbrowser.open(url='http://www.soccergaming.com/forums/showthread.php?p=3562558')
		return{'FINISHED'}

class visit_url_blog(bpy.types.Operator) :
	bl_idname = "system.visit_url_blog"
	bl_label = ""
	def invoke(self, context, event) :
		webbrowser.open(url='http://3dgamedevblog.com')
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
			
			f=fifa_main.fifa_rx3(path,0)
			if f.code=='io_error':
				self.report({'ERROR'},'File Error')
				return {'CANCELLED'}
			elif f.code=='file_clopy':
				self.report({'ERROR'},'Illegal File')
				return {'CANCELLED'}
			elif f.code=='corrupt_file':
				self.report({'ERROR'},'Corrupt File')
				return {'CANCELLED'}
				
			print(f)
			f.type=path.split(sep='\\')[-1].split(sep='_')[0]+'_'+'texture'
			f.file_ident()
			f.read_file_offsets(dir)
			
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
					#Use Existing Material
					new_mat=bpy.data.materials[f.type.split(sep='_')[0]+'_'+str(f.id)]
					for i in range(5):
						new_mat.texture_slots.clear(i) #Clear Texture Slots
					
				#Add Textures
				for id in range(f.texture_count):
					
					name=f.tex_names[id]
					#Empty tex_name 
					if len(name) ==0:
						print('Skipping Texture, Probably Unsupported')
						continue
					
					slot=new_mat.texture_slots.add()
					name_fixed=name.split(sep='.')[0:len(name.split(sep='.'))-1]
					name_fixed='.'.join(name_fixed)
					#print(name_fixed)
					
					if name_fixed in bpy.data.textures:
						new_tex=bpy.data.textures[name_fixed]
					else:	
						new_tex=bpy.data.textures.new(name_fixed,type='IMAGE')
						
					
					new_tex.image=bpy.data.images.load(dir+'\\'+name)
						
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
			f=fifa_main.fifa_rx3(path,0)
			if f.code=='io_error':
				self.report({'ERROR'},'File Error')
				return {'CANCELLED'}
			elif f.code=='file_clopy':
				self.report({'ERROR'},'Illegal File')
				return {'CANCELLED'}
			elif f.code=='corrupt_file':
				self.report({'ERROR'},'Corrupt File')
				return {'CANCELLED'}
			
			if f.type=='textures':
				#f.type='texture'
				#self.report({'ERROR'},'Texture detected in a Model Path')
				return {'CANCELLED'}
			#else:
			#	f.type=path.split(sep='\\')[-1].split(sep='_')[0]
			
			
			##APPEND FILE TO FILE LIST
			files.append([f,f.type])
			
			#print('FILE TYPE DETECTED: ',f.type)
			
			f.file_ident()
			f.read_file_offsets(dir)
			
			print(f.group_names)
			#print(f.sub_names)
			if scn.geometry_flag==True:
				print('PASSING MESHES TO SCENE')
				for i in range(f.mesh_count):
					sub_name=f.type+'_'+str(f.id)+'_'+str(i)
					if f.type=='head':
						sub_name+='_'+f.sub_names[i]
					obname=fifa_main.createmesh(f.vxtable[i],f.itable[i],f.uvs[i],f.type,objectcount,f.id,sub_name,f.cols[i],False,[],scn.fifa_import_loc)
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
						try:
							ob.name=f.group_names[id]  
						except IndexError:
							print('Missing Group Name')
			
				
				
				
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
						print(i[0],i[1])
						if not i[0] in bpy.data.textures:
							new_tex=bpy.data.textures.new(i[0],type='IMAGE')
							try:
								new_tex.image=bpy.data.images.load(os.path.realpath(i[1]))
							except RuntimeError:
								print('!!!Texture Not Found!!!',i[1])
								continue	
							except:
								print('allh malakia')
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
			
			
			#Stadium Objects Renaming. Should be done after material assignment
			if f.type=='stadium':
				for i in range(f.mesh_count):
					bpy.data.objects[f.type+'_'+str(f.id)+'_'+str(i)].name=str(i)+'_'+f.sub_names[i]
			
			
			
			
			#BONE IMPORTING SECTION
			if scn.bones_flag==True and len(f.bones)>0:
				for arm_id in range(len(f.bones)):
					amt=bpy.data.armatures.new('armature_'+str(f.id)+'_'+str(arm_id))
					ob = bpy.data.objects.new('armature_object_'+str(arm_id), amt)
					scn.objects.link(ob)
					bpy.context.scene.objects.active = ob
					bpy.ops.object.mode_set(mode='EDIT')
					for i in range(len(f.bones[arm_id])):
						bone = amt.edit_bones.new('mynewnewbone'+'_'+str(i))
						bone.head,bone.tail,bone.roll=f.bones[arm_id][i]
					bpy.ops.object.mode_set(mode='OBJECT')
					ob.scale=Vector((0.01,0.01,0.01))
					ob.rotation_euler[1]=1.5707972049713135
				
				
				
				
			##PROPS IMPORTING SECTION
			if scn.props_flag==True:
				print('FOUND PROPS: ',len(f.props))
				print('POSITIONS FOUND: ',len(f.prop_positions))
				
				
				for i in range(len(f.props)):
					object_name=gh.create_prop(f.props[i],f.prop_positions[i],f.prop_rotations[i])
				
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
					obname=fifa_main.createmesh(collision[1],collision[2],[],collision[0],collisioncount,f.id,'',[],False,[],scn.fifa_import_loc)
					#bpy.data.objects[obname].scale=Vector((0.01,0.01,0.01))
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
			f=fifa_main.fifa_rx3(scn.crwd_import_path,0)
			if f.__class__.__name__=='str':
				self.report({'ERROR'},'File Error')
				return {'CANCELLED'}
			
			f.type='crowd'
			print('FILE TYPE DETECTED: ',f.type)
			
			
			fifa_main.read_crowd_15(f) #READ CROWD FILE
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
			crowd_name=fifa_main.createmesh(crowd_verts,crowd_faces,[],f.type,0,f.id,'crowd',[],False,[],scn.fifa_import_loc)
			gh.crowd_col(crowd_name,crowd_col,'seat_colors') #Add the color layer
			
			
			#Getting Crowd Types
			if scn.game_enum=="2": #FIFA 15
				for i in crowd_types:
					if i[1]>=250:
						away.append(i[2][0])
						away.append(i[2][1])
						away.append(i[2][2])
						away.append(i[2][3])
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
						empty.append(i[2][0])
						empty.append(i[2][1])		
						empty.append(i[2][2])
						empty.append(i[2][3])
			else: #FIFA 13/14	
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
			bpy.data.objects[crowd_name].rotation_euler[0]=radians(90)
			
		##IMPORT LNX FILE
		if not scn.lnx_import_path=='':
			
			#INIT FILE
			f=fifa_main.fifa_rx3(scn.lnx_import_path,0)
			if f.__class__.__name__=='str':
				self.report({'ERROR'},'File Error')
				return {'CANCELLED'}
			
			
			f.type='lights'
			print('FILE TYPE DETECTED: ',f.type)
			
			xmldata=minidom.parse(f.data)
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

		
###TEXTURE EXPORT OPERATOR### WORKS FOR THE EXPORTER ONLY, WILL BE USED FOR THE OVERWRITER AS WELL
class texture_export(bpy.types.Operator):
	bl_idname='mesh.texture_export'
	bl_label='EXPORT TEXTURES'
	def invoke(self,context,event):
		scn=bpy.context.scene
		textures_list=[]
		texture_dict={}
		status=''
		
		
		if scn.stadium_export_flag or scn.trophy_export_flag: #EXPORT STADIUM/TROPHY/BALL TEXTURES
			print('EXPORTING TEXTURES IN NORMAL MODE')
			for item in bpy.data.objects:
				if (scn.stadium_export_flag and item.type=='EMPTY' and item.name[0:5]=='stad_') or (scn.trophy_export_flag and item.type=='EMPTY' and item.name in ['BALL','TROPHY']):
					for child_item in item.children:
						item_texture_dict,item_textures_list,status=tex_gh.get_textures_list(child_item)
						texture_dict.update(item_texture_dict)
						textures_list+=item_textures_list
						if status=='material_missing':
							self.report({'ERROR'},'Missing Material')
							return {'CANCELLED'}
			
			if scn.trophy_export_flag: type='trophy-ball_' #fix file naming for trophy or ball
			if scn.stadium_export_flag: type='stadium'
			
			#Convert Textures to DDS
			status=fifa_main.write_textures_to_file(textures_list,type,scn.file_id)
			if status=='missing_texture_file':
				self.report({'ERROR'},'Missing '+status.split(sep=',')[1]+' Texture File')
				return {'CANCELLED'}
			elif status=='success':
				self.report({'INFO'},'Textures exported Successfully')
				
		
		if scn.gen_overwriter_flag:
			print('EXPORTING TEXTURES IN OVERWRITING MODE')
			name=scn.model_import_path.split(sep='\\')[-1].split(sep='.')[0]
			id=name.split(sep='_')[1]
			type=name.split(sep='_')[0]
			
			try:
				object=bpy.data.objects[type+'_'+str(id)+'_0'] #query the first model of the file
			except KeyError:
				self.report({'ERROR'},'Missing Appropriate Object. Check the naming.')
			
			texture_dict,textures_list,status=fifa_main.get_textures_list(object)
			if status=='material_missing':
				self.report({'ERROR'},'Missing Material')
				return {'CANCELLED'}
				
			#Convert Textures to DDS
			status=fifa_main.write_textures_to_file(textures_list,type,id)
			if status=='missing_texture_file':
				self.report({'ERROR'},'Missing '+status.split(sep=',')[1]+' Texture File')
				return {'CANCELLED'}
			elif status=='success':
				self.report({'INFO'},'Textures exported Successfully')	
		
		if scn.face_edit_flag:
			
			
			print('EXPORTING TEXTURES IN FACE EDITING MODE')
			parts=[]
			if scn.face_edit_head_flag:
				try:
					name=scn.model_import_path.split(sep='\\')[-1].split(sep='.')[0]
					id=name.split(sep='_')[1]
					type=name.split(sep='_')[0]
					head_found=False
					eyes_found=False
				except:
					self.report({'ERROR'},'Please select the original head file in the Main Model Path')
					return {'CANCELLED'}
				
				#EXPORT FACE TEXTURES
				try:
					object=bpy.data.objects[type+'_'+str(id)+'_0_'+'head'] #try with first mesh
					head_found=True
				except KeyError:
					try:
						object=bpy.data.objects[type+'_'+str(id)+'_1_'+'head'] #try with second mesh
						head_found=True
					except KeyError:
						self.report({'ERROR'},'Head Part not found')
						#return {'CANCELLED'}
				
				if head_found:
					#COMMON PROCEDURE
					texture_dict,textures_list,status=tex_gh.get_textures_list(object)
					if status=='material_missing': #check for missing material
						self.report({'ERROR'},'Missing Face Material')
						return {'CANCELLED'}
					
					type='face' #override correct texture file type
					#Convert Textures to DDS
					status=fifa_main.write_textures_to_file(textures_list,type,id)
					if status=='missing_texture_file':
						self.report({'ERROR'},'Missing '+status.split(sep=',')[1]+' Texture File')
						return {'CANCELLED'}
					elif status=='success':
						self.report({'INFO'},'Textures exported Successfully')
				
				
				#EXPORT EYE TEXTURES
				type=name.split(sep='_')[0]
				try:
					object=bpy.data.objects[type+'_'+str(id)+'_0_'+'eyes'] #try with first mesh
					eyes_found=True
				except KeyError:
					try:
						object=bpy.data.objects[type+'_'+str(id)+'_1_'+'eyes'] #try with second mesh
						eyes_found=True
					except KeyError:
						self.report({'ERROR'},'Eyes Part not found')
						#return {'CANCELLED'}
				
				if eyes_found:
					#COMMON PROCEDURE
					texture_dict,textures_list,status=tex_gh.get_textures_list(object)
					if status=='material_missing': #check for missing material
						self.report({'ERROR'},'Missing Eyes Material')
						return {'CANCELLED'}
					
					type='eyes' #override correct texture file type
					#Convert Textures to DDS
					status=fifa_main.write_textures_to_file(textures_list,type,id)
					if status=='missing_texture_file':
						self.report({'ERROR'},'Missing '+status.split(sep=',')[1]+' Texture File')
						return {'CANCELLED'}
					elif status=='success':
						self.report({'INFO'},'Textures exported Successfully')
				
			if scn.face_edit_hair_flag:
				try:
					name=scn.hair_import_path.split(sep='\\')[-1].split(sep='.')[0]
					id=name.split(sep='_')[1]
					type=name.split(sep='_')[0]
				except:
					self.report({'ERROR'},'Please select the original hair file in the Main Model Path')
					return {'CANCELLED'}	
				
				#EXPORT HAIR TEXTURES
				try:
					object=bpy.data.objects[type+'_'+str(id)+'_0'] #try with first mesh
				except KeyError:
					self.report({'ERROR'},'Hair Part not found')
					return {'CANCELLED'}
					
				texture_dict,textures_list,status=tex_gh.get_textures_list(object)
				if status=='material_missing': #check for missing material
					self.report({'ERROR'},'Missing Material')
					return {'CANCELLED'}
				
				#Convert Textures to DDS
				status=fifa_main.write_textures_to_file(textures_list,type,id)
				if status=='missing_texture_file':
					self.report({'ERROR'},'Missing '+status.split(sep=',')[1]+' Texture File')
					return {'CANCELLED'}
				elif status=='success':
					self.report({'INFO'},'Textures exported Successfully')
		return {'FINISHED'}

class fifa_3d_model():
	def __init__(self):
		self.diffuseId=0
		self.name=''
		
		self.colorList=[]
		self.boundBox= ()
		self.meshDescr=''
		self.meshDescrShort=''
		self.chunkLength=0
		
		self.vertsCount=0
		self.verts=[]
		self.uvLayerCount=0
		self.uvs=[]
		self.indicesCount=0
		self.indices=[]
		self.colors=[]
		self.normals=[]
		
		self.material=0
		
###EXPORTER OPERATOR###		
class test_file_export(bpy.types.Operator) :
	bl_idname = "mesh.test_fifa_export"
	bl_label = "EXPORT"
	def invoke(self, context, event) :
		scn=bpy.context.scene
		print('Test Exporter')
		#offset_list=[]
		#object_list=[]
		#collision_list=[]
		#material_list=[]
		#textures_list=[]
		#group_list=[]
		#prop_list=[]
		#material_dict={}
		
		#Calling Writing to file Functions
		if scn.stadium_export_flag:	
			f=fifa_main.fifa_rx3(scn.export_path+'stadium_'+str(scn.file_id)+'.rx3',1)
		elif scn.trophy_export_flag:	
			f=fifa_main.fifa_rx3(scn.export_path+'trophy-ball_'+str(scn.file_id)+'.rx3',1)
		
		for item in bpy.data.objects:
			#stadium props handling
			if scn.stadium_export_flag and item.type=='EMPTY' and item.name=='PROPS':
				rot_x_mat=Matrix.Rotation(radians(-90),4,'X')
				scale_mat=Matrix.Scale(10000,4)
				for child_item in item.children:
					co=rot_x_mat*scale_mat*child_item.location
					rot=(child_item.rotation_euler[0],child_item.rotation_euler[2],child_item.rotation_euler[1])
					rot=(round(rot[0]+radians(90)),round(rot[1]-radians(180)),round(rot[2]))
					
					
					f.prop_list.append((child_item.name,(co[0],co[1],co[2]),rot))
			#geometry objects handling (stadiums & balls & trophies)
			if item.type=='EMPTY' and (item.name[0:5]=='stad_' or item.name=='TROPHY' or item.name=='BALL'):
				#Skip if empty
				print(item.name)
				if len(item.children)==0:
					continue
				
				if scn.stadium_export_flag:
					#Populate Group List
					if len(f.group_list)==0:
						group_object_offset=0
					else:
						group_object_offset=f.group_list[-1][4]+f.group_list[-1][3]
					
					f.group_list.append([item.name,[0,0,0],[0,0,0],len(item.children),group_object_offset])
					#Get Group Bounding Box Values
					
					f.group_list[-1][1],f.group_list[-1][2]=gh.object_bbox(item)
				
				
				print('Group Found: '+str(item.name))
				for child_item in item.children:
					#Initialize Entry for object information storage
					entry=fifa_3d_model()
					
					entry.diffuseId=0
					#Store Name
					#entry.append(child_item.name) #0
					entry.name=child_item.name
					#Get Object Data
					#entry_collist,entry_boundbox,entry_mesh_descr,entry_mesh_descr_short,entry_chunk_length=fifa_main.convert_mesh_init(child_item,0)
					entry.colorList,entry.boundBox,entry.meshDescr,entry.meshDescrShort,entry.chunkLength=fifa_main.convert_mesh_init(child_item,0)
					
					#entry_vert_length,entry_verts_table,entry_uvlen,entry_uvs_table,entry_ind_length,entry_indices_table,entry_cols,entry_norms=fifa_main.convert_mesh_init(child_item,1)
					entry.vertsCount,entry.verts,entry.uvLayerCount,entry.uvs,entry.indicesCount,entry.indices,entry.colors,entry.normals=fifa_main.convert_mesh_init(child_item,1)
					
					#Append Data to Entry
					#entry.append(entry_vert_length) #1
					#entry.append(entry_ind_length) #2
					#entry.append(entry_uvlen) #3
					#entry.append(entry_cols) #4
					#entry.append(entry_boundbox) #5
					#entry.append(entry_mesh_descr) #6
					#entry.append(entry_mesh_descr_short) #7
					#entry.append(entry_chunk_length) #8
					#entry.append(entry_verts_table) #9
					#entry.append(entry_uvs_table) #10
					#entry.append(entry_indices_table) #11
					
				
					if scn.stadium_export_flag:	
						#Material and Texture Storing
						try:
							mat_name=child_item.material_slots[0].name
							if not mat_name in f.material_dict:
								
								#Convert material name
								#Exceptions
								materialType=mat_name.split(sep='_')[0]
								if materialType in standard_materials:
									local_mat_name = materialType
								#check alpha or opaque
								else:
									if bpy.data.materials[mat_name].use_transparency:
										local_mat_name='diffusealpha'
									else:
										local_mat_name='diffuseopaque'
								
								local_texture_list=[]
								local_texture_name_list=[]
								textureCount=0
								#Store 3 first textures Texture Slot Names
								#Matchup Textures with the FIFA Slot Type dictionary.
								for i in range(10): # 9 slots for textures
									try:
										local_texture_list.append(bpy.data.materials[mat_name].texture_slots[i].name)
										local_texture_name_list.append(texture_slotType_dict[i])
										textureCount+=1
									except:
										print('Empty Texture Slot')
									
								print(local_texture_name_list)
								#Calculate Material Section Size
								size=16+len(local_mat_name)+1
								for i in range(len(local_texture_name_list)):
									size+=len(local_texture_name_list[i])
									size+=5
								size=gh.size_round(size)
								
								#Material and texture Storage
								f.material_dict[mat_name]=(mat_name,local_mat_name,local_texture_list,local_texture_name_list,size)
								f.material_list.append(mat_name)
								
								for i in range(textureCount):
									if not local_texture_list[i] in f.texture_list:
										f.texture_list.append(local_texture_list[i])
								
								#Get object diffuse and ambient texture ids
								try:
									entry_diffuse=f.texture_list.index(local_texture_list[0])
									#entry_ambient=f.texture_list.index(local_texture_list[1])
									entry_material=f.material_list.index(mat_name)
								except:
									self.report({'ERROR'},'Missing Texture in '+str(child_item.name))
									return {'CANCELLED'}
								
							else:
								try:
									entry_diffuse=f.texture_list.index(f.material_dict[mat_name][2][0])
									#entry_ambient=textures_list.index(f.material_dict[mat_name][2][1])
									entry_material=f.material_list.index(mat_name)
								except:
									self.report({'ERROR'},'Missing Texture in '+str(child_item.name))
									return {'CANCELLED'}
						except IndexError:
							print('No material in object' +str(child_item.name))
						
					#FINALISE ENTRY ADDITION
					#entry.append(entry_diffuse) #12
					entry.diffuseId=entry_diffuse
					#entry.append(entry_ambient) ###
					try:
						entry.material=entry_material #13
					except:
						pass
					
					f.object_list.append(entry)
			
			#Collision Checkers (Stadiums Only)
			if scn.stadium_export_flag and item.type=='MESH' and item.name[0:14]=='stad_Collision':
				entry=[]
				collision_tris_length,collision_verts_table,collision_part_name=fifa_main.convert_mesh_collisions(item)
				entry.append(collision_tris_length)
				entry.append(collision_verts_table)
				entry.append(collision_part_name)
				f.collision_list.append(entry)
				
		
		#Adding InitianShading Group to material list
		#if scn.stadium_export_flag:
		#	material_list.insert(7,'InitialShadinggroup')
		#	material_dict['InitialShadinggroup']=('InitialShadinggroup','InitialShadinggroup',[],[],48)
		
			
		
		#Populating Offset List
		f.write_offsets(0)	 
		f.write_offsets(1)	 
		
		
		#Printing Debugging Data
		print('Overall Objects Detected:',len(f.object_list))
		print('Materials Detected:',len(f.material_list)) 
		#for i in object_list:
			#print(i[0],i[1],i[2],i[8])
			#print(i[6],i[7])  
		
		#print(material_dict)
		print(f.texture_list)
		#print(group_list)
		#print(prop_list)
		
				
		f.write_offsets_to_file()
		f.write_offset_data_to_file('fifa_tools\\')
		
		#Signature
		f.data.seek(f.offset_list[-1][1])
		f.data.seek(f.offset_list[-1][2],1)
		s=bytes(sig,'utf-8')
		f.data.write(s)
		
		f.data.close()	
		return {'FINISHED'}


###CROWD EXPORTER OPERATOR###		
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
		global e #globalize file
		scn=context.scene
		dict = {'head': 'face', 'eyes': 'eyes'}
		parts_dict={}
		
		
		#GENERAL OVERWRITING MODE
		if scn.gen_overwriter_flag:
			print('GENERAL OVERWRITING MODE PROCEDURE \n')
			name=scn.model_import_path.split(sep='\\')[-1]
			try:
				copyfile(scn.model_import_path,scn.export_path+'\\'+name)  #copy file to export directory
			except FileNotFoundError:
				self.report({'ERROR'},'File Not Found')
				return {'CANCELLED'}		
			e=fifa_main.fifa_rx3(scn.export_path+'\\'+name,0) #open copied file
			#check return codes
			if e=='io_error':
				self.report({'ERROR'},'File Error')
				return {'CANCELLED'}
			elif e=='corrupt_file':
				self.report({'ERROR'},'Corrupt File')
				return {'CANCELLED'}
			elif e=='file_clopy':
				self.report({'ERROR'},'Illegal File')
				return {'CANCELLED'}
			
			e.overwrite_geometry_data() #overwrite data
		
		#FACE EDITING MODE
		if scn.face_edit_flag:
			print('FACE EDITING MODE PROCEDURE \n')
			parts=[]
			status=0
			if scn.face_edit_head_flag and scn.model_import_path:
				parts.append(scn.model_import_path)
				status=1
			if scn.face_edit_hair_flag and scn.hair_import_path:
				parts.append(scn.hair_import_path)
				status=1
			if not status:
				self.report({'ERROR'},'Please select the original head file in the Main Model Path')
				return {'CANCELLED'}
			if scn.face_edit_hair_flag and scn.hair_import_path:	
				parts.append(scn.hair_import_path)
			progress=0
			for path in parts:
				name=path.split(sep='\\')[-1]
				try:
					t=fifa_main.fifa_rx3(path,0)
					copyfile(t.data.raw.name,scn.export_path+'\\'+name)  #copy file to export directory
				except FileNotFoundError:
					self.report({'ERROR'},'File Not Found')
					return {'CANCELLED'}
				e=fifa_main.fifa_rx3(scn.export_path+'\\'+name,0) #open copied file
				#check return codes
				if e=='io_error':
					self.report({'ERROR'},'File Error')
					return {'CANCELLED'}
				elif e=='corrupt_file':
					self.report({'ERROR'},'Corrupt File')
					return {'CANCELLED'}
				elif e=='file_clopy':
					self.report({'ERROR'},'Illegal File')
					return {'CANCELLED'}
				
				e.overwrite_geometry_data() #overwrite data
				progress+=1
				
			
			print('Total Files Modified ',progress)
		return {'FINISHED'}


###DEVELOPMENT PANEL###
class batch_importer(bpy.types.Operator):
	bl_idname="mesh.batch_import"
	bl_label="Batch Import Models"
	
	def invoke(self,context,event):
		scn=bpy.context.scene
		path=scn.batch_import_path
		
		count=0
		for fpath in os.listdir(path):
			if len(fpath.split(sep=".rx3"))>1 and (not 'textures' in fpath):
				count+=1
		
		step=float(360/count)
		print('step: ',step)
		count=0
		for fpath in os.listdir(path):
			vec=Vector((0,scn.batch_radius,0))
			if len(fpath.split(sep=".rx3"))>1 and (not 'textures' in fpath):
				eul=Euler()
				eul.rotate_axis('Z',radians(count*step))
				vec.rotate(eul)
				scn.fifa_import_loc=vec
				scn.fifa_import_loc[1] *= -1
				print('importing model')
				scn.model_import_path=path+fpath
				scn.geometry_flag=True
				bpy.ops.mesh.fifa_import('INVOKE_DEFAULT')
				count+=1
		return {'FINISHED'}
		

class rx3Unlocker(bpy.types.Operator):
	bl_idname="system.rx3_unlock"
	bl_label=".rx3 File Unlocker"

	def invoke(self,context,event):
		scn=bpy.context.scene

		if not scn.model_import_path:
			self.report({'ERROR'},'No file selected in the model import path')
			return{'CANCELLED'}

		f=open(scn.model_import_path,'rb')
		path , filename=os.path.split(scn.model_import_path)
		t=open(os.path.join(path,'temp.rx3'),"wb")
		t.write(f.read(8))
		size=struct.unpack('<I',f.read(4))[0]
		t.write(struct.pack('<I',size))
		t.write(f.read(size-0xC))
		f.close()
		os.remove(scn.model_import_path) #delete original file
		os.rename(os.path.join(path,'temp.rx3'),scn.model_import_path)
		return {'FINISHED'}



class group_add(bpy.types.Operator):
	bl_idname = "system.add_stad_groups"
	bl_label = "Add Groups"

	
	def invoke(self, context,event):
		for name in group_names_15:
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
		bcount=0
		for m in bpy.data.armatures:
			if m.users==0:
				bpy.data.armatures.remove(m)
				bcount+=1
		
		
		self.report({'INFO'},str(temp)+' Unused Meshes Removed '+str(count)+' Unused Curves Removed '+str(lcount)+' Unused Lamps Removed '+str(bcount)+' Unused Armatures Removed')	
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
			
			
			ident=obj.name.split(sep='.')[0].split(sep='_')[-1]
			
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