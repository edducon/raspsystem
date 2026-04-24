package logger

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"log/slog"
	"raspyx2/internal/models"
)

func NewErrorResponse(c *gin.Context, log *slog.Logger, writeLog bool, code int, message string) {
	currRequestId, _ := c.Get("requestId")

	if writeLog {
		log.Error(fmt.Sprintf("%d %s %s", code, currRequestId, message))
	}

	errorResponse := models.ErrorResponse{
		Code:    code,
		Message: message,
	}

	c.AbortWithStatusJSON(code, models.ResponseAPI{
		Errors:    errorResponse,
		Success:   false,
		RequestId: fmt.Sprint(currRequestId),
	})
}
