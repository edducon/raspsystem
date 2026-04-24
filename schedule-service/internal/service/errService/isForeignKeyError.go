package errService

import "strings"

func IsForeignKeyError(err error) bool {
	if err == nil {
		return false
	}

	errMsg := strings.ToLower(err.Error())

	if strings.Contains(errMsg, "23503") {
		return true
	}

	return strings.Contains(errMsg, "foreign key constraint") ||
		strings.Contains(errMsg, "foreign key violation") ||
		strings.Contains(errMsg, "referential integrity") ||
		strings.Contains(errMsg, "violates foreign key")
}
