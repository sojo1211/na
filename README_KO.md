# NARUTO-HandSignDetection

물체 감지를 이용해 나루토의 인(手印)을 감지하는 모델과 샘플 프로그램입니다.

<div align="left">
<img src="https://user-images.githubusercontent.com/37477845/95489944-78d5ed00-09d2-11eb-96f6-a687b012c413.gif" width="45%">　<img src="https://user-images.githubusercontent.com/37477845/95645297-97360880-0af8-11eb-9134-d92cbfb5fe42.gif" width="40%">
</div>

---

# 제목
딥 사륜안: 물체 감지 YOLOX를 이용한 나루토 인(手印) 인식

# 개요
이 저장소는 나루토의 인을 인식하기 위한 **학습된 모델**과 샘플 프로그램을 공개하고 있습니다.

기술을 발동하려면 일부 기술을 제외하고 손으로 인을 맺는 것이 필요합니다.
또한 성질 변화는 인에 특징이 나타나기 때문에 (화둔→호랑이 인, 토둔→멧돼지 인 등),
인을 빠르게 인식할 수 있다면 닌자 간의 전투에서 유리해질 수 있습니다.
인 인식에는 딥러닝 물체 감지 모델 중 하나인 **YOLOX-Nano**를 사용하여,
이전 버전의 딥 사륜안(EfficientDet-D0 사용)보다 추론 속도를 대폭 향상시켰습니다.

---

# 필요 패키지
* onnxruntime 1.10.0 이상
* OpenCV 3.4.2 이상
* Pillow 6.1.0 이상 (Ninjutsu_demo.py 실행 시에만)
* Tensorflow 2.3.0 이상 (SSD, EfficientDet 실행 시 또는 후처리를 ONNX로 병합할 때만)

---

# 데이터셋
### 데이터셋에 대해
데이터셋은 비공개입니다 (학습된 모델은 공개).

