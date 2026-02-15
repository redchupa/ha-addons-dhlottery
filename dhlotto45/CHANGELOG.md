# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [redchupa-2-0-3] - 2026-02-18

### Changed
- **prev 센서 데이터 소스 변경**: selectMyLotteryledger.do API의 ltWnResult(당첨결과) 직접 사용
  - 기존: 현재 구매 all_games에서 회차 필터 후 async_check_winning으로 재계산
  - 변경: API 응답의 ltWnResult 그대로 사용 (낙첨, 1등 당첨 등)
- **이전 회차 판단**: ltWnResult != "미추첨"인 건 중 가장 최근 회차를 이전 회차로 사용

---

## [redchupa-2-0-2] - 2026-02-18

### Fixed
- **구매 게임 센서 복원**: lotto45_game_{i}에 구매내역 및 미추첨/당첨 결과 다시 표시 (이전 "구매 내역 없음" 고정 표시 롤백)

---

## [redchupa-2-0-1] - 2026-02-18

### Fixed
- **기존 센서 ID 호환**: `lotto45_current_game_{i}` → `lotto45_game_{i}` 복원 (대시보드 카드 호환)

---

## [redchupa-2-0-0] - 2026-02-18

### Added
- **이전 회차 당첨 결과 센서**: 추첨 직후 당첨 결과를 바로 확인할 수 있는 센서 11개 추가
  - `lotto45_prev_round`: 구매 회차 (이전)
  - `lotto45_prev_game_1` ~ `lotto45_prev_game_5`: 구매 게임 1~5 (이전)
  - `lotto45_prev_game_1_result` ~ `lotto45_prev_game_5_result`: 구매 게임 1~5 (이전) 결과
- **구매 불가 시간대 1회 동기화**: 토요일 20:00~일요일 06:00 구간에서 이전 회차 결과만 1회 API 호출

### Fixed
- **간소화 페이지(mainMode=Y) 대응**: 동행복권 임시 간소화 페이지 운영 시 정상 동작

### Changed
- **센서 네이밍**: "구매 게임 {i} (현재)" / "구매 게임 {i} (이전)" 형식으로 통일
- **빈 슬롯 표시**: "Empty" → "구매 내역 없음"
- **버전 체계**: 날짜 기반 → redchupa-X-Y-Z 시맨틱 버전
- **구매 게임 (현재)**: 구매 게임 (이전)에 내역이 있으므로 항상 "구매 내역 없음" 표시

---

## [26-02-10] - 2026-02-10

### Fixed
- **세션 관리 개선**: 구매 후 API 에러 발생 시 세션을 완전히 초기화하고 재로그인하도록 수정
  - 기존: 구매 후 세션 문제 발생 시 재로그인 실패로 애드온 재시작 필요
  - 개선: 자동으로 세션 초기화 및 재로그인하여 정상 작동 유지
- **로그인 성공 판단 로직 개선**: `/mypage/` 리다이렉트도 로그인 성공으로 인정
- **중복 코드 제거**: `async_get_balance()` 메서드 중복 정의 제거

### Improved
- **안정성 향상**: 장기간 실행 시 세션 만료 문제 자동 복구
- **로깅 개선**: 세션 초기화 과정을 더 명확하게 로그에 표시

---

## [0.7.3] - 2025-02-05

### Changed
- **한국어 센서 이름**: 모든 센서 및 버튼의 Friendly Name을 한국어로 변경
  - "DH Lottery Balance" → "동행복권 예치금"
  - "Lotto 645 Winning Numbers" → "로또 645 당첨번호"
  - "Buy 1 Auto Game" → "1게임 자동 구매"
  - 등등...
- **단위 현지화**: 당첨자 수 단위 "people" → "명", 출현 횟수 "times" → "회"
- **디바이스 이름**: "DH Lottery Add-on" → "동행복권 애드온"

---

## [0.7.0] - 2025-02-04

