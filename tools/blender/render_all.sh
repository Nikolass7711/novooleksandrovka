#!/bin/bash
# Фінальні рендери інтер'єрів (CPU Cycles). Використання: tools/blender/render_all.sh [W H SPP]
cd "$(dirname "$0")"
OUT=../../assets/renders
W=${1:-1920}; H=${2:-1080}; SPP=${3:-128}
python3 s1_house1_living.py  $OUT/R1_house1_living.png  $W $H $SPP
python3 s3_smart.py          $OUT/R3_smart_hero.png     $W $H $SPP
python3 s2_house2_studio.py  $OUT/R2_house2_hero.png    $W $H $SPP
python3 s4_attic_108.py      $OUT/R4_apt108_hero.png    $W $H $SPP
python3 s5_house1_bedroom.py $OUT/R5_house1_bedroom.png $W $H $SPP
# вертикальні версії для 9:16 (та сама сцена, портретний кадр)
if [ "${VERT:-1}" = "1" ]; then
python3 s1_house1_living.py  $OUT/R1v_house1_living.png  1080 1920 $SPP
python3 s3_smart.py          $OUT/R3v_smart_hero.png     1080 1920 $SPP
python3 s4_attic_108.py      $OUT/R4v_apt108_hero.png    1080 1920 $SPP
python3 s5_house1_bedroom.py $OUT/R5v_house1_bedroom.png 1080 1920 $SPP
fi
