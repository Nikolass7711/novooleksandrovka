"""Квартира-смарт 31–43 м² — головна кімната ~20 м², «компактно і світло».
Ракурс приблизно як IMG_7865 (два вікна в торці, пілон справа). Ранок, робоче місце біля вікна.
Вид за вікном — реальний вид з квартири (IMG_7872), не вигаданий."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gp_lib as G  # noqa: E402

out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/s3.png"
W, H, SPP = (int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (1920, 1080, 160)
PH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "photos")

G.reset()
G.resolution(W, H)
floor = G.mat_wood("AshFloor", base=(0.74, 0.62, 0.48), dark=(0.6, 0.48, 0.35), along="Y", plank_len=1.4, plank_w=0.18)
wall = G.mat_plaster("WarmWhite", (0.87, 0.84, 0.78))
ceil = G.mat_plaster("CeilS", (0.92, 0.91, 0.89))
white = G.mat_plain("WhiteFront", (0.86, 0.85, 0.82), 0.45)
ash = G.mat_wood("Ash", base=(0.76, 0.64, 0.5), dark=(0.62, 0.5, 0.37), planks=False, rough=0.45)
frame = G.mat_plain("WinWhite", (0.88, 0.88, 0.87), 0.4)
glass = G.mat_glass()
sage = G.mat_fabric("Sage", (0.5, 0.55, 0.45))
sand = G.mat_fabric("Sand", (0.8, 0.74, 0.64))
linen = G.mat_fabric("LinenS", (0.9, 0.88, 0.84))
rust = G.mat_fabric("Rust", (0.6, 0.32, 0.18))
black = G.mat_plain("BlackS", (0.03, 0.03, 0.03), 0.4, metal=0.5)
ceramic = G.mat_plain("CerS", (0.9, 0.88, 0.84), 0.3, coat=0.5)
clay = G.mat_plain("ClayS", (0.66, 0.45, 0.32), 0.8, noise_bump=0.1, scale=30)
leaf = G.mat_leaf("LeafS", (0.12, 0.21, 0.08))
trunk = G.mat_plain("TrunkS", (0.25, 0.2, 0.15), 0.9)
screen = G.mat_emit("Screen", (0.75, 0.82, 0.95), 1.2, base=(0.05, 0.05, 0.06))
sheer = G.mat_fabric("SheerLinen", (0.93, 0.91, 0.87), sheen=0.4)
grass = G.mat_plain("GrassS", (0.13, 0.19, 0.07), 0.9)

HZ = 2.7
WX, WY = 4.4, 4.6
G.box("Floor", (8, 8, 0.2), (WX / 2, WY / 2, -0.2), floor, bev=0)
G.box("Ceil", (WX + 1, WY + 1, 0.2), (WX / 2, WY / 2, HZ), ceil, bev=0)
T = 0.38
wins = [(0.55, 1.25, 0.85, 2.3), (2.45, 1.25, 0.85, 2.3)]
G.wall_with_openings("WF", (0, WY), (WX, WY), HZ, T, wins, wall)
G.wall_with_openings("WL", (0, 0), (0, WY), HZ, T, [], wall)
G.wall_with_openings("WR", (WX, WY), (WX, 0), HZ, T, [], wall)
G.wall_with_openings("WN", (WX, 0), (0, 0), HZ, T, [(1.6, 0.9, 0, 2.1)], wall)
for (a, w, s_, t) in wins:
    G.window("Win", (0, WY), (WX, WY), a, w, s_, t, frame, glass, mullions=1, wall_thick=0.1)
    G.box("Sill", (w + 0.1, 0.3, 0.03), (a + w / 2, WY + 0.12, s_ - 0.03), ash, bev=0.004)
G.box("Pylon", (0.4, 0.35, HZ), (WX - 0.2, 3.2, 0), wall, bev=0.004)  # пілон як на фото

# робочий стіл уздовж вікон (вбудований, ясен)
G.box("Desk", (3.6, 0.6, 0.04), (1.95, WY - 0.33, 0.74), ash, bev=0.004)
G.box("DeskLeg", (0.04, 0.55, 0.74), (0.2, WY - 0.33, 0), ash, bev=0.003)
G.box("DeskDrawers", (0.45, 0.55, 0.6), (3.5, WY - 0.33, 0.14), white, bev=0.003)
G.box("Laptop", (0.32, 0.22, 0.012), (1.25, WY - 0.38, 0.78), black, bev=0.003)
lid = G.box("LaptopLid", (0.32, 0.008, 0.21), (1.25, WY - 0.27, 0.79), screen, bev=0.002, rot=(math.radians(-12), 0, 0))
G.cup((1.65, WY - 0.42, 0.78), ceramic)
G.books((2.6, WY - 0.35, 0.78), 3, seed=31)
G.plant_big_leaf((3.05, WY - 0.3, 0.78), clay, leaf, trunk, pot_r=0.08, pot_h=0.14, n=7, h=0.42, seed=6)
G.cyl("DeskLamp", 0.07, 0.02, (0.55, WY - 0.3, 0.78), black, bev=0.004)
G.cyl("DeskLampPole", 0.008, 0.42, (0.55, WY - 0.3, 0.8), black, verts=8, bev=0)
G.sphere("DeskLampHead", 0.07, (0.62, WY - 0.38, 1.2), black, scale=(1, 1, 0.6))
G.chair((1.3, WY - 0.95, 0), math.pi, sand, ash)
for (a, w, s_, t) in wins:
    G.curtain((a + w / 2 - 0.55, WY - 0.08, 0.02), 0.5, 2.62, sheer, folds=6, depth=0.035)

# ліва стіна: шафа до стелі (білі фасади без ручок) з нішею-полицею з ясена
G.box("Wardrobe", (0.6, 2.3, HZ - 0.02), (0.3, 1.45, 0), white, bev=0.002)
for k in range(4):
    G.box("Gap", (0.003, 0.002, HZ - 0.1), (0.601, 0.3 + 0.575 * k + 0.575, 0.05), black, bev=0)
G.box("NicheBack", (0.02, 0.9, 1.9), (0.01, 3.1, 0), ash, bev=0)
for yy in (2.66, 3.54):
    G.box("NicheSide", (0.6, 0.025, 1.9), (0.3, yy, 0), ash, bev=0.002)
G.box("NicheTop", (0.6, 0.9, 0.025), (0.3, 3.1, 1.9), ash, bev=0.002)
G.box("NicheBase", (0.6, 0.9, 0.08), (0.3, 3.1, 0), ash, bev=0.002)
for z in (0.45, 0.95, 1.45):
    G.box("Shelf", (0.5, 0.86, 0.025), (0.3, 3.1, z), ash, bev=0.002)
G.books((0.3, 2.9, 0.475), 6, lying=False, seed=33)
G.vase((0.3, 3.35, 0.975), ceramic, r=0.06, h=0.2)
G.books((0.3, 3.05, 1.475), 3, seed=35)

# компактний диван уздовж правої стіни, столик, оливка в куті
G.rug((3.05, 1.45, 0), (1.9, 1.7), G.mat_fabric("RugS", (0.78, 0.74, 0.66), bump=0.5, scale=90))
G.sofa((3.92, 1.45, 0), math.pi / 2, {"fabric": sage}, length=2.0, depth=0.88, seat_h=0.42, modules=2, leg_mat=ash,
       pillows=[(-0.45, rust), (0.45, linen)])
G.throw_blanket((3.85, 0.5, 0.64), (0.45, 0.7), sand, rot_z=0.0, sag=0.1)
G.coffee_table((3.15, 1.45, 0), 0.34, 0.4, ash)
G.cup((3.1, 1.4, 0.4), ceramic)
G.cyl("Croissant", 0.06, 0.03, (3.25, 1.55, 0.4), G.mat_plain("Pastry", (0.75, 0.5, 0.22), 0.6), r2=0.03, bev=0.01)
G.books((3.05, 1.6, 0.4), 2, seed=37)
G.plant_olive((3.95, 2.75, 0), 1.45, clay, leaf, trunk, pot_r=0.2, pot_h=0.38, leaves=420, spread=0.38, seed=3)
G.art((WX, 1.45, 1.55), (0.7, 0.5), [(0.9, 0.86, 0.78), (0.55, 0.6, 0.48), (0.7, 0.42, 0.28)], ash, rot_z=math.pi / 2)

# вид за вікном: реальний (IMG_7872), сонячне ранкове світло
G.plane("Ground", (60, 60), (2, 10, -6), grass)
G.backdrop(os.path.join(PH, "IMG_7872.jpg"), (2.4, 14.0, 1.0), (22, 16.5), math.radians(180), strength=1.25, flip=True,
           crop=(0.25, 0.0, 0.95, 1.0))
G.sky_and_sun(elev_deg=36, azim_deg=-22, sun_strength=7.0, sky_strength=0.35, sun_angle=1.2, sun_color=(1.0, 0.9, 0.78))
for (a, w, s_, t) in wins:
    G.area_light((a + w / 2, WY + 0.05, (s_ + t) / 2), (w, t - s_), (math.radians(-90), 0, 0), 1.0, portal=True)
CAM = os.environ.get("CAM", "hero")
if CAM == "match":
    G.camera((2.0, 0.35, 1.45), (2.0, WY, 1.2), lens=15.5, dof=(4.0, 5.6))
else:
    G.camera((1.0, 0.35, 1.42), (2.9, WY, 0.95), lens=17, dof=(3.0, 4.0))
G.exposure(0.55)
G.render(out, SPP)
