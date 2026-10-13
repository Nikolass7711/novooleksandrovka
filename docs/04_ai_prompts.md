# 04. AI-визуализации: пайплайн, стилевые библии, промпты ключевых кадров

ID кадров совпадают с полем `prompt_ref` в `timelines/*.json`. Готовый ключевой кадр кладётся в `assets/ai/<ID кадра таймлайна>.jpg`, например `assets/ai/M10.jpg`. Рендерер подставит его вместо заглушки и сам наложит обязательный титр.

## 0. Пайплайн

1. **Ключевой кадр (изображение)** делается из реального фото в том же ракурсе.
   - Нужен режим с жёстким контролем геометрии: image-to-image / inpainting плюс ControlNet **MLSD + Depth**. Вес контроля 0,8–1,0, denoise 0,45–0,6.
   - Подходят Flux / SDXL с ControlNet, Photoshop Generative Fill (только по маскам), Krea / Magnific для апскейла.
   - Маска покрывает отделку: пол, стены, потолок и мебель. **Окна, проёмы, колонны, балки, скаты и вид за окном вне маски**: их пиксели берутся из оригинала.
   - Перед генерацией: убрать бочку ультраширика (Lens Correction), выровнять вертикали.
2. **Проверка ключевого кадра** — накладываем его поверх оригинала с прозрачностью 50% и сверяем:
   - окна, двери, колонны, балки, лестницы и скаты на тех же местах и тех же размеров;
   - вид за окном тот же;
   - мебель реального масштаба: дверь ≈ 2,1 м, столешница 0,9 м, диван 0,85 м;
   - тени согласованы с окнами.

   Если хоть один пункт не выполнен, кадр переделывается.
3. **Анимация.** Image-to-video, 4–5 с:
   - камера статичная или очень медленный наезд ≤ 3%;
   - движение только у людей, ткани, света и пара от чашки;
   - инструменты: Kling / Runway / Veo / Luma с режимом фиксированной камеры;
   - брак: мерцание, плывущая мебель, «резиновые» стены. При браке сокращаем движение или оставляем статичный кадр с параллаксом на монтаже.
4. **Переход «без ремонта → с ремонтом»** делается **на монтаже**: match-dissolve 0,8–1,0 с между реальным кадром и ключевым кадром того же ракурса. Без морфинга, вихрей и «сборки» мебели.
5. **Люди на реальных кадрах.**
   - Инпейнтинг людей в реальное фото с учётом пасмурного рассеянного света и мягких теней. Сезон — осень: лёгкие куртки, свитера.
   - Затем I2V с фиксированной камерой.
   - Люди идут по тротуару или проезду, не через машины, заборы и газоны с ограждением.
   - Масштаб по перспективе: рост 1,6–1,9 м относительно дверей и ворот.

### Общий негативный промпт (добавлять ко всем)

```
extra windows, skylights, roof windows, balcony, second floor, mezzanine, staircase (unless present),
changed window size, moved doors, removed columns, removed beams, changed ceiling height, curved walls,
different view outside window, glass villa, marble palace, gold, chandelier crystal, hotel lobby, resort,
neon green, oversaturated, HDR halo, plastic skin, deformed hands, extra fingers, warped faces,
floating furniture, oversized furniture, fisheye distortion, text, watermark, logo, signage
```

---

## 1. Стилевые библии (один проект на один объект)

**H1 — Дом 1 · 136,5 м² — «Тёплый современный»**

- Пол: инженерная доска светлого дуба, натуральное масло, ёлка или прямая укладка.
- Стены: тёплый молочный (≈ NCS S 0804-Y20R), потолок белый матовый, колонны оштукатурены в цвет стен.
- Кухня: фасады молочные матовые + дуб, столешница светлый кварц, остров у колонны.
- Текстиль: лён и букле в кремовых тонах; акценты — терракота и оливка.
- Свет: тёплый 2700–3000 K, трековые линии на потолке.
- Металл: матовая латунь, минимум.

**H2 — Дом 2 · 173,6 м² — «Современный европейский»**

