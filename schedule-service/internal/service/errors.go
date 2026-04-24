package service

import "errors"

var (
	ErrInvalidUUID        = errors.New("invalid uuid")
	ErrGeneratingUUID     = errors.New("failed to generate uuid")
	ErrInvalidUser        = errors.New("invalid user")
	ErrInvalidCredentials = errors.New("invalid credentials")
	ErrInvalidGroup       = errors.New("group is invalid")
)
