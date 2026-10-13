"""Будинок 1 · 136,5 м² — спальня 17,3 м² (АР-3: 4,15 × 4,17 м), вікно ОК-3 1875×2800 у підлогу.
Той самий дизайн-проект, що й кухня-вітальня (дуб, молочні відтінки, льон). Ранок."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gp_lib as G  # noqa: E402

out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/s5.png"
W, H, SPP = (int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (1920, 1080, 160)
PH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "photos")

G.reset()
G.resolution(W, H)
floor = G.mat_wood("OakFloorB", base=(0.70, 0.53, 0.36), dark=(0.52, 0.37, 0.23), along="X", plank_len=1.9, plank_w=0.21)
wall = G.mat_plaster("MilkB", (0.86, 0.83, 0.77))
ceil = G.mat_plaster("CeilB", (0.92, 0.91, 0.885))
frame = G.mat_plain("AnthB", (0.06, 0.065, 0.07), 0.35, metal=0.6)
glass = G.mat_glass()
oak = G.mat_wood("OakB", base=(0.68, 0.5, 0.33), dark=(0.5, 0.35, 0.21), planks=False, rough=0.45)
linen_w = G.mat_fabric("LinenWhite", (0.9, 0.88, 0.84))
linen_o = G.mat_fabric("LinenOat", (0.78, 0.71, 0.6))
terra = G.mat_fabric("TerraB", (0.58, 0.3, 0.18))
olive = G.mat_fabric("OliveB", (0.36, 0.38, 0.22))
boucle = G.mat_fabric("BoucleB", (0.9, 0.87, 0.81), boucle=True)
headb = G.mat_fabric("HeadLinen", (0.74, 0.68, 0.58))
wool = G.mat_fabric("WoolB", (0.8, 0.75, 0.66), bump=0.5, scale=120)
ceramic = G.mat_plain("CerB", (0.9, 0.88, 0.83), 0.3, coat=0.5)
clay = G.mat_plain("ClayB", (0.62, 0.42, 0.3), 0.8, noise_bump=0.1, scale=30)
leaf = G.mat_leaf("LeafB", (0.13, 0.2, 0.08))
trunk = G.mat_plain("TrunkB", (0.25, 0.2, 0.15), 0.9)
warm = G.mat_emit("WarmB", (1.0, 0.78, 0.55), 3.0, base=(0.92, 0.88, 0.8))
sheer = G.mat_fabric("SheerB", (0.94, 0.92, 0.88), sheen=0.4)
grass = G.mat_plain("GrassB", (0.12, 0.2, 0.06), 0.9)

HZ = 2.85
WX, WY = 4.15, 4.17
G.box("Floor", (8, 8, 0.2), (WX / 2, WY / 2, -0.2), floor, bev=0)
G.box("Ceil", (WX + 1, WY + 1, 0.2), (WX / 2, WY / 2, HZ), ceil, bev=0)
T = 0.3
G.wall_with_openings("WF", (0, WY), (WX, WY), HZ, T, [], wall)
G.wall_with_openings("WR", (WX, WY), (WX, 0), HZ, T, [(1.15, 1.875, 0, 2.8)], wall)
G.wall_with_openings("WL", (0, 0), (0, WY), HZ, T, [], wall)
G.wall_with_openings("WN", (WX, 0), (0, 0), HZ, T, [(3.0, 0.9, 0, 2.1)], wall)
G.window("WinB", (WX, WY), (WX, 0), 1.15, 1.875, 0, 2.8, frame, glass, mullions=1, transoms=0, wall_thick=T)
G.curtain((WX - 0.12, WY - 0.75, 0.02), 0.6, 2.78, sheer, rot_z=math.pi / 2, folds=7, depth=0.04)
G.curtain((WX - 0.12, WY - 3.4, 0.02), 0.5, 2.78, sheer, rot_z=math.pi / 2, folds=6, depth=0.04)
G.box("CurtainRail", (0.03, 3.6, 0.03), (WX - 0.12, WY / 2, HZ - 0.06), frame, bev=0)

# ліжко узголів'ям до лівої стіни, обличчям до вікна
G.box("HeadPanel", (0.06, 2.6, 1.15), (0.03, 2.2, 0), oak, bev=0.004)
G.bed((1.15, 2.2, 0), -math.pi / 2, oak, linen_w, linen_o, linen_w, throw_mat=terra, w=1.8, l=2.05)
for y in (0.55, 3.85):
    G.box("Nightstand", (0.42, 0.42, 0.5), (0.3, y, 0), oak, bev=0.006)
    G.cyl("LampB", 0.1, 0.24, (0.28, y, 0.5), ceramic, r2=0.06, bev=0.01)
    G.cyl("LampShadeB", 0.15, 0.2, (0.28, y, 0.74), warm, r2=0.12, bev=0.003)
    G.point_light((0.28, y, 0.84), 10, radius=0.08)
G.books((0.3, 3.85, 0.5), 2, seed=51)
G.cup((0.36, 0.5, 0.5), ceramic)
G.art((0.06, 2.2, 1.55), (1.1, 0.7), [(0.88, 0.84, 0.76), (0.66, 0.42, 0.28), (0.45, 0.47, 0.32)], oak, rot_z=-math.pi / 2)
G.rug((2.55, 2.2, 0), (1.7, 2.8), wool)
# лавка в ногах ліжка
G.box("Bench", (0.42, 1.3, 0.06), (2.45, 2.2, 0.4), oak, bev=0.006)
for y in (1.65, 2.75):
    G.box("BenchLeg", (0.38, 0.05, 0.4), (2.45, y, 0), oak, bev=0.004)
G.books((2.45, 2.0, 0.46), 2, seed=53)
G.throw_blanket((2.45, 2.55, 0.47), (0.4, 0.55), olive, sag=0.0)
# крісло біля вікна і рослина
G.armchair((3.45, 3.55, 0), math.pi + 0.6, boucle, leg_mat=oak, size=0.76)
G.plant_big_leaf((3.75, 0.45, 0), clay, leaf, trunk, pot_r=0.2, pot_h=0.4, n=12, h=1.3, seed=27)
G.box("Dresser", (1.2, 0.45, 0.8), (1.6, 0.25, 0), oak, bev=0.005)
G.vase((1.25, 0.25, 0.8), ceramic, r=0.07, h=0.25, stems=5, stem_mat=trunk, seed=8)

G.plane("GrassB", (60, 60), (10, 2, -0.02), grass)
G.backdrop(os.path.join(PH, "IMG_7850.jpg"), (14.0, 2.0, 0.9), (24, 18), math.radians(90), strength=1.6, crop=(0.12, 0, 1, 1))
G.sky_and_sun(elev_deg=18, azim_deg=105, sun_strength=6.5, sky_strength=0.3, sun_angle=0.9, sun_color=(1.0, 0.88, 0.72))
G.area_light((WX + 0.05, 1.15 + 0.94, 1.4), (1.875, 2.8), (0, math.radians(90), 0), 1.0, portal=True)
G.camera((3.65, 0.3, 1.5), (0.7, 3.0, 0.8), lens=16, dof=(3.3, 4.0))
G.exposure(0.4)
G.render(out, SPP)
