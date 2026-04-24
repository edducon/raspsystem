package teachers

import (
	"raspyx2/config"
	"raspyx2/internal/repository"
)

type TeachersService struct {
	cfg  *config.Config
	repo *repository.Repository
}

func NewTeachersService(cfg *config.Config, repo *repository.Repository) *TeachersService {
	return &TeachersService{
		cfg:  cfg,
		repo: repo,
	}
}
