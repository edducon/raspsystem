package subjects

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"net/http"
	"raspyx2/internal/handler/constHandler"
	"raspyx2/internal/models"
	"raspyx2/pkg/logger"
	"strings"
)

// @Summary Удаление дисциплины
// @Description Удаление дисциплины из системы по её идентификатору
// @Security ApiKeyAuth
// @Tags subjects
// @Accept application/json
// @Produce application/json
// @Param subject_uuid path string true "Идентификатор дисциплины"
// @Success 200 {object} models.ResponseAPI{result=models.SubjectResponse} "Дисциплина успешно удалена"
// @Failure 400 {object} models.ResponseAPI "Неверный формат запроса"
// @Failure 404 {object} models.ResponseAPI "Дисциплина не найдена"
// @Failure 409 {object} models.ResponseAPI "Конфликт при удалении дисциплины"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/subjects/{subject_uuid} [delete]
func (h *SubjectsHandler) DeleteSubject(ctx *gin.Context) {
	subjectUUID := ctx.Param("subject_uuid")

	deleteError := h.service.SubjectsService.DeleteSubject(subjectUUID)
	if deleteError != nil {
		messageError := fmt.Sprintf("Error delete subject: %s", deleteError.Error())
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
		Message:   "Delete subject",
		Result: models.SubjectResponse{
			SubjectUUID: subjectUUID,
		},
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}
