package locations

import (
	"database/sql"
	"errors"
	"fmt"
	"github.com/gin-gonic/gin"
	"net/http"
	"raspyx2/internal/handler/constHandler"
	"raspyx2/internal/models"
	"raspyx2/pkg/logger"
	"strings"
)

// @Summary Обновление локации
// @Description Обновление информации о локации по её идентификатору
// @Security ApiKeyAuth
// @Tags locations
// @Accept application/json
// @Produce application/json
// @Param location_uuid path string true "Идентификатор локации"
// @Param request body models.UpdateLocationRequest true "Данные для обновления локации"
// @Success 200 {object} models.ResponseAPI{result=models.LocationResponse} "Данные о локации успешно обновлены"
// @Failure 400 {object} models.ResponseAPI "Неверный формат запроса"
// @Failure 404 {object} models.ResponseAPI "Локация не найдена"
// @Failure 409 {object} models.ResponseAPI "Конфликт при обновлении локации"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/locations/{location_uuid} [put]
func (h *LocationsHandler) UpdateLocation(ctx *gin.Context) {
	var request models.UpdateLocationRequest

	locationUUID := ctx.Param("location_uuid")

	if err := ctx.ShouldBindJSON(&request); err != nil {
		messageError := fmt.Sprintf("Error parsing location data: %s", err.Error())
		logger.NewErrorResponse(ctx, h.log, true, http.StatusBadRequest, messageError)
		return
	}

	updateError := h.service.LocationsService.UpdateLocation(locationUUID, &request)
	if updateError != nil {
		messageError := "Error update location: "
		if errors.Is(updateError, sql.ErrNoRows) {
			messageError += fmt.Sprintf("%s not found", locationUUID)
			logger.NewErrorResponse(ctx, h.log, true, http.StatusNotFound, messageError)
			return
		} else if strings.Contains(updateError.Error(), "already exists") {
			messageError += "target location already exists"
			logger.NewErrorResponse(ctx, h.log, true, http.StatusConflict, messageError)
			return
		}
		messageError += updateError.Error()
		logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)

	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Update location",
		Result: models.LocationResponse{
			LocationUUID: locationUUID,
		},
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}
