package subjectTypes

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"net/http"
	"raspyx2/internal/handler/constHandler"
	"raspyx2/internal/models"
	"raspyx2/pkg/logger"
	"strings"
)

// @Summary Удаление типа дисциплины
// @Description Удаление типа дисциплины из системы по его идентификатору
// @Security ApiKeyAuth
// @Tags subject_types
// @Accept application/json
// @Produce application/json
// @Param subject_type_uuid path string true "Идентификатор типа дисциплины"
// @Success 200 {object} models.ResponseAPI{result=models.SubjectTypeResponse} "Тип дисциплины успешно удален"
// @Failure 400 {object} models.ResponseAPI "Неверный формат запроса"
// @Failure 404 {object} models.ResponseAPI "Тип дисциплины не найдена"
// @Failure 409 {object} models.ResponseAPI "Конфликт при удалении типа дисциплины"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/subject_types/{subject_type_uuid} [delete]
func (h *SubjectTypesHandler) DeleteSubjectType(ctx *gin.Context) {
	subjectTypeUUID := ctx.Param("subject_type_uuid")

	deleteError := h.service.SubjectTypesService.DeleteSubjectType(subjectTypeUUID)
	if deleteError != nil {
		messageError := fmt.Sprintf("Error delete subject type: %s", deleteError.Error())
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
		Message:   "Delete subject type",
		Result: models.SubjectTypeResponse{
			SubjectTypeUUID: subjectTypeUUID,
		},
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}
