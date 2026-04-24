package handler

import (
	"log/slog"
	"raspyx2/internal/handler/catalog"
	"raspyx2/internal/service"
)

type Handler struct {
	log            *slog.Logger
	services       *service.Service
	CatalogHandler *catalog.Handler
}

func NewHandler(log *slog.Logger, services *service.Service) *Handler {
	return &Handler{
		log:            log,
		services:       services,
		CatalogHandler: catalog.NewHandler(log, services),
	}
}
