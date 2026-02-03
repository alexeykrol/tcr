# Пайплайн перевода RU→en-US (переводчик → редактор → аудит точности)

Цель: на входе **русский текст** (Markdown главы), на выходе — **английский текст (American English)**, который:
- сохраняет **весь смысл** (без потерь/добавлений),
- сохраняет **структуру Markdown** (заголовки, абзацы, списки, выделения),
- звучит естественно для американской аудитории,
- использует стабильную терминологию (caste/role/Game и т.п.).

---

## 0) Артефакты и структура файлов

Минимальная договорённость по путям (как сейчас в проекте):
- RU вход: `chapters/CH-XX.md`
- EN выход: `chapters_en_us/CH-XX.en-US.md`

Рекомендовано добавить (если захочешь позже):
- отчёты аудита: `reviews/CH-XX.audit.md`
- “решения по правкам”: `reviews/CH-XX.decisions.md`

---

## 1) Инварианты (что запрещено на всех этапах)

1) **Никаких пропусков** (omissions) и **никаких добавлений** (additions).
2) **Никакого пересказа** вместо перевода/редактуры.
3) **Форматирование и структура** должны совпадать с RU (заголовки, списки, разрывы, выделения).
4) **Тон**: сохраняем прямой/провокативный голос автора; не “смягчать” и не “усиливать”.
5) Терминология фиксирована и единообразна в пределах всей книги.

---

## 2) Модели и автономность

Да, на разных этапах можно использовать разные модели (и/или одну модель с разными промптами).

Автономный процесс организуется так:
- этапы выполняются **строго последовательно** (Translator → Editor → Auditor → Apply fixes → Final checks),
- каждый этап пишет свой результат в файл (или в “патч/дифф”),
- этап “Auditor” выдаёт **структурированный список проблем** и **минимальные правки**,
- этап “Apply fixes” применяет только **принятые** правки.

Если нужно “почти без участия человека”, обычно делают так:
- Translator и Editor сразу выдают **полный текст**,
- Auditor выдаёт **список проблем + точечные исправления**,
- Apply fixes применяется автоматически по правилам (“исправления только с severity=high/critical”), а остальное — на ручное утверждение.

---

## 3) Этапы пайплайна

### Этап A — Translator (RU → en-US)

**Задача:** сделать литературный перевод, максимально близкий к оригиналу, сохраняя структуру.

**Рекомендуемый вход:** RU‑текст главы (в Markdown), при необходимости — частями.

**Рекомендуемый выход:** полный EN‑текст главы (Markdown), без комментариев.

**Промпт (Translator v1.0)**  
Источник: `translation_prompt_en-US.md` (в проекте). Ниже — эквивалентная версия:

```
You are a professional literary translator. Translate the provided chapter from Russian into American English.

Requirements:
- Preserve all headings, paragraph breaks, bullet lists, and emphasis.
- Keep epigraphs and author attributions.
- Maintain the author's first-person, direct, slightly provocative tone.
- Preserve rhetorical questions and parallelism.
- Do not summarize, censor, or add any content.
- Output only the translated text.

Terminology (use consistently):
- каста -> caste
- роль -> role
- социальная роль -> social role
- Игра (как метафора устройства мира) -> Game (capitalize)
- «Теория каст и ролей» -> [Theory of Castes and Roles](https://www.amazon.com/dp/B07PDHZRCC)

Quotes:
- If you are confident a canonical English translation exists, use it.
- Otherwise translate faithfully.

Style:
- Natural American English.
- Keep long sentences if they carry the original rhythm; split only when clarity suffers.
- For idioms, use an American equivalent with similar intensity (do not increase profanity).

Input format:
<<<
[RU TEXT]
>>>
```

**Рекомендация по “частям” (chunking):**
- дели по логическим блокам: раздел/подраздел/группа абзацев;
- не разрывай таблицы и списки;
- каждый кусок переводить отдельно, затем склеить в порядке оригинала.

---

### Этап B — Editor (стилистика en-US без изменения смысла)

**Задача:** сделать английский естественным, ровным, читабельным; исправить грамматику, пунктуацию, “канцелярит”, кривые кальки.

**Жёсткое правило:** редактор **не имеет права** менять смысл, порядок идей, или структуру Markdown.

**Вход:** EN‑текст от Translator.

