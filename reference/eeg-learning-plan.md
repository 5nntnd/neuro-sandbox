# Learning Brain Activity from Public EEG Data

Standalone base document for a new project. Cost: $0. No hardware, no implants, no purchases.

## Scope

**In:** use public, already-recorded EEG datasets to learn how brain signals look and how to classify mental states with Python.
**Out:** buying hardware, recording your own data, real-time systems, phone apps, any invasive work.

**Background goal:** test whether differences in imagined mental activity (including imagined vowels such as "A" vs "I") can be detected from brain signals. Start with the best-documented task, imagined hand movement, then try imagined speech data as a stretch.

## Setup (one evening)

- Python 3.10+ in a virtual environment, or free Google Colab.
- Install `mne`, `scikit-learn`, `numpy`, `matplotlib`; later `torch` and `moabb`.
- Keep one folder per dataset and one notebook per experiment.

## Public data to use

- **PhysioNet EEG Motor Movement/Imagery:** 109 subjects, 64 channels. Best first dataset. MNE downloads it for you (`mne.datasets.eegbci`).
- **BCI Competition IV (2a, 2b):** classic motor-imagery benchmark, good for comparing with published results.
- **MOABB:** Python library that loads many BCI datasets with one interface and fair evaluation.
- **OpenNeuro:** large open repository of EEG and other neuroimaging datasets.
- **Imagined-speech EEG sets:** public datasets exist (for example Kara One). Check each one's license, number of subjects and tasks before use.

## Week 0: see the noise (one evening)

Goal: feel how noisy accuracy is with about 45 trials before you trust any number. Background in `blindspots.md`.

- [ ] Create a virtual environment and run `pip install -r requirements.txt`.
- [ ] Run `python experiments/week0_noise_check.py`. It downloads runs 4, 8 and 12 for 10 subjects into the gitignored `data/` folder.
- [ ] Open `results/week0_noise_check.png` (the table is in the matching `.txt`). Panel A shows what chance accuracy looks like when the labels are shuffled, against the real result. Panel B shows every subject's accuracy with a 95% confidence interval, the accuracy needed to beat chance, and the score from plain shuffled cross-validation for comparison.
- [x] Write one sentence: how much accuracy would you need before believing a single subject's result? *At 45 trials, at least about 64% under run-wise CV with a permutation p < 0.05; a single 62% (p = 0.065) is not enough.*

## Four-week workflow

1. **Week 1:** load the data, plot raw EEG, mark blinks and muscle noise, understand channels, sampling rate and events.
   - [x] Mark artifacts, try ICA, and note line-noise filtering (50/60 Hz) and the reference used. Done: blinks marked by eye, ICA as diagnostic only, 60 Hz mains varies by subject, reference undocumented (see `datasets.md`, `hypothesis.md`).
   - [x] Check the dataset's license and citation terms. Keep data only in gitignored folders. Done in `datasets.md`.
   - [x] Write the hypothesis and what result would count as "not detected" before looking at any classifier output. Done in `hypothesis.md`.
2. **Week 2:** band-pass filter (8-30 Hz for motor imagery), cut epochs around events, view average band power.
   - [x] Fix the filter band and time window now and write them down, so you don't tune them on the test results. Done in `hypothesis.md`.
   - [ ] Plot band power over C3 and C4 for left vs right imagery to see the mu/beta effect itself.
3. **Week 3:** features (band power, CSP) plus a simple classifier (LDA). Cross-validate and report accuracy per subject.
   - [ ] Use run-wise or subject-wise cross-validation, not shuffled trials (PhysioNet has one session per subject).
   - [ ] Keep CSP and any other fitted step inside the cross-validation pipeline.
   - [ ] Report a confidence interval, a permutation p-value and Cohen's kappa for every subject, not just the best one.
   - [ ] Look at which channels and frequencies drive the classifier, to rule out eye and muscle artifacts.
4. **Week 4:** try a small neural net (EEGNet) and compare with the simple model. Write up what worked and what didn't.
   - [ ] EEGNet on about 45 trials will overfit. Use BCI IV 2a or pool subjects, and compare it with LDA under the same cross-validation.
   - [ ] Pin library versions, set seeds, and make the notebook run top to bottom. Strip outputs before committing.
   - [ ] For the imagined-speech stretch, check which prompts the dataset really contains (A vs I may not exist) and expect a possible null result.

