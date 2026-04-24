package subjectTypes

import (
	"log/slog"
	"raspyx2/config"
	"raspyx2/internal/service"
)

type SubjectTypesHandler struct {
	log     *slog.Logger
	cfg     *config.Config
	service *service.Service
}

func NewSubjectTypesHandler(log *slog.Logger, cfg *config.Config, service *service.Service) *SubjectTypesHandler {
	return &SubjectTypesHandler{
		log:     log,
		cfg:     cfg,
		service: service,
	}
}
