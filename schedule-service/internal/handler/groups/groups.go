package groups

import (
	"log/slog"
	"raspyx2/config"
	"raspyx2/internal/service"
)

type GroupsHandler struct {
	log     *slog.Logger
	cfg     *config.Config
	service *service.Service
}

func NewGroupsHandler(log *slog.Logger, cfg *config.Config, service *service.Service) *GroupsHandler {
	return &GroupsHandler{
		log:     log,
		cfg:     cfg,
		service: service,
	}
}
