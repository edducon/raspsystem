package errService

import "strings"

func IsDuplicateError(err error) bool {
	if err == nil {
		return false
	}

	errMsg := strings.ToLower(err.Error())

	if strings.Contains(errMsg, "23505") {
		return true
	}

	return strings.Contains(errMsg, "unique constraint") ||
		strings.Contains(errMsg, "duplicate key") ||
		strings.Contains(errMsg, "duplicate entry") ||
		strings.Contains(errMsg, "already exists")
}
