package scheduleParser

import (
	"context"
	"log/slog"
	"net/http"
	"raspyx2/config"
	"raspyx2/internal/service"
	"time"
)

type ScheduleParser struct {
	Ctx      context.Context
	Client   *http.Client
	Log      *slog.Logger
	Services *service.Service
}

func NewScheduleParser(ctx context.Context, cfg *config.Config, log *slog.Logger, services *service.Service) *ScheduleParser {
	return &ScheduleParser{
		Ctx:      ctx,
		Client:   &http.Client{Timeout: time.Duration(cfg.Parser.RequestTimeout) * time.Millisecond},
		Log:      log,
		Services: services,
	}
}