## Starter code (untested; run it on your machine)

```python
import mne
from mne.datasets import eegbci
from mne.decoding import CSP
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import make_pipeline

runs = [4, 8, 12]  # imagined left vs right fist
raws = [mne.io.read_raw_edf(f, preload=True) for f in eegbci.load_data(1, runs)]
raw = mne.concatenate_raws(raws)
eegbci.standardize(raw)
raw.set_montage("standard_1005")
raw.filter(8, 30)

events, _ = mne.events_from_annotations(raw, event_id=dict(T1=2, T2=3))
epochs = mne.Epochs(raw, events, dict(left=2, right=3),
                    tmin=0.5, tmax=3.5, baseline=None, preload=True)
X, y = epochs.get_data(), epochs.events[:, 2]

clf = make_pipeline(CSP(n_components=4), LDA())
print(cross_val_score(clf, X, y, cv=5).mean())
```

## Things to expect

- Chance level for two classes is 50%. Getting 65-80% on good subjects is a normal success; some subjects stay near chance.
- Split train and test by session or subject, not randomly by trial, or accuracy will look falsely high.
- Imagined vowels from scalp EEG are a hard, open research problem. Expect small gains above chance at best, and treat any impressive result with suspicion until it survives proper cross-validation.

## Done when

- You can load a dataset, filter it, epoch it and classify two mental states above chance with honest cross-validation.
- You can explain why accuracy varies between subjects.
- You have a notebook someone else could run to reproduce your numbers.

---

# 공개 EEG 데이터로 뇌 활동 배우기

새 프로젝트를 위한 독립 기반 문서. 비용: $0. 하드웨어, 임플란트, 구매 모두 없음.

## 범위

**포함:** 이미 녹음된 공개 EEG 데이터셋으로 뇌 신호가 어떻게 생겼는지, Python으로 정신 상태를 어떻게 분류하는지 배우기.
**제외:** 하드웨어 구매, 직접 데이터 기록, 실시간 시스템, 폰 앱, 모든 침습적 작업.

**배경 목표:** 상상한 정신 활동의 차이(예: 상상한 모음 "A"와 "I")를 뇌 신호에서 감지할 수 있는지 시험하기. 가장 잘 정리된 과제인 손 움직임 상상으로 먼저 시작하고, 확장 과제로 상상 발화 데이터를 다룹니다.

## 준비 (저녁 한 번)

- 가상환경의 Python 3.10 이상, 또는 무료 Google Colab.
- `mne`, `scikit-learn`, `numpy`, `matplotlib` 설치; 나중에 `torch`와 `moabb`.
- 데이터셋마다 폴더 하나, 실험마다 노트북 하나.

## 사용할 공개 데이터

- **PhysioNet EEG Motor Movement/Imagery:** 피험자 109명, 64채널. 첫 데이터셋으로 최고. MNE가 자동 다운로드합니다(`mne.datasets.eegbci`).
- **BCI Competition IV (2a, 2b):** 운동상상의 고전 벤치마크. 발표된 결과와 비교하기 좋습니다.
- **MOABB:** 여러 BCI 데이터셋을 하나의 인터페이스로 불러오고 공정하게 평가하는 Python 라이브러리.
- **OpenNeuro:** EEG 및 기타 신경영상 데이터가 모인 대규모 공개 저장소.
- **상상 발화 EEG 데이터:** 공개 데이터셋이 있습니다(예: Kara One). 사용 전에 라이선스, 피험자 수, 과제를 확인하세요.

## 0주차: 노이즈 직접 보기 (저녁 한 번)

목표: 시행이 약 45개일 때 정확도가 얼마나 흔들리는지 체감한 뒤에 어떤 숫자든 믿기. 배경은 `blindspots.md` 참고.

- [ ] 가상환경을 만들고 `pip install -r requirements.txt`를 실행합니다.
- [ ] `python experiments/week0_noise_check.py`를 실행합니다. 피험자 10명의 4, 8, 12번 런을 gitignore된 `data/` 폴더에 내려받습니다.
- [ ] `results/week0_noise_check.png`를 엽니다(표는 같은 이름의 `.txt`에 있습니다). 패널 A는 라벨을 섞었을 때의 우연 수준 정확도 분포를 실제 결과와 비교해 보여주고, 패널 B는 피험자별 정확도와 95% 신뢰구간, 우연 수준을 넘기 위해 필요한 정확도, 비교용으로 무작위 섞기 교차검증 점수를 보여줍니다.
- [ ] 한 문장 쓰기: 한 피험자의 결과를 믿으려면 정확도가 얼마나 나와야 할까?