- Пол: тёплый серый известняк крупного формата.
- Столярка: копчёный дуб или орех; акцентная стена из натурального камня.
- Графика: тонкие чёрные профили, линейные светильники, пропорции «по сетке».
- Палитра: грейдж, графит, натуральное дерево.
- Мебель: низкая, модульная, кожа цвета коньяка в одном предмете.

**H3 — Дом 3 · дуплекс — «Мягкий минимализм»**

- Стены: известковая штукатурка, светлые оттенки. Пол: светлый ясень или светлый микроцемент.
- Мебель лаконичная, без декора. Приватные зоны отделены льняными шторами.
- Акценты: фактура (рогожка, лён, керамика), а не цвет.

**A1 — Смарт 31–43 м² — «Компактно и светло»**

- Встроенное хранение до потолка, светлое дерево, белые фасады без ручек.
- Компактная кухонная линия, складной стол у окна.
- Одна зона сна, отделённая стеллажом или текстилем.

**A2 / A3** — стилевые решения определяются после получения планов (G6–G8).

**A4 — 107,9 м² — «Дом под крышей»**

- Скаты отделаны белым гипсокартоном **по существующей геометрии**: те же наклоны и те же высоты.
- Видимые деревянные балки допустимы только там, где сейчас проходит конструкция.
- Пол: тёплый дуб. Текстиль: шерсть и лён; палитра — овёс, шалфей, глина.

---

## 2. Промпты ключевых кадров

Формат: **база** · сохранить · промпт (EN) · движение.

### H1-A — кухня-гостиная 136,5 м² (кадры M10, V06, T04, H1-04)
- **База:** IMG_7880.
- **Сохранить:** две колонны, бетонную балку (под отделкой — тот же контур), оконные проёмы, вид на улицу, высоту потолка.
- **Промпт:** `Photorealistic interior photograph, same camera position and lens as the reference, open-plan kitchen-living room in a single-storey brick house, light natural oak engineered floor, warm milk-white plastered walls, columns plastered in wall color, smooth white ceiling with slim track lights, matte milk kitchen fronts with oak, light quartz island near the column, cream linen sofa and boucle armchair, terracotta and olive accents, soft overcast daylight from existing windows, calm European family home, editorial architecture photography, natural colors, no people`
- **Движение:** статично; на монтаже match-dissolve с 7880.

### H1-B — жизненный момент (M11)
- **База:** ключевой кадр H1-A.
- **Промпт:** добавить `a father and a 6-year-old child preparing a snack at the kitchen island, natural candid moment, not looking at camera, soft warm evening light from pendant lamps`.
- **Движение:** I2V, руки двигаются медленно, камера неподвижна.

### H1-C — white box → тот же проект (H1-06)
- **База:** IMG_7853 (реальный white box).
- **Сохранить:** большое окно в сад, дверные проёмы, трековые линии.
- **Промпт:** как H1-A, без кухни: гостиная-зона, тот же диван, тот же пол.

### H1-D — терраса, семейный ужин (H1-09)
- **База:** IMG_7852.
- **Промпт:** `on the existing terrace by the sliding door: a family of four having dinner at a simple oak table, linen tablecloth, warm string lights, overcast late afternoon, pine branches in foreground unchanged, candid`.
- Подпись «Ілюстративна сцена».

### H2-A / H2-C / H2-D — резиденция 173,6 м² (M14, H2-04, H2-06, H2-08)
- **База:** IMG_7887 / IMG_7889 / IMG_7886.
- **Сохранить:** колонны, ряды балок, все проёмы, угловое остекление.
- **Промпт:** `Photorealistic interior, same camera and lens as reference, spacious living area in a brick house, large-format warm grey limestone floor, smoked oak joinery, one natural stone feature wall, slim black metal profiles, linear ceiling lights, low modular greige sofa, one cognac leather lounge chair, calm graphic European modern style, soft daylight from existing windows, no people`.
- Назначение зоны в H2-D (кухня 10,3 м² или студия) уточнить по АР-1/АР-2 до генерации.

### H2-B — друзья за столом (M15)
- **База:** H2-A.
- **Промпт:** добавить `four friends talking at a long oak dining table, relaxed, candid, evening`.

