package subjects

import (
	"log/slog"
	"raspyx2/config"
	"raspyx2/internal/service"
)

type SubjectsHandler struct {
	log     *slog.Logger
	cfg     *config.Config
	service *service.Service
}

func NewSubjectsHandler(log *slog.Logger, cfg *config.Config, service *service.Service) *SubjectsHandler {
	return &SubjectsHandler{
		log:     log,
		cfg:     cfg,
		service: service,
	}
}
