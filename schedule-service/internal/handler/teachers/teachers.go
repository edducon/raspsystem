package teachers

import (
	"log/slog"
	"raspyx2/config"
	"raspyx2/internal/service"
)

type TeachersHandler struct {
	log     *slog.Logger
	cfg     *config.Config
	service *service.Service
}

func NewTeachersHandler(log *slog.Logger, cfg *config.Config, service *service.Service) *TeachersHandler {
	return &TeachersHandler{
		log:     log,
		cfg:     cfg,
		service: service,
	}
}
