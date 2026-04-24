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

// @Summary Получение локаций
// @Description Получение списка всех локаций в системе
// @Security ApiKeyAuth
// @Tags locations
// @Accept application/json
// @Produce application/json
// @Success 200 {object} models.ResponseAPI{result=[]models.Location} "Данные о локациях успешно получены"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/locations [get]
func (h *LocationsHandler) GetAllLocations(ctx *gin.Context) {
	GetAllLocations, GetAllLocationsError := h.service.LocationsService.GetAllLocations()

	if GetAllLocationsError != nil {
		messageError := fmt.Sprintf("Error get list locations: %s", GetAllLocationsError.Error())
		logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)
	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Get list locations",
		Result:    GetAllLocations,
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}

// @Summary Получение локации по её названию
// @Description Получение информации о локации по её location_name
// @Security ApiKeyAuth
// @Tags locations
// @Accept application/json
// @Produce application/json
// @Param location_name path string true "Название локации"
// @Success 200 {object} models.ResponseAPI{result=[]models.Location} "Данные о локации успешно получены"
// @Failure 404 {object} models.ResponseAPI "Локация не найдена"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/locations/number/{location_name} [get]
func (h *LocationsHandler) GetLocationsByName(ctx *gin.Context) {
	locationName := ctx.Param("location_name")
	getLocation, getLocationError := h.service.LocationsService.GetLocationsByName(strings.TrimSpace(locationName))
	if getLocationError != nil {
		if errors.Is(getLocationError, sql.ErrNoRows) {
			messageError := fmt.Sprintf("Location not found: %s", locationName)
			logger.NewErrorResponse(ctx, h.log, true, http.StatusNotFound, messageError)
			return
		}
		messageError := fmt.Sprintf("Error get location %s: %s", locationName, getLocationError)
		logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)

	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Get location",
		Result:    getLocation,
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}

// @Summary Получение локации по идентификатору
// @Description Получение информации о локации по её location_uuid
// @Security ApiKeyAuth
// @Tags locations
// @Accept application/json
// @Produce application/json
// @Param location_uuid path string true "Идентификатор локации"
// @Success 200 {object} models.ResponseAPI{result=models.Location} "Данные о локации успешно получены"
// @Failure 404 {object} models.ResponseAPI "Локация не найдена"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/locations/uuid/{location_uuid} [get]
func (h *LocationsHandler) GetLocationByUUID(ctx *gin.Context) {
	locationUUID := ctx.Param("location_uuid")
	getLocation, getLocationError := h.service.LocationsService.GetLocationByUUID(locationUUID)
	if getLocationError != nil {
		if errors.Is(getLocationError, sql.ErrNoRows) {
			messageError := fmt.Sprintf("Location not found: %s", locationUUID)
			logger.NewErrorResponse(ctx, h.log, true, http.StatusNotFound, messageError)
			return
		}
		messageError := fmt.Sprintf("Error get location: %s", locationUUID)
		logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)

	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Get location",
		Result:    getLocation,
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}
