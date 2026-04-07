# RaspSystem

Система управления расписанием и пересдачами на `Astro + Vue + FastAPI + PostgreSQL + Redis`.

В репозитории есть два основных режима запуска:

- `docker-compose.yml` для локальной разработки
- `docker-compose.prod.yml` и `docker-compose.prod.https.yml` для production

## Что находится в проекте

- `src/` — фронтенд на Astro/Vue
- `backend/` — backend на FastAPI
- `docker-compose.yml` — dev-окружение
- `docker-compose.prod.yml` — production через reverse proxy по HTTP
- `docker-compose.prod.https.yml` — production через reverse proxy с HTTPS
- `infra/nginx/` — конфиги nginx
- `infra/scripts/` — скрипты бэкапа и восстановления Postgres

## Требования

- Docker Desktop с `docker compose`
- Git

Локально вне Docker ничего отдельно ставить не требуется: и фронтенд, и backend запускаются в контейнерах.

## Быстрый старт для разработки

### 1. Подготовить `.env`

Скопируйте шаблон:

```powershell
Copy-Item .env.example .env
```

Для dev обычно достаточно значений из `.env.example`.

### 2. Поднять сервисы

```powershell
docker compose up --build -d
```

После старта будут доступны:

- фронтенд: [http://localhost:4321](http://localhost:4321)
- backend API: [http://localhost:8000/api](http://localhost:8000/api)
- docs в dev: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Проверить, что контейнеры поднялись

```powershell
docker compose ps
```

### 4. Проверить health backend

```powershell
curl http://localhost:8000/api/health
```

Ожидается ответ со статусом `ok`.

## Полезные dev-команды

Поднять всё:

```powershell
docker compose up --build -d
```

Остановить всё:

```powershell
docker compose down
```

Остановить всё с удалением томов базы и Redis:

```powershell
docker compose down -v
```

Посмотреть логи backend:

```powershell
docker compose logs -f backend
```

Посмотреть логи frontend:

```powershell
docker compose logs -f frontend
```

Прогнать миграции вручную:

```powershell
docker compose exec backend alembic upgrade head
```

## Как создать первого администратора

После первого запуска база будет пустой. Создайте первого пользователя с ролью `ADMIN` через встроенный backend-скрипт.

Для dev:

```powershell
docker compose exec backend python -m app.scripts.create_admin --username admin --password CHANGE_ME_NOW --full-name "System Administrator"
```

Для production:

```powershell
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.create_admin --username admin --password CHANGE_ME_NOW --full-name "System Administrator"
```

Что делает эта команда:

- создает активного пользователя с ролью `ADMIN`
- ставит флаг обязательной смены пароля при первом входе
- не привязывает пользователя к преподавателю

После входа в систему такой пользователь будет обязан сменить временный пароль.

## Как дальше создавать пользователей

После входа под первым администратором:

1. Откройте админ-панель.
2. Создайте преподавателей или синхронизируйте справочник.
3. Создайте учетные записи для нужных преподавателей и сотрудников.
4. Передайте временный пароль пользователю.
5. Пользователь при первом входе сменит пароль принудительно.

## Переменные окружения

Основные переменные находятся в:

- `.env.example` — dev-шаблон
- `.env.production.example` — production-шаблон

Самые важные настройки:

- `APP_ENV` — `development` или `production`
- `DEBUG` — в production должно быть `false`
- `SESSION_SECRET_KEY` — длинный случайный секрет для cookie-сессий
- `FRONTEND_ORIGINS` — разрешенные frontend origin
- `CSRF_TRUSTED_ORIGINS` — trusted origin для unsafe-запросов
- `SESSION_SAME_SITE` — политика cookie
- `SESSION_COOKIE_DOMAIN` — общий cookie domain, если нужен
- `API_DOCS_ENABLED` — включать ли `/docs`
- `ALLOW_ORIGINLESS_UNSAFE_REQUESTS` — в production должно быть `false`

## Как работает авторизация

В проекте используется cookie-based session auth.

Сейчас уже реализованы:

- хеширование паролей
- rate limiting на логин и смену пароля
- CSRF token для state-changing запросов
- проверка `Origin` / `Referer`
- инвалидирование старых сессий после смены пароля
- обязательная смена стартового пароля
- audit log для входов и админских действий

## Production запуск

### Вариант 1. Production через HTTP reverse proxy

Подходит, если HTTPS завершается внешним ingress, load balancer или CDN.

#### 1. Подготовить production `.env`

Скопируйте шаблон:

```powershell
Copy-Item .env.production.example .env
```

Обязательно замените:

- `POSTGRES_PASSWORD`
- `SESSION_SECRET_KEY`
- `RASPYX_USERNAME`
- `RASPYX_PASSWORD`
- `FRONTEND_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`

#### 2. Поднять production стек

```powershell
docker compose -f docker-compose.prod.yml up --build -d
```

#### 3. Проверить сервисы

```powershell
docker compose -f docker-compose.prod.yml ps
```

### Вариант 2. Production через встроенный HTTPS nginx

Подходит, если сертификаты лежат прямо на сервере.

#### 1. Подготовить `.env`

```powershell
Copy-Item .env.production.example .env
```

#### 2. Положить сертификаты

Нужны файлы:

- `infra/certs/fullchain.pem`
- `infra/certs/privkey.pem`

#### 3. Поднять HTTPS стек

```powershell
docker compose -f docker-compose.prod.https.yml up --build -d
```

#### 4. Проверить сервисы

```powershell
docker compose -f docker-compose.prod.https.yml ps
```

## Что важно сделать перед production запуском

### 1. Убрать `.env` из git tracking

`.gitignore` уже исключает `.env`, но если файл раньше был добавлен в git, этого недостаточно.

Нужно выполнить один раз:

```powershell
git rm --cached .env
```

### 2. Не публиковать внутренние сервисы наружу

В production не должны быть доступны извне:

- `8000`
- `5432`
- `6379`

Во внешнюю сеть должен смотреть только reverse proxy.

### 3. Отключить debug и docs

Для production:

- `APP_ENV=production`
- `DEBUG=false`
- `API_DOCS_ENABLED=false`
- `ALLOW_ORIGINLESS_UNSAFE_REQUESTS=false`

### 4. Настроить корректную cookie-политику

Если фронтенд и API идут через один origin:

- используйте `SESSION_SAME_SITE=lax`
- `SESSION_COOKIE_DOMAIN` можно оставить пустым

Если используются разные поддомены:

- настройте общий `SESSION_COOKIE_DOMAIN`, например `.example.com`
- при необходимости используйте `SESSION_SAME_SITE=none`
- режим `none` безопасно использовать только с HTTPS

### 5. Проверить firewall

Обычно на публичном сервере наружу должны быть открыты только:

- `80`
- `443`

### 6. Создать первого администратора

После запуска production стека выполните:

```powershell
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.create_admin --username admin --password CHANGE_ME_NOW --full-name "System Administrator"
```

Если используется HTTPS compose:

```powershell
docker compose -f docker-compose.prod.https.yml exec backend python -m app.scripts.create_admin --username admin --password CHANGE_ME_NOW --full-name "System Administrator"
```

## Чеклист перед открытием доступа пользователям

- заполнен production `.env`
- секреты заменены на реальные
- `.env` убран из git tracking
- включен HTTPS
- наружу не опубликованы `8000`, `5432`, `6379`
- `/docs` отключен
- первый `ADMIN` создан
- вход, выход и смена пароля работают
- преподаватель не может открыть чужое расписание
- audit log записывает входы и админские действия

## Audit log

Сейчас audit log пишет:

- успешные и неуспешные входы
- выход из системы
- смену пароля
- создание, изменение и удаление пользователей
- операции по кафедрам и должностям
- операции по преподавателям и справочнику
- операции со снимками расписания
- часть административных действий по пересдачам

В админке есть отдельная вкладка журнала действий с:

- поиском
- фильтром по действию
- фильтром по статусу
- пагинацией

## Бэкап и восстановление Postgres

Скрипты лежат в `infra/scripts/`.

Бэкап:

```bash
sh infra/scripts/postgres-backup.sh
```

Восстановление:

```bash
sh infra/scripts/postgres-restore.sh ./backups/postgres_YYYYMMDD_HHMMSS.sql
```

Перед восстановлением убедитесь, что понимаете последствия для боевой базы.

## Что делать, если нужно полностью сбросить dev-окружение

```powershell
docker compose down -v
docker compose up --build -d
```

После этого база будет пустой, и первого администратора нужно будет создать заново.

## Что делать дальше после базового security hardening

Это уже не блокеры для первого запуска, но хорошие следующие шаги:

- вывести audit log в отдельный API export
- добавить фильтр по пользователю в audit log
- добавить 2FA хотя бы для `ADMIN`
- вынести TLS на внешний ingress или load balancer
- настроить автоматические backup job
- добавить CI-проверки зависимостей и secret scanning
