package subjectTypes

import (
	"raspyx2/config"
	"raspyx2/internal/repository"
)

type SubjectTypesService struct {
	cfg  *config.Config
	repo *repository.Repository
}

func NewSubjectTypesService(cfg *config.Config, repo *repository.Repository) *SubjectTypesService {
	return &SubjectTypesService{
		cfg:  cfg,
		repo: repo,
	}
}
