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

// @Summary Удаление локации
// @Description Удаление локации из системы по её идентификатору
// @Security ApiKeyAuth
// @Tags locations
// @Accept application/json
// @Produce application/json
// @Param location_uuid path string true "Идентификатор локации"
// @Success 200 {object} models.ResponseAPI{result=models.LocationResponse} "Локация успешно удалена"
// @Failure 400 {object} models.ResponseAPI "Неверный формат запроса"
// @Failure 404 {object} models.ResponseAPI "Локация не найдена"
// @Failure 409 {object} models.ResponseAPI "Конфликт при удалении локации"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/locations/{location_uuid} [delete]
func (h *LocationsHandler) DeleteLocation(ctx *gin.Context) {
	locationUUID := ctx.Param("location_uuid")

	deleteError := h.service.LocationsService.DeleteLocation(locationUUID)
	if deleteError != nil {
		messageError := fmt.Sprintf("Error delete location: %s", deleteError.Error())
		if strings.Contains(deleteError.Error(), "not found") {
			logger.NewErrorResponse(ctx, h.log, true, http.StatusNotFound, messageError)
		} else if strings.Contains(deleteError.Error(), "it is being referenced") {
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
		Message:   "Delete location",
		Result: models.LocationResponse{
			LocationUUID: locationUUID,
		},
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}
