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

// @Summary Обновление учебной группы
// @Description Обновление информации об учебной группе по её идентификатору
// @Security ApiKeyAuth
// @Tags groups
// @Accept application/json
// @Produce application/json
// @Param group_uuid path string true "Идентификатор учебной группы"
// @Param request body models.UpdateGroupRequest true "Данные для обновления учебной группы"
// @Success 200 {object} models.ResponseAPI{result=models.GroupResponse} "Данные об учебной группе успешно обновлены"
// @Failure 400 {object} models.ResponseAPI "Неверный формат запроса"
// @Failure 404 {object} models.ResponseAPI "Учебная группа не найдена"
// @Failure 409 {object} models.ResponseAPI "Конфликт при обновлении учебной группы"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/groups/{group_uuid} [put]
func (h *GroupsHandler) UpdateGroup(ctx *gin.Context) {
	var request models.UpdateGroupRequest

	groupUUID := ctx.Param("group_uuid")

	if err := ctx.ShouldBindJSON(&request); err != nil {
		messageError := fmt.Sprintf("Error parsing group data: %s", err.Error())
		logger.NewErrorResponse(ctx, h.log, true, http.StatusBadRequest, messageError)
		return
	}

	updateError := h.service.GroupsService.UpdateGroup(groupUUID, &request)
	if updateError != nil {
		messageError := "Error update group: "
		if errors.Is(updateError, sql.ErrNoRows) {
			messageError += fmt.Sprintf("%s not found", groupUUID)
			logger.NewErrorResponse(ctx, h.log, true, http.StatusNotFound, messageError)
			return
		} else if strings.Contains(updateError.Error(), "already exists") {
			messageError += "target group already exists"
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
		Message:   "Update group",
		Result: models.GroupResponse{
			GroupUUID: groupUUID,
		},
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}