**Выход:** улучшенный EN‑текст, без комментариев.

**Промпт (Editor v1.0)**

```
You are a senior English-language editor (American English).

Task: Edit the provided English text for clarity, flow, idiomatic American English, grammar, and punctuation.

Hard constraints (must follow):
- Do NOT add, remove, or reorder meaning-bearing content.
- Do NOT summarize or paraphrase aggressively; keep the author’s intent and tone.
- Preserve ALL Markdown structure exactly: headings, paragraph breaks, lists, emphasis, and links.
- Keep terminology consistent with the glossary: caste/role/social role/Game and the book link formatting.
- If a sentence is ambiguous, prefer the closest literal interpretation rather than “improving” ideas.

Output:
- Output ONLY the fully revised text (no explanations, no bullets, no change log).

Input:
<<<
[EN TEXT]
>>>
```

Опционально (для более “безопасной” редактуры): попросить “минимальные правки”:
- “Make the smallest set of edits needed to sound natural in American English.”

---

### Этап C — Fidelity Auditor (сверка RU vs EN на потери/искажения)

**Задача:** гарантировать, что смысл не уехал при переводе и редактуре.

**Вход:** RU‑текст главы + EN‑текст (после Editor).

**Выход:** отчёт со списком проблем и минимальными исправлениями.

**Промпт (Auditor v1.0)**

```
You are a translation fidelity auditor. Your job is to compare the Russian source text (RU) and the English target text (EN).

Find and report ONLY issues that affect fidelity or required invariants:
- omissions (missing content),
- additions (content not present in RU),
- mistranslations / meaning shifts,
- tone drift (EN becomes harsher/softer than RU),
- broken structure/formatting relative to RU,
- glossary violations (caste/role/Game, book link).

For each issue:
- Provide a short title.
- Point to a location using the nearest heading + a short excerpt (keep excerpts short).
- Classify severity: critical | high | medium | low.
- Propose the smallest possible fix in EN (prefer a minimal replacement).

Output format (machine-friendly Markdown):
## Issues
1) [severity] Title
   - Location: <heading path>
   - RU excerpt: "<...>"
   - EN excerpt: "<...>"
   - Problem: <one sentence>
   - Minimal fix (EN): "<replacement text>"

Do NOT rewrite the whole chapter. Do NOT “improve” style unless it affects fidelity.

Input:
<<<RU
[RU TEXT]
>>>
<<<EN
[EN TEXT]
>>>
```

---

### Этап D — Apply Fixes (внесение правок + решение ACCEPT/REJECT)

Есть два режима.

**Режим D1 (полуавтомат):**
- Auditor выдаёт список Issues,
- человек быстро проставляет для каждого: `ACCEPT` или `REJECT` (+ 1 строка причины),
- затем правки применяются только для `ACCEPT`.

**Режим D2 (максимально автономный):**
- применяем автоматически только `critical` и `high` (и только если “Minimal fix” — точечная замена),
- `medium/low` складываем в backlog (или оставляем как рекомендации).

Рекомендуемый выход этапа — обновлённый `chapters_en_us/CH-XX.en-US.md` + файл отчёта/решений (если используешь).

---

### Этап E — Final Checks (быстрая финальная проверка)

Чеклист:
- структура Markdown не сломана (заголовки/списки/ссылки/курсив),
- терминология единообразна,
- “Theory of Castes and Roles” оформлена как ссылка на Amazon,
- нет явных пропусков/добавлений по смыслу (особенно в списках и определениях),
- стиль — American English, без русизмов.

---

## 4) Как запускать пайплайн “от одного входа до одного выхода”

**Вход:** `chapters/CH-XX.md`  
**Выход:** `chapters_en_us/CH-XX.en-US.md`

Минимальный автономный сценарий (без дополнительных файлов):
1) Translator переводит RU → EN (при необходимости кусками) и собирает в `chapters_en_us/CH-XX.en-US.md`.
2) Editor принимает EN и возвращает “отредактированный EN” (замена содержимого файла).
3) Auditor получает RU+EN и возвращает список Issues.
4) Apply Fixes применяет правки (авто для `critical/high`, остальное — по решению).
5) Final Checks.

Если хочешь, позже можно сделать это “одной кнопкой” (скрипт), но для этого нужно договориться о точных форматах (особенно для отчётов и применения правок).