### H3-A / H3-C / H3-D — дуплекс (M18, M19, H3-03, H3-05, H3-07)
- **База:** стоп-кадры из IMG_7864 (после получения видео).
- **Промпт:** `soft minimalism, light lime-plaster walls, pale ash floor, low linen sofa, ceramic objects, airy double-height space if present in reference, linen curtains separating private zone, quiet morning light`.
- H3-C — спальня 2-го уровня. H3-D — терраса 2-го уровня, человек с книгой и пледом. Генерировать только по реальным ракурсам.

### A1-A…A1-D — смарт (M22, V09, A1-04…A1-07)
- **База:** IMG_7865 / IMG_7871 / IMG_7869 / IMG_7872.
- **Сохранить:** размер комнаты, оба окна, **вид за окном (насыпь) без изменений**.
- **Промпт A1-A:** `compact studio apartment 35 m2, same camera, built-in floor-to-ceiling light wood storage, white handleless fronts, sleeping zone separated by an open shelf, small sofa, one person with a coffee cup by the window in the morning, realistic scale, bright and calm`.
- **A1-B:** компактная кухонная линия вдоль стены с выводами (подтвердить по плану).
- **A1-C:** ниша-гардероб у колонны.
- **A1-D:** рабочее место у углового окна, ноутбук, вид на дома.

### A4-A…A4-D — 107,9 м² (M27, A4-04, A4-06…A4-08)
- **База:** IMG_7873 / IMG_7877 / IMG_7878 / IMG_7874.
- **Сохранить:** наклоны и высоты скатов, окна во фронтоне (без мансардных окон в скатах), стальную балку, вентшахты.
- **Промпт A4-A:** `living room under existing sloped roof, slopes finished in smooth white plaster following exact geometry, warm oak floor, oat and sage wool and linen textiles, family reading on a large sofa, soft daylight from gable windows`.
- **A4-B:** спальня под скатом.
- **A4-C:** обеденная зона (уточнить по плану).
- **A4-D:** вечер семьи, настольная игра.

### Люди на территории — M03, M07, M28, M29 (+ V03, V10, TR04, TR06)
- **M03:** IMG_7851. Женщина изнутри открывает раздвижную дверь, тёплый свет за стеклом. Фасад, окна и газон без изменений.
- **M07:** IMG_7858. Пара с коляской пересекает площадь по диагонали, сосед с собакой вдали. Масштаб — по дверям домов на фоне.
- **M28:** IMG_7857. Двое детей 7–9 лет на велосипедах едут по проезду, отец идёт по тротуару, сосед машет у калитки.
- **M29:** IMG_7858. Двое соседей разговаривают на **новой скамейке** в тени платана. Скамейка — предложение благоустройства, поэтому подпись «Концепція благоустрою».

### Благоустройство по схеме — TER-POOL, TER-PLAY, TER-REST (M30–M32, TR08–TR10)
- **Основа:** место по генплану (`assets/plans/skhema_proektiv.png`):
  - бассейн — нижняя часть схемы, между корпусами 62;
  - детская площадка — правее бассейна;
  - спортивная — левый нижний угол;
  - зоны отдыха — центральные полосы между рядами домов.
- После получения фото мест в натуре (G9) генерировать **поверх реального ракурса**.
- **TER-POOL:** `conceptual landscape visualization, modest outdoor family pool with light stone deck, a few loungers and shade sails, young trees, parents sitting next to children at the water, calm, not a resort, located between residential buildings`.
  - Без заявленной геометрии чаши: вид обобщённый.
  - Сезон отличается от осенней съёмки, поэтому кадр идёт отдельным блоком с титром «Концепція благоустрою».
- **TER-PLAY:** `small playground with natural wood play structures and soft surfacing, children playing, parents on a bench nearby`.
- **TER-REST:** `neighbourhood rest area with a long shared wooden table, benches, shade trees, two neighbours playing a board game, soft evening light`.
- **Нельзя:** ставить объекты на проезд, парковку или участок дома; добавлять кафе, клубный дом и другие здания.

### EVE-1 / EVE-2 — вечер (M33, M34, V11)
- **База:** IMG_7851 / IMG_7852.
- **Промпт:** `relight to blue hour, warm 2700K light inside existing windows, soft garden path lights, sky deep blue, geometry and materials unchanged`.
- EVE-2: пара медленно идёт по дорожке.
- Подпись «Візуалізація».
