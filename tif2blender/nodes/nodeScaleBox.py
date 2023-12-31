import bpy
import numpy as np 
from .nodesBoolmultiplex import axes_demultiplexer_node_group

#initialize scalebox node group
# Arguably should be refactored to a rescaled primitive cube -> subdivide modifier -> set pos to max -> merge by distance
# Might be simpler than separate mesh grids, and have less redundancy
def scalebox_node_group():
    node_group = bpy.data.node_groups.get("_scalebox")
    if node_group:
        return node_group
    node_group= bpy.data.node_groups.new(type = 'GeometryNodeTree', name = "_scalebox")
    links = node_group.links
    interface = node_group.interface
    
    # -- get Input --
    interface.new_socket("Size (µm)",in_out="INPUT",socket_type='NodeSocketVector')
    interface.items_tree[-1].default_value = (7.0, 5.0, 4.0)
    interface.items_tree[-1].min_value = 0.0
    interface.items_tree[-1].max_value = 10000000.0
    interface.items_tree[-1].attribute_domain = 'POINT'

    interface.new_socket("Size (m)",in_out="INPUT",socket_type='NodeSocketVector')
    interface.items_tree[-1].default_value = (13.0, 10.0, 6.0)
    interface.items_tree[-1].min_value = 0.0
    interface.items_tree[-1].max_value = 10000000.0
    interface.items_tree[-1].attribute_domain = 'POINT'

    interface.new_socket("µm per tick",in_out="INPUT",socket_type='NodeSocketFloat')
    interface.items_tree[-1].default_value = 10
    interface.items_tree[-1].min_value = 0.0
    interface.items_tree[-1].max_value = 3.4028234663852886e+38
    interface.items_tree[-1].attribute_domain = 'POINT'

    interface.new_socket("Axis Selection",in_out="INPUT",socket_type='NodeSocketInt')
    interface.items_tree[-1].default_value = 1111111
    interface.items_tree[-1].min_value = 0
    interface.items_tree[-1].max_value = 1111111
    interface.items_tree[-1].attribute_domain = 'POINT'

    group_input = node_group.nodes.new("NodeGroupInput")
    group_input.location = (-800,0)
    
    #output Geometry
    interface.new_socket("Geometry",in_out="OUTPUT",socket_type='NodeSocketGeometry')
    interface.items_tree[-1].attribute_domain = 'POINT'
    group_output = node_group.nodes.new("NodeGroupOutput")
    group_output.location = (2900,0)
    
    join_geo = node_group.nodes.new("GeometryNodeJoinGeometry")
    join_geo.location = (2100,100)

    ## -- process IO --

    loc_0 =  node_group.nodes.new("ShaderNodeVectorMath")
    loc_0.operation = "MULTIPLY"
    loc_0.location = (-600, -100)
    loc_0.label = "location 0,0,0"
    links.new(group_input.outputs.get("Size (m)"), loc_0.inputs[0])
    loc_0.inputs[1].default_value = (-0.5,-0.5,0)
    
    loc_max =  node_group.nodes.new("ShaderNodeVectorMath")
    loc_max.operation = "MULTIPLY"
    loc_max.location = (-450, -100)
    loc_max.label = "location max val"
    links.new(group_input.outputs.get("Size (m)"), loc_max.inputs[0])
    loc_max.inputs[1].default_value = (0.5,0.5,1)
    
    m_per_µm =  node_group.nodes.new("ShaderNodeVectorMath")
    m_per_µm.operation = "DIVIDE"
    m_per_µm.location = (-600, -300)
    m_per_µm.label = "m per µm"
    links.new(group_input.outputs.get("Size (m)"), m_per_µm.inputs[0])
    links.new(group_input.outputs.get("Size (µm)"), m_per_µm.inputs[1])

    # -- make scale box and read out/store normals
    demultiplex_axes = node_group.nodes.new('GeometryNodeGroup')
    demultiplex_axes.node_tree = axes_demultiplexer_node_group()
    demultiplex_axes.location = (-600, -600)
    links.new(group_input.outputs.get('Axis Selection'), demultiplex_axes.inputs[0])
    
    µm_ticks_float =  node_group.nodes.new("ShaderNodeVectorMath")
    µm_ticks_float.operation = "DIVIDE"
    µm_ticks_float.location = (-600, 200)
    µm_ticks_float.label = "float-nr of ticks"
    links.new(group_input.outputs.get("Size (µm)"), µm_ticks_float.inputs[0])
    links.new(group_input.outputs.get("µm per tick"), µm_ticks_float.inputs[1])

    n_ticks_int =  node_group.nodes.new("ShaderNodeVectorMath")
    n_ticks_int.operation = "CEIL"
    n_ticks_int.location = (-450, 200)
    n_ticks_int.label = "nr of ticks"
    links.new(µm_ticks_float.outputs[0], n_ticks_int.inputs[0])
     
    ticks_offset =  node_group.nodes.new("ShaderNodeVectorMath")
    ticks_offset.operation = "ADD"
    ticks_offset.location = (-300, 200)
    ticks_offset.label = "add 0th tick"
    links.new(n_ticks_int.outputs[0], ticks_offset.inputs[0])
    ticks_offset.inputs[1].default_value = (1,1,1)
       
    µm_overshoot =  node_group.nodes.new("ShaderNodeVectorMath")
    µm_overshoot.operation = "MULTIPLY"
    µm_overshoot.location = (-450, 000)
    µm_overshoot.label = "µm full grid"
    links.new(n_ticks_int.outputs[0], µm_overshoot.inputs[0])
    links.new(group_input.outputs.get("µm per tick"), µm_overshoot.inputs[1])
   
    size_overshoot =  node_group.nodes.new("ShaderNodeVectorMath")
    size_overshoot.operation = "MULTIPLY"
    size_overshoot.location = (-300, 0)
    size_overshoot.label = "overshoot size vec"
    links.new(µm_overshoot.outputs[0], size_overshoot.inputs[0])
    links.new(m_per_µm.outputs[0], size_overshoot.inputs[1])
    
    size_overshootXYZ =  node_group.nodes.new("ShaderNodeSeparateXYZ")
    size_overshootXYZ.location = (-150, 0)
    size_overshootXYZ.label = "grid size"
    links.new(size_overshoot.outputs[0], size_overshootXYZ.inputs[0])
    
    n_ticksXYZ =  node_group.nodes.new("ShaderNodeSeparateXYZ")
    n_ticksXYZ.location = (-150, 200)
    n_ticksXYZ.label = "n ticks"
    links.new(ticks_offset.outputs[0], n_ticksXYZ.inputs[0])
    
    
    # make principal box
    finals = []
    for sideix, side in enumerate(['bottom', 'top']):
        for axix, ax in enumerate(['xy','yz','zx']):
            grid = node_group.nodes.new("GeometryNodeMeshGrid")
            grid.label = ax+"_"+side
            grid.name = ax+"_"+side+"_grid"
            
            for which, axis in enumerate("xyz"):
                if axis in ax:
                    links.new(size_overshootXYZ.outputs[which], grid.inputs[ax.find(axis)])
                    links.new(n_ticksXYZ.outputs[which], grid.inputs[ax.find(axis)+2])
                    
            
            transform = node_group.nodes.new("GeometryNodeTransform")
            links.new(grid.outputs[0], transform.inputs[0])


            if side == "top":
                pretransform = node_group.nodes.new("ShaderNodeVectorMath")
                pretransform.operation = 'MULTIPLY'
                links.new(group_input.outputs.get("Size (m)"), pretransform.inputs[0])
                links.new(pretransform.outputs[0], transform.inputs.get("Translation"))
                
                # shift tops to the correct plane (out-of-axis) and calc rotation
                shift = np.array([float(axis not in ax) for axis in "xyz"]) 
                pretransform.inputs[1].default_value = tuple(shift)
            else:
                pretransform = node_group.nodes.new("GeometryNodeFlipFaces")
                links.new(grid.outputs[0], pretransform.inputs[0])
                links.new(pretransform.outputs[0], transform.inputs[0])
            
            rot = [0,0,0]
            if ax == "yz":
                rot = [0.5,0,0.5]
            elif ax == 'zx':
                rot = [0,-0.5,-0.5]
            transform.inputs.get("Rotation").default_value = tuple(np.array(rot)*np.pi)
            
            # translocate 0,0 to be accurate for each
            bbox = node_group.nodes.new("GeometryNodeBoundBox")
            links.new(transform.outputs[0],bbox.inputs[0])
            
            find_0 = node_group.nodes.new("ShaderNodeVectorMath")
            find_0.operation = "SUBTRACT"
            links.new(loc_0.outputs[0], find_0.inputs[0])
            links.new(bbox.outputs[1], find_0.inputs[1])

            if side == "top":
                top = node_group.nodes.new("ShaderNodeVectorMath")
                top.operation = "MULTIPLY"
                links.new(bbox.outputs[1], top.inputs[0])
                links.new(top.outputs[0], find_0.inputs[1])
                top.inputs[1].default_value = tuple(np.array([float(axis in ax) for axis in "xyz"]))
            else:
                top = None
        
            set_pos = node_group.nodes.new("GeometryNodeSetPosition")
            links.new(transform.outputs[0], set_pos.inputs[0])
            links.new(find_0.outputs[0], set_pos.inputs[-1])

            notnode = node_group.nodes.new("FunctionNodeBooleanMath")
            notnode.operation = "NOT"
            links.new(demultiplex_axes.outputs[sideix*3 + axix + 1], notnode.inputs[0])

            del_ax = node_group.nodes.new("GeometryNodeDeleteGeometry")
            links.new(set_pos.outputs[0], del_ax.inputs[0])
            links.new(notnode.outputs[0], del_ax.inputs[1])
            
            for locix,node in enumerate([grid,pretransform, transform,bbox,top, 
                                        find_0, set_pos, notnode, del_ax]):
                if node:
                    nodeix = (sideix*3)+axix
                    node.location = (200*locix + 200, 300*2.5 + nodeix * -300)
            finals.append(del_ax)
    for final in reversed(finals):            
        links.new(final.outputs[0], join_geo.inputs[0])
    
    # set final nodes to right position
    
    pos =  node_group.nodes.new("GeometryNodeInputPosition")
    pos.location = (2100, -100)
    
    min_axis =  node_group.nodes.new("ShaderNodeVectorMath")
    min_axis.operation = "MINIMUM"
    min_axis.location = (2250, -100)
    links.new(pos.outputs[0], min_axis.inputs[0])
    links.new(loc_max.outputs[0], min_axis.inputs[1])
    
    
    clip_axis =  node_group.nodes.new("GeometryNodeSetPosition")
    clip_axis.location = (2500, 0)
    clip_axis.label = "clip final axis"
    links.new(join_geo.outputs[0], clip_axis.inputs[0])
    links.new(min_axis.outputs[0], clip_axis.inputs[2])

    merge = node_group.nodes.new("GeometryNodeMergeByDistance")
    links.new(clip_axis.outputs[0], merge.inputs[0])
    merge.location = (2700, 0)

    links.new(merge.outputs[0],group_output.inputs[0])

    return node_group

