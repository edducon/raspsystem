package rooms

import (
	"log/slog"
	"raspyx2/config"
	"raspyx2/internal/service"
)

type RoomsHandler struct {
	log     *slog.Logger
	cfg     *config.Config
	service *service.Service
}

func NewRoomsHandler(log *slog.Logger, cfg *config.Config, service *service.Service) *RoomsHandler {
	return &RoomsHandler{
		log:     log,
		cfg:     cfg,
		service: service,
	}
}
