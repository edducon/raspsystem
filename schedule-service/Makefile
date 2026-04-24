include .env
export

RED="\\033[31m"
GREEN="\\033[32m"
YELLOW="\\033[33m"
RESET="\\033[0m"

define delete-docker-service
	@if docker inspect ${APP_NAME}$1 >/dev/null 2>&1; then \
		docker stop ${APP_NAME}$1 >/dev/null 2>&1; \
		docker rm ${APP_NAME}$1 >/dev/null 2>&1; \
		echo -e "${GREEN}${APP_NAME}$1 deleted${RESET}"; \
	else \
		echo -e "${RED}${APP_NAME}$1 does not exist${RESET}"; \
	fi
endef

all: clear network-create db-create migrate-up db-admin-create build run
.PHONY: all

migrate-up: ### migration up
	migrate -path migrations/ -database "${PG_URL}" -verbose up
.PHONY: migrate-up

migrate-down: ### migration up
	migrate -path migrations/ -database "${PG_URL}" -verbose down
.PHONY: migrate-up

migration-create: ### migration creating
	migrate create -ext sql -dir migrations/ -seq $(NAME_MIGRATE)
.PHONY: migration-create

docker-up-local:
	sudo docker-compose -f docker-compose.yaml up -d

docker-build-up-local:
	sudo docker-compose -f docker-compose.yaml up -d --build

docker-down-local:
	sudo docker-compose -f docker-compose.yaml down

db-create: ### Creating postgres db docker instance
	@if docker inspect ${APP_NAME}db >/dev/null 2>&1; then \
  		echo -e "${RED}${APP_NAME}db already exists${RESET}"; \
  	else \
		docker run -p $(PG_PORT):5432 --network=${APP_NAME}-network --restart unless-stopped --name $(APP_NAME)db -e POSTGRES_PASSWORD=$(PG_PASSWORD) -v $(APP_NAME)_postgres_data:/var/lib/postgresql/data -d postgres:17-alpine >/dev/null 2>&1; \
		docker exec $(APP_NAME)db sh -c 'until pg_isready -U postgres; do sleep 0.5; done' >/dev/null 2>&1; \
		docker exec $(APP_NAME)db psql -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$(APP_NAME)db'" | grep -q 1 || docker exec $(APP_NAME)db psql -U postgres -c "CREATE DATABASE $(APP_NAME)db" >/dev/null 2>&1; \
		echo -e "${GREEN}${APP_NAME}db created${RESET}"; \
	fi
.PHONY: db-create

db-delete: ### Deleting postgres db docker instance
	$(call delete-docker-service,db)
.PHONY: db-delete

build: ### Building app
	@echo -e "${GREEN}${APP_NAME} is building...${RESET}"; \
	OUT=$$(go build -o ${APP_NAME} ./cmd 2>&1); \
	EXIT_CODE=$$?; \
	if [ $$EXIT_CODE -eq 0 ]; then \
	  	echo -e "${GREEN}${APP_NAME} builded successfully${RESET}"; \
	else \
	  	echo -ne "${RED}${APP_NAME} building error: "; \
	  	echo -e "$$OUT${RESET}"; \
	fi
.PHONY: build

#run: ### Running app
#	@./${APP_NAME}
#.PHONY: run

run: ### Running app
	go run cmd/main.go
.PHONY: run

db-admin-create: ### Creating admin user in db
	@ADMIN_PASSWORD_HASH=$$(htpasswd -nbB admin admin | cut -d: -f2 | sed 's/$$/\\$$/g'); \
	if docker exec -it $(APP_NAME)db psql -U $(PG_USER) -d $(APP_NAME)db -c "SELECT * FROM users WHERE uuid = '00000000-0000-0000-0000-000000000000'" | grep admin >/dev/null 2>&1; then \
		echo -e "${RED}admin already exists, DO NOT FORGET TO DELETE HIM${RESET}"; \
	else \
		docker exec -it $(APP_NAME)db psql -U $(PG_USER) -d $(APP_NAME)db -c "INSERT INTO users (uuid, username, password_hash, access_level) VALUES ('00000000-0000-0000-0000-000000000000', 'admin', '$$ADMIN_PASSWORD_HASH', 99)" >/dev/null 2>&1; \
		echo -e "${GREEN}admin created, ${RED}DO NOT FORGET TO DELETE HIM${RESET}"; \
	fi
.PHONY: db-admin-create

db-admin-delete: ### Creating admin user in db
	@docker exec -it $(APP_NAME)db psql -U $(PG_USER) -d $(APP_NAME)db -c "DELETE FROM users WHERE uuid = '00000000-0000-0000-0000-000000000000'" >/dev/null 2>&1; \
	echo -e "${GREEN}admin deleted${RESET}"
.PHONY: db-admin-delete

network-create:
	@if docker network ls | grep "${APP_NAME}-network" >/dev/null 2>&1; then \
  		echo -e "${RED}${APP_NAME}-network already exists${RESET}"; \
  	else \
  	  	docker network create ${APP_NAME}-network >/dev/null 2>&1; \
  	  	echo -e "${GREEN}${APP_NAME}-network created${RESET}"; \
  	fi
.PHONY: network-create

network-delete:
	@if docker network inspect ${APP_NAME}-network >/dev/null 2>&1; then \
  		docker network rm "${APP_NAME}-network" >/dev/null 2>&1; \
  		echo -e "${GREEN}${APP_NAME}-network deleted${RESET}"; \
  	else \
  	  	echo -e "${RED}${APP_NAME}-network does not exist${RESET}"; \
  	fi
.PHONY: network-delete

gen-doc:
	swag init -g cmd/main.go -o ./docs
.PHONY: gen-doc

clear: db-delete network-delete ### Cleaning up
.PHONY: clear
