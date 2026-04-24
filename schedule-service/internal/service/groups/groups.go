package groups

import (
	"raspyx2/config"
	"raspyx2/internal/repository"
)

type GroupsService struct {
	cfg  *config.Config
	repo *repository.Repository
}

func NewGroupsService(cfg *config.Config, repo *repository.Repository) *GroupsService {
	return &GroupsService{
		cfg:  cfg,
		repo: repo,
	}
}
