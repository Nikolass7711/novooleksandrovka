"""Green Park — бібліотека для фотореалістичних візуалізацій інтер'єрів (Blender/Cycles, bpy).

Розміри приміщень беруться з АР-альбомів; ракурси камер — приблизно за реальними фото.
Усі рендери — «Візуалізація можливого інтер'єру».
"""
import math
import random

import bpy  # noqa: F401  (bmesh доступний лише після bpy)
import bmesh
import bpy
from mathutils import Euler, Vector

R = random.Random(7)


# ------------------------------------------------------------------ scene
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    c = s.cycles
    c.device = "CPU"
    c.samples = 256
    c.adaptive_threshold = 0.015
    c.use_denoising = True
    c.max_bounces = 10
    c.diffuse_bounces = 5
    c.glossy_bounces = 4
    c.transmission_bounces = 8
    c.transparent_max_bounces = 8
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.sample_clamp_indirect = 8.0
    c.blur_glossy = 1.0
    try:
        s.view_settings.view_transform = "AgX"
        s.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    s.render.image_settings.file_format = "PNG"
    s.render.image_settings.color_depth = "16"
    return s


def resolution(w, h):
    s = bpy.context.scene
    s.render.resolution_x, s.render.resolution_y = w, h
    s.render.resolution_percentage = 100


def exposure(ev):
    bpy.context.scene.view_settings.exposure = ev


def link(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj


def camera(loc, look_at, lens=18.0, sensor=36.0, dof=None, shift=(0, 0)):
    cam = bpy.data.cameras.new("Cam")
    cam.lens = lens
    cam.sensor_width = sensor
    cam.shift_x, cam.shift_y = shift
    cam.clip_start = 0.05
    cam.clip_end = 400
    o = link(bpy.data.objects.new("Cam", cam))
    o.location = Vector(loc)
    d = Vector(look_at) - Vector(loc)
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    if dof:
        cam.dof.use_dof = True
        cam.dof.focus_distance = dof[0]
        cam.dof.aperture_fstop = dof[1]
    bpy.context.scene.camera = o
    return o


def sky_and_sun(elev_deg=22, azim_deg=210, sun_strength=4.0, sky_strength=0.35, sun_angle=1.2,
                sun_color=(1.0, 0.93, 0.82)):
    s = bpy.context.scene
    w = bpy.data.worlds.new("World")
    s.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    sky = nt.nodes.new("ShaderNodeTexSky")
    for t in ("MULTIPLE_SCATTERING", "NISHITA", "HOSEK_WILKIE"):
        try:
            sky.sky_type = t
            break
        except Exception:
            continue
    try:
        sky.sun_disc = False
        sky.sun_elevation = math.radians(elev_deg)
        sky.sun_rotation = math.radians(azim_deg)
    except Exception:
        pass
    nt.links.new(sky.outputs[0], bg.inputs[0])
    bg.inputs[1].default_value = sky_strength
    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = sun_strength
    sun.angle = math.radians(sun_angle)
    sun.color = sun_color
    o = link(bpy.data.objects.new("Sun", sun))
    # напрямок: сонце на висоті elev, азимут azim (0 = +Y, за годинниковою)
    el, az = math.radians(elev_deg), math.radians(azim_deg)
    d = Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))
    o.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    return o


def area_light(loc, size, rot, energy, color=(1, 1, 1), portal=False, shape="RECTANGLE"):
    l = bpy.data.lights.new("Area", "AREA")
    l.shape = shape
    l.size = size[0]
    l.size_y = size[1]
    l.energy = energy
    l.color = color
    try:
        l.cycles.is_portal = portal
    except Exception:
        pass
    o = link(bpy.data.objects.new("Area", l))
    o.location = loc
    o.rotation_euler = rot
    return o


def point_light(loc, energy, radius=0.05, color=(1.0, 0.78, 0.55)):
    l = bpy.data.lights.new("Pt", "POINT")
    l.energy = energy
    l.shadow_soft_size = radius
    l.color = color
    o = link(bpy.data.objects.new("Pt", l))
    o.location = loc
    return o


# ------------------------------------------------------------------ materials
def _mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    return m, nt, p


def _set(p, key, val):
    if key in p.inputs:
        p.inputs[key].default_value = val


def _coord(nt, kind="Object"):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tc.outputs[kind], mp.inputs[0])
    return mp


def _bump(nt, p, height_socket, strength=0.1, distance=0.01):
    b = nt.nodes.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = strength
    b.inputs["Distance"].default_value = distance
    nt.links.new(height_socket, b.inputs["Height"])
    nt.links.new(b.outputs[0], p.inputs["Normal"])
    return b


def mat_plain(name, color, rough=0.5, metal=0.0, coat=0.0, sheen=0.0, noise_bump=0.0, scale=40.0):
    m, nt, p = _mat(name)
    _set(p, "Base Color", (*color, 1))
    _set(p, "Roughness", rough)
    _set(p, "Metallic", metal)
    _set(p, "Coat Weight", coat)
    _set(p, "Sheen Weight", sheen)
    if noise_bump:
        mp = _coord(nt)
        n = nt.nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = 8
        nt.links.new(mp.outputs[0], n.inputs[0])
        _bump(nt, p, n.outputs["Fac"], noise_bump, 0.004)
    return m


def mat_plaster(name, color, rough=0.88):
    m, nt, p = _mat(name)
    mp = _coord(nt)
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 3.0
    n.inputs["Detail"].default_value = 6
    nt.links.new(mp.outputs[0], n.inputs[0])
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (*[c * 0.965 for c in color], 1)
    cr.color_ramp.elements[1].color = (*[min(1, c * 1.02) for c in color], 1)
    nt.links.new(n.outputs["Fac"], cr.inputs[0])
    nt.links.new(cr.outputs[0], p.inputs["Base Color"])
    _set(p, "Roughness", rough)
    n2 = nt.nodes.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value = 160
    nt.links.new(mp.outputs[0], n2.inputs[0])
    _bump(nt, p, n2.outputs["Fac"], 0.06, 0.002)
    return m


