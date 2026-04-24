package groups

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

// @Summary Получение учебных групп
// @Description Получение списка всех учебных групп в системе
// @Security ApiKeyAuth
// @Tags groups
// @Accept application/json
// @Produce application/json
// @Success 200 {object} models.ResponseAPI{result=[]models.Group} "Данные об учебных группах успешно получены"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/groups [get]
func (h *GroupsHandler) GetAllGroups(ctx *gin.Context) {
	GetAllGroups, GetAllGroupsError := h.service.GroupsService.GetAllGroups()

	if GetAllGroupsError != nil {
		messageError := fmt.Sprintf("Error get list groups: %s", GetAllGroupsError.Error())
		logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)
	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Get list groups",
		Result:    GetAllGroups,
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}

// @Summary Получение учебной группы по номеру
// @Description Получение информации об учебной группе по её group_number
// @Security ApiKeyAuth
// @Tags groups
// @Accept application/json
// @Produce application/json
// @Param group_number path string true "Номер учебной группы"
// @Success 200 {object} models.ResponseAPI{result=[]models.Group} "Данные об учебной группе успешно получены"
// @Failure 404 {object} models.ResponseAPI "Учебная группа не найдена"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/groups/number/{group_number} [get]
func (h *GroupsHandler) GetGroupsByNumber(ctx *gin.Context) {
	groupNumber := ctx.Param("group_number")
	getGroup, getGroupError := h.service.GroupsService.GetGroupsByNumber(strings.TrimSpace(groupNumber))
	if getGroupError != nil {
		if errors.Is(getGroupError, sql.ErrNoRows) {
			messageError := fmt.Sprintf("Group not found: %s", groupNumber)
			logger.NewErrorResponse(ctx, h.log, true, http.StatusNotFound, messageError)
			return
		}
		messageError := fmt.Sprintf("Error get group %s: %s", groupNumber, getGroupError)
		logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)

	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Get group",
		Result:    getGroup,
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}

// @Summary Получение учебной группы по идентификатору
// @Description Получение информации об учебной группе по её group_uuid
// @Security ApiKeyAuth
// @Tags groups
// @Accept application/json
// @Produce application/json
// @Param group_uuid path string true "Идентификатор учебной группы"
// @Success 200 {object} models.ResponseAPI{result=models.Group} "Данные об учебной группе успешно получены"
// @Failure 404 {object} models.ResponseAPI "Учебная группа не найдена"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/groups/uuid/{group_uuid} [get]
func (h *GroupsHandler) GetGroupByUUID(ctx *gin.Context) {
	groupUUID := ctx.Param("group_uuid")
	getGroup, getGroupError := h.service.GroupsService.GetGroupByUUID(groupUUID)
	if getGroupError != nil {
		if errors.Is(getGroupError, sql.ErrNoRows) {
			messageError := fmt.Sprintf("Group not found: %s", groupUUID)
			logger.NewErrorResponse(ctx, h.log, true, http.StatusNotFound, messageError)
			return
		}
		messageError := fmt.Sprintf("Error get group: %s", groupUUID)
		logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)

	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Get group",
		Result:    getGroup,
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}
