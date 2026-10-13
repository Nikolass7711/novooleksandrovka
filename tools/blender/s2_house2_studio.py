"""Будинок 2 · 173,6 м² (АР-1/2) — студія 36,9 м², «сучасний європейський»: камінь, горіх, графіка.
Ракурс приблизно як IMG_7887 (дві колони, вікна в торці). Золота година, світло увімкнене."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gp_lib as G  # noqa: E402

out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/s2.png"
W, H, SPP = (int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (1920, 1080, 160)
PH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "photos")

G.reset()
G.resolution(W, H)

lime = G.mat_stone("Limestone", a=(0.66, 0.62, 0.56), b=(0.57, 0.53, 0.48), scale=2.2, rough=0.5, tiles=(1.2, 0.6))
wall = G.mat_plaster("Greige", (0.66, 0.62, 0.57))
ceil = G.mat_plaster("Ceil2", (0.9, 0.89, 0.87))
feature = G.mat_stone("FeatureStone", a=(0.62, 0.58, 0.52), b=(0.44, 0.41, 0.37), scale=3.5, rough=0.75, tiles=(0.9, 0.3), vertical="YZ")
ct_stone = G.mat_stone("CTStone", a=(0.6, 0.56, 0.5), b=(0.45, 0.42, 0.38), scale=4, rough=0.6)
walnut = G.mat_wood("Walnut", base=(0.36, 0.23, 0.15), dark=(0.2, 0.12, 0.07), planks=False, rough=0.4)
smoked = G.mat_wood("SmokedOak", base=(0.42, 0.32, 0.23), dark=(0.25, 0.18, 0.12), planks=False, rough=0.45)
frame = G.mat_plain("Black", (0.03, 0.03, 0.032), 0.35, metal=0.7)
glass = G.mat_glass()
greige = G.mat_fabric("GreigeFabric", (0.46, 0.43, 0.39))
cognac = G.mat_plain("Cognac", (0.33, 0.18, 0.1), 0.5, coat=0.15, noise_bump=0.2, scale=120)
graphite = G.mat_fabric("Graphite", (0.18, 0.18, 0.19))
oat = G.mat_fabric("Oat", (0.78, 0.72, 0.62))
rugm = G.mat_fabric("Rug2", (0.5, 0.47, 0.42), bump=0.6, scale=90)
ceramic = G.mat_plain("Ceramic2", (0.85, 0.83, 0.78), 0.35, coat=0.4)
dark_cer = G.mat_plain("DarkCeramic", (0.12, 0.11, 0.1), 0.5, noise_bump=0.1, scale=60)
leaf = G.mat_leaf("Leaf2", (0.11, 0.19, 0.07))
trunk = G.mat_plain("Trunk2", (0.22, 0.18, 0.14), 0.9, noise_bump=0.3, scale=20)
warm = G.mat_emit("WarmGlow", (1.0, 0.72, 0.45), 6.0)
grass = G.mat_plain("Grass2", (0.12, 0.18, 0.06), 0.9, noise_bump=0.5, scale=80)

HZ = 2.85
WX, WY = 7.6, 6.2
G.box("Floor", (12, 12, 0.2), (WX / 2, WY / 2, -0.2), lime, bev=0)
G.box("Ceil", (WX + 1, WY + 1, 0.2), (WX / 2, WY / 2, HZ), ceil, bev=0)
T = 0.3
G.wall_with_openings("WL", (0, 0), (0, WY), HZ, T, [(1.8, 1.0, 0, 2.6)], wall)
G.wall_with_openings("WF", (0, WY), (WX, WY), HZ, T, [(0.7, 1.45, 0, 2.6), (3.3, 2.05, 0, 2.6), (6.15, 1.0, 0, 2.6)], wall)
G.wall_with_openings("WR", (WX, WY), (WX, 0), HZ, T, [(0.0, 2.6, 0, 2.75)], wall)
G.wall_with_openings("WN", (WX, 0), (0, 0), HZ, T, [(3.0, 1.2, 0, 2.2)], wall)
for (p0, p1, a, w, top, m) in [((0, 0), (0, WY), 1.8, 1.0, 2.6, 0), ((0, WY), (WX, WY), 0.7, 1.45, 2.6, 1),
                               ((0, WY), (WX, WY), 3.3, 2.05, 2.6, 1), ((0, WY), (WX, WY), 6.15, 1.0, 2.6, 0),
                               ((WX, WY), (WX, 0), 0.0, 2.6, 2.75, 1)]:
    G.window("Win", p0, p1, a, w, 0, top, frame, glass, mullions=m, wall_thick=T)
for x in (2.55, 5.25):
    G.box("Column", (0.3, 0.3, HZ - 0.3), (x, 3.3, 0), wall, bev=0.004)
G.box("Beam", (WX, 0.3, 0.3), (WX / 2, 3.3, HZ - 0.3), wall, bev=0.004)
# лінійні світильники
for y in (1.6, 4.8):
    G.box("LinLight", (3.2, 0.04, 0.03), (WX / 2, y, HZ - 0.03), G.mat_emit("Lin", (1, 0.8, 0.6), 3.0, base=(0.1, 0.1, 0.1)), bev=0)

# акцентна стіна з каменю + консоль з горіха (ліва стіна, глибина кімнати)
G.box("StoneWall", (0.06, 3.0, HZ), (0.03, 4.55, 0), feature, bev=0)
G.box("Console", (0.45, 2.4, 0.42), (0.285, 4.55, 0.12), walnut, bev=0.006)
G.box("ConsoleShadow", (0.4, 2.3, 0.12), (0.26, 4.55, 0), frame, bev=0)
G.box("NicheLight", (0.02, 2.4, 0.01), (0.52, 4.55, 0.11), warm, bev=0)
G.books((0.3, 3.75, 0.54), 4, rot_z=0.1, seed=12)
G.vase((0.28, 5.3, 0.54), dark_cer, r=0.1, h=0.42, stems=6, stem_mat=trunk, seed=9)
G.cyl("Bowl2", 0.16, 0.06, (0.3, 4.55, 0.54), ceramic, r2=0.08, bev=0.01)
G.art((0.06, 4.55, 1.35), (1.2, 0.85), [(0.5, 0.46, 0.4), (0.2, 0.19, 0.18), (0.75, 0.7, 0.62), (0.58, 0.35, 0.2)],
      frame, rot_z=-math.pi / 2)

# вітальня: модульний диван спиною до кам'яної стіни, обличчям у простір
G.rug((2.45, 4.6, 0), (3.0, 2.6), rugm)
G.sofa((1.45, 4.6, 0), -math.pi / 2, {"fabric": greige}, length=2.8, depth=1.05, seat_h=0.4, back_h=0.72,
       leg_mat=frame, pillows=[(-0.9, oat), (-0.4, graphite), (0.85, oat)])
G.throw_blanket((1.5, 5.75, 0.62), (0.5, 0.75), graphite, rot_z=1.5, sag=0.1)
G.box("CTstone", (1.2, 0.75, 0.3), (2.75, 4.6, 0), ct_stone, bev=0.02)
G.books((2.6, 4.45, 0.3), 2, seed=21)
G.cup((2.95, 4.8, 0.3), ceramic)
G.cup((3.05, 4.6, 0.3), dark_cer)
lc = G.armchair((3.85, 5.3, 0), math.pi / 2 + 0.5, cognac, leg_mat=frame, size=0.78)
G.cyl("SideT", 0.2, 0.48, (3.75, 4.4, 0), walnut, bev=0.01)
G.vase((3.75, 4.4, 0.48), ceramic, r=0.05, h=0.16)
G.cyl("FLbase", 0.15, 0.03, (0.75, 6.0, 0), frame, bev=0.005)
G.cyl("FLpole", 0.01, 1.45, (0.75, 6.0, 0.03), frame, verts=10, bev=0)
G.cyl("FLshade", 0.2, 0.28, (0.75, 6.0, 1.38), G.mat_emit("Shade", (1, 0.75, 0.5), 2.5, base=(0.85, 0.8, 0.72)), r2=0.16, bev=0.003)
G.point_light((0.75, 6.0, 1.45), 30, radius=0.1)

# обідня зона: стіл з горіха, графітові стільці, лінійна підвіска
G.rect_table((5.6, 1.7, 0), (2.2, 1.0), 0.75, walnut, frame)
for x in (4.95, 5.6, 6.25):
    G.chair((x, 1.08, 0), 0, graphite, frame)
    G.chair((x, 2.32, 0), math.pi, graphite, frame)
G.box("LinPend", (1.6, 0.06, 0.05), (5.6, 1.7, 1.62), frame, bev=0.004)
G.box("LinPendGlow", (1.55, 0.04, 0.005), (5.6, 1.7, 1.615), warm, bev=0)
for x in (5.1, 6.1):
    G.cyl("Wire", 0.002, HZ - 1.67, (x, 1.7, 1.67), frame, verts=6, bev=0)
G.point_light((5.6, 1.7, 1.55), 40, radius=0.4)
G.bowl_fruit((5.4, 1.75, 0.75), dark_cer, [G.mat_plain("Pear", (0.65, 0.6, 0.2), 0.5), G.mat_plain("Plum", (0.25, 0.08, 0.12), 0.3)])
G.vase((6.1, 1.6, 0.75), ceramic, r=0.06, h=0.26, stems=4, stem_mat=trunk, seed=5)
G.plant_big_leaf((7.15, 5.75, 0), dark_cer, leaf, trunk, pot_r=0.24, pot_h=0.5, n=15, h=1.5, seed=13)
G.plant_big_leaf((0.45, 0.45, 0), dark_cer, leaf, trunk, pot_r=0.2, pot_h=0.4, n=9, h=1.1, seed=17)

# двір: реальний вид
G.plane("Grass", (60, 60), (4, 4, -0.02), grass)
G.backdrop(os.path.join(PH, "IMG_7858.jpg"), (4.0, 17.0, 1.0), (28, 21), math.radians(180), strength=1.1, flip=True)
G.backdrop(os.path.join(PH, "IMG_7850.jpg"), (17.0, 3.0, 0.9), (26, 19.5), math.radians(90), strength=1.1, crop=(0.12, 0, 1, 1))
G.backdrop(os.path.join(PH, "IMG_7857.jpg"), (-12.0, 3.0, 0.9), (26, 19.5), math.radians(-90), strength=1.1)

G.sky_and_sun(elev_deg=9, azim_deg=18, sun_strength=7.5, sky_strength=0.1, sun_angle=1.0, sun_color=(1.0, 0.72, 0.45))
for (loc, size, rot) in [((1.42, WY + 0.02, 1.3), (1.45, 2.6), (math.radians(-90), 0, 0)),
                         ((4.32, WY + 0.02, 1.3), (2.05, 2.6), (math.radians(-90), 0, 0)),
                         ((WX + 0.02, 4.9, 1.38), (2.6, 2.75), (0, math.radians(90), 0))]:
    G.area_light(loc, size, rot, 1.0, portal=True)
G.exposure(0.55)
CAM = os.environ.get("CAM", "hero")
if CAM == "match":  # ракурс як IMG_7887 — для переходу «до/після»
    G.camera((3.95, 0.4, 1.45), (3.4, WY, 1.15), lens=16.5, dof=(4.5, 5.6))
else:  # героїчний ракурс з кута: диван анфас, кам'яна стіна, вітраж на заході
    G.camera((5.0, 3.75, 1.3), (1.0, 4.95, 0.8), lens=20, dof=(3.6, 4.0))
G.render(out, SPP)
