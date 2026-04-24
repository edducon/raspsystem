package parser

import (
	"context"
	"log/slog"
	"raspyx2/config"
	"raspyx2/internal/models"
	"raspyx2/internal/parser/scheduleParser"
	"raspyx2/internal/service"
)

type ScheduleParser interface {
	ParseGroupSchedule(data *models.ParseGroupScheduleData) (*models.ParseScheduleResponse, error)

	ParseGroups() ([]string, error)
	ParseSubjects(data *models.ParseScheduleResponse)
	ParseTeachers(data *models.ParseScheduleResponse)
	ParseRooms(data *models.ParseScheduleResponse)
	ParseLocations(data *models.ParseScheduleResponse)
	ParseSubjectTypes(data *models.ParseScheduleResponse)
	ParseSchedules(group string, data *models.ParseScheduleResponse)

	RemoveTrash(s string) string

	Parse()
}
type Parser struct {
	ScheduleParser
}

func NewParser(ctx context.Context, cfg *config.Config, log *slog.Logger, services *service.Service) *Parser {
	return &Parser{
		ScheduleParser: scheduleParser.NewScheduleParser(ctx, cfg, log, services),
	}
}
