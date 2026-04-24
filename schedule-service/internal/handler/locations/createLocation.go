package locations

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"net/http"
	"raspyx2/internal/handler/constHandler"
	"raspyx2/internal/models"
	"raspyx2/pkg/logger"
	"strings"
)

// @Summary Добавление локации
// @Description Создание новой локации
// @Security ApiKeyAuth
// @Tags locations
// @Accept application/json
// @Produce application/json
// @Param request body models.AddLocationRequest true "Данные новой локации"
// @Success 201 {object} models.ResponseAPI{result=models.LocationResponse} "Локация успешно создана"
// @Failure 400 {object} models.ResponseAPI "Неверный формат запроса"
// @Failure 409 {object} models.ResponseAPI "Конфликт при создании локации"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/locations [post]
func (h *LocationsHandler) CreateLocation(ctx *gin.Context) {
	var request models.AddLocationRequest

	if err := ctx.ShouldBindJSON(&request); err != nil {
		messageError := fmt.Sprintf("Error parsing location data: %s", err.Error())
		logger.NewErrorResponse(ctx, h.log, true, http.StatusBadRequest, messageError)
		return
	}

	request.Name = strings.TrimSpace(request.Name)

	createLocationUUID, createLocationError := h.service.LocationsService.CreateLocation(&request)
	if createLocationError != nil {
		messageError := fmt.Sprintf("Error new location: %s", createLocationError.Error())
		if strings.Contains(createLocationError.Error(), "already exists") {
			logger.NewErrorResponse(ctx, h.log, true, http.StatusConflict, messageError)
		} else {
			logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		}
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)
	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Add new location",
		Result: models.LocationResponse{
			LocationUUID: createLocationUUID,
		},
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusCreated, responseApi)
}
