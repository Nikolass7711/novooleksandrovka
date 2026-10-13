"""Квартира 107,9 м² (3-й поверх, під скатним дахом) — вітальня, «дім під дахом».
Ракурс приблизно як IMG_7873: фронтон з двома вікнами в торці, скати ліворуч і праворуч,
пласка стеля посередині. Скати оздоблені по існуючій геометрії; мансардних вікон немає.
Вечір: захід сонця у фронтонні вікна, теплі лампи."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gp_lib as G  # noqa: E402
import bmesh  # noqa: E402

out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/s4.png"
W, H, SPP = (int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (1920, 1080, 160)
PH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "photos")

G.reset()
G.resolution(W, H)
floor = G.mat_wood("OakA", base=(0.62, 0.49, 0.36), dark=(0.47, 0.35, 0.24), along="Y", plank_len=2.0, plank_w=0.2)
wall = G.mat_plaster("Oat", (0.84, 0.8, 0.72))
ceil = G.mat_plaster("CeilA", (0.9, 0.88, 0.84))
beam_w = G.mat_wood("BeamOak", base=(0.6, 0.45, 0.3), dark=(0.45, 0.32, 0.2), planks=False, rough=0.55)
frame = G.mat_plain("AnthA", (0.07, 0.075, 0.08), 0.35, metal=0.6)
glass = G.mat_glass()
sage = G.mat_fabric("SageA", (0.47, 0.5, 0.42))
oat = G.mat_fabric("OatF", (0.82, 0.76, 0.66))
clayf = G.mat_fabric("ClayF", (0.62, 0.36, 0.24))
wool = G.mat_fabric("WoolA", (0.74, 0.68, 0.58), bump=0.6, scale=80)
oak = G.mat_wood("OakFurn", base=(0.66, 0.49, 0.32), dark=(0.5, 0.35, 0.22), planks=False, rough=0.45)
ceramic = G.mat_plain("CerA", (0.88, 0.85, 0.8), 0.35, coat=0.4)
clay = G.mat_plain("ClayA", (0.6, 0.4, 0.28), 0.8, noise_bump=0.1, scale=30)
leaf = G.mat_leaf("LeafA", (0.12, 0.2, 0.08))
trunk = G.mat_plain("TrunkA", (0.25, 0.2, 0.15), 0.9)
warm = G.mat_emit("WarmA", (1.0, 0.72, 0.45), 5.0, base=(0.9, 0.85, 0.78))
game = [G.mat_plain("GameBox", (0.72, 0.2, 0.15), 0.5), G.mat_plain("GameBoard", (0.9, 0.85, 0.7), 0.6)]
grass = G.mat_plain("GrassA", (0.12, 0.18, 0.07), 0.9)

WX, WY = 6.6, 8.0
KNEE, FLAT, FX0, FX1 = 2.15, 3.05, 1.7, 4.9  # висота стін біля скатів, пласка стеля, її межі
G.box("Floor", (12, 14, 0.2), (WX / 2, WY / 2, -0.2), floor, bev=0)


def prism(name, profile, y0, y1, mat):
    """Видавлює 2D-профіль (x,z) уздовж Y — для скатної стелі."""
    bm = bmesh.new()
    f0 = [bm.verts.new((x, y0, z)) for (x, z) in profile]
    f1 = [bm.verts.new((x, y1, z)) for (x, z) in profile]
    n = len(profile)
    for i in range(n):
        bm.faces.new((f0[i], f0[(i + 1) % n], f1[(i + 1) % n], f1[i]))
    bm.faces.new(f0[::-1])
    bm.faces.new(f1)
    o = G._obj(name, bm, mat)
    return o


# стеля: скати + пласка частина (тонкий шар над внутрішнім профілем)
th = 0.15
prism("CeilShell", [(-0.3, KNEE), (FX0, FLAT), (FX1, FLAT), (WX + 0.3, KNEE), (WX + 0.3, KNEE + th),
                    (FX1, FLAT + th), (FX0, FLAT + th), (-0.3, KNEE + th)], -0.3, WY + 0.3, ceil)
# бічні стіни до висоти KNEE
G.box("WallL", (0.3, WY + 0.6, KNEE), (-0.15, WY / 2, 0), wall, bev=0)
G.box("WallR", (0.3, WY + 0.6, KNEE), (WX + 0.15, WY / 2, 0), wall, bev=0)
# фронтон (далека стіна) з двома вікнами: будуємо прямокутну стіну до FLAT з прорізами + трикутники під скатами
wins = [(2.1, 0.95, 0.6, 2.35), (3.55, 0.95, 0.6, 2.35)]
G.wall_with_openings("Gable", (0, WY), (WX, WY), FLAT, 0.3, wins, wall)
for (a, w, s_, t) in wins:
    G.window("WinA", (0, WY), (WX, WY), a, w, s_, t, frame, glass, mullions=0, transoms=1, wall_thick=0.12)
G.wall_with_openings("Near", (WX, 0), (0, 0), FLAT, 0.3, [(2.8, 0.9, 0, 2.1)], wall)
# дерев'яні балки-затяжки там, де проходить конструкція
for y in (2.0, 4.0, 6.0):
    G.box("Tie", (FX1 - FX0 + 0.3, 0.14, 0.18), ((FX0 + FX1) / 2, y, FLAT - 0.18), beam_w, bev=0.006)

# вітальня
G.rug((3.3, 4.3, 0), (3.2, 2.6), wool)
G.sofa((3.3, 5.5, 0), math.pi, {"fabric": sage}, length=2.9, depth=1.0, seat_h=0.42, leg_mat=oak,
       pillows=[(-0.95, oat), (-0.45, clayf), (0.9, oat)])
G.throw_blanket((4.4, 5.5, 0.66), (0.5, 0.8), clayf, rot_z=1.5, sag=0.12)
G.rect_table((3.3, 4.25, 0), (1.2, 0.7), 0.38, oak, oak)
G.box("BoardGame", (0.42, 0.42, 0.012), (3.25, 4.25, 0.38), game[1], bev=0.002)
for k, (dx, dy) in enumerate([(-0.1, 0.05), (0.08, -0.06), (0.12, 0.1), (-0.05, -0.12)]):
    G.cyl("Piece", 0.015, 0.035, (3.25 + dx, 4.25 + dy, 0.392), game[0] if k % 2 else ceramic, verts=16, bev=0.002)
G.box("GameLid", (0.3, 0.3, 0.05), (3.75, 4.45, 0.38), game[0], bev=0.003, rot=(0, 0, 0.3))
G.cup((2.9, 4.1, 0.38), ceramic)
G.cup((3.65, 4.05, 0.38), ceramic)
for (x, y, r) in [(2.45, 3.35, 0.35), (4.15, 3.3, -0.4)]:
    G.cushion("FloorCushion", (0.6, 0.6, 0.16), (x, y, 0), oat if r > 0 else clayf, soft=0.45, rot=(0, 0, r))
G.armchair((5.35, 4.1, 0), math.pi / 2 + 0.25, oat, leg_mat=oak)

# обідня зона біля фронтонних вікон
G.round_table((3.3, 6.8, 0), 0.6, 0.75, oak, oak)
for a in (0, 1.57, 3.14, 4.71):
    G.chair((3.3 + 0.85 * math.sin(a), 6.8 - 0.85 * math.cos(a), 0), a + math.pi, oat, oak)
G.pendant((3.3, 6.8, 1.85), "dome", oak, warm, frame, FLAT, r=0.28, light=35)
G.vase((3.3, 6.8, 0.75), clay, r=0.07, h=0.25, stems=6, stem_mat=trunk)

# торшер, полиці під скатом, рослини
G.cyl("FLb", 0.14, 0.03, (1.35, 5.9, 0), frame, bev=0.005)
G.cyl("FLp", 0.01, 1.45, (1.35, 5.9, 0.03), frame, verts=10, bev=0)
G.cyl("FLs", 0.21, 0.3, (1.35, 5.9, 1.38), warm, r2=0.17, bev=0.003)
G.point_light((1.35, 5.9, 1.5), 35, radius=0.12)
G.box("LowShelf", (0.4, 3.2, 0.7), (0.2, 5.0, 0), oak, bev=0.004)
G.books((0.2, 4.0, 0.7), 8, lying=False, seed=41, rot_z=math.pi / 2)
G.vase((0.2, 5.6, 0.7), ceramic, r=0.08, h=0.28)
G.plant_big_leaf((6.05, 7.4, 0), clay, leaf, trunk, pot_r=0.22, pot_h=0.42, n=14, h=1.35, seed=21)
G.plant_olive((0.55, 7.3, 0), 1.5, clay, leaf, trunk, pot_r=0.2, pot_h=0.38, leaves=420, spread=0.38, seed=5)
G.art((WX, 4.4, 1.25), (0.9, 0.6), [(0.86, 0.8, 0.7), (0.5, 0.55, 0.45), (0.65, 0.38, 0.25)], oak, rot_z=math.pi / 2)

# вид з фронтонних вікон — реальна територія (IMG_7857), захід
G.plane("GroundA", (80, 80), (3, 20, -8), grass)
G.backdrop(os.path.join(PH, "IMG_7857.jpg"), (3.3, 22.0, -1.5), (30, 22.5), math.radians(180), strength=1.0, flip=True)
G.sky_and_sun(elev_deg=6, azim_deg=8, sun_strength=6.0, sky_strength=0.08, sun_angle=1.0, sun_color=(1.0, 0.62, 0.36))
for (a, w, s_, t) in wins:
    G.area_light((a + w / 2, WY + 0.05, (s_ + t) / 2), (w, t - s_), (math.radians(-90), 0, 0), 1.0, portal=True)
G.area_light((3.3, 4.5, FLAT - 0.05), (2.5, 4.0), (0, 0, 0), 18, color=(1.0, 0.8, 0.6))  # м'яке тепле «приховане» світло
CAM = os.environ.get("CAM", "hero")
if CAM == "match":
    G.camera((3.3, 0.35, 1.5), (3.3, WY, 1.4), lens=15.5, dof=(6.0, 5.6))
else:
    G.camera((1.35, 0.5, 1.4), (3.7, 6.6, 0.85), lens=18, dof=(4.0, 4.0))
G.exposure(0.6)
G.render(out, SPP)
