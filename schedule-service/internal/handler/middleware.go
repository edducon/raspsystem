package handler

import (
	"fmt"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"

	"raspyx2/internal/handler/constHandler"
)

func (h *Handler) RequestLogger() gin.HandlerFunc {
	return func(c *gin.Context) {
		xRequestID := c.GetHeader("X-Request-ID")
		if xRequestID == "" {
			xRequestID = uuid.NewString()
		}

		c.Set(constHandler.REQUEST_ID, xRequestID)
		startedAt := time.Now()

		c.Next()

		currentRequestID, _ := c.Get(constHandler.REQUEST_ID)
		h.log.Info(fmt.Sprintf(
			"%d %s %s %s %s %s",
			c.Writer.Status(),
			currentRequestID,
			c.Request.Method,
			c.Request.RequestURI,
			c.Request.Proto,
			time.Since(startedAt),
		))
	}
}
