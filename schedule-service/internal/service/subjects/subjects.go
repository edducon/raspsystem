package subjects

import (
	"raspyx2/config"
	"raspyx2/internal/repository"
)

type SubjectsService struct {
	cfg  *config.Config
	repo *repository.Repository
}

func NewSubjectsService(cfg *config.Config, repo *repository.Repository) *SubjectsService {
	return &SubjectsService{
		cfg:  cfg,
		repo: repo,
	}
}
