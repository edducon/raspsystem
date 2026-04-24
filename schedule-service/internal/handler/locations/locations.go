package locations

import (
	"log/slog"
	"raspyx2/config"
	"raspyx2/internal/service"
)

type LocationsHandler struct {
	log     *slog.Logger
	cfg     *config.Config
	service *service.Service
}

func NewLocationsHandler(log *slog.Logger, cfg *config.Config, service *service.Service) *LocationsHandler {
	return &LocationsHandler{
		log:     log,
		cfg:     cfg,
		service: service,
	}
}