## 4주 작업 흐름

1. **1주차:** 데이터를 불러와 원시 EEG를 그리고, 눈 깜빡임과 근육 노이즈를 표시하며, 채널, 샘플링 속도, 이벤트를 이해합니다.
   - [ ] 아티팩트를 표시하고 ICA를 시도하며, 전원 잡음 필터(50/60Hz)와 사용한 기준 전극을 기록합니다.
   - [ ] 데이터셋의 라이선스와 인용 조건을 확인합니다. 데이터는 gitignore된 폴더에만 둡니다.
   - [ ] 분류기 결과를 보기 전에 가설과 "감지 못 함"으로 볼 결과 기준을 적어 둡니다.
2. **2주차:** 대역통과 필터(운동상상은 8~30Hz), 이벤트 주변 에포크 분할, 평균 대역 파워 확인.
   - [ ] 필터 대역과 시간 구간을 지금 정해서 적어 두고, 테스트 결과를 보면서 조정하지 않습니다.
   - [ ] 왼손/오른손 상상에서 C3, C4의 대역 파워를 그려 mu/beta 효과를 직접 확인합니다.
3. **3주차:** 특징(대역 파워, CSP) + 간단한 분류기(LDA). 교차검증 후 피험자별 정확도를 기록합니다.
   - [ ] 시행을 무작위로 섞지 말고 런 단위 또는 피험자 단위 교차검증을 씁니다(PhysioNet은 피험자당 세션이 하나).
   - [ ] CSP 등 학습이 필요한 단계는 모두 교차검증 파이프라인 안에 둡니다.
   - [ ] 최고 피험자만이 아니라 모든 피험자의 신뢰구간, 순열검정 p값, Cohen's kappa를 보고합니다.
   - [ ] 분류기가 어떤 채널과 주파수에 의존하는지 확인해 눈/근육 아티팩트를 배제합니다.
4. **4주차:** 작은 신경망(EEGNet)을 시도하고 간단한 모델과 비교합니다. 잘된 점과 안 된 점을 정리합니다.
   - [ ] 시행 약 45개에서 EEGNet은 과적합됩니다. BCI IV 2a를 쓰거나 피험자를 합치고, 같은 교차검증으로 LDA와 비교합니다.
   - [ ] 라이브러리 버전을 고정하고 시드를 설정하며, 노트북이 처음부터 끝까지 돌아가게 합니다. 커밋 전에 출력을 지웁니다.
   - [ ] 상상 발화 확장 과제에서는 데이터셋에 실제로 어떤 프롬프트가 있는지 확인하고(A 대 I는 없을 수 있음) 결과가 없을 가능성을 염두에 둡니다.

## 시작 코드 (테스트하지 않음, 본인 컴퓨터에서 실행)

위 영문 섹션의 "Starter code"와 동일한 코드를 사용하세요. 주석만 번역하면 다음과 같습니다: `runs = [4, 8, 12]`는 왼손 vs 오른손 주먹 상상 구간입니다.

## 예상해야 할 것

- 2개 클래스의 우연 수준은 50%입니다. 좋은 피험자에서 65~80%면 정상적인 성공이며, 일부 피험자는 우연 수준에 머뭅니다.
- 훈련/테스트는 시행(trial)별 무작위가 아니라 세션이나 피험자 단위로 나누세요. 그렇지 않으면 정확도가 거짓으로 높게 나옵니다.
- 두피 EEG로 상상한 모음을 구분하는 것은 어렵고 아직 열린 연구 문제입니다. 잘해야 우연 수준을 조금 넘는 정도로 예상하고, 인상적인 결과는 제대로 된 교차검증을 통과하기 전까지 의심하세요.

## 완료 기준

- 데이터셋을 불러와 필터링, 에포크 분할, 두 가지 정신 상태 분류를 정직한 교차검증으로 우연 수준 이상 해냅니다.
- 피험자마다 정확도가 다른 이유를 설명할 수 있습니다.
- 다른 사람이 숫자를 재현할 수 있는 노트북이 있습니다.
