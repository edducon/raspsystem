package teachers

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"net/http"
	"raspyx2/internal/handler/constHandler"
	"raspyx2/internal/models"
	"raspyx2/pkg/logger"
	"strings"
)

// @Summary Удаление преподавателя
// @Description Удаление преподавателя из системы по его идентификатору
// @Security ApiKeyAuth
// @Tags teachers
// @Accept application/json
// @Produce application/json
// @Param teacher_uuid path string true "Идентификатор преподавателя"
// @Success 200 {object} models.ResponseAPI{result=models.TeacherResponse} "Преподаватель успешно удалена"
// @Failure 400 {object} models.ResponseAPI "Неверный формат запроса"
// @Failure 404 {object} models.ResponseAPI "Преподаватель не найден"
// @Failure 409 {object} models.ResponseAPI "Конфликт при удалении преподавателя"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/teachers/{teacher_uuid} [delete]
func (h *TeachersHandler) DeleteTeacher(ctx *gin.Context) {
	teacherUUID := ctx.Param("teacher_uuid")

	deleteError := h.service.TeachersService.DeleteTeacher(teacherUUID)
	if deleteError != nil {
		messageError := fmt.Sprintf("Error delete teacher: %s", deleteError.Error())
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
		Message:   "Delete teacher",
		Result: models.TeacherResponse{
			TeacherUUID: teacherUUID,
		},
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}
