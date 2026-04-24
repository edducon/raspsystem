package schedule

import (
	"raspyx2/config"
	"raspyx2/internal/repository"
)

type ScheduleService struct {
	cfg  *config.Config
	repo *repository.Repository
}

func NewScheduleService(cfg *config.Config, repo *repository.Repository) *ScheduleService {
	return &ScheduleService{
		cfg:  cfg,
		repo: repo,
	}
}
