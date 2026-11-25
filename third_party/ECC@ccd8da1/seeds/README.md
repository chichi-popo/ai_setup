# 번들 시험용 시드 파일 (참조 전용)

시험 프로젝트에 복사해 쓰고 시험 후 지운다. 의도된 문제점(번들이 잡아야 할 항목):

- `seed_ml_review.py`: ① 가변 기본 인자(`cache={}`) ② bare `except` + 삼키는 예외 + 미정의 `df` ③ 스케일러를 전체 데이터에 fit ④ 예측 시점에 없는 `outcome_value` 컬럼 사용 ⑤ 시드 없는 무작위 분할(시간 의존 데이터면 부적절)
- `SeedView.vue`: ① `reactive` 구조 분해로 반응성 손실 ② 쿼리 키에 `.value` ③ `watch(reactive 객체)` ④ `v-for` 인덱스 key ⑤ 같은 요소의 `v-if`+`v-for` ⑥ 사용자 HTML에 `v-html` ⑦ 불필요한 래퍼 `div` ⑧ `lang="ts"` 없음, `console.log`
