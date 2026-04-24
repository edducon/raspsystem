package groups

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"net/http"
	"raspyx2/internal/handler/constHandler"
	"raspyx2/internal/models"
	"raspyx2/pkg/logger"
	"strings"
)

// @Summary Удаление учебной группы
// @Description Удаление учебной группы из системы по её идентификатору
// @Security ApiKeyAuth
// @Tags groups
// @Accept application/json
// @Produce application/json
// @Param group_uuid path string true "Идентификатор учебной группы"
// @Success 200 {object} models.ResponseAPI{result=models.GroupResponse} "Учебная группа успешно удалена"
// @Failure 400 {object} models.ResponseAPI "Неверный формат запроса"
// @Failure 404 {object} models.ResponseAPI "Учебная группа не найдена"
// @Failure 409 {object} models.ResponseAPI "Конфликт при удалении учебной группы"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/groups/{group_uuid} [delete]
func (h *GroupsHandler) DeleteGroup(ctx *gin.Context) {
	groupUUID := ctx.Param("group_uuid")

	deleteError := h.service.GroupsService.DeleteGroup(groupUUID)
	if deleteError != nil {
		messageError := fmt.Sprintf("Error delete group: %s", deleteError.Error())
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
		Message:   "Delete group",
		Result: models.GroupResponse{
			GroupUUID: groupUUID,
		},
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}
