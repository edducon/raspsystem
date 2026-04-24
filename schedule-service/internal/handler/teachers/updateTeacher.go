package teachers

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

// @Summary Обновление преподавателя
// @Description Обновление информации о преподавателе по его идентификатору
// @Security ApiKeyAuth
// @Tags teachers
// @Accept application/json
// @Produce application/json
// @Param teacher_uuid path string true "Идентификатор преподавателя"
// @Param request body models.UpdateTeacherRequest true "Данные для обновления преподавателя"
// @Success 200 {object} models.ResponseAPI{result=models.TeacherResponse} "Данные о преподавателе успешно обновлены"
// @Failure 400 {object} models.ResponseAPI "Неверный формат запроса"
// @Failure 404 {object} models.ResponseAPI "Преподаватель не найден"
// @Failure 409 {object} models.ResponseAPI "Конфликт при обновлении преподавателя"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/teachers/{teacher_uuid} [put]
func (h *TeachersHandler) UpdateTeacher(ctx *gin.Context) {
	var request models.UpdateTeacherRequest

	teacherUUID := ctx.Param("teacher_uuid")

	if err := ctx.ShouldBindJSON(&request); err != nil {
		messageError := fmt.Sprintf("Error parsing teacher data: %s", err.Error())
		logger.NewErrorResponse(ctx, h.log, true, http.StatusBadRequest, messageError)
		return
	}

	updateError := h.service.TeachersService.UpdateTeacher(teacherUUID, &request)
	if updateError != nil {
		messageError := "Error update teacher: "
		if errors.Is(updateError, sql.ErrNoRows) {
			messageError += fmt.Sprintf("%s not found", teacherUUID)
			logger.NewErrorResponse(ctx, h.log, true, http.StatusNotFound, messageError)
			return
		} else if strings.Contains(updateError.Error(), "required") {
			messageError += updateError.Error()
			logger.NewErrorResponse(ctx, h.log, true, http.StatusBadRequest, messageError)
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
		Message:   "Update teacher",
		Result: models.TeacherResponse{
			TeacherUUID: teacherUUID,
		},
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}
