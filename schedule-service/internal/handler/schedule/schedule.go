package schedule

import (
	"log/slog"
	"raspyx2/config"
	"raspyx2/internal/service"
)

type ScheduleHandler struct {
	log     *slog.Logger
	cfg     *config.Config
	service *service.Service
}

func NewScheduleHandler(log *slog.Logger, cfg *config.Config, service *service.Service) *ScheduleHandler {
	return &ScheduleHandler{
		log:     log,
		cfg:     cfg,
		service: service,
	}
}
