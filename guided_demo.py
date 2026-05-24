#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
나루토 기술 가이드 데모
  A / D  : 기술 변경
  C      : 초기화
  Q / ESC: 종료
"""

import argparse, csv, time
import cv2 as cv  # type: ignore
import numpy as np  # type: ignore
from PIL import ImageFont, ImageDraw, Image  # type: ignore
from model.yolox.yolox_onnx import YoloxONNX  # type: ignore

SIGN_IMG_DIR = 'setting/sign_images'
GUIDE_W = 260

SIGN_IMG_MAP = {
    1:  '1_Ne.jpg',
    2:  '2_Ushi.jpg',
    3:  '3_Tora.jpg',
    4:  '4_U.jpg',
    5:  '5_Tatsu.jpg',
    6:  '6_Mi.jpg',
    7:  '7_Uma.jpg',
    8:  '8_Hitsuji.jpg',
    9:  '9_Saru.jpg',
    10: '10_Tori.jpg',
    11: '11_Inu.jpg',
    12: '12_I.jpg',
    13: '13_Gassho.jpg',
    15: '15_Mizunoe.jpg',
}

KR = {
    1:'쥐', 2:'소', 3:'호랑이', 4:'토끼', 5:'용',
    6:'뱀', 7:'말', 8:'양', 9:'원숭이', 10:'닭',
    11:'개', 12:'멧돼지', 13:'합장', 15:'임'
}

JUTSU_DESC = {
    '分身の術':        ['분신의 술', '자신과 똑같은 분신을', '만들어내는 기술.', '나루토 단골 기술!'],
    '変わり身の術':    ['변신의 술', '순간적으로 다른 물체와', '위치를 바꿔 공격을', '피하는 기술.'],
    '口寄せの術':      ['소환의 술', '두루마리에 계약한', '생물을 소환하는 기술.'],
    '豪火球の術':      ['화둔·호화구슬의 술', '입에서 거대한 불덩어리를', '발사하는 기술.', '우치하 일족의 기본기!'],
    '鳳仙花の術':      ['화둔·봉선화의 술', '여러 개의 작은 불덩이를', '동시에 발사하는 기술.'],
    '龍火の術':        ['화둔·용화의 술', '용 모양의 불꽃을', '발사하는 기술.'],
    '火龍炎弾の術':    ['화둔·화룡염탄의 술', '용 모양 거대 불꽃을', '발사하는 기술.'],
    '水乱破の術':      ['수둔·수란파의 술', '입에서 물을 발사해', '상대를 공격하는 기술.'],
    '水鮫弾の術':      ['수둔·수상어탄의 술', '물로 상어를 만들어', '적에게 돌진시키는 기술.'],
    '水龍弾の術':      ['수둔·수룡탄의 술', '거대한 물 용을 만들어', '공격하는 기술.', '인이 무려 44개!'],
    '屍鬼封尽の術':    ['봉인술·사귀봉진의 술', '죽음의 신을 불러 적의', '영혼을 봉인하는 기술.', '쓰면 사용자도 죽음...'],
    '口寄せ 穢土転生の術': ['소환술·예토전생', '죽은 자를 불러내는', '금지된 술.'],
    '口寄せ 土遁追牙の術': ['소환·토둔 추아의 술', '땅속에서 개들이', '적을 추격하는 기술.'],
}

# ── PIL 한글 폰트 헬퍼 ────────────────────────────────────────
_font_cache = {}

def _font(size):
    if size not in _font_cache:
        for path in [
            'C:/Windows/Fonts/malgun.ttf',
            'C:/Windows/Fonts/gulim.ttc',
            'C:/Windows/Fonts/batang.ttc',
        ]:
            try:
                _font_cache[size] = ImageFont.truetype(path, size)
                break
            except OSError:
                pass
        else:
            _font_cache[size] = ImageFont.load_default()
    return _font_cache[size]


def _text_w(text, size):
    bb = _font(size).getbbox(text)
    return bb[2] - bb[0]


def put_kr(img, text, xy, size, color_bgr):
    """BGR numpy 배열에 한글 텍스트를 그린다 (in-place)."""
    pil = Image.fromarray(cv.cvtColor(img, cv.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil)
    r, g, b = color_bgr[2], color_bgr[1], color_bgr[0]
    draw.text(xy, text, font=_font(size), fill=(r, g, b))
    img[:] = cv.cvtColor(np.array(pil), cv.COLOR_RGB2BGR)


# ─────────────────────────────────────────────────────────────

def _fade(elapsed, total=4.0, ramp=0.3):
    if elapsed < ramp:
        return elapsed / ramp
    elif elapsed < total - ramp:
        return 1.0
    else:
        return max(0.0, (total - elapsed) / ramp)


def _draw_text_effect(frame, text, cx, cy, fade, color=(0, 220, 255)):
    sz = 62
    tw = _text_w(text, sz)
    tx, ty = cx - tw // 2, cy - 36
    for dx, dy in [(-3,-3),(3,-3),(-3,3),(3,3),(0,-4),(0,4)]:
        put_kr(frame, text, (tx+dx, ty+dy), sz, (0,0,0))
    put_kr(frame, text, (tx, ty), sz, color)


# ── 화둔 공통 ─ 입에서 불 뿜기 ────────────────────────────────
# ── 수둔 공통 ─ 양쪽 파도가 밀려와 중앙 충돌 ─────────────────
def _effect_sudun(frame, elapsed, jutsu_kr):
    h, w = frame.shape[:2]
    fade = _fade(elapsed)
    cx, cy = w // 2, h // 2

    # 파도 진행: 1.8초에 걸쳐 양쪽에서 중앙으로
    progress = min(1.0, elapsed / 1.8)

    def wave_surface(origin_x, direction, amplitude, freq, phase):
        """origin_x 에서 direction 방향으로 진행하는 파도 표면 포인트 반환"""
        reach = int(progress * (w // 2 + 60)) * direction
        pts = []
        for xi in range(0, w + 4, 4):
            offset = xi - origin_x
            envelope = max(0.0, 1.0 - abs(offset - reach) / max(1, abs(reach) + 1))
            y = int(cy
                    + amplitude * np.sin(xi / w * freq * np.pi + phase + elapsed * 5) * envelope
                    + amplitude * 0.4 * np.sin(xi / w * (freq * 1.8) * np.pi - elapsed * 3.5) * envelope)
            pts.append((xi, y))
        return pts

    water_layer = np.zeros_like(frame)

    # 파도 3겹 (깊이감)
    configs = [
        (0,   1, 140, 3.5, 0.0,  (200, 100,  10)),   # 좌 - 깊은 파랑
        (w,  -1, 140, 3.5, 1.2,  (200, 100,  10)),   # 우 - 깊은 파랑
        (0,   1,  90, 5.0, 0.5,  (240, 160,  40)),   # 좌 - 밝은 레이어
        (w,  -1,  90, 5.0, 1.8,  (240, 160,  40)),   # 우 - 밝은 레이어
    ]
    for ox, dr, amp, fr, ph, col in configs:
        pts = wave_surface(ox, dr, amp, fr, ph)
        fill = pts + [(w, h), (0, h)]
        cv.fillPoly(water_layer, [np.array(fill, np.int32)], col)

    # bloom additive
    k = 61
    blurred = cv.GaussianBlur(water_layer, (k, k), 20)
    tmp = frame.astype(np.int32) + blurred.astype(np.int32)
    frame[:] = np.clip(tmp, 0, 255).astype(np.uint8)

    # 파도 표면 흰 거품선
    for ox, dr, amp, fr, ph, _ in configs[:2]:
        pts = wave_surface(ox, dr, amp, fr, ph)
        for i in range(len(pts) - 1):
            cv.line(frame, pts[i], pts[i + 1],
                    (int(200 * fade), int(230 * fade), int(255 * fade)), 2, cv.LINE_AA)

    # 충돌 지점 물보라 (진행 80% 이후)
    if progress > 0.8:
        splash_t = (progress - 0.8) / 0.2
        rng = np.random.default_rng(int(elapsed * 35))
        n = 200
        angles = rng.uniform(-np.pi * 0.9, np.pi * 0.9 + np.pi * 0.0, n)  # 위 반구
        speeds = rng.uniform(80, 400, n)
        lives  = rng.random(n)
        spray_layer = np.zeros_like(frame)
        for j in range(n):
            t = (splash_t * 0.8 + lives[j]) % 1.0
            px = int(cx + np.sin(angles[j]) * speeds[j] * t)
            py = int(cy + np.cos(angles[j]) * speeds[j] * t - 200 * t)
            if not (0 <= px < w and 0 <= py < h):
                continue
            sz = max(2, int((1 - t) * 14 * fade))
            v  = int((1 - t) * 220 * fade)
            cv.circle(spray_layer, (px, py), sz, (v, int(v * 0.7), int(v * 0.3)), -1, cv.LINE_AA)
        k2 = 31
        bl2 = cv.GaussianBlur(spray_layer, (k2, k2), 12)
        tmp2 = frame.astype(np.int32) + bl2.astype(np.int32)
        frame[:] = np.clip(tmp2, 0, 255).astype(np.uint8)

    _draw_text_effect(frame, jutsu_kr + '!', cx, cy - 160, fade, color=(255, 230, 80))


def _effect_hwadun(frame, elapsed, jutsu_kr):
    h, w = frame.shape[:2]
    fade = _fade(elapsed)
    cx = w // 2
    mouth_y = int(h * 0.62)

    rng = np.random.default_rng(int(elapsed * 40))
    n = 300

    # 각 파티클: 입에서 부채꼴로 퍼져나감
    angles = rng.uniform(-0.55, 0.55, n)   # 라디안, 위쪽 방향 기준
    speeds = rng.uniform(180, 520, n)
    life   = rng.random(n)

    fire_layer = np.zeros_like(frame)
    for j in range(n):
        t = (elapsed * 0.6 + life[j]) % 1.0
        dx = np.sin(angles[j]) * speeds[j] * t
        dy = -np.cos(angles[j]) * speeds[j] * t  # 위로
        px = int(cx + dx)
        py = int(mouth_y + dy)
        if not (0 <= px < w and 0 <= py < h):
            continue
        sz  = max(2, int((1 - t) * 28 * fade))
        r_v = int((1 - t * 0.7) * 240 * fade)
        g_v = int(r_v * max(0.0, 0.6 - t))
        cv.circle(fire_layer, (px, py), sz, (0, g_v, r_v), -1, cv.LINE_AA)

    # bloom
    k = 89
    blurred = cv.GaussianBlur(fire_layer, (k, k), 22)
    tmp = frame.astype(np.int32) + blurred.astype(np.int32)
    frame[:] = np.clip(tmp, 0, 255).astype(np.uint8)

    # 밝은 코어
    for j in range(n // 3):
        t = (elapsed * 0.6 + life[j]) % 1.0
        dx = np.sin(angles[j]) * speeds[j] * t * 0.5
        dy = -np.cos(angles[j]) * speeds[j] * t * 0.5
        px = int(cx + dx)
        py = int(mouth_y + dy)
        if not (0 <= px < w and 0 <= py < h):
            continue
        sz2 = max(1, int((1 - t) * 8 * fade))
        wh  = int((1 - t) * 255 * fade)
        cv.circle(frame, (px, py), sz2, (int(wh * 0.3), int(wh * 0.85), wh), -1, cv.LINE_AA)

    # 입 발광
    m_layer = np.zeros_like(frame)
    cv.circle(m_layer, (cx, mouth_y), int(60 * fade), (0, 100, 255), -1)
    k2 = max(3, int(30 * 4) | 1)
    blurred2 = cv.GaussianBlur(m_layer, (k2, k2), 30)
    tmp2 = frame.astype(np.int32) + blurred2.astype(np.int32)
    frame[:] = np.clip(tmp2, 0, 255).astype(np.uint8)
    cv.circle(frame, (cx, mouth_y), max(1, int(18 * fade)), (100, 200, 255), -1)

    _draw_text_effect(frame, jutsu_kr + '!', cx, mouth_y - 220, fade, color=(0, 120, 255))


# ── 소환·토둔 추아의 술 ─ 흙 벽이 아래서 솟아오름 ───────────
def _effect_chuuga(frame, elapsed, jutsu_kr):
    h, w = frame.shape[:2]
    fade = _fade(elapsed)

    rise = min(1.0, elapsed / 1.2)
    wall_h = int(rise * h * 0.85)
    if wall_h <= 0:
        _draw_text_effect(frame, jutsu_kr + '!', w // 2, h // 2, fade, color=(80, 150, 200))
        return

    wall_top = h - wall_h
    wall_x = w // 2 - int(w * 0.38)
    wall_w = int(w * 0.76)

    overlay = np.zeros((h, w, 3), np.uint8)

    # 블록 패턴
    bw, bh = 72, 44
    rng = np.random.default_rng(7)
    for ri in range(h // bh + 2):
        by1 = h - (ri + 1) * bh
        by2 = by1 + bh - 3
        if by2 < wall_top:
            break
        offset = (ri % 2) * (bw // 2)
        for ci in range(-1, wall_w // bw + 2):
            bx1 = wall_x + ci * bw - offset
            bx2 = bx1 + bw - 3
            x1 = max(bx1, wall_x); x2 = min(bx2, wall_x + wall_w)
            y1 = max(by1, wall_top); y2 = min(by2, h - 1)
            if x2 <= x1 or y2 <= y1:
                continue
            base = int(rng.integers(55, 105))
            col = (int(base * 0.45), int(base * 0.65), base)
            cv.rectangle(overlay, (x1, y1), (x2, y2), col, -1)
            dark = (int(base * 0.2), int(base * 0.3), int(base * 0.45))
            cv.rectangle(overlay, (x1, y1), (x2, y2), dark, 2)
            # 균열 선
            if rng.random() < 0.3:
                cx1 = rng.integers(x1, x2)
                cy1 = rng.integers(y1, y2)
                cx2 = int(cx1 + rng.integers(-18, 18))
                cy2 = int(cy1 + rng.integers(-10, 10))
                cv.line(overlay, (int(cx1), int(cy1)), (int(cx2), int(cy2)), dark, 1)

    # 상단 가장자리 강조 (솟는 느낌)
    cv.rectangle(overlay, (wall_x, wall_top), (wall_x + wall_w, wall_top + 6), (60, 100, 150), -1)

    cv.addWeighted(overlay, fade, frame, 1.0, 0, dst=frame)

    # 먼지 파티클 (솟는 가장자리에서)
    dust_rng = np.random.default_rng(int(elapsed * 20))
    n = 80
    dust_x = dust_rng.integers(wall_x, wall_x + wall_w, n)
    dust_vy = dust_rng.uniform(60, 200, n)
    dust_life = dust_rng.random(n)
    for j in range(n):
        t = (elapsed * 0.6 + dust_life[j]) % 1.0
        px = int(dust_x[j] + dust_rng.integers(-30, 30))
        py = int(wall_top - dust_vy[j] * t)
        if not (0 <= px < w and 0 <= py < h):
            continue
        sz = max(2, int((1 - t) * 10))
        alpha_v = int((1 - t) * 160 * fade)
        col = (int(alpha_v * 0.5), int(alpha_v * 0.7), alpha_v)
        cv.circle(frame, (px, py), sz, col, -1, cv.LINE_AA)

    _draw_text_effect(frame, jutsu_kr + '!', w // 2, max(30, wall_top - 50), fade, color=(80, 170, 230))


# ── 분신의 술 ─ 화면을 격자로 분신 복제 ──────────────────────
def _effect_bunsin(frame, elapsed, jutsu_kr):
    h, w = frame.shape[:2]
    fade = _fade(elapsed)
    original = frame.copy()

    cols, rows = 4, 3
    sw, sh = w // cols, h // rows
    tiled = np.zeros_like(frame)
    small = cv.resize(original, (sw, sh))
    for r in range(rows):
        for c in range(cols):
            tiled[r*sh:(r+1)*sh, c*sw:(c+1)*sw] = small

    alpha = min(1.0, fade)
    cv.addWeighted(tiled, alpha, frame, 1.0 - alpha, 0, dst=frame)
    _draw_text_effect(frame, jutsu_kr + '!', w // 2, h // 2, fade, color=(255, 210, 50))


# ── 효과 디스패처 ─────────────────────────────────────────────
def draw_success_effect(frame, elapsed, jutsu_kr):
    h, w = frame.shape[:2]
    fade = _fade(elapsed)
    if '분신' in jutsu_kr:
        _effect_bunsin(frame, elapsed, jutsu_kr)
    elif '추아' in jutsu_kr:
        _effect_chuuga(frame, elapsed, jutsu_kr)
    elif '수둔' in jutsu_kr:
        _effect_sudun(frame, elapsed, jutsu_kr)
    elif '화둔' in jutsu_kr:
        _effect_hwadun(frame, elapsed, jutsu_kr)


def load_imgs():
    imgs = {}
    for idx, fname in SIGN_IMG_MAP.items():
        img = cv.imread(f'{SIGN_IMG_DIR}/{fname}')
        if img is not None:
            imgs[idx] = img
    return imgs


def jp_to_idx(ch, labels):
    for i, row in enumerate(labels):
        if row[1] == ch:
            return i
    return -1


EXCLUDED_SIGNS = {12, 13, 15}  # 멧돼지, 합장, 임
SIGN_SCORE_TH = {4: 0.07, 2: 0.12, 8: 0.12}  # 토끼/소/양 낮게

def load_jutsu(labels, valid_imgs):
    out = []
    with open('setting/jutsu.csv', encoding='utf-8-sig') as f:
        for row in csv.reader(f):
            if not any(row):
                continue
            name = row[2] if row[2] else row[3]
            ids = [jp_to_idx(s, labels) for s in row[4:] if s]
            ids = [i for i in ids if i > 0]
            allowed = ('分身', '火遁', '水遁', '土遁')
            if ids and not any(i in EXCLUDED_SIGNS for i in ids) and any(k in name for k in allowed):
                out.append({'name': name, 'signs': ids})
    return out


def make_guide_panel(sign_imgs, jutsu, step, h):
    panel = np.zeros((h, GUIDE_W, 3), np.uint8)
    panel[:] = (15, 15, 15)

    signs = jutsu['signs']
    n = len(signs)
    desc = JUTSU_DESC.get(jutsu['name'], [jutsu['name']])

    # ── 기술 이름 헤더 ─────────────────────────────────────
    cv.rectangle(panel, (0, 0), (GUIDE_W, 44), (30, 30, 30), -1)
    put_kr(panel, desc[0], (10, 8), 22, (50, 200, 255))

    # ── 현재 따라할 손동작 (크게) ──────────────────────────
    big = 180
    bx = (GUIDE_W - big) // 2
    by = 50

    if step < n:
        sid = signs[step]
        src = sign_imgs.get(sid)
        tile = cv.resize(src, (big, big)) if src is not None else np.full((big, big, 3), 40, np.uint8)
        blink = int(time.time() * 2.5) % 2 == 0
        col = (0, 230, 255) if blink else (0, 130, 180)
        cv.rectangle(tile, (0, 0), (big-1, big-1), col, 5)
        panel[by:by+big, bx:bx+big] = tile

        kr = KR.get(sid, '?')
        tw = _text_w(kr, 30)
        put_kr(panel, kr, ((GUIDE_W - tw) // 2, by + big + 4), 30, (255, 230, 0))
        cv.putText(panel, f'{step+1} / {n}', (10, by + big + 52),
                   cv.FONT_HERSHEY_SIMPLEX, 0.48, (120, 120, 120), 1)
    else:
        cv.putText(panel, 'DONE!', (bx + 20, by + big // 2),
                   cv.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 120), 3)

    # ── 기술 설명 ──────────────────────────────────────────
    desc_y = by + big + 60
    for line in desc[1:]:
        put_kr(panel, line, (8, desc_y), 15, (160, 200, 160))
        desc_y += 19

    # ── 하단: 전체 순서 썸네일 ─────────────────────────────
    thumb = 44
    pad = 4
    cols = GUIDE_W // (thumb + pad)
    seq_y = by + big + 130

    for i, sid in enumerate(signs):
        col_i = i % cols
        row_i = i // cols
        tx = pad + col_i * (thumb + pad)
        ty = seq_y + row_i * (thumb + pad + 18)
        if ty + thumb > h:
            break

        src = sign_imgs.get(sid)
        t = cv.resize(src, (thumb, thumb)) if src is not None else np.full((thumb, thumb, 3), 40, np.uint8)

        if i < step:
            green = np.zeros_like(t); green[:, :, 1] = 80
            t = cv.addWeighted(t, 0.4, green, 0.6, 0)
            cv.rectangle(t, (0, 0), (thumb-1, thumb-1), (0, 200, 80), 2)
        elif i == step:
            blink = int(time.time() * 2.5) % 2 == 0
            cv.rectangle(t, (0, 0), (thumb-1, thumb-1), (0, 230, 255) if blink else (0, 120, 170), 3)
        else:
            t = (t * 0.35).astype(np.uint8)
            cv.rectangle(t, (0, 0), (thumb-1, thumb-1), (50, 50, 50), 1)

        panel[ty:ty+thumb, tx:tx+thumb] = t

        kr = KR.get(sid, '?')
        put_kr(panel, kr, (tx, ty + thumb + 2), 13, (160, 160, 160))

    return panel


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--device", type=int, default=0)
    p.add_argument("--width", type=int, default=960)
    p.add_argument("--height", type=int, default=540)
    p.add_argument("--file", type=str, default=None)
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--model", type=str, default='model/yolox/yolox_nano.onnx')
    p.add_argument("--score_th", type=float, default=0.15)
    p.add_argument("--sign_interval", type=float, default=12.0)
    p.add_argument("--jutsu", type=int, default=2)
    args = p.parse_args()

    if args.file:
        cap = cv.VideoCapture(args.file)
    else:
        cap = cv.VideoCapture(args.device, cv.CAP_DSHOW)
    cap.set(cv.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, args.height)

    yolox = YoloxONNX(
        model_path=args.model,
        input_shape=(416, 416),
        class_score_th=args.score_th,
        nms_th=0.45,
        nms_score_th=0.1,
    )

    with open('setting/labels.csv', encoding='utf-8-sig') as f:
        labels = [row for row in csv.reader(f)]

    sign_imgs = load_imgs()
    jutsu_list = load_jutsu(labels, sign_imgs)

    bunsin_idx = next((i for i, j in enumerate(jutsu_list) if '分身' in j['name']), 0)
    jutsu_idx = bunsin_idx
    step = 0
    last_sign_time = time.time()
    last_detected = -1
    success_time = None

    print(f"기술 {len(jutsu_list)}개 로드 완료. A/D 키로 변경")

    while True:
        t0 = time.time()
        ret, frame = cap.read()
        if not ret or frame is None:
            time.sleep(0.03)
            continue

        h, w = frame.shape[:2]
        bboxes, scores, class_ids = yolox.inference(frame)

        jutsu = jutsu_list[jutsu_idx]
        signs = jutsu['signs']

        # 인 감지
        for _, score, cid in zip(bboxes, scores, class_ids):
            did = int(cid) + 1
            th = SIGN_SCORE_TH.get(did, args.score_th)
            if score < th:
                continue
            if did == last_detected:
                continue
            last_detected = did
            last_sign_time = time.time()
            if step < len(signs) and did == signs[step]:
                step += 1
                if step == len(signs):
                    success_time = time.time()
                    step = 0

        if (time.time() - last_sign_time) > args.sign_interval and step > 0:
            step = 0
            last_detected = -1

        # 바운딩박스
        for bbox, score, cid in zip(bboxes, scores, class_ids):
            if score < args.score_th:
                continue
            cid2 = int(cid) + 1
            x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
            cv.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 3)
            cv.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 1)
            label = f"{KR.get(cid2, '?')} {score*100:.0f}%"
            put_kr(frame, label, (x1, max(0, y1 - 32)), 26, (255, 200, 0))

        # 성공 이펙트 + 자동 다음 기술 넘어가기
        if success_time:
            elapsed = time.time() - success_time
            if elapsed < 4.0:
                kr_name = JUTSU_DESC.get(jutsu['name'], [jutsu['name']])[0]
                draw_success_effect(frame, elapsed, kr_name)
            elif elapsed >= 4.0:
                jutsu_idx = (jutsu_idx + 1) % len(jutsu_list)
                success_time = None
                last_detected = -1

        # 조작키 안내
        put_kr(frame, '[A/D] 기술변경  [C] 초기화  [Q] 종료', (10, 6), 18, (160, 160, 160))

        # 가이드 패널 생성 후 오른쪽에 붙이기
        guide = make_guide_panel(sign_imgs, jutsu, step, h)
        canvas = np.hstack([frame, guide])

        cv.imshow('NARUTO Hand Sign Guide', canvas)

        key = cv.waitKeyEx(1)
        if key in (ord('q'), 27):
            break
        elif key in (ord('c'), ord('C')):
            step = 0; last_detected = -1
        elif key in (ord('a'), ord('A'), 0x250000):
            jutsu_idx = (jutsu_idx - 1) % len(jutsu_list)
            step = 0; last_detected = -1
        elif key in (ord('d'), ord('D'), 0x270000):
            jutsu_idx = (jutsu_idx + 1) % len(jutsu_list)
            step = 0; last_detected = -1

        time.sleep(max(0, 1/args.fps - (time.time() - t0)))

    cap.release()
    cv.destroyAllWindows()


if __name__ == '__main__':
    main()
