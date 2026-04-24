package middleware

import (
	"net/http"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"
)

const (
	contextUserIDKey              = "user_id"
	contextUserRoleKey            = "user_role"
	contextCanScheduleSemesterKey = "can_schedule_semester"
	contextCanScheduleSessionKey  = "can_schedule_session"
	contextCanScheduleRetakesKey  = "can_schedule_retakes"
)

func InternalAuth() gin.HandlerFunc {
	return func(ctx *gin.Context) {
		rawUserID := strings.TrimSpace(ctx.GetHeader("X-User-ID"))
		if rawUserID == "" {
			ctx.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "X-User-ID header is required"})
			return
		}

		userID, err := strconv.Atoi(rawUserID)
		if err != nil {
			ctx.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "X-User-ID header must be an integer"})
			return
		}

		ctx.Set(contextUserIDKey, userID)
		ctx.Set(contextUserRoleKey, strings.TrimSpace(ctx.GetHeader("X-User-Role")))
		ctx.Set(contextCanScheduleSemesterKey, parseBoolHeader(ctx.GetHeader("X-Can-Schedule-Semester")))
		ctx.Set(contextCanScheduleSessionKey, parseBoolHeader(ctx.GetHeader("X-Can-Schedule-Session")))
		ctx.Set(contextCanScheduleRetakesKey, parseBoolHeader(ctx.GetHeader("X-Can-Schedule-Retakes")))
		ctx.Next()
	}
}

func RequireScheduleSemester() gin.HandlerFunc {
	return func(ctx *gin.Context) {
		if GetUserRole(ctx) == "ADMIN" || CanScheduleSemester(ctx) {
			ctx.Next()
			return
		}
		ctx.AbortWithStatusJSON(http.StatusForbidden, gin.H{"error": "semester scheduling permission required"})
	}
}

func RequireScheduleSession() gin.HandlerFunc {
	return func(ctx *gin.Context) {
		if GetUserRole(ctx) == "ADMIN" || CanScheduleSession(ctx) {
			ctx.Next()
			return
		}
		ctx.AbortWithStatusJSON(http.StatusForbidden, gin.H{"error": "session scheduling permission required"})
	}
}

func RequireScheduleRetakes() gin.HandlerFunc {
	return func(ctx *gin.Context) {
		if GetUserRole(ctx) == "ADMIN" || CanScheduleRetakes(ctx) {
			ctx.Next()
			return
		}
		ctx.AbortWithStatusJSON(http.StatusForbidden, gin.H{"error": "retake scheduling permission required"})
	}
}

func GetUserID(ctx *gin.Context) int {
	value, _ := ctx.Get(contextUserIDKey)
	userID, _ := value.(int)
	return userID
}

func GetUserRole(ctx *gin.Context) string {
	value, _ := ctx.Get(contextUserRoleKey)
	role, _ := value.(string)
	return role
}

func CanScheduleSemester(ctx *gin.Context) bool {
	return getBool(ctx, contextCanScheduleSemesterKey)
}

func CanScheduleSession(ctx *gin.Context) bool {
	return getBool(ctx, contextCanScheduleSessionKey)
}

func CanScheduleRetakes(ctx *gin.Context) bool {
	return getBool(ctx, contextCanScheduleRetakesKey)
}

func getBool(ctx *gin.Context, key string) bool {
	value, _ := ctx.Get(key)
	flag, _ := value.(bool)
	return flag
}

func parseBoolHeader(value string) bool {
	switch strings.ToLower(strings.TrimSpace(value)) {
	case "1", "true", "yes":
		return true
	default:
		return false
	}
}
