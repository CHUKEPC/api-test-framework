# api-test-framework

[![CI](https://github.com/CHUKEPC/api-test-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/CHUKEPC/api-test-framework/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Type Checked: mypy](https://img.shields.io/badge/mypy-strict-blue.svg)](https://mypy-lang.org/)

Декларативный фреймворк для тестирования REST API с YAML DSL, нативным плагином для pytest, проверками JSONPath, цепочками переменных (request chaining), хелперами аутентификации и расширенной отчетностью. Готовый к публикации в PyPI пакет Python.

---

## Возможности

- **Декларативный YAML и JSON DSL**: Описание полноценных сценариев тестирования HTTP API без дублирования кода.
- **Интеграция с Pytest**: Автоматическое обнаружение и запуск файлов `test_*.yaml` через стандартный раннер `pytest` (точка входа `pytest11`).
- **Цепочки запросов (Chaining) и извлечение переменных**: Извлечение значений из ответа (JSONPath, заголовки, регулярные выражения) на шаге $N$ и передача их в запрос на шаге $N+1$.
- **Шаблонизация Jinja2 и динамические переменные**: Встроенные генераторы (`{{ uuid() }}`, `{{ timestamp() }}`, `{{ random_int(1, 100) }}`) и подстановка переменных окружения в стиле shell (`${API_URL:-http://localhost}`).
- **Мощный движок проверок (Assertions Engine)**:
  - Коды состояния HTTP (точное совпадение или список допустимых кодов `[200, 201]`)
  - Глубокое сравнение подмножеств JSON-ответов
  - Выражения JSONPath (`jsonpath-ng`) с операторами: `equals`, `not_equals`, `contains`, `exists`, `regex`, `gt`, `gte`, `lt`, `lte`, `type`, `len`
  - Валидация JSON Schema (`Draft 2020-12`)
  - Проверка HTTP-заголовков (регистронезависимо с операторами `equals`, `contains`, `regex`, `exists`)
  - Контроль времени ответа и порогов производительности (`max_duration`)
  - Реестр пользовательских функций проверок (Custom assertion functions)
- **Асинхронный HTTP-клиент**: Высокопроизводительный клиент на базе `httpx` с настраиваемыми повторными попытками (retries), задержками, проверкой SSL и таймаутами.
- **Хелперы аутентификации**: Встроенная поддержка Bearer-токенов, HTTP Basic Auth, API-ключей (в заголовке или query-параметрах) и OAuth2 Client Credentials flow.
- **Хуки жизненного цикла сьюта**: Декларативные HTTP-запросы `setup` и `teardown`, выполняемые до и после тестов сьюта.
- **Информативные отчеты**:
  - Красивый вывод в терминал с таблицами и цветными бейджами через `rich`
  - Интерактивные самодостаточные HTML-отчеты
  - Стандартные отчеты JUnit XML для CI/CD систем
  - Структурированные отчеты в формате JSON
- **Автономный CLI**: Запуск тестов, валидация синтаксиса и структуры YAML, генерация начального шаблона через команду `api-test`.

---

## Архитектура проекта

Проект спроектирован по принципам чистой архитектуры со строгим разделением ответственности на подпакеты:

```
src/api_test_framework/
├── __init__.py
├── main.py              # Точка входа Click CLI
├── config.py            # Конфигурация рантайма (таймауты, ретраи, base URL)
├── exceptions.py        # Иерархия кастомных исключений
├── py.typed             # Маркер типизации PEP 561
├── pytest_plugin.py     # Плагин pytest (discovery, collector, items, fixtures)
├── variables.py         # Менеджер переменных, шаблоны Jinja2 и извлечение данных
├── loader/              # Загрузка тестовых файлов и валидация схемы DSL
│   ├── __init__.py
│   ├── json_loader.py
│   ├── validator.py
│   └── yaml_loader.py
├── models/              # Доменные модели Pydantic
│   ├── __init__.py
│   ├── assertion.py
│   ├── request.py
│   ├── response.py
│   ├── result.py
│   ├── test_case.py
│   └── test_suite.py
├── runner/              # Движок выполнения тестов
│   ├── __init__.py
│   ├── chain.py         # Последовательный запуск с цепочками переменных и хуками
│   ├── executor.py      # Асинхронный клиент httpx с политикой ретраев
│   └── parallel.py      # Параллельный раннер с семафором воркеров
├── assertions/          # Модули проверок ответа
│   ├── __init__.py
│   ├── body.py          # Глубокое сравнение, regex, подстрока
│   ├── headers.py       # Проверки заголовков
│   ├── jsonpath.py      # Запросы jsonpath-ng
│   ├── registry.py      # Реестр кастомных функций проверок
│   ├── schema.py        # Проверка JSON Schema
│   ├── status.py        # Проверка кодов ответа
│   └── timing.py        # Проверка времени выполнения
├── auth/                # Стратегии аутентификации
│   ├── __init__.py
│   ├── api_key.py       # API Key (заголовок/query)
│   ├── base.py          # Абстрактный базовый класс BaseAuth
│   ├── basic.py         # HTTP Basic Auth (base64)
│   ├── bearer.py        # Bearer-токен
│   └── oauth2.py        # OAuth2 Client Credentials flow
├── reporting/           # Генераторы отчетов
│   ├── __init__.py
│   ├── base.py          # Базовый класс BaseReporter
│   ├── html.py          # Генератор HTML-отчетов
│   ├── json_report.py   # Генератор JSON-отчетов
│   ├── junit.py         # Генератор JUnit XML для CI
│   └── terminal.py      # Rich терминальный репортер
└── cli/                 # Интерфейс командной строки
    ├── __init__.py
    ├── app.py           # Команды run, validate, init
    └── template.py      # Шаблон для скаффолдинга
```

---

## Установка

```bash
# Установка библиотеки в текущее окружение
pip install -e .

# Установка с зависимостями для разработки и тестирования
pip install -e ".[dev]"
```

---

## Быстрый старт

### 1. Создание шаблона тестового файла

Сгенерируйте стартовый файл теста с помощью команды:

```bash
api-test init test_users.yaml
```

### 2. Пример YAML-спецификации теста

Пример декларативного описания теста с аутентификацией, проверками и цепочкой переменных:

```yaml
name: "Users API Verification Suite"
description: "Проверка создания, чтения пользователя и соответствия схемы"
base_url: "https://jsonplaceholder.typicode.com"

# Заголовки по умолчанию для всех запросов сьюта
headers:
  Content-Type: "application/json"
  Accept: "application/json"

# Начальные переменные (поддерживают функции uuid, timestamp, random_*)
variables:
  new_username: "qa_lead_{{ random_str(6) }}"
  new_email: "qa_{{ random_int(100, 999) }}@example.com"

tests:
  - name: "Create new user"
    description: "POST-запрос создания пользователя и сохранение сгенерированного ID"
    request:
      method: "POST"
      url: "/users"
      json:
        name: "Test Engineer"
        username: "{{ new_username }}"
        email: "{{ new_email }}"
    assertions:
      status_code: 201
      headers:
        content-type:
          op: "contains"
          expected: "application/json"
      jsonpath:
        - path: "$.id"
          op: "exists"
        - path: "$.username"
          op: "equals"
          expected: "{{ new_username }}"
      max_duration: 3.0
    extract:
      - name: "created_user_id"
        source: "jsonpath"
        expression: "$.id"

  - name: "Retrieve created user"
    description: "GET-запрос с подстановкой сохраненной переменной created_user_id"
    request:
      method: "GET"
      url: "/users/1"  # Либо /users/{{ created_user_id }}
    assertions:
      status_code: 200
      jsonpath:
        - path: "$.id"
          op: "equals"
          expected: 1
      max_duration: 2.0
```

### 3. Запуск через CLI

```bash
# Запуск теста с красивым выводом в терминал
api-test run test_users.yaml

# Запуск с формированием HTML, JUnit XML и JSON отчетов
api-test run test_users.yaml --report-html report.html --report-junit report.xml --report-json report.json

# Параллельный запуск всех тестов в папке
api-test run examples/ --parallel --workers 4

# Валидация структуры и синтаксиса YAML без выполнения HTTP-запросов
api-test validate test_users.yaml
```

### 4. Запуск через Pytest

Фреймворк зарегистрирован как плагин `pytest11`. Любые файлы с маской `test_*.yaml` или `*_test.yaml` обнаруживаются автоматически:

```bash
# Запуск YAML-тестов через стандартный pytest
pytest examples/

# Передача параметров CLI в pytest
pytest examples/ --api-base-url="https://api.staging.example.com" --api-auth-token="secret-token"
```

Доступные фикстуры в тестах:
- `api_client`: Готовый экземпляр `HttpExecutor`
- `base_url`: Базовый URL из опций CLI или переменных окружения
- `auth_token`: Токен авторизации
- `api_vars`: Контекст `VariableManager`

---

## Справочник проверок (Assertions)

| Ключ | Описание | Пример |
| :--- | :--- | :--- |
| `status_code` | Точный код или список допустимых кодов | `status_code: 200` или `status_code: [200, 201]` |
| `headers` | Словарь или список правил (`equals`, `contains`, `regex`, `exists`) | `content-type: { op: "contains", expected: "application/json" }` |
| `body` | Точное тело ответа или глубокое совпадение структуры | `body: { "status": "ok" }` |
| `body_contains` | Подстрока в тексте ответа | `body_contains: "Success"` |
| `body_regex` | Регулярное выражение для текста ответа | `body_regex: "token=[A-Za-z0-9]+"` |
| `jsonpath` | Список проверок JSONPath с операторами сравнения | `- path: "$.data[0].id", op: "gt", expected: 0` |
| `schema` | JSON Schema словарь или путь к файлу `.json`/`.yaml` | `schema: "schemas/user.json"` |
| `max_duration` | Максимальное время выполнения запроса в секундах | `max_duration: 1.5` |
| `custom` | Имена зарегистрированных пользовательских функций | `custom: ["check_csrf_token"]` |

### Операторы JSONPath

- `equals`: Строгое равенство (`val == expected`)
- `not_equals`: Неравенство
- `contains`: Проверка вхождения подстроки или элемента списка
- `exists`: Проверка существования пути (`expected: true` или `expected: false`)
- `regex`: Соответствие регулярному выражению
- `gt`, `gte`, `lt`, `lte`: Числовые сравнения (>, >=, <, <=)
- `type`: Проверка типа данных (`str`, `int`, `float`, `bool`, `list`, `dict`)
- `len`: Проверка длины списка или строки

---

## Настройка аутентификации

```yaml
# Bearer-токен
auth:
  type: "bearer"
  token: "{{ auth_token }}"

# HTTP Basic Auth
auth:
  type: "basic"
  username: "admin"
  password: "password123"

# API-ключ в заголовке или query-параметрах
auth:
  type: "api_key"
  key_name: "X-API-Key"
  key_value: "secret-key-val"
  location: "header" # или "query"

# OAuth2 Client Credentials Flow
auth:
  type: "oauth2"
  token_url: "https://auth.example.com/oauth/token"
  client_id: "client-id"
  client_secret: "client-secret"
  scope: "read write"
```

---

## Разработка и тестирование

```bash
# Запуск линтера (ruff)
make lint

# Проверка типов (mypy strict mode)
make type-check

# Запуск тестов с измерением покрытия кодом
make test

# Сборка пакета для PyPI (sdist и wheel)
make build
```

---

## Лицензия

Проект распространяется под лицензией MIT. Подробности см. в файле [LICENSE](LICENSE).
