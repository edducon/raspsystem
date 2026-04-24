package rooms

import (
	"raspyx2/config"
	"raspyx2/internal/repository"
)

type RoomsService struct {
	cfg  *config.Config
	repo *repository.Repository
}

func NewRoomsService(cfg *config.Config, repo *repository.Repository) *RoomsService {
	return &RoomsService{
		cfg:  cfg,
		repo: repo,
	}
}
