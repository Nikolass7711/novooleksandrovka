"""Будинок 1 · 136,5 м² (АР-3/4/5) — кухня-вітальня 46 м², стиль «теплий сучасний».
Ракурс приблизно як IMG_7880. Запуск: python3 s1_house1_living.py OUT.png [W H SAMPLES]"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gp_lib as G  # noqa: E402

out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/s1.png"
W, H, SPP = (int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (2560, 1440, 384)

G.reset()
G.resolution(W, H)

# ---------------- матеріали
floor = G.mat_wood("OakFloor", base=(0.70, 0.53, 0.36), dark=(0.52, 0.37, 0.23), along="Y", plank_len=1.9, plank_w=0.21)
wall = G.mat_plaster("MilkWall", (0.86, 0.83, 0.77))
ceil = G.mat_plaster("Ceiling", (0.92, 0.91, 0.885))
frame = G.mat_plain("Anthracite", (0.06, 0.065, 0.07), 0.35, metal=0.6)
glass = G.mat_glass()
front = G.mat_plain("MilkFront", (0.84, 0.81, 0.75), 0.48, noise_bump=0.02, scale=200)
oak = G.mat_wood("Oak", base=(0.68, 0.5, 0.33), dark=(0.5, 0.35, 0.21), planks=False, rough=0.45)
quartz = G.mat_stone("Quartz", a=(0.92, 0.91, 0.885), b=(0.86, 0.85, 0.82), scale=8, rough=0.22)
linen = G.mat_fabric("Linen", (0.80, 0.75, 0.66))
boucle = G.mat_fabric("Boucle", (0.9, 0.87, 0.81), boucle=True)
terra = G.mat_fabric("Terracotta", (0.55, 0.26, 0.15))
olive = G.mat_fabric("OliveVelvet", (0.33, 0.35, 0.2), sheen=0.9)
wool = G.mat_fabric("WoolRug", (0.76, 0.70, 0.60), bump=0.5, scale=120)
brass = G.mat_plain("Brass", (0.78, 0.6, 0.37), 0.32, metal=1.0)
steel = G.mat_plain("Steel", (0.75, 0.75, 0.74), 0.25, metal=1.0)
black_glass = G.mat_plain("BlackGlass", (0.01, 0.01, 0.012), 0.08, coat=1.0)
ceramic = G.mat_plain("Ceramic", (0.9, 0.88, 0.83), 0.3, coat=0.5)
clay = G.mat_plain("ClayPot", (0.62, 0.42, 0.3), 0.8, noise_bump=0.1, scale=30)
stoneware = G.mat_plain("Stoneware", (0.35, 0.33, 0.3), 0.7, noise_bump=0.1, scale=60)
leaf = G.mat_leaf("Leaf", (0.13, 0.2, 0.08))
olive_leaf = G.mat_leaf("OliveLeaf", (0.2, 0.25, 0.14))
trunk = G.mat_plain("Trunk", (0.25, 0.2, 0.15), 0.9, noise_bump=0.3, scale=20)
opal = G.mat_emit("Opal", (1.0, 0.82, 0.62), 4.0)
grass = G.mat_plain("Grass", (0.12, 0.2, 0.06), 0.9, noise_bump=0.5, scale=80)
hedge = G.mat_leaf("Hedge", (0.07, 0.14, 0.05))
deck = G.mat_wood("Deck", base=(0.45, 0.32, 0.22), dark=(0.3, 0.2, 0.13), along="X", plank_len=3.0, plank_w=0.14, rough=0.7)
fruit = [G.mat_plain("Orange", (0.85, 0.38, 0.06), 0.4), G.mat_plain("Apple", (0.55, 0.12, 0.06), 0.35),
         G.mat_plain("Lemon", (0.9, 0.75, 0.15), 0.4)]

HZ = 2.85
# ---------------- архітектура (АР-3: загальна кімната 46,3 м², відкрита до зони вітража)
G.box("Floor", (9.6, 12.0, 0.2), (3.3, 4.7, -0.2), floor, bev=0)
G.box("Ceil", (7.2, 10.0, 0.2), (3.3, 4.7, HZ), ceil, bev=0)
T = 0.3
G.wall_with_openings("WL", (0, 0), (0, 9.4), HZ, T, [(5.2, 0.65, 0, 2.6), (6.6, 0.65, 0, 2.6)], wall)
G.wall_with_openings("WF", (0, 9.4), (6.6, 9.4), HZ, T, [(1.2, 1.875, 0, 2.6), (4.3, 2.3, 0, 2.75)], wall)
G.wall_with_openings("WR", (6.6, 9.4), (6.6, 0), HZ, T, [(0.0, 3.4, 0, 2.75), (4.4, 3.0, 0, 2.6)], wall)
G.wall_with_openings("WN", (6.6, 0), (0, 0), HZ, T, [(2.2, 1.0, 0, 2.2)], wall)
for (p0, p1, a, w, top, mull) in [((0, 0), (0, 9.4), 5.2, 0.65, 2.6, 0), ((0, 0), (0, 9.4), 6.6, 0.65, 2.6, 0),
                                  ((0, 9.4), (6.6, 9.4), 1.2, 1.875, 2.6, 1), ((0, 9.4), (6.6, 9.4), 4.3, 2.3, 2.75, 1),
                                  ((6.6, 9.4), (6.6, 0), 0.0, 3.4, 2.75, 2), ((6.6, 9.4), (6.6, 0), 4.4, 3.0, 2.6, 1)]:
    G.window("Win", p0, p1, a, w, 0, top, frame, glass, mullions=mull, wall_thick=T)
# колони і балка (як у коробці)
for y in (2.8, 6.2):
    G.box("Column", (0.32, 0.32, HZ - 0.3), (4.9, y, 0), wall, bev=0.004)
G.box("Beam", (0.32, 9.4, 0.3), (4.9, 4.7, HZ - 0.3), wall, bev=0.004)
# плінтус
G.box("Skirt", (0.012, 4.0, 0.06), (0.006, 7.4, 0), wall, bev=0)
# трекові лінії на стелі
for x in (1.6, 3.2):
    G.box("Track", (0.035, 7.5, 0.045), (x, 4.7, HZ - 0.045), frame, bev=0.002)

# ---------------- кухня вздовж лівої стіни + острів
G.kitchen_run(0.0, 4.6, 4.0, -math.pi / 2, front, quartz, oak, upper=("shelf", oak), sink_at=1.4, hob_at=2.9,
              metal=steel, glass_black=black_glass)
G.box("Splash", (0.012, 4.0, 0.62), (0.006, 2.6, 0.9), quartz, bev=0)
G.island((2.2, 2.6, 0), (2.4, 1.0), oak, quartz, rot_z=math.pi / 2)
for y in (1.95, 2.6, 3.25):
    G.stool((2.95, y), oak, frame)
G.bowl_fruit((2.1, 3.1, 0.9), ceramic, fruit)
G.vase((2.25, 1.95, 0.9), stoneware, r=0.09, h=0.32, stems=7, stem_mat=trunk)
G.box("Board", (0.42, 0.28, 0.025), (0.35, 1.5, 0.9), oak, bev=0.004)
for i, y in enumerate((3.4, 3.62, 3.8)):
    G.cyl("Jar", 0.055, 0.14 + 0.04 * i, (0.13, y, 1.59), ceramic, bev=0.004)
G.plant_big_leaf((0.15, 2.3, 1.59), clay, leaf, trunk, pot_r=0.08, pot_h=0.12, n=7, h=0.4, seed=8)
G.cup((2.45, 2.2, 0.9), ceramic)

# ---------------- обідня зона біля розсувних дверей
G.rect_table((5.75, 3.55, 0), (2.0, 0.95), 0.75, oak, oak, rot_z=math.pi / 2)
for y in (2.95, 3.55, 4.15):
    G.chair((5.12, y, 0), -math.pi / 2, linen, oak)
    G.chair((6.38, y, 0), math.pi / 2, linen, oak)
G.pendant((5.75, 3.2, 1.72), "globe", opal, opal, frame, HZ, r=0.17, light=18)
G.pendant((5.75, 3.95, 1.72), "globe", opal, opal, frame, HZ, r=0.17, light=18)
G.vase((5.75, 3.55, 0.75), ceramic, r=0.07, h=0.22, stems=5, stem_mat=trunk, seed=4)

# ---------------- вітальня
G.rug((2.6, 7.55, 0), (3.2, 2.3), wool)
G.sofa((2.55, 8.75, 0), math.pi, {"fabric": linen}, length=2.7, depth=1.0, leg_mat=oak,
       pillows=[(-0.75, terra), (-0.3, olive), (0.75, terra)])
G.throw_blanket((3.75, 8.55, 0.66), (0.45, 0.8), olive, rot_z=0.1, sag=0.12)
G.coffee_table((2.55, 7.45, 0), 0.5, 0.36, oak)
G.books((2.4, 7.35, 0.36), 3, rot_z=0.4)
G.cup((2.78, 7.55, 0.36), ceramic)
G.cup((2.9, 7.3, 0.36), ceramic)
G.armchair((0.95, 7.0, 0), -math.pi / 2 + 0.35, boucle, leg_mat=oak)
# арочний торшер
G.cyl("LampBase", 0.16, 0.03, (0.55, 8.1, 0), stoneware, bev=0.005)
G.cyl("LampPole", 0.012, 1.85, (0.55, 8.1, 0.03), brass, verts=12, bev=0)
G.sphere("LampShade", 0.2, (0.85, 7.6, 1.78), brass, scale=(1, 1, 0.55))
G.point_light((0.85, 7.6, 1.66), 12, radius=0.08)
G.plant_olive((0.55, 9.0, 0), 1.7, clay, olive_leaf, trunk, pot_r=0.24, pot_h=0.45, leaves=650, spread=0.5)
G.plant_big_leaf((6.15, 8.85, 0), stoneware, leaf, trunk, pot_r=0.22, pot_h=0.42, n=13, h=1.35)
G.art((3.75, 9.385, 1.15), (0.9, 1.15), [(0.86, 0.8, 0.7), (0.72, 0.46, 0.3), (0.42, 0.42, 0.28), (0.93, 0.9, 0.85)],
      oak, rot_z=math.pi)
# плетений кошик з пледом біля дивана
G.cyl("Basket", 0.2, 0.36, (4.15, 8.3, 0), G.mat_fabric("Rattan", (0.6, 0.45, 0.28), bump=0.8, scale=60), bev=0.01)
G.cushion("BasketThrow", (0.3, 0.3, 0.12), (4.15, 8.3, 0.3), terra, soft=0.45)

# ---------------- двір: газон, тераса і реальний вид Green Park за вікнами (IMG_7850)
PH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "photos")
G.plane("Grass", (60, 60), (6, 6, -0.02), grass)
G.box("Deck", (3.2, 8.9, 0.05), (8.2, 4.95, -0.03), deck, bev=0)
G.backdrop(os.path.join(PH, "IMG_7850.jpg"), (17.0, 5.0, 0.9), (26, 19.5), math.radians(90), strength=1.7,
           crop=(0.12, 0.0, 1.0, 1.0))
G.backdrop(os.path.join(PH, "IMG_7850.jpg"), (3.0, 20.0, 0.9), (26, 19.5), math.radians(180), strength=1.7, flip=True,
           crop=(0.12, 0.0, 1.0, 1.0))
G.backdrop(os.path.join(PH, "IMG_7857.jpg"), (-14.0, 5.0, 0.9), (26, 19.5), math.radians(-90), strength=1.6)

# ---------------- світло і камера
G.sky_and_sun(elev_deg=16, azim_deg=62, sun_strength=6.0, sky_strength=0.3, sun_angle=0.8)
for (loc, size, rot) in [((6.62, 7.7, 1.38), (3.4, 2.75), (0, math.radians(90), 0)),
                         ((6.62, 3.5, 1.3), (3.0, 2.6), (0, math.radians(90), 0)),
                         ((2.14, 9.42, 1.3), (1.875, 2.6), (math.radians(-90), 0, 0)),
                         ((5.45, 9.42, 1.38), (2.3, 2.75), (math.radians(-90), 0, 0))]:
    G.area_light(loc, size, rot, 1.0, portal=True)
G.camera((4.35, 0.42, 1.42), (2.0, 9.4, 1.15), lens=16.5, dof=(6.5, 5.6))
G.exposure(-0.1)
G.render(out, SPP)