인터넷에서 수집한 이미지, 직접 촬영한 이미지 외에 [naruto-hand-sign-dataset](https://www.kaggle.com/vikranthkanumuru/naruto-hand-sign-dataset)을 활용하였습니다.

### 인식 가능한 인의 종류
**14종류** (子~亥, 壬, 合掌)의 인에 대응합니다.

<table>
	<tbody>
		<tr>
			<td width="25%">子(Ne/쥐)</td>
			<td width="25%">丑(Ushi/소)</td>
			<td width="25%">寅(Tora/호랑이)</td>
			<td width="25%">卯(U/토끼)</td>
		</tr>
		<tr>
			<td><img src="https://user-images.githubusercontent.com/37477845/95611897-6d032d00-0a9d-11eb-86c4-de1c50c0d7b6.jpg" width="100%"></td>
			<td><img src="https://user-images.githubusercontent.com/37477845/95611906-6ffe1d80-0a9d-11eb-9054-4e68c42e52ca.jpg" width="100%"></td>
			<td><img src="https://user-images.githubusercontent.com/37477845/95611912-712f4a80-0a9d-11eb-8cb8-fc7097e16f60.jpg" width="100%"></td>
			<td><img src="https://user-images.githubusercontent.com/37477845/95611915-72607780-0a9d-11eb-9995-66524ce4f978.jpg" width="100%"></td>
		</tr>
	</tbody>
</table>
<table>
	<tbody>
		<tr>
			<td width="25%">辰(Tatsu/용)</td>
			<td width="25%">巳(Mi/뱀)</td>
			<td width="25%">午(Uma/말)</td>
			<td width="25%">未(Hitsuji/양)</td>
		</tr>
		<tr>
			<td><img src="https://user-images.githubusercontent.com/37477845/95611920-7391a480-0a9d-11eb-8e74-db39acf90f83.jpg" width="100%"></td>
			<td><img src="https://user-images.githubusercontent.com/37477845/95611922-742a3b00-0a9d-11eb-8a21-8bdf207db9bb.jpg" width="100%"></td>
			<td><img src="https://user-images.githubusercontent.com/37477845/95611928-755b6800-0a9d-11eb-86c0-67605ffd6e9b.jpg" width="100%"></td>
			<td><img src="https://user-images.githubusercontent.com/37477845/95611930-768c9500-0a9d-11eb-81c6-067b632dc43d.jpg" width="100%"></td>
		</tr>
	</tbody>
</table>
<table>
	<tbody>
		<tr>
			<td width="25%">申(Saru/원숭이)</td>
			<td width="25%">酉(Tori/닭)</td>
			<td width="25%">戌(Inu/개)</td>
			<td width="25%">亥(I/멧돼지)</td>
		</tr>
		<tr>
			<td><img src="https://user-images.githubusercontent.com/37477845/95611931-77252b80-0a9d-11eb-97d6-e3efc6f1aac3.jpg" width="100%"></td>
			<td><img src="https://user-images.githubusercontent.com/37477845/95611935-77bdc200-0a9d-11eb-95e1-feb8bf7f61de.jpg" width="100%"></td>
			<td><img src="https://user-images.githubusercontent.com/37477845/95611936-78eeef00-0a9d-11eb-90b3-f565e4763c50.jpg" width="100%"></td>
			<td><img src="https://user-images.githubusercontent.com/37477845/95611938-7a201c00-0a9d-11eb-9df0-3ddd06703c55.jpg" width="100%"></td>
		</tr>
	</tbody>
</table>
<table>
	<tbody>
		<tr>
			<td width="25%">壬(Mizunoe)</td>
			<td width="25%">合掌(합장)</td>
		</tr>
		<tr>
			<td><img src="https://user-images.githubusercontent.com/37477845/95611947-7c827600-0a9d-11eb-97ae-9d7eabc58cd5.jpg" width="100%"></td>
			<td><img src="https://user-images.githubusercontent.com/37477845/95611943-7b514900-0a9d-11eb-97be-4fda80d17879.jpg" width="100%"></td>
		</tr>
	</tbody>
</table>

### 데이터셋 규모
* 총 이미지 수: 10,026장 (애니메이션 이미지: 2,651장)
* 라벨링 완료: 7,098장
* 라벨링 미완료: 2,928장
* 어노테이션 박스 수: 8,941개

---

# 학습된 모델
학습된 모델은 `model` 디렉토리에 포함되어 있습니다.
* **YOLOX-Nano** (`model/yolox/yolox_nano.onnx`)

---

# 디렉토리 구조
```
│  simple_demo.py
│  Ninjutsu_demo.py
│
├─model
│  └─yolox
│      │ yolox_nano.onnx
│      └─yolox_onnx.py
│
├─post_process_gen_tools
│
├─setting
│  ├─labels.csv      ← 인의 라벨 이름
│  └─jutsu.csv       ← 기술 이름 및 필요 인 목록
│
└─utils
```

---

# 실행 방법

## 패키지 설치
```bash
pip install onnxruntime opencv-python Pillow
```

## 데모 실행
```bash
python simple_demo.py          # 단순 인식 데모
python Ninjutsu_demo.py        # 기술 판정 데모
```

## 데모 설명

### simple_demo.py
웹캠으로 인(手印)을 실시간 감지하는 단순 데모입니다.

### Ninjutsu_demo.py
기술 판정 데모입니다. 인의 입력 순서를 기억하여 `jutsu.csv`에 등록된 기술 이름을 화면에 표시합니다.

## 실행 옵션

<details>
<summary>옵션 목록 펼치기</summary>

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--device` | 카메라 장치 번호 | 0 |
| `--file` | 동영상 파일 경로 (지정 시 카메라 대신 사용) | None |
| `--fps` | 처리 FPS | 30 |
| `--width` | 카메라 캡처 가로 크기 | 960 |
| `--height` | 카메라 캡처 세로 크기 | 540 |
| `--skip_frame` | 몇 프레임마다 처리할지 | 0 |
| `--model` | 모델 파일 경로 | model/yolox/yolox_nano.onnx |
| `--input_shape` | 모델 입력 크기 | 416,416 |
| `--score_th` | 클래스 판별 임계값 | 0.7 |
| `--nms_th` | NMS 임계값 | 0.45 |
| `--nms_score_th` | NMS 스코어 임계값 | 0.1 |
| `--sign_interval` | 이전 인 감지 후 지정 시간(초) 경과 시 인 기록 초기화 *(Ninjutsu_demo만)* | 2.0 |
| `--jutsu_display_time` | 기술 성립 시 기술 이름 표시 시간(초) *(Ninjutsu_demo만)* | 5 |
| `--use_display_score` | 인 감지 스코어 표시 여부 *(Ninjutsu_demo만)* | False |
| `--erase_bbox` | 바운딩 박스 표시 제거 여부 *(Ninjutsu_demo만)* | False |
| `--use_jutsu_lang_en` | 기술 이름 영어 표기 사용 여부 *(Ninjutsu_demo만)* | False |
| `--chattering_check` | 몇 번 연속 감지해야 인 성립으로 인정할지 *(Ninjutsu_demo만)* | 1 |
| `--use_fullscreen` | 전체화면 표시 사용 여부 (실험적 기능) *(Ninjutsu_demo만)* | False |

</details>

---

# 활용 사례
* [제15회 UE4 쁘치콘 「인(印) VADERS」](https://www.youtube.com/watch?v=K4-E5SseVtI)

---

# 라이선스
NARUTO-HandSignDetection은 [MIT 라이선스](https://en.wikipedia.org/wiki/MIT_License)를 따릅니다.

# 폰트 라이선스
衡山毛筆フォント (https://opentype.jp/kouzanmouhitufont.htm)

# 제작자
Kazuhito Takahashi (https://twitter.com/KzhtTkhs)