### Added
- **MQTT Discovery 지원**: Home Assistant와 자동 통합
  - 센서 자동 등록
  - 버튼 엔티티 생성 (1게임/5게임 자동 구매)
  - Unique ID 지원으로 센서 관리 용이
- **상금 정보 센서**: 등수별 상금 및 당첨자 수 센서 추가
  - 총 판매액, 1~5등 상금, 1~5등 당첨자 수, 총 당첨자 수
- **구매 버튼**: MQTT를 통한 1게임/5게임 자동 구매 버튼
  - 버튼 클릭만으로 간편하게 구매
  - 구매 후 센서 자동 업데이트

### Improved
- **로그인 안정성**: RSA 암호화 및 세션 관리 개선
- **에러 처리**: 더 명확한 에러 메시지 및 로깅
- **센서 업데이트**: 구매 후 즉시 센서 업데이트

---

## [0.6.8] - 2025-01-28

### Added
- **번호 통계 분석**: Hot/Cold 번호, 출현 빈도 분석 센서
- **구매 통계**: 총 구매 금액, 당첨률, 수익률 센서
- **구매 내역**: 최근 구매 게임 1-5 개별 센서

### Improved
- **로그인 개선**: User-Agent 로테이션, Circuit Breaker 추가
- **안정성 향상**: 연속 실패 방지 로직 추가

---

## [0.6.0] - 2025-01-20

### Added
- **REST API**: 로또 구매, 통계 조회, 랜덤 번호 생성 API
- **Swagger UI**: API 테스트 인터페이스 (`/docs`)
- **Web UI**: 간단한 웹 인터페이스 제공

### Improved
- **센서 업데이트**: 주기적 자동 업데이트 (기본 1시간)
- **예치금 관리**: 구매 가능 금액 자동 체크

---

## [0.5.0] - 2025-01-15

### Added
- **자동 구매 기능**: 로또 6/45 자동 구매 (1-5게임)
- **구매 제한**: 시간 및 주간 게임 수 자동 체크
- **Home Assistant 센서**: 예치금, 당첨번호, 회차 정보 센서

### Initial Features
- 동행복권 로그인 및 세션 관리
- 최신 당첨번호 조회
- 예치금 조회
- 구매 내역 조회

---

## Version History

### 버전 명명 규칙
- **Major (X.0.0)**: 주요 기능 추가 또는 호환성 변경
- **Minor (0.X.0)**: 새로운 기능 추가
- **Patch (0.0.X)**: 버그 수정 및 개선

### 주요 마일스톤
- **v0.7.x**: MQTT Discovery 및 한국어 지원
- **v0.6.x**: 통계 분석 및 안정성 개선
- **v0.5.x**: 초기 릴리스 및 기본 기능

---

## 업데이트 안내

### 자동 업데이트
Home Assistant Add-on Store에서 자동으로 업데이트 알림을 받을 수 있습니다.

### 수동 업데이트
1. Add-on Store → **DH Lotto 45** 클릭
2. **Update** 버튼 클릭
3. 업데이트 완료 후 **Restart** 클릭

### 변경 로그 확인
각 버전의 상세한 변경 사항은 [GitHub Releases](https://github.com/redchupa/ha-addons-dhlottery/releases)에서 확인할 수 있습니다.

---

## 호환성

### Home Assistant
- **최소 버전**: 2023.1.0 이상
- **권장 버전**: 2024.1.0 이상

### Python
- **버전**: 3.11+

### 의존성
- aiohttp >= 3.9.0
- fastapi >= 0.109.0
- uvicorn >= 0.27.0
- paho-mqtt >= 2.0.0 (MQTT 사용 시)

---

## 피드백 및 버그 리포트

문제가 발생하거나 개선 제안이 있으시면:
- **GitHub Issues**: https://github.com/redchupa/ha-addons-dhlottery/issues
- **Discussions**: https://github.com/redchupa/ha-addons-dhlottery/discussions

---

**Updated**: 2026-02-10
