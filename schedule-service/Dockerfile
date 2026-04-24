FROM golang:1.23-alpine AS builder

WORKDIR /app

COPY . .

RUN go build -mod vendor -o /schedule-service ./cmd/main.go

FROM alpine:3.20

WORKDIR /app

COPY --from=builder /schedule-service /app/schedule-service
COPY --from=builder /app/migrations /app/migrations

CMD ["/app/schedule-service"]
