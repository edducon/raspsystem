package handler

import (
	"net/http"
	internalauth "raspyx2/internal/middleware"

	"github.com/gin-gonic/gin"
)

func (h *Handler) InitRoutes() *gin.Engine {
	routes := gin.New()
	routes.Use(h.RequestLogger())

	routes.GET("/healthz", func(ctx *gin.Context) {
		ctx.JSON(http.StatusOK, gin.H{"status": "ok"})
	})

	routes.GET("/buildings", h.CatalogHandler.ListBuildings)
	routes.GET("/buildings/:id", h.CatalogHandler.GetBuilding)
	routes.GET("/campuses", h.CatalogHandler.ListCampuses)
	routes.GET("/campuses/:id", h.CatalogHandler.GetCampus)
	routes.GET("/rooms", h.CatalogHandler.ListRooms)
	routes.GET("/rooms/:id", h.CatalogHandler.GetRoom)
	routes.GET("/directions", h.CatalogHandler.ListDirections)
	routes.GET("/directions/:id", h.CatalogHandler.GetDirection)
	routes.GET("/groups", h.CatalogHandler.ListGroups)
	routes.GET("/groups/:id", h.CatalogHandler.GetGroup)
	routes.GET("/subjects", h.CatalogHandler.ListSubjects)
	routes.GET("/subjects/:id", h.CatalogHandler.GetSubject)
	routes.GET("/subject-types", h.CatalogHandler.ListSubjectTypes)
	routes.GET("/subject-types/:id", h.CatalogHandler.GetSubjectType)

	mutating := routes.Group("/")
	mutating.Use(internalauth.InternalAuth())
	{
		mutating.POST("/buildings", h.CatalogHandler.CreateBuilding)
		mutating.PUT("/buildings/:id", h.CatalogHandler.UpdateBuilding)
		mutating.DELETE("/buildings/:id", h.CatalogHandler.DeleteBuilding)

		mutating.POST("/campuses", h.CatalogHandler.CreateCampus)
		mutating.PUT("/campuses/:id", h.CatalogHandler.UpdateCampus)
		mutating.DELETE("/campuses/:id", h.CatalogHandler.DeleteCampus)

		mutating.POST("/rooms", h.CatalogHandler.CreateRoom)
		mutating.PUT("/rooms/:id", h.CatalogHandler.UpdateRoom)
		mutating.DELETE("/rooms/:id", h.CatalogHandler.DeleteRoom)

		mutating.POST("/directions", h.CatalogHandler.CreateDirection)
		mutating.PUT("/directions/:id", h.CatalogHandler.UpdateDirection)
		mutating.DELETE("/directions/:id", h.CatalogHandler.DeleteDirection)

		mutating.POST("/groups", h.CatalogHandler.CreateGroup)
		mutating.PUT("/groups/:id", h.CatalogHandler.UpdateGroup)
		mutating.DELETE("/groups/:id", h.CatalogHandler.DeleteGroup)

		mutating.POST("/subjects", h.CatalogHandler.CreateSubject)
		mutating.PUT("/subjects/:id", h.CatalogHandler.UpdateSubject)
		mutating.DELETE("/subjects/:id", h.CatalogHandler.DeleteSubject)

		mutating.POST("/subject-types", h.CatalogHandler.CreateSubjectType)
		mutating.PUT("/subject-types/:id", h.CatalogHandler.UpdateSubjectType)
		mutating.DELETE("/subject-types/:id", h.CatalogHandler.DeleteSubjectType)
	}

	return routes
}
