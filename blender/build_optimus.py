# Optimus Prime — live-action movie mecha build (Blender 4.5, bpy)
# Parametric hard-surface model: beveled/tapered forms, layered armor,
# dark inner frame, procedural weathering. Renders a hero still for review.
import bpy, math, random
from mathutils import Vector

random.seed(11)

# ---------- scene reset ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------- materials ----------
def principled(name, base, metallic=0.0, rough=0.5, coat=0.0, coat_rough=0.25, emit=None, emit_str=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = rough
    if coat > 0:
        bsdf.inputs["Coat Weight"].default_value = coat
        bsdf.inputs["Coat Roughness"].default_value = coat_rough
    if emit is not None:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_str
    return m

def add_weathering(mat, scale=6.0, rough_lo=0.7, rough_hi=1.35, bump=0.09, grime=0.5):
    """Procedural wear: roughness variation + micro bump + patchy grime darkening
    of the base color, so surfaces read as used metal, not clean plastic."""
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 6.0
    noise.inputs["Roughness"].default_value = 0.8
    ramp = nt.nodes.new("ShaderNodeMapRange")
    ramp.inputs["From Min"].default_value = 0.25
    ramp.inputs["From Max"].default_value = 0.85
    base_rough = bsdf.inputs["Roughness"].default_value
    ramp.inputs["To Min"].default_value = base_rough * rough_lo
    ramp.inputs["To Max"].default_value = base_rough * rough_hi
    bumpn = nt.nodes.new("ShaderNodeBump")
    bumpn.inputs["Strength"].default_value = bump
    bumpn.inputs["Distance"].default_value = 0.02
    nt.links.new(tex.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Value"])
    nt.links.new(ramp.outputs["Result"], bsdf.inputs["Roughness"])
    nt.links.new(noise.outputs["Fac"], bumpn.inputs["Height"])
    nt.links.new(bumpn.outputs["Normal"], bsdf.inputs["Normal"])
    # grime: large-scale blotches darken the base color toward a desaturated tint
    base_col = tuple(bsdf.inputs["Base Color"].default_value)[:3]
    grime_col = (base_col[0] * 0.42 + 0.012, base_col[1] * 0.42 + 0.010, base_col[2] * 0.42 + 0.008)
    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    noise2.inputs["Scale"].default_value = max(1.2, scale * 0.35)
    noise2.inputs["Detail"].default_value = 4.0
    noise2.inputs["Roughness"].default_value = 0.9
    ramp2 = nt.nodes.new("ShaderNodeMapRange")
    ramp2.inputs["From Min"].default_value = 0.35
    ramp2.inputs["From Max"].default_value = 0.9
    ramp2.inputs["To Min"].default_value = 0.0
    ramp2.inputs["To Max"].default_value = grime
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = 'MIX'
    mix.inputs[1].default_value = (*base_col, 1.0)
    mix.inputs[2].default_value = (*grime_col, 1.0)
    nt.links.new(tex.outputs["Object"], noise2.inputs["Vector"])
    nt.links.new(noise2.outputs["Fac"], ramp2.inputs["Value"])
    nt.links.new(ramp2.outputs["Result"], mix.inputs[0])
    nt.links.new(mix.outputs[0], bsdf.inputs["Base Color"])

RED    = principled("Paint_Red",    (0.155, 0.011, 0.011), metallic=0.35, rough=0.47, coat=0.55, coat_rough=0.22)
BLUE   = principled("Paint_Blue",   (0.008, 0.029, 0.105), metallic=0.35, rough=0.49, coat=0.55, coat_rough=0.24)
SILVER = principled("Paint_Silver", (0.42, 0.44, 0.47),    metallic=0.85, rough=0.38, coat=0.6, coat_rough=0.2)
CHROME = principled("Chrome",       (0.9, 0.92, 0.95),     metallic=1.0,  rough=0.07)
STEEL  = principled("Steel",        (0.32, 0.33, 0.35),    metallic=1.0,  rough=0.32)
GUN    = principled("Gunmetal",     (0.055, 0.058, 0.065), metallic=0.9,  rough=0.46)
DARK   = principled("InnerFrame",   (0.02, 0.02, 0.022),   metallic=0.6,  rough=0.62)
RUBBER = principled("Rubber",       (0.012, 0.012, 0.013), metallic=0.0,  rough=0.94)
GLASS  = principled("GlassSmoke",   (0.045, 0.09, 0.115),  metallic=0.9,  rough=0.03)
GOLD   = principled("BrassDark",    (0.30, 0.19, 0.06),    metallic=1.0,  rough=0.35)
EYE    = principled("EyeGlow",      (0.05, 0.28, 0.9),     metallic=0.0,  rough=0.3, emit=(0.08, 0.40, 1.0), emit_str=7.0)
LIGHTW = principled("LampWarm",     (1.0, 0.75, 0.4),      metallic=0.0,  rough=0.4, emit=(1.0, 0.72, 0.35), emit_str=3.0)
for m, s in ((RED, 5.0), (BLUE, 5.0), (SILVER, 7.0), (STEEL, 9.0), (GUN, 8.0)):
    add_weathering(m, scale=s, bump=0.05)
add_weathering(RUBBER, scale=14.0, rough_lo=0.9, rough_hi=1.05, bump=0.12)

# ---------- helpers ----------
ROOT = bpy.data.collections.new("OPTIMUS")
scene.collection.children.link(ROOT)

def _link(obj, mat=None):
    ROOT.objects.link(obj)
    if obj.name in scene.collection.objects:
        scene.collection.objects.unlink(obj)
    if mat is not None:
        obj.data.materials.append(mat)
    return obj

def bevel(obj, width=0.03, segments=4):
    mod = obj.modifiers.new("bev", 'BEVEL')
    mod.width = width
    mod.segments = segments
    mod.limit_method = 'ANGLE'
    wn = obj.modifiers.new("wn", 'WEIGHTED_NORMAL')
    wn.keep_sharp = True
    return obj

def bbox(name, loc, dims, mat, bevel_w=0.03, rot=(0, 0, 0), bevel_seg=4):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel(o, bevel_w, bevel_seg)
    return _link(o, mat)

def tapered(name, loc, dims_bot, dims_top, height, mat, bevel_w=0.025, rot=(0, 0, 0)):
    """Trapezoidal prism: bottom dims -> top dims over height, centered at loc."""
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    o = bpy.context.object
    o.name = name
    vs = o.data.vertices
    for v in vs:
        top = v.co.z > 0
        d = dims_top if top else dims_bot
        v.co.x *= d[0] / 2 * 2 / 2  # placeholder, set below properly
    # rebuild cleanly with explicit coords
    bpy.data.objects.remove(o, do_unlink=True)
    xb, yb = dims_bot[0] / 2, dims_bot[1] / 2
    xt, yt = dims_top[0] / 2, dims_top[1] / 2
    h = height / 2
    verts = [(-xb, -yb, -h), (xb, -yb, -h), (xb, yb, -h), (-xb, yb, -h),
             (-xt, -yt, h), (xt, -yt, h), (xt, yt, h), (-xt, yt, h)]
    faces = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    o = bpy.data.objects.new(name, mesh)
    o.location = loc
    o.rotation_euler = rot
    bevel(o, bevel_w, 3)
    return _link(o, mat)

def cyl(name, loc, radius, depth, mat, rot=(0, 0, 0), vertices=28, bevel_w=0.012, smooth=True):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    if smooth:
        for p in o.data.polygons:
            p.use_smooth = True
    if bevel_w > 0:
        bevel(o, bevel_w, 3)
    return _link(o, mat)

def ball(name, loc, scale, mat, subdiv=3):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdiv, radius=1.0, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for p in o.data.polygons:
        p.use_smooth = True
    return _link(o, mat)

def dome(name, loc, scale, mat):
    """Half-dome (upper hemisphere) for pauldrons / helmet shell."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=36, ring_count=20, radius=1.0, location=loc)
    o = bpy.context.object
    o.name = name
    # delete lower half
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(o.data)
    verts_low = [v for v in bm.verts if v.co.z < -0.02]
    bmesh.ops.delete(bm, geom=verts_low, context='VERTS')
    bm.to_mesh(o.data)
    bm.free()
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for p in o.data.polygons:
        p.use_smooth = True
    return _link(o, mat)

def piston(name, loc, r_outer, r_inner, len_outer, len_inner, axis='Z', mat_o=STEEL, mat_i=CHROME):
    rot = {'Z': (0, 0, 0), 'X': (0, math.radians(90), 0), 'Y': (math.radians(90), 0, 0)}[axis]
    cyl(name + "_sleeve", loc, r_outer, len_outer, mat_o, rot=rot, vertices=20)
    off = {'Z': (0, 0, (len_outer + len_inner) / 2 - 0.02), 'X': (0, (len_outer + len_inner) / 2 - 0.02, 0), 'Y': (0, 0, 0)}[axis]
    if axis == 'Y':
        off = (0, -(len_outer + len_inner) / 2 + 0.02, 0)
        loc2 = (loc[0] + off[0], loc[1] + off[1], loc[2] + off[2])
    else:
        loc2 = (loc[0] + off[0], loc[1] + off[1], loc[2] + off[2])
    cyl(name + "_rod", loc2, r_inner, len_inner, mat_i, rot=rot, vertices=16)

def vent_slats(prefix, loc, count, size, gap, mat, axis='X', rot=(0, 0, 0)):
    for i in range(count):
        off = i * (size[2] + gap) if axis == 'Z' else i * (size[0] + gap)
        l = (loc[0] + (off if axis == 'X' else 0), loc[1], loc[2] + (off if axis == 'Z' else 0))
        bbox(f"{prefix}_{i}", l, size, mat, bevel_w=0.008, rot=rot, bevel_seg=2)

def curved_panel(name, loc, width, height, radius, mat, thick=0.05):
    """Front-bulging curved plate (cab front): center forward, edges sweep back."""
    nx, nz = 16, 10
    verts, faces = [], []
    for j in range(nz + 1):
        z = -height / 2 + height * j / nz
        for i in range(nx + 1):
            x = -width / 2 + width * i / nx
            sag = radius - math.sqrt(max(radius * radius - x * x, 0.01))
            verts.append((x, sag, z))
    for j in range(nz):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    o = bpy.data.objects.new(name, mesh)
    o.location = loc
    for p in mesh.polygons:
        p.use_smooth = True
    sol = o.modifiers.new("sol", 'SOLIDIFY')
    sol.thickness = thick
    sol.offset = 0.5
    bevel(o, 0.015, 2)
    return _link(o, mat)

def bolt_ring(prefix, center, radius, count, bolt_r, mat, axis='Z'):
    for i in range(count):
        a = 2 * math.pi * i / count
        if axis == 'Z':
            loc = (center[0] + radius * math.cos(a), center[1], center[2] + radius * math.sin(a))
            rot = (math.radians(90), 0, 0)
        else:
            loc = (center[0] + radius * math.cos(a), center[1] + radius * math.sin(a), center[2])
            rot = (0, 0, 0)
        cyl(f"{prefix}_{i}", loc, bolt_r, bolt_r * 1.4, mat, rot=rot, vertices=6, bevel_w=0.004)

# ================= LEGS =================
def build_leg(side):  # side: +1 right (x+), -1 left
    sx = side
    g = f"L{int(sx>0)}"
    # --- foot: layered, toe forward (-Y is front? we use -Y as FRONT) ---
    # Convention: front of robot faces -Y.
    bbox(f"{g}_foot_base", (0.62 * sx, -0.18, 0.16), (0.52, 1.25, 0.30), BLUE, 0.05)
    tapered(f"{g}_foot_toe", (0.62 * sx, -0.78, 0.13), (0.50, 0.55, 0), (0.40, 0.30, 0), 0.24, BLUE, 0.04)
    bbox(f"{g}_foot_toeplate", (0.62 * sx, -0.92, 0.20), (0.42, 0.28, 0.10), STEEL, 0.03)
    bbox(f"{g}_heel", (0.62 * sx, 0.42, 0.15), (0.48, 0.35, 0.28), GUN, 0.04)
    # ankle joint: dark cylinder + side discs
    cyl(f"{g}_ankle", (0.62 * sx, 0.05, 0.48), 0.17, 0.56, DARK, rot=(0, math.radians(90), 0), vertices=24)
    cyl(f"{g}_ankle_disc", (0.90 * sx, 0.05, 0.48), 0.20, 0.07, STEEL, rot=(0, math.radians(90), 0), vertices=24)
    piston(f"{g}_ankle_pist", (0.62 * sx, 0.30, 0.62), 0.045, 0.028, 0.28, 0.22, axis='Z')
    # --- shin: big tapered armor (wide top -> narrower ankle), layered ---
    tapered(f"{g}_shin_main", (0.64 * sx, 0.0, 1.28), (0.62, 0.78, 0), (0.50, 0.60, 0), 1.30, BLUE, 0.05)
    # front shin plate (red accent panel, sloped)
    tapered(f"{g}_shin_front", (0.64 * sx, -0.36, 1.30), (0.46, 0.16, 0), (0.36, 0.12, 0), 1.15, RED, 0.03)
    bbox(f"{g}_shin_chevron", (0.64 * sx, -0.44, 1.72), (0.30, 0.06, 0.16), CHROME, 0.015)
    # side shin armor + vents
    bbox(f"{g}_shin_side", (0.94 * sx, 0.05, 1.35), (0.10, 0.55, 0.95), BLUE, 0.035)
    vent_slats(f"{g}_shin_vent", (0.99 * sx, -0.10, 0.95), 4, (0.04, 0.30, 0.07), 0.045, DARK, axis='Z')
    # calf back block + wheel (outer side)
    bbox(f"{g}_calf", (0.64 * sx, 0.38, 1.30), (0.52, 0.30, 1.05), GUN, 0.05)
    cyl(f"{g}_wheel_tire", (0.99 * sx, 0.30, 1.05), 0.34, 0.16, RUBBER, rot=(0, math.radians(90), 0), vertices=36, bevel_w=0.03)
    cyl(f"{g}_wheel_hub", (1.00 * sx, 0.30, 1.05), 0.19, 0.18, STEEL, rot=(0, math.radians(90), 0), vertices=24)
    bolt_ring(f"{g}_wheel_bolt", (1.10 * sx, 0.30, 1.05), 0.11, 6, 0.022, GUN, axis='Z')
    # --- knee: layered cap + joint ---
    cyl(f"{g}_knee_joint", (0.64 * sx, 0.02, 2.02), 0.165, 0.56, DARK, rot=(0, math.radians(90), 0), vertices=24)
    tapered(f"{g}_knee_cap", (0.64 * sx, -0.30, 2.06), (0.52, 0.24, 0), (0.42, 0.18, 0), 0.48, SILVER, 0.04)
    cyl(f"{g}_knee_disc", (0.97 * sx, 0.02, 2.02), 0.16, 0.06, CHROME, rot=(0, math.radians(90), 0), vertices=24)
    piston(f"{g}_knee_pist", (0.64 * sx, 0.33, 1.95), 0.05, 0.03, 0.30, 0.24, axis='Z')
    # --- thigh: inner frame + front/side armor shells ---
    bbox(f"{g}_thigh_frame", (0.64 * sx, 0.02, 2.78), (0.44, 0.48, 1.05), DARK, 0.05)
    tapered(f"{g}_thigh_front", (0.64 * sx, -0.26, 2.80), (0.52, 0.20, 0), (0.46, 0.16, 0), 1.10, BLUE, 0.04)
    bbox(f"{g}_thigh_side", (0.93 * sx, 0.02, 2.80), (0.12, 0.52, 1.02), BLUE, 0.04)
    bbox(f"{g}_thigh_stripe", (0.64 * sx, -0.37, 3.05), (0.34, 0.03, 0.10), SILVER, 0.01)
    # hip joint
    cyl(f"{g}_hip_joint", (0.60 * sx, 0.0, 3.42), 0.24, 0.52, GUN, rot=(0, math.radians(90), 0), vertices=28)
    cyl(f"{g}_hip_disc", (0.88 * sx, 0.0, 3.42), 0.19, 0.07, STEEL, rot=(0, math.radians(90), 0), vertices=24)

build_leg(+1)
build_leg(-1)

# ================= PELVIS / ABDOMEN =================
bbox("pelvis_core", (0, 0, 3.52), (1.30, 0.78, 0.52), GUN, 0.07)
tapered("pelvis_front", (0, -0.30, 3.50), (1.05, 0.30, 0), (0.92, 0.24, 0), 0.46, STEEL, 0.04)
bbox("pelvis_belt", (0, -0.42, 3.66), (0.86, 0.10, 0.20), GOLD, 0.03)
for s in (+1, -1):
    bbox(f"hip_skirt_{int(s>0)}", (0.78 * s, -0.05, 3.28), (0.46, 0.66, 0.42), BLUE, 0.05, rot=(0, 0, s * math.radians(6)))
    bbox(f"hip_skirt_back_{int(s>0)}", (0.72 * s, 0.30, 3.34), (0.44, 0.30, 0.48), BLUE, 0.05)
# abdomen: stacked dark segments (visible mechanical waist)
for i in range(3):
    z = 3.86 + i * 0.17
    w = 0.92 - i * 0.05
    bbox(f"abdomen_{i}", (0, 0.02, z), (w, 0.55, 0.15), DARK if i % 2 == 0 else GUN, 0.04)
bbox("abdomen_front", (0, -0.28, 4.02), (0.55, 0.10, 0.42), STEEL, 0.03)
piston("waist_pist_r", (0.52, 0.18, 3.95), 0.05, 0.03, 0.26, 0.2, axis='Z')
piston("waist_pist_l", (-0.52, 0.18, 3.95), 0.05, 0.03, 0.26, 0.2, axis='Z')

# ================= TORSO / CHEST =================
# inner chest frame (dark, seen through gaps)
bbox("chest_frame", (0, 0.03, 5.15), (2.15, 1.05, 2.15), DARK, 0.08)
# chest main volume: tapered (wide shoulders -> narrower waist), deep
tapered("chest_main", (0, 0, 5.30), (2.05, 1.28, 0), (2.55, 1.42, 0), 1.95, RED, 0.10)
# sloped upper chest / hood slope toward neck
tapered("chest_slope", (0, -0.05, 6.28), (2.45, 1.35, 0), (1.70, 1.05, 0), 0.42, RED, 0.06)
# curved cab front panel under the glass (center proud, edges sweep back into the chest)
curved_panel("cab_curve", (0, -0.615, 5.24), 2.34, 1.66, 3.6, RED)
# windshield recess: dark inset panel the glass sits in (breaks the flat front)
bbox("shield_recess", (0, -0.665, 5.76), (2.14, 0.06, 0.94), DARK, 0.02, rot=(math.radians(-8), 0, 0))
# windshield panels: two panes angled into a shallow V (front = -Y)
for s in (+1, -1):
    g = int(s > 0)
    r = (math.radians(-12), 0, s * math.radians(6))
    bbox(f"shield_frame_{g}", (0.55 * s, -0.685, 5.80), (1.04, 0.09, 0.90), CHROME, 0.02, rot=r)
    bbox(f"shield_glass_{g}", (0.55 * s, -0.705, 5.80), (0.92, 0.05, 0.78), GLASS, 0.015, rot=r)
    bbox(f"wiper_{g}", (0.38 * s, -0.76, 5.58), (0.03, 0.02, 0.55), DARK, 0.005, rot=(math.radians(-12), 0, s * math.radians(6) + math.radians(18)))
# center divider + brow visor above shields
bbox("shield_center", (0, -0.76, 5.82), (0.12, 0.10, 0.96), RED, 0.02, rot=(math.radians(-10), 0, 0))
bbox("brow_visor", (0, -0.74, 6.30), (2.20, 0.10, 0.16), RED, 0.03, rot=(math.radians(-14), 0, 0))
# grille: recessed dark bay + vertical chrome bars (narrower, deeper than v1)
bbox("grille_bay", (0, -0.678, 4.90), (1.30, 0.06, 0.60), DARK, 0.015)
for i in range(6):
    bbox(f"grille_bar_{i}", (-0.52 + i * 0.21, -0.70, 4.90), (0.075, 0.05, 0.54), CHROME, 0.008)
bbox("grille_frame_top", (0, -0.69, 5.22), (1.36, 0.07, 0.07), CHROME, 0.01)
bbox("grille_frame_bot", (0, -0.69, 4.58), (1.36, 0.07, 0.07), CHROME, 0.01)
for s in (+1, -1):
    g = int(s > 0)
    cyl(f"headlight_{g}", (0.88 * s, -0.63, 5.06), 0.105, 0.07, CHROME, rot=(math.radians(90), 0, 0), vertices=24)
    cyl(f"headlight_lens_{g}", (0.88 * s, -0.67, 5.06), 0.082, 0.03, LIGHTW, rot=(math.radians(90), 0, 0), vertices=24)
    bbox(f"fog_{g}", (0.95 * s, -0.72, 4.42), (0.20, 0.05, 0.11), LIGHTW, 0.015)
# bumper / lower chest apron
tapered("chest_apron", (0, -0.55, 4.42), (1.95, 0.35, 0), (2.05, 0.42, 0), 0.35, STEEL, 0.04)
bbox("apron_stripe", (0, -0.76, 4.40), (1.20, 0.04, 0.08), RED, 0.01)
# side chest intakes + stacked chrome strips under grille
for s in (+1, -1):
    g = int(s > 0)
    vent_slats(f"intake_{g}", (1.16 * s, -0.45, 4.72), 3, (0.05, 0.35, 0.09), 0.05, DARK, axis='Z')
    for i in range(3):
        bbox(f"sidechrome_{g}_{i}", (1.24 * s, -0.20 + i * 0.0, 5.30 - i * 0.22), (0.06, 0.55, 0.10), CHROME, 0.012)
# chest side armor (angled plates wrapping the torso)
for s in (+1, -1):
    g = int(s > 0)
    bbox(f"chest_side_{g}", (1.22 * s, 0.05, 5.45), (0.22, 1.15, 1.55), RED, 0.05, rot=(0, 0, s * math.radians(-4)))
    bbox(f"chest_side_trim_{g}", (1.30 * s, -0.30, 4.90), (0.08, 0.5, 0.5), SILVER, 0.02)
# angled front corner pillars: wrap the cab corners so the chest front is not one slab
for s in (+1, -1):
    g = int(s > 0)
    bbox(f"chest_pillar_{g}", (1.13 * s, -0.52, 5.42), (0.30, 0.34, 1.70), RED, 0.05, rot=(0, s * math.radians(24), 0))
    bbox(f"chest_pillar_trim_{g}", (1.20 * s, -0.62, 5.90), (0.10, 0.10, 0.80), CHROME, 0.015, rot=(0, s * math.radians(24), 0))
# neck ring + collar
cyl("neck_ring", (0, 0, 6.52), 0.34, 0.18, GUN, vertices=28)
cyl("collar", (0, 0, 6.44), 0.46, 0.14, STEEL, vertices=28)

# ================= ARMS =================
def build_arm(side):
    sx = side
    g = f"A{int(sx>0)}"
    # shoulder joint + layered dome pauldron
    cyl(f"{g}_sh_joint", (1.48 * sx, 0, 6.02), 0.30, 0.42, GUN, rot=(0, math.radians(90), 0), vertices=28)
    dome(f"{g}_pauldron", (1.62 * sx, 0, 6.10), (0.55, 0.58, 0.50), RED)
    dome(f"{g}_pauldron_top", (1.62 * sx, 0, 6.30), (0.40, 0.42, 0.34), RED)
    bbox(f"{g}_pauldron_trim", (1.98 * sx, 0, 5.95), (0.10, 0.60, 0.18), SILVER, 0.02)
    vent_slats(f"{g}_pauldron_vent", (1.98 * sx, -0.18, 6.18), 3, (0.04, 0.26, 0.06), 0.04, DARK, axis='Z')
    # smokestack on outer shoulder (chrome exhaust)
    cyl(f"{g}_stack", (1.86 * sx, 0.34, 6.35), 0.075, 0.85, CHROME, vertices=20)
    cyl(f"{g}_stack_tip", (1.86 * sx, 0.34, 6.80), 0.095, 0.10, GUN, vertices=20)
    # upper arm: frame + red shell
    bbox(f"{g}_upper_frame", (1.66 * sx, 0.02, 5.35), (0.44, 0.46, 0.95), DARK, 0.06)
    tapered(f"{g}_upper_shell", (1.66 * sx, -0.10, 5.38), (0.62, 0.46, 0), (0.55, 0.42, 0), 1.0, RED, 0.05)
    bbox(f"{g}_upper_side", (1.94 * sx, 0.05, 5.35), (0.10, 0.40, 0.85), SILVER, 0.03)
    # elbow
    cyl(f"{g}_elbow", (1.66 * sx, 0.02, 4.82), 0.20, 0.46, GUN, rot=(0, math.radians(90), 0), vertices=24)
    cyl(f"{g}_elbow_disc", (1.92 * sx, 0.02, 4.82), 0.14, 0.06, STEEL, rot=(0, math.radians(90), 0), vertices=20)
    piston(f"{g}_elbow_pist", (1.66 * sx, 0.30, 5.05), 0.04, 0.025, 0.24, 0.18, axis='Z')
    # forearm: bigger tapered housing (silver) + blue panel + vents
    tapered(f"{g}_forearm", (1.66 * sx, 0.0, 4.18), (0.52, 0.52, 0), (0.60, 0.58, 0), 1.05, SILVER, 0.05)
    bbox(f"{g}_forearm_panel", (1.66 * sx, -0.30, 4.22), (0.44, 0.08, 0.80), BLUE, 0.02)
    vent_slats(f"{g}_forearm_vent", (1.99 * sx, -0.05, 3.95), 3, (0.04, 0.30, 0.07), 0.045, DARK, axis='Z')
    bbox(f"{g}_forearm_stripe", (1.66 * sx, -0.35, 4.55), (0.30, 0.03, 0.08), RED, 0.01)
    # wrist + fist with fingers
    cyl(f"{g}_wrist", (1.66 * sx, 0, 3.62), 0.16, 0.30, DARK, vertices=20)
    bbox(f"{g}_fist", (1.66 * sx, -0.02, 3.38), (0.40, 0.42, 0.34), GUN, 0.06)
    for i in range(4):
        fx = 1.66 * sx + (i - 1.5) * 0.095
        bbox(f"{g}_finger_{i}", (fx, -0.05, 3.16), (0.085, 0.16, 0.20), STEEL, 0.025)
        bbox(f"{g}_finger_tip_{i}", (fx, -0.06, 3.02), (0.08, 0.14, 0.12), STEEL, 0.02)
    bbox(f"{g}_thumb", (1.66 * sx - 0.24 * sx, -0.16, 3.30), (0.09, 0.14, 0.24), STEEL, 0.025, rot=(0, sx * math.radians(20), 0))

build_arm(+1)
build_arm(-1)

# ================= BACKPACK =================
bbox("pack_main", (0, 0.62, 5.45), (1.70, 0.55, 1.85), GUN, 0.07)
for s in (+1, -1):
    g = int(s > 0)
    cyl(f"tank_{g}", (0.52 * s, 0.72, 5.55), 0.21, 1.55, CHROME, vertices=26)
    cyl(f"tank_cap_{g}", (0.52 * s, 0.72, 6.36), 0.16, 0.10, STEEL, vertices=20)
    for i, dz in enumerate((-0.5, 0.0, 0.5)):
        cyl(f"tank_band_{g}_{i}", (0.52 * s, 0.72, 5.55 + dz), 0.225, 0.07, GUN, vertices=26)
    bbox(f"pack_fin_{g}", (0.95 * s, 0.66, 5.60), (0.08, 0.42, 1.30), SILVER, 0.02)
vent_slats("pack_vent", (-0.5, 0.93, 4.95), 5, (0.16, 0.05, 0.08), 0.05, DARK, axis='X')

# ================= HEAD =================
# neck + throat mechanics
cyl("neck", (0, 0, 6.62), 0.20, 0.22, DARK, vertices=20)
bbox("throat", (0, -0.10, 6.66), (0.30, 0.18, 0.18), GUN, 0.03)
# face core: narrow tapered form (wider at brow, narrower at jaw), dark steel
tapered("face_main", (0, -0.07, 7.00), (0.38, 0.34, 0), (0.48, 0.40, 0), 0.66, STEEL, 0.05)
# forehead plate (slightly proud, angled back)
bbox("face_forehead", (0, -0.20, 7.30), (0.44, 0.16, 0.16), SILVER, 0.03, rot=(math.radians(-14), 0, 0))
# brow ridge: one heavy angled bar over the eyes
bbox("brow", (0, -0.265, 7.27), (0.50, 0.07, 0.08), GUN, 0.015, rot=(math.radians(-16), 0, 0))
# nose ridge
bbox("nose", (0, -0.275, 7.05), (0.085, 0.05, 0.20), SILVER, 0.012)
# eyes: deep sockets, emissive strip sitting proud, steel eyelid bar above
for s in (+1, -1):
    g = int(s > 0)
    bbox(f"eye_socket_{g}", (0.135 * s, -0.27, 7.13), (0.185, 0.05, 0.115), DARK, 0.008, rot=(math.radians(-8), 0, 0))
    bbox(f"eye_{g}", (0.135 * s, -0.298, 7.13), (0.135, 0.03, 0.058), EYE, 0.005, rot=(math.radians(-8), 0, 0))
    bbox(f"brow_lid_{g}", (0.135 * s, -0.285, 7.235), (0.175, 0.035, 0.032), STEEL, 0.006, rot=(math.radians(-22), 0, 0))
# mouthplate: dark border plate + raised silver vent plate with center ridge
bbox("mouth_border", (0, -0.19, 6.78), (0.40, 0.10, 0.30), GUN, 0.02)
tapered("mouth_plate", (0, -0.225, 6.78), (0.29, 0.13, 0), (0.34, 0.16, 0), 0.24, SILVER, 0.025)
for i in range(3):
    bbox(f"mouth_slat_{i}", (0, -0.30, 6.705 + i * 0.055), (0.19, 0.014, 0.016), DARK, 0.004)
bbox("mouth_ridge", (0, -0.305, 6.78), (0.035, 0.02, 0.20), STEEL, 0.006)
tapered("chin", (0, -0.15, 6.585), (0.28, 0.24, 0), (0.34, 0.28, 0), 0.13, GUN, 0.03)
# cheek guards (angled, tapered) + jaw hinges
for s in (+1, -1):
    g = int(s > 0)
    tapered(f"cheek_{g}", (0.245 * s, -0.14, 6.94), (0.085, 0.20, 0), (0.075, 0.17, 0), 0.34, SILVER, 0.02, rot=(0, s * math.radians(-16), 0))
    cyl(f"jaw_{g}", (0.27 * s, -0.03, 6.72), 0.07, 0.07, GUN, rot=(0, math.radians(90), 0), vertices=18)
    bbox(f"jaw_plate_{g}", (0.235 * s, -0.10, 6.66), (0.09, 0.24, 0.13), STEEL, 0.02, rot=(0, s * math.radians(-10), 0))
# helmet: smooth dome shell + brim ring + back plate + crest fin + antennae
dome("helmet", (0, 0.04, 7.28), (0.48, 0.50, 0.50), BLUE)
bpy.ops.mesh.primitive_torus_add(major_radius=0.45, minor_radius=0.04, location=(0, 0.03, 7.25))
_brim = bpy.context.object
_brim.name = "helmet_brim"
_brim.scale = (1.0, 1.0, 0.55)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
_link(_brim, BLUE)
bbox("helmet_back", (0, 0.22, 7.16), (0.64, 0.26, 0.64), BLUE, 0.07)
for s in (+1, -1):
    g = int(s > 0)
    cyl(f"ear_{g}", (0.43 * s, 0.02, 7.08), 0.105, 0.08, STEEL, rot=(0, math.radians(90), 0), vertices=22)
    cyl(f"ear_cap_{g}", (0.47 * s, 0.02, 7.08), 0.055, 0.05, CHROME, rot=(0, math.radians(90), 0), vertices=18)
    vent_slats(f"helmet_vent_{g}", (0.44 * s, -0.10, 7.40), 3, (0.03, 0.12, 0.045), 0.035, DARK, axis='Z')
    bbox(f"antenna_{g}", (0.31 * s, 0.09, 7.86), (0.05, 0.05, 0.26), BLUE, 0.012, rot=(0, s * math.radians(-6), 0))
    bbox(f"side_fin_{g}", (0.40 * s, 0.07, 7.46), (0.05, 0.24, 0.20), BLUE, 0.015, rot=(math.radians(10), 0, 0))
# crest: front-to-back fin plate on the crown + chrome forehead gem
bbox("crest", (0, 0.03, 7.80), (0.055, 0.42, 0.17), BLUE, 0.012, rot=(math.radians(8), 0, 0))
bbox("crest_gem", (0, -0.16, 7.65), (0.07, 0.05, 0.09), CHROME, 0.01, rot=(math.radians(8), 0, 0))

# head presence pass: scale whole head assembly up around the neck pivot
HEAD_PREFIXES = ("neck", "throat", "face_", "chin", "mouth_", "nose", "brow", "eye_", "cheek_", "jaw_", "helmet", "ear_", "antenna_", "side_fin_", "crest")
pivot = Vector((0, 0, 6.55))
for o in bpy.data.objects:
    if o.name.startswith(HEAD_PREFIXES) and o.type == 'MESH':
        o.location = pivot + (o.location - pivot) * 1.13
        o.scale = o.scale * 1.13

print("BUILD DONE, objects:", len(bpy.data.objects))

# ================= STAGE / LIGHTS / CAMERA =================
# ground: dark matte disc with slight metalness for reflection feel
bpy.ops.mesh.primitive_circle_add(radius=9, location=(0, 0, 0), fill_type='NGON')
ground = bpy.context.object
ground.name = "Ground"
gm = principled("GroundMat", (0.012, 0.013, 0.016), metallic=0.4, rough=0.42)
ground.data.materials.append(gm)
bpy.ops.mesh.primitive_torus_add(major_radius=3.4, minor_radius=0.02, location=(0, 0, 0.012))
ring = bpy.context.object
ring.name = "GroundRing"
ring.data.materials.append(principled("RingMat", (0.1, 0.35, 0.6), metallic=0.2, rough=0.4, emit=(0.15, 0.5, 0.9), emit_str=1.6))

world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.008, 0.010, 0.016, 1.0)
bg.inputs[1].default_value = 1.0

def area_light(name, loc, energy, size, color, target=(0, 0, 4.0)):
    bpy.ops.object.light_add(type='AREA', location=loc)
    l = bpy.context.object
    l.name = name
    l.data.energy = energy
    l.data.shape = 'DISK'
    l.data.size = size
    l.data.color = color
    direction = Vector(target) - Vector(loc)
    l.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    return l

area_light("Key", (6.5, -7.5, 10.5), 1400, 6.0, (1.0, 0.96, 0.92))
area_light("Rim", (-7.5, 5.5, 8.5), 1100, 5.0, (0.55, 0.75, 1.0))
area_light("Fill", (-6.0, -6.5, 3.5), 350, 5.0, (0.8, 0.85, 1.0))
area_light("Top", (0.5, -1.0, 13.0), 700, 4.0, (1.0, 1.0, 1.0))
# faint blue spill in front of the face so the emissive eyes read at this distance
bpy.ops.object.light_add(type='POINT', location=(0, -1.0, 7.15))
_eye_spill = bpy.context.object
_eye_spill.name = "EyeSpill"
_eye_spill.data.energy = 2.5
_eye_spill.data.color = (0.35, 0.65, 1.0)
_eye_spill.data.shadow_soft_size = 0.1
if hasattr(_eye_spill.data, "use_custom_distance"):
    _eye_spill.data.use_custom_distance = True
    _eye_spill.data.cutoff_distance = 1.4

# reflection cards: big soft emissive planes (invisible to camera) so paint/glass
# pick up studio streaks instead of reflecting a black void
def refl_card(name, loc, size, rot, strength, color=(1.0, 1.0, 1.0)):
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=loc, rotation=rot)
    p = bpy.context.object
    p.name = name
    p.scale = (size[0], size[1], 1.0)
    m = principled(name + "Mat", color, metallic=0.0, rough=1.0, emit=color, emit_str=strength)
    p.data.materials.append(m)
    p.visible_camera = False
    return p

refl_card("CardTop", (0.5, -3.5, 11.5), (10.0, 5.0), (math.radians(35), 0, 0), 5.0)
refl_card("CardFront", (0, -11.0, 5.5), (9.0, 4.0), (math.radians(90), 0, 0), 2.2)
refl_card("CardLeft", (-9.5, -1.5, 5.0), (2.2, 7.0), (math.radians(90), 0, math.radians(90)), 4.0, (0.75, 0.85, 1.0))
refl_card("CardRight", (9.5, -1.5, 5.0), (2.2, 7.0), (math.radians(90), 0, math.radians(-90)), 3.0, (1.0, 0.9, 0.8))

bpy.ops.object.camera_add(location=(6.4, -11.2, 5.4))
cam = bpy.context.object
cam.name = "HeroCam"
cam.data.lens = 50
direction = Vector((0, 0, 3.95)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 64
scene.cycles.use_denoising = True
scene.cycles.denoiser = 'OPENIMAGEDENOISE'
scene.cycles.max_bounces = 6
scene.render.resolution_x = 1000
scene.render.resolution_y = 1250
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = "/home/hatch/workspace/three-home-blender/hero_still.png"
scene.render.film_transparent = False
# color management: AgX, medium-high contrast for filmic look
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.view_settings.exposure = 0.0

bpy.ops.wm.save_as_mainfile(filepath="/home/hatch/workspace/three-home-blender/optimus.blend")
bpy.ops.render.render(write_still=True)
print("RENDER DONE")

# head close-up: second still so the face sculpt can be judged at reading distance
bpy.ops.object.camera_add(location=(1.45, -3.1, 7.75))
cam2 = bpy.context.object
cam2.name = "HeadCam"
cam2.data.lens = 85
direction2 = Vector((0, -0.05, 7.15)) - cam2.location
cam2.rotation_euler = direction2.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam2
scene.render.resolution_x = 900
scene.render.resolution_y = 900
scene.cycles.samples = 48
scene.render.filepath = "/home/hatch/workspace/three-home-blender/head_closeup.png"
bpy.ops.render.render(write_still=True)
print("HEAD RENDER DONE")