def mat_wood(name, base=(0.62, 0.45, 0.30), dark=(0.42, 0.28, 0.17), planks=True, plank_len=1.6,
             plank_w=0.19, rough=0.42, along="X", ring_scale=3.0, coat=0.0):
    """Процедурне дерево; planks=True — дошка підлоги з швами та варіацією дощок."""
    m, nt, p = _mat(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tc.outputs["Object"], mp.inputs[0])
    if along == "Y":
        mp.inputs["Rotation"].default_value = (0, 0, math.radians(90))
    # волокна: хвиля, витягнута вздовж X
    mg = nt.nodes.new("ShaderNodeMapping")
    mg.inputs["Scale"].default_value = (0.25, 6.0 * ring_scale / 3, 1.0)
    nt.links.new(mp.outputs[0], mg.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 2.5
    nz.inputs["Detail"].default_value = 10
    nz.inputs["Roughness"].default_value = 0.6
    nt.links.new(mg.outputs[0], nz.inputs[0])
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_type = "BANDS"
    wv.inputs["Scale"].default_value = 1.2
    wv.inputs["Distortion"].default_value = 9.0
    wv.inputs["Detail"].default_value = 6
    nt.links.new(mg.outputs[0], wv.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "FLOAT"
    mix.inputs[0].default_value = 0.45
    nt.links.new(wv.outputs["Fac"], mix.inputs[2])
    nt.links.new(nz.outputs["Fac"], mix.inputs[3])
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position = 0.25
    cr.color_ramp.elements[0].color = (*dark, 1)
    cr.color_ramp.elements[1].position = 0.85
    cr.color_ramp.elements[1].color = (*base, 1)
    nt.links.new(mix.outputs[0], cr.inputs[0])
    col = cr.outputs[0]
    if planks:
        br = nt.nodes.new("ShaderNodeTexBrick")
        br.offset = 0.37
        br.offset_frequency = 1
        br.squash = 1.0
        br.inputs["Scale"].default_value = 1.0
        br.inputs["Mortar Size"].default_value = 0.0018
        br.inputs["Mortar Smooth"].default_value = 0.3
        br.inputs["Bias"].default_value = 0.0
        br.inputs["Brick Width"].default_value = plank_len
        br.inputs["Row Height"].default_value = plank_w
        br.inputs["Color1"].default_value = (0.86, 0.86, 0.86, 1)
        br.inputs["Color2"].default_value = (1.08, 1.06, 1.04, 1)
        br.inputs["Mortar"].default_value = (0.0, 0.0, 0.0, 1)
        nt.links.new(mp.outputs[0], br.inputs[0])
        mul = nt.nodes.new("ShaderNodeMix")
        mul.data_type = "RGBA"
        mul.blend_type = "MULTIPLY"
        mul.inputs[0].default_value = 1.0
        nt.links.new(col, mul.inputs[6])
        nt.links.new(br.outputs["Color"], mul.inputs[7])
        col = mul.outputs[2]
        inv = nt.nodes.new("ShaderNodeMath")
        inv.operation = "SUBTRACT"
        inv.inputs[0].default_value = 1.0
        nt.links.new(br.outputs["Fac"], inv.inputs[1])
        _bump(nt, p, inv.outputs[0], 0.35, 0.003)
    nt.links.new(col, p.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = rough - 0.08
    rr.inputs["To Max"].default_value = rough + 0.1
    nt.links.new(nz.outputs["Fac"], rr.inputs[0])
    nt.links.new(rr.outputs[0], p.inputs["Roughness"])
    _set(p, "Coat Weight", coat)
    _set(p, "Coat Roughness", 0.15)
    return m


def mat_stone(name, a=(0.74, 0.71, 0.66), b=(0.62, 0.59, 0.55), scale=1.6, rough=0.55, tiles=None, vertical=None):
    """vertical: None (підлога), 'YZ' або 'XZ' — для стін."""
    m, nt, p = _mat(name)
    mp = _coord(nt)
    if vertical == "YZ":
        mp.inputs["Rotation"].default_value = (0, math.radians(90), 0)
    elif vertical == "XZ":
        mp.inputs["Rotation"].default_value = (math.radians(90), 0, 0)
    vor = nt.nodes.new("ShaderNodeTexNoise")
    vor.inputs["Scale"].default_value = scale
    vor.inputs["Detail"].default_value = 12
    vor.inputs["Roughness"].default_value = 0.65
    nt.links.new(mp.outputs[0], vor.inputs[0])
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (*b, 1)
    cr.color_ramp.elements[1].color = (*a, 1)
    cr.color_ramp.elements[0].position = 0.35
    cr.color_ramp.elements[1].position = 0.7
    nt.links.new(vor.outputs["Fac"], cr.inputs[0])
    col = cr.outputs[0]
    fine = nt.nodes.new("ShaderNodeTexNoise")
    fine.inputs["Scale"].default_value = 90
    nt.links.new(mp.outputs[0], fine.inputs[0])
    if tiles:
        br = nt.nodes.new("ShaderNodeTexBrick")
        br.offset = 0.0
        br.inputs["Scale"].default_value = 1.0
        br.inputs["Brick Width"].default_value = tiles[0]
        br.inputs["Row Height"].default_value = tiles[1]
        br.inputs["Mortar Size"].default_value = 0.0025
        br.inputs["Color1"].default_value = (0.95, 0.95, 0.95, 1)
        br.inputs["Color2"].default_value = (1.04, 1.03, 1.02, 1)
        br.inputs["Mortar"].default_value = (0.55, 0.55, 0.55, 1)
        nt.links.new(mp.outputs[0], br.inputs[0])
        mul = nt.nodes.new("ShaderNodeMix")
        mul.data_type = "RGBA"
        mul.blend_type = "MULTIPLY"
        mul.inputs[0].default_value = 1.0
        nt.links.new(col, mul.inputs[6])
        nt.links.new(br.outputs["Color"], mul.inputs[7])
        col = mul.outputs[2]
        add = nt.nodes.new("ShaderNodeMath")
        add.operation = "MULTIPLY_ADD"
        add.inputs[1].default_value = 0.1
        nt.links.new(fine.outputs["Fac"], add.inputs[0])
        nt.links.new(br.outputs["Fac"], add.inputs[2])
        inv = nt.nodes.new("ShaderNodeMath")
        inv.operation = "SUBTRACT"
        inv.inputs[0].default_value = 1.0
        nt.links.new(add.outputs[0], inv.inputs[1])
        _bump(nt, p, inv.outputs[0], 0.25, 0.003)
    else:
        _bump(nt, p, fine.outputs["Fac"], 0.08, 0.002)
    nt.links.new(col, p.inputs["Base Color"])
    _set(p, "Roughness", rough)
    return m


def mat_fabric(name, color, rough=0.95, sheen=0.6, scale=600, bump=0.25, boucle=False):
    m, nt, p = _mat(name)
    _set(p, "Base Color", (*color, 1))
    _set(p, "Roughness", rough)
    _set(p, "Sheen Weight", sheen)
    _set(p, "Sheen Roughness", 0.5)
    mp = _coord(nt)
    if boucle:
        v = nt.nodes.new("ShaderNodeTexVoronoi")
        v.inputs["Scale"].default_value = 260
        nt.links.new(mp.outputs[0], v.inputs[0])
        _bump(nt, p, v.outputs["Distance"], 0.6, 0.004)
    else:
        n = nt.nodes.new("ShaderNodeTexWave")
        n.inputs["Scale"].default_value = scale
        n.inputs["Distortion"].default_value = 2
        nt.links.new(mp.outputs[0], n.inputs[0])
        _bump(nt, p, n.outputs["Fac"], bump, 0.002)
    return m


def mat_glass(name="Glass", tint=(0.96, 0.98, 0.98), rough=0.0):
    """Скло, прозоре для тіньових променів (щоб сонце швидко проходило у вікна)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    g = nt.nodes.new("ShaderNodeBsdfGlass")
    g.inputs["Color"].default_value = (*tint, 1)
    g.inputs["Roughness"].default_value = rough
    g.inputs["IOR"].default_value = 1.45
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (*tint, 1)
    lp = nt.nodes.new("ShaderNodeLightPath")
    mx = nt.nodes.new("ShaderNodeMixShader")
    sh = nt.nodes.new("ShaderNodeMath")
    sh.operation = "MAXIMUM"
    nt.links.new(lp.outputs["Is Shadow Ray"], sh.inputs[0])
    nt.links.new(lp.outputs["Is Diffuse Ray"], sh.inputs[1])
    nt.links.new(sh.outputs[0], mx.inputs[0])
    nt.links.new(g.outputs[0], mx.inputs[1])
    nt.links.new(tr.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs[0])
    return m


def mat_emit(name, color=(1.0, 0.8, 0.6), strength=6.0, base=(0.95, 0.93, 0.9)):
    m, nt, p = _mat(name)
    _set(p, "Base Color", (*base, 1))
    _set(p, "Emission Color", (*color, 1))
    _set(p, "Emission Strength", strength)
    _set(p, "Subsurface Weight", 0.3)
    _set(p, "Roughness", 0.6)
    return m


def mat_leaf(name, color=(0.12, 0.22, 0.07)):
    m, nt, p = _mat(name)
    _set(p, "Base Color", (*color, 1))
    _set(p, "Roughness", 0.45)
    _set(p, "Subsurface Weight", 0.25)
    _set(p, "Subsurface Radius", (0.05, 0.1, 0.02))
    _set(p, "Coat Weight", 0.2)
    mp = _coord(nt)
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 30
    nt.links.new(mp.outputs[0], n.inputs[0])
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (color[0] * 0.75, color[1] * 0.8, color[2] * 0.7, 1)
    cr.color_ramp.elements[1].color = (color[0] * 1.25, color[1] * 1.2, color[2] * 1.1, 1)
    nt.links.new(n.outputs["Fac"], cr.inputs[0])
    nt.links.new(cr.outputs[0], p.inputs["Base Color"])
    return m


def mat_art(name, palette):
    """Абстрактне полотно: м'які плями кольорів."""
    m, nt, p = _mat(name)
    mp = _coord(nt, "UV" if False else "Generated")
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 1.6
    n.inputs["Detail"].default_value = 2
    n.inputs["Distortion"].default_value = 0.8
    nt.links.new(mp.outputs[0], n.inputs[0])
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.interpolation = "CONSTANT"
    els = cr.color_ramp.elements
    els[0].color = (*palette[0], 1)
    els[1].position = 0.55
    els[1].color = (*palette[1], 1)
    for i, c in enumerate(palette[2:]):
        e = els.new(0.62 + 0.08 * i)
        e.color = (*c, 1)
    nt.links.new(n.outputs["Fac"], cr.inputs[0])
    nt.links.new(cr.outputs[0], p.inputs["Base Color"])
    _set(p, "Roughness", 0.9)
    return m


# ------------------------------------------------------------------ geometry
def _obj(name, bm, mat=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = link(bpy.data.objects.new(name, me))
    if mat:
        o.data.materials.append(mat)
    return o


def smooth(o):
    for pl in o.data.polygons:
        pl.use_smooth = True
    return o


def bevel(o, w=0.008, seg=3, angle=40):
    mod = o.modifiers.new("Bevel", "BEVEL")
    mod.width = w
    mod.segments = seg
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(angle)
    try:
        mod.harden_normals = True
    except Exception:
        pass
    smooth(o)
    return o


def box(name, size, loc, mat=None, bev=0.006, seg=3, rot=(0, 0, 0)):
    """size=(x,y,z), loc = центр нижньої грані."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z = (v.co.z + 0.5) * size[2]
    o = _obj(name, bm, mat)
    o.location = loc
    o.rotation_euler = rot
    if bev:
        bevel(o, min(bev, min(size) * 0.45), seg)
    return o


def cushion(name, size, loc, mat, soft=0.35, rot=(0, 0, 0), puff=0.0):
    """М'яка подушка: куб + subdivision + bevel."""
    o = box(name, size, loc, mat, bev=min(size) * soft, seg=5, rot=rot)
    if puff:
        d = o.modifiers.new("Puff", "SIMPLE_DEFORM")
        d.deform_method = "BEND"
        d.angle = puff
    return o


def cyl(name, r, h, loc, mat=None, verts=48, r2=None, bev=0.003, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r, radius2=r if r2 is None else r2, depth=h)
    for v in bm.verts:
        v.co.z += h / 2
    o = _obj(name, bm, mat)
    o.location = loc
    o.rotation_euler = rot
    if bev:
        bevel(o, bev, 2, angle=60)
    smooth(o)
    return o


def sphere(name, r, loc, mat=None, scale=(1, 1, 1), sub=3):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    o = _obj(name, bm, mat)
    o.location = loc
    o.scale = scale
    smooth(o)
    return o


def plane(name, size, loc, mat=None, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
    o = _obj(name, bm, mat)
    o.location = loc
    o.rotation_euler = rot
    return o


# ------------------------------------------------------------------ architecture
def wall_with_openings(name, p0, p1, height, thick, openings, mat, inner_offset=0.0):
    """Стіна від p0 до p1 (у плані XY), openings: [(start_along, width, sill, top)].
    Будується з прямокутних блоків навколо прорізів."""
    p0, p1 = Vector((*p0, 0)), Vector((*p1, 0))
    d = p1 - p0
    L = d.length
    ang = math.atan2(d.y, d.x)
    pieces = []
    cur = 0.0
    for (a, w, sill, top) in sorted(openings):
        if a > cur:
            pieces.append((cur, a - cur, 0, height))
        if sill > 0:
            pieces.append((a, w, 0, sill))
        if top < height:
            pieces.append((a, w, top, height))
        cur = a + w
    if cur < L:
        pieces.append((cur, L - cur, 0, height))
    objs = []
    n = Vector((-math.sin(ang), math.cos(ang), 0))
    for i, (a, w, z0, z1) in enumerate(pieces):
        c = p0 + d.normalized() * (a + w / 2) + n * (thick / 2 + inner_offset)
        o = box(f"{name}_{i}", (w, thick, z1 - z0), (c.x, c.y, z0), mat, bev=0)
        o.rotation_euler = (0, 0, ang)
        objs.append(o)
    return objs


def window(name, p0, p1, a, w, sill, top, frame_mat, glass_mat, mullions=1, transoms=0, depth=0.07,
           frame=0.055, wall_thick=0.0):
    """Алюмінієва рама + скло у прорізі стіни (p0→p1)."""
    p0, p1 = Vector((*p0, 0)), Vector((*p1, 0))
    d = (p1 - p0).normalized()
    ang = math.atan2(d.y, d.x)
    n = Vector((-d.y, d.x, 0))
    base = p0 + d * a + n * (wall_thick * 0.5)
    h = top - sill
    parts = []

    def put(off_x, off_z, sx, sz, mat, sy=depth):
        c = base + d * off_x
        o = box(name, (sx, sy, sz), (c.x, c.y, sill + off_z), mat, bev=0.002 if mat == frame_mat else 0)
        o.rotation_euler = (0, 0, ang)
        parts.append(o)

    put(frame / 2, 0, frame, h, frame_mat)
    put(w - frame / 2, 0, frame, h, frame_mat)
    put(w / 2, 0, w, frame, frame_mat)
    put(w / 2, h - frame, w, frame, frame_mat)
    for i in range(1, mullions + 1):
        put(w * i / (mullions + 1), 0, frame * 0.8, h, frame_mat)
    for j in range(1, transoms + 1):
        put(w / 2, h * j / (transoms + 1), w, frame * 0.8, frame_mat)
    put(w / 2, frame, w - 2 * frame, h - 2 * frame, glass_mat, sy=0.012)
    return parts


# ------------------------------------------------------------------ furniture & props
def sofa(loc, rot_z, mats, length=2.6, depth=1.0, seat_h=0.42, back_h=0.78, arm=0.16, modules=3,
         leg_mat=None, pillows=None):
    fab = mats["fabric"]
    root = bpy.data.objects.new("Sofa", None)
    link(root)
    parts = []
    base_h = 0.16
    parts.append(box("SofaBase", (length, depth, base_h), (0, 0, 0.06), mats.get("base", fab), bev=0.03))
    if leg_mat:
        for sx in (-1, 1):
            for sy in (-1, 1):
                parts.append(box("Leg", (0.04, 0.04, 0.06), (sx * (length / 2 - 0.08), sy * (depth / 2 - 0.08), 0), leg_mat, bev=0.004))
    inner = length - 2 * arm
    seat_d = depth - 0.22
    for i in range(modules):
        w = inner / modules
        x = -inner / 2 + w * (i + 0.5)
        parts.append(cushion("Seat", (w - 0.012, seat_d, seat_h - 0.22), (x, 0.11 - 0.01, 0.22), fab, soft=0.32))
        parts.append(cushion("Back", (w - 0.02, 0.22, back_h - seat_h + 0.12), (x, -depth / 2 + 0.2, seat_h - 0.04), fab,
                             soft=0.4, rot=(math.radians(-9), 0, 0)))
    for sx in (-1, 1):
        parts.append(cushion("Arm", (arm, depth, 0.62 - 0.06), (sx * (length / 2 - arm / 2), 0, 0.06), fab, soft=0.38))
    if pillows:
        for k, (px, pm) in enumerate(pillows):
            parts.append(cushion("Pillow", (0.46, 0.14, 0.44), (px, -depth / 2 + 0.36, seat_h + 0.02), pm, soft=0.48,
                                 rot=(math.radians(-14), 0, math.radians(R.uniform(-8, 8)))))
    for o in parts:
        o.parent = root
    root.location = loc
    root.rotation_euler = (0, 0, rot_z)
    return root


def armchair(loc, rot_z, fab, leg_mat=None, size=0.82):
    root = link(bpy.data.objects.new("Armchair", None))
    parts = [cushion("ACbase", (size, size, 0.40), (0, 0, 0.04), fab, soft=0.35),
             cushion("ACback", (size, 0.22, 0.42), (0, -size / 2 + 0.11, 0.38), fab, soft=0.45),
             cushion("ACarmL", (0.18, size, 0.24), (-size / 2 + 0.09, 0, 0.38), fab, soft=0.45),
             cushion("ACarmR", (0.18, size, 0.24), (size / 2 - 0.09, 0, 0.38), fab, soft=0.45)]
    if leg_mat:
        for sx in (-1, 1):
            for sy in (-1, 1):
                parts.append(cyl("ACleg", 0.018, 0.05, (sx * (size / 2 - 0.08), sy * (size / 2 - 0.08), 0), leg_mat))
    for o in parts:
        o.parent = root
    root.location = loc
    root.rotation_euler = (0, 0, rot_z)
    return root


def round_table(loc, r, h, top_mat, base_mat, thick=0.035):
    cyl("TableTop", r, thick, (loc[0], loc[1], h - thick), top_mat, verts=96, bev=0.008)
    cyl("TableBase", r * 0.28, h - thick, (loc[0], loc[1], 0), base_mat, verts=48, r2=r * 0.18)


def coffee_table(loc, r, h, top_mat):
    cyl("CT", r, h, loc, top_mat, verts=96, bev=0.02)


def rect_table(loc, size, h, top_mat, leg_mat, rot_z=0, thick=0.04):
    root = link(bpy.data.objects.new("Table", None))
    parts = [box("Top", (size[0], size[1], thick), (0, 0, h - thick), top_mat, bev=0.006)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box("Leg", (0.06, 0.06, h - thick), (sx * (size[0] / 2 - 0.12), sy * (size[1] / 2 - 0.12), 0), leg_mat, bev=0.004))
    for o in parts:
        o.parent = root
    root.location = loc
    root.rotation_euler = (0, 0, rot_z)
    return root


def chair(loc, rot_z, seat_mat, frame_mat):
    root = link(bpy.data.objects.new("Chair", None))
    parts = [cushion("Seat", (0.46, 0.46, 0.06), (0, 0, 0.42), seat_mat, soft=0.4),
             box("Back", (0.44, 0.04, 0.34), (0, -0.22, 0.5), frame_mat, bev=0.01, rot=(math.radians(-6), 0, 0))]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box("Leg", (0.03, 0.03, 0.43), (sx * 0.2, sy * 0.2, 0), frame_mat, bev=0.004))
    for o in parts:
        o.parent = root
    root.location = loc
    root.rotation_euler = (0, 0, rot_z)
    return root


def stool(loc, seat_mat, frame_mat, h=0.66):
    cyl("StoolSeat", 0.19, 0.05, (loc[0], loc[1], h - 0.05), seat_mat, bev=0.015)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        o = cyl("StoolLeg", 0.012, h - 0.05, (loc[0] + 0.13 * math.cos(a), loc[1] + 0.13 * math.sin(a), 0), frame_mat, bev=0)
    cyl("StoolRing", 0.15, 0.012, (loc[0], loc[1], 0.25), frame_mat, verts=48, r2=0.15, bev=0)


def kitchen_run(x0, y0, length, rot_z, front_mat, top_mat, carcass_mat, depth=0.62, h=0.9, upper=None,
                sink_at=None, hob_at=None, metal=None, glass_black=None, tall=None):
    """Нижній ряд шаф з фасадами (зазори 3 мм), стільниця, опційно верхні шафи/полиця, мийка, варильна поверхня."""
    root = link(bpy.data.objects.new("Kitchen", None))
    parts = []
    plinth = 0.1
    parts.append(box("Plinth", (length, depth - 0.06, plinth), (length / 2, depth / 2 - 0.03, 0), carcass_mat, bev=0))
    n = max(1, int(round(length / 0.6)))
    w = length / n
    for i in range(n):
        parts.append(box("Front", (w - 0.004, 0.019, h - plinth - 0.04 - 0.004), (w * (i + 0.5), depth - 0.01, plinth + 0.002), front_mat, bev=0.002))
    parts.append(box("Carcass", (length, depth - 0.02, h - plinth - 0.04), (length / 2, depth / 2 - 0.01, plinth), carcass_mat, bev=0))
    parts.append(box("Top", (length + 0.02, depth + 0.03, 0.03), (length / 2, depth / 2 + 0.005, h - 0.03), top_mat, bev=0.004))
    if sink_at is not None and metal is not None:
        parts.append(box("Sink", (0.6, 0.42, 0.005), (sink_at, depth / 2, h + 0.0005), metal, bev=0.002))
        parts.append(cyl("Tap", 0.014, 0.32, (sink_at, 0.1, h), metal, bev=0))
        tp = cyl("TapSpout", 0.012, 0.2, (sink_at, 0.1, h + 0.31), metal, bev=0, rot=(math.radians(-90), 0, 0))
        parts.append(tp)
    if hob_at is not None and glass_black is not None:
        parts.append(box("Hob", (0.6, 0.5, 0.006), (hob_at, depth / 2, h), glass_black, bev=0.002))
    if upper:
        kind, mat_u = upper
        if kind == "shelf":
            parts.append(box("Shelf", (length * 0.6, 0.26, 0.04), (length * 0.55, 0.13, 1.55), mat_u, bev=0.004))
        elif kind == "cabinets":
            for i in range(n):
                parts.append(box("Upper", (w - 0.004, 0.36, 0.72), (w * (i + 0.5), 0.18, 1.5), mat_u, bev=0.002))
    if tall:
        for k in range(tall):
            parts.append(box("Tall", (0.598, depth, 2.3), (-0.3 - 0.6 * k, depth / 2, 0), front_mat, bev=0.002))
    for o in parts:
        o.parent = root
    root.location = (x0, y0, 0)
    root.rotation_euler = (0, 0, rot_z)
    return root


def island(loc, size, front_mat, top_mat, rot_z=0, h=0.9, waterfall=True):
    root = link(bpy.data.objects.new("Island", None))
    parts = [box("IslBody", (size[0] - 0.04, size[1] - 0.12, h - 0.04), (0, -0.04, 0), front_mat, bev=0.003),
             box("IslTop", (size[0], size[1], 0.04), (0, 0, h - 0.04), top_mat, bev=0.004)]
    if waterfall:
        for sx in (-1, 1):
            parts.append(box("IslWF", (0.04, size[1], h - 0.04), (sx * (size[0] / 2 - 0.02), 0, 0), top_mat, bev=0.004))
    for o in parts:
        o.parent = root
    root.location = loc
    root.rotation_euler = (0, 0, rot_z)
    return root


def pendant(loc, kind, shade_mat, emit_mat, cord_mat, ceiling_z, r=0.2, light=25.0):
    x, y, z = loc
    cyl("Cord", 0.003, ceiling_z - z - r * 0.4, (x, y, z + r * 0.4), cord_mat, verts=8, bev=0)
    if kind == "globe":
        sphere("Globe", r, (x, y, z), emit_mat, sub=4)
    else:  # dome
        sphere("Dome", r, (x, y, z), shade_mat, scale=(1, 1, 0.6), sub=4)
        sphere("Bulb", r * 0.25, (x, y, z - r * 0.15), emit_mat)
    point_light((x, y, z - r * 0.3), light, radius=r * 0.4)


def rug(loc, size, mat, rot_z=0, thick=0.012, round_=False):
    if round_:
        return cyl("Rug", size[0] / 2, thick, loc, mat, verts=96, bev=0.004)
    return box("Rug", (size[0], size[1], thick), loc, mat, bev=0.004, rot=(0, 0, rot_z))


def plant_olive(loc, height, pot_mat, leaf_mat, trunk_mat, pot_r=0.22, pot_h=0.42, leaves=420, spread=0.45, seed=1):
    rr = random.Random(seed)
    x, y, z = loc
    cyl("Pot", pot_r, pot_h, (x, y, z), pot_mat, verts=64, r2=pot_r * 0.82, bev=0.01)
    cyl("Soil", pot_r * 0.92, 0.01, (x, y, z + pot_h - 0.03), mat_plain("Soil", (0.08, 0.06, 0.05), 1.0), verts=48, bev=0)
    trunk_h = height * 0.55
    cyl("Trunk", 0.025, trunk_h, (x, y, z + pot_h - 0.02), trunk_mat, verts=12, r2=0.015, bev=0)
    cz = z + pot_h + trunk_h + spread * 0.6
    bm = bmesh.new()
    for i in range(leaves):
        # точка в еліпсоїді крони
        while True:
            px, py, pz = rr.uniform(-1, 1), rr.uniform(-1, 1), rr.uniform(-1, 1)
            if px * px + py * py + pz * pz <= 1:
                break
        c = Vector((x + px * spread, y + py * spread, cz + pz * spread * 0.8))
        L, W = rr.uniform(0.05, 0.09), rr.uniform(0.012, 0.02)
        rot = Euler((rr.uniform(-1, 1), rr.uniform(-1.2, 1.2), rr.uniform(0, 6.28)))
        vs = [Vector((-L / 2, 0, 0)), Vector((0, -W / 2, 0.003)), Vector((L / 2, 0, 0)), Vector((0, W / 2, 0.003))]
        m3 = rot.to_matrix()
        vv = [bm.verts.new(c + m3 @ v) for v in vs]
        bm.faces.new(vv)
    o = _obj("Leaves", bm, leaf_mat)
    smooth(o)
    return o


def plant_big_leaf(loc, pot_mat, leaf_mat, stem_mat, pot_r=0.2, pot_h=0.38, n=11, seed=3, h=1.25):
    """Монстера/фікус: великі листки на стеблах."""
    rr = random.Random(seed)
    x, y, z = loc
    cyl("Pot", pot_r, pot_h, (x, y, z), pot_mat, verts=64, r2=pot_r * 0.85, bev=0.01)
    bm = bmesh.new()
    for i in range(n):
        a = rr.uniform(0, 2 * math.pi)
        tilt = rr.uniform(0.25, 0.8)
        L = rr.uniform(0.5, h)
        tip = Vector((x + math.cos(a) * tilt * L * 0.55, y + math.sin(a) * tilt * L * 0.55, z + pot_h + L * (1 - tilt * 0.35)))
        base = Vector((x, y, z + pot_h))
        # стебло
        st = cyl("Stem", 0.006, (tip - base).length, (0, 0, 0), stem_mat, verts=6, bev=0)
        st.location = base
        st.rotation_euler = (tip - base).to_track_quat("Z", "Y").to_euler()
        # лист: овал з 12 вершин, нахилений
        sz = rr.uniform(0.16, 0.26)
        rot = Euler((rr.uniform(0.5, 1.2), 0, a + math.pi / 2)).to_matrix()
        ring = []
        for k in range(12):
            t = 2 * math.pi * k / 12
            v = Vector((math.cos(t) * sz, math.sin(t) * sz * 0.62 + sz * 0.62, -abs(math.sin(t)) * 0.03))
            ring.append(bm.verts.new(tip + rot @ v))
        cen = bm.verts.new(tip + rot @ Vector((0, sz * 0.62, 0.02)))
        for k in range(12):
            bm.faces.new((cen, ring[k], ring[(k + 1) % 12]))
    o = _obj("BigLeaves", bm, leaf_mat)
    smooth(o)
    return o


def books(loc, count, rot_z=0, lying=True, seed=5, palette=None):
    rr = random.Random(seed)
    palette = palette or [(0.55, 0.42, 0.32), (0.82, 0.78, 0.7), (0.3, 0.35, 0.3), (0.62, 0.3, 0.22), (0.9, 0.88, 0.84)]
    mats = [mat_plain(f"Book{i}", c, 0.7) for i, c in enumerate(palette)]
    x, y, z = loc
    root = link(bpy.data.objects.new("Books", None))
    zz = 0
    for i in range(count):
        if lying:
            w, d, t = rr.uniform(0.17, 0.24), rr.uniform(0.23, 0.3), rr.uniform(0.018, 0.035)
            b = box("Book", (d, w, t), (rr.uniform(-0.01, 0.01), rr.uniform(-0.01, 0.01), zz), rr.choice(mats), bev=0.002,
                    rot=(0, 0, math.radians(rr.uniform(-6, 6))))
            zz += t
        else:
            t, w, d = rr.uniform(0.02, 0.04), rr.uniform(0.15, 0.2), rr.uniform(0.2, 0.27)
            b = box("Book", (t, w, d), (zz, 0, 0), rr.choice(mats), bev=0.002)
            zz += t + 0.002
        b.parent = root
    root.location = loc
    root.rotation_euler = (0, 0, rot_z)
    return root


def cup(loc, mat, r=0.042, h=0.09):
    cyl("Cup", r, h, loc, mat, verts=48, r2=r * 0.85, bev=0.004)


def vase(loc, mat, r=0.08, h=0.3, stems=None, stem_mat=None, seed=2):
    cyl("Vase", r, h, loc, mat, verts=64, r2=r * 0.6, bev=0.01)
    if stems and stem_mat:
        rr = random.Random(seed)
        for i in range(stems):
            a = rr.uniform(0, 6.28)
            t = rr.uniform(0.1, 0.35)
            L = rr.uniform(0.35, 0.6)
            st = cyl("Branch", 0.003, L, (loc[0], loc[1], loc[2] + h - 0.05), stem_mat, verts=6, bev=0)
            st.rotation_euler = (t * math.cos(a), t * math.sin(a), 0)


def bowl_fruit(loc, bowl_mat, fruit_mats, r=0.14):
    cyl("Bowl", r, 0.07, loc, bowl_mat, verts=64, r2=r * 0.55, bev=0.01)
    rr = random.Random(11)
    for i in range(5):
        a = i * 1.26
        sphere("Fruit", 0.038, (loc[0] + 0.06 * math.cos(a), loc[1] + 0.06 * math.sin(a), loc[2] + 0.075 + (0.02 if i == 4 else 0)),
               rr.choice(fruit_mats), sub=3)


def throw_blanket(loc, size, mat, rot_z=0, sag=0.06):
    """Плед, перекинутий через підлокітник / край ліжка (вигнутий тонкий шар)."""
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=24, y_segments=12, size=0.5)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z = -sag * (1 - (2 * v.co.x / size[0]) ** 2) + 0.01 * math.sin(v.co.y * 40)
    o = _obj("Throw", bm, mat)
    sol = o.modifiers.new("Sol", "SOLIDIFY")
    sol.thickness = 0.008
    o.modifiers.new("Sub", "SUBSURF").levels = 1
    smooth(o)
    o.location = loc
    o.rotation_euler = (0, 0, rot_z)
    return o


def curtain(loc, width, height, mat, rot_z=0, folds=14, depth=0.05):
    bm = bmesh.new()
    nx, nz = folds * 6, 8
    verts = []
    for j in range(nz + 1):
        row = []
        for i in range(nx + 1):
            u = i / nx
            row.append(bm.verts.new((u * width - width / 2, depth * math.sin(u * folds * 2 * math.pi), j / nz * height)))
        verts.append(row)
    for j in range(nz):
        for i in range(nx):
            bm.faces.new((verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i]))
    o = _obj("Curtain", bm, mat)
    smooth(o)
    sol = o.modifiers.new("Sol", "SOLIDIFY")
    sol.thickness = 0.003
    o.location = loc
    o.rotation_euler = (0, 0, rot_z)
    return o


def mat_sheer(name="Sheer", color=(0.96, 0.94, 0.9)):
    m, nt, p = _mat(name)
    _set(p, "Base Color", (*color, 1))
    _set(p, "Roughness", 0.9)
    _set(p, "Transmission Weight", 0.55)
    _set(p, "Sheen Weight", 0.5)
    _set(p, "Alpha", 0.75)
    return m


def art(loc, size, palette, frame_mat, rot_z=0, name="Art"):
    root = link(bpy.data.objects.new(name, None))
    a = box(name + "Frame", (size[0] + 0.04, 0.03, size[1] + 0.04), (0, 0, -0.02), frame_mat, bev=0.003)
    c = box(name + "Canvas", (size[0], 0.032, size[1]), (0, 0.002, 0), mat_art(name + "M", palette), bev=0.001)
    a.parent = root
    c.parent = root
    root.location = loc
    root.rotation_euler = (0, 0, rot_z)
    return root


def bed(loc, rot_z, frame_mat, linen_mat, duvet_mat, pillow_mat, throw_mat=None, w=1.8, l=2.1):
    root = link(bpy.data.objects.new("Bed", None))
    parts = [box("BedBase", (w + 0.1, l + 0.06, 0.3), (0, 0, 0.0), frame_mat, bev=0.02),
             cushion("Headboard", (w + 0.1, 0.12, 0.85), (0, -l / 2 - 0.02, 0.12), frame_mat, soft=0.3),
             cushion("Mattress", (w, l, 0.22), (0, 0.02, 0.3), linen_mat, soft=0.25)]
    # ковдра з легкими хвилями
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=30, y_segments=30, size=0.5)
    rr = random.Random(4)
    for v in bm.verts:
        v.co.x *= w + 0.16
        v.co.y *= l * 0.72
        v.co.z = 0.03 * math.sin(v.co.x * 7 + v.co.y * 3) + 0.018 * math.sin(v.co.y * 11 + v.co.x * 2) + 0.01 * math.sin(v.co.x * 23)
        if abs(v.co.x) > w / 2:
            v.co.z -= (abs(v.co.x) - w / 2) * 2.8
    d = _obj("Duvet", bm, duvet_mat)
    d.modifiers.new("Sol", "SOLIDIFY").thickness = 0.05
    d.modifiers.new("Sub", "SUBSURF").levels = 1
    smooth(d)
    d.location = (0, l * 0.14, 0.53)
    parts.append(d)
    for sx in (-0.45, 0.45):
        parts.append(cushion("BPillow", (0.62, 0.42, 0.16), (sx * w / 1.8 * 1.0, -l / 2 + 0.3, 0.5), pillow_mat, soft=0.48,
                             rot=(math.radians(-20), 0, 0)))
    parts.append(cushion("BPillow2", (0.5, 0.14, 0.36), (-0.15, -l / 2 + 0.52, 0.52), linen_mat, soft=0.48, rot=(math.radians(-18), 0, 0)))
    if throw_mat:
        t = throw_blanket((0, l / 2 - 0.35, 0.585), (w + 0.3, 0.55), throw_mat, sag=0.0)
        parts.append(t)
    for o in parts:
        o.parent = root
    root.location = loc
    root.rotation_euler = (0, 0, rot_z)
    return root


def outdoor_garden(center, extent, grass, hedge, trunk, seed=9, hedge_lines=(), pines=(), deck=None):
    """Двір за вікнами: газон, туї, сосни (м'які силуети)."""
    plane("Grass", (extent, extent), (center[0], center[1], -0.02), grass)
    for (p0, p1, h) in hedge_lines:
        p0, p1 = Vector(p0), Vector(p1)
        d = p1 - p0
        o = box("Hedge", (d.length, 0.9, h), ((p0.x + p1.x) / 2, (p0.y + p1.y) / 2, 0), hedge, bev=0)
        o.rotation_euler = (0, 0, math.atan2(d.y, d.x))
        sub = o.modifiers.new("Sub", "SUBSURF")
        sub.levels = 3
        sub.render_levels = 3
        tex = bpy.data.textures.new("HedgeN", "CLOUDS")
        tex.noise_scale = 0.07
        tex.noise_depth = 4
        dm = o.modifiers.new("Disp", "DISPLACE")
        dm.texture = tex
        dm.strength = 0.18
    rr = random.Random(seed)
    for (x, y, h) in pines:
        cyl("PineTrunk", 0.07, h * 0.5, (x, y, 0), trunk, verts=10, r2=0.05, bev=0)
        for k in range(14):
            t = k / 13
            s = (1 - t * 0.7) * h * 0.13 * rr.uniform(0.7, 1.2)
            a = rr.uniform(0, 6.28)
            off = (1 - t) * h * 0.12
            c = sphere("PineCrown", s, (x + off * math.cos(a), y + off * math.sin(a), h * (0.42 + t * 0.55)),
                       hedge, scale=(1.3, 1.3, 0.55), sub=3)
            tex = bpy.data.textures.get("PineN") or bpy.data.textures.new("PineN", "CLOUDS")
            tex.noise_scale = 0.15
            dm = c.modifiers.new("Disp", "DISPLACE")
            dm.texture = tex
            dm.strength = s * 0.35
    if deck:
        (x0, y0, x1, y1, dm_) = deck
        box("Deck", (x1 - x0, y1 - y0, 0.05), ((x0 + x1) / 2, (y0 + y1) / 2, -0.03), dm_, bev=0)


def render(path, samples=None):
    s = bpy.context.scene
    if samples:
        s.cycles.samples = samples
    s.render.filepath = path
    bpy.ops.render.render(write_still=True)


def backdrop(img_path, center, size, rot_z, strength=1.6, flip=False, crop=(0, 0, 1, 1)):
    """Реальне фото Green Park як вид за вікном (емісійна площина, не відкидає тіней)."""
    m = bpy.data.materials.new("Backdrop")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = strength
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(img_path)
    tex.extension = "EXTEND"
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    x0, y0, x1, y1 = crop
    sx = (x1 - x0)
    mp.inputs["Scale"].default_value = (-sx if flip else sx, y1 - y0, 1)
    mp.inputs["Location"].default_value = (x1 if flip else x0, y0, 0)
    nt.links.new(tc.outputs["Generated"], mp.inputs[0])
    nt.links.new(mp.outputs[0], tex.inputs[0])
    nt.links.new(tex.outputs[0], em.inputs[0])
    nt.links.new(em.outputs[0], out.inputs[0])
    o = plane("Backdrop", size, (0, 0, 0), m)
    o.rotation_euler = (math.radians(90), 0, rot_z)
    o.location = (center[0], center[1], center[2])
    o.visible_shadow = False
    o.visible_diffuse = False
    return o
