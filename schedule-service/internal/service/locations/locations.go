package locations

import (
	"raspyx2/config"
	"raspyx2/internal/repository"
)

type LocationsService struct {
	cfg  *config.Config
	repo *repository.Repository
}

func NewLocationsService(cfg *config.Config, repo *repository.Repository) *LocationsService {
	return &LocationsService{
		cfg:  cfg,
		repo: repo,
	}
}
